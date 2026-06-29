from __future__ import annotations

import httpx

from phase6_deploy.config import Settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def run_groq_smoke(settings: Settings) -> tuple[bool, str]:
    """Tiny Groq prompt to confirm API key works (edge case 6.1 / CI)."""
    if not settings.groq_api_key:
        return False, "GROQ_API_KEY not set"
    payload = {
        "model": settings.groq_model,
        "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
        "max_tokens": 5,
        "temperature": 0,
    }
    try:
        response = httpx.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
        if response.status_code != 200:
            return False, f"Groq HTTP {response.status_code}: {response.text[:200]}"
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return True, f"Groq smoke OK (tokens={usage.get('total_tokens', '?')}, reply={content!r})"
    except Exception as exc:  # noqa: BLE001
        return False, f"Groq smoke failed: {exc}"
