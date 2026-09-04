from __future__ import annotations

import json
import logging

import httpx

from ...domain.entities.business_type import BusinessType
from ..config.settings import TokenizationSettings
from .ports import LLMReorderPort

logger = logging.getLogger(__name__)


class GroqReorderAdapter:
    
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
        if not self._settings.groq_enabled or not self._settings.groq_api_key:
            logger.info("Groq disabled or no api key - return original order")
            return list(available_templates)

        prompt = self._build_prompt(business_type, description, available_templates)
        payload = {
            "model": self._settings.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um especialista em tokenização. Receberá um setor, "
                        "uma descrição e uma lista de templates disponíveis. "
                        "Ordene do MAIS adequado ao MENOS adequado. "
                        "Responda APENAS com JSON array de nomes exatamente como fornecidos. "
                        "NUNCA invente ou crie template novo."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._settings.groq_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        client = self._client or httpx.AsyncClient(
            timeout=self._settings.groq_timeout_seconds
        )
        close_client = self._client is None
        try:
            resp = await client.post(self._settings.groq_api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            ordered = self._parse_ordered(content, available_templates)
            
            allowed = set(available_templates)
            filtered = [n for n in ordered if n in allowed]
            
            missing = [n for n in available_templates if n not in filtered]
            result = filtered + missing
            logger.info("Groq reorder success: %s -> %s", available_templates, result)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq reorder failed, fallback to original order: %s", exc)
            return list(available_templates)
        finally:
            if close_client:
                await client.aclose()

    def _build_prompt(
        self,
        business_type: BusinessType,
        description: str,
        templates: list[str],
    ) -> str:
        tmpl_list = ", ".join(f'"{t}"' for t in templates)
        return (
            f"Setor do usuário: {business_type.value}. "
            f"Descrição da necessidade: {description}. "
            f"Templates disponíveis para este setor: [{tmpl_list}]. "
            "Ordene do MAIS adequado ao MENOS adequado. "
            "Responda apenas com a lista ordenada JSON array. NÃO invente opções novas."
        )

    async def diagnose(self, description: str, industry: str | None = None) -> dict:
        
        if not self._settings.groq_enabled or not self._settings.groq_api_key:
            return {}
        try:
            from app.services.tokenization.domain.entities.journey_enums import ObjectiveCategory

            categories = [c.value for c in ObjectiveCategory]
            prompt = (
                f"Analise o objetivo de negócio: '{description}'. "
                f"Indústria: {industry or 'não informada'}. "
                f"Classifique em uma das categorias: {categories}. "
                "Responda APENAS JSON com keys: primary_category, confidence (high/medium/low), "
                "confidence_score (0-1), reasoning (string), secondary_categories (array), pain_points (array), goals (array)."
            )
            payload = {
                "model": self._settings.groq_model,
                "messages": [
                    {"role": "system", "content": "Você é especialista em tokenização. Classifique objetivos de negócio. Responda apenas JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }
            headers = {
                "Authorization": f"Bearer {self._settings.groq_api_key.get_secret_value()}",
                "Content-Type": "application/json",
            }
            client = self._client or httpx.AsyncClient(timeout=self._settings.groq_timeout_seconds)
            close_client = self._client is None
            try:
                resp = await client.post(self._settings.groq_api_url, json=payload, headers=headers)
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
            logger.warning("Groq diagnose failed: %s", exc)
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
            # Try to extract JSON array substring
            try:
                start = content.index("[")
                end = content.rindex("]") + 1
                arr = json.loads(content[start:end])
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr]
            except Exception:  # noqa: BLE001
                pass
            return list(available)
