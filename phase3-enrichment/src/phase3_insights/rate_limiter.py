from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class GroqModelLimits:
    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int
    tokens_per_day: int


MODEL_LIMITS: dict[str, GroqModelLimits] = {
    "llama-3.3-70b-versatile": GroqModelLimits(
        requests_per_minute=30,
        requests_per_day=1_000,
        tokens_per_minute=12_000,
        tokens_per_day=100_000,
    ),
}

# Full synthesis run = 6 question calls + 1 executive summary
SYNTHESIS_CALLS_PER_RUN = 7


class GroqDailyBudgetExceeded(Exception):
    """Raised when the daily Groq quota is exhausted."""


class GroqRateLimiter:
    """Tracks per-minute and per-day Groq usage with a safety margin."""

    def __init__(
        self,
        limits: GroqModelLimits,
        *,
        daily_requests: int = 0,
        daily_tokens: int = 0,
        safety_margin: float = 0.05,
        default_tokens_per_request: int = 6_000,
    ) -> None:
        self._limits = limits
        self._daily_requests = daily_requests
        self._daily_tokens = daily_tokens
        self._safety_margin = safety_margin
        self._estimated_tokens = default_tokens_per_request
        self._minute_request_times: deque[float] = deque()
        self._minute_token_events: deque[tuple[float, int]] = deque()
        self._last_request_at: float | None = None

    @property
    def estimated_tokens_per_request(self) -> int:
        return self._estimated_tokens

    @property
    def daily_requests(self) -> int:
        return self._daily_requests

    @property
    def daily_tokens(self) -> int:
        return self._daily_tokens

    @property
    def min_interval_seconds(self) -> float:
        rpm_interval = 60.0 / self._limits.requests_per_minute
        tpm_interval = 60.0 * self._estimated_tokens / self._limits.tokens_per_minute
        return max(rpm_interval, tpm_interval, 2.0)

    def remaining_daily_requests(self) -> int:
        return max(0, self._limits.requests_per_day - self._daily_requests)

    def remaining_daily_tokens(self) -> int:
        return max(0, self._limits.tokens_per_day - self._daily_tokens)

    def can_complete_synthesis_run(self) -> bool:
        needed_tokens = self._estimated_tokens * SYNTHESIS_CALLS_PER_RUN
        return (
            self.remaining_daily_requests() >= SYNTHESIS_CALLS_PER_RUN
            and self.remaining_daily_tokens() >= int(needed_tokens * (1 + self._safety_margin))
        )

    def can_make_request(self, estimated_tokens: int | None = None) -> bool:
        est = estimated_tokens if estimated_tokens is not None else self._estimated_tokens
        if self._daily_requests >= self._limits.requests_per_day:
            return False
        if self._daily_tokens + est > int(self._limits.tokens_per_day * (1 - self._safety_margin)):
            return False
        return True

    def wait_for_slot(self, estimated_tokens: int | None = None) -> None:
        est = estimated_tokens if estimated_tokens is not None else self._estimated_tokens
        while True:
            now = time.time()

            if self._last_request_at is not None:
                elapsed = now - self._last_request_at
                if elapsed < self.min_interval_seconds:
                    time.sleep(self.min_interval_seconds - elapsed)
                    now = time.time()

            self._prune_minute_window(now)

            if (
                self._minute_request_count() < self._limits.requests_per_minute
                and self._minute_token_count() + est <= self._limits.tokens_per_minute
            ):
                return

            if self._minute_request_times:
                wait_until = self._minute_request_times[0] + 60.05
            else:
                wait_until = now + 2.0

            sleep_for = max(0.5, wait_until - now)
            print(f"Rate limit: waiting {sleep_for:.1f}s (RPM/TPM window)...", flush=True)
            time.sleep(sleep_for)

    def _prune_minute_window(self, now: float) -> None:
        while self._minute_request_times and now - self._minute_request_times[0] >= 60:
            self._minute_request_times.popleft()
        while self._minute_token_events and now - self._minute_token_events[0][0] >= 60:
            self._minute_token_events.popleft()

    def _minute_request_count(self) -> int:
        return len(self._minute_request_times)

    def _minute_token_count(self) -> int:
        return sum(tokens for _, tokens in self._minute_token_events)

    def record_request(self, tokens: int) -> None:
        now = time.time()
        self._last_request_at = now
        self._minute_request_times.append(now)
        self._minute_token_events.append((now, tokens))
        self._daily_requests += 1
        self._daily_tokens += tokens
        if tokens > 0:
            self._estimated_tokens = int(0.7 * self._estimated_tokens + 0.3 * tokens)

    def summary(self) -> str:
        return (
            f"daily requests {self._daily_requests}/{self._limits.requests_per_day}, "
            f"daily tokens {self._daily_tokens}/{self._limits.tokens_per_day}, "
            f"est. {self._estimated_tokens} tokens/call"
        )
