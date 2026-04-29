# Research Project Cheat Sheet

**Quick reference for common commands and workflows**

---

## 🚀 Quick Start (First Time Setup)

```bash
# 1. Navigate to project
cd "/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET"

# 2. Validate setup
./scripts/validate_setup.sh

# 3. Start vLLM server (separate terminal)
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000

# 4. Run Phase 1 experiments
cd QLM
../scripts/phase1_runner.sh
```

---

## 📁 Important Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `EXPERIMENT_PLAN.md` | Detailed experiment plan | Read first! Complete roadmap |
| `QUICKSTART.md` | Step-by-step Phase 1 guide | When starting experiments |
| `PROGRESS.md` | Progress tracker | Update daily |
| `README.md` | Project overview | Share with others |
| `CHEATSHEET.md` | This file | Quick reference |

---

## 🧪 Running Experiments

### Single Experiment (Manual)

```bash
cd QLM
export QLMPROJDIR=$(pwd)

# Basic experiment (60s, 1000 samples, 2 rps)
python benchmarks/workload_driver.py \
    --dataset sharegpt \
    --duration 60 \
    --max-samples 1000 \
    --arrival-rate 2 \
    --num-users 1 \
    --model unsloth/Llama-3.2-1B-Instruct \
    --no-start-vllm \
    --output ../results/phase1/my_experiment.json
```

### All Phase 1 Experiments (Automated)

```bash
cd QLM
../scripts/phase1_runner.sh
```

### Quick Test (10 seconds)

```bash
cd QLM
python benchmarks/workload_driver.py \
    --dataset sharegpt \
    --duration 10 \
    --max-samples 50 \
    --arrival-rate 2 \
    --no-start-vllm \
    --output /tmp/test.json
```

---

## 📊 Analysis

### Start Jupyter Notebook

```bash
cd analysis
jupyter notebook phase1_sharegpt.ipynb
```

### View Metrics (Command Line)

```bash
cd results/phase1
python -c "
import json
with open('vllm_baseline_mixed.json') as f:
    data = json.load(f)
    s = data['summary']
    print(f\"Requests: {s['num_requests_dispatched']}\")
    print(f\"Mean delay: {s['scheduling_delay_ms_mean']:.2f} ms\")
    print(f\"P99 delay: {s['scheduling_delay_ms_p99']:.2f} ms\")
    print(f\"Mean queue: {s['queue_length_mean']:.2f}\")
    print(f\"Max queue: {s['queue_length_max']}\")
"
```

---

## 🔧 Common Commands

### vLLM Server

```bash
# Start server
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000

# Check if running
curl http://localhost:8000/health

# Stop server
pkill -f "vllm serve"
```

### QLM Setup

```bash
# Install QLM
cd QLM
pip install -e .

# Set environment variable
export QLMPROJDIR=$(pwd)

# Test basic functionality
python benchmarks/basic_test.py
```

### Download Datasets

```bash
# ShareGPT (Phase 1)
cd QLM/data
wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json

# MAST (Phase 2)
python -c "
from huggingface_hub import hf_hub_download
import json
file_path = hf_hub_download(repo_id='mcemri/MAD', filename='MAD_full_dataset.json', repo_type='dataset')
print(f'Downloaded to: {file_path}')
"
```

---

## 📈 Experiment Parameters

### Workload Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `--arrival-rate` | 0.5, 1, 2, 5, 10 | Requests per second |
| `--burst-size` | 1, 5, 10 | Requests per burst |
| `--burst-interval` | 2.0, 5.0 | Seconds between bursts |
| `--num-users` | 1, 4, 8, 16 | Concurrent users |
| `--prompt-length` | short, medium, long | Prompt length filter |
| `--duration` | 10, 30, 60, 300 | Experiment duration (seconds) |
| `--max-samples` | 50, 500, 1000 | Max prompts to load |

### Example Combinations

```bash
# Baseline: 2 rps, 1 user, mixed prompts, 60s
--arrival-rate 2 --num-users 1 --duration 60

# High load: 5 rps, 1 user, 60s
--arrival-rate 5 --num-users 1 --duration 60

# Bursty: 5 requests every 2 seconds
--burst-size 5 --burst-interval 2.0 --duration 60

# Multi-user: 8 concurrent users, 2 rps each
--arrival-rate 2 --num-users 8 --duration 60

# Short prompts only
--arrival-rate 2 --prompt-length short --duration 60

# Long prompts only
--arrival-rate 2 --prompt-length long --duration 60
```

---

## 📋 Experiment Checklist

### Phase 1 (12 experiments)

