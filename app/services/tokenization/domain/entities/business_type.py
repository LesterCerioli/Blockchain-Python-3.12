from enum import Enum


class BusinessType(str, Enum):
    RETAIL = "retail"
    FINTECH = "fintech"
    GAMING = "gaming"
    REAL_ESTATE = "real_estate"
    MEDIA = "media"
    DAO = "dao"
    DEFI = "defi"
    SOCIAL = "social"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    LOGISTICS = "logistics"
    ENERGY = "energy"
    FINANCE = "finance"
    BLOCKCHAIN = "blockchain"
    OTHER = "other"

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]
