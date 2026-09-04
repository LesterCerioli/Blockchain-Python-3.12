import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.tokenization.application.recommendation_choice_service import RecommendationChoiceService
from app.services.tokenization.domain.entities.business_type import BusinessType
from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.entities.token_model import TokenModel
from app.services.tokenization.domain.entities.tokenization_choice import TokenizationChoice
from app.services.tokenization.infrastructure.config.settings import TokenizationSettings
from app.services.tokenization.infrastructure.llm.groq_adapter import GroqReorderAdapter
from app.services.tokenization.infrastructure.persistence.dynamodb_choice_repository import DynamoDBChoiceRepository


def _make_template(name: str, industry: str) -> Template:
    return Template(
        template_id=f"id-{name}",
        name=name,
        description=f"desc {name}",
        category="loyalty",
        strategy="customer-retention",
        token_standard="ERC20",
        status=TemplateStatus.ACTIVE,
        version=TemplateVersion(major=1, minor=0, patch=0),
        metadata=TemplateMetadata(tags=[industry]),
        characteristics=TemplateCharacteristics(target_use_case="loyalty", industry=industry),
        token_model=TokenModel(standard="ERC20", name=name, symbol="TKN"),
    )


class TestBusinessType:
    def test_values(self):
        assert BusinessType.RETAIL.value == "retail"
        assert BusinessType.FINANCE.value == "finance"
        assert "retail" in BusinessType.values()


class TestTokenizationChoice:
    def test_valid(self):
        c = TokenizationChoice(
            id="1", user_id="u1", business_type=BusinessType.RETAIL,
            description_tokenization="need to improve loyalty and reduce churn 15%",
            tokenization_template="Loyalty Token"
        )
        assert c.business_type == BusinessType.RETAIL

    def test_blank_user_id_raises(self):
        with pytest.raises(ValueError):
            TokenizationChoice(id="1", user_id=" ", business_type=BusinessType.RETAIL,
                               description_tokenization="valid description 1234567890", tokenization_template="T")

    def test_short_description_raises(self):
        with pytest.raises(ValueError):
            TokenizationChoice(id="1", user_id="u1", business_type=BusinessType.RETAIL,
                               description_tokenization="short", tokenization_template="T")


class TestGroqAdapter:
    def test_disabled_returns_original(self):
        settings = TokenizationSettings(groq_enabled=False)
        adapter = GroqReorderAdapter(settings=settings)
        result = asyncio.run(adapter.reorder(BusinessType.RETAIL, "desc", ["A", "B"]))
        assert result == ["A", "B"]

    def test_no_api_key_returns_original(self):
        settings = TokenizationSettings(groq_api_key=None, groq_enabled=True)
        adapter = GroqReorderAdapter(settings=settings)
        result = asyncio.run(adapter.reorder(BusinessType.RETAIL, "desc", ["A", "B"]))
        assert result == ["A", "B"]

    def test_reorder_filters_invention(self):
        
        async def mock_post(*args, **kwargs):
            class Resp:
                def raise_for_status(self): pass
                def json(self):
                    return {"choices": [{"message": {"content": '["B", "A", "Invented Token"]'}}]}
            return Resp()
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=mock_post)
        mock_client.aclose = AsyncMock()
        settings = TokenizationSettings(groq_api_key="test-key", groq_enabled=True)
        adapter = GroqReorderAdapter(settings=settings, http_client=mock_client)
        result = asyncio.run(adapter.reorder(BusinessType.RETAIL, "desc", ["A", "B"]))
        
        assert "Invented Token" not in result
        assert set(result) == {"A", "B"}
        assert result[0] == "B"

    def test_groq_failure_fallback(self):
        async def mock_post_fail(*args, **kwargs):
            raise httpx.ConnectError("fail")
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=mock_post_fail)
        mock_client.aclose = AsyncMock()
        settings = TokenizationSettings(groq_api_key="test-key", groq_enabled=True, groq_timeout_seconds=1)
        adapter = GroqReorderAdapter(settings=settings, http_client=mock_client)
        result = asyncio.run(adapter.reorder(BusinessType.RETAIL, "desc", ["A", "B"]))
        assert result == ["A", "B"]


