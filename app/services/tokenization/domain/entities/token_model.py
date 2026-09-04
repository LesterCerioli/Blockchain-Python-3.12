from pydantic import BaseModel, Field, model_validator


class VestingSchedule(BaseModel):
    cliff_months: int = Field(default=0, ge=0, description="Cliff period in months")
    vesting_months: int = Field(default=0, ge=0, description="Total vesting period in months")
    initial_unlock_pct: float = Field(default=0.0, ge=0, le=100, description="Initial unlock percentage")
    periodic_unlock_pct: float = Field(default=0.0, ge=0, le=100, description="Periodic unlock percentage")

    model_config = {"frozen": True}


class EmissionCurve(BaseModel):
    emission_type: str = Field(
        default="fixed",
        description="fixed, decreasing, or increasing",
    )
    rate_per_period: float = Field(default=0.0, ge=0, description="Emission rate per period")
    max_emissions: int | None = Field(default=None, ge=0, description="Maximum total emissions")
    period_duration_days: int = Field(default=30, ge=1, description="Duration of each emission period")

    model_config = {"frozen": True}


class GovernanceConfig(BaseModel):
    governance_enabled: bool = False
    voting_threshold_pct: float = Field(default=50.0, ge=0, le=100, description="Quorum threshold percentage")
    proposal_delay_hours: int = Field(default=0, ge=0, description="Delay before proposal can be voted")
    voting_period_hours: int = Field(default=0, ge=0, description="Duration of voting period")
    executor_roles: list[str] = Field(default_factory=list, description="Roles that can execute proposals")

    model_config = {"frozen": True}


class ComplianceConfig(BaseModel):
    kyc_required: bool = False
    aml_required: bool = False
    accredited_only: bool = False
    jurisdiction_restrictions: list[str] = Field(
        default_factory=list,
        description="ISO country codes where token is restricted",
    )
    max_holders: int | None = Field(default=None, ge=0, description="Maximum number of holders")
    transfer_cooldown_seconds: int = Field(
        default=0, ge=0,
        description="Minimum seconds between transfers",
    )
    whitelist_required: bool = False

    model_config = {"frozen": True}


class TokenModel(BaseModel):
    standard: str
    name: str
    symbol: str
    decimals: int = Field(ge=0, le=18, default=18)
    initial_supply: int = Field(ge=0, default=0)
    max_supply: int | None = Field(default=None, ge=0)
    mintable: bool = False
    burnable: bool = False
    pausable: bool = False
    transferable: bool = True
    metadata_uri: str | None = None

    vesting: VestingSchedule = Field(default_factory=VestingSchedule)
    emission: EmissionCurve = Field(default_factory=EmissionCurve)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_supply_rules(self) -> "TokenModel":
        if self.initial_supply > 0 and self.max_supply is not None:
            if self.initial_supply > self.max_supply:
                raise ValueError(
                    f"initial_supply ({self.initial_supply}) cannot exceed "
                    f"max_supply ({self.max_supply})"
                )
        if self.burnable and not self.mintable:
            raise ValueError("burnable requires mintable to be enabled")
        if self.max_supply is not None and self.max_supply > 0 and self.emission.max_emissions is not None:
            total_possible = self.initial_supply + self.emission.max_emissions
            if total_possible > self.max_supply:
                raise ValueError(
                    f"initial_supply ({self.initial_supply}) + "
                    f"emission.max_emissions ({self.emission.max_emissions}) "
                    f"exceeds max_supply ({self.max_supply})"
                )
        return self

    @property
    def has_supply_cap(self) -> bool:
        return self.max_supply is not None and self.max_supply > 0
