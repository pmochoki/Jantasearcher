from fastapi import FastAPI

app = FastAPI(title="JobDragon API")


@app.get("/health")
def health():
    return {"ok": True}

