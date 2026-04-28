"""vLLM-Continuum integration helpers for live HyperAgent runs.

HyperAgent's main SWE-bench path uses AutoGen agents, and AutoGen owns the
OpenAI-compatible client calls. This module installs a small OpenAI SDK hook
that adds Continuum scheduling metadata to every chat completion request and
records per-request metrics from the OpenAI-compatible response usage.
"""

from __future__ import annotations

import atexit
import json
import os
import time
from pathlib import Path
from threading import Lock
from typing import Any

_LOCK = Lock()
_ORIGINAL_CREATE = None
_ORIGINAL_ASYNC_CREATE = None
_PATCHED = False
_REQUEST_COUNTER = 0
_JOB_ID: str | None = None
_METRICS_PATH: Path | None = None
_RECORDS: list[dict[str, Any]] = []


def continuum_enabled() -> bool:
    return os.environ.get("HYPERAGENT_CONTINUUM_ENABLED", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def build_continuum_llm_configs(
    *,
    model: str,
    base_url: str,
    api_key: str = "EMPTY",
) -> dict[str, Any]:
    """Build one OpenAI-compatible config list for all HyperAgent roles."""
    common = {
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "api_type": "openai",
        "price": [0.0, 0.0],
    }
    return {
        "name": "vllm-continuum",
        "nav": [{**common, "stop_sequences": ["\nObservation:"]}],
        "edit": [{**common, "stop_sequences": ["\nObservation:"]}],
        "exec": [{**common, "stop_sequences": ["\nObservation:"]}],
        "plan": [{**common}],
        "type": "patch",
    }


def configure_continuum_tracking(
    *,
    job_id: str,
    metrics_path: str | Path | None = None,
) -> None:
    """Set the active Continuum job id and metrics output path."""
    global _JOB_ID, _METRICS_PATH, _REQUEST_COUNTER, _RECORDS

    with _LOCK:
        _JOB_ID = job_id
        if metrics_path is None:
            metrics_dir = Path(
                os.environ.get(
                    "HYPERAGENT_CONTINUUM_METRICS_DIR",
                    "results/hyperagent_continuum_metrics",
                )
            )
            _METRICS_PATH = metrics_dir / f"{job_id}.metrics.json"
        else:
            _METRICS_PATH = Path(metrics_path)
        _REQUEST_COUNTER = 0
        _RECORDS = []


def enable_continuum_from_env(
    *,
    default_job_id: str | None = None,
    metrics_path: str | Path | None = None,
) -> None:
    """Enable request metadata/metrics if HYPERAGENT_CONTINUUM_ENABLED is set."""
    if not continuum_enabled():
        return

    job_id = (
        os.environ.get("HYPERAGENT_CONTINUUM_JOB_ID")
        or default_job_id
        or f"hyperagent-{int(time.time())}"
    )
    configure_continuum_tracking(job_id=job_id, metrics_path=metrics_path)
    patch_openai_chat_completions()


def _infer_agent_name(messages: Any) -> str:
    if not isinstance(messages, list):
        return "unknown"

    text_parts: list[str] = []
    for message in messages[:3]:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", ""))
        content = str(message.get("content", ""))
        if role == "system":
            text_parts.append(content[:1000])
    joined = "\n".join(text_parts).lower()

    if "navigator" in joined:
        return "Navigator"
    if "editor" in joined or "code editor" in joined:
        return "Editor"
    if "executor" in joined:
        return "Executor"
    if "planner" in joined:
        return "Planner"
    return "unknown"


def _usage_value(usage: Any, key: str) -> int | None:
    if usage is None:
        return None
    value = getattr(usage, key, None)
    if value is None and isinstance(usage, dict):
        value = usage.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _cached_prompt_tokens(usage: Any) -> int | None:
    if usage is None:
        return None
    details = getattr(usage, "prompt_tokens_details", None)
    if details is None and isinstance(usage, dict):
        details = usage.get("prompt_tokens_details")
    if details is None:
        return None
    value = getattr(details, "cached_tokens", None)
    if value is None and isinstance(details, dict):
        value = details.get("cached_tokens")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _write_metrics() -> None:
    with _LOCK:
        if _METRICS_PATH is None:
            return
        path = _METRICS_PATH
        records = list(_RECORDS)
        job_id = _JOB_ID

    path.parent.mkdir(parents=True, exist_ok=True)
    prompt_total = sum(r.get("prompt_tokens") or 0 for r in records)
    completion_total = sum(r.get("completion_tokens") or 0 for r in records)
    cached_total = sum(r.get("cached_prompt_tokens") or 0 for r in records)
    new_prefill_total = sum(r.get("new_prefill_tokens") or 0 for r in records)
    latency_total = sum(r.get("request_latency_s") or 0.0 for r in records)
    payload = {
        "job_id": job_id,
        "num_requests": len(records),
        "gpu_seconds_per_job": latency_total,
        "total_prompt_tokens": prompt_total,
        "total_completion_tokens": completion_total,
        "total_cached_prompt_tokens": cached_total,
        "total_new_prefill_tokens": new_prefill_total,
        "prefill_reuse_ratio": (
            cached_total / prompt_total if prompt_total > 0 else 0.0
        ),
        "records": records,
    }
    path.write_text(json.dumps(payload, indent=2))


def _record_response(
    *,
    request_index: int,
    model: str | None,
    agent: str,
    start_time: float,
    end_time: float,
    response: Any,
    extra_body: dict[str, Any],
) -> None:
    usage = getattr(response, "usage", None)
    prompt_tokens = _usage_value(usage, "prompt_tokens")
    completion_tokens = _usage_value(usage, "completion_tokens")
    total_tokens = _usage_value(usage, "total_tokens")
    cached_tokens = _cached_prompt_tokens(usage)
    new_prefill_tokens = None
    if prompt_tokens is not None:
        new_prefill_tokens = max(0, prompt_tokens - (cached_tokens or 0))

    record = {
        "request_index": request_index,
        "job_id": extra_body.get("job_id"),
        "agent": agent,
        "model": model,
        "request_start_time": start_time,
        "request_end_time": end_time,
        "request_latency_s": end_time - start_time,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cached_prompt_tokens": cached_tokens,
        "new_prefill_tokens": new_prefill_tokens,
        "continuum_extra_body": extra_body,
    }
    with _LOCK:
        _RECORDS.append(record)
    _write_metrics()


def _next_request_index() -> int:
    global _REQUEST_COUNTER
    with _LOCK:
        _REQUEST_COUNTER += 1
        return _REQUEST_COUNTER


def _active_job_id() -> str:
    if _JOB_ID is not None:
        return _JOB_ID
    return os.environ.get("HYPERAGENT_CONTINUUM_JOB_ID", "hyperagent-job")


def _merge_continuum_extra_body(kwargs: dict[str, Any]) -> dict[str, Any]:
    extra_body = dict(kwargs.get("extra_body") or {})
    extra_body.setdefault("job_id", _active_job_id())
    # In live HyperAgent we do not know before generation whether the current
    # request will produce the final answer. The final extra pin expires by TTL
    # and does not affect serial single-job JCT.
    extra_body.setdefault("is_last_step", False)
    kwargs["extra_body"] = extra_body
    return extra_body


def patch_openai_chat_completions() -> None:
    """Patch OpenAI SDK chat completions to add Continuum metadata."""
    global _ORIGINAL_CREATE, _ORIGINAL_ASYNC_CREATE, _PATCHED
    if _PATCHED:
        return

    from openai.resources.chat.completions import Completions

    _ORIGINAL_CREATE = Completions.create

    def create_with_continuum(self, *args: Any, **kwargs: Any) -> Any:
        request_index = _next_request_index()
        model = kwargs.get("model")
        agent = _infer_agent_name(kwargs.get("messages"))
        extra_body = _merge_continuum_extra_body(kwargs)
        start_time = time.time()
        response = _ORIGINAL_CREATE(self, *args, **kwargs)
        end_time = time.time()
        _record_response(
            request_index=request_index,
            model=model,
            agent=agent,
            start_time=start_time,
            end_time=end_time,
            response=response,
            extra_body=extra_body,
        )
        return response

    Completions.create = create_with_continuum

    try:
        from openai.resources.chat.completions import AsyncCompletions

        _ORIGINAL_ASYNC_CREATE = AsyncCompletions.create

        async def async_create_with_continuum(
            self, *args: Any, **kwargs: Any
        ) -> Any:
            request_index = _next_request_index()
            model = kwargs.get("model")
            agent = _infer_agent_name(kwargs.get("messages"))
            extra_body = _merge_continuum_extra_body(kwargs)
            start_time = time.time()
            response = await _ORIGINAL_ASYNC_CREATE(self, *args, **kwargs)
            end_time = time.time()
            _record_response(
                request_index=request_index,
                model=model,
                agent=agent,
                start_time=start_time,
                end_time=end_time,
                response=response,
                extra_body=extra_body,
            )
            return response

        AsyncCompletions.create = async_create_with_continuum
    except Exception:
        # HyperAgent's current path is synchronous; async support is best-effort.
        pass

    atexit.register(_write_metrics)
    _PATCHED = True
