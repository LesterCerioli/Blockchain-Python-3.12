class TokenizationError(Exception):
    
    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class TemplateNotFoundError(TokenizationError):
    def __init__(self, template_id: str) -> None:
        super().__init__(f"Template not found: {template_id}")
        self.template_id = template_id


class TemplateAlreadyExistsError(TokenizationError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Template already exists with name: {name}")
        self.name = name


class TemplateNotEditableError(TokenizationError):
    def __init__(self, template_id: str, status: str) -> None:
        super().__init__(
            f"Template {template_id} is not editable in status: {status}"
        )
        self.template_id = template_id
        self.status = status


class TemplateNotArchivableError(TokenizationError):
    def __init__(self, template_id: str, status: str) -> None:
        super().__init__(
            f"Template {template_id} cannot be archived in status: {status}"
        )
        self.template_id = template_id
        self.status = status


class InvalidTemplateVersionError(TokenizationError):
    def __init__(self, current_version: str, target_version: str) -> None:
        super().__init__(
            f"Invalid version bump from {current_version} to {target_version}"
        )
        self.current_version = current_version
        self.target_version = target_version


class ApprovalRequiredError(TokenizationError):
    def __init__(self, template_id: str) -> None:
        super().__init__(
            f"Template {template_id} requires approval before activation"
        )
        self.template_id = template_id


class TemplateValidationError(TokenizationError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation error on {field}: {message}")
        self.field = field
        self.message = message


class CatalogSearchError(TokenizationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
