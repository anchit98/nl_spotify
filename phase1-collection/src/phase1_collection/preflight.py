from __future__ import annotations

import os
import sys
from typing import Iterable

from phase1_collection.config import ALL_SOURCES, Settings, load_source_signoff


REQUIRED_SECRETS = (
    "SUPABASE_PROJECT_URL",
    "SUPABASE_PROJECT_ANON_KEY",
)

# Accept alternate Supabase env names used in some setups.
SECRET_ALIASES: dict[str, tuple[str, ...]] = {
    "SUPABASE_PROJECT_URL": ("SUPABASE_URL",),
    "SUPABASE_PROJECT_ANON_KEY": ("SUPABASE_ANON_KEY",),
}


def _resolve_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value and str(value).strip():
        return value
    for alias in SECRET_ALIASES.get(name, ()):
        value = os.getenv(alias)
        if value and str(value).strip():
            return value
    return None


def check_env_vars(names: Iterable[str]) -> list[str]:
    missing = []
    for name in names:
        if not _resolve_secret(name):
            missing.append(name)
    return missing


def run_preflight(settings: Settings, sources: Iterable[str]) -> None:
    missing = check_env_vars(REQUIRED_SECRETS)

    if missing:
        joined = ", ".join(sorted(set(missing)))
        print(f"PREFLIGHT FAILED: missing required secrets: {joined}", file=sys.stderr)
        sys.exit(1)

    signoff = load_source_signoff()
    blocked = []
    for source in sources:
        meta = signoff.get(source, {})
        if not meta.get("approved"):
            blocked.append(source)

    if blocked:
        joined = ", ".join(blocked)
        print(
            f"PREFLIGHT FAILED: legal sign-off not approved for: {joined}. "
            "Update config/source_signoff.yaml after review.",
            file=sys.stderr,
        )
        sys.exit(1)

    unknown = [s for s in sources if s not in ALL_SOURCES]
    if unknown:
        joined = ", ".join(unknown)
        print(f"PREFLIGHT FAILED: unknown sources: {joined}", file=sys.stderr)
        sys.exit(1)

    print("PREFLIGHT OK (public sources + Supabase API)")
