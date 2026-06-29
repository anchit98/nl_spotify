import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parent

def load_environment() -> None:
    load_dotenv(PACKAGE_ROOT / ".env")
    load_dotenv(REPO_ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_environment()
        url = os.getenv("SUPABASE_PROJECT_URL") or os.getenv("SUPABASE_URL")
        anon = os.getenv("SUPABASE_PROJECT_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not anon:
            raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_PROJECT_ANON_KEY are required")
        
        return cls(
            supabase_url=url.rstrip("/"),
            supabase_anon_key=anon,
        )
