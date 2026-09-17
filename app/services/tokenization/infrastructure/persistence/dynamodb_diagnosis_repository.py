from __future__ import annotations

import json
import logging
import os
from time import time
from uuid import uuid4

import boto3

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    logger.debug("dotenv not available")

ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

TABLE_DIAGNOSIS = "BLOCKCHAIN_ai_diagnosis_history"
TABLE_TEMPLATES = "BLOCKCHAIN_tokenization_templates"


class DynamoDBDiagnosisRepository:
    
    def __init__(self) -> None:
        self._client = boto3.client(
            "dynamodb",
            endpoint_url=ENDPOINT,
            region_name=REGION,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )

    def _validate_fk(self, tokenization_implementation_id: str | None) -> None:
        if not tokenization_implementation_id:
            return
        resp = self._client.get_item(
            TableName=TABLE_TEMPLATES,
            Key={"id": {"S": tokenization_implementation_id}},
        )
        if "Item" not in resp:
            raise ValueError(
                f"tokenization_implementation_id '{tokenization_implementation_id}' "
                f"nao existe em {TABLE_TEMPLATES}.id"
            )

    async def save(
        self,
        user_id: str,
        objective_description: str,
        primary_category: str,
        diagnosis_payload: dict,
        tokenization_implementation_id: str | None = None,
    ) -> str:
        self._validate_fk(tokenization_implementation_id)
        now = int(time() * 1000)
        item_id = str(uuid4())
        item: dict = {
            "id": {"S": item_id},
            "user_id": {"S": user_id},
            "objective_description": {"S": objective_description},
            "primary_category": {"S": primary_category},
            "diagnosis_payload": {"S": json.dumps(diagnosis_payload)},
            "created_at": {"N": str(now)},
            "record_type": {"S": "diagnosis"},
        }
        if tokenization_implementation_id:
            item["tokenization_implementation_id"] = {"S": tokenization_implementation_id}
        self._client.put_item(TableName=TABLE_DIAGNOSIS, Item=item)
        return item_id

    async def list_by_user(self, user_id: str) -> list[dict]:
        resp = self._client.query(
            TableName=TABLE_DIAGNOSIS,
            IndexName="user_id_index",
            KeyConditionExpression="#uid = :uid",
            ExpressionAttributeNames={"#uid": "user_id"},
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        return resp.get("Items", [])

    async def list_by_implementation(self, tokenization_implementation_id: str) -> list[dict]:
        resp = self._client.query(
            TableName=TABLE_DIAGNOSIS,
            IndexName="implementation_id_index",
            KeyConditionExpression="#impl = :impl",
            ExpressionAttributeNames={"#impl": "tokenization_implementation_id"},
            ExpressionAttributeValues={":impl": {"S": tokenization_implementation_id}},
        )
        return resp.get("Items", [])
