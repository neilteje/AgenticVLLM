# Research Progress Tracker

**Project**: Efficient Execution of Agentic Traces Using vLLM  
**Student**: Neil Teje  
**Supervisor**: Prof. Ragini Gupta  
**Start Date**: March 30, 2026

---

## Current Status: Phase 1 - ShareGPT Baseline Experiments

**Target Completion**: Week of April 7-14, 2026 (1-2 weeks)

---

## Phase 1: ShareGPT Baseline (URGENT)

### Week 1: Setup & vLLM Experiments

#### Day 1-2: Setup (Target: April 1-2)
- [ ] Verify QLM installation and dependencies
- [ ] Download ShareGPT dataset to `QLM/data/`
- [ ] Test basic vLLM endpoint with `basic_test.py`
- [ ] Test workload driver with small sample (10s, 50 samples)
- [ ] Verify metrics JSON format and collection
- [ ] Set up results directory structure

**Blockers**: _None yet_

**Notes**: 
- Gurobi license status: _TBD (ask supervisor)_
- GPU access on Delta: _TBD (need to set up)_

---

#### Day 3-4: vLLM Baseline Experiments (Target: April 3-4)
- [ ] Start vLLM server on GPU node
- [ ] Run E1.1: vLLM Baseline (2 rps, mixed prompts)
- [ ] Run E1.3: vLLM High Rate (5 rps)
- [ ] Run E1.5: vLLM Bursty (5 req/2s)
- [ ] Run E1.7: vLLM Multi-User (8 users)
- [ ] Run E1.9: vLLM Short Prompts
- [ ] Run E1.11: vLLM Long Prompts
- [ ] Verify all 6 JSON files created successfully
- [ ] Create preliminary analysis notebook

**Results**:
- E1.1: _Pending_
- E1.3: _Pending_
- E1.5: _Pending_
- E1.7: _Pending_
- E1.9: _Pending_
- E1.11: _Pending_

**Issues**: _None yet_

---

### Week 2: QLM Experiments & Analysis

#### Day 5-6: QLM Experiments (Target: April 5-6)
- [ ] Configure QLM with SLO settings in `qlm/config.yaml`
- [ ] Run E1.2: QLM Baseline (2 rps, mixed prompts)
- [ ] Run E1.4: QLM High Rate (5 rps)
- [ ] Run E1.6: QLM Bursty (5 req/2s)
- [ ] Run E1.8: QLM Multi-User (8 users)
- [ ] Run E1.10: QLM Short Prompts
- [ ] Run E1.12: QLM Long Prompts
- [ ] Verify all 6 JSON files created successfully

**Results**:
- E1.2: _Pending_
- E1.4: _Pending_
- E1.6: _Pending_
- E1.8: _Pending_
- E1.10: _Pending_
- E1.12: _Pending_

**Issues**: _None yet_

---

#### Day 7: Analysis & Visualization (Target: April 7)
- [ ] Run analysis notebook `phase1_sharegpt.ipynb`
- [ ] Generate all 5 plots:
  - [ ] Plot 1: Scheduling Delay CDF (vLLM vs QLM)
  - [ ] Plot 2: Queue Length Over Time
  - [ ] Plot 3: Throughput vs Load
  - [ ] Plot 4: Prompt Length Sensitivity
  - [ ] Plot 5: Queue Dynamics Summary
- [ ] Create summary statistics table
- [ ] Export LaTeX table for Overleaf
- [ ] Calculate key improvement percentages

**Key Findings** (to be filled after analysis):
- QLM scheduling delay improvement: _TBD_
- QLM queue length reduction: _TBD_
- Throughput comparison: _TBD_
- Prompt length sensitivity: _TBD_

---

#### Day 8-9: Report Writing (Target: April 8-9)
- [ ] Write Methodology section in Overleaf:
  - [ ] Experimental setup description
  - [ ] Workload parameters table
  - [ ] Metrics definitions
  - [ ] Systems under test (vLLM vs QLM)
- [ ] Write Results section:
  - [ ] Insert 5 plots
  - [ ] Insert summary table
  - [ ] Describe key findings
  - [ ] Statistical analysis (mean, p50, p95, p99)
- [ ] Draft Discussion section:
  - [ ] QLM's SLO-aware scheduling benefits
  - [ ] Workload sensitivity insights
  - [ ] Limitations of Phase 1
- [ ] Email supervisor with progress update

