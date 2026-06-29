from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from phase3_insights.rate_limiter import MODEL_LIMITS, GroqModelLimits

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parent


def load_environment() -> None:
    load_dotenv(PACKAGE_ROOT / ".env")
    load_dotenv(REPO_ROOT / ".env")


def _limits_for_model(model: str) -> GroqModelLimits:
    if model in MODEL_LIMITS:
        return MODEL_LIMITS[model]
    return GroqModelLimits(
        requests_per_minute=int(os.getenv("GROQ_REQUESTS_PER_MINUTE", "30")),
        requests_per_day=int(os.getenv("GROQ_REQUESTS_PER_DAY", "1000")),
        tokens_per_minute=int(os.getenv("GROQ_TOKENS_PER_MINUTE", "12000")),
        tokens_per_day=int(os.getenv("GROQ_TOKENS_PER_DAY", "100000")),
    )


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    groq_api_key: str
    groq_model: str
    groq_limits: GroqModelLimits
    rate_limit_safety_margin: float
    skip_executive_summary: bool

    @classmethod
    def from_env(cls) -> Settings:
        load_environment()
        url = os.getenv("SUPABASE_PROJECT_URL") or os.getenv("SUPABASE_URL")
        anon = os.getenv("SUPABASE_PROJECT_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        if not url or not anon:
            raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_PROJECT_ANON_KEY are required")
        if not groq_key:
            raise ValueError("GROQ_API_KEY is required for Phase 3 synthesis")

        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return cls(
            supabase_url=url.rstrip("/"),
            supabase_anon_key=anon,
            groq_api_key=groq_key,
            groq_model=model,
            groq_limits=_limits_for_model(model),
            rate_limit_safety_margin=float(os.getenv("GROQ_RATE_LIMIT_SAFETY_MARGIN", "0.05")),
            skip_executive_summary=os.getenv("SKIP_EXECUTIVE_SUMMARY", "").lower() in ("1", "true"),
        )
