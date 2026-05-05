from pss_ai import AppSettings, PSSAssistant
from pss_ai.logging_utils import setup_logging
from pss_ai.models import UserQuery


def main() -> None:
    settings = AppSettings()
    setup_logging(settings.log_level)

    assistant = PSSAssistant(settings)
    print("PSS Assistant CLI - scrivi 'exit' per uscire")
    while True:
        text = input("\nDomanda: ").strip()
        if text.lower() in {"exit", "quit"}:
            break
        comune = input("Comune (invio per saltare): ").strip() or None
        query = UserQuery(text=text, comune=comune)
        result = assistant.run(query)
        print("\nRisposta:", result.answer)
        print("Triage:", result.triage_level, "| Confidence:", result.confidence)
        print("Prestazioni match:", result.matched_services[:5])
        print("Slot suggeriti:", result.suggested_slots)


if __name__ == "__main__":
    main()
