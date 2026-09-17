import json
import logging
import os
from time import time
from uuid import uuid4

import boto3

logger = logging.getLogger(__name__)

TABLE_TEMPLATE_AUDIT = "BLOCKCHAIN_tokenization_audit_logs"


class DynamoDBTemplateAuditLogger:
    """Logs template lifecycle events to DynamoDB for audit trail."""

    def __init__(self) -> None:
        endpoint = os.environ.get("LOCALSTACK_ENDPOINT")
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

        self._client = boto3.client(
            "dynamodb",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def log_event(
        self,
        action: str,
        template_name: str,
        performed_by: str,
        details: dict | None = None,
    ) -> None:
        """Append an audit event for a template lifecycle change."""
        item = {
            "user_id": {"S": performed_by},
            "id": {"S": str(uuid4())},
            "template_name": {"S": template_name},
            "action": {"S": action},
            "created_at": {"N": str(int(time() * 1000))},
        }
        if details:
            item["details"] = {"S": json.dumps(details)}

        try:
            self._client.put_item(TableName=TABLE_TEMPLATE_AUDIT, Item=item)
        except Exception:
            logger.exception("Failed to write template audit event: %s", action)
