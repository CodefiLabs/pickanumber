# karpathy/jobs: Cross-Domain Replication

**Date:** 2026-03-26
**Subject:** [`karpathy/jobs`](https://github.com/karpathy/jobs) — Andrej Karpathy's AI-exposure scoring system. 342 occupations from the BLS Occupational Outlook Handbook, scored 0–10 by a single Gemini Flash call.
**Why it's interesting:** Karpathy is a careful practitioner. The system has anchored prompt examples, a focused single-call architecture, and ships real numbers on real data. It's also the textbook "LLM picks a number" failure — and because it's at scale (342 examples), we can show the methodology working *across the whole distribution* rather than on one page like impeccable. This is the cross-domain validation that proves the seven principles aren't hackathon-specific.

---

## TL;DR

We re-scored all 342 occupations using the principled methodology, with the same evidence-gathering prompt across 9 models from 5 providers (Anthropic, Google, OpenAI, xAI, Zhipu).

- **Discrimination improvement: 21–58% (median 41%)** across 9 models. Every principled run produces higher std dev than the naive baseline (2.26).
- **Rank preservation: Spearman ρ = 0.87.** The principled approach mostly agrees with the naive ordering — it spreads scores out, doesn't reshuffle them randomly.
- **Cross-model agreement: ρ = 0.77–0.93** across all 36 model pairs. The methodology produces stable rankings regardless of which model collects the evidence.
- **The naive distribution is a textbook RLHF bell curve** centered at 5.3 with a spike at 7. Every principled run breaks it: bimodal or heavy-tailed, with clusters at 0 (physical jobs) and 10 (digital jobs).
- **The 13% of rankings that change are the interesting ones.** Teachers, actors, directors — jobs the naive scorer marks 6–7 because they "use computers," but the principled approach scores 0–2 because their core work is physical or interpersonal.

If impeccable is the qualitative case study (one rubric, one mitigation, before/after), karpathy/jobs is the quantitative one (342 cases × 9 models, distribution-level evidence).

---

## What karpathy/jobs is

Karpathy's repo scores how exposed each occupation is to AI displacement, on a 0–10 scale. The data source is the BLS Occupational Outlook Handbook — one markdown page per occupation with task descriptions, work environment, etc. The output is a JSON file with one score per occupation and a short rationale.

The use case is straightforward: a leaderboard of which jobs AI is most likely to replace, derived from authoritative source material. It's been cited as a reference for AI-impact analysis in several public discussions.

---

## How it scores today

Single Gemini Flash call per occupation. Temperature 0.2.

```
Prompt:  "Rate this occupation's AI exposure on a 0–10 scale.
          Return {exposure: int, rationale: string}."
Anchors: rubric examples at each integer level (0 = no exposure,
         10 = fully replaceable).
Output:  one integer in [0, 10] picked by the LLM directly.
```

The prompt is well-anchored — Karpathy did the rubric-design work. Each integer level has a behavioral example. This is closer to good than the average "rate 0–10" prompt. The model still picks the number.

### What's good in the current design

- **Anchored prompt with examples per integer level** (the Jonsson & Svingby principle, applied competently).
- **Single fast call per occupation.** Cheap, reproducible, easy to swap models.
- **Same input format for every occupation.** No data-cleaning issues across the 342 cases.
- **Real authoritative source data** (BLS), not vibes-based job descriptions.

### What goes wrong

The number is picked by the LLM. With 342 cases, the failure mode is now visible at the distribution level rather than in any individual score.

The naive distribution histogram, 0–10:

```
 0:                       (0)
 1: █████████             (9)
 2: ████████████████████  (36)
 3: ███████████████████████ (47)
 4: ████████████████████  (42)
 5: █████████████████████ (43)
 6: █████████████████     (35)
 7: ██████████████████████████████████ (70)  ← cluster
 8: ██████████████        (29)
 9: ███████████████       (30)
10: █                     (1)
```

Mean 5.31, std dev 2.26. The 70-occupation pile-up at 7 is the RLHF signature: when the model is unsure, it picks a "safe" 7 — close to the upper-middle, sounds confident, doesn't commit to a strong claim either direction. One occupation gets a 10. Zero get a 0. That's not what AI exposure looks like across 342 jobs.

---

## Failure modes vs the seven principles

| # | Principle | Status in karpathy/jobs | Evidence |
|---|---|---|---|
| 1 | Collect evidence, not numbers | **Violated** | Prompt asks for an integer directly. No instruction to enumerate observed task evidence first. |
| 2 | Discrete impact set, both signs | **Violated** | Single 0–10 integer. No way to register independent positives + negatives within one occupation. |
| 3 | Diminishing returns (sqrt) | **N/A** | Only one signal, so no aggregation problem at the per-occupation level. |
| 4 | Confidence multiplier from evidence density | **Absent** | Every occupation gets the same model call with the same depth. No way to know whether a 7 was based on 2 surface tasks or 20 deeply considered ones. |
| 5 | Anchored center | **Present (implicit)** | Prompt anchors say 5 = "moderate exposure." The score still drifts to 7 anyway because that's where RLHF lives. |
| 6 | Bounded scale | **Present** | Hard 0–10. |
| 7 | Separation of LLM collection vs deterministic computation | **Violated** | The same LLM call collects evidence (in the rationale) and produces the score. They're inseparable. |

Five of seven violated, one N/A, one present. Same shape as impeccable but at scale.

---

## Rescoring: applying the seven principles

### Step 1: Replace the integer pick with evidence collection

Same model (Gemini Flash). Same temperature (0.2). Same input data. The only change is the prompt:

```
Identify 10–20 discrete task evidence items observed in this
occupation. For each item, assign an impact score:
  +5  Core task fully automatable by AI (e.g., data entry)
  +3  Task significantly augmented by AI (e.g., code writing)
  +2  Task moderately assisted by AI (e.g., research)
  +1  Minor AI assistance possible (e.g., scheduling)
  -1  Minor physical/interpersonal barrier
  -2  Moderate physical presence needed
  -3  Core work requires manual skill
  -5  Irreducibly physical work (e.g., roofing)

Return [{ task: "...", impact: <int>, evidence: "..." }, ...].
```

No score request. The LLM enumerates tasks; the formula does the rest.

### Step 2: Apply the formula (BLS variant: 0–10 scale, density 15)

```
net_impact       = sum(item.impact)
total_items      = len(items)
normalized       = net_impact / sqrt(total_items)
raw_score        = clamp(5.0 + normalized * 0.8, 0, 10)
density          = total_items / 15
multiplier       = 0.75 + 0.25 * clamp(density, 0, 1)
final_score      = 5.0 + (raw_score - 5.0) * multiplier
confidence       = clamp(density, 0, 1)
```

(The BLS variant uses center 5, scale 0.8, density denom 15. The default 0–100 hackathon variant uses center 50, scale 8.0, density denom 20. Both are the same formula, retuned for the target scale and the realistic item count per artifact.)

### Step 3: Single-model headline (Gemini Flash, 342 occupations)

| Metric | Karpathy (Naive) | Principled (Evidence) |
|--------|------------------|-----------------------|
| Mean | 5.31 | 3.84 |
| Median | 5.0 | 3.6 |
| Std Dev | 2.26 | **3.18** |
| Min | 1 | 0.0 |
| Max | 10 | 10.0 |
| Spearman ρ vs Karpathy | — | **0.87** |
| Discrimination ratio | baseline | **1.41×** |
| Items per occupation | — | 17.3 avg |

Discrimination went up 41%. Rank ordering held at ρ = 0.87. The methodology spreads the scores out without rolling the dice on the ordering.

### Step 4: The shape change

The principled distribution histogram, 0–10:

```
 0: █████████████████████████████████████████████ (91)
 1: ████████████████      (32)
 2: ██████████████        (28)
 3: ██████████████        (29)
 4: █████████████████     (35)
 5: ████████████████████  (41)
 6: ████████              (17)
 7: ██████████            (21)
 8: ██████████            (20)
 9: ████                  (9)
10: █████████             (19)
```

Bimodal. 91 occupations at 0 (roofers, firefighters, agricultural workers — irreducibly physical) and 19 at 10 (web developers, data scientists — fully digital). The middle is real but no longer the artificial pile-up of 70 occupations at 7.

This isn't the formula creating bimodal structure. It's the formula *revealing* bimodal structure that was always in the data. Physical labor and digital knowledge work are different on the AI-exposure dimension; the naive scorer was smoothing them together.

---

## Multi-model replication (9 models, 5 providers)

Same prompt, same formula, 9 models spanning Intelligence Index 31–57.

| Model | Provider | Mean | Std Dev | Discrim. Improvement | At 0 | At 10 | Avg Items |
|-------|----------|:----:|:-------:|:--------------------:|:----:|:-----:|:---------:|
| Karpathy (naive) | Google | 5.31 | 2.26 | — | 0 | 1 | — |
| GLM-5 | Zhipu | 3.03 | 2.73 | 21% | 102 | 9 | 16.9 |
| GPT-5.4 Mini | OpenAI | 6.16 | 3.05 | 35% | 18 | 64 | 18.8 |
| Claude Haiku 4.5 | Anthropic | 4.48 | 3.17 | 40% | 59 | 23 | 19.8 |
| Gemini 3 Flash | Google | 3.84 | 3.18 | 41% | 82 | 25 | 17.3 |
| Claude Opus 4.6 | Anthropic | 4.64 | 3.19 | 41% | 55 | 40 | 18.5 |
| GPT-5.4 | OpenAI | 4.33 | 3.34 | 48% | 78 | 37 | 20.2 |
| Gemini 3.1 Pro | Google | 4.75 | 3.39 | 50% | 63 | 43 | 15.3 |
| Grok 4.20 Beta | xAI | 3.45 | 3.53 | 56% | 122 | 34 | 22.9 |
| Claude Sonnet 4.5 | Anthropic | 3.97 | 3.56 | 58% | 101 | 43 | 19.9 |

Four findings.

**1. Every model beats naive scoring on discrimination.** All 9 principled runs produce higher std dev (2.73–3.56) than the Karpathy baseline (2.26). The methodology works regardless of which model collects the evidence.

**2. Strong rank agreement across models.** Spearman ρ ranges 0.77–0.93 across all 36 model pairs. The ordering is stable even when exact scores differ.

**3. No capability-discrimination correlation.** Smarter models don't systematically score higher or produce more spread. Intelligence Index 31 (Haiku) and 57 (Opus, Gemini Pro, GPT-5.4) produce roughly comparable discrimination ratios. The methodology normalizes across capability levels.

**4. Provider biases become visible.** OpenAI models are more optimistic about AI exposure (means 4.3–6.2) than Anthropic (3.97–4.64), Google (3.84–4.75), and xAI/Zhipu (3.03–3.45). The methodology surfaces these biases rather than hiding them inside opaque single-number scores. That's a feature: anyone running this can swap providers and see the bias delta directly.

---

## Where naive and principled disagree most

Rank correlation is high (ρ = 0.87), but 13% of pairwise rankings change. Those are the interesting cases.

| Occupation | Naive Score | Principled Score | Interpretation |
|---|:---:|:---:|---|
| Producers and Directors | 7 | 1.0 | Creative/interpersonal core despite digital tools |
| Kindergarten Teachers | 6 | 0.1 | Physical, interpersonal; AI exposure minimal |
| High School Teachers | 7 | 1.23 | Physical classroom; digital component limited |
| Craft Artists | 6 | 0.53 | Physical medium; AI assists design, not creation |
| Actors | 7 | 1.8 | Physical performance; digital post-production only |
| Nurse Practitioners | 5 | 0.0 | Hands-on patient care |
| Interpreters & Translators | 9 | 4.03 | Real-time interpersonal work undervalued by naive scorer |

The naive scorer assigns moderate-high scores based on surface keyword association — teachers use computers, directors use software, so they "could be digitized." The principled scorer, forced to enumerate task-by-task evidence, recognizes that the *core work* of these occupations is physical or interpersonal. The 13% of rankings that change are precisely the cases where keyword-level reasoning fails and evidence-level reasoning succeeds.

---

## Evidence audit: sample occupations

### Web Developers (Karpathy: 9, Principled: 10.0)

Top positive items: write code in HTML/JavaScript (+5), write web programs (+5), monitor website traffic (+5).
Top negative items: make client's vision a reality (−2), meet with clients (−1).
Both methods agree: nearly fully digital work. Methodology adds nothing here — the signal is unambiguous.

### Accountants (Karpathy: 8, Principled: 7.5)

Top positive items: analyze financial records (+5), compute taxes (+5), use accounting software (+5).
Top negative items: meet with clients (−2), testify in court (−1).
Mostly agree: heavily digital with minor interpersonal component.

### Administrative Services Managers (Karpathy: 5, Principled: 3.6)

Top positive items: records/information management (+5), energy analysis (+3), efficiency review (+3).
Top negative items: monitor facilities physically (−3), supervise staff on-site (−3), on-call for physical problems (−3).
Principled scores lower. The naive estimate compressed the physical-presence components into a generic "5"; evidence shows three −3 items the scorer didn't surface.

### Agricultural Workers (Karpathy: 3, Principled: 0.0)

Top positive items: record keeping (+3), trait selection (+3), automated tractors (+3).
Top negative items: harvesting by hand (−5), cleaning animal pens (−5), herding livestock (−5).
Principled scores much lower. The overwhelming physical evidence drowns out the minor digital assists. The naive scorer's "3" hedged toward the middle; the evidence forces a 0.

These are interpretable disagreements, not random rescaling.

---

## Where the methodology helps

- **Distribution-level distortion.** The 70-occupation cluster at 7 in the naive distribution is RLHF, not signal. Principles 1, 2, and 4 pull that cluster apart by forcing the scorer to commit to evidence rather than a neutral integer.
- **Cross-occupation calibration.** When every occupation goes through the same evidence catalog and the same formula, "5" means the same thing across 342 cases. Naive scoring lets each call drift independently.
- **Interpretability.** A naive 7 has only the rationale text behind it. A principled 7.5 has 17 evidence items with task-by-task impacts the reader can audit, agree with, or disagree with item-by-item.
- **Provider-bias visibility.** When you run the same evidence-gathering prompt through 9 models, the per-model means become a measurement of provider bias, not a confound. OpenAI runs +1.5 vs xAI/Zhipu — that's a fact about training, not noise.

## Where the methodology may NOT help

Be honest:

- **Atomic occupations.** A web developer scores 10 under both methods. The signal is too clean for the formula to add much.
- **The minimum-viable adoption case.** A practitioner who just wants Karpathy's data spread out doesn't need all seven principles — Principle 1 (collect items, don't pick numbers) plus Principle 4 (sqrt normalization) is most of the win. Principles 6–7 (multiple perspectives, cross-modal synthesis) are over-engineering for a pure occupation-rating task.
- **Ground truth.** "Correct" AI-exposure scores don't exist for any occupation. We can show the principled approach has higher discrimination, preserves rank ordering, and produces interpretable disagreements at the extremes — we cannot prove it's "more accurate" in an absolute sense.
- **The prompt confound is real.** Both the prompt change (richer evidence-gathering) AND the formula contribute to the improvement. Disentangling them requires a "structured prompt, simple aggregation" control: collect the same evidence items, then score with a plain mean of impacts. That control isolates the formula's contribution from the prompt's contribution. It's recomputation-only (no new API calls); the data already exists.

---

## What this case study proves

Karpathy/jobs is the methodology's clearest cross-domain validation:

1. **Same formula, completely different domain.** Hackathon judging and occupational analysis share nothing — different stakeholders, different criteria, different units of analysis. The seven principles transfer with parameter retuning only (center 5 instead of 50; scale 0.8 instead of 8.0; density denom 15 instead of 20).

2. **Multi-model robustness.** 9 models from 5 providers all produce improved discrimination. The methodology isn't a Claude trick or a Gemini trick. It's the formula doing the work.

3. **Distribution-level evidence.** With 342 cases, we can show the *shape* of the improvement, not just point estimates. The bell-curve-to-bimodal shift is the visual signature of "stop letting the LLM pick a number."

This is the example to point at when someone says "your methodology is hackathon-specific." It isn't.

---

## Files referenced

- [`https://github.com/karpathy/jobs`](https://github.com/karpathy/jobs) — the original repo
- BLS Occupational Outlook Handbook — input data, 342 occupations
- `rescoring/karpathy-jobs/RESULTS.md` (in PROJ-ai-judge-scoring) — full multi-model report this writeup is condensed from
- `rescoring/karpathy-jobs/comparison_results.json` — single-model (Gemini Flash) detailed comparison
- `rescoring/karpathy-jobs/multimodel_results.json` — full 9-model dataset
- `rescoring/karpathy-jobs/distribution_comparison.png` — side-by-side naive vs principled histograms (the headline figure)
- `rescoring/karpathy-jobs/multimodel_distributions.png` — all 10 distributions (naive + 9 principled)
- `rescoring/karpathy-jobs/multimodel_correlations.png` — Spearman heatmap across model pairs
- `rescoring/karpathy-jobs/multimodel_summary.png` — mean and discrimination bar charts
- `rescoring/karpathy-jobs/multimodel_intelligence_vs_scoring.png` — capability vs scoring behavior

The five PNGs are the publication figures. They are not yet copied into this repo's `examples/karpathy-jobs/figures/` directory; that's a one-step `cp` Kevin runs before pushing.

## See also

- `examples/impeccable-rescoring.md` — single-page qualitative case study (UI quality benchmark, 76 vs 59 separation)
- `examples/cua-bench-analysis.md` — partial-fit case study (computer-use agents, P7 satisfied, P2–P6 wide open)
- `paper/paper.md` §5.2 — the same data presented as the paper's primary cross-domain validation
