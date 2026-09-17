import os

import boto3

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

c = boto3.client(
    "dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1"
)

for t in c.list_tables()["TableNames"]:
    if not t.startswith("BLOCKCHAIN_"):
        continue
    d = c.describe_table(TableName=t)["Table"]
    gsis = [g["IndexName"] for g in d.get("GlobalSecondaryIndexes", [])]
    pk = [k["AttributeName"] for k in d["KeySchema"]]
    print(f"{t}: PK={pk}  GSIs={gsis}")
