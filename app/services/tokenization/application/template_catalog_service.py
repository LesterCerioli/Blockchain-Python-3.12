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
    TemplateCloneError,
    TemplateConsistencyError,
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

    def _validate_token_model_consistency(self, template: Template) -> list[str]:
        errors = []
        tm = template.token_model

        if tm.standard not in ("ERC20", "ERC721", "ERC1155", "ERC4626"):
            errors.append(f"Invalid token standard: {tm.standard}")

        if tm.standard == "ERC721":
            if tm.decimals != 0:
                errors.append("ERC721 tokens should have decimals = 0")
            if tm.initial_supply > 1 and not tm.max_supply:
                errors.append("ERC721 with supply > 1 should define max_supply")

        if tm.standard == "ERC1155":
            if tm.decimals != 0:
                errors.append("ERC1155 tokens should have decimals = 0")

        if tm.governance.governance_enabled:
            if tm.governance.voting_period_hours == 0:
                errors.append("Governance enabled but voting_period_hours is 0")
            if tm.governance.voting_threshold_pct <= 0:
                errors.append("Governance enabled but voting_threshold_pct must be > 0")

        if tm.compliance.max_holders is not None:
            if tm.max_supply is not None and tm.compliance.max_holders > tm.max_supply:
                errors.append(
                    f"max_holders ({tm.compliance.max_holders}) exceeds "
                    f"max_supply ({tm.max_supply})"
                )

        if tm.vesting.vesting_months > 0 and tm.vesting.cliff_months > tm.vesting.vesting_months:
            errors.append(
                f"cliff_months ({tm.vesting.cliff_months}) cannot exceed "
                f"vesting_months ({tm.vesting.vesting_months})"
            )

        if tm.emission.emission_type not in ("fixed", "decreasing", "increasing"):
            errors.append(f"Invalid emission_type: {tm.emission.emission_type}")

        return errors

    def _detect_overrides(self, parent: Template, child: Template) -> set[str]:
        overridden = set()
        fields_to_check = {
            "description", "category", "strategy", "token_standard",
        }
        for field in fields_to_check:
            if getattr(parent, field) != getattr(child, field):
                overridden.add(field)

        if parent.token_model.model_dump() != child.token_model.model_dump():
            overridden.add("token_model")
        if parent.characteristics.model_dump() != child.characteristics.model_dump():
            overridden.add("characteristics")
        if parent.metadata.model_dump() != child.metadata.model_dump():
            overridden.add("metadata")
        if [r.model_dump() for r in parent.business_rules] != [r.model_dump() for r in child.business_rules]:
            overridden.add("business_rules")

        return overridden

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

        if token_model is None:
            decimals = 0 if token_standard in ("ERC721", "ERC1155") else 18
            tm = TokenModel(standard=token_standard, name=name, symbol=name[:8].upper(), decimals=decimals)
        else:
            # Ensure ERC721/1155 decimals auto-correct if not explicitly set to 0
            if token_standard in ("ERC721", "ERC1155") and token_model.get("decimals", 18) != 0:
                token_model = {**token_model, "decimals": 0}
            tm = TokenModel(**token_model)
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

        validation_errors = self._validate_token_model_consistency(template)
        if validation_errors:
            raise TemplateConsistencyError("; ".join(validation_errors))

        await self._repository.create(template)
        self._log_event("template_created", name, user_id)
        return template

    async def clone_template(
        self,
        email: str,
        source_name: str,
        new_name: str,
        overrides: dict | None = None,
    ) -> Template:
        user_id = self._resolve_user_id_by_email(email)
        source = await self._resolve(user_id, source_name)

        existing = await self._repository.get_by_name(user_id, new_name)
        if existing is not None:
            raise TemplateAlreadyExistsError(new_name)

        if not source.is_active and not source.is_editable:
            raise TemplateCloneError(
                source_name,
                f"Source template is in status '{source.status.value}' "
                "and cannot be cloned",
            )

        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        from app.services.tokenization.domain.entities.business_rule import BusinessRule
        from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
        from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
        from app.services.tokenization.domain.entities.token_model import TokenModel

        token_model_data = source.token_model.model_dump()
        characteristics_data = source.characteristics.model_dump()
        metadata_data = source.metadata.model_dump()
        business_rules_data = [r.model_dump() for r in source.business_rules]

        overridden_fields: set[str] = set()

        if overrides:
            if "token_model" in overrides:
                token_model_data.update(overrides["token_model"])
                overridden_fields.add("token_model")
            if "characteristics" in overrides:
                characteristics_data.update(overrides["characteristics"])
                overridden_fields.add("characteristics")
            if "metadata" in overrides:
                metadata_data.update(overrides["metadata"])
                overridden_fields.add("metadata")
            if "business_rules" in overrides:
                business_rules_data = overrides["business_rules"]
                overridden_fields.add("business_rules")
            for simple_field in ("description", "category", "strategy", "token_standard"):
                if simple_field in overrides:
                    overridden_fields.add(simple_field)

        template = Template(
            template_id=template_id,
            name=new_name,
            description=overrides.get("description", source.description) if overrides else source.description,
            category=overrides.get("category", source.category) if overrides else source.category,
            strategy=overrides.get("strategy", source.strategy) if overrides else source.strategy,
            token_standard=overrides.get("token_standard", source.token_standard) if overrides else source.token_standard,
            status=TemplateStatus.DRAFT,
            version=TemplateVersion(major=1, minor=0, patch=0),
            metadata=TemplateMetadata(**metadata_data),
            characteristics=TemplateCharacteristics(**characteristics_data),
            token_model=TokenModel(**token_model_data),
            business_rules=[BusinessRule(**r) for r in business_rules_data],
            parent_template_id=source.template_id,
            overridden_fields=overridden_fields,
            created_at=now,
            updated_at=now,
            created_by=user_id,
        )

        validation_errors = self._validate_token_model_consistency(template)
        if validation_errors:
            raise TemplateConsistencyError("; ".join(validation_errors))

        await self._repository.create(template)
        self._log_event(
            "template_cloned",
            new_name,
            user_id,
            {"source": source_name, "overridden_fields": sorted(overridden_fields)},
        )
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
            "parent_template_id": template.parent_template_id,
            "overridden_fields": template.overridden_fields,
            "created_at": template.created_at,
            "updated_at": now,
            "created_by": template.created_by,
            "approved_by": template.approved_by,
            "approved_at": template.approved_at,
        }

        updated = Template(**updated_fields)

        validation_errors = self._validate_token_model_consistency(updated)
        if validation_errors:
            raise TemplateConsistencyError("; ".join(validation_errors))

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

    async def validate_template(self, email: str, name: str) -> dict:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)
        errors = self._validate_token_model_consistency(template)
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "template_name": template.name,
            "token_standard": template.token_standard,
        }

    async def get_template_lineage(self, email: str, name: str) -> list[dict]:
        user_id = self._resolve_user_id_by_email(email)
        template = await self._resolve(user_id, name)
        chain = []
        current = template
        while current is not None:
            chain.append({
                "template_id": current.template_id,
                "name": current.name,
                "version": current.version.to_string(),
                "status": current.status.value,
                "overridden_fields": sorted(current.overridden_fields),
            })
            if current.parent_template_id:
                parent = await self._repository.get_by_id(user_id, current.parent_template_id)
                current = parent
            else:
                current = None
        return chain
