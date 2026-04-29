# Quick Start Guide - Phase 1 Experiments

This guide will help you run the Phase 1 ShareGPT baseline experiments ASAP.

## Prerequisites

1. **GPU Access**: You need a GPU-enabled machine (Delta cluster or local)
2. **QLM Installation**: QLM should be installed in `QLM/` directory
3. **vLLM**: vLLM should be installed (comes with QLM)

## Setup (Day 1 - ~30 minutes)

### Step 1: Verify QLM Installation

```bash
cd QLM
pip install -e .
export QLMPROJDIR=$(pwd)
```

### Step 2: Download ShareGPT Dataset

```bash
cd data
wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json
cd ..
```

This downloads ~500MB of conversational data.

### Step 3: Test Basic Functionality

```bash
# Quick test (10 seconds, 50 samples)
python benchmarks/workload_driver.py \
    --dataset sharegpt \
    --duration 10 \
    --max-samples 50 \
    --arrival-rate 2 \
    --no-start-vllm \
    --output test_metrics.json
```

**Expected output**: Should create `test_metrics.json` with metrics.

### Step 4: Inspect Test Results

```bash
python -c "
import json
with open('test_metrics.json') as f:
    data = json.load(f)
    print('Duration:', data['duration_sec'], 'seconds')
    print('Requests dispatched:', data['summary']['num_requests_dispatched'])
    print('Mean scheduling delay:', data['summary']['scheduling_delay_ms_mean'], 'ms')
"
```

## Running Experiments (Days 2-7)

### Option 1: Automated (Recommended)

```bash
# Make script executable
chmod +x ../scripts/phase1_runner.sh

# Start vLLM server in a separate terminal
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000

# Run all 12 experiments (takes ~12-15 hours)
../scripts/phase1_runner.sh
```

Results will be saved to `../results/phase1/`.

### Option 2: Manual (Run experiments one by one)

**Experiment E1.1: vLLM Baseline**
```bash
python benchmarks/workload_driver.py \
    --dataset sharegpt \
    --duration 60 \
    --max-samples 1000 \
    --arrival-rate 2 \
    --num-users 1 \
    --model unsloth/Llama-3.2-1B-Instruct \
    --no-start-vllm \
    --output ../results/phase1/vllm_baseline_mixed.json
```

**Experiment E1.2: QLM Baseline**
```bash
python benchmarks/workload_driver.py \
    --dataset sharegpt \
    --duration 60 \
    --max-samples 1000 \
    --arrival-rate 2 \
    --num-users 1 \
    --model unsloth/Llama-3.2-1B-Instruct \
    --no-start-vllm \
    --output ../results/phase1/qlm_baseline_mixed.json
```

**Experiment E1.3: vLLM High Rate**
```bash
python benchmarks/workload_driver.py \
    --dataset sharegpt \
    --duration 60 \
    --max-samples 1000 \
    --arrival-rate 5 \
    --num-users 1 \
    --model unsloth/Llama-3.2-1B-Instruct \
    --no-start-vllm \
    --output ../results/phase1/vllm_high_rate.json
```

Continue with remaining experiments (see `EXPERIMENT_PLAN.md` for full list).

## Analysis (Days 6-7)

### Step 1: Install Analysis Dependencies

```bash
pip install jupyter matplotlib seaborn pandas numpy
```

### Step 2: Run Analysis Notebook

```bash
cd ../analysis
jupyter notebook phase1_sharegpt.ipynb
```

### Step 3: Generate Plots

Run all cells in the notebook. This will:
- Load all 12 experiment results
- Generate 5 comparison plots
- Create summary statistics table
- Export LaTeX table for report

Plots will be saved to `analysis/plots/`.

## Deliverables Checklist

After completing Phase 1, you should have:

- [ ] 12 JSON files in `results/phase1/` with raw metrics
- [ ] 5 PNG plots in `analysis/plots/`:
  - `plot1_scheduling_delay_baseline.png`
  - `plot2_queue_length_over_time.png`
  - `plot3_throughput_vs_load.png`
  - `plot4_prompt_length_sensitivity.png`
  - `plot5_queue_dynamics_summary.png`
- [ ] `summary_statistics.csv` with all metrics
- [ ] `summary_table.tex` for Overleaf

## Adding to Overleaf Report

1. Upload plots to Overleaf (Figures folder)
2. Copy `summary_table.tex` content to Results section
3. Write methodology section describing:
   - Experimental setup (vLLM server, QLM configuration)
   - Workload parameters (arrival rate, burstiness, users, prompt lengths)
   - Metrics collected (scheduling delay, queue length, throughput)
4. Write results section with key findings:
   - QLM reduces scheduling delay by X%
   - Queue length improvements under bursty traffic
   - Prompt length sensitivity analysis

## Troubleshooting

### Error: "ShareGPT file not found"
```bash
cd QLM/data
wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json
```

### Error: "vLLM server not responding"
Make sure vLLM is running:
```bash
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000
```

Check if server is up:
```bash
curl http://localhost:8000/health
```

### Error: "Gurobi license not found"
QLM can run without Gurobi (uses heuristic scheduler). To use LP scheduler, add license to `qlm/config.yaml`:
```yaml
gurobi:
  access_id: "your_access_id"
  secret_key: "your_secret"
  license: "your_license_id"
```

### Experiments taking too long
Reduce duration and samples for faster testing:
```bash
--duration 30 --max-samples 500
```

## Timeline Estimate

- **Day 1**: Setup and verification (2-3 hours)
- **Days 2-3**: Run vLLM experiments E1.1, E1.3, E1.5, E1.7, E1.9, E1.11 (~6-8 hours runtime)
- **Days 4-5**: Run QLM experiments E1.2, E1.4, E1.6, E1.8, E1.10, E1.12 (~6-8 hours runtime)
- **Days 6-7**: Analysis and report writing (4-6 hours)

**Total**: ~20-25 hours of work over 1 week

## Next Steps After Phase 1

Once Phase 1 is complete:
1. Email supervisor with results summary
2. Start Phase 2: MAST agentic trace experiments
3. Download MAST dataset from HuggingFace
4. Implement trace preprocessing and replay infrastructure

See `EXPERIMENT_PLAN.md` for Phase 2 details.

## Questions?

- Check `EXPERIMENT_PLAN.md` for detailed experiment descriptions
- Review `QLM/README.md` for QLM-specific documentation
- Email supervisor with progress updates and blockers

---

**Good luck! You got this! 🚀**
