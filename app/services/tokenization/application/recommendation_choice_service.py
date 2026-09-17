from __future__ import annotations

import hashlib
import logging
import time
from uuid import uuid4

from ..domain.entities.business_type import BusinessType
from ..domain.entities.tokenization_choice import TokenizationChoice
from ..domain.interfaces.choice_repository import IChoiceRepository
from ..domain.interfaces.template_repository import ITemplateRepository
from ..infrastructure.config.settings import TokenizationSettings
from ..infrastructure.llm.factory import get_reorder_adapter
from ..infrastructure.llm.ports import LLMReorderPort

logger = logging.getLogger(__name__)

TABLE_USERS = "BLOCKCHAIN_users"


class RecommendationChoiceService:
    
    def __init__(
        self,
        template_repository: ITemplateRepository,
        choice_repository: IChoiceRepository,
        groq_adapter: LLMReorderPort | None = None,
        postgres_choices: IChoiceRepository | None = None,
        llm_history_repository=None,
        diagnosis_repository=None,
        settings: TokenizationSettings | None = None,
        users_client=None,
    ) -> None:
        self._templates = template_repository
        self._choices = choice_repository
        self._settings = settings or TokenizationSettings()
        if groq_adapter is not None:
            self._groq = groq_adapter
        else:
            self._groq = get_reorder_adapter(self._settings)
        self._postgres_choices = postgres_choices
        self._llm_history = llm_history_repository
        self._diagnosis_repo = diagnosis_repository
        if users_client is not None:
            self._users_client = users_client
        else:
            self._users_client = None  # lazy, created on first resolve

    def _get_users_client(self):
        if self._users_client is not None:
            return self._users_client
        import os

        import boto3

        self._users_client = boto3.client(
            "dynamodb",
            endpoint_url=os.environ.get("LOCALSTACK_ENDPOINT"),
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        return self._users_client

    def _resolve_user_id_by_email(self, email: str) -> str:
        
        normalized = (email or "").strip().lower()
        if not normalized:
            raise ValueError("email required")
        resp = self._get_users_client().query(
            TableName=TABLE_USERS,
            IndexName="email_index",
            KeyConditionExpression="#em = :em",
            ExpressionAttributeNames={"#em": "email"},
            ExpressionAttributeValues={":em": {"S": normalized}},
            Limit=1,
        )
        items = resp.get("Items", [])
        if not items:
            raise ValueError(f"user not found for email: {email}")
        return items[0]["user_id"]["S"]

    async def get_templates_by_business_type(
        self, email: str, business_type: BusinessType
    ) -> list[str]:
        user_id = self._resolve_user_id_by_email(email)
                
        templates = await self._templates.search(user_id=user_id, industry=business_type.value)
        
        if not templates:
            all_tpls = await self._templates.list_all(user_id=user_id)
            templates = [
                t
                for t in all_tpls
                if t.characteristics.industry.lower() == business_type.value.lower()
                or business_type.value.lower() in [tag.lower() for tag in t.metadata.tags]
            ]
        return [t.name for t in templates]

    async def reorder_with_groq(
        self,
        business_type: BusinessType,
        description: str,
        available_templates: list[str],
        email: str | None = None,
        tokenization_implementation_id: str | None = None,
    ) -> list[str]:
        
        if not available_templates:
            return []
        start = time.monotonic()
        ordered = await self._groq.reorder(business_type, description, available_templates)
        latency_ms = int((time.monotonic() - start) * 1000)
        allowed = set(available_templates)
        filtered = [n for n in ordered if n in allowed]
        missing = [n for n in available_templates if n not in filtered]
        result = filtered + missing
        filtered_flag = len(ordered) != len(result) or any(n not in allowed for n in ordered)
        if filtered_flag:
            logger.warning("LLM tried to invent, filtered: %s -> %s", ordered, result)

        resolved_user_id: str | None = None
        if email:
            try:
                resolved_user_id = self._resolve_user_id_by_email(email)
            except ValueError:
                resolved_user_id = None

        if self._llm_history is not None and resolved_user_id:
            try:
                provider = getattr(self._settings, "llm_provider", "groq")
                model = getattr(self._settings, f"{provider}_model", "")
                await self._llm_history.save(
                    user_id=resolved_user_id,
                    business_type=business_type.value,
                    provider=provider,
                    model=str(model),
                    description=description,
                    available_templates=available_templates,
                    ordered_templates=result,
                    tokenization_implementation_id=tokenization_implementation_id,
                    filtered_invention=filtered_flag,
                    latency_ms=latency_ms,
                )
            except Exception:
                logger.exception("Failed to persist llm_history for email=%s", email)
        return result

    async def persist_choice(
        self,
        email: str,
        business_type: BusinessType,
        description_tokenization: str,
        tokenization_template: str,
    ) -> TokenizationChoice:
        if not tokenization_template or not tokenization_template.strip():
            raise ValueError("tokenization_template required")
        user_id = self._resolve_user_id_by_email(email)
        trimmed_template = tokenization_template.strip()
        if trimmed_template == "Nenhuma destas — Criar do Zero":
            logger.info(
                "Criar do Zero selected by email=%s — frontend should create template first",
                email,
            )
        choice = TokenizationChoice(
            id=str(uuid4()),
            user_id=user_id,
            business_type=business_type,
            description_tokenization=description_tokenization.strip(),
            tokenization_template=trimmed_template,
        )
        await self._choices.save(choice)
        if self._postgres_choices is not None:
            try:
                await self._postgres_choices.save(choice)
            except Exception:
                logger.exception("Postgres audit write failed for choice %s", choice.id)
        logger.info(
            "Choice persisted user_id=%s business_type=%s template=%s",
            choice.user_id,
            choice.business_type.value,
            choice.tokenization_template,
        )
        return choice

    async def get_user_choices(self, email: str) -> list[TokenizationChoice]:
        user_id = self._resolve_user_id_by_email(email)
        return await self._choices.list_by_user(user_id)
