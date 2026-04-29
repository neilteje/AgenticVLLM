# Plan: Live HyperAgent + vLLM-Continuum on Delta

## Goal

Run **live HyperAgent**, not `hyperagent-replay`, against a
**vLLM-Continuum** OpenAI-compatible server. The unit of work is one
SWE-Bench / HyperAgent job:

```text
one issue / instance_id -> one HyperAgent run -> one Continuum job_id
```

This lets us measure whether Continuum's KV-pinning improves a real
HyperAgent execution, first on the named instances and then on a larger
set.

## What is now integrated

### 1. Live HyperAgent request hook

File: `HyperAgent/src/hyperagent/continuum.py`

This module patches the OpenAI SDK call path used by AutoGen. HyperAgent's
live run path creates AutoGen `AssistantAgent` / `GroupChatManager`
objects, and AutoGen owns the actual OpenAI-compatible chat-completion
requests. The hook adds Continuum metadata to every request:

- `job_id`: the SWE-Bench `instance_id`, for example
  `astropy__astropy-12907`.
- `is_last_step`: currently `False` for live requests. In a live run we do
  not know before generation whether the model will emit the final answer;
  the final pin expires by TTL and does not affect serial single-job JCT.

It also records per-request metrics into JSON:

- `request_latency_s`
- `prompt_tokens`
- `completion_tokens`
- `cached_prompt_tokens`
- `new_prefill_tokens = prompt_tokens - cached_prompt_tokens`
- aggregate `gpu_seconds_per_job`
- aggregate `prefill_reuse_ratio`

### 1b. HyperAgent summarizer path

File: `HyperAgent/src/hyperagent/agents/llms.py`

HyperAgent also uses a `LocalLLM` summarizer outside the AutoGen agent
loop. When `HYPERAGENT_CONTINUUM_ENABLED=1`, that summarizer now uses:

- `HYPERAGENT_CONTINUUM_BASE_URL`
- `HYPERAGENT_CONTINUUM_MODEL`
- `HYPERAGENT_CONTINUUM_API_KEY` (default `EMPTY`)

This prevents summarizer requests from silently going to Together while
the main agents go to Continuum.

### 2. HyperAgent constructor support

File: `HyperAgent/src/hyperagent/pilot.py`

`HyperAgent(...)` now accepts:

- `continuum_job_id`
- `continuum_metrics_path`

When `HYPERAGENT_CONTINUUM_ENABLED=1`, these activate the live request
hook for that job.

### 3. SWE-Bench runner support

File: `HyperAgent/scripts/run_swe_bench.py`

New flags:

```bash
--backend continuum
--continuum_base_url http://127.0.0.1:8000/v1
--continuum_model Qwen/Qwen2.5-Coder-14B-Instruct
--continuum_metrics_folder results/hyperagent_continuum_metrics
--instance_ids astropy__astropy-12907,astropy__astropy-14365
```

When `--backend continuum` is used, all planner/navigator/editor/executor
LLM configs point to the Continuum server instead of Anthropic.

### 4. Continuum parser support for HyperAgent tool calls

File: `vllm-continuum/vllm/v1/core/estimate_with_func.py`

Continuum's `ToolCallParser` now recognizes HyperAgent-style tool calls
inside fenced code blocks:

```python
open_file._run(...)
search._run(...)
```

This matters because live HyperAgent cannot know `this_func_call` before
the LLM response is generated. Instead, Continuum parses the generated
tool call at request finish and uses that for the next pinning decision.

The earlier safeguard is also still present: if a client does provide
`this_func_call`, Continuum preserves it instead of overwriting it.

## Target instances

Partner's current set:

```text
astropy__astropy-12907
astropy__astropy-14309
astropy__astropy-14365
```

Initial expansion set:

```text
astropy__astropy-12907
astropy__astropy-13398
django__django-10097
sphinx-doc__sphinx-8120
xarray__xarray-2905
```

Local `MAST/traces/HyperAgent` currently contains raw annotated traces for:

```text
astropy__astropy-12907_human.json
astropy__astropy-14365_human.json
```

