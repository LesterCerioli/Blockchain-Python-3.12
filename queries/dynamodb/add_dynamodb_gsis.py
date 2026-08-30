import os
import time

import boto3

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

c = boto3.client(
    "dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1"
)

gsi_specs = {
    "BLOCKCHAIN_sessions": [
        ("session_id_index", "session_id", "S"),
        ("user_id_index", "user_id", "S"),
        ("expires_at_index", "expires_at", "N"),
    ],
    "BLOCKCHAIN_kyc_profiles": [
        ("user_index", "user_id", "S"),
        ("version_index", "version", "N"),
    ],
    "BLOCKCHAIN_app_metadata": [
        ("user_meta_index", "user_id", "S"),
    ],
    "BLOCKCHAIN_audit_logs": [
        ("user_index", "user_id", "S"),
        ("action_index", "action", "S"),
        ("time_index", "created_at", "N"),
    ],
    "BLOCKCHAIN_rate_limits": [
        ("key_index", "key", "S"),
    ],
    "BLOCKCHAIN_token_meta": [
        ("symbol_index", "symbol", "S"),
    ],
}


def existing_gsis(table_name):
    return {
        g["IndexName"]
        for g in c.describe_table(TableName=table_name)["Table"].get(
            "GlobalSecondaryIndexes", []
        )
    }


def wait_active(table_name, idx_name):
    for _ in range(120):
        st = {
            g["IndexName"]: g["IndexStatus"]
            for g in c.describe_table(TableName=table_name)["Table"].get(
                "GlobalSecondaryIndexes", []
            )
        }
        if st.get(idx_name) == "ACTIVE":
            return
        time.sleep(1)
    print(f"  AVISO: GSI {idx_name} nao ficou ACTIVE em 120s")


for table, specs in gsi_specs.items():
    print(f"Tabela: {table}")
    for idx_name, attr, attr_type in specs:
        if idx_name in existing_gsis(table):
            print(f"  GSI {idx_name} ja existe - ignorando.")
            continue
        c.update_table(
            TableName=table,
            AttributeDefinitions=[{"AttributeName": attr, "AttributeType": attr_type}],
            GlobalSecondaryIndexUpdates=[
                {
                    "Create": {
                        "IndexName": idx_name,
                        "KeySchema": [{"AttributeName": attr, "KeyType": "HASH"}],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                }
            ],
        )
        print(f"  Criado GSI {idx_name} - aguardando ACTIVE...")
        wait_active(table, idx_name)

print("\nEstado final das GSIs:")
for table in gsi_specs:
    d = c.describe_table(TableName=table)["Table"]
    st = {g["IndexName"]: g["IndexStatus"] for g in d.get("GlobalSecondaryIndexes", [])}
    print(f"{table}: {st}")
