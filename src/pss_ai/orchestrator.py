from __future__ import annotations

import logging

from .config import AppSettings
from .models import AssistantAnswer, UserQuery
from .services.dataset_service import filter_dataset, load_dataset
from .services.search_service import match_service_codes
from .services.mock_features import build_trace, estimate_triage_level, suggest_mock_slots
from .adapters.ai_provider import AIProvider, AnthropicProvider, MockAIProvider, OpenAIProvider

logger = logging.getLogger(__name__)


class PSSAssistant:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.dataset = load_dataset(settings.data_file)
        self.ai = self._build_ai_provider(settings)

    def _build_ai_provider(self, settings: AppSettings) -> AIProvider:
        mode = settings.ai_mode.lower().strip()
        model_hint = (settings.openai_model or "").lower()

        has_openai = bool(settings.openai_api_key)
        has_anthropic = bool(settings.anthropic_api_key)
        openai_key_looks_anthropic = bool(settings.openai_api_key and settings.openai_api_key.startswith("sk-ant-"))
        wants_claude = model_hint.startswith("claude")

        if mode == "auto":
            if has_anthropic:
                logger.info("AI_MODE=auto: using Anthropic provider with ANTHROPIC_API_KEY")
                return AnthropicProvider(api_key=settings.anthropic_api_key or "", model=settings.anthropic_model)
            if openai_key_looks_anthropic or wants_claude:
                logger.info("AI_MODE=auto: detected Claude config, using Anthropic provider")
                return AnthropicProvider(api_key=settings.openai_api_key or "", model=settings.openai_model)
            if has_openai:
                logger.info("AI_MODE=auto: using OpenAI provider (%s)", settings.openai_model)
                return OpenAIProvider(api_key=settings.openai_api_key or "", model=settings.openai_model)
            logger.warning("AI_MODE=auto: no API key found, fallback to MOCK provider")
            return MockAIProvider()

        if mode == "anthropic":
            key = settings.anthropic_api_key or settings.openai_api_key
            model = settings.anthropic_model if settings.anthropic_api_key else settings.openai_model
            if not key:
                raise ValueError("AI_MODE=anthropic but no Anthropic key found")
            logger.info("Using Anthropic provider with model %s", model)
            return AnthropicProvider(api_key=key, model=model)

        if mode == "openai":
            if not settings.openai_api_key:
                raise ValueError("AI_MODE=openai but OPENAI_API_KEY is missing")
            if openai_key_looks_anthropic or wants_claude:
                raise ValueError("AI_MODE=openai is not compatible with Anthropic key/model. Use AI_MODE=anthropic or auto.")
            logger.info("Using OpenAI provider with model %s", settings.openai_model)
            return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)

        logger.info("Using MOCK AI provider")
        return MockAIProvider()

    def run(self, query: UserQuery, extracted_terms: list[str] | None = None) -> AssistantAnswer:
        filters_applied = bool(query.comune or query.struttura_privata)
        filtered = filter_dataset(self.dataset, comune=query.comune, struttura_privata=query.struttura_privata)
        terms = extracted_terms or []
        matching_terms = terms if terms else [query.text]
        matches = match_service_codes(filtered, matching_terms)

        triage_level, base_confidence = estimate_triage_level(query.text)
        match_boost = min(0.35, 0.05 * len(matches))
        confidence = round(min(0.98, base_confidence + match_boost), 2)

        prompt = (
            "Contesto: assistente sanitario Lombardia. "
            f"Domanda utente: {query.text}. "
            f"Filtri: comune={query.comune}, privata={query.struttura_privata}. "
            f"Prestazioni trovate: {matches[:8]}. "
            f"Triage stimato: {triage_level}."
        )

        try:
            answer = self.ai.answer(prompt)
        except Exception as exc:
            logger.exception("LLM provider error, fallback demo response: %s", exc)
            answer = (
                "[FALLBACK DEMO] Provider AI temporaneamente non disponibile. "
                "Ti mostro una risposta simulata coerente con i dati locali."
            )

        used_mock = isinstance(self.ai, MockAIProvider)

        return AssistantAnswer(
            answer=answer,
            matched_services=matches,
            used_mock=used_mock,
            triage_level=triage_level,
            confidence=confidence,
            suggested_slots=suggest_mock_slots(count=3),
            trace=build_trace(bool(terms), filters_applied, used_mock),
        )