The other instance IDs are still valid SWE-Bench-style live-run targets,
but they are not present as local MAST raw trace files in this checkout.
For live HyperAgent, the runner uses the SWE-Bench dataset split and
filters by `--instance_ids`.

## Delta setup

### 1. Get a GPU node

```bash
ssh <netid>@login.delta.ncsa.illinois.edu

srun -A bewu-delta-gpu -p gpuA100x4-interactive \
  --gpus=1 --cpus-per-task=16 --mem=96g \
  --time=04:00:00 --pty /bin/bash
```

### 2. Clone and install

```bash
cd /projects/bewu/$USER
git clone <your MONET repo url> MONET
cd MONET

module load gcc-native/13.2 cudatoolkit/25.3_12.8

conda create -n hyperagent-continuum python=3.10 -y
conda activate hyperagent-continuum
python -m pip install -U pip

python -m pip install -e HyperAgent
python -m pip install -e vllm-continuum
```

If HyperAgent dependency resolution is too slow or brittle, first try the
minimal live-run install:

```bash
python -m pip install openai==1.43.0 pyautogen==0.3.0 datasets docker
python -m pip install -e HyperAgent
python -m pip install -e vllm-continuum
```

HyperAgent also expects:

- Docker available for SWE-Bench images.
- `GITHUB_TOKEN` set if GitHub cloning hits rate limits.
- Zoekt / ctags available for full code-search behavior, per
  `HyperAgent/README.md`.

## Terminal A: start vLLM-Continuum

Use a stable `RUN_OUTPUT_DIR` so Continuum server-side scheduler events are
saved.

```bash
cd /projects/bewu/$USER/MONET
conda activate hyperagent-continuum

export RUN_OUTPUT_DIR=$PWD/results/live_hyperagent_continuum/server_events
mkdir -p "$RUN_OUTPUT_DIR"

vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --scheduling-policy continuum \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768
```

Leave this terminal running.

## Terminal B: smoke test server

```bash
cd /projects/bewu/$USER/MONET
conda activate hyperagent-continuum

python3 - <<'PY'
import json
import urllib.request

payload = {
    "model": "Qwen/Qwen2.5-Coder-14B-Instruct",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "max_completion_tokens": 16,
    "job_id": "smoke-live-hyperagent",
    "is_last_step": False,
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer EMPTY",
    },
)
print(urllib.request.urlopen(req, timeout=120).read().decode())
PY
```

Check Terminal A logs for the Continuum request arriving with that job id.

## Run live HyperAgent on the first target instances

Start small. Use two instances that are definitely present in local MAST
raw traces and commonly appear in SWE-Bench workflows:

```bash
cd /projects/bewu/$USER/MONET/HyperAgent
conda activate hyperagent-continuum

export HYPERAGENT_CONTINUUM_ENABLED=1
export HYPERAGENT_CONTINUUM_BASE_URL=http://127.0.0.1:8000/v1
export HYPERAGENT_CONTINUUM_MODEL=Qwen/Qwen2.5-Coder-14B-Instruct

python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url http://127.0.0.1:8000/v1 \
  --continuum_model Qwen/Qwen2.5-Coder-14B-Instruct \
  --continuum_metrics_folder ../results/live_hyperagent_continuum/metrics \
  --output_folder ../results/live_hyperagent_continuum/patches \
  --model_nick_name hyperagent-continuum-qwen \
  --instance_ids astropy__astropy-12907,astropy__astropy-14365
```

Then run partner set:

```bash
python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url http://127.0.0.1:8000/v1 \
  --continuum_model Qwen/Qwen2.5-Coder-14B-Instruct \
  --continuum_metrics_folder ../results/live_hyperagent_continuum/metrics \
  --output_folder ../results/live_hyperagent_continuum/patches \
  --model_nick_name hyperagent-continuum-qwen \
  --instance_ids astropy__astropy-12907,astropy__astropy-14309,astropy__astropy-14365
```

Then expansion set:

