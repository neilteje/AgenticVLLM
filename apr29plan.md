# apr29plan.md — End-to-End Live HyperAgent with vLLM-Continuum (Delta / RunPod)

## 0) What we are running (important)

This plan runs **live `HyperAgent/`** (AutoGen-based agent execution) against a
**vLLM-Continuum server**. It is *not* `hyperagent-replay/`.

We run **Regime A (serial, single-job)** by ensuring we execute **one SWE-bench /
HyperAgent instance at a time**. That makes the workflow apples-to-apples for
“cache usage per job”.

## 1) Target instances (MAST / SWE-bench IDs)

Primary first:
- `astropy__astropy-14209`
- `astropy__astropy-14365`

Then add (your expansion mix):
- `astropy__astropy-1207`
- `astropy__astropy-7336`
- `astropy__astropy-7606`
- `django__django-10973`

Notes:
- Your local `MAST/traces/HyperAgent/` folder may not contain *every* of these IDs as
  raw JSON trace files. That does **not** block the **live** run; live execution uses
  SWE-bench dataset splits inside `HyperAgent/scripts/run_swe_bench.py`.
- If an id isn’t found in the selected split, the script prints a warning; fix by
  either changing `--split` or using the exact SWE-bench instance id string that
  exists in that split.

## 2) Repo pieces you’ll use

From this MONET checkout:
- `vllm-continuum/` — run the server:
  - stock vLLM: default FCFS
  - Continuum: `--scheduling-policy continuum`
- `HyperAgent/` — run live HyperAgent:
  - `HyperAgent/scripts/run_swe_bench.py`
  - Continuum integration is enabled by:
    - `HYPERAGENT_CONTINUUM_ENABLED=1`
    - `--backend continuum`

## 3) Terminals (3-terminal setup)

1. **Terminal 1:** vLLM server (stock first, then Continuum)
2. **Terminal 2:** HyperAgent runner (one instance per command; this is Regime A)
3. **Terminal 3:** monitoring + quick metric sanity checks

## 4) RunPod / Delta general guidance

### Pick a GPU
If you want “metrics don’t break due to OOM”, request a high-VRAM GPU:
- **1× H100 / H200 is the safe route**
For Regime A (serial), you typically do **not** need more than 1 GPU.

### Persistent storage
If you’re using RunPod, make sure model caches + artifacts won’t exceed persistent disk.
If possible:
- put HF cache / model weights on a larger persistent volume

## 5) Install / build (one-time per VM)

Inside the VM (RunPod or Delta), assume you have MONET checked out.

```bash
cd /workspace  # adjust to your MONET location
python -m pip install -e HyperAgent
python -m pip install -e vllm-continuum
```

Also ensure Docker is available if you’re running the SWE-bench harness.

## 6) Shared environment variables (Terminal 2 and Terminal 3)

Set these in Terminal 2 and Terminal 3 (Terminal 1 also needs them for vLLM args).

```bash
export CONTINUUM_MODEL="Qwen/Qwen2.5-Coder-14B-Instruct"
export POD_VLLM_BASE_URL="http://127.0.0.1:8000/v1"

# Enables the HyperAgent->OpenAI hook we added
export HYPERAGENT_CONTINUUM_ENABLED=1
export HYPERAGENT_CONTINUUM_BASE_URL="$POD_VLLM_BASE_URL"
export HYPERAGENT_CONTINUUM_MODEL="$CONTINUUM_MODEL"

# Continuum/OpenAI-compatible endpoint accepts EMPTY
export HYPERAGENT_CONTINUUM_API_KEY="EMPTY"
```

Create output dirs:

```bash
mkdir -p results/live_hyperagent_stock/{patches,metrics}
mkdir -p results/live_hyperagent_continuum/{patches,metrics,server_events}
```

Set the instance list:

```bash
export INSTANCE_IDS="astropy__astropy-14209,astropy__astropy-14365"
```

Later for expansion:
```bash
export INSTANCE_IDS="astropy__astropy-14209,astropy__astropy-14365,astropy__astropy-1207,astropy__astropy-7336,astropy__astropy-7606,django__django-10973"
```

## 7) Phase A — Baseline run with STOCK vLLM

### Terminal 1: start stock vLLM

```bash
cd vllm-continuum

vllm serve "$CONTINUUM_MODEL" \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768
```

Key point: even though we set `--backend continuum` in the HyperAgent runner
(to enable metrics collection), **the server is stock FCFS** here.

### Terminal 2: run ONE instance at a time (Regime A)

Run instance `astropy__astropy-14209`:

```bash
cd HyperAgent

time python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url "http://127.0.0.1:8000/v1" \
  --continuum_model "$CONTINUUM_MODEL" \
  --continuum_metrics_folder ../results/live_hyperagent_stock/metrics \
  --output_folder ../results/live_hyperagent_stock/patches \
  --model_nick_name hyperagent-stock-qwen \
  --instance_ids astropy__astropy-14209
```

