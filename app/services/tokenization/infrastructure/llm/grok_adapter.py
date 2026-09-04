from __future__ import annotations

import json
import logging

import httpx

from ...domain.entities.business_type import BusinessType
from ..config.settings import TokenizationSettings
from .ports import LLMReorderPort

logger = logging.getLogger(__name__)


class GrokReorderAdapter:
    
    def __init__(
        self,
        settings: TokenizationSettings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or TokenizationSettings()
        self._client = http_client

    async def reorder(
        self,
        business_type: BusinessType,
        description: str,
        available_templates: list[str],
    ) -> list[str]:
        if not available_templates:
            return []
        if not self._settings.grok_enabled or not self._settings.grok_api_key:
            logger.info("Grok disabled or no api key - return original order")
            return list(available_templates)

        prompt = self._build_prompt(business_type, description, available_templates)
        payload = {
            "model": self._settings.grok_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Voce e especialista em tokenizacao. Ordene templates do MAIS adequado ao MENOS adequado. Responda APENAS JSON array com nomes exatamente como fornecidos. NUNCA invente.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.grok_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        client = self._client or httpx.AsyncClient(timeout=self._settings.grok_timeout_seconds)
        close_client = self._client is None
        try:
            resp = await client.post(self._settings.grok_api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            ordered = self._parse_ordered(content, available_templates)
            allowed = set(available_templates)
            filtered = [n for n in ordered if n in allowed]
            missing = [n for n in available_templates if n not in filtered]
            result = filtered + missing
            logger.info("Grok reorder success: %s -> %s", available_templates, result)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("Grok reorder failed, fallback to original order: %s", exc)
            return list(available_templates)
        finally:
            if close_client:
                await client.aclose()

    def _build_prompt(self, business_type: BusinessType, description: str, templates: list[str]) -> str:
        tmpl_list = ", ".join(f'"{t}"' for t in templates)
        return (
            f"Setor: {business_type.value}. Descricao: {description}. "
            f"Templates disponiveis: [{tmpl_list}]. "
            "Ordene do MAIS adequado ao MENOS adequado. Responda apenas JSON array. NAO invente."
        )

    async def diagnose(self, description: str, industry: str | None = None) -> dict:
        
        if not self._settings.grok_enabled or not self._settings.grok_api_key:
            return {}
        try:
            from app.services.tokenization.domain.entities.journey_enums import ObjectiveCategory

            categories = [c.value for c in ObjectiveCategory]
            prompt = (
                f"Analise o objetivo: '{description}'. Industria: {industry or 'nao informada'}. "
                f"Categorias: {categories}. "
                "Responda apenas JSON com primary_category, confidence, confidence_score, reasoning, secondary_categories, pain_points, goals."
            )
            payload = {
                "model": self._settings.grok_model,
                "messages": [
                    {"role": "system", "content": "Voce e especialista em tokenizacao. Classifique objetivos. Responda apenas JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            headers = {
                "Authorization": f"Bearer {self._settings.grok_api_key.get_secret_value()}",
                "Content-Type": "application/json",
            }
            client = self._client or httpx.AsyncClient(timeout=self._settings.grok_timeout_seconds)
            close_client = self._client is None
            try:
                resp = await client.post(self._settings.grok_api_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = json.loads(content) if content else {}
                if isinstance(parsed, dict) and "primary_category" in parsed:
                    return parsed
                return {}
            finally:
                if close_client:
                    await client.aclose()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Grok diagnose failed: %s", exc)
            return {}

    def _parse_ordered(self, content: str, available: list[str]) -> list[str]:
        if not content:
            return list(available)
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                for key in ("ordered", "templates", "result", "list"):
                    if key in parsed and isinstance(parsed[key], list):
                        return [str(x).strip() for x in parsed[key]]
                for v in parsed.values():
                    if isinstance(v, list):
                        return [str(x).strip() for x in v]
                return list(available)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed]
            return list(available)
        except Exception:  # noqa: BLE001
            try:
                start = content.index("[")
                end = content.rindex("]") + 1
                arr = json.loads(content[start:end])
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr]
            except Exception:  # noqa: BLE001
                pass
            return list(available)
