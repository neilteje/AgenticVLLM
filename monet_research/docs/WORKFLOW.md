# Research Workflow Visualization

**Visual guide to the complete research workflow**

---

## 🗺️ Overall Project Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROJECT START                                │
│                                                                   │
│  Read: PROJECT_SUMMARY.md → EXPERIMENT_PLAN.md → QUICKSTART.md  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: SETUP                                │
│                   (Day 1, ~2-3 hours)                            │
│                                                                   │
│  1. Run: ./scripts/validate_setup.sh                            │
│  2. Download ShareGPT dataset                                    │
│  3. Test basic functionality                                     │
│  4. Verify GPU access                                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 1: SHAREGPT EXPERIMENTS                       │
│                  (Days 2-5, ~12-15 hours)                        │
│                                                                   │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │  vLLM Baseline   │      │   QLM Baseline   │                │
│  │   (E1.1, E1.3,   │      │   (E1.2, E1.4,   │                │
│  │    E1.5, E1.7,   │      │    E1.6, E1.8,   │                │
│  │    E1.9, E1.11)  │      │   E1.10, E1.12)  │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                            │
│           └────────┬────────────────┘                            │
│                    │                                             │
│                    ▼                                             │
│          12 JSON result files                                    │
│      (saved to results/phase1/)                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 1: ANALYSIS & REPORT                          │
│                  (Days 6-7, ~4-6 hours)                          │
│                                                                   │
│  1. Run: jupyter notebook phase1_sharegpt.ipynb                 │
│     ├─ Load 12 experiment results                               │
│     ├─ Generate 5 plots                                          │
│     ├─ Create summary table                                      │
│     └─ Calculate improvements                                    │
│                                                                   │
│  2. Write Overleaf report:                                       │
│     ├─ Methodology section                                       │
│     ├─ Results section (insert 5 plots)                         │
│     └─ Discussion section                                        │
│                                                                   │
│  3. Email supervisor with findings                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 2: AGENTIC TRACE EXPERIMENTS                     │
│                  (Weeks 3-6, ~4 weeks)                           │
│                                                                   │
│  Week 3: MAST Trace Preprocessing                               │
│    ├─ Download MAST dataset                                      │
│    ├─ Parse trace structure                                      │
│    ├─ Tokenize with tiktoken                                     │
│    └─ Generate trace statistics                                  │
│                                                                   │
│  Week 4: Trace Replay Infrastructure                            │
│    ├─ Implement trace executor                                   │
│    ├─ Add multi-step support to QLM                             │
│    └─ Test trace replay                                          │
│                                                                   │
│  Week 5: Trace-Aware Scheduling                                 │
│    ├─ Heuristic 1: Step Priority                                │
│    ├─ Heuristic 2: Semantic Batching                            │
│    └─ Heuristic 3: Context-Aware                                │
│                                                                   │
│  Week 6: Experiments & Analysis                                 │
│    ├─ Run E2.1-E2.7 (7 experiments)                             │
│    ├─ Generate 3-4 plots                                         │
│    └─ Update report                                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│         PHASE 3: CONTINUUM COMPARISON (Optional)                 │
│                  (Week 7+, ~1 week)                              │
│                                                                   │
│  1. Install Continuum                                            │
│  2. Adapt MAST traces                                            │
│  3. Run Continuum experiments                                    │
│  4. Compare: vLLM vs QLM vs Continuum                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FINAL REPORT & SUBMISSION                       │
│                                                                   │
│  1. Complete all report sections                                 │
│  2. Finalize 6-7 figures                                         │
│  3. Write abstract and conclusion                                │
│  4. Proofread and polish                                         │
│  5. Submit to Overleaf                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Daily Workflow (Phase 1)

```
Morning:
  ├─ Check PROGRESS.md for today's tasks
  ├─ Review CHEATSHEET.md for commands
  └─ Start vLLM server (if needed)

During Experiments:
  ├─ Run experiments (manual or automated)
  ├─ Monitor progress (check JSON files)
  └─ Take notes in PROGRESS.md

Evening:
  ├─ Verify results (check metrics)
  ├─ Update PROGRESS.md with completed tasks
  └─ Plan tomorrow's tasks
```

---