- [ ] E1.1: vLLM Baseline (2 rps, mixed)
- [ ] E1.2: QLM Baseline (2 rps, mixed)
- [ ] E1.3: vLLM High Rate (5 rps)
- [ ] E1.4: QLM High Rate (5 rps)
- [ ] E1.5: vLLM Bursty
- [ ] E1.6: QLM Bursty
- [ ] E1.7: vLLM Multi-User (8 users)
- [ ] E1.8: QLM Multi-User (8 users)
- [ ] E1.9: vLLM Short Prompts
- [ ] E1.10: QLM Short Prompts
- [ ] E1.11: vLLM Long Prompts
- [ ] E1.12: QLM Long Prompts

### Analysis Tasks

- [ ] Run Jupyter notebook
- [ ] Generate 5 plots
- [ ] Create summary table
- [ ] Calculate improvement percentages
- [ ] Export LaTeX table

### Report Tasks

- [ ] Write Methodology section
- [ ] Write Results section
- [ ] Insert figures
- [ ] Insert summary table
- [ ] Write Discussion section

---

## 🐛 Troubleshooting

### Problem: ShareGPT not found

```bash
cd QLM/data
wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json
```

### Problem: vLLM not responding

```bash
# Check if running
curl http://localhost:8000/health

# Restart
pkill -f "vllm serve"
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000
```

### Problem: No GPU

```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.device_count())  # Should be > 0
print(torch.cuda.get_device_name(0))  # GPU name
```

### Problem: Experiments too slow

```bash
# Reduce duration and samples
--duration 30 --max-samples 500
```

### Problem: Out of memory

```bash
# Use smaller model
--model unsloth/Llama-3.2-1B-Instruct

# Reduce batch size (in QLM config.yaml)
max_batch_size: 5
```

---

## 📊 Key Metrics Reference

| Metric | Abbreviation | Unit | Good Value |
|--------|--------------|------|------------|
| Time to First Token | TTFT | ms | < 100 ms |
| Time per Output Token | TPOT | ms | < 10 ms |
| End-to-End Latency | E2E | ms | < 1000 ms |
| Scheduling Delay | - | ms | < 50 ms |
| Requests per Second | RPS | req/s | Higher is better |
| Tokens per Second | TPS | tok/s | Higher is better |
| SLO Attainment | - | % | > 95% |
| GPU Utilization | - | % | > 80% |
| Queue Length | - | count | Lower is better |

---

## 🔗 Important Links

### Documentation
- Experiment Plan: `EXPERIMENT_PLAN.md`
- Quick Start: `QUICKSTART.md`
- Progress Tracker: `PROGRESS.md`

### Papers
- MAST: https://arxiv.org/pdf/2503.13657
- QLM: https://dl.acm.org/doi/10.1145/3698038.3698523
- Continuum: https://arxiv.org/abs/2511.02230
- LLM-Inference-Bench: https://arxiv.org/abs/2411.00136

### Datasets
- ShareGPT: https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered
- MAST/MAD: https://huggingface.co/datasets/mcemri/MAD

### Report
- Overleaf: https://www.overleaf.com/7334415764npgkvkfrzfvj#ef3e65

---

## ⏱️ Time Estimates

| Task | Time | Notes |
|------|------|-------|
| Setup & validation | 30 min | First time only |
| Single experiment | 1-2 min | 60s duration + overhead |
| All 12 Phase 1 experiments | 12-15 hours | Includes runtime + setup |
| Analysis (Jupyter) | 1-2 hours | Generate all plots |
| Report writing (Phase 1) | 4-6 hours | Methodology + Results |
| **Total Phase 1** | **20-25 hours** | Over 1-2 weeks |

---

## 📧 Communication

### Email Updates (Template)

```
Subject: [Research Update] Phase 1 Progress - Week X

Hi Prof. Gupta,

Progress update for week X:

Completed:
- [x] Task 1
- [x] Task 2

In Progress:
- [ ] Task 3

Blockers:
- Issue 1 (need help with X)

Next Steps:
- Task 4
- Task 5

Results Summary:
- Key finding 1
- Key finding 2

Attachments:
- plot1.png
- plot2.png

Best,
Neil
```

### Questions for Supervisor

1. Gurobi license for QLM LP scheduler?
2. Delta cluster GPU access?
3. MAST trace format clarification?
4. Continuum comparison priority?

---

## 🎯 Success Criteria

### Phase 1
- ✅ 12 experiments completed
- ✅ 5 plots generated
- ✅ Methodology + Results drafted
- ✅ Clear understanding of QLM benefits

### Phase 2
- ✅ MAST traces preprocessed
- ✅ 3 scheduling heuristics implemented
- ✅ 7 experiments completed
- ✅ 3-4 additional plots

### Final Report
- ✅ 6-7 high-quality figures
- ✅ 10-15 page report
- ✅ Reproducible codebase
- ✅ Clear contributions

---

**Last Updated**: March 30, 2026  
**Version**: 1.0
