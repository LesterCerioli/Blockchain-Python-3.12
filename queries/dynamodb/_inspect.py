import boto3, os

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

c = boto3.client("dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1")

for t in ("BLOCKCHAIN_ohlcv_candles", "BLOCKCHAIN_positions"):
    try:
        d = c.describe_table(TableName=t)["Table"]
    except Exception as e:
        print(f"{t}: ERRO {e}")
        continue
    print(f"{t}:")
    print("  KeySchema:", d["KeySchema"])
    print("  AttributeDefinitions:", d.get("AttributeDefinitions"))
    print("  GSIs:", [(g["IndexName"], g["KeySchema"]) for g in d.get("GlobalSecondaryIndexes", [])])
