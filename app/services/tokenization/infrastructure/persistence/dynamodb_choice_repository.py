from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3

from ...domain.entities.business_type import BusinessType
from ...domain.entities.tokenization_choice import TokenizationChoice
from ...domain.interfaces.choice_repository import IChoiceRepository

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

# Spec says tabela tokenization_templates já criada -> we use BLOCKCHAIN_tokenization_templates
TABLE_CHOICES = "BLOCKCHAIN_tokenization_templates"


class DynamoDBChoiceRepository(IChoiceRepository):
    """Persists TokenizationChoice in DynamoDB table BLOCKCHAIN_tokenization_templates.

    Uses same table as templates (PAY_PER_REQUEST, schemaless) with distinct
    attributes: business_type, description_tokenization, tokenization_template.
    Isolation by user_id via GSI user_id_index.
    """

    def __init__(self) -> None:
        self._client = boto3.client(
            "dynamodb",
            endpoint_url=ENDPOINT,
            region_name=REGION,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )

    def _to_item(self, choice: TokenizationChoice) -> dict:
        return {
            "id": {"S": choice.id},
            "user_id": {"S": choice.user_id},
            "business_type": {"S": choice.business_type.value},
            "description_tokenization": {"S": choice.description_tokenization},
            "tokenization_template": {"S": choice.tokenization_template},
            "chosen_at": {"S": choice.chosen_at},
            # marker to distinguish from template catalog items
            "record_type": {"S": "choice"},
            # keep name attribute for GSI compatibility if needed
            "name": {"S": f"choice:{choice.id}"},
            "category": {"S": choice.business_type.value},
            "status": {"S": "choice"},
            "created_at": {"N": str(int(datetime.fromisoformat(choice.chosen_at).timestamp() * 1000))},
        }

    def _from_item(self, item: dict) -> TokenizationChoice | None:
        if not item or item.get("record_type", {}).get("S") != "choice":
            return None
        try:
            return TokenizationChoice(
                id=item["id"]["S"],
                user_id=item["user_id"]["S"],
                business_type=BusinessType(item["business_type"]["S"]),
                description_tokenization=item["description_tokenization"]["S"],
                tokenization_template=item["tokenization_template"]["S"],
                chosen_at=item["chosen_at"]["S"],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse choice item %s: %s", item.get("id"), exc)
            return None

    async def save(self, choice: TokenizationChoice) -> None:
        item = self._to_item(choice)
        # put_item is parameterized via boto3, no SQL injection surface
        self._client.put_item(TableName=TABLE_CHOICES, Item=item)

    async def list_by_user(self, user_id: str) -> list[TokenizationChoice]:
        resp = self._client.query(
            TableName=TABLE_CHOICES,
            IndexName="user_id_index",
            KeyConditionExpression="#uid = :uid",
            FilterExpression="#rt = :rt",
            ExpressionAttributeNames={"#uid": "user_id", "#rt": "record_type"},
            ExpressionAttributeValues={
                ":uid": {"S": user_id},
                ":rt": {"S": "choice"},
            },
        )
        choices = []
        for item in resp.get("Items", []):
            c = self._from_item(item)
            if c:
                choices.append(c)
        return choices

    async def get_by_id(self, user_id: str, choice_id: str) -> TokenizationChoice | None:
        resp = self._client.get_item(
            TableName=TABLE_CHOICES,
            Key={"id": {"S": choice_id}},
        )
        item = resp.get("Item")
        if not item:
            return None
        choice = self._from_item(item)
        if choice and choice.user_id == user_id:
            return choice
        return None
