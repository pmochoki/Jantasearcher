# JobDragon

Full-stack job application automation web app scaffold.

## Tech

- Frontend: Next.js + Tailwind
- Backend: FastAPI (Python)
- DB: SQLite (later)
- Automation: Playwright (later)
- AI: Claude (later)
- Notifications: Telegram (later)

## Repo layout

- `frontend/`: Next.js app (UI)
- `backend/`: FastAPI server (API + secrets)
- `scraper/`: LinkedIn scraper (Playwright) (pending)
- `applier/`: Auto-apply + ATS handlers (Playwright) (pending)
- `ai/`: CV tailoring + cover letter modules (pending)
- `database/`: SQLite schema + queries (pending)
- `notifications/`: Telegram bot (pending)
- `uploads/`: master CV + generated PDFs (pending)

## Local dev

### Frontend

```bash
cd frontend
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Copy `.env.example` to `.env` and fill values as needed.

