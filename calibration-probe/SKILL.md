---
name: calibration-probe
description: Run a 30-second synthetic test on a candidate LLM to predict whether it's in a regime where the evidence-scoring methodology will help — BEFORE you invest in a full pipeline run. Classifies the model into one of five regimes (CALIBRATED, INFLATION_LIKELY, DEFLATION_LIKELY, PICKS_A_NUMBER, JITTERY) using a 20-item rating prompt with no ground truth. Use this skill whenever the user asks "is my LLM judge calibrated", "what regime is my model in", "should I bother with the full pipeline", "test my model before scoring", "is this model good enough for evaluation", "preflight my judge", or any time they're about to deploy LLM-as-judge and want a cheap diagnostic first. Triggers as a natural preflight before evidence-scoring, hackathon-judge, or any rubric-based scoring task. Returns a regime label plus a one-paragraph adoption recommendation.
license: MIT
---

# Calibration Probe — predict the regime before you run the methodology

A 30-second synthetic test that classifies a candidate LLM's number-picking behavior into one of five regimes, telling the practitioner whether the evidence-scoring methodology will help, hurt, or make no difference *before* they spend hours running a full pipeline.

This skill is a preflight diagnostic for the seven-principle evidence-scoring methodology from *Don't Let the LLM Pick a Number*. It is the empirical answer to the question reviewers always ask: "does this methodology always help?" The answer is: *no, but here's how to tell whether it will help on your model.*

## When to use this

- You're about to deploy an LLM-as-judge and want a cheap diagnostic first.
- You've never tested whether your specific model is reliable at scoring.
- You're comparing several candidate models and want to pick the most calibrated one.
- A practitioner asks "should I run the full pipeline or use a lighter touch?" — the probe answers that empirically, not by gut feel.
- You ran the methodology and got worse results than naive scoring; the probe diagnoses why.

If the user wants to actually score something, use `evidence-scoring`, `what-works-feedback-judge`, or `hackathon-judge`. This skill answers the *meta* question — should you bother — not the scoring question itself.

## The five regimes

Every LLM, on a given task, falls into one of these number-picking shapes:

| Regime | What it looks like | Methodology recommendation |
|---|---|---|
| **CALIBRATED** | Full scale used, both 1s/2s and 9s/10s show up, range ≥ 5 | **Lighter touch.** Principles 1, 4, 5 only. Full pipeline may over-correct. |
| **INFLATION_LIKELY** | Lots of 9s/10s, almost no 1s/2s — model only knows how to praise | **Full pipeline.** Methodology is designed for this case. Counter-bias is correctly calibrated. |
| **DEFLATION_LIKELY** | Lots of 1s/2s, almost no 9s/10s — model only knows how to criticize | **Full pipeline + reduced counter-bias.** The model is already deflating; don't pile on. |
| **PICKS_A_NUMBER** | Tight cluster around one score (range ≤ 2), can't differentiate quality | **Switch model.** The formula cannot rescue intrinsically weak signal. |
| **JITTERY** | Same item gets very different scores run-to-run (per-item std ≥ 2.5) | **Use ensembling, not methodology.** Reliability is the constraint, not calibration. |
| AMBIGUOUS | None of the above patterns are clear | **Full pipeline with audit.** Default to the conservative path. |

## The protocol

Run the probe in five steps. The whole thing takes ~30 seconds plus inference time (typically 1–3 minutes for 30 repeats on a fast model).

### Step 1 — Pick the items file

Default: `items/sentence-structure.json` (20 short prose samples spanning quality from broken fragments to carefully constructed prose). This is domain-neutral — the probe tests the *number-picking shape*, not domain knowledge. Any sufficiently capable LLM should handle sentence-structure rating competently, so observing miscalibration here is a clean signal about the model.

For domain-specific calibration testing, the user can substitute their own items file (same JSON shape — see `items/sentence-structure.json` for the format).

### Step 2 — Pick the system prompt

Default: `prompts/sentence-structure-system.md`. Defines the 1–10 scale with explicit bands and asks for a JSON response. Substitute domain-specific prompts only if the items file is also domain-specific.

### Step 3 — Run the model N times

Make N independent calls to the candidate LLM with the same system prompt and items. Default N = 30. Each call must return a JSON object with a `"scores"` array — one integer per item, in the same order as the items file.

For each call, save the result as `runs-probes/<run-name>/run-001.json`, `run-002.json`, etc. The exact JSON shape:

```json
{
  "scores": [3, 7, 2, 9, 6, 4, 10, 7, 3, 8, 5, 7, 8, 6, 2, 8, 4, 7, 9, 5],
  "summary": "Mixed quality, full scale used"
}
```

If a call fails parsing (malformed JSON, missing scores), save it with `{"parse_failed": true, "error": "..."}` so the aggregator can count failed runs.

**Why N = 30:** sufficient for stable per-item std estimates, which is what the JITTERY classifier depends on. Use N = 100 if bimodality detection is needed (a model that gives 6 OR 9 but never 7-8 on the same item — the signature of two competing internal interpretations). Use N = 10 only when you're rapidly iterating on the prompt and want a quick read.

**Temperature:** 0.7 by default. Temperature 0 collapses to mode-only and you lose the run-to-run variance signal. Temperature > 1.0 starts breaking output coherence.

### Step 4 — Run the aggregator

Once all N runs are saved, run the aggregator:

```bash
python3 scripts/aggregate.py \
  --runs-dir runs-probes/<run-name> \
  --items items/sentence-structure.json \
  --out runs-probes/<run-name>
```

