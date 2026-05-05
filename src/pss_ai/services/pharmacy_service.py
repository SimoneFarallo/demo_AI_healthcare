from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Pharmacy:
    name: str
    city: str
    address: str
    lat: float
    lon: float
    open_24h: bool
    inventory: list[str]


MOCK_PHARMACIES: list[Pharmacy] = [
    Pharmacy("Farmacia Duomo", "Milano", "Via Torino 12", 45.4642, 9.1900, True, ["tachipirina", "ibuprofene", "amoxicillina"]),
    Pharmacy("Farmacia Navigli", "Milano", "Alzaia Naviglio Grande 44", 45.4512, 9.1738, False, ["ibuprofene", "vitamina c", "omeprazolo"]),
    Pharmacy("Farmacia Centrale", "Brescia", "Corso Zanardelli 9", 45.5416, 10.2118, True, ["tachipirina", "aspirina", "antistaminico"]),
    Pharmacy("Farmacia San Martino", "Bergamo", "Via XX Settembre 18", 45.6983, 9.6773, False, ["omeprazolo", "antibiotico", "spray gola"]),
    Pharmacy("Farmacia Lago", "Como", "Piazza Cavour 6", 45.8081, 9.0852, False, ["tachipirina", "ibuprofene", "collirio"]),
]


def search_pharmacies_for_drug(drug_name: str, city: str | None = None, open_24h: bool = False) -> list[Pharmacy]:
    target = (drug_name or "").strip().lower()
    city_target = (city or "").strip().lower()

    items = []
    for pharmacy in MOCK_PHARMACIES:
        if city_target and pharmacy.city.lower() != city_target:
            continue
        if open_24h and not pharmacy.open_24h:
            continue
        if not target or any(target in med.lower() for med in pharmacy.inventory):
            items.append(pharmacy)
    return items


def pharmacies_to_dataframe(items: list[Pharmacy]):
    import pandas as pd

    rows = [
        {
            "Farmacia": p.name,
            "Comune": p.city,
            "Indirizzo": p.address,
            "Aperta 24h": "SI" if p.open_24h else "NO",
            "Farmaci disponibili (mock)": ", ".join(p.inventory),
        }
        for p in items
    ]
    return pd.DataFrame(rows)


def pharmacies_map_html(items: list[Pharmacy]) -> str:
    if not items:
        return "<div style='padding:16px;border-radius:12px;background:#fef2f2;color:#991b1b'>Nessuna farmacia trovata con i filtri selezionati.</div>"

    markers_js = "\n".join(
        [
            f"L.marker([{p.lat}, {p.lon}]).addTo(map).bindPopup('<b>{p.name}</b><br>{p.address}<br>{p.city}<br>24h: {'SI' if p.open_24h else 'NO'}');"
            for p in items
        ]
    )
    center_lat = items[0].lat
    center_lon = items[0].lon

    return f"""
<div id='pharmacy-map' style='height:420px;border-radius:14px;overflow:hidden;'></div>
<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'/>
<script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script>
<script>
  const container = document.getElementById('pharmacy-map');
  container.innerHTML = '';
  const map = L.map('pharmacy-map').setView([{center_lat}, {center_lon}], 10);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19 }}).addTo(map);
  {markers_js}
</script>
"""
