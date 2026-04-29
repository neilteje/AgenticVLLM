# Delta GPU Quick-Run Guide

**Goal**: Replay HyperAgent traces through stock vLLM on an A100, collect job completion time + throughput metrics, run resource-group analysis. Everything in under 1 hour.

---

## Step 0 — SSH into Delta

```bash
ssh <your-username>@login.delta.ncsa.illinois.edu
```

---

## Step 1 — Request a GPU node (A100, 1 hour)

```bash
srun -A bewu-delta-gpu -p gpuA100x4-interactive --gpus=1 --cpus-per-task=16 --mem=64g --time=01:00:00 --pty /bin/bash
```

Wait for the allocation. Once you get a prompt, continue.

---

## Step 2 — Clone the repo and set up environment (~3 min)

```bash
module load gcc-native/13.2 cudatoolkit/25.3_12.8

cd /projects/bewu/$USER
git clone https://github.com/<your-gh-username>/MONET.git
cd MONET/hyperagent-replay

conda create -n ha-replay python=3.11 -y
conda activate ha-replay
python -m pip install -U pip uv
python -m pip install -e .
UV_TORCH_BACKEND=cu128 uv pip install vllm
```

> If you already cloned MONET before, just `cd` into it and activate the env:
> ```bash
> module load gcc-native/13.2 cudatoolkit/25.3_12.8
> cd /projects/bewu/$USER/MONET/hyperagent-replay
> conda activate ha-replay
> ```

---

## Step 3 — Start the vLLM server (background, ~2 min to load)

```bash
vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768 \
  > vllm_server.log 2>&1 &

VLLM_PID=$!
echo "vLLM server PID: $VLLM_PID"
```

Wait for it to be ready (~1-2 min on A100):

```bash
until curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; do
  echo "waiting for vLLM server..."
  sleep 5
done
echo "SERVER IS READY"
```

---

## Step 4 — Replay small HyperAgent traces (~2-5 min each)

### Trace A: django-10924 (17 turns — fastest)

```bash
ha-trace-replay extracted/django__django-10924_human.extracted.json \
  --model Qwen/Qwen2.5-Coder-14B-Instruct \
  --base-url http://127.0.0.1:8000/v1 \
  --max-model-len 32768 \
  --output replays/django__django-10924_human.replay.json
```

### Trace B: pylint-6506 (16 turns)

```bash
ha-trace-replay extracted/pylint-dev__pylint-6506_human.extracted.json \
  --model Qwen/Qwen2.5-Coder-14B-Instruct \
  --base-url http://127.0.0.1:8000/v1 \
  --max-model-len 32768 \
  --output replays/pylint-dev__pylint-6506_human.replay.json
```

### Trace C: scikit-learn-25570 (15 turns)

```bash
ha-trace-replay extracted/scikit-learn__scikit-learn-25570_human.extracted.json \
  --model Qwen/Qwen2.5-Coder-14B-Instruct \
  --base-url http://127.0.0.1:8000/v1 \
  --max-model-len 32768 \
  --output replays/scikit-learn__scikit-learn-25570_human.replay.json
```

Each replay prints timing at the end. **Screenshot or copy the timing output** — that's your job-completion-time data for the meeting.

---

## Step 5 — Evaluate the replays

```bash
ha-trace-eval replays/django__django-10924_human.replay.json \
  --output evals/django__django-10924_human.eval.json

ha-trace-eval replays/pylint-dev__pylint-6506_human.replay.json \
  --output evals/pylint-dev__pylint-6506_human.eval.json

ha-trace-eval replays/scikit-learn__scikit-learn-25570_human.replay.json \
  --output evals/scikit-learn__scikit-learn-25570_human.eval.json
```

Print a quick summary of all evals:

```bash
for f in evals/*.eval.json; do
  echo "=== $(basename $f) ==="
  python3 -c "
import json, sys
d = json.load(open('$f'))
rm = d.get('replay_metrics', {})
print(f\"  wall_solve_time:   {rm.get('wall_solve_time_s', 'N/A'):.1f}s\")
print(f\"  lm_only_time:      {rm.get('lm_only_solve_time_s', 'N/A'):.1f}s\")
print(f\"  turns replayed:    {rm.get('num_replayed_turns', 'N/A')}\")
print(f\"  avg latency/turn:  {rm.get('avg_request_latency_s', 'N/A'):.2f}s\")
print(f\"  p95 latency:       {rm.get('p95_request_latency_s', 'N/A'):.2f}s\")
print(f\"  total prompt tok:  {rm.get('total_prompt_tokens', 'N/A')}\")
print(f\"  total compl tok:   {rm.get('total_completion_tokens', 'N/A')}\")
print()
"
done
```

