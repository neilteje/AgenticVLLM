# Project Summary: Efficient Execution of Agentic Traces Using vLLM

**One-page overview of the entire research project**

---

## 🎯 Core Research Question

**How can we optimize LLM serving engines for agentic workloads (multi-step, tool-calling traces) vs traditional conversational workloads?**

---

## 🔬 Research Approach

```
Phase 1: ShareGPT Baseline (1-2 weeks)
    ↓
    Establish baseline: vLLM vs QLM on conversational workloads
    Deliverable: 5 graphs, methodology + results sections
    
Phase 2: Agentic Traces (3-4 weeks)
    ↓
    Characterize MAST traces, implement trace-aware scheduling
    Deliverable: 3-4 graphs, system design + results sections
    
Phase 3: Continuum Comparison (optional)
    ↓
    Compare against state-of-the-art multi-turn scheduler
    Deliverable: 1-2 graphs, comparison section
```

---

## 📊 Experiment Matrix

### Phase 1: ShareGPT (12 experiments)

| Comparison | vLLM | QLM | Variable |
|------------|------|-----|----------|
| Baseline | E1.1 | E1.2 | 2 rps, mixed prompts |
| High Load | E1.3 | E1.4 | 5 rps |
| Bursty | E1.5 | E1.6 | 5 req/2s bursts |
| Multi-User | E1.7 | E1.8 | 8 concurrent users |
| Short Prompts | E1.9 | E1.10 | ≤200 chars |
| Long Prompts | E1.11 | E1.12 | >1000 chars |

**Goal**: Understand QLM's SLO-aware scheduling benefits on conversational workloads

### Phase 2: Agentic Traces (7 experiments)

| Exp | System | Scheduling Strategy | Load |
|-----|--------|---------------------|------|
| E2.1 | vLLM | FCFS (baseline) | 1 tps |
| E2.2 | QLM | SLO-aware | 1 tps |
| E2.3 | QLM | Step Priority | 1 tps |
| E2.4 | QLM | Semantic Batching | 1 tps |
| E2.5 | QLM | Context-Aware | 1 tps |
| E2.6 | vLLM | FCFS | 5 tps (high load) |
| E2.7 | QLM | Best Heuristic | 5 tps (high load) |

**Goal**: Identify which trace-aware scheduling strategies work best

---

## 📈 Key Metrics

### Latency (Lower is Better)
- **TTFT**: Time to First Token
- **TPOT**: Time per Output Token
- **E2E**: End-to-End Latency
- **Scheduling Delay**: Queue waiting time

### Throughput (Higher is Better)
- **RPS**: Requests per Second
- **TPS**: Tokens per Second

### SLO (Higher is Better)
- **SLO Attainment**: % requests meeting SLO

### Resources
- **GPU Utilization**: % GPU usage
- **Queue Length**: Requests waiting

### Trace-Specific (Phase 2)
- **Trace Completion Time**: Multi-step trace duration
- **Batching Efficiency**: Latency reduction from batching

---

## 🎨 Report Structure (6-7 Figures)

### Phase 1 Figures (5 graphs)
1. **Scheduling Delay CDF**: vLLM vs QLM baseline
2. **Queue Length Over Time**: 4 scenarios (baseline, high rate, bursty, multi-user)
3. **Throughput vs Load**: Bar chart comparison
4. **Prompt Length Sensitivity**: Short vs long prompts
5. **Queue Dynamics Summary**: Mean/max queue length

### Phase 2 Figures (3-4 graphs)
6. **Trace Completion Time**: Agentic traces, multiple schedulers
7. **Batching Effectiveness**: Semantic similarity batching
8. **Workload Comparison**: ShareGPT vs MAST characteristics

### Phase 3 Figures (optional, 1-2 graphs)
9. **Three-Way Comparison**: vLLM vs QLM vs Continuum

---

## 🚀 Quick Start Workflow

### Day 1: Setup (2-3 hours)
```bash
./scripts/validate_setup.sh
# Download ShareGPT dataset
# Test basic functionality
```

### Days 2-3: vLLM Experiments (6-8 hours)
```bash
# Start vLLM server
vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000

# Run E1.1, E1.3, E1.5, E1.7, E1.9, E1.11
```

### Days 4-5: QLM Experiments (6-8 hours)
```bash
# Run E1.2, E1.4, E1.6, E1.8, E1.10, E1.12
```

### Days 6-7: Analysis & Report (4-6 hours)
```bash
# Generate plots in Jupyter
jupyter notebook analysis/phase1_sharegpt.ipynb

# Write methodology + results in Overleaf
```

---

## 🎯 Expected Contributions

### 1. Workload Characterization
- **Finding**: Agentic traces have different patterns than conversational workloads
- **Evidence**: Distribution of trace lengths, tool calls, context growth
- **Impact**: Informs scheduler design for agentic systems

### 2. Trace-Aware Scheduling
- **Finding**: Semantic batching reduces latency by X%
- **Evidence**: Experiments E2.3-E2.5 show scheduling heuristics effectiveness
- **Impact**: Practical scheduling strategies for agentic workloads

### 3. Benchmark Suite
- **Finding**: Reproducible benchmarking framework for LLM serving
- **Evidence**: 19 experiments across 2 workload types
- **Impact**: Community can use for future research

