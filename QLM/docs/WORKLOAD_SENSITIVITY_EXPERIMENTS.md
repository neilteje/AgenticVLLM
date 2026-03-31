# QLM Workload Sensitivity Experiments

**Goal:** Understand how different workload patterns affect performance.

---

## 1. Parameters to vary

| Parameter | What it controls | How to vary in QLM |
|-----------|------------------|--------------------|
| **Request arrival rate** | How many requests per second are pushed | In the experiment driver: control `push()` rate (e.g. Poisson/inter-arrival times). |
| **Prompt length distribution** | Short vs long prompts | Sample prompts from datasets with different length distributions, or truncate/pad. |
| **Output token distribution** | Implicit in request “size” | QLM uses `workload_tokens` in config; can vary per-request or use datasets with different reply lengths. |
| **Burstiness** | Spiky vs smooth arrival | In the driver: send requests in bursts (e.g. N at once every T seconds) vs uniform spacing. |
| **Number of concurrent users** | Multiple logical streams of requests | Simulate multiple “users” (e.g. separate async tasks) each pushing at different rates. |

**Current QLM interface:** `Queue.push(prompt, model, slo, insertion_time)`. Experiments need a **workload driver** that generates sequences of `(prompt, model, slo, insertion_time)` with the above distributions.

---

## 2. Metrics to collect

| Metric | Meaning | How to get it in QLM |
|--------|---------|----------------------|
| **Queue length** | Number of requests/groups waiting | Instrument `VirtualQueueEngine` / `VirtualQueue`: record `sum(len(vq.groups))` or total requests across groups over time. |
| **GPU utilization** | How busy the vLLM worker is | From vLLM `/metrics` (worker already has `get_backpressure()`); add scraping of GPU util (e.g. `nvidia-smi` or vLLM metrics). |
| **Scheduling delay** | Time from request insert to start of execution | Record `insertion_time` when pushing; when request is popped and sent to worker, record delay = `now - insertion_time`. Log per request. |

**Implementation note:** QLM does not yet log these metrics to a file. Add a small **metrics collector** (e.g. callback or wrapper around `add_request` / `pop_request` / worker calls) that writes time-series data (timestamp, queue_length, gpu_util, scheduling_delay) for later analysis.

---

## 3. Datasets for workloads

### ShareGPT (already referenced in QLM)

- **Source:** [Hugging Face: anon8231489123/ShareGPT_Vicuna_unfiltered](https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered) — file `ShareGPT_V3_unfiltered_cleaned_split.json`.
- **QLM data README:** `data/README.md` says:
  ```bash
  wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json
  ```
- **Usage in QLM:** `benchmarks/basic_test.py` already loads this JSON, filters conversations with ≥2 turns, and uses the first user message as the prompt. You can extend this to sample by prompt length, add SLO/length variation, and control arrival times.

### Other Hugging Face datasets that can run on QLM

These are text/conversation datasets you can use as **prompt** (and optionally output-length) sources. Download via `datasets` or direct URL and map to `(prompt, model, slo)` in your workload driver.

| Dataset | HF path | Notes |
|---------|---------|--------|
| **LMSYS Chat 1M** | `lmsys/lmsys-chat-1m` | ~1M conversations; ~69.5 tokens/prompt, ~214.5 tokens/response; good for prompt/response length distribution. |
| **WildChat** | `allenai/WildChat-4.8M` | Large conversation set; multiple models; useful for diverse prompt lengths and “user” behavior. |
| **ShareGPT Vicuna** | `anon8231489123/ShareGPT_Vicuna_unfiltered` | Same as current ShareGPT; multiple splits available on HF. |
| **OpenAssistant** | `OpenAssistant/oasst1` | Conversation-style; can extract first user message as prompt. |
| **Multi-turn conversations** | `jackwarner/multi-turn-conversations` | Multi-turn; good for testing burstiness (multiple turns per “user”). |

**Suggested approach:** Use **ShareGPT** as the first dataset (already in the repo’s instructions), then add **one or two** from Hugging Face (e.g. `lmsys/lmsys-chat-1m`, `allenai/WildChat-4.8M`) to vary prompt length and “user” patterns. Load with:

```python
from datasets import load_dataset
ds = load_dataset("lmsys/lmsys-chat-1m", split="train", trust_remote_code=True)
# Then map to prompts (e.g. first user message) and optionally token counts
```

---

## 4. Implemented: workload driver and metrics

- **Dataset loaders** (`qlm/workload/datasets.py`): ShareGPT (local JSON) and Hugging Face datasets (`lmsys/lmsys-chat-1m`, `allenai/WildChat-4.8M`, `OpenAssistant/oasst1`, `HuggingFaceH4/ultrachat_200k`). Prompt length buckets: `short`, `medium`, `long`.
- **Metrics** (`qlm/workload/metrics.py`): `ExperimentMetrics` records queue length samples, scheduling delays, and backpressure (GPU proxy); saves JSON with summary stats.
- **Workload driver** (`benchmarks/workload_driver.py`): CLI to run experiments with configurable arrival rate, burstiness (`--burst-size`, `--burst-interval`), `--num-users`, `--dataset`, `--duration`, `--prompt-length`. Writes metrics to a JSON file.

### Quick start

1. **Download ShareGPT** (if using `--dataset sharegpt`):
   ```bash
   cd QLM && wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json -O data/ShareGPT_V3_unfiltered_cleaned_split.json
   ```
2. **Set project dir** and run (vLLM must be running on port 8000, or use `--no-start-vllm` and start vLLM yourself):
   ```bash
   export QLMPROJDIR=/path/to/QLM
   python benchmarks/workload_driver.py --dataset sharegpt --duration 60 --arrival-rate 2 --output metrics.json
   ```
3. **Burstiness**: e.g. 5 requests every 2 seconds:
   ```bash
   python benchmarks/workload_driver.py --dataset sharegpt --burst-size 5 --burst-interval 2.0 --duration 60 --output burst_metrics.json
   ```
4. **Multiple users + Hugging Face dataset**:
   ```bash
   python benchmarks/workload_driver.py --dataset lmsys/lmsys-chat-1m --num-users 4 --arrival-rate 1 --max-samples 500 --output hf_metrics.json
   ```

### Suggested next steps

1. Run sweeps over arrival rate, burstiness, and number of users; record metrics for each run.
2. Compare datasets (ShareGPT vs LMSYS vs WildChat) and prompt-length buckets.
3. Plot queue length, backpressure (GPU proxy), and scheduling delay vs the varied parameters.


diff access patterns hetereogoenous workloads on vllm
diff req rate conccurrency prompt lenghts
analyze the workload differences
service engines

GPT traces, mast traces, workload aware
replaced with agentic workflow traces

have 2 datasets... VLLM with QLM

finish the experiments

6-7 graphs for report