from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from phase3_insights.config import Settings
from phase3_insights.prompts import SYSTEM_PROMPT, extract_json
from phase3_insights.rate_limiter import GroqDailyBudgetExceeded, GroqRateLimiter

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_429_RETRIES = 3


class GroqError(Exception):
    pass


class GroqRateLimitError(GroqError):
    pass


@dataclass(frozen=True)
class GroqCompletion:
    data: dict
    tokens_used: int


class GroqClient:
    def __init__(self, settings: Settings, rate_limiter: GroqRateLimiter) -> None:
        self._settings = settings
        self._rate_limiter = rate_limiter
        self._headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    def complete_json(self, user_prompt: str) -> GroqCompletion:
        if not self._rate_limiter.can_make_request():
            raise GroqDailyBudgetExceeded(self._rate_limiter.summary())

        self._rate_limiter.wait_for_slot()

        payload = {
            "model": self._settings.groq_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        last_error: Exception | None = None
        for attempt in range(MAX_429_RETRIES):
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(GROQ_API_URL, headers=self._headers, json=payload)
                    if response.status_code == 429:
                        retry_after = min(float(response.headers.get("retry-after", "30")), 30.0)
                        print(
                            f"Groq 429: waiting {retry_after:.0f}s "
                            f"(attempt {attempt + 1}/{MAX_429_RETRIES})...",
                            flush=True,
                        )
                        time.sleep(retry_after)
                        last_error = GroqRateLimitError("Groq rate limit hit")
                        continue
                    if response.status_code >= 400:
                        raise GroqError(
                            f"Groq API error {response.status_code}: {response.text}"
                        )
                    body = response.json()
                    tokens = int(body.get("usage", {}).get("total_tokens", 0))
                    self._rate_limiter.record_request(tokens)
                    content = body["choices"][0]["message"]["content"]
                    return GroqCompletion(data=extract_json(content), tokens_used=tokens)
            except httpx.TransportError as exc:
                last_error = exc
                time.sleep(2 ** attempt)

        raise GroqRateLimitError(str(last_error or "Groq request failed after retries"))
