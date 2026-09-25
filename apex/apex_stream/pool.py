"""Telegram client pool with health tracking and least-loaded selection.

Inspired by FileToLink's workloads[client] approach but made idiomatic for an
asyncio/Pyrogram process:

- each client tracks active request/stream workload, consecutive failures,
  last failure time and a cooldown window
- selection always picks the healthy client with the lowest active workload
  that is still below its per-client concurrency ceiling
- a client that repeatedly fails goes into cooldown and is skipped; after the
  cooldown elapses it is re-checked on the next selection pass
- cancellations are reported as neutral (not telegram errors), so an FFmpeg
  stop / client disconnect never trips the circuit breaker

Telegram is NOT imported here: the `client` payload is opaque. That keeps the
pool unit-testable.
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

# Client health states
HEALTHY = "healthy"
DEGRADED = "degraded"
COOLDOWN = "cooldown"
UNAVAILABLE = "unavailable"


class NoClientAvailable(Exception):
    """Raised when every client is at capacity or in cooldown."""


@dataclass
class ClientHandle:
    client_id: int
    client: Any
    max_streams: int = 8
    state: str = HEALTHY
    active_requests: int = 0
    active_streams: int = 0
    consecutive_failures: int = 0
    success_count: int = 0
    failure_count: int = 0
    cooldown_count: int = 0
    rate_limit_count: int = 0
    last_failure_ts: float = 0.0
    last_success_ts: float = 0.0
    cooldown_until: float = 0.0
    created_ts: float = field(default_factory=time.monotonic)
    dc_id: Optional[int] = None

    def is_available(self, now: float) -> bool:
        if self.state == UNAVAILABLE:
            return False
        if self.state == COOLDOWN:
            return now >= self.cooldown_until
        return True

    def current_load(self) -> tuple[int, int]:
        # primary sort: active streams; tie-break: total active requests
        return (self.active_streams, self.active_requests)


class ClientPool:
    def __init__(
        self,
        max_streams_per_client: int = 8,
        failure_threshold: int = 3,
        cooldown_seconds: int = 30,
        logger: Optional[Any] = None,
    ):
        self.max_streams_per_client = max_streams_per_client
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.logger = logger
        self._clients: dict[int, ClientHandle] = {}
        self._lock = asyncio.Lock()
        self._success_count = 0
        self._failure_count = 0
        self._cooldown_count = 0

    def __len__(self) -> int:
        return len(self._clients)

    async def register(
        self,
        client_id: int,
        client: Any,
        *,
        ready: bool = True,
        dc_id: Optional[int] = None,
    ) -> ClientHandle:
        async with self._lock:
            handle = ClientHandle(
                client_id=client_id,
                client=client,
                max_streams=self.max_streams_per_client,
                state=HEALTHY if ready else DEGRADED,
                dc_id=dc_id,
            )
            self._clients[client_id] = handle
            return handle

    async def unregister(self, client_id: int) -> None:
        async with self._lock:
            self._clients.pop(client_id, None)

    async def set_state(self, client_id: int, state: str) -> None:
        async with self._lock:
            handle = self._clients.get(client_id)
            if handle:
                handle.state = state

    def _eligible(self, now: float) -> list[ClientHandle]:
        out = []
        for handle in self._clients.values():
            if not handle.is_available(now):
                continue
            # re-open a client whose cooldown has elapsed
            if handle.state == COOLDOWN:
                handle.state = DEGRADED
            if handle.active_streams >= handle.max_streams:
                continue
            out.append(handle)
        return out

    async def select(self, avoid: Optional[int] = None, dc_id: Optional[int] = None) -> ClientHandle:
        """Pick the least-loaded eligible client, or raise NoClientAvailable.

        When `avoid` is set and another eligible client exists, that client is
        skipped so a failed run reconnects to a *different* pool member.

        When `dc_id` is set, clients whose primary DC equals it are preferred:
        a same-DC client can fetch 1 MiB chunks without an auth.ExportAuthorization
        RPC (that RPC flood-waits the account when repeated), so a matching
        client is picked even if it is busier than a non-matching one. Clients
        on other DCs are still used as a fallback (fewer exports > none).
        """
        now = time.monotonic()
        async with self._lock:
            eligible = self._eligible(now)
            if not eligible:
                raise NoClientAvailable(
                    "all Telegram clients at capacity or in cooldown"
                )
            if dc_id is not None:
                preferred = [h for h in eligible if h.dc_id == dc_id]
                if len(preferred) >= 1 and (
                    len(preferred) > 1 or len(eligible) > len(preferred)
                ):
                    if len(preferred) > 1:
                        eligible = preferred
                    else:
                        # a single preferred client exists: use it only when it
                        # is not the avoided one or when no alternative exists
                        if preferred[0].client_id != avoid:
                            eligible = preferred
            candidates = eligible
            if avoid is not None and len(eligible) > 1:
                others = [h for h in eligible if h.client_id != avoid]
                if others:
                    candidates = others
            chosen = min(candidates, key=lambda h: h.current_load())
            chosen.active_streams += 1
            chosen.active_requests += 1
            return chosen

    async def release(self, client_id: int) -> None:
        async with self._lock:
            handle = self._clients.get(client_id)
            if not handle:
                return
            handle.active_streams = max(0, handle.active_streams - 1)
            handle.active_requests = max(0, handle.active_requests - 1)

    async def note_success(self, client_id: int) -> None:
        async with self._lock:
            handle = self._clients.get(client_id)
            if not handle:
                return
            handle.success_count += 1
            handle.last_success_ts = time.monotonic()
            self._success_count += 1
            handle.consecutive_failures = 0
            if handle.state == COOLDOWN:
                handle.state = DEGRADED
            elif handle.state == DEGRADED:
                handle.state = HEALTHY

    async def note_failure(
        self,
        client_id: int,
        *,
        telegram_error: bool,
        cooldown_seconds: Optional[int] = None,
    ) -> None:
        async with self._lock:
            handle = self._clients.get(client_id)
            if not handle:
                return
            if not telegram_error:
                # Cancellation / client-disconnect / FFmpeg stop: not a transport
                # failure, must not trip cooldown.
                return
            handle.consecutive_failures += 1
            handle.failure_count += 1
            self._failure_count += 1
            handle.last_failure_ts = time.monotonic()
            if cooldown_seconds is not None:
                handle.rate_limit_count += 1
            if handle.consecutive_failures >= self.failure_threshold:
                handle.state = COOLDOWN
                handle.cooldown_count += 1
                self._cooldown_count += 1
                cooldown = max(
                    self.cooldown_seconds,
                    int(cooldown_seconds or 0),
                )
                handle.cooldown_until = handle.last_failure_ts + cooldown
                if self.logger:
                    reason = (
                        f"rate-limit={cooldown_seconds}s"
                        if cooldown_seconds is not None
                        else "transport failure"
                    )
                    self.logger.warning(
                        f"[POOL] client={client_id} entered COOLDOWN for {cooldown}s "
                        f"({handle.consecutive_failures} failures; {reason})"
                    )
            elif handle.state == HEALTHY:
                handle.state = DEGRADED

    def snapshot(self) -> dict:
        now = time.monotonic()
        clients = list(self._clients.values())
        return {
            "total": len(self._clients),
            "max_streams_per_client": self.max_streams_per_client,
            "active_streams": sum(h.active_streams for h in clients),
            "active_requests": sum(h.active_requests for h in clients),
            "counters": {
                "successes": self._success_count,
                "failures": self._failure_count,
                "cooldowns": self._cooldown_count,
            },
            "states": {
                state: sum(h.state == state for h in clients)
                for state in (HEALTHY, DEGRADED, COOLDOWN, UNAVAILABLE)
            },
            "clients": [
                {
                    "id": h.client_id,
                    "state": h.state,
                    "active_streams": h.active_streams,
                    "active_requests": h.active_requests,
                    "consecutive_failures": h.consecutive_failures,
                    "success_count": h.success_count,
                    "failure_count": h.failure_count,
                    "cooldown_count": h.cooldown_count,
                    "rate_limit_count": h.rate_limit_count,
                    "last_failure_ts": round(h.last_failure_ts, 2),
                    "last_success_ts": round(h.last_success_ts, 2),
                    "cooldown_remaining": max(0.0, h.cooldown_until - now),
                    "max_streams": h.max_streams,
                    "dc_id": h.dc_id,
                }
                for h in self._clients.values()
            ],
        }