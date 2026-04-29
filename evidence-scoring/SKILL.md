---
name: evidence-scoring
description: Score anything — a draft, a build, a submission, a candidate, a vendor — using the seven-principle methodology from "Don't Let the LLM Pick a Number." The LLM never picks the score; it collects discrete signed evidence items and a formula computes the number. Use this skill whenever the user wants to evaluate something rigorously, build a custom scoring rubric, replace a vague 0-10 LLM judge, or set up reproducible scoring across runs. Triggers on phrases like "score this", "build me a rubric", "evaluate this", "judge X across multiple dimensions", "stop my LLM from picking 7 every time", or any request that smells like rubric-based scoring done seriously.
license: MIT
---

# Evidence Scoring — the seven-principle methodology, generic

The user brings the domain. You bring the structure. Together you produce a defensible 0–100 score whose number is computed from evidence, not chosen by the LLM.

This skill is the lifted methodology from the paper *Don't Let the LLM Pick a Number*. Its sister skills (`what-works-feedback-judge`, `hackathon-judge`) are pre-baked applications. Use this one when nothing pre-baked fits.

## When to use this

- The user wants to score something but every off-the-shelf rubric is too generic.
- An existing LLM judge is producing 7-out-of-10s no matter the input.
- The user wants reproducibility across runs and reviewers.
- The user is willing to do a 5-minute setup conversation in exchange for stable scores.

If the user just wants quick feedback on a draft, use `what-works-feedback-judge`. If they want to score code submissions with optional demo video, use `hackathon-judge`. This skill is the toolkit underneath both.

## The seven principles (memorize these)

1. **Separate observation from scoring.** The LLM finds evidence. A formula, not the LLM, produces the score.
2. **Discrete signed impact items.** Every observation gets one of `{+5, +3, +2, +1, -1, -2, -3, -5}`. No 0-10 picks. No "pretty good." Forces commitment.
3. **Diminishing returns.** `normalized = net_impact / sqrt(total_items)`. The 40th item adds less than the 4th. Evidence farming is punished.
4. **Density-weighted confidence.** Confidence = how much evidence the scorer found, not how sure the scorer feels. Sparse runs are visibly low-confidence.
5. **Anchored center.** Sparse-evidence runs regress toward 50. The multiplier never exceeds 1.0 — high evidence confirms but never amplifies beyond raw.
6. **Bounded scale with self-check.** Scores live in `[0, 100]`. Across criteria, the spread must be ≥ 20. If the spread is smaller, the evaluator wasn't discriminating.
7. **Separation of LLM and deterministic computation.** Independent passes by different model families collect evidence. Math, not the LLM, combines them.

## Two application patterns

You will pick one based on the user's needs. Both use the same per-criterion formula; they differ in how many criteria run.

### Pattern A — Pooled (one bucket, one score)

For simple checkers: one scope, one final number. Examples: "is this draft ready to ship?", "is this PR safe to merge?", "is this candidate worth a phone screen?".

```
items[]                            # all evidence in one pool
net_impact   = sum(item.impact)
total_items  = len(items)
normalized   = net_impact / sqrt(total_items)
raw          = clamp(50 + normalized * 8.0, 0, 100)
density      = total_items / 20
multiplier   = 0.75 + 0.25 * clamp(density, 0, 1)   # never > 1.0
final        = round(50 + (raw - 50) * multiplier)
confidence   = clamp(density, 0, 1)
```

`what-works-feedback-judge` is a pooled skill (Working / Not working / Missing / Confusing — four labeled buckets that score as one pool).

### Pattern B — Per-criterion matrix (5×5 or N×M)

For benchmarks: every dimension scored independently, then weighted-averaged. Examples: hackathon submissions, vendor evaluations, candidate scorecards, model benchmarks.

```
# For each criterion c:
per_criterion[c] = pooled_formula(items_in_c)

# Across criteria:
overall_score      = round(sum(c.final * c.weight for c in criteria))
overall_confidence = min(c.confidence for c in criteria)
self_check_span    = max(c.final) - min(c.final)         # must be >= 20
```

Default 5×5 matrix when the domain doesn't suggest something specific:

| | criterion_1 | criterion_2 | criterion_3 | criterion_4 | criterion_5 |
|---|---|---|---|---|---|
| **requester** | items… | items… | items… | items… | items… |
| **sme** | items… | items… | items… | items… | items… |
| **end_user** | items… | items… | items… | items… | items… |
| **production** | items… | items… | items… | items… | items… |
| **adversary** | items… | items… | items… | items… | items… |

Customize when the domain demands. A code review benchmark might use perspectives `author / reviewer / future_maintainer / on_call / adversary`. A pitch evaluation might use `customer / investor / competitor / regulator / engineer`. Forcing five perspectives is the principle, not the specific labels.

## The setup conversation (5 min)

Before scoring anything, walk through this with the user. Capture answers as you go.