**Overleaf Sections Completed**:
- [ ] Abstract (draft)
- [ ] Introduction
- [ ] Background
- [ ] Methodology (Phase 1)
- [ ] Results (Phase 1)
- [ ] Discussion (partial)

---

## Phase 2: Agentic Trace Experiments

**Target Start**: Week of April 14, 2026  
**Target Completion**: Week of May 5, 2026 (3-4 weeks)

### Week 3: MAST Trace Preprocessing
- [ ] Download MAST dataset from HuggingFace (`mcemri/MAD`)
- [ ] Analyze trace structure and format
- [ ] Parse traces to extract LLM calls, tool calls, dependencies
- [ ] Tokenize traces using tiktoken
- [ ] Generate trace statistics:
  - [ ] Distribution of trace lengths
  - [ ] Prompt/output length distributions
  - [ ] Tool call frequency analysis
  - [ ] Context accumulation patterns
- [ ] Create trace dataset loader (`qlm/workload/mast_traces.py`)
- [ ] Write trace characterization section for report

**Deliverable**: MAST trace analysis (2-3 graphs)

---

### Week 4: Trace Replay Infrastructure
- [ ] Implement trace executor that respects dependencies
- [ ] Add multi-step trace support to QLM queue
- [ ] Implement trace-level metrics collection
- [ ] Add trace ID tracking for correlation
- [ ] Test trace replay with small sample
- [ ] Validate trace execution correctness

**Deliverable**: Trace replay system ready for experiments

---

### Week 5: Trace-Aware Scheduling
- [ ] Implement Heuristic 1: Step Priority Scheduling
  - [ ] Critical path analysis
  - [ ] Step type classification (tool call vs reasoning)
  - [ ] Priority assignment algorithm
- [ ] Implement Heuristic 2: Semantic Batching
  - [ ] Token-based similarity computation
  - [ ] Batching decision algorithm
  - [ ] Batch execution logic
- [ ] Implement Heuristic 3: Context-Aware Scheduling
  - [ ] KV cache warmth tracking
  - [ ] Context-aware prioritization
  - [ ] Memory pressure handling
- [ ] Integrate heuristics into QLM scheduler

**Deliverable**: 3 trace-aware scheduling heuristics

---

### Week 6: Agentic Trace Experiments & Analysis
- [ ] Run experiments E2.1-E2.7 (see EXPERIMENT_PLAN.md)
- [ ] Collect and validate metrics
- [ ] Analyze scheduling decisions
- [ ] Compare against ShareGPT baseline
- [ ] Generate 3-4 plots for report
- [ ] Write agentic workload characterization section
- [ ] Write trace-aware scheduling design section
- [ ] Update results section with Phase 2 findings

**Deliverable**: Phase 2 experimental results (3-4 graphs)

---

## Phase 3: Continuum Comparison (Stretch Goal)

**Target**: Week of May 12, 2026 (if time permits)

- [ ] Install Continuum from GitHub
- [ ] Adapt MAST traces to Continuum format
- [ ] Run Continuum experiments
- [ ] Compare QLM vs Continuum
- [ ] Analyze KV cache TTL effectiveness
- [ ] Add comparison section to report (1-2 graphs)

**Deliverable**: Three-way comparison (vLLM vs QLM vs Continuum)

---

## Report Progress

### Overleaf Link
https://www.overleaf.com/7334415764npgkvkfrzfvj#ef3e65

### Sections Status

| Section | Status | Target Date | Actual Date | Notes |
|---------|--------|-------------|-------------|-------|
| Abstract | Not Started | May 15 | - | Write last |
| Introduction | Not Started | April 10 | - | Motivation, problem, contribution |
| Background | Not Started | April 10 | - | vLLM, QLM, MAST |
| Methodology (Phase 1) | Not Started | April 9 | - | ShareGPT experiments |
| Results (Phase 1) | Not Started | April 9 | - | 4-5 graphs |
| Methodology (Phase 2) | Not Started | May 5 | - | Agentic traces |
| Results (Phase 2) | Not Started | May 5 | - | 3-4 graphs |
| Discussion | Not Started | May 10 | - | Key findings, limitations |
| Related Work | Not Started | May 10 | - | Sarathi, ORCA, etc. |
| Conclusion | Not Started | May 15 | - | Summary, future work |

### Figures Status

