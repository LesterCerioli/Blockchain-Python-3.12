

from __future__ import annotations

import os
import sys

import boto3

TABLE_LLM_HISTORY = "BLOCKCHAIN_llm_reorder_history"
TABLE_AI_DIAGNOSIS = "BLOCKCHAIN_ai_diagnosis_history"

LLM_HISTORY_TABLES: list[dict] = [
    {
        "name": TABLE_LLM_HISTORY,
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "tokenization_implementation_id", "AttributeType": "S"},
            {"AttributeName": "provider", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_id_index",  # usado por list_by_user
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "implementation_id_index",  # usado por list_by_implementation
                "KeySchema": [{"AttributeName": "tokenization_implementation_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "provider_index",
                "KeySchema": [{"AttributeName": "provider", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "created_at_index",
                "KeySchema": [{"AttributeName": "created_at", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": TABLE_AI_DIAGNOSIS,
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "tokenization_implementation_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_id_index",  # usado por list_by_user
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "implementation_id_index",  # usado por list_by_implementation
                "KeySchema": [{"AttributeName": "tokenization_implementation_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "created_at_index",
                "KeySchema": [{"AttributeName": "created_at", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
]


def get_client():
    endpoint = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    return boto3.client("dynamodb", endpoint_url=endpoint, region_name=region)


def create_table(client, table_name, attribute_defs, key_schema, gsis=None) -> bool:
    params = {
        "TableName": table_name,
        "AttributeDefinitions": attribute_defs,
        "KeySchema": key_schema,
        "BillingMode": "PAY_PER_REQUEST",
    }
    if gsis:
        params["GlobalSecondaryIndexes"] = gsis
    try:
        client.create_table(**params)
        print(f"Tabela {table_name} criada com sucesso!")
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 30})
        return True
    except client.exceptions.ResourceInUseException:
        print(f"Tabela {table_name} ja existe - ignorando.")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"Erro ao criar {table_name}: {e}", file=sys.stderr)
        return False


def create_llm_history_tables(client=None) -> bool:
    """Cria apenas as 2 tabelas de historico de IA. Retorna True se ambas OK."""
    client = client or get_client()
    ok = True
    for cfg in LLM_HISTORY_TABLES:
        print(f"Criando tabela: {cfg['name']}")
        created = create_table(
            client,
            table_name=cfg["name"],
            attribute_defs=cfg["attribute_defs"],
            key_schema=cfg["key_schema"],
            gsis=cfg.get("gsis"),
        )
        print("  [OK]" if created else "  [FAILED]")
        ok = ok and created
    return ok


def verify_llm_history_tables(client=None) -> bool:
    """Confere PK + GSIs das 2 tabelas. Retorna True se conforme."""
    client = client or get_client()
    expected = {
        TABLE_LLM_HISTORY: {"user_id_index", "implementation_id_index", "provider_index", "created_at_index"},
        TABLE_AI_DIAGNOSIS: {"user_id_index", "implementation_id_index", "created_at_index"},
    }
    ok = True
    existing = set(client.list_tables().get("TableNames", []))
    for table, want_gsis in expected.items():
        if table not in existing:
            print(f"  [MISSING] {table} nao existe")
            ok = False
            continue
        desc = client.describe_table(TableName=table)["Table"]
        got = {g["IndexName"] for g in desc.get("GlobalSecondaryIndexes", [])}
        missing = want_gsis - got
        if missing:
            print(f"  [MISSING GSIs] {table}: faltam {sorted(missing)} (tem {sorted(got)})")
            ok = False
        else:
            print(f"  [OK] {table}: GSIs={sorted(got)}")
    return ok


def main() -> int:
    print("== Criando tabelas de historico de IA ==")
    if not create_llm_history_tables():
        print("Falha na criacao.", file=sys.stderr)
        return 1
    print("\n== Verificando ==")
    if not verify_llm_history_tables():
        print("Verificacao falhou.", file=sys.stderr)
        return 1
    print("\nAll LLM history tables ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