```bash
python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url http://127.0.0.1:8000/v1 \
  --continuum_model Qwen/Qwen2.5-Coder-14B-Instruct \
  --continuum_metrics_folder ../results/live_hyperagent_continuum/metrics \
  --output_folder ../results/live_hyperagent_continuum/patches \
  --model_nick_name hyperagent-continuum-qwen \
  --instance_ids astropy__astropy-12907,astropy__astropy-13398,django__django-10097,sphinx-doc__sphinx-8120,xarray__xarray-2905
```

If `sphinx-doc__sphinx-8120` does not match the dataset's exact instance id,
inspect the split and adjust the repo prefix. The run script prints a
warning for requested IDs that are not found.

## Run stock vLLM baseline

Restart Terminal A without Continuum scheduling:

```bash
vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768
```

Then run the same HyperAgent command but keep `--backend continuum`.
Why? The backend flag simply builds OpenAI-compatible configs pointing to
`http://127.0.0.1:8000/v1` and enables the live metrics hook. Stock vLLM
ignores `job_id` / `is_last_step`, but metrics are still collected.

Write stock results to a separate folder:

```bash
python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url http://127.0.0.1:8000/v1 \
  --continuum_model Qwen/Qwen2.5-Coder-14B-Instruct \
  --continuum_metrics_folder ../results/live_hyperagent_stock/metrics \
  --output_folder ../results/live_hyperagent_stock/patches \
  --model_nick_name hyperagent-stock-qwen \
  --instance_ids astropy__astropy-12907,astropy__astropy-14365
```

## Metrics to report

Primary outcome:

- `wall_solve_time_s`: live HyperAgent wall-clock per instance. This can be
  computed from the run script logs or added as a wrapper timer if needed.

Already collected by `HyperAgent/src/hyperagent/continuum.py`:

- `gpu_seconds_per_job`: sum of LLM request latencies.
- `total_prompt_tokens`
- `total_completion_tokens`
- `total_cached_prompt_tokens`
- `total_new_prefill_tokens`
- `prefill_reuse_ratio`
- per-request latency and token records.

Server-side Continuum diagnostics:

- `RUN_OUTPUT_DIR/scheduler_timestamps`
- `pinned_time`
- `unpinned_time`
- `Request_evicted_from_running_queue_time`
- `waiting_to_running`
- `prompt_length`
- `hit_length`

Paper-facing comparisons:

1. Stock vLLM live HyperAgent vs vLLM-Continuum live HyperAgent.
2. Per instance:
   - wall JCT
   - GPU-seconds-per-job
   - prefill tokens processed
   - work-avoided ratio:

```text
(stock_total_new_prefill_tokens - continuum_total_new_prefill_tokens)
/ stock_total_new_prefill_tokens
```

3. Sanity:
   - completion tokens should be in the same rough range.
   - final patch exists / does not exist.
   - no explosion in context retries or errors.

## Immediate debugging checklist

If no requests hit Continuum:

1. Confirm `--backend continuum` is present.
2. Confirm server is reachable:

```bash
curl http://127.0.0.1:8000/v1/models
```

3. Confirm `HYPERAGENT_CONTINUUM_ENABLED=1`.
4. Check metrics JSON under the chosen `--continuum_metrics_folder`.

If Continuum receives requests but no pinning happens:

1. Check generated responses contain tool calls like `open_file._run(...)`.
2. Check `RUN_OUTPUT_DIR/scheduler_timestamps` has `pinned_time`.
3. Check the patched `vllm-continuum/vllm/v1/core/estimate_with_func.py` is
   installed via `python -m pip install -e vllm-continuum`.

If target instance IDs are missing:

1. They may not be in `SWE-bench_Verified` `--split verified`.
2. Try `--split test` or inspect the dataset instance IDs.
3. Local `MAST/traces/HyperAgent` only confirms raw trace availability for
   `astropy__astropy-12907` and `astropy__astropy-14365` in this checkout.

## What not to confuse

- `hyperagent-replay`: deterministic replay of recorded LLM turns. Useful
  for controlled Regime A experiments.
- `HyperAgent`: live agent execution. This is what we integrated now.
- `MAST/traces/HyperAgent`: recorded traces / annotations. These are not
  what the live runner executes directly.
- SWE-Bench dataset: source of live issue instances for `run_swe_bench.py`.
