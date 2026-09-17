from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Strategy:
    code: str
    name: str
    description: str
    business_model: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("strategy code must not be blank")
        if not self.name.strip():
            raise ValueError("strategy name must not be blank")
        if not self.business_model.strip():
            raise ValueError("business_model must not be blank")
