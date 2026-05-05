# Quick start (Windows)

1) First-time backend deps:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2) First-time frontend deps:
```powershell
npm install
npm --prefix frontend install
```

3) Daily run (frontend only):
```powershell
npm run dev
```

Optional full run (backend + frontend):
```powershell
npm run dev:full
```
