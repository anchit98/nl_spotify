from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Patterns that must not appear in committed source (edge case 6.2)
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("groq_api_key", re.compile(r"gsk_[A-Za-z0-9]{20,}")),
    ("supabase_jwt", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "__pycache__",
    "dist",
    "build",
}

ALLOWLIST_FILES = {
    ".env.example",
    "phase1-collection/.env.example",
    "phase2-cleaning/.env.example",
    "phase3-enrichment/.env.example",
    "phase5-operations/.env.example",
    "phase6-deploy/.env.example",
    "backend/.env.example",
    "frontend/.env.example",
}

FORBIDDEN_TRACKED = {".env", "frontend/.env.local"}


def _tracked_files(repo_root: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            capture_output=True,
            check=True,
        )
        paths = [p for p in result.stdout.decode("utf-8", errors="ignore").split("\0") if p]
        return [repo_root / p for p in paths]
    except (OSError, subprocess.CalledProcessError):
        return None


def scan_repo(repo_root: Path) -> list[str]:
    findings: list[str] = []
    tracked = _tracked_files(repo_root)
    if tracked is not None:
        candidates = tracked
    else:
        candidates = [
            path
            for path in repo_root.rglob("*")
            if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
        ]

    for path in candidates:
        rel = path.relative_to(repo_root).as_posix()
        if rel in FORBIDDEN_TRACKED:
            findings.append(f"Tracked secret file: {rel}")
            continue
        if rel in ALLOWLIST_FILES or rel.endswith(".env.example"):
            continue
        if rel == ".env" or rel.endswith("/.env") or rel.endswith(".env.local"):
            findings.append(f"Committed env file: {rel}")
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(text) > 500_000:
            continue
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{name} pattern in {rel}")
    return findings
