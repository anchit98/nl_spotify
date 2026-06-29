from __future__ import annotations

import os

from phase5_ops.config import Settings


def run_preflight(settings: Settings) -> None:
    missing = []
    for name, aliases in (
        ("SUPABASE_PROJECT_URL", ("SUPABASE_URL",)),
        ("SUPABASE_PROJECT_ANON_KEY", ("SUPABASE_ANON_KEY",)),
    ):
        if not os.getenv(name) and not any(os.getenv(a) for a in aliases):
            missing.append(name)
    if missing:
        raise ValueError(f"Missing required env: {', '.join(missing)}")
    if not settings.alert_webhook_url:
        print("WARN: ALERT_WEBHOOK_URL not set — alerts will be stored in ops.alerts only.")
    print("PREFLIGHT OK (Phase 5 operations)")
