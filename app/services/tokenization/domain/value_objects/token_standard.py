from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenStandard:
    name: str
    version: str
    contract_type: str

    def __post_init__(self) -> None:
        valid_standards = {"ERC20", "ERC721", "ERC1155", "ERC4626"}
        if self.name not in valid_standards:
            raise ValueError(
                f"invalid token standard: {self.name}. "
                f"must be one of {', '.join(sorted(valid_standards))}"
            )
