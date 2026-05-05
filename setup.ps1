$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) {
  python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
}

Write-Host "Setup completato."
Write-Host "Avvio CLI: python main.py"
Write-Host "Avvio API: python main.py api"
