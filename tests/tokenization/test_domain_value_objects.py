import pytest
from uuid import UUID

from app.services.tokenization.domain.value_objects.template_id import TemplateId
from app.services.tokenization.domain.value_objects.category import Category
from app.services.tokenization.domain.value_objects.strategy import Strategy
from app.services.tokenization.domain.value_objects.token_standard import TokenStandard


class TestTemplateId:
    def test_creates_with_default_uuid(self):
        tid = TemplateId()
        assert isinstance(tid.value, UUID)
        assert str(tid) == str(tid.value)

    def test_creates_with_specific_uuid(self):
        specific = UUID("12345678-1234-5678-1234-567812345678")
        tid = TemplateId(value=specific)
        assert tid.value == specific

    def test_frozen(self):
        tid = TemplateId()
        with pytest.raises(AttributeError):
            tid.value = UUID("00000000-0000-0000-0000-000000000000")


class TestCategory:
    def test_creates_valid_category(self):
        cat = Category(code="loyalty", name="Loyalty", description="Loyalty tokens")
        assert cat.code == "loyalty"
        assert cat.name == "Loyalty"

    def test_blank_code_raises(self):
        with pytest.raises(ValueError, match="category code must not be blank"):
            Category(code="  ", name="Loyalty", description="desc")

    def test_blank_name_raises(self):
        with pytest.raises(ValueError, match="category name must not be blank"):
            Category(code="loyalty", name="  ", description="desc")

    def test_frozen(self):
        cat = Category(code="loyalty", name="Loyalty", description="desc")
        with pytest.raises(AttributeError):
            cat.code = "reward"


class TestStrategy:
    def test_creates_valid_strategy(self):
        s = Strategy(
            code="retention",
            name="Retention",
            description="Customer retention",
            business_model="saas",
        )
        assert s.code == "retention"
        assert s.business_model == "saas"

    def test_blank_code_raises(self):
        with pytest.raises(ValueError, match="strategy code must not be blank"):
            Strategy(code="  ", name="Retention", description="desc", business_model="saas")

    def test_blank_name_raises(self):
        with pytest.raises(ValueError, match="strategy name must not be blank"):
            Strategy(code="retention", name="  ", description="desc", business_model="saas")

    def test_blank_business_model_raises(self):
        with pytest.raises(ValueError, match="business_model must not be blank"):
            Strategy(code="retention", name="Retention", description="desc", business_model="  ")

    def test_frozen(self):
        s = Strategy(code="x", name="X", description="d", business_model="b")
        with pytest.raises(AttributeError):
            s.code = "y"


class TestTokenStandard:
    def test_creates_valid_erc20(self):
        ts = TokenStandard(name="ERC20", version="1.0", contract_type="fungible")
        assert ts.name == "ERC20"

    def test_creates_valid_erc721(self):
        ts = TokenStandard(name="ERC721", version="1.0", contract_type="nft")
        assert ts.name == "ERC721"

    def test_creates_valid_erc1155(self):
        ts = TokenStandard(name="ERC1155", version="1.0", contract_type="multi")
        assert ts.name == "ERC1155"

    def test_creates_valid_erc4626(self):
        ts = TokenStandard(name="ERC4626", version="1.0", contract_type="vault")
        assert ts.name == "ERC4626"

    def test_invalid_standard_raises(self):
        with pytest.raises(ValueError, match="invalid token standard"):
            TokenStandard(name="ERC9999", version="1.0", contract_type="unknown")

    def test_frozen(self):
        ts = TokenStandard(name="ERC20", version="1.0", contract_type="fungible")
        with pytest.raises(AttributeError):
            ts.name = "ERC721"
