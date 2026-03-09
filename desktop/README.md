# MAPIG Desktop Wrapper

Desktop packaging for MAPIG using Electron.

## What this gives you

- A Windows installer (`.exe`) that non-technical users can run.
- First-launch setup screen for API keys.
- Backend and frontend start automatically.
- Closing the app shuts down all MAPIG processes.

## Runtime behavior

- OpenAI key is required.
- Perplexity key is optional:
  - enabled + key present -> `SEARCH_PROVIDER=hybrid`
  - disabled or missing key -> `SEARCH_PROVIDER=local`
- API keys are stored in the OS-protected user profile (Electron `safeStorage`).
- Writable files (checkpoints/logs/settings) are stored under the app's `userData` folder.

## Build prerequisites (for the developer creating the installer)

1. Node.js LTS installed.
2. Python 3.11 installed.
3. Backend dependencies installed (`poetry install` from repo root).
4. Frontend dependencies installed (`npm --prefix frontend install`).
5. Desktop dependencies installed (`npm --prefix desktop install`).
6. PyInstaller installed in your Python environment (`poetry run pip install pyinstaller` or equivalent).

## Build Windows installer

From repo root:

```powershell
npm --prefix desktop run dist
```

Installer output:

`desktop/release/`

## Development run

From repo root:

```powershell
npm --prefix desktop run dev
```

In development mode, desktop wrapper starts:
- backend via `python -m uvicorn app.main:app`
- frontend via `npm --prefix frontend run dev`

