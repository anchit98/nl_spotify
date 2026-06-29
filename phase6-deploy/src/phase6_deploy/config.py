from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE6_ROOT = Path(__file__).resolve().parents[2]


def load_environment() -> None:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(PHASE6_ROOT / ".env")


def supabase_project_ref(url: str) -> str:
    match = re.match(r"https://([^.]+)\.supabase\.co", url.rstrip("/"))
    return match.group(1) if match else ""


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    phase6_root: Path
    supabase_url: str | None
    supabase_anon_key: str | None
    groq_api_key: str | None
    groq_model: str
    app_env: str
    expected_supabase_ref: str | None
    staging_api_url: str | None
    production_api_url: str | None

    @classmethod
    def from_env(cls) -> Settings:
        load_environment()
        url = os.getenv("SUPABASE_PROJECT_URL") or os.getenv("SUPABASE_URL")
        anon = os.getenv("SUPABASE_PROJECT_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        return cls(
            repo_root=REPO_ROOT,
            phase6_root=PHASE6_ROOT,
            supabase_url=url.rstrip("/") if url else None,
            supabase_anon_key=anon,
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            app_env=os.getenv("APP_ENV", "development"),
            expected_supabase_ref=os.getenv("EXPECTED_SUPABASE_PROJECT_REF") or None,
            staging_api_url=os.getenv("STAGING_API_URL"),
            production_api_url=os.getenv("PRODUCTION_API_URL"),
        )
