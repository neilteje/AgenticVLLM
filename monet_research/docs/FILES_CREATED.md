# Files Created for Your Research Project

This document lists all the files I've created to help you with your research project.

---

## 📋 Planning & Documentation Files

### 1. **EXPERIMENT_PLAN.md** (MOST IMPORTANT!)
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/EXPERIMENT_PLAN.md`

**Purpose**: Comprehensive experiment plan covering all 3 phases

**Contents**:
- Executive summary of the project
- Phase 1: ShareGPT baseline (12 experiments)
- Phase 2: Agentic traces (7 experiments)
- Phase 3: Continuum comparison (stretch goal)
- Detailed experiment matrix with parameters
- Metrics definitions
- Timeline and deliverables
- Report structure

**When to use**: Read this FIRST! It's your complete roadmap.

---

### 2. **QUICKSTART.md**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/QUICKSTART.md`

**Purpose**: Step-by-step guide to get started with Phase 1 experiments

**Contents**:
- Setup instructions (30 minutes)
- How to run experiments (manual and automated)
- Analysis workflow
- Troubleshooting guide
- Timeline estimates

**When to use**: When you're ready to start running experiments.

---

### 3. **PROGRESS.md**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/PROGRESS.md`

**Purpose**: Track your daily/weekly progress

**Contents**:
- Task checklists for each phase
- Meeting logs
- Email update templates
- Questions for supervisor
- Results tracking
- Report progress tracker

**When to use**: Update this daily as you complete tasks.

---

### 4. **README.md**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/README.md`

**Purpose**: Project overview and repository documentation

**Contents**:
- Project overview
- Repository structure
- Quick start guide
- Experiment overview
- Key metrics
- Report structure
- Troubleshooting

**When to use**: Share with others or when you need a high-level overview.

---

### 5. **CHEATSHEET.md**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/CHEATSHEET.md`

**Purpose**: Quick reference for common commands

**Contents**:
- Common commands (vLLM, QLM, experiments)
- Experiment parameters reference
- Troubleshooting quick fixes
- Metrics reference table
- Time estimates

**When to use**: When you need to quickly look up a command or parameter.

---

### 6. **PROJECT_SUMMARY.md**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/PROJECT_SUMMARY.md`

**Purpose**: One-page visual summary of the entire project

**Contents**:
- Research question
- Experiment matrix
- Key metrics
- Expected contributions
- Timeline
- Success criteria

**When to use**: When you need to explain the project to someone or remind yourself of the big picture.

---

## 🔧 Scripts

### 7. **validate_setup.sh**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/scripts/validate_setup.sh`

**Purpose**: Validate that your environment is ready for experiments

**What it checks**:
- QLM installation
- Required Python packages
- ShareGPT dataset
- vLLM installation
- GPU availability
- Directory structure
- vLLM server status

**How to run**:
```bash
./scripts/validate_setup.sh
```

**When to use**: Run this FIRST before starting any experiments!

---

### 8. **phase1_runner.sh**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/scripts/phase1_runner.sh`

**Purpose**: Automated runner for all 12 Phase 1 experiments

**What it does**:
- Runs all 12 ShareGPT experiments (E1.1-E1.12)
- Saves results to `results/phase1/`
- Provides progress updates

**How to run**:
```bash
cd QLM
../scripts/phase1_runner.sh
```

**When to use**: After validating setup, run this to execute all Phase 1 experiments.

---

## 📊 Analysis Files

### 9. **phase1_sharegpt.ipynb**
**Location**: `/Users/neilteje/Desktop/uiuc 2025-2026/Research/MONET/analysis/phase1_sharegpt.ipynb`

**Purpose**: Jupyter notebook for analyzing Phase 1 results

**What it does**:
- Loads all 12 experiment results
- Generates 5 comparison plots:
  1. Scheduling Delay CDF
  2. Queue Length Over Time
  3. Throughput vs Load
  4. Prompt Length Sensitivity
  5. Queue Dynamics Summary
- Creates summary statistics table
- Exports LaTeX table for report
- Calculates improvement percentages

**How to run**:
```bash
cd analysis
jupyter notebook phase1_sharegpt.ipynb
```

**When to use**: After completing Phase 1 experiments, run this to generate plots and analysis.

---

## 📁 Directory Structure

The files are organized as follows:

```
MONET/
├── EXPERIMENT_PLAN.md          ← Read this first!
├── QUICKSTART.md               ← Setup guide
├── PROGRESS.md                 ← Update daily
├── README.md                   ← Project overview
├── CHEATSHEET.md               ← Quick reference
├── PROJECT_SUMMARY.md          ← One-page summary
├── FILES_CREATED.md            ← This file
│
├── scripts/
│   ├── validate_setup.sh       ← Run first!
│   └── phase1_runner.sh        ← Run Phase 1 experiments
│
├── analysis/
│   ├── phase1_sharegpt.ipynb   ← Analysis notebook
│   └── plots/                  ← Generated plots go here
│
├── results/
│   ├── phase1/                 ← Phase 1 experiment outputs
│   └── phase2/                 ← Phase 2 experiment outputs
│
├── QLM/                        ← QLM codebase (already exists)
│   ├── benchmarks/
│   │   ├── basic_test.py
│   │   └── workload_driver.py
│   ├── qlm/
│   └── data/
│       └── ShareGPT_V3_unfiltered_cleaned_split.json (download)
│
└── MAST/                       ← MAST codebase (already exists)
    ├── traces/
    └── README.md
```

---

## 🚀 Recommended Reading Order