1. **What are we scoring?** (one sentence — "the new homepage hero", "this Next.js refactor", "this Series-A pitch deck", etc.)
2. **Pooled or matrix?** (One score? → pooled. Multiple dimensions you want to see separately? → matrix.)
3. **If matrix: what are the criteria?** Aim for 3–5 unless they have a strong reason for more. Each one should be scorable independently — if two criteria can't be separated cleanly, merge them.
4. **If matrix: what are the perspectives?** Use the default 5 unless the domain has obvious better ones. Forcing multiple stakeholder viewpoints is the principle.
5. **What do +5 and −5 look like in this domain?** Get one concrete example of each per criterion. The anchors are the calibration. Vague anchors → vague scores.
6. **Weights?** Only ask if matrix. Default-equal is fine if the user can't articulate weights. Write them out: must sum to 1.0.
7. **What planted traps exist (if any)?** A "trap" is something the scorer is supposed to catch and penalize. Fake records in a dataset, jurisdiction violations in a legal doc, hallucinated facts in a research summary, single-API-call-as-AI in a "novel AI" pitch. List them; assign expected impact (`+5 if caught, -5 if normalized` is the canonical pattern).

Show the user the catalog before scoring. Iterate until they say "yes, that matches the work."

## Collecting evidence

Now run the scorer. For each item:

- **Description** — short, specific, falsifiable. Not "good UX" — "user can recover from a deleted item with one click at app/items/page.tsx:84".
- **Evidence** — file:line, timestamp, page number, quote. The reader must be able to verify.
- **Impact** — exactly one of `{+5, +3, +2, +1, -1, -2, -3, -5}`.
- **Cell** (if matrix) — which perspective × criterion this item belongs to.

Hard rules:

- **5 items per cell maximum.** Anything past 5 is padding; sqrt normalization gives diminishing returns anyway.
- **3 items per cell minimum target.** Fewer than 3 means you didn't look hard enough.
- **No invented evidence.** If you didn't observe it, don't list it. Sparse evidence is honest signal — fabricated evidence corrupts the formula.
- **Impact must come from the set.** No `+4`. No `-2.5`. The discrete set is what removes the LLM-pick-a-number anchor; if you let yourself off the hook, you'll drift back to picking 7.

## Computing the score

Run the formula. Show your math — the user needs to see the numbers, not trust the black box.

```
net_impact <X>, total_items <N> → normalized <V>
raw_score <R>, density <D> → multiplier <M>
final_score <S>, confidence <C>
```

Then add 1–2 plain sentences explaining what specifically pushed the score up or down. The math + the prose together = a defensible report.

If matrix: also report per-criterion scores, the weighted overall, the overall confidence (= min across criteria), and whether the self-check passed (span ≥ 20). If the self-check fails, the evaluator was not discriminating; flag it explicitly and offer to re-examine the items.

## When something doesn't fit

- **The user wants pairwise comparisons, not absolute scores.** That's a different methodology (see `lechmazur/writing-style`). Pairwise can complement absolute scoring as a diagnostic, but don't replace the formula with it.
- **The user wants a sub-score below 0 or above 100.** Don't. Clamp. The bounded scale is principle 6 for a reason.
- **The user has fewer than 3 items per cell.** Either look harder, or accept the low confidence and report it honestly. Density is signal — don't paper over it.
- **All scores cluster within a 20-point band.** Self-check failure. Re-examine items. The evaluator was either soft or unable to distinguish — both are surfaceable as feedback.

## Final report format

```
# <subject> — Evidence Scoring report

**Final: <overall_score>/100** — confidence <overall_confidence>, self-check <pass/fail>

## Per criterion
| criterion | final | conf | net | items | weight |
|---|---|---|---|---|---|
| brief_fidelity         | 78 | 1.0 | +18 | 22 | 0.30 |
| trap_handling          | 92 | 0.85 | +24 | 17 | 0.25 |
| production_correctness | 41 | 0.7 | -10 | 14 | 0.20 |
| domain_judgment        | 60 | 0.6 |  +4 | 12 | 0.15 |
| long_horizon_carry     | 58 | 0.5 |  +1 | 10 | 0.10 |

## Top items
- (+5, requester × brief_fidelity) — <description, evidence>
- (+5, adversary × trap_handling)  — <description, evidence>
- (-5, production × production_correctness) — <description, evidence>
- ...

## Math (show your work)
- brief_fidelity: net +18, items 22 → normalized +3.84 → raw 80.7, density 1.10 → multiplier 1.0 → final 81
- trap_handling: ...

## Why this score
1–3 paragraphs. Top drivers in plain prose. Where the evidence was thin. What the self-check told us.
```

## Reference

- Paper: `paper/paper.md` in this repo (CodefiLabs/pickanumber)
- Worked rescoring example: `examples/impeccable-rescoring.md` — what changes when an existing LLM-judged benchmark drops the LLM-picks-a-number step
- Companion analysis: `examples/cua-bench-analysis.md` — when the methodology partially fits (deterministic-reward benchmarks)
- Sister skills: `what-works-feedback-judge` (pooled, 4-bucket idea-readiness), `hackathon-judge` (per-criterion, project submissions with optional video)

## Done

When the report lands, stop. Don't volunteer recommendations. The score plus the top items plus the math is the deliverable; what the user does with it is their call.
