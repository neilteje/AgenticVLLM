Good — I dug into the reuse-analysis CSVs and into `vllm-continuum` itself. A lot of what you need is already wired into Continuum at the protocol level. Here's my analysis, then the plan.

# 1. Why throughput drops on some traces while JCT wins

Throughput as you're computing it is `total_tokens / wall_time` (both wall-based and LM-only). When your sub-agent cache hits, both the numerator (tokens that actually flowed through vLLM) and the denominator (time) shrink. Which one shrinks faster is determined entirely by which turns got cached.

Per-trace numbers from `pairwise_comparison.csv` (LM-only tokens/s, baseline → reuse, and the executed-request avg prompt tokens):

| Trace | Cache hit % | Baseline → Reuse tokens/s | Baseline avg prompt tok/req | Reuse avg prompt tok/req |
|---|---|---|---|---|
| astropy-12907 | 31% | **726 → 968 (+33%)** | 11,288 | **15,143** |
| astropy-14365 | 44% | 1,388 → 1,471 (+6%) | 16,180 | 16,282 |
| astropy-6938 | 41% | **767 → 622 (−19%)** | 5,023 | **4,418** |
| matplotlib-24334 | 36% | **795 → 697 (−12%)** | 8,076 | **6,626** |
| matplotlib-24265 | 17% | 258 → 252 (−2%) | 1,763 | 1,917 |

