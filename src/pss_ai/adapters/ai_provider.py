from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def answer(self, prompt: str) -> str:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def answer(self, prompt: str) -> str:
        return (
            "[MOCK] Ho analizzato la richiesta in modo sicuro. "
            "Per la versione online possiamo usare un modello reale mantenendo gli stessi endpoint. "
            f"Estratto richiesta: {prompt[:180]}"
        )


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.api_key = api_key

    def answer(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed. Install requirements.txt") from exc

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(model=self.model, input=prompt, temperature=0.2)
        return response.output_text


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest") -> None:
        self.model = model
        self.api_key = api_key

    def answer(self, prompt: str) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package not installed. Install requirements.txt") from exc

        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        blocks = msg.content or []
        text_parts = [b.text for b in blocks if getattr(b, "type", "") == "text"]
        return "\n".join(text_parts).strip() or "Nessuna risposta dal modello."
