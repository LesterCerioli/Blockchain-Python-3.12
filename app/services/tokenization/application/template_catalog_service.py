import uuid
from datetime import datetime, timezone
from typing import Protocol

import boto3

from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.exceptions import (
    ApprovalRequiredError,
    InvalidTemplateVersionError,
    TemplateAlreadyExistsError,
    TemplateNotArchivableError,
    TemplateNotEditableError,
    TemplateNotFoundError,
    TemplateValidationError,
)
from app.services.tokenization.domain.interfaces.template_repository import ITemplateRepository

TABLE_USERS = "BLOCKCHAIN_users"


class IAuditLogger(Protocol):
    def log_event(
        self,
        action: str,
        template_name: str,
        performed_by: str,
        details: dict | None = None,
    ) -> None: ...


class TemplateCatalogService:
    def __init__(
        self,
        template_repository: ITemplateRepository,
        audit_logger: IAuditLogger | None = None,
        users_client=None,
    ) -> None:
        self._repository = template_repository
        self._audit_logger = audit_logger
        if users_client is not None:
            self._users_client = users_client
        else:
            import os
            import boto3
            self._users_client = boto3.client(
                "dynamodb",
                endpoint_url=os.environ.get("LOCALSTACK_ENDPOINT"),
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            )

    def _resolve_user_id_by_email(self, email: str) -> str:
        resp = self._users_client.query(
            TableName=TABLE_USERS,
            IndexName="email_index",
            KeyConditionExpression="#em = :em",
            ExpressionAttributeNames={"#em": "email"},
            ExpressionAttributeValues={":em": {"S": email.strip().lower()}},
            Limit=1,
        )
        items = resp.get("Items", [])
        if not items:
            raise TemplateNotFoundError(f"user not found for email: {email}")
        return items[0]["user_id"]["S"]

    def _log_event(
        self,
        action: str,
        template_name: str,
        performed_by: str,
        details: dict | None = None,
    ) -> None:
        if self._audit_logger:
            self._audit_logger.log_event(action, template_name, performed_by, details)

    async def _resolve(self, user_id: str, name: str) -> Template:
        template = await self._repository.get_by_name(user_id, name)
        if template is None:
            raise TemplateNotFoundError(name)
        return template

    async def create_template(
        self,
        email: str,
        name: str,
        description: str,
        category: str,
        strategy: str,
        token_standard: str,
        token_model: dict | None = None,
        characteristics: dict | None = None,
        metadata: dict | None = None,
        business_rules: list[dict] | None = None,
    ) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        existing = await self._repository.get_by_name(user_id, name)
        if existing is not None:
            raise TemplateAlreadyExistsError(name)

        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        from app.services.tokenization.domain.entities.business_rule import BusinessRule
        from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
        from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
        from app.services.tokenization.domain.entities.token_model import TokenModel

        tm = TokenModel(standard=token_standard, name=name, symbol=name[:8].upper()) if token_model is None else TokenModel(**token_model)
        ch = TemplateCharacteristics(target_use_case="general", industry="general") if characteristics is None else TemplateCharacteristics(**characteristics)
        md = TemplateMetadata() if metadata is None else TemplateMetadata(**metadata)
        rules = [BusinessRule(**r) for r in business_rules] if business_rules else []

        template = Template(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            strategy=strategy,
            token_standard=token_standard,
            status=TemplateStatus.DRAFT,
            version=TemplateVersion(major=1, minor=0, patch=0),
            metadata=md,
            characteristics=ch,
            token_model=tm,
            business_rules=rules,
            created_at=now,
            updated_at=now,
            created_by=user_id,
        )

        await self._repository.create(template)
        self._log_event("template_created", name, user_id)
        return template

    async def get_template(self, email: str, name: str) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        return await self._resolve(user_id, name)

    async def update_template(
        self,
        email: str,
        name: str,
        description: str | None = None,
        category: str | None = None,
        strategy: str | None = None,
        token_standard: str | None = None,
        token_model: dict | None = None,
        characteristics: dict | None = None,
        metadata: dict | None = None,
        business_rules: list[dict] | None = None,
    ) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        if not template.is_editable:
            raise TemplateNotEditableError(name, template.status.value)

        now = datetime.now(timezone.utc).isoformat()

        from app.services.tokenization.domain.entities.business_rule import BusinessRule
        from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
        from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
        from app.services.tokenization.domain.entities.token_model import TokenModel

        updated_fields = {
            "template_id": template.template_id,
            "name": template.name,
            "description": description or template.description,
            "category": category or template.category,
            "strategy": strategy or template.strategy,
            "token_standard": token_standard or template.token_standard,
            "status": template.status,
            "version": template.version,
            "metadata": TemplateMetadata(**metadata) if metadata else template.metadata,
            "characteristics": TemplateCharacteristics(**characteristics) if characteristics else template.characteristics,
            "token_model": TokenModel(**token_model) if token_model else template.token_model,
            "business_rules": [BusinessRule(**r) for r in business_rules] if business_rules else template.business_rules,
            "created_at": template.created_at,
            "updated_at": now,
            "created_by": template.created_by,
            "approved_by": template.approved_by,
            "approved_at": template.approved_at,
        }

        updated = Template(**updated_fields)
        await self._repository.update(updated)
        self._log_event("template_updated", name, user_id)
        return updated

    async def archive_template(self, email: str, name: str) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        if template.status == TemplateStatus.ARCHIVED:
            raise TemplateNotArchivableError(name, template.status.value)

        now = datetime.now(timezone.utc).isoformat()
        archived = template.model_copy(
            update={"status": TemplateStatus.ARCHIVED, "updated_at": now}
        )
        await self._repository.update(archived)
        self._log_event("template_archived", name, user_id)
        return archived

    async def submit_for_review(self, email: str, name: str) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        if template.status != TemplateStatus.DRAFT:
            raise TemplateNotEditableError(name, template.status.value)

        now = datetime.now(timezone.utc).isoformat()
        submitted = template.model_copy(
            update={"status": TemplateStatus.PENDING_REVIEW, "updated_at": now}
        )
        await self._repository.update(submitted)
        self._log_event("template_submitted", name, user_id)
        return submitted

    async def approve_template(
        self, email: str, name: str, approved_by: str
    ) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        if template.status != TemplateStatus.PENDING_REVIEW:
            raise TemplateNotEditableError(name, template.status.value)

        now = datetime.now(timezone.utc).isoformat()
        approved = template.model_copy(
            update={
                "status": TemplateStatus.APPROVED,
                "approved_by": approved_by,
                "approved_at": now,
                "updated_at": now,
            }
        )
        await self._repository.update(approved)
        self._log_event("template_approved", name, user_id, {"approved_by": approved_by})
        return approved

    async def activate_template(self, email: str, name: str) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        if template.status != TemplateStatus.APPROVED:
            raise ApprovalRequiredError(name)

        now = datetime.now(timezone.utc).isoformat()
        activated = template.model_copy(
            update={"status": TemplateStatus.ACTIVE, "updated_at": now}
        )
        await self._repository.update(activated)
        self._log_event("template_activated", name, user_id)
        return activated

    async def deprecate_template(self, email: str, name: str) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        now = datetime.now(timezone.utc).isoformat()
        deprecated = template.model_copy(
            update={"status": TemplateStatus.DEPRECATED, "updated_at": now}
        )
        await self._repository.update(deprecated)
        self._log_event("template_deprecated", name, user_id)
        return deprecated

    async def bump_version(
        self, email: str, name: str, bump_type: str = "patch"
    ) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)

        current = template.version
        if bump_type == "major":
            new_version = TemplateVersion(
                major=current.major + 1, minor=0, patch=0
            )
        elif bump_type == "minor":
            new_version = TemplateVersion(
                major=current.major, minor=current.minor + 1, patch=0
            )
        elif bump_type == "patch":
            new_version = TemplateVersion(
                major=current.major, minor=current.minor, patch=current.patch + 1
            )
        else:
            raise InvalidTemplateVersionError(current.to_string(), bump_type)

        now = datetime.now(timezone.utc).isoformat()
        updated = template.model_copy(
            update={"version": new_version, "updated_at": now}
        )
        await self._repository.update(updated)
        self._log_event("template_version_bumped", name, user_id, {"new_version": new_version.to_string()})
        return updated

    async def list_templates(self, email: str) -> list[Template]:
        user_id = self._resolve_user_id_by_email(email)
        return await self._repository.list_all(user_id)

    async def list_by_status(self, email: str, status: TemplateStatus) -> list[Template]:
        user_id = self._resolve_user_id_by_email(email)
        return await self._repository.list_by_status(user_id, status)

    async def list_by_category(self, email: str, category: str) -> list[Template]:
        user_id = self._resolve_user_id_by_email(email)
        return await self._repository.list_by_category(user_id, category)

    async def list_by_strategy(self, email: str, strategy: str) -> list[Template]:
        user_id = self._resolve_user_id_by_email(email)
        return await self._repository.list_by_strategy(user_id, strategy)

    async def search_templates(
        self,
        email: str,
        query: str | None = None,
        category: str | None = None,
        strategy: str | None = None,
        token_standard: str | None = None,
        status: TemplateStatus | None = None,
        tags: list[str] | None = None,
        industry: str | None = None,
    ) -> list[Template]:
        user_id = self._resolve_user_id_by_email(email)
        return await self._repository.search(
            user_id=user_id,
            query=query,
            category=category,
            strategy=strategy,
            token_standard=token_standard,
            status=status,
            tags=tags,
            industry=industry,
        )

    async def count_templates(self, email: str) -> int:
        user_id = self._resolve_user_id_by_email(email)
        return await self._repository.count(user_id)
