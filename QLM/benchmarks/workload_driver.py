#!/usr/bin/env python3
"""
QLM Workload Driver: run workload-sensitivity experiments with configurable
arrival rate, burstiness, concurrent users, and datasets (ShareGPT + Hugging Face).

Usage:
  export QLMPROJDIR=/path/to/QLM
  # With vLLM running separately on port 8000 (optional: use --no-start-vllm and a dummy endpoint)
  python benchmarks/workload_driver.py --dataset sharegpt --duration 60 --arrival-rate 2 --output metrics.json

  # Burstiness: send 5 requests every 2 seconds
  python benchmarks/workload_driver.py --dataset sharegpt --duration 60 --burst-size 5 --burst-interval 2.0

  # Multiple concurrent users
  python benchmarks/workload_driver.py --dataset lmsys/lmsys-chat-1m --num-users 4 --arrival-rate 1 --max-samples 500
"""

import argparse
import asyncio
import os
import sys
import time

# Add project root for imports when run from repo
_QLM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _QLM_ROOT not in sys.path:
    sys.path.insert(0, _QLM_ROOT)

from qlm.queue.queue import Queue
from qlm.endpoints.endpoint import Endpoint
from qlm.workload.datasets import get_prompts_from_dataset, load_sharegpt, load_hf_dataset, SUPPORTED_DATASETS
from qlm.workload.metrics import ExperimentMetrics


def _make_dummy_endpoint(model: str, address: str, port: int):
    """Minimal endpoint that does not start vLLM (for when vLLM is already running)."""
    class DummyEndpoint:
        def __init__(self):
            self.model = model
            self.address = address
            self.port = port
        def model_swap(self, new_model: str):
            self.model = new_model
    return DummyEndpoint()


async def _metrics_sampler(
    queue: Queue,
    metrics: ExperimentMetrics,
    sample_interval_sec: float,
    stop_event: asyncio.Event,
):
    """Periodically record queue length and backpressure (GPU proxy)."""
    while not stop_event.is_set():
        try:
            metrics.record_queue_length(queue.get_queue_length())
            for w in queue.workers:
                try:
                    bp = await asyncio.to_thread(w.get_backpressure)
                    metrics.record_backpressure(bp)
                    break
                except Exception:
                    pass
        except asyncio.CancelledError:
            break
        await asyncio.sleep(sample_interval_sec)


async def _user_task(
    queue: Queue,
    prompts: list,
    arrival_rate: float,
    burst_size: int,
    burst_interval: float,
    model: str,
    slo: float,
    user_id: int,
    stop_event: asyncio.Event,
):
    """One simulated user: push requests according to arrival_rate or burst pattern."""
    idx = 0
    n = len(prompts)
    if n == 0:
        return
    if burst_size > 1 and burst_interval > 0:
        # Bursty: send burst_size requests every burst_interval seconds
        while not stop_event.is_set():
            for _ in range(burst_size):
                prompt = prompts[idx % n].get("prompt") or prompts[idx % n]
                if isinstance(prompt, dict):
                    prompt = prompt.get("prompt", "")
                queue.push(prompt=prompt, model=model, slo=slo, insertion_time=time.time())
                idx += 1
            await asyncio.sleep(burst_interval)
    else:
        # Uniform: 1 request every 1/arrival_rate seconds
        interval = 1.0 / arrival_rate if arrival_rate > 0 else 1.0
        while not stop_event.is_set():
            prompt = prompts[idx % n].get("prompt") or prompts[idx % n]
            if isinstance(prompt, dict):
                prompt = prompt.get("prompt", "")
            queue.push(prompt=prompt, model=model, slo=slo, insertion_time=time.time())
            idx += 1
            await asyncio.sleep(interval)