| Figure | Description | Status | File | Notes |
|--------|-------------|--------|------|-------|
| 1 | Scheduling Delay CDF | Not Started | `plot1_scheduling_delay_baseline.png` | vLLM vs QLM |
| 2 | Queue Length Over Time | Not Started | `plot2_queue_length_over_time.png` | 4 subplots |
| 3 | Throughput vs Load | Not Started | `plot3_throughput_vs_load.png` | Bar chart |
| 4 | Prompt Length Sensitivity | Not Started | `plot4_prompt_length_sensitivity.png` | 2 subplots |
| 5 | Queue Dynamics Summary | Not Started | `plot5_queue_dynamics_summary.png` | Mean/max queue |
| 6 | Trace Completion Time | Not Started | TBD | Phase 2 |
| 7 | Batching Effectiveness | Not Started | TBD | Phase 2 |
| 8 | Workload Comparison | Not Started | TBD | Phase 2 |

**Target**: 6-7 high-quality figures total

---

## Meetings & Communication

### Meeting Log

| Date | Type | Attendees | Topics | Action Items |
|------|------|-----------|--------|--------------|
| Jan 15, 2026 | Kickoff | Ragini, Neil | Project overview, paper presentations | Read MAST & QLM papers |
| TBD | Progress Update | Ragini, Neil | Phase 1 results | Present ShareGPT findings |
| TBD | Checkpoint | Ragini, Neil | Phase 2 design | Discuss trace-aware scheduling |

### Email Updates

| Date | Subject | Summary | Response |
|------|---------|---------|----------|
| March 30, 2026 | Phase 1 Urgency | Need to finish ShareGPT experiments in 1-2 weeks | Acknowledged |
| TBD | Phase 1 Complete | Results summary, plots, next steps | TBD |
| TBD | Phase 2 Progress | MAST trace analysis, scheduling design | TBD |

---

## Questions for Supervisor

### Urgent (Ask ASAP)
1. **Gurobi License**: Can you share the Gurobi license for QLM's LP scheduler?
2. **Delta Cluster**: How do I submit GPU jobs on Delta? Any specific queue/partition?
3. **Timeline**: Is 1-2 weeks for Phase 1 realistic, or should I prioritize speed over thoroughness?

### Medium Priority
4. **MAST Traces**: What is the exact structure of MAST traces? Any preprocessing needed?
5. **Semantic Similarity**: Should I use tiktoken embeddings or a different approach for batching?
6. **Continuum**: Is Continuum comparison essential or can it be a stretch goal?

### Low Priority
7. **Report Length**: What's the target page count for the final report?
8. **Code Release**: Should I prepare a GitHub repo for public release?

---

## Resources & Links

### Papers
- [MAST] https://arxiv.org/pdf/2503.13657
- [QLM] https://dl.acm.org/doi/10.1145/3698038.3698523
- [Continuum] https://arxiv.org/abs/2511.02230
- [LLM-Inference-Bench] https://arxiv.org/abs/2411.00136
- [Etalon] https://arxiv.org/abs/2507.09019

### Datasets
- ShareGPT: https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered
- MAST/MAD: https://huggingface.co/datasets/mcemri/MAD

### Code
- QLM: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/QLM/`
- MAST: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/MAST/`
- Continuum: https://github.com/Hanchenli/vllm-continuum

### Documentation
- Experiment Plan: `EXPERIMENT_PLAN.md`
- Quick Start: `QUICKSTART.md`
- This File: `PROGRESS.md`

---

## Notes & Observations

### March 30, 2026
- Created comprehensive experiment plan
- Set up directory structure
- Ready to start Phase 1 experiments
- Need to verify GPU access on Delta

### _Add notes as you go..._

---

## Success Metrics

### Phase 1 Success Criteria
- ✅ All 12 experiments completed with valid metrics
- ✅ 5 comparison graphs generated
- ✅ Methodology + Results sections drafted
- ✅ Clear understanding of QLM benefits on conversational workloads

### Phase 2 Success Criteria
- ✅ MAST traces preprocessed and characterized
- ✅ 3 trace-aware scheduling heuristics implemented
- ✅ 7 agentic trace experiments completed
- ✅ 3-4 additional graphs in report
- ✅ Clear findings on agentic vs conversational workloads

### Final Report Success Criteria
- ✅ 6-7 high-quality figures
- ✅ 10-15 page technical report
- ✅ Reproducible codebase
- ✅ Clear contributions and findings
- ✅ Submitted to Overleaf by deadline

---

**Last Updated**: March 30, 2026  
**Next Update**: _After Phase 1 setup complete_
