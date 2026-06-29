from __future__ import annotations

from phase3_insights.config import Settings


def run_preflight(settings: Settings) -> None:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is missing")
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError("Supabase credentials are missing")
    print("PREFLIGHT OK (Groq + Supabase)", flush=True)
