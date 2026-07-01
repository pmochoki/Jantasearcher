# Jantasearcher

Full-stack job application automation: scrape **external-apply** LinkedIn jobs, generate AI cover letters, and get Telegram notifications.

## What it does

1. **Scrape LinkedIn** — logs in with Playwright, searches jobs, and saves only roles with an **Apply on company website** link (skips Easy Apply).
2. **AI cover letters** — uses Claude to draft tailored cover letters from your background + the job description.
3. **Telegram alerts** — notifies you when new jobs are found, scrapes finish, or a cover letter is ready.

## Tech

- Frontend: Next.js + Tailwind
- Backend: FastAPI (Python)
- DB: SQLite
- Automation: Playwright
- AI: Claude (Anthropic)
- Notifications: Telegram Bot API

## Repo layout

- `frontend/` — Next.js dashboard, jobs list, cover letter UI
- `backend/` — FastAPI API
- `scraper/` — LinkedIn scraper (external apply only)
- `ai/` — Cover letter generation
- `database/` — SQLite schema + queries
- `notifications/` — Telegram bot helpers

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` — a secondary LinkedIn account is recommended
   - `CLAUDE_API_KEY`, `APPLICANT_NAME`, `APPLICANT_BACKGROUND`
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional but recommended)
2. Install Playwright browsers: `playwright install chromium`

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — dashboard and jobs list connect to the API at `http://localhost:8000`.

### Run scraper (CLI)

```bash
cd scraper
pip install -r requirements.txt
python -m scraper.run
```

Or trigger from the API: `POST /scraper/run`

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | Dashboard counts |
| GET | `/jobs` | List external-apply jobs |
| GET | `/jobs/{id}` | Single job |
| POST | `/jobs/{id}/cover-letter` | Generate + save cover letter |
| PATCH | `/jobs/{id}/status` | Update application status |
| POST | `/scraper/run` | Run LinkedIn scraper |

## Notes

- LinkedIn may show CAPTCHAs — the scraper pauses and saves partial results.
- Use a VPN, low daily caps, and human-like delays (`SCRAPER_DELAY_*`).
- External apply URLs open the company’s own careers site; auto-submit is not included in v1 (you review + apply manually with the generated cover letter).
