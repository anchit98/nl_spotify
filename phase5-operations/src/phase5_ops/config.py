from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE5_ROOT = Path(__file__).resolve().parents[2]


def load_environment() -> None:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(PHASE5_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    alert_webhook_url: str | None
    groq_model: str
    prompt_version: str
    phase5_root: Path

    @classmethod
    def from_env(cls) -> Settings:
        load_environment()
        url = os.getenv("SUPABASE_PROJECT_URL") or os.getenv("SUPABASE_URL")
        anon = os.getenv("SUPABASE_PROJECT_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not anon:
            raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_PROJECT_ANON_KEY are required")

        webhook = os.getenv("ALERT_WEBHOOK_URL") or None
        if webhook:
            webhook = webhook.strip() or None

        return cls(
            supabase_url=url.rstrip("/"),
            supabase_anon_key=anon,
            alert_webhook_url=webhook,
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            prompt_version=os.getenv("PROMPT_VERSION", "2026-06-v1"),
            phase5_root=PHASE5_ROOT,
        )
