from __future__ import annotations

from supabase import create_client

from phase6_deploy.config import Settings

PAGE = 1000


def _count_table(client, schema: str, table: str) -> int | None:
    try:
        total = 0
        offset = 0
        schema_client = client.schema(schema)
        while True:
            response = (
                schema_client.table(table)
                .select("id", count="exact")
                .range(offset, offset + PAGE - 1)
                .execute()
            )
            batch = response.data or []
            total += len(batch)
            if len(batch) < PAGE:
                break
            offset += PAGE
        return total
    except Exception:  # noqa: BLE001
        return None


def reconcile_layers(settings: Settings) -> tuple[list[str], dict[str, int | None]]:
    """Cross-layer integrity warnings (edge case C.4)."""
    warnings: list[str] = []
    counts: dict[str, int | None] = {}

    if not settings.supabase_url or not settings.supabase_anon_key:
        return ["Supabase credentials required for reconciliation"], counts

    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    counts["raw_feedback_items"] = _count_table(client, "raw", "feedback_items")
    counts["clean_feedback_items"] = _count_table(client, "clean", "feedback_items")
    counts["synthesis_runs"] = _count_table(client, "insights", "synthesis_runs")

    raw = counts.get("raw_feedback_items")
    clean = counts.get("clean_feedback_items")
    if raw is not None and clean is not None and clean > raw:
        warnings.append(f"Clean count ({clean}) exceeds raw ({raw}) — investigate cleaning pipeline")

    if clean is not None and clean == 0:
        warnings.append("Clean layer is empty — dashboard will have no trends")

    runs = counts.get("synthesis_runs")
    if runs is not None and runs == 0:
        warnings.append("No synthesis runs — run Phase 3 before go-live")

    return warnings, counts
