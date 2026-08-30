from __future__ import annotations

import json
import logging
import os
from time import time
from uuid import uuid4

import boto3

from ...domain.entities.template import Template
from ...domain.entities.template_status import TemplateStatus
from ...domain.interfaces.template_repository import ITemplateRepository

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

TABLE_TEMPLATES = "BLOCKCHAIN_tokenization_templates"


def generate_id() -> str:
    return str(uuid4())


def now_ms() -> int:
    return int(time() * 1000)


class DynamoDBTemplateRepository(ITemplateRepository):
    def __init__(self) -> None:
        self._client = boto3.client(
            "dynamodb",
            endpoint_url=ENDPOINT,
            region_name=REGION,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )

    def _to_item(self, template: Template) -> dict:
        now = now_ms()
        return {
            "id": {"S": template.template_id},
            "user_id": {"S": template.created_by},
            "name": {"S": template.name},
            "description": {"S": template.description},
            "category": {"S": template.characteristics.category},
            "strategy": {"S": template.characteristics.target_use_case},
            "token_standard": {"S": template.token_model.standard},
            "status": {"S": template.status},
            "version": {"S": template.version},
            "metadata": {"S": json.dumps(template.metadata.model_dump())},
            "characteristics": {"S": json.dumps(template.characteristics.model_dump())},
            "token_model": {"S": json.dumps(template.token_model.model_dump())},
            "business_rules": {"S": json.dumps([r.model_dump() for r in template.business_rules])},
            "created_by": {"S": template.created_by},
            "approved_by": {"S": template.approved_by or ""},
            "approved_at": {"S": template.approved_at or ""},
            "created_at": {"N": str(template.metadata.created_at.timestamp() * 1000 if hasattr(template.metadata.created_at, 'timestamp') else now)},
            "updated_at": {"N": str(template.metadata.updated_at.timestamp() * 1000 if hasattr(template.metadata.updated_at, 'timestamp') else now)},
        }

    def _from_item(self, item: dict) -> Template | None:
        if not item:
            return None

        from ...domain.entities.business_rule import BusinessRule
        from ...domain.entities.template_characteristics import TemplateCharacteristics
        from ...domain.entities.template_metadata import TemplateMetadata
        from ...domain.entities.token_model import TokenModel

        metadata_data = json.loads(item.get("metadata", {}).get("S", "{}"))
        characteristics_data = json.loads(item.get("characteristics", {}).get("S", "{}"))
        token_model_data = json.loads(item.get("token_model", {}).get("S", "{}"))
        business_rules_data = json.loads(item.get("business_rules", {}).get("S", "[]"))

        return Template(
            template_id=item["id"]["S"],
            name=item["name"]["S"],
            description=item["description"]["S"],
            characteristics=TemplateCharacteristics(**characteristics_data),
            token_model=TokenModel(**token_model_data),
            status=item["status"]["S"],
            version=item["version"]["S"],
            metadata=TemplateMetadata(**metadata_data),
            business_rules=[BusinessRule(**r) for r in business_rules_data],
            created_by=item.get("created_by", {}).get("S", ""),
        )

    async def get_by_id(self, user_id: str, template_id: str) -> Template | None:
        resp = self._client.get_item(
            TableName=TABLE_TEMPLATES,
            Key={"id": {"S": template_id}},
        )
        item = resp.get("Item")
        if item and item.get("user_id", {}).get("S") == user_id:
            return self._from_item(item)
        return None

    async def get_by_name(self, user_id: str, name: str) -> Template | None:
        resp = self._client.query(
            TableName=TABLE_TEMPLATES,
            IndexName="name_index",
            KeyConditionExpression="#nm = :nm",
            ExpressionAttributeNames={"#nm": "name"},
            ExpressionAttributeValues={":nm": {"S": name}},
            Limit=1,
        )
        items = resp.get("Items", [])
        for item in items:
            if item.get("user_id", {}).get("S") == user_id:
                return self._from_item(item)
        return None

    async def create(self, template: Template) -> None:
        item = self._to_item(template)
        self._client.put_item(TableName=TABLE_TEMPLATES, Item=item)

    async def update(self, template: Template) -> None:
        item = self._to_item(template)
        self._client.put_item(TableName=TABLE_TEMPLATES, Item=item)

    async def delete(self, user_id: str, template_id: str) -> None:
        self._client.delete_item(
            TableName=TABLE_TEMPLATES,
            Key={"id": {"S": template_id}},
        )

    async def list_all(self, user_id: str) -> list[Template]:
        resp = self._client.query(
            TableName=TABLE_TEMPLATES,
            IndexName="user_id_index",
            KeyConditionExpression="#uid = :uid",
            ExpressionAttributeNames={"#uid": "user_id"},
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        return [self._from_item(item) for item in resp.get("Items", [])]

    async def list_by_status(self, user_id: str, status: TemplateStatus) -> list[Template]:
        all_templates = await self.list_all(user_id)
        return [t for t in all_templates if t.status == status]

    async def list_by_category(self, user_id: str, category: str) -> list[Template]:
        all_templates = await self.list_all(user_id)
        return [t for t in all_templates if t.characteristics.category.lower() == category.lower()]

    async def list_by_strategy(self, user_id: str, strategy: str) -> list[Template]:
        all_templates = await self.list_all(user_id)
        return [t for t in all_templates if t.characteristics.target_use_case.lower() == strategy.lower()]

    async def list_by_token_standard(self, user_id: str, standard: str) -> list[Template]:
        all_templates = await self.list_all(user_id)
        return [t for t in all_templates if t.token_model.standard.upper() == standard.upper()]

    async def search(
        self,
        user_id: str,
        query: str | None = None,
        category: str | None = None,
        strategy: str | None = None,
        token_standard: str | None = None,
        status: TemplateStatus | None = None,
        tags: list[str] | None = None,
        industry: str | None = None,
    ) -> list[Template]:
        all_templates = await self.list_all(user_id)
        results = all_templates

        if query:
            query_lower = query.lower()
            results = [
                t for t in results
                if query_lower in t.name.lower()
                or query_lower in t.description.lower()
                or any(query_lower in tag.lower() for tag in t.metadata.tags)
            ]

        if category:
            results = [t for t in results if t.characteristics.category == category]

        if strategy:
            results = [t for t in results if t.characteristics.target_use_case == strategy]

        if token_standard:
            results = [t for t in results if t.token_model.standard == token_standard]

        if status:
            results = [t for t in results if t.status == status]

        if tags:
            results = [
                t for t in results
                if any(tag in t.metadata.tags for tag in tags)
            ]

        if industry:
            results = [t for t in results if t.characteristics.industry == industry]

        return results

    async def count(self, user_id: str) -> int:
        templates = await self.list_all(user_id)
        return len(templates)
