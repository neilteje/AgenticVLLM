# Phase 2: MAST/HyperAgent → vLLM-Continuum (Delta How-To)

**Goal**: Replay **MAST HyperAgent traces** through **`vllm-continuum`** (Continuum scheduling), then compute:

- **Job completion time (JCT)** per trace/job (avg / p50 / p95 / p99)
- **Throughput** (turns/sec and tokens/sec)

This workflow treats each trace as one **job**, tagged with `job_id = instance_id` on every request.

---

## 0) SSH to Delta

```bash
ssh <your-username>@login.delta.ncsa.illinois.edu
```

---

## 1) Get an interactive GPU (1 hour)

```bash
srun -A bewu-delta-gpu -p gpuA100x4-interactive --gpus=1 --cpus-per-task=16 --mem=64g --time=01:00:00 --pty /bin/bash
```

---

## 2) Clone MONET and create the replay environment

```bash
module load gcc-native/13.2 cudatoolkit/25.3_12.8

cd /projects/bewu/$USER
git clone https://github.com/<your-gh-username>/MONET.git
cd MONET

conda create -n mast-continuum python=3.11 -y
conda activate mast-continuum
python -m pip install -U pip uv
```

Install `hyperagent-replay` (driver) and **stock vLLM** (client dependency):

```bash
python -m pip install -e hyperagent-replay
UV_TORCH_BACKEND=cu128 uv pip install vllm
```

Install **`vllm-continuum`** (server):

```bash
python -m pip install -e vllm-continuum
```

If you hit a `setuptools-scm` version detection error, `git pull` first. This
repo anchors setuptools-scm version detection to `vllm-continuum/setup.py`, so
editable installs from a vendored subdirectory work on Delta.

---

## 3) Terminal A: start the Continuum server

Run this in a dedicated terminal on the GPU node:

```bash
cd /projects/bewu/$USER/MONET
conda activate mast-continuum

vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --scheduling-policy continuum \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768
```

Leave it running.

---

## 4) Terminal B: replay MAST HyperAgent traces against the server

### 4.1 Wait for readiness

```bash
cd /projects/bewu/$USER/MONET
conda activate mast-continuum

until curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; do
  echo "waiting for vLLM-continuum..."
  sleep 5
done
echo "SERVER READY"
```

### 4.2 Replay a small subset first (recommended for the 1-hour limit)

This will replay 3 traces (offset/limit) and write outputs to one directory:

```bash
ha-trace-batch-replay MAST/traces/HyperAgent \
  --pattern "*.json" \
  --output-dir results/phase2_mast_continuum/replays \
  --model Qwen/Qwen2.5-Coder-14B-Instruct \
  --base-url http://127.0.0.1:8000/v1 \
  --max-model-len 32768 \
  --max-completion-tokens 256 \
  --offset 0 \
  --limit 3
```

**Outputs**:

- Per-trace replay JSON: `results/phase2_mast_continuum/replays/*.replay.json`
- Per-trace scheduler timestamps sidecar: `*.scheduler_timestamps.json`
- **Merged** Continuum input file: `results/phase2_mast_continuum/replays/scheduler_timestamps`
- Batch manifest: `results/phase2_mast_continuum/replays/replay_manifest.json`

---

## 5) Compute job completion time stats (Continuum-style)

`vllm-continuum/continuum_exp/analyze.py` consumes the merged `scheduler_timestamps` file and computes JCT stats.

```bash
python vllm-continuum/continuum_exp/analyze.py \
  --input-dir results/phase2_mast_continuum/replays \
  --output-dir results/phase2_mast_continuum/analysis
```

This writes:

- `results/phase2_mast_continuum/analysis/results.json`

Key fields:
- `average_duration` = avg JCT
- `median_duration`, `percentile_95`, `percentile_99`

---

## 6) Evaluate replay outputs (tokens, latencies, wall-time)

Batch-evaluate all replay JSONs:

```bash
ha-trace-batch-eval results/phase2_mast_continuum/replays \
  --pattern "*.replay.json" \
  --output-dir results/phase2_mast_continuum/evals
```

This produces:
- Per-trace eval: `results/phase2_mast_continuum/evals/*.eval.json`
- Aggregate manifest: `results/phase2_mast_continuum/evals/eval_manifest.json`

---

## 7) Print the “meeting numbers” (JCT + throughput)

This reads all `*.eval.json` files and prints:
- wall JCT
- LM-only time
- turns/sec
- tokens/sec

```bash
python3 - <<'PY'
import glob, json, os

paths = sorted(glob.glob("results/phase2_mast_continuum/evals/*.eval.json"))
if not paths:
    raise SystemExit("No evals found. Did you run ha-trace-batch-eval?")

def fnum(x, nd=2):
    return "N/A" if x is None else f"{x:.{nd}f}"

for p in paths:
    d = json.load(open(p))
    rm = d.get("replay_metrics", {})
    wall = rm.get("wall_solve_time_s", 0.0) or 0.0
    lm = rm.get("lm_only_solve_time_s", 0.0) or 0.0
    turns = rm.get("num_replayed_turns", 0) or 0
    pt = rm.get("total_prompt_tokens", 0) or 0
    ct = rm.get("total_completion_tokens", 0) or 0

    turns_per_s = (turns / wall) if wall > 0 else 0.0
    tok_per_s = ((pt + ct) / wall) if wall > 0 else 0.0

    print(f"=== {os.path.basename(p)} ===")
    print(f"JCT_wall_s:           {fnum(wall, 1)}")
    print(f"JCT_lm_only_s:        {fnum(lm, 1)}")
    print(f"turns:                {turns}")
    print(f"throughput_turns/s:   {fnum(turns_per_s, 4)}")
    print(f"throughput_tokens/s:  {fnum(tok_per_s, 2)}   (prompt+completion)")
    print()
PY
```

---

## 8) Notes / knobs for stability

- If context length errors happen on long traces, start with small traces (`--limit 3`) and/or reduce `--max-completion-tokens` to `128`.
- If you want a direct comparison, rerun with stock vLLM (no Continuum):
  - restart server **without** `--scheduling-policy continuum`
  - write to a separate output dir like `results/phase2_mast_vllm_fcfs/...`




clone hyperagent, run hyperagent and patch the inference module within it so it uses vllm, and if we’re able to run continuum

archit and hanchan