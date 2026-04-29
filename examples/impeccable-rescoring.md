# Impeccable: Rescoring Analysis

**Date:** 2026-04-28
**Subject:** [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable) — a real-world frontend-design rubric that violates *Don't Let the LLM Pick a Number* five times in one prompt.
**Why it's interesting:** The author is sophisticated. He isolates judges, ships a deterministic detector, fixes the scale, anchors the criteria. He still falls into the central trap because *picking ten integers and summing them is the path of least resistance.* That makes impeccable an ideal mid-sized target for showing what the methodology fixes.

---

## TL;DR

Impeccable scores UI quality two ways:

- `/impeccable critique` — an LLM rates each of Nielsen's 10 heuristics 0–4, sums to 0–40.
- `/impeccable audit` — an LLM rates 5 technical dimensions 0–4, sums to 0–20.

The integers are picked directly by the LLM. There is no evidence collection, no diminishing returns, no confidence multiplier. A perfect rule-based detector exists alongside but does not contribute to the number.

A 30-minute redesign using the seven principles would replace the ten integer picks with ten *evidence lists*, normalize for evidence count, scale by density-based confidence, and let the deterministic detector contribute weighted negative items. The expected wins: lower variance, better calibration on edge cases, and a clean A/B story.

---

## How impeccable scores today

### The headline rubric (`heuristics-scoring.md`)

> *"Score each of Nielsen's 10 Usability Heuristics on a 0–4 scale. Be honest — a 4 means genuinely excellent, not 'good enough.'"*

Each heuristic ships with a 5-row anchor table (verbatim, *Visibility of System Status*):

| Score | Criteria |
|-------|----------|
| 0 | No feedback — user is guessing what happened |
| 1 | Rare feedback — most actions produce no visible response |
| 2 | Partial — some states communicated, major gaps remain |
| 3 | Good — most operations give clear feedback, minor gaps |
| 4 | Excellent — every action confirms, progress is always visible |

Final score = plain sum, mapped to bands (Excellent 36–40 → Critical 0–11).

### What's good in the current design

- **Discrete integer scale** with behavioral anchors (closer to good than open-ended 0–10).
- **Bounded** with rating bands.
- **Implicit center prior** (the doc notes *"Most real interfaces score 20–32"*).
- **Dual-judge isolation** — the orchestrator launches LLM Assessment A and rule-based Assessment B in *separate heads* so they don't anchor each other:
  > *"Neither may see the other's output — this isolation is what makes the combined score honest."*
- **A clean deterministic baseline exists** (`detect-antipatterns.mjs`, ~24 hand-coded antipattern rules with stable IDs like `side-tab`, `gradient-text`, `ai-color-palette`). It produces a list of findings and an exit code, no number.

### What goes wrong

The deterministic detector and the score live on parallel tracks. The number is computed entirely inside the LLM by ten direct integer picks. The detector's findings are mentioned in prose, never folded into the math.

---

## Failure modes vs the seven principles

| # | Principle | Status in impeccable | Evidence |
|---|---|---|---|
| 1 | Collect evidence, not numbers | **Violated** | Prompt asks for an integer per heuristic; no instruction to enumerate observed feedback events first. |
| 2 | Discrete impact set, both signs | **Partial** | 0–4 is discrete but unsigned. Cannot register independent positives + negatives in one heuristic. |
| 3 | Diminishing returns (sqrt) | **Violated** | Final score is a plain sum of ten subscores. 8/10 perfect heuristics = 4/10 perfect + 4/10 good. |
| 4 | Confidence multiplier from evidence density | **Absent** | No concept of "I inspected 3 things vs 30." Calibration is *"Be honest"*. |
| 5 | Anchored center | **Present (implicit)** | Midpoint at 2; doc anchors *"Most real interfaces score 20–32."* Lives in prose, not math. |
| 6 | Bounded scale | **Present** | 0–40 / 0–20 with bands. |
| 7 | Separation of LLM collection vs deterministic computation | **Violated in scoring; partial elsewhere** | Detector is clean and rule-based but produces zero contribution to the number. |

