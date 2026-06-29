from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_PAYLOAD_KEYS = ("source", "source_item_id", "text")


class ValidationError(ValueError):
  pass


@dataclass(frozen=True)
class HealthCheckResult:
    ok: bool
    message: str
    sample_fields: dict[str, Any] | None = None


def validate_raw_item(source: str, item_id: str, payload: dict[str, Any]) -> None:
    if not source:
        raise ValidationError("source is required")
    if not item_id:
        raise ValidationError("source_item_id is required")
    if not isinstance(payload, dict):
        raise ValidationError("raw_payload must be a JSON object")

    for key in REQUIRED_PAYLOAD_KEYS:
        if key not in payload:
            raise ValidationError(f"raw_payload missing required field: {key}")

    text = payload.get("text")
    if text is None or (isinstance(text, str) and not text.strip()):
        raise ValidationError("raw_payload.text must be non-empty")
