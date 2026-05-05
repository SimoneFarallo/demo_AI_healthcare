# PSS Healthcare - AI-Powered Care Navigation Platform

This is a university project that has been fully refactored with a modern architecture, stronger application logic, and AI-powered workflows for healthcare navigation.

## What This Project Does

- Conversational healthcare assistant (`Care Navigator`)
- Clinical document upload integrated into chat flow (OCR and term extraction)
- Intelligence Box updated from both chat and uploaded documents
- Healthcare facility search with dataset + smart demo fallback
- Pharmacy and medication search with interactive OpenStreetMap
- Selected facility contact panel
- One-page product-style dashboard UI

## Tech Stack

- Backend: Python + FastAPI
- Frontend: React + Vite + TypeScript + Tailwind
- Map: Leaflet / React-Leaflet
- AI providers: Anthropic / OpenAI / Mock (configurable)

## Requirements

- Python 3.10+
- Node.js 18+ (with `npm`)

## Installation

### 1) Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) Frontend dependencies

```powershell
npm.cmd --prefix frontend install
```

## Run

### Recommended: one-command startup

```powershell
python main.py full
```

This starts:
- FastAPI backend at `http://127.0.0.1:8000`
- Vite frontend at `http://127.0.0.1:5173`

### Alternative: run separately

Backend:
```powershell
python main.py api --port 8000
```

Frontend:
```powershell
npm.cmd --prefix frontend run dev
```

## `main.py` Modes

- `python main.py` -> web mode (API + browser open)
- `python main.py api` -> API only
- `python main.py cli` -> CLI mode
- `python main.py demo` -> quick backend demo
- `python main.py full` -> backend + frontend together

## AI Configuration

Use `.env` file:

```env
AI_MODE=auto
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Typical modes:
- `AI_MODE=auto`: uses a real provider when keys are available
- `AI_MODE=mock`: forces mock behavior

## Project Structure

```text
.
├─ main.py
├─ requirements.txt
├─ frontend/
│  ├─ src/
│  └─ package.json
├─ src/pss_ai/
│  ├─ api.py
│  ├─ orchestrator.py
│  ├─ services/
│  └─ adapters/
├─ tests/
├─ EDA_datasets.py
├─ Extra_tools.py
├─ Interface.py
└─ Langchain.py
```

## Notebook Conversion

Original notebooks were converted into Python scripts:

- `EDA_datasets.py`
- `Extra_tools.py`
- `Interface.py`
- `Langchain.py`

## Quick Troubleshooting

- If `npm` is not recognized: install Node.js LTS and reopen terminal
- If Python dependency is missing: reinstall with `-r requirements.txt`
- If port is busy: use another port, e.g. `python main.py api --port 8001`

## Notes

This project is designed for demo and prototyping scenarios. Some data flows and availability responses are intentionally mocked to ensure stable UX during presentations.
