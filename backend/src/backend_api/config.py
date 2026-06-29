from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def supabase_project_ref(url: str) -> str:
    import re

    match = re.match(r"https://([^.]+)\.supabase\.co", url.rstrip("/"))
    return match.group(1) if match else ""


def load_environment() -> None:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(BACKEND_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    cors_origins: list[str]
    cors_origin_regex: str | None
    phase3_src: Path
    repo_root: Path
    groq_api_key: str
    groq_model: str
    app_env: str
    expected_supabase_ref: str | None

    @classmethod
    def from_env(cls) -> Settings:
        load_environment()
        url = os.getenv("SUPABASE_PROJECT_URL") or os.getenv("SUPABASE_URL")
        anon = os.getenv("SUPABASE_PROJECT_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not anon:
            raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_PROJECT_ANON_KEY are required")

        origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
        origin_regex = os.getenv("CORS_ORIGIN_REGEX") or None

        return cls(
            supabase_url=url.rstrip("/"),
            supabase_anon_key=anon,
            cors_origins=origins,
            cors_origin_regex=origin_regex,
            phase3_src=REPO_ROOT / "phase3-enrichment" / "src",
            repo_root=REPO_ROOT,
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            app_env=os.getenv("APP_ENV", "development"),
            expected_supabase_ref=os.getenv("EXPECTED_SUPABASE_PROJECT_REF") or None,
        )
