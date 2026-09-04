from __future__ import annotations

import logging
from uuid import uuid4

from ..domain.entities.business_type import BusinessType
from ..domain.entities.tokenization_choice import TokenizationChoice
from ..domain.interfaces.choice_repository import IChoiceRepository
from ..domain.interfaces.template_repository import ITemplateRepository
from ..infrastructure.llm.groq_adapter import GroqReorderAdapter, LLMReorderPort

logger = logging.getLogger(__name__)


class RecommendationChoiceService:
    """Orquestra fluxo 5 passos: business_type -> templates async -> groq reorder -> persist choice."""

    def __init__(
        self,
        template_repository: ITemplateRepository,
        choice_repository: IChoiceRepository,
        groq_adapter: LLMReorderPort | None = None,
        postgres_choices: IChoiceRepository | None = None,
    ) -> None:
        self._templates = template_repository
        self._choices = choice_repository
        self._groq = groq_adapter or GroqReorderAdapter()
        self._postgres_choices = postgres_choices

    async def get_templates_by_business_type(
        self, user_id: str, business_type: BusinessType
    ) -> list[str]:
        """Passo 1: busca async todos templates vinculados ao setor. Não bloqueia descrição."""
        # Usa search parametrizado por industry (filtrado em memória após query user_id_index)
        templates = await self._templates.search(user_id=user_id, industry=business_type.value)
        # Fallback: also check tags/industry partial via list_all
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
    ) -> list[str]:
        """Passo 3: chama Groq só para reordenar, nunca inventar."""
        if not available_templates:
            return []
        ordered = await self._groq.reorder(business_type, description, available_templates)
        # Double guard: ensure no invention
        allowed = set(available_templates)
        filtered = [n for n in ordered if n in allowed]
        missing = [n for n in available_templates if n not in filtered]
        result = filtered + missing
        if len(ordered) != len(result) or any(n not in allowed for n in ordered):
            logger.warning("Groq tried to invent, filtered: %s -> %s", ordered, result)
        return result

    async def persist_choice(
        self,
        user_id: str,
        business_type: BusinessType,
        description_tokenization: str,
        tokenization_template: str,
    ) -> TokenizationChoice:
        """Passo 5: persiste APENAS escolha final com isolamento user_id.

        Writes to DynamoDB (primary) and optionally to Postgres (audit SQL).
        """
        if not user_id.strip():
            raise ValueError("user_id required")
        if not tokenization_template.strip():
            raise ValueError("tokenization_template required")
        trimmed_template = tokenization_template.strip()
        if trimmed_template == "Nenhuma destas — Criar do Zero":
            logger.info(
                "Criar do Zero selected by user_id=%s — frontend should create template first",
                user_id.strip(),
            )
        choice = TokenizationChoice(
            id=str(uuid4()),
            user_id=user_id.strip(),
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

    async def get_user_choices(self, user_id: str) -> list[TokenizationChoice]:
        return await self._choices.list_by_user(user_id)