class TestRecommendationChoiceService:
    def test_get_templates_by_business_type_filters(self):
        mock_repo = MagicMock()
        # search returns only retail
        retail_tpl = _make_template("Loyalty Token", "retail")
        gaming_tpl = _make_template("Reward Token", "gaming")
        mock_repo.search = AsyncMock(return_value=[retail_tpl])
        mock_repo.list_all = AsyncMock(return_value=[retail_tpl, gaming_tpl])
        choice_repo = MagicMock()
        svc = RecommendationChoiceService(mock_repo, choice_repo, GroqReorderAdapter(TokenizationSettings(groq_enabled=False)))
        result = asyncio.run(svc.get_templates_by_business_type("u1", BusinessType.RETAIL))
        assert "Loyalty Token" in result
        assert "Reward Token" not in result

    def test_reorder_with_groq_only_reorders(self):
        mock_repo = MagicMock()
        choice_repo = MagicMock()
        
        settings = TokenizationSettings(groq_enabled=False)
        groq = GroqReorderAdapter(settings=settings)
        svc = RecommendationChoiceService(mock_repo, choice_repo, groq)
        result = asyncio.run(svc.reorder_with_groq(BusinessType.RETAIL, "challenge desc long enough", ["A", "B", "C"]))
        assert result == ["A", "B", "C"]  # disabled -> original

    def test_persist_choice_isolated(self):
        mock_repo = MagicMock()
        choice_repo = MagicMock()
        choice_repo.save = AsyncMock()
        svc = RecommendationChoiceService(mock_repo, choice_repo, GroqReorderAdapter(TokenizationSettings(groq_enabled=False)))
        choice = asyncio.run(svc.persist_choice("u1", BusinessType.FINTECH, "description with enough length for validation", "Loyalty Token"))
        assert choice.user_id == "u1"
        assert choice.business_type == BusinessType.FINTECH
        assert choice.tokenization_template == "Loyalty Token"
        choice_repo.save.assert_called_once()

    def test_persist_choice_rejects_blank(self):
        mock_repo = MagicMock()
        choice_repo = MagicMock()
        svc = RecommendationChoiceService(mock_repo, choice_repo, GroqReorderAdapter(TokenizationSettings(groq_enabled=False)))
        with pytest.raises(ValueError):
            asyncio.run(svc.persist_choice(" ", BusinessType.RETAIL, "valid description 12345", "T"))

    def test_persist_creates_custom_option(self):
        mock_repo = MagicMock()
        choice_repo = MagicMock()
        choice_repo.save = AsyncMock()
        svc = RecommendationChoiceService(mock_repo, choice_repo, GroqReorderAdapter(TokenizationSettings(groq_enabled=False)))
        
        choice = asyncio.run(svc.persist_choice("u1", BusinessType.RETAIL, "challenge description long enough xyz", "Nenhuma destas — Criar do Zero"))
        assert choice.tokenization_template == "Nenhuma destas — Criar do Zero"

    def test_persist_choice_dual_writes_to_both_repos(self):
        mock_repo = MagicMock()
        dynamo_repo = MagicMock()
        dynamo_repo.save = AsyncMock()
        postgres_repo = MagicMock()
        postgres_repo.save = AsyncMock()
        svc = RecommendationChoiceService(
            mock_repo, dynamo_repo,
            GroqReorderAdapter(TokenizationSettings(groq_enabled=False)),
            postgres_choices=postgres_repo,
        )
        choice = asyncio.run(svc.persist_choice(
            "u1", BusinessType.FINTECH, "description with enough length for validation", "Loyalty Token"
        ))
        dynamo_repo.save.assert_called_once()
        postgres_repo.save.assert_called_once()
        saved_choice = postgres_repo.save.call_args[0][0]
        assert saved_choice.user_id == "u1"

    def test_persist_choice_postgres_optional(self):
        mock_repo = MagicMock()
        dynamo_repo = MagicMock()
        dynamo_repo.save = AsyncMock()
        svc = RecommendationChoiceService(
            mock_repo, dynamo_repo,
            GroqReorderAdapter(TokenizationSettings(groq_enabled=False)),
            postgres_choices=None,
        )
        choice = asyncio.run(svc.persist_choice(
            "u1", BusinessType.FINTECH, "description with enough length for validation", "Loyalty Token"
        ))
        dynamo_repo.save.assert_called_once()

    def test_persist_choice_postgres_failure_does_not_block(self):
        mock_repo = MagicMock()
        dynamo_repo = MagicMock()
        dynamo_repo.save = AsyncMock()
        postgres_repo = MagicMock()
        postgres_repo.save = AsyncMock(side_effect=Exception("Postgres down"))
        svc = RecommendationChoiceService(
            mock_repo, dynamo_repo,
            GroqReorderAdapter(TokenizationSettings(groq_enabled=False)),
            postgres_choices=postgres_repo,
        )
        choice = asyncio.run(svc.persist_choice(
            "u1", BusinessType.FINTECH, "description with enough length for validation", "Loyalty Token"
        ))
        dynamo_repo.save.assert_called_once()
        assert choice.user_id == "u1"


class TestDynamoDBChoiceRepository:
    def test_to_from_item(self):
        repo = DynamoDBChoiceRepository.__new__(DynamoDBChoiceRepository)
        choice = TokenizationChoice(id="cid", user_id="u1", business_type=BusinessType.RETAIL,
                                    description_tokenization="challenge desc 1234567890", tokenization_template="Loyalty Token")
        item = repo._to_item(choice)
        assert item["user_id"]["S"] == "u1"
        assert item["business_type"]["S"] == "retail"
        assert item["record_type"]["S"] == "choice"
        parsed = repo._from_item(item)
        assert parsed is not None
        assert parsed.user_id == "u1"
        assert parsed.business_type == BusinessType.RETAIL

    def test_created_at_is_epoch_ms(self):
        repo = DynamoDBChoiceRepository.__new__(DynamoDBChoiceRepository)
        choice = TokenizationChoice(
            id="cid", user_id="u1", business_type=BusinessType.RETAIL,
            description_tokenization="challenge desc 1234567890",
            tokenization_template="Loyalty Token",
            chosen_at="2026-01-15T10:30:00+00:00",
        )
        item = repo._to_item(choice)
        created_at = int(item["created_at"]["N"])
        assert created_at > 0
        assert created_at == 1768503000000


class TestPostgresChoiceRepositorySQL:
    def test_sql_uses_parameterized_queries(self):
        
        import inspect
        from app.services.tokenization.infrastructure.persistence.postgres_choice_repository import PostgresChoiceRepository
        source = inspect.getsource(PostgresChoiceRepository.save)
        assert ':user_id' in source or ':id' in source
        assert 'text(' in source
        
        assert 'f"' not in source or '{user_id}' not in source
        source_list = inspect.getsource(PostgresChoiceRepository.list_by_user)
        assert ':user_id' in source_list
        assert 'WHERE user_id = :user_id' in source_list
