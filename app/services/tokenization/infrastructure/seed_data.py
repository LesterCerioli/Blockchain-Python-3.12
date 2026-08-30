from app.services.tokenization.domain.entities.business_rule import BusinessRule
from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.entities.token_model import TokenModel


def _base_template(
    template_id: str,
    name: str,
    description: str,
    category: str,
    strategy: str,
    token_standard: str,
    target_use_case: str,
    industry: str,
    tags: list[str],
    mintable: bool = False,
    burnable: bool = False,
    max_supply: int | None = None,
    decimals: int = 18,
    business_rules: list[dict] | None = None,
) -> Template:
    rules = [BusinessRule(**r) for r in business_rules] if business_rules else []
    return Template(
        template_id=template_id,
        name=name,
        description=description,
        category=category,
        strategy=strategy,
        token_standard=token_standard,
        status=TemplateStatus.ACTIVE,
        version=TemplateVersion(major=1, minor=0, patch=0),
        metadata=TemplateMetadata(
            author="platform",
            license="MIT",
            audit_status="audited",
            tags=tags,
        ),
        characteristics=TemplateCharacteristics(
            target_use_case=target_use_case,
            industry=industry,
            gas_optimization=True,
        ),
        token_model=TokenModel(
            standard=token_standard,
            name=name,
            symbol=name[:8].upper().replace(" ", ""),
            decimals=decimals,
            mintable=mintable,
            burnable=burnable,
            max_supply=max_supply,
            transferable=True,
        ),
        business_rules=rules,
        created_by="seed",
    )


