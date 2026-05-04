---
name: what-works-feedback-judge
description: Evaluate any productive-output idea (draft, spec, memo, plan, pitch, concept) using a 4-question evidence-based feedback loop — What's working? What's not working? What's missing? What's confusing? — and produce a 0-100 readiness score plus four grouped action lists (Keep / Fix / Add / Clarify). Use this skill whenever the user shares an idea, draft, or concept and asks for feedback, evaluation, critique, or wants to know whether something is ready to ship. Also triggers on phrases like "judge this", "score this idea", "what do you think of...", "give me feedback on...", "is this any good?", "is this ready?", "what should I change?", "rate this", "critique this", or any time the user is iterating on a piece of output and wants structured input. Even when the user doesn't explicitly ask for scoring, surface this as a reliable refinement loop. Persists each pass to ./_judge/ as JSON keyed by idea slug, so iterations accumulate into measurable progress.
license: MIT
---

# What-Works Feedback Judge

A skill that pairs a four-question feedback frame (Working / Not working / Missing / Confusing) with the evidence-based scoring methodology from *Don't Let the LLM Pick a Number*. The LLM never picks a score directly. It collects discrete evidence items with bounded magnitudes in each bucket. Math computes the readiness score. The user gets a number plus four grouped action lists.

## Why this exists

Most LLM feedback is either vague praise ("this is great!") or unstructured critique. Both waste the user's time. This skill forces:

- **Specificity.** Each bucket demands concrete items with discrete magnitudes. No hand-waves.
- **Balance.** The four-bucket structure prevents pure-praise or pure-critique answers.
- **Depth via density.** A confidence multiplier penalizes shallow critique — the formula already knows that 3 evidence items isn't enough engagement to be confident in a verdict.
- **Measurability.** When the user re-runs after edits, the v1 → v2 score delta tells them whether the revision actually moved the needle.

The methodology comes from the paper *Don't Let the LLM Pick a Number*: models are unreliable at picking numeric scores directly, but reliable at collecting bounded evidence items. Math turns the items into a defensible number.

## When to trigger

Trigger this skill whenever the user shares any productive-output idea and wants feedback. This includes:

- Drafts (LinkedIn posts, emails, scripts, specs, blog drafts)
- Concepts (product ideas, strategy moves, positioning, value props)
- Plans (project plans, roadmaps, schedules, agendas)
- Content (articles, talking points, pitches, decks)
- Decisions (should we ship this, should we hire here, should we pivot)

Trigger phrases (non-exhaustive): "judge this", "score this", "what do you think of...", "give me feedback on...", "is this any good?", "is this ready?", "what should I change?", "rate this idea", "critique this".

If the user is iterating on output and you sense they want structured input, offer this skill explicitly: "Want me to run this through the what-works feedback judge?"

## The protocol

Work through the four buckets **in this exact order**: Working → Not working → Missing → Confusing. Each bucket has its own allowed magnitude set. After each bucket, recompute the cumulative score and show a one-line readout so the user watches the score move through the analysis.

### Bucket 1: Working (positive evidence)

Allowed magnitudes: **+1, +2, +3, +5**

Find what's working — concrete strengths to keep doing or do more of. Each item should be a short, specific observation about the work, not generic praise. Aim for 3–7 items.

Magnitude guidance:

- **+5** = exceptional. This is the heart of why the idea works. Reserve for genuinely standout strengths.
- **+3** = strong. Materially valuable strength, would be missed if removed.
- **+2** = solid. Contributing positively, well-executed.
- **+1** = nice touch. Minor positive, would notice it if it were gone.

The reason high values are gated: if everything scores +5, nothing does. Calibration discipline is what makes the final score meaningful.

### Bucket 2: Not working (negative evidence)

Allowed magnitudes: **−1, −2, −3, −5**

Find what's not working — concrete flaws, friction points, errors, or weak spots. Be specific about what and where. Aim for 3–7 items.

Magnitude guidance:

- **−5** = critical flaw. Could sink the idea. Must be fixed before shipping.
- **−3** = significant problem. Should be fixed; degrades the work materially.
- **−2** = noticeable issue. Worth addressing for polish.
- **−1** = minor friction. Improves the work but not a blocker.

### Bucket 3: Missing (severity-scored gaps)

Allowed magnitudes: **−1, −2, −3, −5**

Find what's missing — pieces that should be there but aren't. Score by severity using the same negative scale as Not working. Each item is implicitly tagged "add" in the final action list. Aim for 2–5 items.

### Bucket 4: Confusing (capped clarity items)

Allowed magnitudes: **−1, −2, −3** (cap intentional — no −5 allowed)

Find what's confusing — places where the idea is unclear, ambiguous, or hard to follow. Each item is implicitly tagged "clarify" in the final action list. Aim for 1–4 items.

The cap exists because confusion impedes evaluation but isn't always a real flaw. Sometimes the framing is off and the underlying idea is fine. Capping at −3 prevents clarity issues from dominating the score the way a true critical flaw should.

## Running score display

