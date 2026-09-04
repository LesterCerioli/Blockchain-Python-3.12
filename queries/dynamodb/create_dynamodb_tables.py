
import os

import boto3

ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

client = boto3.client("dynamodb", endpoint_url=ENDPOINT, region_name=REGION)


def create_table(table_name, attribute_defs, key_schema, gsis=None):
    
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
        print(f"Erro ao criar {table_name}: {e}")
        return False



tables = [
    {
        "name": "BLOCKCHAIN_sessions",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "session_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "expires_at", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "session_id_index",
                "KeySchema": [{"AttributeName": "session_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "expires_at_index",
                "KeySchema": [{"AttributeName": "expires_at", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "BLOCKCHAIN_kyc_profiles",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "version", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "version_index",
                "KeySchema": [{"AttributeName": "version", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "BLOCKCHAIN_app_metadata",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_meta_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
    {
        "name": "BLOCKCHAIN_audit_logs",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "action", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "action_index",
                "KeySchema": [{"AttributeName": "action", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "time_index",
                "KeySchema": [{"AttributeName": "created_at", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "BLOCKCHAIN_rate_limits",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "key", "AttributeType": "S"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "key_index",
                "KeySchema": [{"AttributeName": "key", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
    {
        "name": "BLOCKCHAIN_token_meta",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "symbol", "AttributeType": "S"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "symbol_index",
                "KeySchema": [{"AttributeName": "symbol", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
    {
        "name": "BLOCKCHAIN_users",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "email_index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "BLOCKCHAIN_tokenization_templates",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "name", "AttributeType": "S"},
            {"AttributeName": "category", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "name_index",
                "KeySchema": [{"AttributeName": "name", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "category_index",
                "KeySchema": [{"AttributeName": "category", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "status_index",
                "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}],
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
        "name": "BLOCKCHAIN_tokenization_audit_logs",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "template_name", "AttributeType": "S"},
            {"AttributeName": "action", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "template_name_index",
                "KeySchema": [{"AttributeName": "template_name", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "action_index",
                "KeySchema": [{"AttributeName": "action", "KeyType": "HASH"}],
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
        "name": "BLOCKCHAIN_ohlcv_candles",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "symbol", "AttributeType": "S"},
            {"AttributeName": "interval", "AttributeType": "S"},
            {"AttributeName": "open_time", "AttributeType": "N"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "symbol_interval_index",
                "KeySchema": [
                    {"AttributeName": "symbol", "KeyType": "HASH"},
                    {"AttributeName": "interval", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "symbol_time_index",
                "KeySchema": [
                    {"AttributeName": "symbol", "KeyType": "HASH"},
                    {"AttributeName": "open_time", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "BLOCKCHAIN_positions",
        "attribute_defs": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "pool_address", "AttributeType": "S"},
        ],
        "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "gsis": [
            {
                "IndexName": "user_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "pool_index",
                "KeySchema": [{"AttributeName": "pool_address", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
]

for cfg in tables:
    print(f"Criando tabela: {cfg['name']}")
    ok = create_table(
        table_name=cfg["name"],
        attribute_defs=cfg["attribute_defs"],
        key_schema=cfg["key_schema"],
        gsis=cfg.get("gsis"),
    )
    print("  [OK]" if ok else "  [FAILED]")

print("\nAll table creation processes completed.")