The textbook attack: *"Assessment A's prompt asks the LLM to emit ten integers in {0,1,2,3,4} and the orchestrator just sums them."* That is exactly what the methodology exists to close.

---

## Rescore: applying the seven principles

Below is a worked redesign of one Nielsen heuristic — *Visibility of System Status* — using the evidence-item methodology. The same pattern applies to the other nine and to all five `audit` dimensions.

### Step 1: Replace the integer pick with an evidence catalog

Instead of "score 0–4," the prompt asks the LLM to emit a list of evidence items drawn from a fixed catalog. Each item has an explicit, signed impact in the standard set `{+5, +3, +2, +1, -1, -2, -3, -5}`.

```yaml
heuristic: visibility-of-system-status
catalog:
  positive:
    - id: vss-pos-loading-feedback
      impact: +3
      definition: Long-running operation (>500ms) shows progress indicator
    - id: vss-pos-state-confirmation
      impact: +2
      definition: Destructive action shows confirmation + result toast
    - id: vss-pos-async-status
      impact: +1
      definition: Async save shows "saving / saved / error" state
    - id: vss-pos-empty-state-helpful
      impact: +2
      definition: Empty list states explain *why* it's empty + next step
    - id: vss-pos-skeleton-load
      impact: +1
      definition: Initial render uses skeleton/placeholder, not blank screen
  negative:
    - id: vss-neg-silent-action
      impact: -3
      definition: Action completes with no visible response (button click,
                  form submit, delete)
    - id: vss-neg-blank-loading
      impact: -2
      definition: Loading state is a blank screen with no indicator
    - id: vss-neg-stale-state
      impact: -2
      definition: UI shows stale data after action; requires manual refresh
    - id: vss-neg-mystery-spinner
      impact: -1
      definition: Spinner with no context for what's loading
  critical_negative:
    - id: vss-neg-error-swallowed
      impact: -5
      definition: Error condition produces zero feedback (silent failure)
```

The LLM's job is now: *"For the target page, list every evidence item from the catalog that you observed, with a one-line citation."* No integer picking.

### Step 2: Compute the heuristic score with the formula

Suppose the LLM returns:
- 1× `vss-pos-loading-feedback` (+3)
- 2× `vss-pos-async-status` (+1, +1)
- 1× `vss-pos-skeleton-load` (+1)
- 1× `vss-neg-mystery-spinner` (−1)
- 1× `vss-neg-blank-loading` (−2)

```
total_items   = 6
net_impact    = 3 + 1 + 1 + 1 - 1 - 2 = 3
normalized    = 3 / sqrt(6) = 1.225
raw_score     = 50 + (1.225 * 8.0) = 59.8
density       = 6 / 20 = 0.30
multiplier    = 0.75 + 0.25 * 0.30 = 0.825
final (100pt) = 50 + (59.8 - 50) * 0.825 = 58.1
```

To plug into impeccable's existing 0–4 band, scale by 4/100 → **2.32** (rounds to 2 if discrete bands are required, or kept continuous for richer reporting).

### Step 3: Sum across heuristics with the same diminishing-returns trick

Instead of `sum(s_i for i in 1..10)`, treat all heuristics as contributing items to a single page-level pool:

```
total_items_page = sum(items in heuristic i for i in 1..10)
net_page         = sum(impacts across all 10 heuristics)
normalized       = net_page / sqrt(total_items_page)
raw_page_score   = 50 + (normalized * 8.0)  → clamped [0,100]
multiplier       = 0.75 + 0.25 * clamp(total_items_page / 50, 0, 1)
final_page       = 50 + (raw_page_score - 50) * multiplier
```

Now an interface that nails 8/10 heuristics with thin evidence does *not* automatically tie an interface that nails 4/10 with rich evidence. Density and depth carry weight.

### Step 4: Fold the deterministic detector into the math

