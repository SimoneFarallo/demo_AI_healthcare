from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CarePlan:
    urgency_banner: str
    recommended_actions: list[str]
    required_documents: list[str]
    estimated_waiting_days: int


def build_mock_care_plan(symptom_text: str, triage_level: str, city: str | None = None) -> CarePlan:
    city_label = city or "il tuo comune"

    if triage_level == "high":
        return CarePlan(
            urgency_banner="Attenzione: sintomi potenzialmente urgenti. In caso di peggioramento chiama il 112.",
            recommended_actions=[
                "Contatta la guardia medica o il medico curante entro poche ore",
                "Valuta PS se i sintomi aumentano (dolore toracico, dispnea, sanguinamento)",
                f"Cerca struttura con priorita alta vicino a {city_label}",
            ],
            required_documents=["Tessera sanitaria", "Prescrizione", "Documento di identita", "Referti recenti"],
            estimated_waiting_days=1,
        )

    if triage_level == "medium":
        return CarePlan(
            urgency_banner="Priorita intermedia: consigliata valutazione medica in tempi brevi.",
            recommended_actions=[
                "Prenota visita specialistica entro 3-7 giorni",
                "Monitora sintomi e temperatura",
                f"Valuta strutture pubbliche e private a {city_label}",
            ],
            required_documents=["Tessera sanitaria", "Prescrizione", "Lista farmaci attuali"],
            estimated_waiting_days=5,
        )

    return CarePlan(
        urgency_banner="Situazione non urgente: percorso ordinario consigliato.",
        recommended_actions=[
            "Prenota controllo ambulatoriale",
            "Conserva eventuali esami precedenti",
            "Segui terapia indicata dal medico",
        ],
        required_documents=["Tessera sanitaria", "Prescrizione (se presente)"],
        estimated_waiting_days=12,
    )
