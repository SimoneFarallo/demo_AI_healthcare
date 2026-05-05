from __future__ import annotations

from rapidfuzz import fuzz, process
import pandas as pd


DEMO_KEYWORD_FALLBACKS = {
    "cardio": ["VISITA CARDIOLOGICA", "ELETTROCARDIOGRAMMA"],
    "torac": ["VISITA CARDIOLOGICA", "ECG DINAMICO"],
    "piede": ["VISITA ORTOPEDICA", "VISITA PODOLOGICA", "RX PIEDE"],
    "cavig": ["VISITA ORTOPEDICA", "RX CAVIGLIA"],
    "trauma": ["VISITA ORTOPEDICA", "RADIOGRAFIA", "VISITA FISIATRICA"],
    "ortoped": ["VISITA ORTOPEDICA", "RX ARTI INFERIORI"],
    "podolog": ["VISITA PODOLOGICA"],
    "frattur": ["VISITA ORTOPEDICA", "RADIOGRAFIA", "PRONTO SOCCORSO ORTOPEDICO"],
    "gonf": ["VISITA ORTOPEDICA", "ECOGRAFIA MUSCOLOTENDINEA"],
    "derma": ["VISITA DERMATOLOGICA"],
    "ocul": ["VISITA OCULISTICA"],
    "gine": ["VISITA GINECOLOGICA"],
    "neuro": ["VISITA NEUROLOGICA"],
    "sangue": ["ESAMI DEL SANGUE", "EMOCROMO", "PCR"],
    "analisi": ["ESAMI DEL SANGUE", "EMOCROMO", "URINE COMPLETE"],
    "eco": ["ECOGRAFIA", "ECOGRAFIA ADDOME"],
}


def _demo_fallback_matches(df: pd.DataFrame, terms: list[str]) -> list[str]:
    choices = df["Codice prestazione ambulatoriale"].dropna().astype(str).unique().tolist()
    lowered = " ".join(terms).lower()

    for key, targets in DEMO_KEYWORD_FALLBACKS.items():
        if key in lowered:
            picked = [c for c in choices if any(t.lower() in c.lower() for t in targets)]
            if picked:
                return sorted(picked[:8])

    # Generic fallback for demo: always return top frequent-looking items.
    return sorted(choices[:8])


def match_service_codes(df: pd.DataFrame, terms: list[str], threshold: int = 88) -> list[str]:
    choices = df["Codice prestazione ambulatoriale"].dropna().astype(str).unique().tolist()
    if not choices:
        return []

    if not terms:
        return _demo_fallback_matches(df, ["visita"])

    matches: set[str] = set()
    for term in terms:
        if not isinstance(term, str) or not term.strip():
            continue
        best = process.extract(term, choices, scorer=fuzz.token_set_ratio, limit=5)
        for value, score, *_ in best:
            if score >= threshold:
                matches.add(value)

    if matches:
        return sorted(matches)

    return _demo_fallback_matches(df, terms)