SEED_TEMPLATES: list[Template] = [
    _base_template(
        template_id="tpl-loyalty-token",
        name="Loyalty Token",
        description="ERC-20 token for customer loyalty programs with earn/burn mechanics",
        category="loyalty",
        strategy="customer-retention",
        token_standard="ERC20",
        target_use_case="customer loyalty rewards",
        industry="retail",
        tags=["loyalty", "rewards", "retail", "customer-retention"],
        mintable=True,
        burnable=True,
        business_rules=[
            {
                "rule_id": "loyalty-earn-rate",
                "name": "Earn Rate",
                "description": "Points earned per unit of currency spent",
                "rule_type": "earning",
                "parameters": {"rate": 0.01, "currency": "USD"},
            },
            {
                "rule_id": "loyalty-expiry",
                "name": "Token Expiry",
                "description": "Tokens expire after 12 months of inactivity",
                "rule_type": "expiry",
                "parameters": {"months": 12},
            },
        ],
    ),
    _base_template(
        template_id="tpl-reward-token",
        name="Reward Token",
        description="ERC-20 token for gamified reward distribution and achievement tracking",
        category="reward",
        strategy="engagement",
        token_standard="ERC20",
        target_use_case="gamified rewards and achievements",
        industry="gaming",
        tags=["reward", "gamification", "engagement", "gaming"],
        mintable=True,
        burnable=True,
        business_rules=[
            {
                "rule_id": "reward-daily-limit",
                "name": "Daily Reward Limit",
                "description": "Maximum tokens claimable per day",
                "rule_type": "limit",
                "parameters": {"max_daily": 1000},
            },
        ],
    ),
    _base_template(
        template_id="tpl-access-token",
        name="Access Token",
        description="ERC-721 NFT for gated access to premium content and services",
        category="access",
        strategy="premium-access",
        token_standard="ERC721",
        target_use_case="gated access and membership",
        industry="media",
        tags=["access", "membership", "nft", "gated-content"],
        max_supply=10000,
        business_rules=[
            {
                "rule_id": "access-tier",
                "name": "Access Tier",
                "description": "Defines access level for the token holder",
                "rule_type": "access-control",
                "parameters": {"tier": "premium", "renewable": True},
            },
        ],
    ),
    _base_template(
        template_id="tpl-participation-token",
        name="Participation Token",
        description="ERC-20 token for community governance and voting participation",
        category="participation",
        strategy="governance",
        token_standard="ERC20",
        target_use_case="governance and voting",
        industry="dao",
        tags=["governance", "voting", "dao", "participation"],
        mintable=True,
        business_rules=[
            {
                "rule_id": "vote-weight",
                "name": "Vote Weight",
                "description": "Each token equals one vote",
                "rule_type": "governance",
                "parameters": {"weight": 1, "quorum_pct": 10},
            },
        ],
    ),
    _base_template(
        template_id="tpl-asset-token",
        name="Asset-Backed Token",
        description="ERC-20 token representing fractional ownership of real-world assets",
        category="asset-rights",
        strategy="asset-tokenization",
        token_standard="ERC20",
        target_use_case="real-world asset tokenization",
        industry="finance",
        tags=["asset", "fractional-ownership", "rwa", "real-estate"],
        decimals=6,
        business_rules=[
            {
                "rule_id": "asset-verification",
                "name": "Asset Verification",
                "description": "Requires verified asset backing before minting",
                "rule_type": "compliance",
                "parameters": {"require_audit": True, "min_asset_value": 100000},
            },
        ],
    ),
    _base_template(
        template_id="tpl-incentive-token",
        name="Incentive Token",
        description="ERC-20 token for referral and behavioral incentive programs",
        category="incentive",
        strategy="behavior-incentive",
        token_standard="ERC20",
        target_use_case="referral and incentive programs",
        industry="fintech",
        tags=["incentive", "referral", "behavior", "fintech"],
        mintable=True,
        burnable=True,
        business_rules=[
            {
                "rule_id": "incentive-referral-bonus",
                "name": "Referral Bonus",
                "description": "Bonus tokens for successful referrals",
                "rule_type": "incentive",
                "parameters": {"referrer_bonus": 50, "referee_bonus": 25},
            },
        ],
    ),
    _base_template(
        template_id="tpl-community-token",
        name="Community Token",
        description="ERC-20 token for community building, social engagement, and ecosystem growth",
        category="community",
        strategy="community-building",
        token_standard="ERC20",
        target_use_case="community engagement and social tokens",
        industry="social",
        tags=["community", "social", "engagement", "creator-economy"],
        mintable=True,
        max_supply=1000000000,
        business_rules=[
            {
                "rule_id": "community-staking-reward",
                "name": "Staking Reward",
                "description": "APY for staking community tokens",
                "rule_type": "staking",
                "parameters": {"apy_pct": 5.0, "lock_period_days": 30},
            },
        ],
    ),
    _base_template(
        template_id="tpl-financing-token",
        name="Financing Token",
        description="ERC-20 token for DeFi lending, borrowing, and yield-bearing positions",
        category="financing",
        strategy="defi-lending",
        token_standard="ERC20",
        target_use_case="decentralized finance lending and borrowing",
        industry="defi",
        tags=["defi", "lending", "borrowing", "yield", "financing"],
        decimals=18,
        business_rules=[
            {
                "rule_id": "financing-collateral-ratio",
                "name": "Collateral Ratio",
                "description": "Minimum collateralization ratio for borrowing",
                "rule_type": "risk-management",
                "parameters": {"min_collateral_ratio": 150, "liquidation_threshold": 120},
            },
        ],
    ),
    _base_template(
        template_id="tpl-ecosystem-token",
        name="Ecosystem Token",
        description="ERC-20 token serving as the native utility token of a blockchain ecosystem",
        category="ecosystem",
        strategy="ecosystem-utility",
        token_standard="ERC20",
        target_use_case="platform utility and ecosystem governance",
        industry="blockchain",
        tags=["ecosystem", "utility", "platform", "infrastructure"],
        mintable=True,
        burnable=True,
        max_supply=10000000000,
        business_rules=[
            {
                "rule_id": "ecosystem-fee-discount",
                "name": "Fee Discount",
                "description": "Discount on platform fees based on token holdings",
                "rule_type": "utility",
                "parameters": {"min_holdings": 1000, "discount_pct": 10},
            },
        ],
    ),
    _base_template(
        template_id="tpl-erc1155-multi",
        name="Multi-Token Collection",
        description="ERC-1155 multi-token for representing multiple asset types in a single contract",
        category="asset-rights",
        strategy="multi-asset",
        token_standard="ERC1155",
        target_use_case="multi-asset collections and game items",
        industry="gaming",
        tags=["erc1155", "multi-token", "game-items", "collectibles"],
        business_rules=[
            {
                "rule_id": "multi-token-batch",
                "name": "Batch Transfer",
                "description": "Supports batch transfers of multiple token IDs",
                "rule_type": "transfer",
                "parameters": {"max_batch_size": 100},
            },
        ],
    ),
    _base_template(
        template_id="tpl-erc4626-vault",
        name="Tokenized Vault",
        description="ERC-4626 tokenized vault for standardized yield-bearing deposit accounts",
        category="financing",
        strategy="yield-vault",
        token_standard="ERC4626",
        target_use_case="tokenized yield vaults and structured products",
        industry="defi",
        tags=["erc4626", "vault", "yield", "structured-product"],
        decimals=18,
        business_rules=[
            {
                "rule_id": "vault-deposit-min",
                "name": "Minimum Deposit",
                "description": "Minimum deposit amount for vault entry",
                "rule_type": "access-control",
                "parameters": {"min_deposit": 100, "currency": "USDC"},
            },
        ],
    ),
]


async def seed_catalog(email: str, service) -> list[Template]:
    """Seed the catalog with initial templates."""
    from app.services.tokenization.domain.exceptions import TemplateNotFoundError

    seeded = []
    for template in SEED_TEMPLATES:
        try:
            existing = await service.get_template(email, template.name)
        except TemplateNotFoundError:
            existing = None
        if existing is None:
            await service._repository.create(template)
            seeded.append(template)
    return seeded
