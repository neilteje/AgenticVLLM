# Efficient Execution of Agentic Traces Using vLLM - Experiment Plan

**Project Goal**: Design and evaluate trace-aware scheduling mechanisms for agentic LLM workloads on top of vLLM and QLM serving engines.

**Timeline**: Phase 1 (ShareGPT experiments) - 1-2 weeks | Phase 2 (Agentic traces) - Ongoing

---

## Executive Summary

This project investigates how to efficiently schedule agentic execution traces (multi-step, interdependent LLM calls) using vLLM and QLM serving engines. We will:

1. **Phase 1 (URGENT - 1-2 weeks)**: Benchmark vLLM and QLM on conversational workloads (ShareGPT) to establish baseline performance
2. **Phase 2**: Extend benchmarking to agentic traces from MAST dataset
3. **Phase 3 (Stretch)**: Compare against Continuum scheduler for multi-turn agent workloads

The key research question: **How do agentic workloads (multi-step, tool-calling, interdependent requests) differ from conversational workloads in terms of scheduling requirements, and how can we optimize serving engines for them?**

---

## Background Context

### Key Papers & Systems

1. **MAST (Multi-Agent Systems Failure Taxonomy)**
   - Paper: https://arxiv.org/pdf/2503.13657
   - Dataset: https://huggingface.co/datasets/mcemri/MAD (1K+ annotated multi-agent traces)
   - Provides real agentic execution traces with tool calls, reasoning steps, failures

