from __future__ import annotations

import logging
import os
from uuid import uuid4

import boto3

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    logger.debug("python-dotenv not available; relying on existing environment")

ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

TABLE_SESSIONS = "BLOCKCHAIN_sessions"
TABLE_KYC = "BLOCKCHAIN_kyc_profiles"
TABLE_METADATA = "BLOCKCHAIN_app_metadata"
TABLE_AUDIT = "BLOCKCHAIN_audit_logs"
TABLE_RATE_LIMITS = "BLOCKCHAIN_rate_limits"
TABLE_TOKEN_META = "BLOCKCHAIN_token_meta"
TABLE_OHLCV = "BLOCKCHAIN_ohlcv_candles"
TABLE_POSITIONS = "BLOCKCHAIN_positions"
TABLE_USERS = "BLOCKCHAIN_users"


def generate_id() -> str:

    return str(uuid4())


def now_ms() -> int:

    from time import time

    return int(time() * 1000)


class DynamoDBClient:
    def __init__(self) -> None:
        self._client = boto3.client(
            "dynamodb",
            endpoint_url=ENDPOINT,
            region_name=REGION,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )

    def put_item(self, table: str, item: dict) -> str:

        self._client.put_item(TableName=table, Item=item)
        return item["id"]["S"]

    def update_item(
        self,
        table: str,
        key: dict,
        update_expression: str,
        expr_names: dict | None = None,
        expr_values: dict | None = None,
        condition_expression: str | None = None,
    ) -> None:
        params = {
            "TableName": table,
            "Key": key,
            "UpdateExpression": update_expression,
        }
        if expr_names:
            params["ExpressionAttributeNames"] = expr_names
        if expr_values:
            params["ExpressionAttributeValues"] = expr_values
        if condition_expression:
            params["ConditionExpression"] = condition_expression
        self._client.update_item(**params)

    def delete_item(self, table: str, item_id: str) -> None:
        self._client.delete_item(TableName=table, Key={"id": {"S": item_id}})

    def get_by_id(self, table: str, item_id: str) -> dict | None:
        resp = self._client.get_item(TableName=table, Key={"id": {"S": item_id}})
        return resp.get("Item")

    def query_index(
        self,
        table: str,
        index_name: str,
        partition_attr: str,
        partition_value: str,
    ) -> list[dict]:

        resp = self._client.query(
            TableName=table,
            IndexName=index_name,
            KeyConditionExpression="#pk = :pv",
            ExpressionAttributeNames={"#pk": partition_attr},
            ExpressionAttributeValues={":pv": {"S": partition_value}},
        )
        return resp.get("Items", [])
