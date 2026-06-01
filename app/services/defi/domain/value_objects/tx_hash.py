import re
from dataclasses import dataclass

_TX_HASH_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class TxHash:
    value: str

    def __post_init__(self) -> None:
        if not _TX_HASH_PATTERN.match(self.value):
            raise ValueError(
                f"Invalid transaction hash: {self.value!r}. "
                "Expected 0x followed by 64 hex characters."
            )
        object.__setattr__(self, "value", self.value.lower())

    def __str__(self) -> str:
        return self.value