### First Time Setup (Day 1)
1. **PROJECT_SUMMARY.md** - Get the big picture (5 minutes)
2. **EXPERIMENT_PLAN.md** - Understand the full plan (30 minutes)
3. **QUICKSTART.md** - Follow setup instructions (30 minutes)
4. Run **validate_setup.sh** - Verify everything works (5 minutes)

### Starting Experiments (Day 2+)
1. **CHEATSHEET.md** - Quick reference for commands
2. Run **phase1_runner.sh** - Execute experiments
3. **PROGRESS.md** - Track your progress daily

### Analysis & Report (Week 2)
1. **phase1_sharegpt.ipynb** - Generate plots
2. **PROGRESS.md** - Update with findings
3. **EXPERIMENT_PLAN.md** - Reference report structure

---

## 📝 How to Use These Files

### Daily Workflow
1. Check **PROGRESS.md** for today's tasks
2. Use **CHEATSHEET.md** for command reference
3. Update **PROGRESS.md** with completed tasks
4. Add notes/observations to **PROGRESS.md**

### Weekly Workflow
1. Review **EXPERIMENT_PLAN.md** for next week's goals
2. Update **PROGRESS.md** with weekly summary
3. Email supervisor using template in **PROGRESS.md**

### When Stuck
1. Check **CHEATSHEET.md** for troubleshooting
2. Check **QUICKSTART.md** for setup issues
3. Check **EXPERIMENT_PLAN.md** for context

---

## 🎯 Key Files for Each Phase

### Phase 1: ShareGPT Baseline
- **QUICKSTART.md** - Setup and run experiments
- **validate_setup.sh** - Verify setup
- **phase1_runner.sh** - Run all experiments
- **phase1_sharegpt.ipynb** - Analyze results
- **PROGRESS.md** - Track progress

### Phase 2: Agentic Traces
- **EXPERIMENT_PLAN.md** - Phase 2 details
- **PROGRESS.md** - Track Phase 2 tasks
- (You'll create new scripts/notebooks for Phase 2)

### Phase 3: Continuum Comparison
- **EXPERIMENT_PLAN.md** - Phase 3 details
- **PROGRESS.md** - Track Phase 3 tasks

---

## 📊 Expected Outputs

After running all experiments and analysis, you should have:

### From Experiments
- `results/phase1/vllm_baseline_mixed.json`
- `results/phase1/qlm_baseline_mixed.json`
- `results/phase1/vllm_high_rate.json`
- `results/phase1/qlm_high_rate.json`
- `results/phase1/vllm_bursty.json`
- `results/phase1/qlm_bursty.json`
- `results/phase1/vllm_multiuser.json`
- `results/phase1/qlm_multiuser.json`
- `results/phase1/vllm_short_prompts.json`
- `results/phase1/qlm_short_prompts.json`
- `results/phase1/vllm_long_prompts.json`
- `results/phase1/qlm_long_prompts.json`

### From Analysis
- `analysis/plots/plot1_scheduling_delay_baseline.png`
- `analysis/plots/plot2_queue_length_over_time.png`
- `analysis/plots/plot3_throughput_vs_load.png`
- `analysis/plots/plot4_prompt_length_sensitivity.png`
- `analysis/plots/plot5_queue_dynamics_summary.png`
- `analysis/plots/summary_statistics.csv`
- `analysis/plots/summary_table.tex`

---

## ✅ Checklist: Have You...

### Setup
- [ ] Read PROJECT_SUMMARY.md
- [ ] Read EXPERIMENT_PLAN.md
- [ ] Read QUICKSTART.md
- [ ] Run validate_setup.sh
- [ ] Downloaded ShareGPT dataset
- [ ] Tested basic functionality

### Phase 1 Experiments
- [ ] Started vLLM server
- [ ] Run phase1_runner.sh (or manual experiments)
- [ ] Verified all 12 JSON files created
- [ ] Run phase1_sharegpt.ipynb
- [ ] Generated all 5 plots

### Documentation
- [ ] Updated PROGRESS.md daily
- [ ] Wrote methodology section in Overleaf
- [ ] Wrote results section in Overleaf
- [ ] Emailed supervisor with update

---

## 🆘 Need Help?

### File-Specific Issues
- **Setup problems**: Check QUICKSTART.md troubleshooting section
- **Command syntax**: Check CHEATSHEET.md
- **Experiment design**: Check EXPERIMENT_PLAN.md
- **Progress tracking**: Update PROGRESS.md

### General Issues
1. Check the relevant file's troubleshooting section
2. Search for error message in QUICKSTART.md or CHEATSHEET.md
3. Add question to PROGRESS.md for supervisor
4. Email supervisor using template in PROGRESS.md

---

## 📧 Sharing Files

### With Supervisor
- Email **PROGRESS.md** weekly for updates
- Share **PROJECT_SUMMARY.md** for quick overview
- Share plots from `analysis/plots/` with results

### With Others
- Share **README.md** for project overview
- Share **EXPERIMENT_PLAN.md** for detailed methodology
- Share **QUICKSTART.md** for reproduction

---

## 🎉 You're All Set!

You now have:
- ✅ Complete experiment plan (EXPERIMENT_PLAN.md)
- ✅ Step-by-step setup guide (QUICKSTART.md)
- ✅ Progress tracker (PROGRESS.md)
- ✅ Automated experiment runner (phase1_runner.sh)
- ✅ Analysis notebook (phase1_sharegpt.ipynb)
- ✅ Quick reference (CHEATSHEET.md)
- ✅ Project overview (README.md, PROJECT_SUMMARY.md)

**Next step**: Run `./scripts/validate_setup.sh` to verify your setup!

---

**Created**: March 30, 2026  
**Last Updated**: March 30, 2026  
**Version**: 1.0