## 📊 Experiment Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGLE EXPERIMENT                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Start vLLM Server                                            │
│     $ vllm serve unsloth/Llama-3.2-1B-Instruct --port 8000      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Configure Experiment Parameters                              │
│     ├─ Dataset: sharegpt                                         │
│     ├─ Duration: 60 seconds                                      │
│     ├─ Arrival rate: 2 rps                                       │
│     ├─ Users: 1                                                  │
│     └─ Prompt length: mixed                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Run Workload Driver                                          │
│     $ python benchmarks/workload_driver.py \                    │
│         --dataset sharegpt \                                     │
│         --duration 60 \                                          │
│         --arrival-rate 2 \                                       │
│         --output results/phase1/experiment.json                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Experiment Execution (60 seconds)                            │
│     ├─ Load prompts from ShareGPT                               │
│     ├─ Send requests to vLLM at specified rate                  │
│     ├─ Collect metrics (latency, queue length, etc.)            │
│     └─ Save results to JSON                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Verify Results                                               │
│     ├─ Check JSON file exists                                    │
│     ├─ Verify metrics are reasonable                             │
│     └─ Update PROGRESS.md                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 Analysis Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              AFTER ALL EXPERIMENTS COMPLETE                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Open Jupyter Notebook                                        │
│     $ cd analysis                                                │
│     $ jupyter notebook phase1_sharegpt.ipynb                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Load Experiment Results                                      │
│     ├─ Read 12 JSON files from results/phase1/                  │
│     ├─ Extract metrics (latency, throughput, queue length)      │
│     └─ Create summary dataframe                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Generate Plots (5 total)                                     │
│     ├─ Plot 1: Scheduling Delay CDF                             │
│     ├─ Plot 2: Queue Length Over Time                           │
│     ├─ Plot 3: Throughput vs Load                               │
│     ├─ Plot 4: Prompt Length Sensitivity                        │
│     └─ Plot 5: Queue Dynamics Summary                           │
│                                                                   │
│     Saved to: analysis/plots/*.png                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Calculate Statistics                                         │
│     ├─ Mean, median, p95, p99 for all metrics                   │
│     ├─ Improvement percentages (vLLM vs QLM)                    │
│     └─ Export summary table (CSV + LaTeX)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Write Report Sections                                        │
│     ├─ Upload plots to Overleaf                                  │
│     ├─ Insert LaTeX table                                        │
│     ├─ Write methodology section                                 │
│     ├─ Write results section                                     │
│     └─ Write discussion section                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔀 Decision Tree: Which File to Use?

```
START: What do you need?
    │
    ├─ Overview of the project?
    │   └─> Read PROJECT_SUMMARY.md (5 min)
    │
    ├─ Detailed experiment plan?
    │   └─> Read EXPERIMENT_PLAN.md (30 min)
    │
    ├─ Setup instructions?
    │   └─> Read QUICKSTART.md (30 min)
    │
    ├─ Verify setup is correct?
    │   └─> Run ./scripts/validate_setup.sh
    │
    ├─ Run experiments?
    │   ├─ Automated (all 12 experiments)
    │   │   └─> Run ./scripts/phase1_runner.sh
    │   └─ Manual (single experiment)
    │       └─> Check CHEATSHEET.md for command
    │
    ├─ Analyze results?
    │   └─> Run analysis/phase1_sharegpt.ipynb
    │
    ├─ Track progress?
    │   └─> Update PROGRESS.md
    │
    ├─ Quick command reference?
    │   └─> Check CHEATSHEET.md
    │
    ├─ Troubleshooting?
    │   └─> Check QUICKSTART.md or CHEATSHEET.md
    │
    └─ Share with others?
        └─> Share README.md
```

---

## 📅 Weekly Workflow

```
WEEK 1: Setup & vLLM Experiments
┌─────────────────────────────────────────────────────────────────┐
│ Monday:    Setup, validate, download dataset                    │
│ Tuesday:   Run E1.1, E1.3, E1.5 (vLLM experiments)             │
│ Wednesday: Run E1.7, E1.9, E1.11 (vLLM experiments)            │
│ Thursday:  Verify results, preliminary analysis                 │
│ Friday:    Update PROGRESS.md, email supervisor                 │
└─────────────────────────────────────────────────────────────────┘

WEEK 2: QLM Experiments & Analysis
┌─────────────────────────────────────────────────────────────────┐
│ Monday:    Run E1.2, E1.4, E1.6 (QLM experiments)              │
│ Tuesday:   Run E1.8, E1.10, E1.12 (QLM experiments)            │
│ Wednesday: Run analysis notebook, generate plots                │
│ Thursday:  Write methodology + results sections                 │
│ Friday:    Polish report, email supervisor with findings        │
└─────────────────────────────────────────────────────────────────┘

WEEK 3-6: Phase 2 (Agentic Traces)
┌─────────────────────────────────────────────────────────────────┐
│ Week 3: MAST preprocessing & characterization                   │
│ Week 4: Trace replay infrastructure                             │
│ Week 5: Trace-aware scheduling heuristics                       │
│ Week 6: Experiments, analysis, report writing                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Milestone Checklist

```
PHASE 1 MILESTONES:
├─ [✓] Setup validated (validate_setup.sh passes)
├─ [✓] ShareGPT dataset downloaded
├─ [ ] 6 vLLM experiments complete (E1.1, E1.3, E1.5, E1.7, E1.9, E1.11)
├─ [ ] 6 QLM experiments complete (E1.2, E1.4, E1.6, E1.8, E1.10, E1.12)
├─ [ ] Analysis notebook run (5 plots generated)
├─ [ ] Methodology section written
├─ [ ] Results section written (with plots)
├─ [ ] Discussion section written
└─ [ ] Supervisor notified of Phase 1 completion

PHASE 2 MILESTONES:
├─ [ ] MAST dataset downloaded
├─ [ ] Trace preprocessing complete
├─ [ ] Trace characterization (2-3 graphs)
├─ [ ] Trace replay infrastructure working
├─ [ ] 3 scheduling heuristics implemented
├─ [ ] 7 agentic experiments complete (E2.1-E2.7)
├─ [ ] Analysis complete (3-4 graphs)
└─ [ ] Report updated with Phase 2 findings

FINAL REPORT MILESTONES:
├─ [ ] All sections complete (10-15 pages)
├─ [ ] 6-7 high-quality figures
├─ [ ] Abstract written
├─ [ ] Conclusion written
├─ [ ] Proofread and polished
└─ [ ] Submitted to Overleaf
```

---

## 🚨 Critical Path

**The fastest path to completing Phase 1:**

```
Day 1 (3 hours):
  ./scripts/validate_setup.sh
  Download ShareGPT
  Test basic functionality
  ↓
Days 2-3 (8 hours):
  Run all 6 vLLM experiments
  ↓
Days 4-5 (8 hours):
  Run all 6 QLM experiments
  ↓
Day 6 (4 hours):
  Run analysis notebook
  Generate 5 plots
  ↓
Day 7 (4 hours):
  Write methodology + results
  Email supervisor
  ↓
PHASE 1 COMPLETE! (27 hours total)
```

---

## 💡 Pro Tips

### For Experiments
- Run experiments overnight (12-15 hours unattended)
- Use `screen` or `tmux` to keep vLLM server running
- Check results periodically (verify JSON files)
- Keep PROGRESS.md updated

### For Analysis
- Run analysis notebook incrementally (cell by cell)
- Save plots as you generate them
- Export summary table early
- Take screenshots of interesting findings

### For Report
- Write methodology while experiments run
- Insert plots as soon as they're generated
- Update Overleaf daily (don't wait until the end)
- Ask supervisor for feedback early

---

## 📞 When to Contact Supervisor

```
URGENT (Email immediately):
├─ Experiments failing consistently
├─ GPU access issues on Delta
├─ Missing critical resources (Gurobi license)
└─ Major blockers preventing progress

WEEKLY (Email every Friday):
├─ Progress update (completed tasks)
├─ Results summary (key findings)
├─ Next week's plan
└─ Questions/clarifications needed

MILESTONE (Email after major milestones):
├─ Phase 1 complete (with plots)
├─ Phase 2 complete (with plots)
└─ Final report draft ready
```

---

**Last Updated**: March 30, 2026  
**Version**: 1.0
