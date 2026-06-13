import asyncio

from fastapi import FastAPI

from app.database import init_db
from app.api.jobs import router as jobs_router

app = FastAPI(
    title="AI Transaction Pipeline",
    version="1.0.0",
)

app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])


@app.on_event("startup")
async def on_startup() -> None:
    max_retries = 10
    delay_seconds = 2

    for attempt in range(max_retries):
        try:
            await init_db()
            return
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay_seconds)


@app.get("/")
async def root():
    return {
        "message": "running",
        "service": "ai-transaction-pipeline",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
