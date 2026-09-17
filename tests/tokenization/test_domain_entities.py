import pytest
from pydantic import ValidationError

from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.entities.business_rule import BusinessRule
from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
from app.services.tokenization.domain.entities.token_model import TokenModel
from app.services.tokenization.domain.entities.template import Template


class TestTemplateStatus:
    def test_all_statuses_exist(self):
        assert TemplateStatus.DRAFT == "draft"
        assert TemplateStatus.PENDING_REVIEW == "pending_review"
        assert TemplateStatus.APPROVED == "approved"
        assert TemplateStatus.ACTIVE == "active"
        assert TemplateStatus.DEPRECATED == "deprecated"
        assert TemplateStatus.ARCHIVED == "archived"


class TestTemplateVersion:
    def test_creates_valid_version(self):
        v = TemplateVersion(major=1, minor=2, patch=3)
        assert v.to_string() == "1.2.3"

    def test_to_string_default(self):
        v = TemplateVersion(major=1, minor=0, patch=0)
        assert v.to_string() == "1.0.0"

    def test_is_compatible_with_same_major_higher_minor(self):
        v1 = TemplateVersion(major=1, minor=0, patch=0)
        v2 = TemplateVersion(major=1, minor=2, patch=0)
        assert v1.is_compatible_with(v2) is True

    def test_is_compatible_with_different_major(self):
        v1 = TemplateVersion(major=1, minor=0, patch=0)
        v2 = TemplateVersion(major=2, minor=0, patch=0)
        assert v1.is_compatible_with(v2) is False

    def test_major_ge_1(self):
        with pytest.raises(Exception):
            TemplateVersion(major=0, minor=0, patch=0)

    def test_frozen(self):
        v = TemplateVersion(major=1, minor=0, patch=0)
        with pytest.raises(ValidationError):
            v.major = 2


class TestBusinessRule:
    def test_creates_valid_rule(self):
        r = BusinessRule(
            rule_id="r1",
            name="Rate Limit",
            description="Max 100 tokens per day",
            rule_type="limit",
            parameters={"max": 100},
        )
        assert r.rule_id == "r1"
        assert r.parameters["max"] == 100

    def test_frozen(self):
        r = BusinessRule(rule_id="r1", name="X", description="d", rule_type="t")
        with pytest.raises(ValidationError):
            r.rule_id = "r2"


class TestTemplateCharacteristics:
    def test_creates_valid(self):
        tc = TemplateCharacteristics(
            target_use_case="loyalty", industry="retail"
        )
        assert tc.target_use_case == "loyalty"
        assert tc.cross_chain is False

    def test_frozen(self):
        tc = TemplateCharacteristics(target_use_case="x", industry="y")
        with pytest.raises(ValidationError):
            tc.industry = "z"


class TestTemplateMetadata:
    def test_creates_defaults(self):
        m = TemplateMetadata()
        assert m.author == "platform"
        assert m.license == "MIT"
        assert m.tags == []

    def test_frozen(self):
        m = TemplateMetadata()
        with pytest.raises(ValidationError):
            m.author = "other"


class TestTokenModel:
    def test_creates_valid_erc20(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN")
        assert tm.decimals == 18
        assert tm.mintable is False

    def test_has_supply_cap_true(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN", max_supply=1000)
        assert tm.has_supply_cap is True

    def test_has_supply_cap_false(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN")
        assert tm.has_supply_cap is False

    def test_decimals_range(self):
        with pytest.raises(Exception):
            TokenModel(standard="ERC20", name="Token", symbol="TKN", decimals=19)

    def test_frozen(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN")
        with pytest.raises(ValidationError):
            tm.symbol = "XYZ"


class TestTemplate:
    def _make_template(self, **overrides) -> Template:
        defaults = dict(
            template_id="tpl-1",
            name="Test Template",
            description="A test template",
            category="loyalty",
            strategy="retention",
            token_standard="ERC20",
        )
        defaults.update(overrides)
        return Template(**defaults)

    def test_creates_with_defaults(self):
        t = self._make_template()
        assert t.template_id == "tpl-1"
        assert t.status == TemplateStatus.DRAFT
        assert t.version.to_string() == "1.0.0"
        assert t.is_editable is True
        assert t.is_active is False
        assert t.is_archived is False

    def test_name_not_empty(self):
        with pytest.raises(Exception):
            self._make_template(name="  ")

    def test_category_not_empty(self):
        with pytest.raises(Exception):
            self._make_template(category="  ")

    def test_category_lowercased(self):
        t = self._make_template(category="LOYALTY")
        assert t.category == "loyalty"

    def test_is_editable_for_draft(self):
        t = self._make_template(status=TemplateStatus.DRAFT)
        assert t.is_editable is True

    def test_is_editable_for_pending_review(self):
        t = self._make_template(status=TemplateStatus.PENDING_REVIEW)
        assert t.is_editable is True

    def test_not_editable_for_active(self):
        t = self._make_template(status=TemplateStatus.ACTIVE)
        assert t.is_editable is False

    def test_is_active(self):
        t = self._make_template(status=TemplateStatus.ACTIVE)
        assert t.is_active is True

    def test_is_archived(self):
        t = self._make_template(status=TemplateStatus.ARCHIVED)
        assert t.is_archived is True

    def test_frozen(self):
        t = self._make_template()
        with pytest.raises(ValidationError):
            t.name = "Changed"
