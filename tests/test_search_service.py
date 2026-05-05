import pandas as pd

from pss_ai.services.search_service import match_service_codes


def test_match_service_codes_returns_match():
    df = pd.DataFrame(
        {
            "Codice prestazione ambulatoriale": [
                "VISITA CARDIOLOGICA",
                "ECG DINAMICO",
                "ECOCARDIOGRAMMA",
            ]
        }
    )
    out = match_service_codes(df, ["visita cardio"], threshold=60)
    assert "VISITA CARDIOLOGICA" in out
