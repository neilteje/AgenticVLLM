# Efficient Execution of Agentic Traces Using vLLM

**Research Project - Spring 2026**  
**Student**: Neil Teje 

---

## Project Overview

This project investigates how to efficiently schedule agentic execution traces (multi-step, interdependent LLM calls) using vLLM and QLM serving engines. We benchmark performance on conversational workloads (ShareGPT) and agentic workloads (MAST traces) to understand scheduling requirements and optimize serving infrastructure.

### Research Questions

1. How do agentic workloads differ from conversational workloads in terms of:
   - Request patterns (burstiness, dependencies, context growth)
   - Latency and throughput requirements
   - Resource utilization (GPU, memory, KV cache)

2. How can we design trace-aware scheduling mechanisms to:
   - Identify latency-sensitive vs throughput-sensitive steps
   - Batch similar tool calls across traces
   - Manage context growth and KV cache efficiently

3. How do different serving engines (vLLM, QLM, Continuum) compare on agentic workloads?

---

## Repository Structure

```
MONET/
├── QLM/                          # QLM codebase (SLO-aware LLM serving)
│   ├── benchmarks/
│   │   ├── basic_test.py         # Basic QLM functionality test
│   │   └── workload_driver.py    # Phase 1 experiment driver
│   ├── qlm/
│   │   ├── workload/
│   │   │   ├── datasets.py       # ShareGPT + HuggingFace loaders
│   │   │   └── metrics.py        # Metrics collection
│   │   ├── queue/
│   │   │   └── queue.py          # QLM scheduler
│   │   └── config.yaml           # QLM configuration
│   └── data/
│       └── ShareGPT_V3_unfiltered_cleaned_split.json
│
├── MAST/                         # MAST reference code & traces
│   ├── traces/                   # Multi-agent execution traces
│   └── README.md
│
├── scripts/
│   ├── validate_setup.sh         # Setup validator (run this first!)
│   └── phase1_runner.sh          # Phase 1 experiment runner
│
├── analysis/
│   ├── phase1_sharegpt.ipynb     # Phase 1 analysis notebook
│   └── plots/                    # Generated figures
│
├── results/
│   ├── phase1/                   # Phase 1 experiment outputs
│   └── phase2/                   # Phase 2 experiment outputs
│
├── EXPERIMENT_PLAN.md            # Detailed experiment plan (READ THIS!)
├── QUICKSTART.md                 # Quick start guide for Phase 1
├── PROGRESS.md                   # Progress tracking document
└── README.md                     # This file
```

---

## Quick Start

### 1. Validate Setup (5 minutes)

```bash
cd /Users/neilteje/Desktop/uiuc\ 2025-2026/Research/MONET
chmod +x scripts/validate_setup.sh
./scripts/validate_setup.sh
```

This will check:
- QLM installation
- Required Python packages
- ShareGPT dataset
- vLLM installation
- GPU availability
- Directory structure

### 2. Start vLLM Server

```bash
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000
```

Keep this running in a separate terminal.

### 3. Run Phase 1 Experiments (12-15 hours)

```bash
cd QLM
chmod +x ../scripts/phase1_runner.sh
../scripts/phase1_runner.sh
```

This runs all 12 ShareGPT baseline experiments comparing vLLM and QLM.

### 4. Analyze Results

```bash
cd ../analysis
jupyter notebook phase1_sharegpt.ipynb
```

Run all cells to generate plots and summary statistics.

---

## Documentation

### Essential Reading (Start Here!)

1. **EXPERIMENT_PLAN.md** - Comprehensive experiment plan with:
   - Phase 1: ShareGPT baseline (12 experiments)
   - Phase 2: Agentic traces (7 experiments)
   - Phase 3: Continuum comparison (stretch goal)
   - Metrics, workload parameters, expected deliverables

2. **QUICKSTART.md** - Step-by-step guide to run Phase 1 experiments

3. **PROGRESS.md** - Progress tracker with:
   - Task checklists
   - Meeting logs
   - Questions for supervisor
   - Success criteria

### Reference Papers

