from __future__ import annotations

import re
from pathlib import Path


KNOWN_SERVICES = [
    "VISITA CARDIOLOGICA",
    "VISITA DERMATOLOGICA",
    "VISITA OCULISTICA",
    "VISITA GINECOLOGICA",
    "ELETTROCARDIOGRAMMA",
    "ECG",
    "ECOGRAFIA",
    "ESAMI DEL SANGUE",
    "EMOCROMO",
    "TAC",
    "RISONANZA",
]

KNOWN_DRUGS = [
    "ibuprofene",
    "tachipirina",
    "paracetamolo",
    "amoxicillina",
    "omeprazolo",
    "aspirina",
    "antistaminico",
]


DOC_TYPE_HINTS = {
    "prescrizione_medica": ["prescrizione", "impegnativa", "ssn", "medico prescrittore"],
    "ricetta": ["ricetta", "farmaco", "posologia", "dosaggio"],
    "documento_struttura": ["struttura", "ambulatorio", "ospedale", "contatti", "indirizzo"],
    "piano_azione": ["piano", "azione", "follow-up", "controllo", "obiettivo"],
}


def _mock_terms_from_filename(path: Path) -> list[str]:
    name = path.stem.replace("_", " ").replace("-", " ").upper()
    tokens = [t for t in name.split() if len(t) > 3]
    if not tokens or name.startswith("TMP"):
        return ["VISITA CARDIOLOGICA"]
    return [" ".join(tokens[:3])]


def extract_terms_from_text(text: str) -> list[str]:
    raw = re.findall(r" - ([A-Za-zÀ-ÖØ-öø-ÿ' ]+)", text)
    cleaned = [item.strip() for item in raw if item.strip()]
    if cleaned:
        return cleaned

    generic = re.findall(r"\b([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ\- ]{3,})\b", text)
    if generic:
        return [g.strip() for g in generic[:12]]

    return []


def extract_text_from_file(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(path)

    suffix = file_path.suffix.lower()

    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            import fitz  # type: ignore
            text = ""
            with fitz.open(path) as pdf:
                for page in pdf:
                    text += page.get_text() + "\n"
            return text
        except Exception:
            return ""

    # image and other file types fallback for demo
    return ""


def detect_document_type(text: str, filename: str = "") -> str:
    lowered = f"{filename} {text}".lower()
    scores: dict[str, int] = {k: 0 for k in DOC_TYPE_HINTS}

    for doc_type, hints in DOC_TYPE_HINTS.items():
        for h in hints:
            if h in lowered:
                scores[doc_type] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "documento_generico"


def extract_entities(text: str) -> dict:
    lowered = text.lower()

    services = [s for s in KNOWN_SERVICES if s.lower() in lowered]
    drugs = [d for d in KNOWN_DRUGS if d in lowered]

    structures = re.findall(r"(?:ospedale|clinica|ambulatorio|centro medico)\s+[A-Za-zÀ-ÖØ-öø-ÿ ]+", text, flags=re.IGNORECASE)
    structures = list(dict.fromkeys([s.strip() for s in structures]))[:10]

    action_lines = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        if re.search(r"\b(contattare|prenotare|eseguire|monitorare|controllo|follow-up)\b", l, flags=re.IGNORECASE):
            action_lines.append(l)
    action_lines = action_lines[:10]

    return {
        "services": services,
        "drugs": drugs,
        "structures": structures,
        "action_items": action_lines,
    }


def analyze_document(path: str) -> dict:
    p = Path(path)
    text = extract_text_from_file(path)

    terms = extract_terms_from_text(text)
    if not terms:
        terms = _mock_terms_from_filename(p)

    doc_type = detect_document_type(text, p.name)
    entities = extract_entities(text)

    # merge entities services into terms for better retrieval
    merged_terms = list(dict.fromkeys(terms + entities.get("services", [])))

    return {
        "document_type": doc_type,
        "extracted_terms": merged_terms,
        "entities": entities,
        "text_preview": (text[:800] if text else "(no extracted text, fallback filename mode)"),
    }


def extract_terms_from_file(path: str) -> list[str]:
    return analyze_document(path)["extracted_terms"]
