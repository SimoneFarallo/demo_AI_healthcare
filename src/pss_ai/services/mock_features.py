from __future__ import annotations

from datetime import datetime, timedelta


URGENT_KEYWORDS = {
    "dolore toracico": "high",
    "dispnea": "high",
    "sangue": "high",
    "tachicardia": "medium",
    "febbre": "medium",
    "controllo": "low",
}


def estimate_triage_level(text: str) -> tuple[str, float]:
    lowered = text.lower()
    level = "standard"
    score = 0.55
    for keyword, keyword_level in URGENT_KEYWORDS.items():
        if keyword in lowered:
            level = keyword_level
            score = 0.9 if keyword_level == "high" else 0.75 if keyword_level == "medium" else 0.6
            break
    return level, score


def suggest_mock_slots(base_date: datetime | None = None, count: int = 3) -> list[str]:
    now = base_date or datetime.now()
    slots: list[str] = []
    for i in range(1, count + 1):
        day = now + timedelta(days=i)
        slots.append(day.strftime("%Y-%m-%d") + " 09:30")
    return slots


def build_trace(has_terms: bool, filters_applied: bool, used_mock: bool) -> list[str]:
    return [
        "input_received",
        "terms_extracted" if has_terms else "terms_missing",
        "dataset_filtered" if filters_applied else "dataset_unfiltered",
        "fuzzy_matching_done",
        "mock_llm_response" if used_mock else "real_llm_response",
    ]
