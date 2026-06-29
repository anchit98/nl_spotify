from __future__ import annotations

import httpx


def smoke_api(base_url: str, *, label: str) -> list[str]:
    errors: list[str] = []
    base = base_url.rstrip("/")

    try:
        live = httpx.get(f"{base}/health", timeout=30.0)
        if live.status_code != 200:
            errors.append(f"{label}: /health returned {live.status_code}")
    except httpx.HTTPError as exc:
        errors.append(f"{label}: /health unreachable — {exc}")
        return errors

    try:
        ready = httpx.get(f"{base}/health/ready", timeout=45.0)
        if ready.status_code != 200:
            errors.append(f"{label}: /health/ready returned {ready.status_code} — {ready.text[:200]}")
    except httpx.HTTPError as exc:
        errors.append(f"{label}: /health/ready unreachable — {exc}")

    return errors


def smoke_deployments(staging_url: str | None, production_url: str | None) -> list[str]:
    errors: list[str] = []
    if staging_url:
        errors.extend(smoke_api(staging_url, label="staging"))
    if production_url:
        errors.extend(smoke_api(production_url, label="production"))
    if not staging_url and not production_url:
        errors.append("No STAGING_API_URL or PRODUCTION_API_URL configured")
    return errors
