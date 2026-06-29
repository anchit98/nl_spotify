from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import HTTPException

from backend_api.config import Settings, supabase_project_ref


def liveness() -> dict[str, str]:
    return {"status": "ok"}


def readiness(settings: Settings, db_probe: Callable[[], None]) -> dict[str, Any]:
    """
    Deep health check for Render/Vercel deploy gates (edge case 6.5).
    Fails if Supabase is unreachable, Groq key missing, or env pairing invalid (6.3).
    """
    checks: dict[str, Any] = {"status": "ok", "app_env": settings.app_env}
    errors: list[str] = []

    if settings.expected_supabase_ref:
        actual = supabase_project_ref(settings.supabase_url)
        checks["supabase_ref"] = actual
        if actual != settings.expected_supabase_ref:
            errors.append(
                f"supabase ref mismatch: expected {settings.expected_supabase_ref}, got {actual}"
            )

    if not settings.groq_api_key:
        errors.append("GROQ_API_KEY is not configured")

    try:
        db_probe()
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"database unreachable: {exc}")
        checks["database"] = "error"

    if errors:
        checks["status"] = "degraded"
        checks["errors"] = errors
        raise HTTPException(status_code=503, detail=checks)
    return checks
