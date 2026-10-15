"""AxiomCode request limits (W3) — per-key rate limiting + proof
concurrency, in-process and dependency-free.

RateLimiter: sliding window per key (default 60 requests / 60 s,
AXIOMCODE_RATE_LIMIT_PER_MIN). ConcurrencyGate: at most N proofs in
flight per key (default 2, AXIOMCODE_MAX_CONCURRENT_PROOFS) — a Lean
build is the expensive unit, so concurrency is gated separately from
request rate.

State is per-process by design: each server process enforces its own
limits. (A multi-process deployment would move these to the store;
the single-host launch topology does not need it.)
"""

import os
import threading
import time
from collections import deque

RATE_LIMIT_PER_MIN = int(os.environ.get("AXIOMCODE_RATE_LIMIT_PER_MIN", "60"))
MAX_CONCURRENT_PROOFS = int(os.environ.get("AXIOMCODE_MAX_CONCURRENT_PROOFS", "2"))


class RateLimiter:
    """Sliding-window limiter: allow(key) is True while fewer than
    `limit` requests from `key` landed in the last `window_s` seconds."""

    def __init__(self, limit: int = RATE_LIMIT_PER_MIN, window_s: float = 60.0):
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_s
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True


class ConcurrencyGate:
    """Per-key cap on simultaneous proofs. acquire() is non-blocking:
    False means the key is already at its cap (caller answers 429 /
    a rate_limited error rather than queueing unboundedly)."""

    def __init__(self, limit: int = MAX_CONCURRENT_PROOFS):
        self.limit = limit
        self._in_flight: dict[str, int] = {}
        self._lock = threading.Lock()

    def acquire(self, key: str) -> bool:
        with self._lock:
            if self._in_flight.get(key, 0) >= self.limit:
                return False
            self._in_flight[key] = self._in_flight.get(key, 0) + 1
            return True

    def release(self, key: str) -> None:
        with self._lock:
            n = self._in_flight.get(key, 0)
            if n <= 1:
                self._in_flight.pop(key, None)
            else:
                self._in_flight[key] = n - 1

    def in_flight(self, key: str) -> int:
        with self._lock:
            return self._in_flight.get(key, 0)
