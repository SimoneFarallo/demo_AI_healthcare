from __future__ import annotations

import os
import tempfile
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import AppSettings
from .models import UserQuery
from .orchestrator import PSSAssistant
from .services.dataset_service import filter_dataset
from .services.ocr_service import analyze_document, extract_terms_from_file
from .services.pharmacy_service import pharmacies_to_dataframe, search_pharmacies_for_drug
from .services.search_service import match_service_codes

settings = AppSettings()
assistant = PSSAssistant(settings)
app = FastAPI(title="PSS AI Assistant", version="0.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    text: str = Field(min_length=3)
    comune: str | None = None
    struttura_privata: str | None = None
    extracted_terms: list[str] = Field(default_factory=list)


class ExtractMatchRequest(BaseModel):
    file_path: str
    comune: str | None = None
    struttura_privata: str | None = None


class FacilitySearchRequest(BaseModel):
    prestazione: str
    comune: str | None = None


class PharmacyRequest(BaseModel):
    farmaco: str
    comune: str | None = None
    only_24h: bool = False


def _answer_to_dict(result) -> dict:
    return {
        "answer": result.answer,
        "matched_services": result.matched_services,
        "used_mock": result.used_mock,
        "triage_level": result.triage_level,
        "confidence": result.confidence,
        "suggested_slots": result.suggested_slots,
        "trace": result.trace,
    }


@app.get("/")
def root() -> dict:
    return {"message": "Backend online. Avvia il frontend React su http://localhost:5173"}


@app.get("/health")
def health() -> dict:
    provider_effective = assistant.ai.__class__.__name__.replace("Provider", "").lower()
    return {
        "status": "ok",
        "ai_mode_config": settings.ai_mode,
        "provider_effective": provider_effective,
        "dataset_rows": int(len(assistant.dataset)),
        "version": "0.8.0",
    }


@app.post("/ask")
def ask(payload: AskRequest) -> dict:
    query = UserQuery(text=payload.text, comune=payload.comune, struttura_privata=payload.struttura_privata)
    result = assistant.run(query, extracted_terms=payload.extracted_terms)
    return _answer_to_dict(result)


@app.post("/extract-and-match")
def extract_and_match(payload: ExtractMatchRequest) -> dict:
    try:
        doc = analyze_document(payload.file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    query_text = (
        f"Analisi documento tipo {doc['document_type']}. "
        f"Servizi: {doc['entities'].get('services', [])}. "
        f"Farmaci: {doc['entities'].get('drugs', [])}. "
        f"Azioni: {doc['entities'].get('action_items', [])}."
    )
    query = UserQuery(text=query_text, comune=payload.comune, struttura_privata=payload.struttura_privata)
    result = assistant.run(query, extracted_terms=doc["extracted_terms"])

    response = _answer_to_dict(result)
    response["document_context"] = doc
    return response


@app.post("/extract-and-match-upload")
async def extract_and_match_upload(
    file: UploadFile = File(...),
    comune: str | None = Form(default=None),
    struttura_privata: str | None = Form(default=None),
) -> dict:
    suffix = os.path.splitext(file.filename or "")[1] or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = analyze_document(tmp_path)
        query_text = (
            f"Analisi documento tipo {doc['document_type']}. "
            f"Servizi: {doc['entities'].get('services', [])}. "
            f"Farmaci: {doc['entities'].get('drugs', [])}. "
            f"Azioni: {doc['entities'].get('action_items', [])}."
        )
        query = UserQuery(text=query_text, comune=comune, struttura_privata=struttura_privata)
        result = assistant.run(query, extracted_terms=doc["extracted_terms"])

        response = _answer_to_dict(result)
        response["document_context"] = doc
        return response
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@app.post("/facility-search")
def facility_search(payload: FacilitySearchRequest) -> dict:
    scoped = filter_dataset(assistant.dataset, comune=payload.comune)
    matches = match_service_codes(scoped, [payload.prestazione], threshold=75)
    result = scoped[scoped["Codice prestazione ambulatoriale"].isin(matches)].head(60)
    if result.empty:
        result = scoped.head(60)
    return {"count": int(len(result)), "matches": matches[:10], "rows": result.to_dict(orient="records")}


@app.post("/pharmacies")
def pharmacies(payload: PharmacyRequest) -> dict:
    items = search_pharmacies_for_drug(payload.farmaco, city=payload.comune, open_24h=payload.only_24h)
    df = pharmacies_to_dataframe(items)
    return {"count": int(len(df)), "rows": df.to_dict(orient="records")}
