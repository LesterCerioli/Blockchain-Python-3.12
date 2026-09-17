from __future__ import annotations

import hashlib
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

TABLE_LLM_HISTORY = "BLOCKCHAIN_llm_reorder_history"
TABLE_TEMPLATES = "BLOCKCHAIN_tokenization_templates"


class DynamoDBLLMHistoryRepository:
    
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
        business_type: str,
        provider: str,
        model: str,
        description: str,
        available_templates: list[str],
        ordered_templates: list[str],
        tokenization_implementation_id: str | None = None,
        filtered_invention: bool = False,
        latency_ms: int = 0,
    ) -> str:
        self._validate_fk(tokenization_implementation_id)
        now = int(time() * 1000)
        item_id = str(uuid4())
        desc_hash = hashlib.sha256(description.encode()).hexdigest()
        item: dict = {
            "id": {"S": item_id},
            "user_id": {"S": user_id},
            "business_type": {"S": business_type},
            "provider": {"S": provider},
            "model": {"S": model},
            "description_hash": {"S": desc_hash},
            "available_templates": {"S": json.dumps(available_templates)},
            "ordered_templates": {"S": json.dumps(ordered_templates)},
            "filtered_invention": {"BOOL": filtered_invention},
            "latency_ms": {"N": str(latency_ms)},
            "created_at": {"N": str(now)},
            "record_type": {"S": "llm_reorder"},
        }
        if tokenization_implementation_id:
            item["tokenization_implementation_id"] = {"S": tokenization_implementation_id}
        self._client.put_item(TableName=TABLE_LLM_HISTORY, Item=item)
        return item_id

    async def list_by_user(self, user_id: str) -> list[dict]:
        resp = self._client.query(
            TableName=TABLE_LLM_HISTORY,
            IndexName="user_id_index",
            KeyConditionExpression="#uid = :uid",
            ExpressionAttributeNames={"#uid": "user_id"},
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        return resp.get("Items", [])

    async def list_by_implementation(self, tokenization_implementation_id: str) -> list[dict]:
        resp = self._client.query(
            TableName=TABLE_LLM_HISTORY,
            IndexName="implementation_id_index",
            KeyConditionExpression="#impl = :impl",
            ExpressionAttributeNames={"#impl": "tokenization_implementation_id"},
            ExpressionAttributeValues={":impl": {"S": tokenization_implementation_id}},
        )
        return resp.get("Items", [])
