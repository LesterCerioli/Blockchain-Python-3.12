from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized.startswith("0x") or len(normalized) != 42:
            raise ValueError(f"Invalid Ethereum address: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
