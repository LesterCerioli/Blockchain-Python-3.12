from enum import Enum

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    TRANSFER_RESTRICTION = "transfer_restriction"
    EARNING = "earning"
    STAKING = "staking"
    EXPIRY = "expiry"
    WHITELIST = "whitelist"
    KYCAML = "kycaml"
    VESTING = "vesting"
    COMPLIANCE = "compliance"
    GOVERNANCE = "governance"
    CUSTOM = "custom"


class BusinessRule(BaseModel):
    rule_id: str
    name: str
    description: str
    rule_type: str
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=0, description="Rule execution priority (higher = first)")
    enabled: bool = True

    model_config = {"frozen": True}

    def validate_parameters(self) -> None:
        required = {
            RuleType.EARNING: {"rate", "period"},
            RuleType.STAKING: {"min_stake", "reward_rate"},
            RuleType.EXPIRY: {"months"},
            RuleType.VESTING: {"cliff_months", "vesting_months"},
            RuleType.TRANSFER_RESTRICTION: {"restriction_type"},
            RuleType.WHITELIST: {"list_type"},
            RuleType.KYCAML: {"level"},
        }
        expected = required.get(RuleType(self.rule_type), set())
        missing = expected - set(self.parameters.keys())
        if missing:
            raise ValueError(
                f"Rule type '{self.rule_type}' requires parameters: {missing}"
            )
