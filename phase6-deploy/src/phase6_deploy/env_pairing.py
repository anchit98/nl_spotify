from __future__ import annotations

from phase6_deploy.config import Settings, supabase_project_ref


def validate_env_pairing(settings: Settings) -> list[str]:
    """Return list of errors; empty means OK (edge case 6.3)."""
    errors: list[str] = []

    if not settings.supabase_url:
        errors.append("SUPABASE_PROJECT_URL is not set")
        return errors

    actual_ref = supabase_project_ref(settings.supabase_url)
    if settings.expected_supabase_ref and actual_ref != settings.expected_supabase_ref:
        errors.append(
            f"Supabase project ref mismatch: URL has '{actual_ref}', "
            f"EXPECTED_SUPABASE_PROJECT_REF is '{settings.expected_supabase_ref}'"
        )

    if settings.app_env == "production" and "localhost" in (settings.supabase_url or ""):
        errors.append("Production APP_ENV cannot use localhost Supabase URL")

    if settings.app_env == "staging" and settings.production_api_url:
        if settings.supabase_url and settings.production_api_url in settings.supabase_url:
            errors.append("Staging appears to reference production API URL in Supabase config")

    return errors
