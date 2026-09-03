import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.tokenization.domain.entities.token_model import (
    ComplianceConfig,
    EmissionCurve,
    GovernanceConfig,
    TokenModel,
    VestingSchedule,
)


class TestTokenModelBasic:
    def test_default_values(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN")
        assert tm.standard == "ERC20"
        assert tm.decimals == 18
        assert tm.initial_supply == 0
        assert tm.max_supply is None
        assert tm.mintable is False
        assert tm.burnable is False
        assert tm.pausable is False
        assert tm.transferable is True

    def test_has_supply_cap_true(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN", max_supply=1000)
        assert tm.has_supply_cap is True

    def test_has_supply_cap_false(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN")
        assert tm.has_supply_cap is False

    def test_frozen_model(self):
        tm = TokenModel(standard="ERC20", name="Token", symbol="TKN")
        with pytest.raises(ValidationError):
            tm.name = "Other"


class TestTokenModelValidation:
    def test_initial_supply_exceeds_max_supply_raises(self):
        with pytest.raises(ValidationError, match="initial_supply.*cannot exceed"):
            TokenModel(
                standard="ERC20",
                name="Token",
                symbol="TKN",
                initial_supply=2000,
                max_supply=1000,
            )

    def test_burnable_without_mintable_raises(self):
        with pytest.raises(ValidationError, match="burnable requires mintable"):
            TokenModel(
                standard="ERC20",
                name="Token",
                symbol="TKN",
                burnable=True,
                mintable=False,
            )

    def test_burnable_with_mintable_ok(self):
        tm = TokenModel(
            standard="ERC20",
            name="Token",
            symbol="TKN",
            burnable=True,
            mintable=True,
        )
        assert tm.burnable is True
        assert tm.mintable is True

    def test_emission_exceeds_max_supply_raises(self):
        with pytest.raises(ValidationError, match="exceeds max_supply"):
            TokenModel(
                standard="ERC20",
                name="Token",
                symbol="TKN",
                initial_supply=800,
                max_supply=1000,
                emission=EmissionCurve(max_emissions=300),
            )

    def test_valid_emission_within_max_supply(self):
        tm = TokenModel(
            standard="ERC20",
            name="Token",
            symbol="TKN",
            initial_supply=500,
            max_supply=1000,
            emission=EmissionCurve(max_emissions=400),
        )
        assert tm.initial_supply == 500


class TestVestingSchedule:
    def test_default_values(self):
        v = VestingSchedule()
        assert v.cliff_months == 0
        assert v.vesting_months == 0
        assert v.initial_unlock_pct == 0.0
        assert v.periodic_unlock_pct == 0.0

    def test_frozen(self):
        v = VestingSchedule()
        with pytest.raises(ValidationError):
            v.cliff_months = 1


class TestEmissionCurve:
    def test_default_values(self):
        e = EmissionCurve()
        assert e.emission_type == "fixed"
        assert e.rate_per_period == 0.0
        assert e.max_emissions is None

    def test_valid_emission_type(self):
        e = EmissionCurve(emission_type="decreasing")
        assert e.emission_type == "decreasing"


class TestGovernanceConfig:
    def test_default_values(self):
        g = GovernanceConfig()
        assert g.governance_enabled is False
        assert g.voting_threshold_pct == 50.0

    def test_governance_enabled(self):
        g = GovernanceConfig(
            governance_enabled=True,
            voting_threshold_pct=60.0,
            voting_period_hours=72,
        )
        assert g.governance_enabled is True


class TestComplianceConfig:
    def test_default_values(self):
        c = ComplianceConfig()
        assert c.kyc_required is False
        assert c.aml_required is False
        assert c.jurisdiction_restrictions == []

    def test_with_restrictions(self):
        c = ComplianceConfig(
            kyc_required=True,
            jurisdiction_restrictions=["US", "CN"],
            max_holders=1000,
        )
        assert c.kyc_required is True
        assert len(c.jurisdiction_restrictions) == 2


class TestTokenModelWithAllConfig:
    def test_full_configuration(self):
        tm = TokenModel(
            standard="ERC20",
            name="Governance Token",
            symbol="GOV",
            decimals=18,
            initial_supply=1000000,
            max_supply=10000000,
            mintable=True,
            burnable=True,
            vesting=VestingSchedule(
                cliff_months=6,
                vesting_months=24,
                initial_unlock_pct=10.0,
            ),
            emission=EmissionCurve(
                emission_type="decreasing",
                rate_per_period=5.0,
                max_emissions=5000000,
            ),
            governance=GovernanceConfig(
                governance_enabled=True,
                voting_threshold_pct=51.0,
                voting_period_hours=168,
                executor_roles=["multisig", "dao"],
            ),
            compliance=ComplianceConfig(
                kyc_required=True,
                aml_required=True,
                jurisdiction_restrictions=["US"],
                max_holders=5000,
            ),
        )
        assert tm.has_supply_cap is True
        assert tm.vesting.cliff_months == 6
        assert tm.emission.emission_type == "decreasing"
        assert tm.governance.governance_enabled is True
        assert tm.compliance.kyc_required is True
