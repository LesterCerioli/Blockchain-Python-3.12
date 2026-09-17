from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class TemplateId:
    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)
