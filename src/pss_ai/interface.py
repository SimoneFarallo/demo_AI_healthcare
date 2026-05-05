from __future__ import annotations

from typing import Any

import gradio as gr

from pss_ai import AppSettings, PSSAssistant
from pss_ai.models import UserQuery
from pss_ai.services.care_plan_service import build_mock_care_plan
from pss_ai.services.dataset_service import filter_dataset
from pss_ai.services.ocr_service import extract_terms_from_file
from pss_ai.services.pharmacy_service import pharmacies_map_html, pharmacies_to_dataframe, search_pharmacies_for_drug
from pss_ai.services.search_service import match_service_codes

settings = AppSettings()
assistant = PSSAssistant(settings)
DATASET = assistant.dataset

APP_CSS = """
:root {
  --bg-1: #e8f7f2;
  --bg-2: #f8fcfa;
  --card: #ffffff;
  --ink: #0f2f2a;
  --muted: #4b6661;
  --brand: #0c9f77;
  --brand-2: #0d7f6a;
  --warn: #f59e0b;
}
body, .gradio-container {
  background: linear-gradient(140deg, var(--bg-1) 0%, var(--bg-2) 46%, #ffffff 100%) !important;
  color: var(--ink);
}
.hero {
  background: linear-gradient(135deg, #0d7f6a 0%, #0c9f77 55%, #16b58a 100%);
  border-radius: 24px;
  padding: 24px;
  color: white;
  box-shadow: 0 16px 36px rgba(12, 159, 119, 0.25);
  margin-bottom: 14px;
}
.hero h1 { margin: 0; font-size: 34px; letter-spacing: .2px; }
.hero p { margin: 8px 0 0; opacity: .95; }
.section-card {
  background: var(--card);
  border: 1px solid #d8eee7;
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 8px 20px rgba(8, 30, 25, 0.06);
}
.section-title { margin-bottom: 6px; }
.section-sub { color: var(--muted); margin-top: 0; }
"""


def _normalize_file_path(file_obj: Any) -> str:
    if file_obj is None:
        raise ValueError("Nessun file caricato")
    if isinstance(file_obj, str):
        return file_obj
    name = getattr(file_obj, "name", None)
    if name:
        return str(name)
    path = getattr(file_obj, "path", None)
    if path:
        return str(path)
    raise ValueError("Formato file non supportato")


def run_chat(user_input: str, comune: str | None):
    if not user_input or not user_input.strip():
        return "Inserisci una domanda valida.", "standard", 0.0, [], ""
    result = assistant.run(UserQuery(text=user_input.strip(), comune=comune or None))
    return result.answer, result.triage_level, result.confidence, result.suggested_slots, " -> ".join(result.trace)


def run_ocr_search(file: Any, comune: str | None = None, risposta_strutt: str | None = None):
    file_path = _normalize_file_path(file)
    terms = extract_terms_from_file(file_path)
    filtered = filter_dataset(DATASET, comune=comune or None, struttura_privata=risposta_strutt or None)
    matches = match_service_codes(filtered, terms, threshold=80)
    if not matches:
        return filtered.head(0), terms
    return filtered[filtered["Codice prestazione ambulatoriale"].isin(matches)].head(300), terms


def run_facility_search(words: str, comune: str | None):
    scoped = filter_dataset(DATASET, comune=comune or None)
    if not words or not words.strip():
        return scoped.head(0)
    matches = match_service_codes(scoped, [words], threshold=75)
    if not matches:
        return scoped.head(0)
    return scoped[scoped["Codice prestazione ambulatoriale"].isin(matches)].head(300)


def run_pharmacy_search(drug_name: str, city: str | None, only_24h: bool):
    items = search_pharmacies_for_drug(drug_name, city=city or None, open_24h=only_24h)
    return pharmacies_to_dataframe(items), pharmacies_map_html(items)


def run_care_plan(symptoms: str, triage_level: str, city: str | None):
    plan = build_mock_care_plan(symptoms, triage_level, city)
    return plan.urgency_banner, plan.recommended_actions, plan.required_documents, plan.estimated_waiting_days


