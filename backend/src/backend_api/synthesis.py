from __future__ import annotations

import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend_api.config import Settings
from backend_api.db import InsightsDatabase, clear_response_caches

_lock = threading.Lock()
_job_running = False
_pipeline_phase: str | None = None
_pipeline_started_at: str | None = None
_pipeline_message: str | None = None


def _phase_python(repo_root: Path, phase_dir: str) -> Path:
    env_key = f"{phase_dir.upper().replace('-', '_')}_PYTHON"
    override = os.getenv(env_key)
    if override:
        return Path(override)
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    candidate = repo_root / phase_dir / ".venv" / scripts / ("python.exe" if sys.platform == "win32" else "python")
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def _run_phase(
    python: Path,
    module: str,
    *,
    cwd: Path,
    pythonpath: Path,
    extra_args: list[str] | None = None,
) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(pythonpath)
    cmd = [str(python), "-m", module, *(extra_args or [])]
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        check=False,
        capture_output=False,
    )
    return result.returncode


def synthesis_status(db: InsightsDatabase) -> dict[str, Any]:
    running = db.get_running_run()
    return {
        "in_progress": running is not None or _job_running,
        "phase": _pipeline_phase,
        "message": _pipeline_message,
        "started_at": _pipeline_started_at,
        "run": running,
    }


def start_synthesis(settings: Settings, db: InsightsDatabase) -> dict[str, Any]:
    global _job_running, _pipeline_phase, _pipeline_started_at, _pipeline_message

    with _lock:
        if _job_running or db.get_running_run():
            return {"started": False, "reason": "Synthesis already in progress"}

        _job_running = True
        _pipeline_phase = "collecting"
        _pipeline_started_at = datetime.now(timezone.utc).isoformat()
        _pipeline_message = "Collecting new reviews since last update"

    def _worker() -> None:
        global _job_running, _pipeline_phase, _pipeline_message

        repo = settings.repo_root
        warnings: list[str] = []

        try:
            collect_rc = _run_phase(
                _phase_python(repo, "phase1-collection"),
                "phase1_collection.runner",
                cwd=repo / "phase1-collection",
                pythonpath=repo / "phase1-collection" / "src",
                extra_args=["--mode", "weekly"],
            )
            if collect_rc != 0:
                warnings.append("collection had errors")

            _pipeline_phase = "cleaning"
            _pipeline_message = "Cleaning newly collected reviews"

            clean_rc = _run_phase(
                _phase_python(repo, "phase2-cleaning"),
                "phase2_cleaning.cleaner",
                cwd=repo / "phase2-cleaning",
                pythonpath=repo / "phase2-cleaning" / "src",
            )
            if clean_rc != 0:
                warnings.append("cleaning failed")
                _pipeline_message = "Cleaning failed — pipeline stopped"
                return

            clear_response_caches()

            _pipeline_phase = "synthesizing"
            _pipeline_message = (
                "Synthesizing insights from full review corpus"
                + (" (after collection warnings)" if warnings else "")
            )

            synth_rc = _run_phase(
                _phase_python(repo, "phase3-enrichment"),
                "phase3_insights.synthesizer",
                cwd=repo / "phase3-enrichment",
                pythonpath=repo / "phase3-enrichment" / "src",
            )
            if synth_rc != 0:
                _pipeline_message = "Synthesis failed"
            elif warnings:
                _pipeline_message = "Complete with warnings: " + ", ".join(warnings)
            else:
                _pipeline_message = "Pipeline complete"

            clear_response_caches()

        finally:
            with _lock:
                _job_running = False
                _pipeline_phase = None

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return {
        "started": True,
        "message": "Pipeline started: collect → clean → synthesize",
    }