The rule is obvious once you look at the last two columns: **cache hits drop throughput exactly when you cached the expensive-prefix turns, and raise throughput when you cached the cheap-prefix turns**. astropy-12907 still-executed turns average 15k prompt tokens (+34% vs baseline's 11.3k) because you cached the short navigator look-ups and left the fat editor/planner turns behind → the remaining pool is *denser*, so tokens/s went up. On astropy-6938 you cached the fat editor look-ups and left the small exploratory ones → remaining pool is *lighter*, tokens/s fell. Totally consistent with `savings_by_tool_signature.csv`: `open_file_gen`, `open_file`, `get_all_symbols` get 34–38% hit rates and carry 13–23k prompt-tokens/req, so different traces hit different slices.

**So the paradox isn't real, and throughput here does not mean "efficiency".** It is a weighted average of the *survivors*. For a scheduler study this is a misleading number to publish.

# 2. Why throughput-as-defined doesn't matter for what you're actually doing

You explicitly said: "one job = one user input, given one job, make it faster." That is **end-to-end single-job latency** — a JCT problem, not a system-throughput problem. Tokens/s is the right KPI only when you are trying to fit **more concurrent jobs onto a fixed GPU** (multi-tenant serving). In your current serial-replay design there is never more than one in-flight request, so tokens/s is just GPU utilization inside the one job, and it can swing either direction depending on which turns you skipped without telling you anything about efficiency.

What actually characterizes your optimization on a single job:

1. **JCT wall-clock (`wall_solve_time_s`)** — you already have it. Primary success metric.
2. **JCT LM-only (`lm_only_solve_time_s`)** — factors out synthetic tool sleeps. Already have it.
3. **Per-turn request latency p50/p95/p99** — already have it.
4. **GPU-seconds-per-job** = Σ(request_latency_s). This is what you actually cost the GPU. Sub-agent caching drives this down by skipping; Continuum drives this down by shrinking prefill.
5. **Prefill tokens processed** = `Σ(prompt_tokens − cached_tokens)`. OpenAI-compat vLLM already returns `usage.prompt_tokens_details.cached_tokens`; `vllm-continuum` preserves this field (`protocol.py:132–140`). This is the cleanest efficiency metric because it's conserved: caching a turn zeros its prefill, KV-pinning a turn zeros its cached prefix. Both methods show up in the same number.
6. **Decode tokens** (completion_tokens) — mostly fixed across engines; useful as a sanity check.
7. **Work-avoided ratio** = (baseline_prefill − variant_prefill) / baseline_prefill. Per-trace and aggregate. This is the apples-to-apples efficiency metric to put in the paper.
8. **Stage-level p95** from your existing `derive_slos_and_resource_groups.py` — per `(sub-agent × tool signature)`. This exposes *where* the speedup lands (e.g. "Navigator × open_file p95 drops 40% under Continuum; Planner p95 doesn't move").
9. **Critical-path latency** — for HyperAgent the DAG is already serial (Planner gates everything), so this equals JCT today. But the moment you add parallelism, critical-path ≠ sum-of-latencies and you'll need this.
10. **Context-trim events** (`num_turns_context_trimmed`, `num_context_retry_events`) — already recorded. Continuum shouldn't change these, but worth logging as a robustness control.

Honestly, if you want one headline number besides JCT, it should be **(5) prefill-tokens-processed** or **(4) GPU-seconds-per-job**, not tokens/s.

# 3. Continuum's "job" vs yours — already more aligned than you think

I went into `vllm-continuum/vllm/v1/core/sched/request_queue.py` and `estimate_with_func.py` to confirm what Continuum's scheduler actually uses. Three findings that change the plan:

**(a) Continuum's scheduling unit is exactly `job_id`.** `ContinuumRequestQueue` groups by `job_id` and does job-level FCFS + "pinned request priority". In the `mini-swe-agent` / SWE-bench setting Hanchen built it for, one job = one SWE instance, i.e. one user query's whole trajectory — **the same definition you use**. Your "one user input = one job" mapping is Continuum-native. You were worried about a mismatch; there isn't one at the scheduling level.

**(b) Continuum accepts four custom protocol fields** (`vllm/entrypoints/openai/protocol.py:292–298, 634–638, 1147–1151`):
- `job_id` — groups all turns of a trace
- `this_func_call` — current tool signature  
- `last_func_call` — previous tool signature
- `is_last_step` — signals end of the job so Continuum releases the pinned KV

These are passed through `extra_body` in the OpenAI Python client — **no vLLM-side code change needed** on our side, it's a first-class API.

**(c) The pin mechanism (`scheduler.py:1358` + `estimate_with_func.set_up_pin`).** When a non-final turn of a pinned-scheduling job finishes, Continuum keeps that request's KV blocks alive for `FIXED_THRESHOLD_CONTINUUM = 2.0s` (tunable) if the tool-signature's observed execution time is ≤ 2s. So the next turn of the same job — which shares the entire growing prefix — can prefix-match that pinned cache. That's exactly the "within-one-job speedup for a multi-turn agent" that matches *your* research goal. The relevance of this mechanism to single-job optimization is real; the part you can't unlock in isolation is the *scheduler-reorder* benefit (which needs concurrent jobs).

**(d) One caveat on `this_func_call`.** `estimate_with_func.request_finished` overwrites `request.this_func_call` by parsing `\`\`\`bash ... \`\`\`` out of the model output (mini-swe-agent's format). HyperAgent emits mostly python code blocks with tool names like `open_file._run`. Two clean options: (i) pass the tool signature as the first token inside a `\`\`\`bash` fence so the parser sees it, or (ii) one-line patch to `estimate_with_func.py` to skip the re-parse when `request.this_func_call` is already set by the client. Option (ii) is better for paper-reproducibility and costs you about 5 lines.

# 4. Two regimes you need to run, and why both

**Regime A — Serial single-job (the question you're actually optimizing).** One trace at a time, serial turns. Measures only Continuum's *KV-pinning* benefit (the scheduler has nothing to reorder). This is the cleanest apples-to-apples against your `baseline` and `reuse` replays: you reuse every setting already in `hyperagent-replay/replays-two/`.

**Regime B — Concurrent multi-job (what Continuum is actually built for).** Stagger trace arrivals (e.g. Poisson λ=1/30s, or simultaneous kick-off of 5 traces) so multiple jobs are in flight at once. The scheduler now has a real choice and Continuum's job-level FCFS + pinned-priority can actually reorder. This is also where `throughput` (jobs/s, tokens/s) *becomes* a legitimate metric again.

Regime A answers: "does Continuum help our single-job goal?" Regime B answers: "is our method still useful once you pile up realistic traffic?" Both matter. The paper has a much stronger story with both.

# 5. The 2×2×2 experiment matrix

For each trace in your existing 10-trace set, run:

| | **No reuse** (baseline) | **Sub-agent reuse** (your method) |
|---|---|---|
| **vLLM stock (FCFS)** | cell A — already have | cell B — already have |
| **vllm-continuum (`--scheduling-policy continuum`)** | cell C — **new** | cell D — **new** |

Times two regimes (serial, concurrent) = 8 runs per trace. For 10 traces that's ~80 replay invocations. On A100 the per-trace wall-clock is well known from your baselines (153s – 4634s), so budget-wise: the 2 fastest traces each regime get you a ~15-min pilot, and the full sweep fits into one or two 6-hour allocations.

What each cell tells you:
- **A vs B** — how much does app-level sub-agent caching save? (you already answered: −34.8% wall.)
- **A vs C** — how much does engine-level KV pinning alone save?
- **C vs D** — do the two mechanisms stack? (hypothesis: yes, because they act on disjoint sets of turns — reuse removes redundant *requests*, Continuum accelerates the *surviving* prefills.)
- **B vs D** — is Continuum a good baseline, or does it beat you?

You can also collapse the four cells into one stacked-bar chart per trace: "baseline prefill tokens → stock+reuse saves X → continuum+no-reuse saves Y → continuum+reuse saves X+Y (if additive)". That's a strong figure.

# 6. Integration: minimal code plan (no code written yet)

I'd scope it as **three small edits + two new drivers**, all in `hyperagent-replay`.

**Edit 1 — `src/hyperagent_replay/replay.py`, `replay_trace`.** In the `client.chat.completions.create(...)` call add `extra_body={...}` with:
```
job_id = trace["instance_id"]
this_func_call = f"{turn['agent']}::{turn.get('action',{}).get('tool_name') or 'LLM_ONLY'}"
last_func_call = previous_turn_this_func_call  # None for turn 0
is_last_step = (completed_turns == total_turns)
```
Gate it behind a new CLI flag `--engine-mode {stock,continuum}`. If `stock`, don't send these fields (keeps results bit-reproducible against your existing replays). This is ~20 lines.

**Edit 2 — capture `cached_tokens`.** In `results.append(...)` pull `getattr(usage, "prompt_tokens_details", None)` and store `cached_tokens`. Compute `prefill_tokens_new = prompt_tokens - cached_tokens` and surface it in `timing` as `total_prefill_tokens_processed`. This is the work metric for metric (5) above.

**Edit 3 — one-line patch in `vllm-continuum/vllm/v1/core/estimate_with_func.py:request_finished`** so that if the incoming request already has `this_func_call` set, it's not overwritten by the bash-regex parser. Otherwise your HyperAgent tool signatures don't flow into `func_call_to_exec_time` and pin decisions get made on garbage. 5 lines.

**New driver 1 — `ha-trace-concurrent-replay`.** An asyncio driver that accepts a list of extracted traces plus an arrival schedule (`--arrival-rate`, `--burst-size`, or an explicit schedule file), fires each trace as an independent coroutine against a single base URL, and writes per-trace replay JSONs + one merged scheduler_timestamps. Replay inside one trace remains sequential (the agent logic requires it); concurrency is *across* traces. ~150 lines on top of `replay.py`'s existing `replay_trace`.

**New driver 2 — `ha-compare-engines`.** Orchestrates the 2×2 matrix from one YAML: point at two base URLs (stock + continuum), two modes (no-reuse/reuse), run the same trace set against each, emit a single normalized comparison CSV mirroring your existing `pairwise_comparison.csv` but with two extra columns (`engine`, `reuse_mode`). ~100 lines, mostly wiring.

**New analysis columns.** Extend the reuse analyzer to report, per cell of the matrix: wall JCT, LM-only JCT, Σrequest_latency (GPU-seconds), total prefill tokens processed, mean/p50/p95/p99 turn latency, stage-level p95 from `derive_slos_and_resource_groups`, and Continuum-specific events (num pins, avg pin lifetime, prefix-hit length from `hit_length`) for Continuum cells. The Continuum events are free: `print_history` in `estimate_with_func.py` already dumps `RUN_OUTPUT_DIR/scheduler_timestamps` with `pinned_time`, `unpinned_time`, `waiting_to_running`/`evicted_to_running` carrying `prompt_length` and `hit_length`.

# 7. Fairness / pitfalls I want to handle before you run

- **Warmup**: first turn of a trace on a cold vLLM server pays model-load cost. Run one throwaway trace per server before timing.
- **Prefix-cache state between traces**: vLLM's automatic prefix cache persists across requests. When you run A→B→C serially, trace C sees leftover cache from A and B. Either `curl POST /reset_prefix_cache` between traces (stock vLLM supports it), or randomize trace order across runs and report multi-seed averages. This matters more than it sounds — an uncontrolled prefix cache can silently close half of the gap between "stock" and "continuum".
- **Same seed, temperature 0, same `max_completion_tokens`, same `max_model_len`.** You already do this; carry it to Continuum runs verbatim.
- **`max_completion_tokens=512` vs `256`**: your existing astropy-12907 eval used 256 but the current default is 512. Pick one and lock it across all cells.
- **Ordering of traces**: report mean over 3 shuffled orderings to wash out cache-state carryover.
- **Arrival schedule for Regime B**: use the same random schedule across engines. Seed the arrival generator, save the schedule to disk, replay that schedule under each engine.

# 8. Expected outcome & the story to tell

If the hypothesis lands:
- **A→B**: −35% wall (known).
- **A→C**: I'd expect −15% to −25% wall on long-trace instances (astropy-12907, astropy-14365, matplotlib-24334), driven by prefix-cache pinning; ≈0% on short traces (django-10924, 25433) because they barely span the 2-second pin window.
- **A→D**: −45% to −55% wall — stacked. `cached_tokens` as % of `prompt_tokens` should go from ~60–80% (stock's prefix cache) to ~85–95% (Continuum's pinned cache) on the surviving turns in D.

That directly answers both your questions:
1. **Throughput dropping doesn't mean your method is worse**; it means you cached the heavy turns. Replace it with prefill-tokens-processed (or GPU-seconds) and the story reads correctly.
2. **Continuum is usable as a baseline with zero server-side code changes** (just `extra_body` + one regex-guard patch), and the combination of your sub-agent reuse with Continuum is the paper's contribution (two orthogonal savings mechanisms, one per-layer).

Want me to proceed to implementation? If so, my suggested order is: Edit 2 first (it's independent and gives us the prefill-processed metric retroactively for the current 10 baseline+reuse replays), then Edit 1 + Edit 3 (unlocks Continuum Regime A), then the concurrent driver (Regime B), then the comparison analyzer. We can pilot Regime A on 3 small traces (django-10924, matplotlib-25433, django-11179) in ~15 minutes of GPU time to validate before committing to the full sweep.