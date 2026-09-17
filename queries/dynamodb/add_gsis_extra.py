import boto3, os, time

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

c = boto3.client("dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1")

# GSI specs: (index_name, [(attr, type, key_type)])  -- sort keys optional
gsi_specs = {
    "BLOCKCHAIN_ohlcv_candles": [
        ("symbol_interval_index", [("symbol", "S", "HASH"), ("interval", "S", "RANGE")]),
        ("symbol_time_index", [("symbol", "S", "HASH"), ("open_time", "N", "RANGE")]),
    ],
    "BLOCKCHAIN_positions": [
        ("user_index", [("user_id", "S", "HASH")]),
        ("pool_index", [("pool_address", "S", "HASH")]),
    ],
}


def existing_gsis(table_name):
    return {g["IndexName"] for g in c.describe_table(TableName=table_name)["Table"].get("GlobalSecondaryIndexes", [])}


def wait_active(table_name, idx_name):
    for _ in range(120):
        st = {g["IndexName"]: g["IndexStatus"] for g in c.describe_table(TableName=table_name)["Table"].get("GlobalSecondaryIndexes", [])}
        if st.get(idx_name) == "ACTIVE":
            return
        time.sleep(1)


for table, specs in gsi_specs.items():
    print(f"Tabela: {table}")
    for idx_name, keys in specs:
        if idx_name in existing_gsis(table):
            print(f"  GSI {idx_name} ja existe - ignorando.")
            continue
        attr_defs = [{"AttributeName": a, "AttributeType": t} for a, t, _ in keys]
        key_schema = [{"AttributeName": a, "KeyType": kt} for a, _, kt in keys]
        c.update_table(
            TableName=table,
            AttributeDefinitions=attr_defs,
            GlobalSecondaryIndexUpdates=[{
                "Create": {
                    "IndexName": idx_name,
                    "KeySchema": key_schema,
                    "Projection": {"ProjectionType": "ALL"},
                }
            }],
        )
        print(f"  Criado GSI {idx_name} - aguardando ACTIVE...")
        wait_active(table, idx_name)

print("\nEstado final:")
for table in gsi_specs:
    d = c.describe_table(TableName=table)["Table"]
    st = {g["IndexName"]: g["IndexStatus"] for g in d.get("GlobalSecondaryIndexes", [])}
    print(f"{table}: {st}")
