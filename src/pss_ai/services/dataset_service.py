from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "Codice prestazione ambulatoriale",
    "Comune struttura",
}


STRUCTURE_NAME_CANDIDATES = [
    "Denominazione struttura",
    "Nome struttura",
]


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")

    # Backward-compatible normalization across historical dataset versions.
    if "Denominazione struttura" not in df.columns:
        for candidate in STRUCTURE_NAME_CANDIDATES:
            if candidate in df.columns:
                df["Denominazione struttura"] = df[candidate]
                break
        else:
            df["Denominazione struttura"] = ""

    return df


def filter_dataset(df: pd.DataFrame, comune: str | None = None, struttura_privata: str | None = None) -> pd.DataFrame:
    out = df
    if comune:
        out = out[out["Comune struttura"].astype(str).str.lower() == comune.lower()]
    if struttura_privata and "Struttura privata" in out.columns:
        out = out[out["Struttura privata"].astype(str).str.lower() == struttura_privata.lower()]
    return out.copy()
