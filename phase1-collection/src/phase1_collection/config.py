from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parent
CONFIG_DIR = PACKAGE_ROOT / "config"
SIGNOFF_PATH = CONFIG_DIR / "source_signoff.yaml"

ALL_SOURCES = (
    "app_store",
    "google_play",
    "reddit",
    "community_forum",
    "social_media",
)


def load_environment() -> None:
    """Load env from phase1-collection/.env then repo-root .env (repo wins)."""
    load_dotenv(PACKAGE_ROOT / ".env")
    load_dotenv(REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str | None
    initial_lookback_days: int
    adhoc_lookback_days: int
    enabled_sources: tuple[str, ...]
    reddit_user_agent: str
    spotify_app_store_id: str
    spotify_play_store_id: str

    @classmethod
    def from_env(cls) -> Settings:
        load_environment()
        url = os.getenv("SUPABASE_PROJECT_URL") or os.getenv("SUPABASE_URL")
        anon = os.getenv("SUPABASE_PROJECT_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not anon:
            raise ValueError(
                "SUPABASE_PROJECT_URL and SUPABASE_PROJECT_ANON_KEY are required"
            )

        enabled_raw = os.getenv("ENABLED_SOURCES", ",".join(ALL_SOURCES))
        enabled = tuple(s.strip() for s in enabled_raw.split(",") if s.strip())
        return cls(
            supabase_url=url.rstrip("/"),
            supabase_anon_key=anon,
            supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET"),
            initial_lookback_days=int(os.getenv("INITIAL_LOOKBACK_DAYS", "90")),
            adhoc_lookback_days=int(os.getenv("ADHOC_LOOKBACK_DAYS", "7")),
            enabled_sources=enabled,
            reddit_user_agent=os.getenv(
                "REDDIT_USER_AGENT",
                "nl-spotify-collector/1.0 (public collection)",
            ),
            spotify_app_store_id=os.getenv("SPOTIFY_APP_STORE_ID", "324684580"),
            spotify_play_store_id=os.getenv("SPOTIFY_PLAY_STORE_ID", "com.spotify.music"),
        )


def load_source_signoff() -> dict[str, dict]:
    with SIGNOFF_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data.get("sources", {})


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def initial_window_start(settings: Settings) -> datetime:
    return utc_now() - timedelta(days=settings.initial_lookback_days)
