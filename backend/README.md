# JantaSearcher Backend

FastAPI server for JantaSearcher. Keep all secrets and third-party API calls here (Claude, LinkedIn automation control, Telegram).

**The Telegram bot only works while the backend service is running** (local uvicorn, Vercel backend service, or Render).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
PYTHONPATH=.. uvicorn app.main:app --reload --port 8000
```

On startup you should get a Telegram message: **"JantaSearcher is connected."**

## Deploy

- **Vercel Services** (recommended): root `vercel.json` deploys frontend + backend together. Add env vars in the Vercel dashboard.
- **Render** (fallback): use `render.yaml` if Playwright build fails on Vercel.

After Vercel deploy, set env vars in Project Settings → Environment Variables, then redeploy.

## Telegram troubleshooting

| Symptom | Fix |
|---------|-----|
| Commands get no reply | Backend is not running — start locally or deploy to Render |
| `/list` unknown | Pull latest `main` and restart backend |
| Worked before, stopped | Mac slept / terminal closed — use Render for 24/7 |
| Still silent | `GET /telegram/health` — check `webhook_blocks_polling` |

## Endpoints

- `GET /health`
- `GET /telegram/health` — bot token, chat IDs, webhook status
- `POST /telegram/daily-summary` — trigger summary now