Every CLI antipattern hit becomes a negative evidence item with a fixed impact:

```yaml
detector_items:
  - id: antipattern-side-tab
    impact: -2
    source: detector
  - id: antipattern-gradient-text
    impact: -1
    source: detector
  - id: antipattern-ai-color-palette
    impact: -3
    source: detector
  ...
```

These items enter the same formula as LLM-collected items. Now:

- The deterministic baseline contributes **directly** to the score (principle 7 honored across the whole pipeline, not just the detector subprocess).
- A page can fail the LLM review *and* the detector simultaneously without double-counting through ad-hoc weighting — they're just items in the same pool.
- The detector's findings get to *push the score* the way the LLM's do, so improvements to the rule set move the number.

### Step 5: Keep dual-judge isolation, repurpose it

Bakaus's "neither may see the other's output" insight is correct and worth keeping. In the rescored version it becomes:

- **Pass 1 (LLM):** evidence collection only — emit items from the catalog with citations. No score.
- **Pass 2 (detector):** rule-based scan, emits items as above.
- **Pass 3 (math, deterministic):** apply the formula.

Three independent stages, no anchoring. The LLM never sees a number to anchor to because the LLM never produces a number.

---

## Why this is worth doing

1. **Real-world target with a sophisticated author.** Bakaus did most things right and still lost the score-picking battle. That's a much stronger empirical case than rescoring a strawman rubric.
2. **Both halves of the apparatus already exist.** Impeccable ships the deterministic baseline (24 antipattern rules) AND the LLM rubric (10 heuristic anchors). The methodology runs on top of his work and demonstrates the merge — no detector to invent.
3. **Tight experiment loop.** Pick 20 popular open-source UIs (Linear, Vercel dashboard, GitHub issues, Notion). Run impeccable's `/critique` 5× per UI, then run the rescored version 5× per UI. Compare:
   - Variance across runs (predicted: rescored drops, vanilla doesn't)
   - Sensitivity to rubric phrasing (perturb the prompt slightly)
   - Behavior at the edges (a great UI vs a deliberate bad one) — does the score saturate or stay calibrated?
4. **Visual artifacts.** The 342-occupation rescoring made a clean before/after distribution chart. UI scoring would do the same and the *artifacts are screenshots*, which is a much stronger figure than a job title.

A tidy 30–60 hour experiment that produces a real comparison artifact and could anchor a related-work paragraph or a full case-study sidebar.

---

## A two-week experiment plan

1. **Day 1–2.** Pick 5 representative pages (1 great, 1 typical, 1 weak, 1 deliberate-bad, 1 contested). Run vanilla `/impeccable critique` 5× per page. Capture all 25 score traces.
2. **Day 3–5.** Build the rescored rubric — port heuristics-scoring.md into an evidence catalog with signed impacts. Wire detector findings as items. Implement the formula in a small Python script.
3. **Day 6–8.** Run rescored version 5× per page on the same 5 pages. Capture traces.
4. **Day 9–10.** Variance analysis (std-dev across runs), calibration check (does the great page beat the bad page reliably?), sensitivity test (small prompt perturbation, does the score move?).
5. **Day 11–14.** Write up as a paper sidebar or standalone blog post: *"Rescoring impeccable: what changes when you stop letting the LLM pick a number."*

Outputs:
- One short markdown report with side-by-side score tables.
- Two distribution plots (vanilla vs rescored).
- A reusable evidence-catalog YAML that other harness authors can fork.

---

## Files inspected

- `https://github.com/pbakaus/impeccable` — README.md
- `source/skills/impeccable/SKILL.md`
- `source/skills/impeccable/reference/heuristics-scoring.md` (canonical rubric)
- `source/skills/impeccable/reference/audit.md` (5-dimension technical rubric)
- `source/skills/impeccable/reference/critique.md` (dual-judge orchestration)
- `src/detect-antipatterns.mjs` (deterministic CLI rule set)
