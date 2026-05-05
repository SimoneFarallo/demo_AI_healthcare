from pss_ai.models import UserQuery
from pss_ai.orchestrator import PSSAssistant


class DummySettings:
    data_file = "data/final_data_cleaned.csv"
    ai_mode = "mock"
    openai_api_key = None
    openai_model = "gpt-4o-mini"


def test_orchestrator_mock_run():
    assistant = PSSAssistant(DummySettings())  # type: ignore[arg-type]
    out = assistant.run(UserQuery(text="dolore toracico"), extracted_terms=["VISITA"])
    assert out.used_mock is True
    assert out.triage_level in {"high", "medium", "low", "standard"}
    assert 0 <= out.confidence <= 1
    assert len(out.suggested_slots) == 3
    assert "fuzzy_matching_done" in out.trace
