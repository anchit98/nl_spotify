from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend_api.config import Settings
from backend_api.db import InsightsDatabase, clear_response_caches
from backend_api.health import liveness, readiness
from backend_api.pm_buddy import chat as pm_buddy_chat
from backend_api.synthesis import start_synthesis, synthesis_status

settings = Settings.from_env()
db = InsightsDatabase(settings)

app = FastAPI(title="Spotify Discovery Insights API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return liveness()


@app.get("/health/ready")
def health_ready() -> dict:
    def _probe() -> None:
        db.list_runs(limit=1)

    return readiness(settings, _probe)


@app.get("/api/insights/latest")
def get_latest_insights() -> dict:
    bundle = db.get_latest_bundle()
    if not bundle:
        raise HTTPException(status_code=404, detail="No successful synthesis run found")
    return bundle


@app.get("/api/insights/runs")
def list_runs() -> dict:
    return {"runs": db.list_runs()}


@app.get("/api/insights/runs/{run_id}")
def get_run(run_id: str) -> dict:
    bundle = db.get_run_bundle(run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Run not found")
    return bundle


@app.get("/api/insights/trends")
def get_trends(granularity: str = "month") -> dict:
    if granularity not in ("week", "month", "year"):
        raise HTTPException(status_code=400, detail="granularity must be week, month, or year")
    return db.get_trends(granularity=granularity)


@app.get("/api/synthesis/status")
def get_synthesis_status() -> dict:
    return synthesis_status(db)


@app.post("/api/synthesize")
def trigger_synthesis() -> dict:
    result = start_synthesis(settings, db)
    if not result.get("started"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Already running"))
    return result


@app.post("/api/cache/invalidate")
def invalidate_cache() -> dict[str, str]:
    clear_response_caches()
    return {"status": "ok"}


class ChatTurn(BaseModel):
    role: str
    content: str


class PmBuddyChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list)


@app.post("/api/pm-buddy/chat")
def pm_buddy_chat_endpoint(body: PmBuddyChatRequest) -> dict[str, Any]:
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
    history = [{"role": t.role, "content": t.content} for t in body.history[-10:]]
    try:
        return pm_buddy_chat(settings, db, message=body.message, history=history)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
