# JobDragon Backend

FastAPI server for JobDragon. Keep all secrets and third-party API calls here (Claude, LinkedIn automation control, Telegram).

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`

