# cua-bench: Rescoring Analysis

**Date:** 2026-04-29
**Subject:** [`trycua/cua`](https://github.com/trycua/cua) — `cua-bench`, the benchmarking + RL-environment library inside the Cua computer-use-agent stack.
**Why it's interesting:** Unlike `impeccable`, which lets an LLM pick ten integers, **cua-bench is already on the right side of Principle 7 by construction.** The agent emits actions; deterministic Python / JavaScript / shell checks emit the reward. That makes it a useful counterpoint — proof that "stop letting the LLM pick a number" is necessary but not sufficient. cua-bench commits to determinism and *still* leaves five of the other six principles on the table.

---

## TL;DR

cua-bench is a **partial fit**, not a slam-dunk impeccable-style rescore. Honest framing:

- **Principle 7 (LLM vs deterministic separation): already satisfied.** The evaluator never sees the model. No win for the methodology to claim here.
- **Principles 1–6: still wide open.** Per-task scores are a single float in `[0, 1]`. Three example tasks ship three different partial-credit conventions. "Success" is a hard-coded `reward >= 0.5` threshold. Cross-task aggregation is plain mean. There is no anchored center, no bounded common scale, no signed evidence, no diminishing returns, no density-based confidence.
- **The opportunity is multi-step tasks.** Atomic boolean tasks ("did the button get clicked?") don't need the methodology — `{0, 1}` is the right answer. But OSWorld-class tasks ("open Settings, change wallpaper to image X, close Settings") collapse all their step-by-step richness into one terminal float, and that's where signed evidence-item scoring would dominate.

The clean takeaway: **cua-bench is what happens when a benchmark gets P7 right and stops there.** The remaining principles aren't about fixing a broken pipeline — they're about turning a deterministic single-signal pass/fail into deterministic *multi-signal evidence accumulation* so partial credit and cross-task aggregation become principled instead of improvised.

---

## What cua-bench is

cua-bench exposes a Gym-style interface (`make / reset / step / evaluate`) for evaluating agents that drive real desktops (macOS, Linux, Windows) inside Cua's sandbox VMs. Tasks are Python modules with a `main.py` defining four hooks via decorators: `@cb.tasks_config`, `@cb.setup_task`, `@cb.solve_task`, `@cb.evaluate_task`. Runs launch with:

```bash
cb run dataset datasets/cua-bench-basic --agent cua-agent --max-parallel 4
```

The runner spawns parallel workers, each resets an env, lets the agent take steps until DONE, then calls the env's `evaluate_task` hook to produce a reward. Per-step traces are logged to a HuggingFace Dataset on disk for downstream RL (PPO via Tinker).

---

## How cua-bench scores today

### The reward contract (verbatim from `cua_bench/runners.py`, lines 137–152)

```python
# Evaluate
if env.evaluate_task_fn is not None:
    result = await env.evaluate()
    if isinstance(result, (int, float)):
        reward = float(result)
    elif isinstance(result, list) and len(result) > 0:
        reward = float(result[0])
    elif isinstance(result, dict) and "reward" in result:
        reward = float(result["reward"])

return TaskResult(
    task_path=str(env_path),
    variant_id=task_index,
    success=reward >= 0.5,  # Common threshold
    reward=reward,
    steps=step_count,
    ...
)
```

Per-task score: a single float, roughly `[0, 1]`. "Success" is hard-coded `reward >= 0.5`. Aggregate is mean: `BenchmarkResult` carries `avg_reward`, `success_count`, `failed_count`. **No LLM judge in the loop.**

### Three example tasks, three partial-credit conventions

**`basic_gui_env/main.py` — pure pass/fail:**

```python
@cb.evaluate_task(split="train")
async def evaluate(task_cfg, session) -> list[float]:
    if pid is None:
        return [0.0]
    submitted = await session.execute_javascript(pid, "window.__submitted")
    return [1.0] if submitted is True else [0.0]
```

**`2048_env/main.py` — improvised continuous metric:**

```python
m = await session.execute_javascript(pid, "window.__max_tile || 0") or 0
score = min(max(int(m), 0), 2048) / 2048.0
return [float(score)]
```

**`minesweeper_game_env/main.py` — three-band rule with partial credit:**

```python
if game_won is True:
    return [1.0]
elif game_lost is True:
    return [0.0]
else:
    revealed_count = await session.execute_javascript(pid, "window.game.revealedCount")
    total_non_mines = rows * cols - mines
    if revealed_count and total_non_mines > 0:
        return [revealed_count / total_non_mines]
    return [0.0]
```

All three live in `[0, 1]`. None of them are actually comparable to each other. Yet `BenchmarkResult.avg_reward` is the unweighted mean across them.

### What's good in the current design

- **No LLM scoring.** Principle 7 satisfied structurally. The agent and evaluator code paths are separate decorated functions; the evaluator never sees a model.
- **Deterministic state introspection.** `window.__submitted`, `window.__gameWon`, `window.__max_tile` — all rule-based JavaScript checks against environment state. No prompt-engineered judge to drift.
- **Per-step traces are preserved.** `agent_step` events, screenshots, action lists are all logged to a HuggingFace Dataset on disk. The raw material for evidence items is already being captured — it's just being thrown away at scoring time.
- **Sparse-reward design is principled for RL.** The `plan.md` is explicit: *"`evaluate_task` returns a single terminal reward per episode; intermediate steps get reward 0.0 and the terminal step gets the full reward."* Reasonable for PPO; lossy for evaluation.

### What goes wrong

The evaluator's *signal collection* is deterministic, but the *signal compression* is improvised. Each task author invents their own [0, 1] mapping. There is no shared anchor for "neutral effort," no bounded common scale that means the same thing across tasks, no way to register that an agent did the wrong thing (every example evaluator is uniformly non-negative), no density-based confidence pull-back when a score is based on one JS flag firing, and no diminishing-returns curve when a long task accumulates many positive signals.

The richest part of every task — the per-step trace — is collapsed into one terminal float and discarded.

---

## Failure modes vs the seven principles

| # | Principle | Status in cua-bench | Evidence |
|---|---|---|---|
| 1 | Collect evidence, not numbers | **Partial** | Each evaluator collects exactly one signal (sometimes a small handful in a band rule). The richer per-step trace is captured but unused at scoring time. |
| 2 | Discrete impact set, both signs | **Violated** | Every example evaluator returns non-negative floats. No way to register "agent took wrong path / made extraneous changes / used the shell to bypass the GUI." |
| 3 | Diminishing returns (sqrt) | **Violated** | Where partial credit exists (`revealed_count / total_non_mines`, `max_tile / 2048`), it's linear — the 80th revealed cell counts the same as the 4th. |
| 4 | Confidence multiplier from evidence density | **Absent** | `basic_gui_env` returns `1.0` from one JS flag. If that flag fires for any reason, full credit. No density-based regression to mean. |
| 5 | Anchored center | **Violated** | "Success" is hard-coded `reward >= 0.5` in `runners.py` with comment `# Common threshold`. No notion of "50 = neutral effort" calibrated across tasks. |
| 6 | Bounded scale | **Partial** | Roughly `[0, 1]` by convention, but not enforced. Different tasks use different distributions inside that range, so cross-task aggregation is misleading. |
| 7 | Separation of LLM collection vs deterministic computation | **Satisfied (by construction)** | Agent emits actions; evaluator runs deterministic state checks. No scoring LLM exists. |

The attack is the inverse of impeccable's. Impeccable violates P7 and gets the rest right enough. cua-bench gets P7 perfect and leaves the rest improvised.

---

## Where the methodology helps

cua-bench tasks generally come in two shapes:

### Shape A — atomic boolean tasks

e.g. `basic_gui_env`: "click Submit." Inherently `{0, 1}`. **The methodology adds nothing here.** You can't refine "did the button get clicked" into multiple evidence items because there's exactly one signal. Be honest: atomic pass/fail is a region where the seven principles are overkill.

### Shape B — multi-step, judgment-laden tasks

e.g. "open Settings, change wallpaper to image X, close Settings." Today these collapse to either pass/fail or a single ad-hoc ratio. This is where evidence items dominate.

**Sample evidence catalog for "Change wallpaper" task:**

| Item ID | Impact | Detection (deterministic) |
|---|---|---|
| `wp-pos-final-state-correct` | +5 | screenshot hash matches target image X |
| `wp-pos-target-app-opened` | +3 | Settings window was in z-order at any point during run |
| `wp-pos-correct-pane-reached` | +2 | "Personalization" pane was active in trace |
| `wp-pos-cleanup-complete` | +1 | Settings window closed at end |
| `wp-pos-no-extraneous-changes` | +1 | no other settings keys mutated (preferences diff is empty outside target key) |
| `wp-neg-extra-app-opened` | −1 | non-Settings app focused mid-run |
| `wp-neg-extraneous-clicks` | −1 | clicks on UI not on the action path (>3 stray clicks in trace) |
| `wp-neg-wrong-pane` | −2 | a different settings pane was navigated/changed |
| `wp-neg-required-step-skipped` | −3 | wallpaper changed without Settings ever being opened (e.g. `defaults write` from terminal) |
| `wp-neg-final-state-wrong` | −5 | wallpaper unchanged or wrong image |

Crucially, **every item is detectable by deterministic checks already in cua-bench's world** — window z-order, screenshot hashes, mouse-event traces, FS diffs, JS `window.__*` flags. No LLM judge is introduced. P7 stays satisfied. The deterministic evaluator goes from one signal to ten.

### Worked example: applying the formula

Suppose an agent opens the Settings app, clicks around the wrong pane briefly, then finds the Personalization pane and successfully changes the wallpaper, but leaves Settings open at the end.

Items observed: `wp-pos-final-state-correct (+5)`, `wp-pos-target-app-opened (+3)`, `wp-pos-correct-pane-reached (+2)`, `wp-pos-no-extraneous-changes (+1)`, `wp-neg-wrong-pane (−2)`. Total: 5 items, net_impact = +9.

```
normalized_impact   = 9 / sqrt(5)          ≈ 4.025
raw_score           = 50 + (4.025 * 8.0)   ≈ 82.2
evidence_density    = 5 / 20               = 0.25
confidence_mult     = 0.75 + (0.25 * 0.25) = 0.8125
deviation           = 82.2 − 50            = 32.2
final_score         = round(50 + 32.2 * 0.8125) ≈ 76
confidence          = 0.25
```

**Compare to today's evaluator:** the existing logic would either return `1.0` (wallpaper changed → success) or `0.0` (wallpaper unchanged → fail). Both readings discard the "navigated wrong pane first" and "didn't close Settings" details. The evidence-item version says *76 with 0.25 confidence* — a calibrated "mostly right but enough sloppiness to dock the score, and we're aware we only inspected five facets."

Now run a second agent that bypasses the GUI entirely with a shell command. Items: `wp-pos-final-state-correct (+5)`, `wp-neg-required-step-skipped (−3)`. Total: 2 items, net_impact = +2.

```
normalized_impact   = 2 / sqrt(2)          ≈ 1.414
raw_score           = 50 + (1.414 * 8.0)   ≈ 61.3
evidence_density    = 2 / 20               = 0.10
confidence_mult     = 0.75 + (0.25 * 0.10) = 0.775
deviation           = 11.3
final_score         = round(50 + 11.3 * 0.775) ≈ 59
```

Today's evaluator returns `1.0` for both agents — same score. The seven-principle version separates them (76 vs 59) and registers low confidence (0.25 / 0.10) on both. The second agent's score is dragged closer to neutral *because the evidence base is thin*, which is exactly what we want when an agent technically achieved the end state by skipping the path.

---

## Where the methodology may NOT help

Be honest:

- **Pure pass/fail tasks.** `{0, 1}` is the right answer for "did the button get clicked." Adding seven principles to a coin flip is overkill.
- **The LLM-vs-deterministic separation is already done.** Principle 7 was an easy sell against impeccable; there's no win to claim here.
- **Variance is hardware-driven, not judge-driven.** Repeated cua-bench runs vary because real GUIs flake (timing, focus, random seeds). The methodology won't fix VM-flakiness — that's a flake-tolerant retry / CI problem.
- **Upstream benchmark conventions (OSWorld, ScreenSpot, Windows Arena).** cua-bench inherits external success criteria. Rewriting their scoring would either fork or break leaderboard comparability.
- **The Tinker PPO RL loop.** Replacing reward with a confidence-discounted, sqrt-normalized composite changes the optimization landscape. Possibly for the better, but it'd need separate validation before claiming a win.

This isn't where the impeccable rescoring story rhymes. cua-bench's flaws are *small task authors improvising partial credit*, not *one author letting an LLM pick the number*.

---

## Recommendation

**Don't run a full impeccable-style rescoring experiment on cua-bench.** Instead, treat it as:

### 1. A counterpoint paragraph in related-work writing

> "Where impeccable lets the LLM pick a number on a 0–4 rubric (violating Principle 7), cua-bench commits to deterministic state-introspection and is scored entirely by rules — Principle 7 is satisfied by construction. What it lacks is principles 2–6: signed evidence sets, sqrt diminishing returns, density-based confidence, an anchored center, and a uniformly bounded scale. Three example evaluators ship three different partial-credit conventions and a hard-coded `success >= 0.5` threshold. The opportunity is not to stop the LLM picking numbers — it is to turn deterministic single-signal pass/fail into deterministic multi-signal evidence accumulation, so cross-task aggregation and partial-credit reporting become principled instead of improvised."

This is a paragraph, not a section. It strengthens the broader case because it shows the seven principles are independently necessary — getting P7 right doesn't get you the rest for free.

### 2. (Optional) A future-work bullet

If a tractable case study is wanted: **pick one multi-step OSWorld-class task with rich trace data** ("configure Slack notifications" or "create a calendar event matching specs"). Build a 12–15 item signed evidence catalog over its existing trace data. Show that the seven-principle composite correlates better with human preference than the existing single-flag terminal reward across N=20 agent runs. Tractable 1–2 week experiment with a real artifact. Pairs well with the impeccable rescoring as a "two-domain validation" — UI quality + computer-use task quality, same methodology, both improved.

### 3. A skip

If experiments aren't expanding, the related-work paragraph alone is enough. The methodology is stronger when it can name a benchmark that *isn't* the canonical "LLM picks a number" failure but still benefits from the rest of the principles — that argues each principle pulls its own weight.

---

## File references

- `https://github.com/trycua/cua/blob/main/libs/cua-bench/plan.md` — RL/Tinker plan, trace schema, sparse-reward design rationale
- `https://github.com/trycua/cua/blob/main/libs/cua-bench/cua_bench/runners.py` — canonical reward-resolution + `success >= 0.5` threshold (lines 137–152)
- `https://github.com/trycua/cua/blob/main/libs/cua-bench/cua_bench/decorators.py` — the four task hooks
- `https://github.com/trycua/cua/blob/main/libs/cua-bench/example_tasks/basic_gui_env/main.py` — pure pass/fail
- `https://github.com/trycua/cua/blob/main/libs/cua-bench/example_tasks/2048_env/main.py` — improvised continuous metric
- `https://github.com/trycua/cua/blob/main/libs/cua-bench/example_tasks/minesweeper_game_env/main.py` — three-band rule with partial credit