2. **QLM (Queue Management for SLO-oriented LLM Serving)**
   - Paper: https://dl.acm.org/doi/10.1145/3698038.3698523
   - Code: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/QLM/`
   - Key features: Request grouping, virtual queues, RWT (Request Waiting Time) estimation, SLO-aware scheduling
   - Built on top of vLLM with optimization-based scheduler (uses Gurobi)

3. **Continuum (Multi-Turn LLM Agent Scheduling with KV Cache TTL)**
   - Paper: https://arxiv.org/abs/2511.02230
   - Code: https://github.com/Hanchenli/vllm-continuum
   - Optimizes multi-turn agent conversations with KV cache time-to-live management

4. **Benchmarking References**
   - LLM-Inference-Bench: https://arxiv.org/abs/2411.00136
   - Etalon Framework: https://arxiv.org/abs/2507.09019
   - Sarathi-Serve, ORCA, SHEPHERD (baseline schedulers)

---

## Phase 1: ShareGPT Baseline Experiments (URGENT - 1-2 weeks)

### Objective
Establish baseline performance characteristics of vLLM and QLM on standard conversational workloads before moving to agentic traces.

### Datasets
- **Primary**: ShareGPT (conversational, single-turn request-response)
  - Location: `QLM/data/ShareGPT_V3_unfiltered_cleaned_split.json`
  - Download: `wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json`
- **Alternative**: LMSYS-Chat-1M, WildChat, UltraChat (already supported in `qlm/workload/datasets.py`)

### Systems to Benchmark
1. **vLLM (baseline)** - Default FCFS scheduler
2. **QLM** - SLO-aware scheduler with request grouping and RWT estimation

### Workload Parameters to Vary

#### 1. Request Arrival Patterns
- **Arrival Rate**: 0.5, 1, 2, 5, 10 requests/sec
- **Burstiness**: 
  - Steady (Poisson): uniform arrival
  - Bursty: 5 requests every 2 seconds, 10 requests every 5 seconds
- **Concurrent Users**: 1, 4, 8, 16 users

#### 2. Prompt Characteristics
- **Prompt Length Distribution**:
  - Short: ≤200 chars
  - Medium: 200-1000 chars
  - Long: >1000 chars
  - Mixed: natural distribution from dataset
- **Output Token Distribution**: 
  - Controlled via sampling parameters (max_tokens: 128, 256, 512, 1024)

#### 3. SLO Configurations (QLM-specific)
- **Interactive requests**: SLO = 10s (tight latency requirements)
- **Batch requests**: SLO = 1000s (throughput-oriented)
- **Mixed workload**: 50/50 interactive/batch

#### 4. Model Configurations
- **Single model**: Llama-3.2-1B-Instruct (fast inference)
- **Multi-model** (stretch): Llama-3.1-8B + Llama-3.1-70B

### Metrics to Collect

#### Primary Metrics (from papers)
1. **Latency Metrics**:
   - Time to First Token (TTFT) - p50, p95, p99
   - Time per Output Token (TPOT) - p50, p95, p99
   - End-to-End Latency - p50, p95, p99
   - Scheduling Delay (queue waiting time)

2. **Throughput Metrics**:
   - Requests per second (RPS)
   - Tokens per second (TPS) - input + output
   - Request completion rate

3. **SLO Metrics** (QLM-specific):
   - SLO Attainment (% requests meeting SLO)
   - SLO Violation Rate
   - SLO headroom distribution

4. **Resource Utilization**:
   - GPU Utilization (%)
   - GPU Memory Usage
   - Batch size distribution
   - KV Cache utilization

5. **Queue Dynamics**:
   - Queue length over time (mean, max, p95)
   - Queue drain time
   - Head-of-Line (HOL) blocking time
   - Backpressure samples

#### Secondary Metrics
- Request eviction rate (if applicable)
- Model swap overhead (multi-model scenarios)
- Scheduling overhead (time spent in scheduler)
- Goodput (useful work vs total work)

### Experiment Matrix

| Exp ID | System | Dataset | Arrival | Burst | Users | Prompt Len | SLO Mix | Duration | Output File |
|--------|--------|---------|---------|-------|-------|------------|---------|----------|-------------|
| E1.1   | vLLM   | ShareGPT | 2 rps  | No    | 1     | Mixed      | N/A     | 60s      | `vllm_baseline_mixed.json` |
| E1.2   | QLM    | ShareGPT | 2 rps  | No    | 1     | Mixed      | 50/50   | 60s      | `qlm_baseline_mixed.json` |
| E1.3   | vLLM   | ShareGPT | 5 rps  | No    | 1     | Mixed      | N/A     | 60s      | `vllm_high_rate.json` |
| E1.4   | QLM    | ShareGPT | 5 rps  | No    | 1     | Mixed      | 50/50   | 60s      | `qlm_high_rate.json` |
| E1.5   | vLLM   | ShareGPT | 2 rps  | Yes   | 1     | Mixed      | N/A     | 60s      | `vllm_bursty.json` |
| E1.6   | QLM    | ShareGPT | 2 rps  | Yes   | 1     | Mixed      | 50/50   | 60s      | `qlm_bursty.json` |
| E1.7   | vLLM   | ShareGPT | 2 rps  | No    | 8     | Mixed      | N/A     | 60s      | `vllm_multiuser.json` |
| E1.8   | QLM    | ShareGPT | 2 rps  | No    | 8     | Mixed      | 50/50   | 60s      | `qlm_multiuser.json` |
| E1.9   | vLLM   | ShareGPT | 2 rps  | No    | 1     | Short      | N/A     | 60s      | `vllm_short_prompts.json` |
| E1.10  | QLM    | ShareGPT | 2 rps  | No    | 1     | Short      | 50/50   | 60s      | `qlm_short_prompts.json` |
| E1.11  | vLLM   | ShareGPT | 2 rps  | No    | 1     | Long       | N/A     | 60s      | `vllm_long_prompts.json` |
| E1.12  | QLM    | ShareGPT | 2 rps  | No    | 1     | Long       | 50/50   | 60s      | `qlm_long_prompts.json` |

**Total**: 12 core experiments (~12-15 hours runtime)

### Implementation Steps

#### Step 1: Setup & Verification (Day 1)
- [ ] Verify QLM installation and dependencies
- [ ] Download ShareGPT dataset to `QLM/data/`
- [ ] Test basic vLLM endpoint: `python benchmarks/basic_test.py`
- [ ] Verify Gurobi license for QLM (if using LP scheduler)
- [ ] Test workload driver: `python benchmarks/workload_driver.py --duration 10 --max-samples 50`

#### Step 2: vLLM Baseline Experiments (Days 2-3)
- [ ] Start vLLM server: `vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000`
- [ ] Run experiments E1.1, E1.3, E1.5, E1.7, E1.9, E1.11 (vLLM baseline)
- [ ] Collect and validate metrics JSON files
- [ ] Generate preliminary visualizations (queue length, latency CDFs)

#### Step 3: QLM Experiments (Days 4-5)
- [ ] Configure QLM with SLO settings in `qlm/config.yaml`
- [ ] Run experiments E1.2, E1.4, E1.6, E1.8, E1.10, E1.12 (QLM)
- [ ] Collect and validate metrics JSON files
- [ ] Compare against vLLM baseline

#### Step 4: Analysis & Visualization (Days 6-7)
- [ ] Generate comparison plots:
  - Latency CDFs (TTFT, TPOT, E2E) - vLLM vs QLM
  - Throughput over time
  - Queue length over time
  - SLO attainment vs arrival rate
  - GPU utilization vs load
- [ ] Statistical analysis (mean, median, p95, p99 for all metrics)
- [ ] Write methodology section for report
- [ ] Draft initial results section

### Expected Deliverables (End of Week 2)
1. **Metrics Dataset**: 12 JSON files with raw time-series data
2. **Analysis Notebook**: Jupyter notebook with all plots and statistical summaries
3. **Report Sections**:
   - Methodology (experimental setup, workload parameters, metrics)
   - Results (4-5 graphs comparing vLLM vs QLM on ShareGPT)
4. **Key Findings**: 1-page summary of vLLM vs QLM performance on conversational workloads

---

## Phase 2: Agentic Trace Experiments (Weeks 3-6)

### Objective
Evaluate how agentic workloads (multi-step, tool-calling, interdependent requests) differ from conversational workloads and identify scheduling optimizations.

### Datasets
- **MAST Traces**: Multi-agent execution traces from HuggingFace
  - Full dataset: `mcemri/MAD` (1K+ traces)
  - Human-labeled subset: `MAD_human_labelled_dataset.json`
  - Trace structure: Multi-turn conversations with tool calls, reasoning steps, failures
- **Trace Characteristics to Analyze**:
  - Number of steps per trace
  - Tool call patterns (sequential vs parallel)
  - Context growth over trace execution
  - Dependency structure (which steps depend on previous outputs)

### Key Research Questions
1. **Workload Characterization**:
   - How do agentic traces differ from ShareGPT in prompt length, output length, burstiness?
   - What is the distribution of trace lengths (number of LLM calls per task)?
   - What fraction of steps are tool calls vs reasoning?
   - How much context accumulates across trace execution?

2. **Scheduling Opportunities**:
   - Can we identify latency-sensitive vs throughput-sensitive steps within a trace?
   - Can we parallelize independent tool calls within a trace?
   - How do we batch similar tool calls across different traces?
   - What is the benefit of trace-aware scheduling vs treating each step independently?

3. **Performance Comparison**:
   - How does QLM's SLO-aware scheduling help with agentic workloads?
   - What is the overhead of trace-aware scheduling?
   - How does multi-step context management affect KV cache utilization?

### Implementation Tasks

#### Task 1: MAST Trace Preprocessing (Week 3)
- [ ] Download MAST dataset from HuggingFace
- [ ] Parse trace structure (extract LLM calls, tool calls, dependencies)
- [ ] Tokenize traces using tiktoken (as mentioned by supervisor)
- [ ] Analyze trace statistics:
  - Distribution of trace lengths
  - Distribution of prompt/output lengths per step
  - Tool call frequency and types
  - Context accumulation patterns
- [ ] Create trace dataset loader for QLM (similar to `qlm/workload/datasets.py`)

#### Task 2: Trace Replay Infrastructure (Week 3-4)
- [ ] Implement trace executor that respects dependencies
- [ ] Add support for multi-step traces in QLM queue
- [ ] Implement trace-level metrics (end-to-end trace completion time, step-level latency)
- [ ] Add trace ID tracking for correlation

#### Task 3: Trace-Aware Scheduling Heuristics (Week 4-5)
- [ ] **Heuristic 1: Step Priority** - Assign priorities based on:
  - Critical path analysis (which steps block others)
  - Step type (tool call vs reasoning)
  - Remaining trace budget
- [ ] **Heuristic 2: Semantic Batching** - Group similar tool calls:
  - Tokenize tool call prompts
  - Compute semantic similarity (cosine similarity of token embeddings)
  - Batch similar calls across traces
- [ ] **Heuristic 3: Context-Aware Scheduling** - Consider KV cache:
  - Prioritize traces with warm KV cache
  - Evict cold traces under memory pressure
- [ ] Integrate heuristics into QLM scheduler

#### Task 4: Agentic Trace Experiments (Week 5-6)
- [ ] Run baseline experiments (vLLM + QLM) on MAST traces
- [ ] Run trace-aware scheduling experiments
- [ ] Compare against ShareGPT baseline
- [ ] Analyze scheduling decisions (which heuristics help most?)

### Experiment Matrix (Agentic Traces)

| Exp ID | System | Dataset | Scheduling | Traces | Arrival | Duration | Metrics |
|--------|--------|---------|------------|--------|---------|----------|---------|
| E2.1   | vLLM   | MAST    | FCFS       | 100    | 1 tps   | 300s     | Baseline agentic |
| E2.2   | QLM    | MAST    | SLO-aware  | 100    | 1 tps   | 300s     | QLM agentic |
| E2.3   | QLM    | MAST    | Step Priority | 100 | 1 tps   | 300s     | Trace-aware v1 |
| E2.4   | QLM    | MAST    | Semantic Batch | 100 | 1 tps  | 300s     | Trace-aware v2 |
| E2.5   | QLM    | MAST    | Context-Aware | 100 | 1 tps  | 300s     | Trace-aware v3 |
| E2.6   | vLLM   | MAST    | FCFS       | 100    | 5 tps   | 300s     | High load |
| E2.7   | QLM    | MAST    | Best Heuristic | 100 | 5 tps | 300s     | High load optimized |

### Metrics (Agentic-Specific)
- **Trace-Level**:
  - End-to-end trace completion time (p50, p95, p99)
  - Trace SLO attainment
  - Steps completed per trace
  - Trace failure rate
- **Step-Level**:
  - Per-step latency (tool calls vs reasoning)
  - Step scheduling delay
  - Step batching efficiency (how many steps batched together)
- **Semantic Similarity Analysis**:
  - Distribution of similarity scores for tool calls
  - Batching opportunities (% of steps that could be batched)
  - Batching effectiveness (latency reduction from batching)

### Expected Deliverables (End of Week 6)
1. **MAST Trace Analysis**: Characterization of agentic workload patterns
2. **Trace-Aware Scheduler**: Implementation of 3 scheduling heuristics
3. **Experimental Results**: 7 experiments comparing scheduling strategies
4. **Report Sections**:
   - Agentic Workload Characterization (2-3 graphs)
   - Trace-Aware Scheduling Design
   - Performance Comparison (3-4 graphs)
5. **Key Findings**: How agentic workloads differ and which scheduling strategies work best

---

## Phase 3: Continuum Comparison (Stretch Goal)

### Objective
Compare QLM against Continuum, a state-of-the-art multi-turn agent scheduler.

### Tasks
- [ ] Install Continuum: https://github.com/Hanchenli/vllm-continuum
- [ ] Adapt MAST traces to Continuum format
- [ ] Run experiments E2.1-E2.7 with Continuum
- [ ] Compare QLM vs Continuum on agentic traces
- [ ] Analyze KV cache TTL effectiveness

### Expected Deliverables
1. **Continuum Benchmark Results**: Same metrics as Phase 2
2. **Three-Way Comparison**: vLLM vs QLM vs Continuum
3. **Report Section**: Related Work and Comparison (1-2 graphs)

---

## Technical Infrastructure

### Compute Resources
- **Delta Cluster** (UIUC): GPU nodes for experiments
- **Local Development**: MacBook for preprocessing and analysis

### Software Stack
- **vLLM**: Latest stable release
- **QLM**: Custom fork with trace support
- **Python Libraries**: 
  - `tiktoken` (tokenization)
  - `numpy`, `pandas` (data analysis)
  - `matplotlib`, `seaborn` (visualization)
  - `datasets` (HuggingFace)
  - `gurobipy` (QLM optimization)

### Code Structure
```
MONET/
├── QLM/                          # QLM codebase
│   ├── benchmarks/
│   │   ├── basic_test.py
│   │   ├── workload_driver.py    # Phase 1 experiments
│   │   └── trace_driver.py       # Phase 2 experiments (TO CREATE)
│   ├── qlm/
│   │   ├── workload/
│   │   │   ├── datasets.py       # ShareGPT + HF loaders
│   │   │   ├── mast_traces.py    # MAST trace loader (TO CREATE)
│   │   │   └── metrics.py        # Metrics collection
│   │   ├── queue/
│   │   │   └── queue.py          # QLM scheduler
│   │   └── schedulers/
│   │       └── trace_aware.py    # Trace-aware heuristics (TO CREATE)
│   └── data/
│       ├── ShareGPT_V3_unfiltered_cleaned_split.json
│       └── mast_traces/          # MAST dataset (TO CREATE)
├── MAST/                         # MAST reference code
├── analysis/                     # Analysis notebooks (TO CREATE)
│   ├── phase1_sharegpt.ipynb
│   ├── phase2_agentic.ipynb
│   └── plots/
├── results/                      # Experiment outputs (TO CREATE)
│   ├── phase1/
│   └── phase2/
└── EXPERIMENT_PLAN.md           # This file
```

---

## Report Structure (Overleaf)

### Sections to Write
1. **Abstract** (write last)
2. **Introduction**
   - Motivation: Why agentic workloads matter
   - Problem: Existing serving engines don't optimize for traces
   - Contribution: Trace-aware scheduling + benchmarking
3. **Background**
   - LLM Serving (vLLM, paged attention, continuous batching)
   - SLO-Aware Scheduling (QLM)
   - Agentic Systems (MAST)
4. **Methodology** (write NOW for Phase 1)
   - Experimental Setup
   - Workload Parameters
   - Metrics
   - Systems Under Test
5. **Workload Characterization** (after Phase 2)
   - ShareGPT Analysis
   - MAST Trace Analysis
   - Comparison: Conversational vs Agentic
6. **System Design** (after Phase 2)
   - Trace-Aware Scheduling Heuristics
   - Implementation Details
7. **Experimental Results**
   - Phase 1: ShareGPT Baseline (4-5 graphs)
   - Phase 2: Agentic Traces (3-4 graphs)
   - Phase 3: Continuum Comparison (1-2 graphs, if time)
8. **Discussion**
   - Key Findings
   - Limitations
   - Future Work
9. **Related Work**
10. **Conclusion**

### Target Graphs (6-7 total)
1. **Latency CDF**: vLLM vs QLM on ShareGPT (TTFT, E2E)
2. **Throughput vs Load**: Requests/sec vs arrival rate
3. **SLO Attainment**: % requests meeting SLO vs load
4. **Queue Dynamics**: Queue length over time (steady vs bursty)
5. **Trace Completion Time**: Agentic traces (vLLM vs QLM vs trace-aware)
6. **Batching Effectiveness**: Latency reduction from semantic batching
7. **Workload Comparison**: ShareGPT vs MAST characteristics (prompt length, context growth)

---

## Immediate Action Items (This Week)

### Day 1-2: Setup
- [x] Read this plan thoroughly
- [ ] Verify QLM installation: `cd QLM && pip install -e .`
- [ ] Download ShareGPT: `cd QLM/data && wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json`
- [ ] Test basic vLLM: `python benchmarks/basic_test.py`
- [ ] Test workload driver: `python benchmarks/workload_driver.py --duration 10 --max-samples 50 --output test_metrics.json`
- [ ] Inspect metrics JSON to understand format

### Day 3-4: vLLM Baseline
- [ ] Start vLLM server on GPU node
- [ ] Run experiments E1.1, E1.3, E1.5, E1.7, E1.9, E1.11
- [ ] Verify metrics collection (check JSON files)
- [ ] Create analysis notebook: `analysis/phase1_sharegpt.ipynb`
- [ ] Generate preliminary plots (latency, throughput, queue length)

### Day 5-7: QLM Experiments
- [ ] Configure QLM SLO settings
- [ ] Run experiments E1.2, E1.4, E1.6, E1.8, E1.10, E1.12
- [ ] Compare vLLM vs QLM results
- [ ] Write methodology section in Overleaf
- [ ] Draft initial results section with 4-5 graphs
- [ ] Email supervisor with progress update

---

## Success Criteria

### Phase 1 (Week 2)
- ✅ 12 experiments completed with valid metrics
- ✅ 4-5 comparison graphs (vLLM vs QLM on ShareGPT)
- ✅ Methodology + Results sections drafted in Overleaf
- ✅ Understanding of QLM's SLO-aware scheduling benefits

### Phase 2 (Week 6)
- ✅ MAST traces preprocessed and loaded
- ✅ Trace-aware scheduling heuristics implemented
- ✅ 7 agentic trace experiments completed
- ✅ 3-4 additional graphs in report
- ✅ Characterization of agentic vs conversational workloads

### Final Report
- ✅ 6-7 high-quality graphs
- ✅ Complete technical report (10-15 pages)
- ✅ Reproducible codebase on GitHub
- ✅ Clear findings on trace-aware scheduling effectiveness

---

## Open Questions & Next Steps

### Questions for Supervisor
1. **Gurobi License**: Do we have access to the Gurobi license for QLM's LP scheduler?
2. **Compute Resources**: What GPU nodes are available on Delta? How to submit jobs?
3. **MAST Trace Format**: What is the exact structure of MAST traces? Do we need to preprocess them?
4. **Semantic Similarity**: Should we use tiktoken embeddings or a different approach for batching similar tool calls?
5. **Continuum Priority**: Is Continuum comparison essential or stretch goal?

### Immediate Next Steps (After Supervisor Approval)
1. Start Phase 1 experiments immediately (ShareGPT baseline)
2. Parallelize: Run vLLM experiments while setting up QLM
3. Document everything in Overleaf as we go
4. Weekly progress updates to supervisor

---

## References

### Papers
- [MAST] Cemri et al., "Why Do Multi-Agent LLM Systems Fail?", 2025
- [QLM] Patke et al., "Queue Management for SLO-Oriented LLM Serving", SoCC 2024
- [Continuum] Li et al., "Efficient Multi-Turn LLM Agent Scheduling with KV Cache TTL", 2024
- [LLM-Inference-Bench] Argonne National Lab, 2024
- [Etalon] "Holistic Performance Evaluation Framework for LLM Inference Systems", 2024
- [Sarathi-Serve] "Efficient LLM Serving with Chunked Prefills", 2023
- [ORCA] Yu et al., "ORCA: A Distributed Serving System for Transformer-Based Models", OSDI 2022

### Datasets
- ShareGPT: https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered
- MAST/MAD: https://huggingface.co/datasets/mcemri/MAD
- LMSYS-Chat-1M: https://huggingface.co/datasets/lmsys/lmsys-chat-1m

### Code Repositories
- QLM: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/QLM/`
- MAST: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/MAST/`
- Continuum: https://github.com/Hanchenli/vllm-continuum
- LLM-Inference-Bench: https://github.com/argonne-lcf/LLM-Inference-Bench

---

**Document Version**: 1.0  
**Last Updated**: March 30, 2026  
**Author**: Neil Teje  
**Supervisor**: Prof. Ragini Gupta