---

## Step 6 — Resource group + SLO derivation (no GPU needed, instant)

```bash
python3 src/hyperagent_replay/derive_slos_and_resource_groups.py \
  --glob "trajectories/**/*.json" \
  --slo-class interactive \
  --single-file-output-dir trajectory_reports \
  | tee slo_report.txt
```

This analyzes all 28 trajectories and prints:
- Stage-level SLOs per resource group (sub-agent x tool signature)
- Episode-level SLOs (p50/p95/p99 of total cost per trace)
- Redundancy / similarity metrics (repeated tool calls, avoidable cost)

---

## Step 7 — (If time permits) Try vllm-continuum

Kill the stock vLLM server first:

```bash
kill $VLLM_PID
sleep 5
```

Install and start vllm-continuum:

```bash
cd /projects/bewu/$USER/MONET/vllm-continuum
uv pip install -e .

vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --scheduling-policy continuum \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768 \
  > vllm_continuum_server.log 2>&1 &

VLLM_PID=$!

until curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; do
  echo "waiting for continuum server..."
  sleep 5
done
echo "CONTINUUM SERVER IS READY"
```

Replay the same trace for a direct comparison:

```bash
cd /projects/bewu/$USER/MONET/hyperagent-replay

ha-trace-replay extracted/django__django-10924_human.extracted.json \
  --model Qwen/Qwen2.5-Coder-14B-Instruct \
  --base-url http://127.0.0.1:8000/v1 \
  --max-model-len 32768 \
  --output replays/django__django-10924_continuum.replay.json

ha-trace-eval replays/django__django-10924_continuum.replay.json \
  --output evals/django__django-10924_continuum.eval.json
```

---

## Step 8 — Copy results off the node before time runs out

```bash
cd /projects/bewu/$USER/MONET/hyperagent-replay

echo "=== FILES TO KEEP ==="
ls -lh replays/*.replay.json
ls -lh evals/*.eval.json
ls -lh slo_report.txt
ls -lh trajectory_reports/
```

Results live in `/projects/bewu/$USER/` which persists across sessions, so they won't be deleted when your job ends. But **copy them to your laptop** too:

From your **local machine**:

```bash
scp -r <your-username>@login.delta.ncsa.illinois.edu:/projects/bewu/<your-username>/MONET/hyperagent-replay/replays/ ./replays/
scp -r <your-username>@login.delta.ncsa.illinois.edu:/projects/bewu/<your-username>/MONET/hyperagent-replay/evals/ ./evals/
scp <your-username>@login.delta.ncsa.illinois.edu:/projects/bewu/<your-username>/MONET/hyperagent-replay/slo_report.txt .
```

---

## What You'll Have for the Meeting

| Deliverable | Source |
|---|---|
| Job completion time on stock vLLM (3 traces) | `evals/*.eval.json` → `wall_solve_time_s` |
| Per-turn latency distribution | `evals/*.eval.json` → `avg`, `p95`, `p99` |
| Token throughput | `evals/*.eval.json` → `total_prompt_tokens / wall_solve_time_s` |
| Resource groups + SLOs for all 28 traces | `slo_report.txt` |
| vLLM vs Continuum comparison (if Step 7 done) | Compare the two eval JSONs side-by-side |

---

## Troubleshooting

**vLLM server won't start**: Check `vllm_server.log` for errors. Most common: wrong CUDA version. Make sure you ran `module load gcc-native/13.2 cudatoolkit/25.3_12.8` first.

**Context length error during replay**: The replay tool has built-in context budgeting and will auto-trim. If it still fails, the trace is too large for 32768 context — skip it and try a smaller one.

**Running out of time**: Priorities in order: (1) get at least 1 replay done, (2) run the SLO derivation, (3) try more traces, (4) try continuum.

**conda not found on GPU node**: Run `module load anaconda3` or use the full path to your conda install.