Then run `astropy__astropy-14365`:

```bash
time python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url "http://127.0.0.1:8000/v1" \
  --continuum_model "$CONTINUUM_MODEL" \
  --continuum_metrics_folder ../results/live_hyperagent_stock/metrics \
  --output_folder ../results/live_hyperagent_stock/patches \
  --model_nick_name hyperagent-stock-qwen \
  --instance_ids astropy__astropy-14365
```

Why single-instance commands?
- it gives you clean **wall JCT attribution** per instance
- it preserves the “scheduler doesn’t reorder inside a serial job” assumption

### Terminal 3: monitor metric files
```bash
watch -n 3 'ls -ლა results/live_hyperagent_stock/metrics | tail -n 20; nvidia-smi | head'
```

Check expected metrics fields exist in one JSON:
```bash
ls results/live_hyperagent_stock/metrics/*.metrics.json | head -n 1
python3 -c "import json; p='$(ls results/live_hyperagent_stock/metrics/*.metrics.json | head -n 1)'; d=json.load(open(p)); print(d.keys()); print(d['job_id']); print('total_new_prefill_tokens' in d, 'prefill_reuse_ratio' in d)"
```

## 8) Phase B — Variant run with vLLM-Continuum

Stop Terminal 1 stock server (Ctrl+C) then start Continuum.

### Terminal 1: start Continuum server (write scheduler_timestamps)

```bash
cd vllm-continuum

export RUN_OUTPUT_DIR="$PWD/../results/live_hyperagent_continuum/server_events"
mkdir -p "$RUN_OUTPUT_DIR"

vllm serve "$CONTINUUM_MODEL" \
  --scheduling-policy continuum \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768
```

### Terminal 2: rerun the same instances

```bash
cd HyperAgent

time python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url "http://127.0.0.1:8000/v1" \
  --continuum_model "$CONTINUUM_MODEL" \
  --continuum_metrics_folder ../results/live_hyperagent_continuum/metrics \
  --output_folder ../results/live_hyperagent_continuum/patches \
  --model_nick_name hyperagent-continuum-qwen \
  --instance_ids astropy__astropy-14209
```

Then:

```bash
time python scripts/run_swe_bench.py \
  --split verified \
  --backend continuum \
  --continuum_base_url "http://127.0.0.1:8000/v1" \
  --continuum_model "$CONTINUUM_MODEL" \
  --continuum_metrics_folder ../results/live_hyperagent_continuum/metrics \
  --output_folder ../results/live_hyperagent_continuum/patches \
  --model_nick_name hyperagent-continuum-qwen \
  --instance_ids astropy__astropy-14365
```

### Terminal 3: verify Continuum wrote server events

```bash
ls -la results/live_hyperagent_continuum/server_events
ls -la results/live_hyperagent_continuum/server_events/scheduler_timestamps* 2>/dev/null || true
```

Quick pin count:
```bash
python3 - <<'PY'
import json, glob
paths = glob.glob('results/live_hyperagent_continuum/server_events/scheduler_timestamps*')
assert paths, "No scheduler_timestamps found"
d = json.load(open(paths[0]))
count = 0
for job_id, history in d.items():
    for e in history:
        if isinstance(e, dict) and 'pinned_time' in e:
            count += 1
print("jobs:", len(d), "pinned_time events:", count)
PY
```

## 9) Work-avoided efficiency metric (how to compare)

For each instance, compare:
- `total_new_prefill_tokens` in stock vs continuum metrics JSON

Define:
```text
work_avoided_prefill_ratio
= (stock_total_new_prefill_tokens - continuum_total_new_prefill_tokens)
  / stock_total_new_prefill_tokens
```

Also compare:
- wall JCT (from runner timing / logs)
- `gpu_seconds_per_job` from metrics JSON
- `prefill_reuse_ratio` as a sanity indicator

## 10) Expansion schedule

After 2 instances work end-to-end:
1) Expand to the 5 additional instances by setting `INSTANCE_IDS` to include:
   - `astropy__astropy-1207`
   - `astropy__astropy-7336`
   - `astropy__astropy-7606`
   - `django__django-10973`
2) Keep **one instance per command** until you trust pinning + metrics.

## 11) Fast debugging checklist

### No metrics JSON produced
1. Ensure you used `--backend continuum`
2. Ensure `HYPERAGENT_CONTINUUM_ENABLED=1`
3. Ensure `HYPERAGENT_CONTINUUM_BASE_URL` points to the server

### Metrics exist but Continuum has no pin events
1. Confirm `scheduler_timestamps` exists
2. Confirm the vLLM-Continuum server has the tool-call parsing patch installed
3. Confirm HyperAgent’s generated tool calls are fenced and parsable

---
End.