async def run_experiment(
    dataset_name: str,
    max_samples: int,
    duration_sec: float,
    arrival_rate: float,
    burst_size: int,
    burst_interval: float,
    num_concurrent_users: int,
    model: str,
    slo: float,
    address: str,
    port: int,
    start_vllm: bool,
    output_path: str,
    project_dir: str,
    prompt_length_bucket: str,
):
    project_dir = project_dir or os.environ.get("QLMPROJDIR", _QLM_ROOT)
    os.environ["QLMPROJDIR"] = project_dir

    # Load prompts
    print(f"Loading dataset: {dataset_name} (max_samples={max_samples}, prompt_length_bucket={prompt_length_bucket or 'all'})")
    try:
        prompts = get_prompts_from_dataset(
            dataset_name,
            project_dir=project_dir,
            max_samples=max_samples,
            prompt_length_bucket=prompt_length_bucket or None,
        )
    except FileNotFoundError as e:
        print(f"Dataset error: {e}")
        return 1
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        return 1
    if not prompts:
        print("No prompts loaded. Check dataset path or filters.")
        return 1
    print(f"Loaded {len(prompts)} prompts.")

    # Endpoint and queue
    if start_vllm:
        endpoint = Endpoint(model=model, address=address, port=port)
    else:
        endpoint = _make_dummy_endpoint(model, address, port)
    q = Queue()
    q.register_worker(address, port, endpoint)

    # Metrics and dispatch callback
    metrics = ExperimentMetrics()
    metrics.start()

    def on_dispatch(request, dispatch_time: float):
        metrics.record_scheduling_delay(str(request.request_id), request.insertion_time, dispatch_time)

    q.set_on_dispatch_callback(on_dispatch)

    # Run queue loop and metrics sampler in background
    stop_event = asyncio.Event()
    queue_task = asyncio.create_task(q.run_queue())
    sampler_task = asyncio.create_task(
        _metrics_sampler(q, metrics, 0.25, stop_event)
    )

    # Run N user tasks
    user_tasks = [
        asyncio.create_task(
            _user_task(
                q, prompts, arrival_rate, burst_size, burst_interval,
                model, slo, i, stop_event,
            )
        )
        for i in range(num_concurrent_users)
    ]

    # Stop after duration
    await asyncio.sleep(duration_sec)
    stop_event.set()
    sampler_task.cancel()
    try:
        await sampler_task
    except asyncio.CancelledError:
        pass
    await asyncio.gather(*user_tasks)
    queue_task.cancel()
    try:
        await queue_task
    except asyncio.CancelledError:
        pass

    metrics.stop()
    metrics.save_json(output_path)
    print("Experiment finished.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="QLM workload sensitivity experiments")
    ap.add_argument("--dataset", type=str, default="sharegpt",
                    help="Dataset: sharegpt or a Hugging Face name (e.g. lmsys/lmsys-chat-1m)")
    ap.add_argument("--max-samples", type=int, default=1000,
                    help="Max prompts to load from dataset (default 1000)")
    ap.add_argument("--duration", type=float, default=60.0,
                    help="Experiment duration in seconds (default 60)")
    ap.add_argument("--arrival-rate", type=float, default=2.0,
                    help="Requests per second per user when not using burst (default 2)")
    ap.add_argument("--burst-size", type=int, default=0,
                    help="If > 1, send this many requests per burst (burstiness)")
    ap.add_argument("--burst-interval", type=float, default=2.0,
                    help="Seconds between bursts when burst-size > 1 (default 2)")
    ap.add_argument("--num-users", type=int, default=1,
                    help="Number of concurrent simulated users (default 1)")
    ap.add_argument("--model", type=str, default="unsloth/Llama-3.2-1B-Instruct",
                    help="Model name for requests")
    ap.add_argument("--slo", type=float, default=1000.0,
                    help="SLO in seconds (default 1000)")
    ap.add_argument("--address", type=str, default="localhost",
                    help="Worker address (default localhost)")
    ap.add_argument("--port", type=int, default=8000,
                    help="Worker port (default 8000)")
    ap.add_argument("--no-start-vllm", action="store_true",
                    help="Do not start vLLM; assume it is already running")
    ap.add_argument("--output", type=str, default="workload_metrics.json",
                    help="Output path for metrics JSON (default workload_metrics.json)")
    ap.add_argument("--project-dir", type=str, default=None,
                    help="QLM project dir (default QLMPROJDIR or repo root)")
    ap.add_argument("--prompt-length", type=str, default=None,
                    choices=["short", "medium", "long"],
                    help="Filter prompts by length bucket: short (<=200), medium (200-1000), long (>1000)")
    args = ap.parse_args()

    return asyncio.run(
        run_experiment(
            dataset_name=args.dataset,
            max_samples=args.max_samples,
            duration_sec=args.duration,
            arrival_rate=args.arrival_rate,
            burst_size=args.burst_size or 1,
            burst_interval=args.burst_interval,
            num_concurrent_users=args.num_users,
            model=args.model,
            slo=args.slo,
            address=args.address,
            port=args.port,
            start_vllm=not args.no_start_vllm,
            output_path=args.output,
            project_dir=args.project_dir,
            prompt_length_bucket=args.prompt_length,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
