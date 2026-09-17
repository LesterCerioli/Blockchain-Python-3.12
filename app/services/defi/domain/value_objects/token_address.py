from dataclasses import dataclass

from web3 import Web3


@dataclass(frozen=True)
class TokenAddress:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.startswith("0x"):
            raise ValueError(f"Invalid token address: {self.value!r}")
        try:
            checksummed = Web3.to_checksum_address(self.value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid token address: {self.value!r}") from exc
        object.__setattr__(self, "value", checksummed)

    def __str__(self) -> str:
        return self.value
