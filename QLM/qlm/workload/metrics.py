"""
Metrics collection for QLM workload experiments: queue length, scheduling delay, backpressure (GPU proxy).
"""

import json
import time
from pathlib import Path
from typing import Callable, List, Optional


class ExperimentMetrics:
    """
    Records time-series and per-request metrics for workload sensitivity experiments.
    """

    def __init__(self):
        self.queue_length_samples: List[dict] = []  # [{"t": ts, "length": n}, ...]
        self.scheduling_delays: List[dict] = []     # [{"request_id": id, "delay_ms": x, "t": ts}, ...]
        self.backpressure_samples: List[dict] = [] # [{"t": ts, "backpressure": n}, ...]
        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None

    def start(self) -> None:
        self.started_at = time.time()

    def stop(self) -> None:
        self.stopped_at = time.time()

    def record_queue_length(self, length: int) -> None:
        self.queue_length_samples.append({"t": time.time(), "length": length})

    def record_scheduling_delay(self, request_id: str, insertion_time: float, dispatch_time: float) -> None:
        delay_ms = (dispatch_time - insertion_time) * 1000.0
        self.scheduling_delays.append({
            "request_id": str(request_id),
            "delay_ms": delay_ms,
            "insertion_time": insertion_time,
            "dispatch_time": dispatch_time,
        })

    def record_backpressure(self, backpressure: float) -> None:
        self.backpressure_samples.append({"t": time.time(), "backpressure": backpressure})

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "duration_sec": (self.stopped_at - self.started_at) if self.stopped_at and self.started_at else None,
            "queue_length_samples": self.queue_length_samples,
            "scheduling_delays": self.scheduling_delays,
            "backpressure_samples": self.backpressure_samples,
            "summary": self._summary(),
        }

    def _summary(self) -> dict:
        delays = [d["delay_ms"] for d in self.scheduling_delays]
        qlens = [s["length"] for s in self.queue_length_samples]
        bp = [s["backpressure"] for s in self.backpressure_samples]
        return {
            "num_requests_dispatched": len(self.scheduling_delays),
            "scheduling_delay_ms_mean": sum(delays) / len(delays) if delays else None,
            "scheduling_delay_ms_p50": sorted(delays)[len(delays) // 2] if delays else None,
            "scheduling_delay_ms_p99": sorted(delays)[int(len(delays) * 0.99)] if len(delays) > 1 else (delays[0] if delays else None),
            "queue_length_mean": sum(qlens) / len(qlens) if qlens else None,
            "queue_length_max": max(qlens) if qlens else None,
            "backpressure_mean": sum(bp) / len(bp) if bp else None,
        }

    def save_json(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"Metrics saved to {path}")
