"""Lightweight streaming metrics.

Small, allocation-light counters used to aggregate per-stream and per-fetch
statistics. Not a monitoring framework: just a bounded dict of monotonic
counters plus a tiny ring buffer of recent per-stream records for the /status
endpoint. All mutation happens on the asyncio event loop thread.
"""

import time
from collections import deque
from typing import Any


class StreamMetrics:
    def __init__(self, recent_capacity: int = 200):
        self.started_at = time.monotonic()
        self._counters: dict[str, int] = {}
        self._totals: dict[str, float] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=recent_capacity)
        self._active_streams = 0
        self._timing_totals: dict[str, float] = {}
        self._timing_counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + n

    def total(self, name: str, value: float) -> None:
        self._totals[name] = self._totals.get(name, 0) + value

    def stream_started(self) -> None:
        self._active_streams += 1

    def stream_finished(self) -> None:
        self._active_streams = max(0, self._active_streams - 1)

    def observe_timing(self, name: str, seconds: float) -> None:
        """Record a non-negative duration and expose its rolling average."""
        if seconds < 0:
            return
        self._timing_totals[name] = self._timing_totals.get(name, 0.0) + seconds
        self._timing_counts[name] = self._timing_counts.get(name, 0) + 1

    def record_stream(self, entry: dict[str, Any]) -> None:
        self._recent.append(entry)
        # keep summary counters rolling
        self.inc("streams_total")
        if entry.get("status") == "cancelled":
            self.inc("streams_cancelled")
        elif entry.get("error"):
            self.inc("streams_errors")
        else:
            self.inc("streams_completed")
        dur = entry.get("duration", 0.0)
        self.total("stream_duration_seconds", dur)
        self.observe_timing("operation", float(dur))
        sent = entry.get("bytes_sent", 0)
        self.total("stream_bytes_sent", sent)
        for name in ("startup", "operation"):
            value = entry.get(f"{name}_seconds", entry.get(f"{name}_duration"))
            if value is not None:
                self.observe_timing(name, float(value))

    def snapshot(self) -> dict[str, Any]:
        uptime = time.monotonic() - self.started_at
        timings = {
            name: {
                "count": self._timing_counts[name],
                "total_seconds": round(self._timing_totals[name], 3),
                "average_seconds": round(
                    self._timing_totals[name] / self._timing_counts[name], 3
                ),
            }
            for name in self._timing_totals
        }
        return {
            "uptime_seconds": round(uptime, 1),
            "active_streams": self._active_streams,
            "counters": dict(self._counters),
            "totals": dict(self._totals),
            "timings": timings,
            "average_startup_seconds": timings.get("startup", {}).get("average_seconds", 0.0),
            "average_operation_seconds": timings.get("operation", {}).get("average_seconds", 0.0),
            "recent_streams": list(self._recent),
        }