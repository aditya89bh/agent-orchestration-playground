"""Retry policy primitives for resilient orchestration loops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetryDecision:
    """Decision returned by a retry policy after reviewing an attempt."""

    should_retry: bool
    reason: str
    next_attempt: int


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retry policy for deterministic orchestration attempts."""

    max_attempts: int = 2
    minimum_score: int = 6

    def decide(self, attempt: int, review: dict[str, Any]) -> RetryDecision:
        """Decide whether another build-review attempt should run."""
        approved = bool(review.get("approved", False))
        score = int(review.get("score", 0))

        if approved and score >= self.minimum_score:
            return RetryDecision(
                should_retry=False,
                reason="review_approved",
                next_attempt=attempt,
            )

        if attempt >= self.max_attempts:
            return RetryDecision(
                should_retry=False,
                reason="max_attempts_reached",
                next_attempt=attempt,
            )

        return RetryDecision(
            should_retry=True,
            reason="review_not_approved",
            next_attempt=attempt + 1,
        )
