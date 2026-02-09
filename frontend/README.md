# MAPIG Frontend

Web UI for MAPIG (Multi-Agent Psychometric Item Generator). Connects to the FastAPI backend to configure instrument setup, generate items, and view results and audit metadata.

## Tech stack

- Next.js 14+ (App Router), TypeScript
- TailwindCSS, shadcn-style UI (Radix primitives)
- React Hook Form + Zod
- TanStack Query
- Lucide icons

## Install

From the `frontend` directory:

```bash
npm install
```

Or with pnpm:

```bash
pnpm install
```

## Configure API URL

Create a `.env.local` file in the `frontend` directory (or copy from `.env.local.example`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If not set, the app defaults to `http://localhost:8000`.

## Run

1. Start the MAPIG FastAPI backend (from the repo root):

   ```bash
   uvicorn app.main:app --reload
   ```

2. Start the frontend (from `frontend`):

   ```bash
   npm run dev
   ```

   Or:

   ```bash
   pnpm dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build for production

```bash
npm run build
npm run start
```

## Features

- **Instrument Setup**: Construct name/definition, target population, response scale (presets + custom), item count (10–50), constraints and approved domains (tag inputs), optional native construct and example item. Resume thread via X-Thread-ID.
- **Evidence and Audit**: Approved sources, thread/run ID (copy), iteration count, stop reason, run timeline with loop indicator.
- **Generated Items**: Editable item text, expandable rationale, citation chips; export as JSON/CSV, copy items or full output; client-side quality checks (and/or, negations, word count).
- **Developer drawer**: Collapsible last request/response JSON.
- **Theme**: Psynalytics brand (teal, lime), light/dark mode, responsive 3-column layout.