This produces:
- `aggregate.json` — per-item mean/std/mode/range + across-runs distribution stats + regime label
- `REPORT.md` — human-readable summary with the regime, histogram, top-5 most variable items, and the classifier thresholds

### Step 5 — Read the regime + recommend an adoption depth

Open `REPORT.md`, read the regime label, and tell the user what to do:

- **CALIBRATED** → "Your model is in good shape. Use Principles 1, 4, 5 only — collect evidence, sqrt-normalize, regress sparse evaluations toward the mean. The full pipeline's counter-bias may over-correct on your model. Run a small naive-vs-principled comparison on 5–10 ground-truth items if you want to verify."

- **INFLATION_LIKELY** → "Your model defaults to praise. The full evidence-scoring pipeline is designed for exactly this case — it will close the gap to humans. Use the full counter-bias prompts."

- **DEFLATION_LIKELY** → "Your model defaults to criticism. The full pipeline will help, but turn DOWN the counter-bias instructions ('skeptic's eye', 'don't inflate') — they will compound the deflation."

- **PICKS_A_NUMBER** → "Your model can't differentiate quality on this task. Range ≤ 2 means it gives essentially the same number to everything. The methodology cannot rescue this. Switch models, or accept that automated scoring on this task will be unreliable."

- **JITTERY** → "Your model is unstable. The same item gets very different scores run-to-run (per-item std ≥ 2.5). Reliability is the constraint, not calibration. Use ensembling (run the model 3–5 times and average) before reaching for the methodology."

- **AMBIGUOUS** → "The probe didn't classify cleanly. Default to the full pipeline with a post-hoc audit — track positive:negative item ratio per criterion and watch for either inflation (>2:1 positive) or over-correction (>2:1 negative)."

Always include the histogram and the per-item std in your verbal summary — those are the underlying signals, not the regime label alone.

## What the regime classifier checks (in order)

The classifier evaluates conditions in this order and returns the first match. The order matters because high run-to-run variance makes the distribution-shape rules unreliable, and extreme-cluster cases must be classified as inflation/deflation before falling into PICKS_A_NUMBER.

| # | Regime | Trigger condition |
|---|---|---|
| 1 | JITTERY          | mean_per_item_std ≥ 2.5 |
| 2 | INFLATION_LIKELY | ceiling_rate ≥ 0.25 AND floor_rate < 0.05 |
| 3 | DEFLATION_LIKELY | floor_rate ≥ 0.25 AND ceiling_rate < 0.05 |
| 4 | PICKS_A_NUMBER   | range ≤ 2 (after inflation/deflation rule out the extremes) |
| 5 | CALIBRATED       | range ≥ 5 AND floor_rate ≥ 0.05 AND ceiling_rate < 0.35 |
| 6 | AMBIGUOUS        | none of the above |

Where `ceiling_rate` = fraction of all (item × repeat) ratings at the top 2 scale points (e.g., 9 or 10 on a 1–10 scale), `floor_rate` = fraction at the bottom 2 scale points, `range` = max − min across all ratings, `mean_per_item_std` = average of within-item standard deviations across repeats.

## Honest caveat — domain transfer

The probe measures *generic* number-picking on a synthetic task. A model classified CALIBRATED on sentence-structure could still inflate on your domain (hackathon submissions, code reviews, business pitches) because domain-specific positivity is in the training data.

The probe likely catches the **worst** cases — extreme inflation, extreme clustering, weak signal — and they don't go away in your domain. Probe-as-preflight is a cheap-but-imperfect signal. The most defensible flow is **probe + 10–15 ground-truth items in the deployment domain**: the probe tells you the structural shape, the domain ground truth tells you whether it transfers.

When in doubt, treat the probe as a *necessary but not sufficient* signal: a CALIBRATED model still needs domain validation, but a PICKS_A_NUMBER model is unreliable everywhere and you don't need to validate further.

## Pairing with other skills

This skill is a preflight for the others:

- **Before `evidence-scoring`**: run the probe on the candidate model. If CALIBRATED, use the lighter touch the skill describes (Principles 1, 4, 5). If INFLATION_LIKELY, run the full setup conversation. If PICKS_A_NUMBER or JITTERY, halt and switch models.
- **Before `hackathon-judge`**: run the probe on the candidate model. The skill accepts a `calibration_regime` parameter that adjusts the counter-bias strength based on the regime label.
- **Before or after `what-works-feedback-judge`**: usually overkill (the skill is single-shot, low-stakes). One useful trigger: *if the user observes the same score regardless of how much they revise their draft*, that is the operational definition of PICKS_A_NUMBER on this task — run the probe to confirm and switch models.

## Reference

- Items file format: `items/sentence-structure.json`
- Default system prompt: `prompts/sentence-structure-system.md`
- Aggregator script: `scripts/aggregate.py` — pure-math regime classifier, no API calls, no provider dependency
- Origin: Section 5.7 + Appendix E of *Don't Let the LLM Pick a Number* (`paper/paper.md` in the CodefiLabs/pickanumber repo). The paper introduces the probe as a structural-shape diagnostic and validates the regime predictions against a six-model held-out grid.

## When to skip this skill

- The user already has ground-truth scores for 50+ items in their target domain. They can compute Pearson and KS distance directly — no probe needed.
- The user is doing pairwise comparisons (Bradley-Terry style) rather than absolute scoring. The probe doesn't apply; pairwise has different reliability properties.
- The user has run the full pipeline before and trusts the model. The probe is a *first-deployment* tool, not a re-run requirement.
