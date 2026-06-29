from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase5_ops.db import Database


def write_health_report(
  db: Database,
  snapshot: dict[str, Any],
  alerts_fired: int,
  theme_spikes: list[dict[str, Any]],
  *,
  output_dir: Path,
) -> Path:
    """Write a JSON + Markdown ops report for the weekly review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    open_actions = db.list_open_review_actions()

    payload = {
        "snapshot": snapshot,
        "alerts_fired": alerts_fired,
        "theme_spikes": theme_spikes[:10],
        "open_review_actions": open_actions,
    }

    json_path = output_dir / "latest_health_report.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Pipeline health report",
        "",
        f"- **Trigger:** {snapshot.get('trigger')}",
        f"- **Clean corpus:** {snapshot.get('corpus_clean_total'):,} items "
        f"({snapshot.get('corpus_rated_total'):,} rated)",
        f"- **Synthesis status:** {snapshot.get('synthesis_status') or 'n/a'}",
        f"- **Synthesis model:** {snapshot.get('synthesis_model') or 'n/a'}",
        f"- **Collection failures (7d):** {snapshot.get('collection_failures', 0)}",
        f"- **Alerts fired this run:** {alerts_fired}",
        "",
        "## Collection by source (7d)",
        "",
    ]
    for source, data in (snapshot.get("collection_by_source") or {}).items():
        lines.append(
            f"- **{source}:** {data.get('items_collected_7d', 0)} items, "
            f"{data.get('runs_7d', 0)} runs, latest status `{data.get('latest_status')}`"
        )

    if theme_spikes:
        lines.extend(["", "## Rising themes (sustained spike)", ""])
        for spike in theme_spikes[:10]:
            lines.append(
                f"- `{spike['question_id']}` **{spike['theme']}**: "
                f"{spike['previous_count']} → {spike['current_count']} "
                f"(+{spike['pct_change']}%)"
            )

    if open_actions:
        lines.extend(["", "## Open review actions", ""])
        for action in open_actions:
            lines.append(
                f"- [{action.get('status')}] {action.get('insight_summary')} "
                f"(owner: {action.get('action_owner') or 'unassigned'})"
            )

    md_path = output_dir / "latest_health_report.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path
