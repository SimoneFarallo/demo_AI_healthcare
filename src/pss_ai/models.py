from dataclasses import dataclass, field


@dataclass(slots=True)
class UserQuery:
    text: str
    comune: str | None = None
    struttura_privata: str | None = None


@dataclass(slots=True)
class AssistantAnswer:
    answer: str
    matched_services: list[str]
    used_mock: bool
    triage_level: str = "standard"
    confidence: float = 0.0
    suggested_slots: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
