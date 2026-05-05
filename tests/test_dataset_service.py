import pandas as pd

from pss_ai.services.dataset_service import filter_dataset


def test_filter_dataset_comune_case_insensitive():
    df = pd.DataFrame(
        {
            "Comune struttura": ["Milano", "Brescia"],
            "Struttura privata": ["SI", "NO"],
            "Codice prestazione ambulatoriale": ["A", "B"],
            "Denominazione struttura": ["X", "Y"],
        }
    )
    result = filter_dataset(df, comune="milano")
    assert len(result) == 1
    assert result.iloc[0]["Comune struttura"] == "Milano"