- **MAST**: [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/pdf/2503.13657)
- **QLM**: [Queue Management for SLO-Oriented LLM Serving](https://dl.acm.org/doi/10.1145/3698038.3698523)
- **Continuum**: [Multi-Turn LLM Agent Scheduling with KV Cache TTL](https://arxiv.org/abs/2511.02230)
- **LLM-Inference-Bench**: [Benchmarking LLM Serving](https://arxiv.org/abs/2411.00136)
- **Etalon**: [Holistic Performance Evaluation Framework](https://arxiv.org/abs/2507.09019)

---

## Project Timeline

### Phase 1: ShareGPT Baseline (Weeks 1-2) - **URGENT**

**Goal**: Establish baseline performance of vLLM and QLM on conversational workloads.

- **Week 1**: Setup, vLLM experiments (E1.1, E1.3, E1.5, E1.7, E1.9, E1.11)
- **Week 2**: QLM experiments (E1.2, E1.4, E1.6, E1.8, E1.10, E1.12), analysis, report writing

**Deliverables**:
- 12 experiment results (JSON files)
- 5 comparison plots
- Methodology + Results sections in report

### Phase 2: Agentic Traces (Weeks 3-6)

**Goal**: Evaluate trace-aware scheduling for agentic workloads.

- **Week 3**: MAST trace preprocessing and analysis
- **Week 4**: Trace replay infrastructure
- **Week 5**: Trace-aware scheduling heuristics
- **Week 6**: Experiments, analysis, report writing

**Deliverables**:
- MAST trace characterization (2-3 graphs)
- 3 trace-aware scheduling heuristics
- 7 experiment results
- 3-4 additional plots for report

### Phase 3: Continuum Comparison (Week 7+) - **Stretch Goal**

**Goal**: Compare QLM against Continuum scheduler.

**Deliverables**:
- Continuum benchmark results
- Three-way comparison (vLLM vs QLM vs Continuum)
- 1-2 additional plots

---

## Experiments Overview

### Phase 1: ShareGPT Baseline (12 experiments)

| Exp | System | Workload | Arrival | Burst | Users | Prompts | Duration |
|-----|--------|----------|---------|-------|-------|---------|----------|
| E1.1 | vLLM | ShareGPT | 2 rps | No | 1 | Mixed | 60s |
| E1.2 | QLM | ShareGPT | 2 rps | No | 1 | Mixed | 60s |
| E1.3 | vLLM | ShareGPT | 5 rps | No | 1 | Mixed | 60s |
| E1.4 | QLM | ShareGPT | 5 rps | No | 1 | Mixed | 60s |
| E1.5 | vLLM | ShareGPT | 2 rps | Yes | 1 | Mixed | 60s |
| E1.6 | QLM | ShareGPT | 2 rps | Yes | 1 | Mixed | 60s |
| E1.7 | vLLM | ShareGPT | 2 rps | No | 8 | Mixed | 60s |
| E1.8 | QLM | ShareGPT | 2 rps | No | 8 | Mixed | 60s |
| E1.9 | vLLM | ShareGPT | 2 rps | No | 1 | Short | 60s |
| E1.10 | QLM | ShareGPT | 2 rps | No | 1 | Short | 60s |
| E1.11 | vLLM | ShareGPT | 2 rps | No | 1 | Long | 60s |
| E1.12 | QLM | ShareGPT | 2 rps | No | 1 | Long | 60s |

**Metrics**: Scheduling delay, queue length, throughput, SLO attainment

### Phase 2: Agentic Traces (7 experiments)

| Exp | System | Dataset | Scheduling | Traces | Arrival | Duration |
|-----|--------|---------|------------|--------|---------|----------|
| E2.1 | vLLM | MAST | FCFS | 100 | 1 tps | 300s |
| E2.2 | QLM | MAST | SLO-aware | 100 | 1 tps | 300s |
| E2.3 | QLM | MAST | Step Priority | 100 | 1 tps | 300s |
| E2.4 | QLM | MAST | Semantic Batch | 100 | 1 tps | 300s |
| E2.5 | QLM | MAST | Context-Aware | 100 | 1 tps | 300s |
| E2.6 | vLLM | MAST | FCFS | 100 | 5 tps | 300s |
| E2.7 | QLM | MAST | Best Heuristic | 100 | 5 tps | 300s |

**Metrics**: Trace completion time, step-level latency, batching efficiency, semantic similarity

---

## Key Metrics

### Latency Metrics
- **Time to First Token (TTFT)**: Time from request submission to first token
- **Time per Output Token (TPOT)**: Average time per generated token
- **End-to-End Latency**: Total request completion time
- **Scheduling Delay**: Time spent waiting in queue

### Throughput Metrics
- **Requests per Second (RPS)**: Request completion rate
- **Tokens per Second (TPS)**: Token generation rate

### SLO Metrics (QLM-specific)
- **SLO Attainment**: Percentage of requests meeting SLO
- **SLO Violation Rate**: Percentage of requests exceeding SLO

### Resource Metrics
- **GPU Utilization**: GPU compute usage (%)
- **Queue Length**: Number of requests waiting
- **Batch Size**: Average batch size during inference

### Trace Metrics (Phase 2)
- **Trace Completion Time**: End-to-end time for multi-step trace
- **Step Latency**: Per-step execution time
- **Batching Efficiency**: Latency reduction from batching similar steps

---

## Report Structure

### Overleaf Link
https://www.overleaf.com/7334415764npgkvkfrzfvj#ef3e65

### Target Sections
1. Abstract
2. Introduction (motivation, problem, contribution)
3. Background (vLLM, QLM, MAST, agentic systems)
4. Methodology (experimental setup, workloads, metrics)
5. Workload Characterization (ShareGPT vs MAST analysis)
6. System Design (trace-aware scheduling heuristics)
7. Experimental Results (6-7 graphs)
8. Discussion (key findings, limitations, future work)
9. Related Work (Sarathi, ORCA, Continuum, etc.)
10. Conclusion

### Target Figures (6-7 total)
1. Scheduling Delay CDF (vLLM vs QLM on ShareGPT)
2. Queue Length Over Time (4 subplots: baseline, high rate, bursty, multi-user)
3. Throughput vs Load (bar chart)
4. Prompt Length Sensitivity (2 subplots: mean delay, P99 delay)
5. Queue Dynamics Summary (mean/max queue length)
6. Trace Completion Time (agentic traces, multiple schedulers)
7. Workload Comparison (ShareGPT vs MAST characteristics)

---

## Development Workflow

### Daily Workflow
1. Update `PROGRESS.md` with completed tasks
2. Run experiments and save results to `results/`
3. Analyze results in Jupyter notebook
4. Update Overleaf report with findings
5. Commit code changes (if applicable)

### Weekly Workflow
1. Email supervisor with progress update
2. Review experiment results and identify issues
3. Plan next week's experiments
4. Update `PROGRESS.md` with next steps

---

## Troubleshooting

### Common Issues

**1. ShareGPT dataset not found**
```bash
cd QLM/data
wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json
```

**2. vLLM server not responding**
```bash
# Check if server is running
curl http://localhost:8000/health

# Restart server
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000
```

**3. GPU not detected**
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.device_count())  # Should be > 0
```

**4. Experiments taking too long**
Reduce duration and samples for faster testing:
```bash
--duration 30 --max-samples 500
```

**5. Gurobi license error**
QLM can run without Gurobi (uses heuristic scheduler). If you have a license, add to `QLM/qlm/config.yaml`:
```yaml
gurobi:
  access_id: "your_access_id"
  secret_key: "your_secret"
  license: "your_license_id"
```

---

## Contact & Support

- **Student**: Neil Teje
- **Supervisor**: Prof. Ragini Gupta
- **Overleaf Report**: https://www.overleaf.com/7334415764npgkvkfrzfvj#ef3e65

---

## Acknowledgments

This project builds on:
- **QLM** by Patke et al. (UIUC & IBM Research)
- **MAST** by Cemri et al. (UC Berkeley)
- **vLLM** by UC Berkeley Sky Computing Lab
- **Continuum** by Li et al. (UC Berkeley)

---

## License

Research code for academic use. See individual repositories for specific licenses:
- QLM: Check `QLM/` repository
- MAST: Check `MAST/` repository

---

**Last Updated**: March 30, 2026  
**Status**: Phase 1 setup complete, ready to start experiments