def build_interface() -> gr.Blocks:
    with gr.Blocks(css=APP_CSS, title="Interface - PSS Healthcare") as demo:
        gr.HTML(
            """
            <div class='hero'>
              <h1>Interface</h1>
              <p>Piattaforma unica per orientamento sanitario: chat AI, OCR prescrizioni, ricerca strutture e farmacie, piano operativo guidato.</p>
            </div>
            """
        )

        gr.Markdown("### Percorso Guidato\nUsa i blocchi dall'alto verso il basso: 1) Analisi iniziale, 2) Ricerca strutture, 3) Farmaci/farmacie, 4) Piano azioni.")

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("### 1) Analisi Richiesta\nDescrivi sintomi o bisogno sanitario. Il sistema restituisce triage, confidence e slot suggeriti (mock).")
            with gr.Row():
                user_q = gr.Textbox(lines=4, label="Richiesta utente", placeholder="Es: ho dolore toracico, dove posso fare visita cardiologica a Milano?")
                user_city = gr.Textbox(label="Comune (opzionale)", placeholder="Milano")
            ask_btn = gr.Button("Analizza")
            answer = gr.Textbox(label="Risposta AI", lines=6)
            with gr.Row():
                triage = gr.Textbox(label="Triage")
                confidence = gr.Number(label="Confidence", precision=2)
            slots = gr.JSON(label="Slot consigliati (mock)")
            trace = gr.Textbox(label="Trace decisionale")
            ask_btn.click(run_chat, inputs=[user_q, user_city], outputs=[answer, triage, confidence, slots, trace])

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("### 2) Ricerca Prestazioni da Prescrizione (OCR)\nCarica un PDF/PNG. Il sistema estrae termini sanitari e trova strutture compatibili.")
            with gr.Row():
                rx_file = gr.File(label="File prescrizione")
                rx_city = gr.Textbox(label="Comune")
                rx_private = gr.Textbox(label="Struttura privata (SI/NO)")
            ocr_btn = gr.Button("Estrai e cerca")
            ocr_df = gr.Dataframe(label="Strutture trovate")
            ocr_terms = gr.JSON(label="Termini estratti")
            ocr_btn.click(run_ocr_search, inputs=[rx_file, rx_city, rx_private], outputs=[ocr_df, ocr_terms])

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("### 3) Ricerca Strutture per Prestazione\nInserisci il nome di una prestazione per ottenere le strutture disponibili.")
            with gr.Row():
                svc_name = gr.Textbox(label="Prestazione", placeholder="VISITA CARDIOLOGICA")
                svc_city = gr.Textbox(label="Comune (opzionale)")
            svc_btn = gr.Button("Cerca")
            svc_df = gr.Dataframe(label="Risultati strutture")
            svc_btn.click(run_facility_search, inputs=[svc_name, svc_city], outputs=[svc_df])

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("### 4) Farmaci e Farmacie (Mock)\nTrova farmacie che hanno il farmaco e visualizzale su mappa interattiva.")
            with gr.Row():
                drug = gr.Textbox(label="Farmaco", placeholder="ibuprofene")
                pharm_city = gr.Textbox(label="Comune (opzionale)")
                only24 = gr.Checkbox(label="Solo 24h", value=False)
            pharm_btn = gr.Button("Trova farmacie")
            pharm_table = gr.Dataframe(label="Farmacie trovate")
            pharm_map = gr.HTML(label="Mappa farmacie")
            pharm_btn.click(run_pharmacy_search, inputs=[drug, pharm_city, only24], outputs=[pharm_table, pharm_map])

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("### 5) Piano Operativo Paziente (Mock)\nGenera un piano guidato con urgenza, documenti e tempo stimato di accesso.")
            with gr.Row():
                cp_symptoms = gr.Textbox(lines=3, label="Sintomi/contesto", placeholder="Descrivi i sintomi")
                cp_triage = gr.Dropdown(choices=["high", "medium", "low", "standard"], value="standard", label="Triage")
                cp_city = gr.Textbox(label="Comune")
            cp_btn = gr.Button("Genera piano")
            cp_banner = gr.Textbox(label="Alert urgenza")
            cp_actions = gr.JSON(label="Azioni raccomandate")
            cp_docs = gr.JSON(label="Documenti da preparare")
            cp_wait = gr.Number(label="Attesa stimata (giorni)")
            cp_btn.click(run_care_plan, inputs=[cp_symptoms, cp_triage, cp_city], outputs=[cp_banner, cp_actions, cp_docs, cp_wait])

    return demo


def launch_interface(server_name: str = "127.0.0.1", server_port: int = 7860) -> None:
    demo = build_interface()
    demo.launch(server_name=server_name, server_port=server_port, share=False, inbrowser=True)


if __name__ == "__main__":
    launch_interface()
