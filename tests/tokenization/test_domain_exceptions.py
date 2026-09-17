import pytest

from app.services.tokenization.domain.exceptions import (
    ApprovalRequiredError,
    CatalogSearchError,
    InvalidTemplateVersionError,
    TemplateAlreadyExistsError,
    TemplateNotArchivableError,
    TemplateNotEditableError,
    TemplateNotFoundError,
    TemplateValidationError,
    TokenizationError,
)


class TestTokenizationErrorHierarchy:
    def test_base_exception(self):
        exc = TokenizationError("test error")
        assert str(exc) == "test error"
        assert isinstance(exc, Exception)

    def test_template_not_found(self):
        exc = TemplateNotFoundError("tpl-1")
        assert "tpl-1" in str(exc)
        assert exc.template_id == "tpl-1"
        assert isinstance(exc, TokenizationError)

    def test_template_already_exists(self):
        exc = TemplateAlreadyExistsError("My Token")
        assert "My Token" in str(exc)
        assert exc.name == "My Token"
        assert isinstance(exc, TokenizationError)

    def test_template_not_editable(self):
        exc = TemplateNotEditableError("tpl-1", "active")
        assert "tpl-1" in str(exc)
        assert "active" in str(exc)
        assert exc.status == "active"
        assert isinstance(exc, TokenizationError)

    def test_template_not_archivable(self):
        exc = TemplateNotArchivableError("tpl-1", "draft")
        assert "tpl-1" in str(exc)
        assert "draft" in str(exc)
        assert isinstance(exc, TokenizationError)

    def test_invalid_template_version(self):
        exc = InvalidTemplateVersionError("1.0.0", "major")
        assert "1.0.0" in str(exc)
        assert "major" in str(exc)
        assert isinstance(exc, TokenizationError)

    def test_approval_required(self):
        exc = ApprovalRequiredError("tpl-1")
        assert "tpl-1" in str(exc)
        assert isinstance(exc, TokenizationError)

    def test_template_validation_error(self):
        exc = TemplateValidationError("name", "must not be empty")
        assert "name" in str(exc)
        assert "must not be empty" in str(exc)
        assert exc.field == "name"
        assert isinstance(exc, TokenizationError)

    def test_catalog_search_error(self):
        exc = CatalogSearchError("search failed")
        assert "search failed" in str(exc)
        assert isinstance(exc, TokenizationError)
