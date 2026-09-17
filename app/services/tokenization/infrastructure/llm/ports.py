from __future__ import annotations

from typing import Protocol

from ...domain.entities.business_type import BusinessType


class LLMReorderPort(Protocol):
    async def reorder(
        self,
        business_type: BusinessType,
        description: str,
        available_templates: list[str],
    ) -> list[str]:
        ...


class LLMDiagnosisPort(Protocol):
    
    async def diagnose(
        self,
        description: str,
        industry: str | None = None,
    ) -> dict:
        """Return dict with keys: primary_category, confidence, confidence_score, reasoning, secondary_categories, pain_points, goals.

        Must not raise - caller falls back to keyword logic on failure.
        """
        ...