After each bucket, run `scripts/score.py` with the cumulative evidence collected so far and show a one-line readout:

```
Score after Working:     67  (3 items, density 0.15, multiplier 0.79)
Score after Not working: 52  (7 items, density 0.35, multiplier 0.84)
Score after Missing:     44  (10 items, density 0.50, multiplier 0.88)
Final score:             46  (12 items, density 0.60, multiplier 0.90)
```

This lets the user watch the score climb in Working, drop as criticism surfaces, and settle at the final number. The density and multiplier hints help them understand WHY the score moved the way it did — sparse evidence pulls scores toward 50 (the "not enough signal to be confident" anchor).

To compute the running score, write the cumulative evidence to a temp JSON file and run:

```bash
python3 scripts/score.py --input /tmp/judge-evidence.json
```

Or pipe via stdin:

```bash
echo '{"working":[{"value":3,"text":"..."}], "not_working":[], "missing":[], "confusing":[]}' \
  | python3 scripts/score.py
```

## Persistence

After collecting all four buckets and computing the final score, save the result to `./_judge/<slug>.json` (relative to the current working directory). The slug is derived from the idea title (kebab-case, lowercase, no special characters). If a file already exists for this slug, append a new pass to the existing `passes` array — that's how iterative re-runs accumulate into measurable progress.

To save:

```bash
python3 scripts/score.py --save \
  --slug agent-hq-pricing \
  --title "Agent HQ pricing strategy" \
  --summary "First pass — initial concept" \
  --input /tmp/judge-evidence.json
```

Override the persistence directory with the `JUDGE_DIR` environment variable when needed (useful for centralizing across projects, or for testing in a temp directory).

JSON shape:

```json
{
  "id": "agent-hq-pricing",
  "title": "Agent HQ pricing strategy",
  "created": "2026-04-29T15:32:00Z",
  "passes": [
    {
      "version": 1,
      "timestamp": "2026-04-29T15:32:00Z",
      "summary": "First pass — initial concept",
      "evidence": {
        "working":     [{"value": 3, "text": "Tier ladder maps cleanly to user growth"}],
        "not_working": [{"value": -3, "text": "Free tier eats paid tier value"}],
        "missing":     [{"value": -5, "text": "No annual discount mechanism"}],
        "confusing":   [{"value": -2, "text": "Per-seat vs per-org unclear"}]
      },
      "scores": {
        "net_impact": -7,
        "total_items": 4,
        "normalized": -3.5,
        "raw_score": 22.0,
        "density": 0.2,
        "multiplier": 0.80,
        "final": 28
      }
    }
  ]
}
```

## Final report format

After persistence, present the final report in this structure:

```
# What-Works Feedback: <idea title>

**Score: <N>/100** — pass <V>, <total_items> items, <confidence> confidence

## Score progression
Working: <S1> → Not working: <S2> → Missing: <S3> → Final: <S4>

## Keep doing (Working)
- (+5) <item text>
- (+3) <item text>
- ...

## Fix (Not working)
- (-5) <item text>
- ...

## Add (Missing)
- (-5) <item text>
- ...

## Clarify (Confusing)
- (-3) <item text>
- ...

Saved to ./_judge/<slug>.json (pass <V>)
```

If this is pass 2+ on the same idea, also include a "What changed since pass <V−1>" section: items resolved, new items found, score delta. Use the helper's `--load` flag to read prior passes:

```bash
python3 scripts/score.py --load --slug agent-hq-pricing
```

## Calibration notes

Stay disciplined about magnitudes. The most common failure mode is grade inflation — reaching for +5/−5 too easily. Reserve them for items that are genuinely critical. The formula's sqrt normalization means total_items also affects the score, so padding with trivial items is counterproductive: it drops normalized_impact even when net_impact is positive.

The density multiplier rewards depth. If your evidence list feels thin (under 8 items total across all buckets), push yourself to find 2–3 more — but only real items, not filler. The multiplier maxes out at 1.0 with 20 items; below that, the score regresses toward 50 to reflect lower confidence.

If the user disagrees with a specific item or magnitude, that's the skill working — surface-level prose feedback hides those calibration disagreements. Adjust the item, recompute, and continue.

**If the score barely moves between revisions** — the user revises substantially and gets the same readiness number twice — that's the operational signature of a model in `PICKS_A_NUMBER` regime on this task. Run `calibration-probe` to confirm. If it lands PICKS_A_NUMBER or JITTERY, switch models; the methodology cannot rescue intrinsically weak signal.

## Reference

- Canonical formula: `references/formula.md`
- Helper script: `scripts/score.py` — handles formula computation and JSON persistence
- Output directory: `./_judge/` (relative to cwd) — created automatically on first save. Override with the `JUDGE_DIR` environment variable.
- Sister skills: `calibration-probe` (preflight regime classifier — run when scores stop moving across revisions), `evidence-scoring` (generic methodology), `hackathon-judge` (project-submission scoring)
- Origin paper: *Don't Let the LLM Pick a Number* — `paper/paper.md` in the CodefiLabs/pickanumber repo
