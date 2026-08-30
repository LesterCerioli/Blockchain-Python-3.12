from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Category:
    code: str
    name: str
    description: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("category code must not be blank")
        if not self.name.strip():
            raise ValueError("category name must not be blank")
