from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from phase5_ops.config import Settings
from phase5_ops.db import Database
from phase5_ops.drift_detector import AlertCandidate


def load_model_pin(phase5_root: Path) -> dict[str, Any]:
    path = phase5_root / "config" / "model_pin.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_thresholds(phase5_root: Path) -> dict[str, Any]:
    path = phase5_root / "config" / "alert_thresholds.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def sync_model_registry(
    db: Database,
    settings: Settings,
    *,
    latest_synthesis_model: str | None,
    thresholds: dict[str, Any],
) -> list[AlertCandidate]:
    """Record pinned model/prompt version; alert on mismatch with latest synthesis."""
    pin = load_model_pin(settings.phase5_root)
    groq_model = pin.get("groq_model") or settings.groq_model
    prompt_version = pin.get("prompt_version") or settings.prompt_version
    notes = pin.get("notes")

    db.record_model_pin(groq_model, prompt_version, notes=notes)

    alerts: list[AlertCandidate] = []
    if not thresholds.get("alert_on_model_mismatch", True):
        return alerts
    if not latest_synthesis_model:
        return alerts
    if latest_synthesis_model != groq_model:
        alerts.append(
            AlertCandidate(
                severity="warning",
                category="model_drift",
                title="Synthesis model differs from pinned version",
                message=(
                    f"Pinned model: {groq_model}. Latest synthesis used: {latest_synthesis_model}. "
                    "Trend comparisons may be invalid until runs use a consistent model."
                ),
                context={"pinned": groq_model, "latest_run": latest_synthesis_model},
            )
        )
    return alerts