### 4. Performance Analysis
- **Finding**: QLM reduces scheduling delay by X% on conversational workloads
- **Evidence**: Phase 1 experiments (E1.1-E1.12)
- **Impact**: Validates SLO-aware scheduling approach

---

## 📦 Deliverables

### Code
- ✅ QLM with trace support
- ✅ Trace-aware scheduling heuristics (3 strategies)
- ✅ Benchmarking scripts (workload driver, analysis notebooks)
- ✅ MAST trace preprocessing pipeline

### Data
- ✅ 12 Phase 1 experiment results (JSON)
- ✅ 7 Phase 2 experiment results (JSON)
- ✅ MAST trace characterization dataset

### Documentation
- ✅ Comprehensive experiment plan
- ✅ Reproducible setup guide
- ✅ Analysis notebooks with plots

### Report
- ✅ 10-15 page technical report
- ✅ 6-7 high-quality figures
- ✅ Methodology, results, discussion sections
- ✅ Published on Overleaf

---

## 🔑 Key Insights (To Be Filled)

### Phase 1: ShareGPT Baseline
- QLM reduces scheduling delay by **X%** (E1.1 vs E1.2)
- QLM handles bursty traffic **X%** better (E1.5 vs E1.6)
- Prompt length affects scheduling by **X** (E1.9-E1.12)

### Phase 2: Agentic Traces
- Agentic traces are **X%** longer than conversational (MAST vs ShareGPT)
- Semantic batching reduces latency by **X%** (E2.4)
- Context-aware scheduling improves KV cache utilization by **X%** (E2.5)

### Phase 3: Continuum Comparison (Optional)
- QLM vs Continuum: **X%** difference in trace completion time
- KV cache TTL effectiveness: **X%** improvement

---

## 📅 Timeline

| Week | Phase | Tasks | Deliverables |
|------|-------|-------|--------------|
| 1-2 | Phase 1 | ShareGPT experiments | 5 graphs, methodology + results |
| 3 | Phase 2 | MAST preprocessing | Trace characterization (2-3 graphs) |
| 4 | Phase 2 | Trace replay infrastructure | Working trace executor |
| 5 | Phase 2 | Trace-aware scheduling | 3 scheduling heuristics |
| 6 | Phase 2 | Agentic experiments | 3-4 graphs, results section |
| 7+ | Phase 3 | Continuum comparison (optional) | 1-2 graphs |
| Final | Report | Writing & polishing | Complete 10-15 page report |

---

## 🎓 Learning Outcomes

### Technical Skills
- LLM serving infrastructure (vLLM, QLM)
- Workload characterization and benchmarking
- Scheduler design and optimization
- Experimental methodology

### Research Skills
- Literature review (MAST, QLM, Continuum, etc.)
- Hypothesis formulation and testing
- Data analysis and visualization
- Technical writing and presentation

### Domain Knowledge
- Agentic LLM systems
- Multi-step reasoning and tool calling
- SLO-aware scheduling
- KV cache management

---

## 📚 Key References

### Systems
- **vLLM**: Efficient LLM inference with paged attention
- **QLM**: SLO-aware queue management for LLM serving
- **Continuum**: Multi-turn agent scheduling with KV cache TTL

### Workloads
- **ShareGPT**: Conversational dataset (single-turn request-response)
- **MAST**: Multi-agent traces (multi-step, tool-calling)

### Benchmarking
- **LLM-Inference-Bench**: Comprehensive benchmarking framework
- **Etalon**: Holistic performance evaluation
- **Sarathi-Serve**: Chunked prefills for efficient serving

---

## 🏆 Success Criteria

### Minimum Viable Project (Must Have)
- ✅ Phase 1 complete (12 experiments, 5 graphs)
- ✅ Methodology + Results sections written
- ✅ Clear findings on vLLM vs QLM

### Target Project (Should Have)
- ✅ Phase 2 complete (7 experiments, 3-4 graphs)
- ✅ Trace-aware scheduling implemented
- ✅ Agentic workload characterization
- ✅ Complete technical report (10-15 pages)

### Stretch Goals (Nice to Have)
- ✅ Phase 3 Continuum comparison
- ✅ Public GitHub release
- ✅ Conference/workshop submission

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| Experiment Plan | `EXPERIMENT_PLAN.md` |
| Quick Start | `QUICKSTART.md` |
| Progress Tracker | `PROGRESS.md` |
| Cheat Sheet | `CHEATSHEET.md` |
| Overleaf Report | https://www.overleaf.com/7334415764npgkvkfrzfvj |
| MAST Dataset | https://huggingface.co/datasets/mcemri/MAD |
| ShareGPT Dataset | https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered |

---

## 💡 Next Actions

### Immediate (This Week)
1. Run `./scripts/validate_setup.sh` to verify setup
2. Start Phase 1 experiments with `./scripts/phase1_runner.sh`
3. Update `PROGRESS.md` daily with completed tasks

### Short-Term (Next 2 Weeks)
1. Complete all 12 Phase 1 experiments
2. Generate 5 comparison plots
3. Write methodology + results sections in Overleaf
4. Email supervisor with Phase 1 findings

### Long-Term (Next 4-6 Weeks)
1. Download and preprocess MAST traces
2. Implement trace-aware scheduling heuristics
3. Run Phase 2 experiments
4. Complete final report

---

**Status**: Ready to start Phase 1 experiments  
**Last Updated**: March 30, 2026  
**Version**: 1.0
