from __future__ import annotations

from ..config.settings import TokenizationSettings
from .groq_adapter import GroqReorderAdapter
from .grok_adapter import GrokReorderAdapter
from .ports import LLMDiagnosisPort, LLMReorderPort

SUPPORTED_PROVIDERS = ("groq", "grok")


def get_reorder_adapter(
    settings: TokenizationSettings | None = None,
) -> LLMReorderPort:
    
    settings = settings or TokenizationSettings()
    provider = (settings.llm_provider or "groq").lower()
    if provider == "groq":
        return GroqReorderAdapter(settings)  # type: ignore[return-value]
    if provider == "grok":
        return GrokReorderAdapter(settings)  # type: ignore[return-value]
    raise ValueError(f"Unsupported LLM provider: {provider!r}. Supported: {', '.join(SUPPORTED_PROVIDERS)}.")


def get_diagnosis_adapter(
    settings: TokenizationSettings | None = None,
) -> LLMDiagnosisPort:
    
    settings = settings or TokenizationSettings()
    provider = (settings.llm_provider or "groq").lower()
    if provider == "groq":
        return GroqReorderAdapter(settings)  # type: ignore[return-value]
    if provider == "grok":
        return GrokReorderAdapter(settings)  # type: ignore[return-value]
    raise ValueError(f"Unsupported LLM provider: {provider!r}. Supported: {', '.join(SUPPORTED_PROVIDERS)}.")
