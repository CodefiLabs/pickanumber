# Scoring Formula Reference

Mirrors the formula in the paper *Don't Let the LLM Pick a Number*. This file is bundled with the skill so the skill is self-contained — `scripts/score.py` implements exactly what's described here.

## Allowed magnitudes by bucket

| Bucket       | Allowed values            | Tag in action list |
|--------------|---------------------------|--------------------|
| working      | +1, +2, +3, +5            | Keep doing         |
| not_working  | −1, −2, −3, −5            | Fix                |
| missing      | −1, −2, −3, −5            | Add                |
| confusing    | −1, −2, −3 (no −5)        | Clarify            |

The confusing cap is intentional: confusion impedes evaluation but isn't always a real flaw, so it shouldn't be able to dominate the score the way a true critical defect can.

## The formula

```
net_impact     = sum(all_evidence_values)
total_items    = count(all_items)

normalized     = net_impact / sqrt(total_items)         # 0 if total_items == 0
raw_score      = clamp(50 + normalized * 8.0, 0, 100)

density        = total_items / 20
multiplier     = 0.75 + 0.25 * clamp(density, 0, 1)     # capped at 1.0

final_score    = round(50 + (raw_score - 50) * multiplier)
confidence     = clamp(density, 0, 1)
```

### Why each piece

- **sqrt normalization** — diminishing returns. The 40th item contributes less than the 4th. Prevents pure-volume gaming.
- **8.0 scale constant** — calibrated so normalized_impact of +5.0 lands at raw_score 90 (the "exceptional" tier).
- **density multiplier** — regression toward 50 (the "average / not enough signal" anchor) when evidence is sparse. Multiplier maxes at 1.0; it confirms a score, never amplifies.
- **clamp to 0–100** — keeps the output interpretable as a percentage-style readiness score.

## Calibration anchors

| normalized_impact | raw_score | Tier                                  |
|-------------------|-----------|---------------------------------------|
| +5.0              | 90        | Exceptional (5–10% of submissions)    |
| +2.5              | 70        | Above average                         |
| 0.0               | 50        | Average                               |
| −2.5              | 30        | Below average                         |
| −5.0              | 10        | Poor                                  |

## Worked examples

### A: Strong idea with rich evidence

```
evidence: 25 items, net_impact = +25
normalized = 25 / sqrt(25) = 5.0
raw_score  = 50 + 5.0 * 8.0 = 90
density    = 25 / 20 = 1.25 -> clamped to 1.0
multiplier = 0.75 + 0.25 * 1.0 = 1.0
final      = round(50 + (90 - 50) * 1.0) = 90
```

Strong score, full confidence.

### B: Strong idea with sparse evidence

```
evidence: 4 items, net_impact = +25
normalized = 25 / sqrt(4) = 12.5
raw_score  = 50 + 12.5 * 8.0 = 150 -> clamped to 100
density    = 4 / 20 = 0.2
multiplier = 0.75 + 0.25 * 0.2 = 0.80
final      = round(50 + (100 - 50) * 0.80) = 90
```

Even though raw score maxed out, sparse evidence pulled it back. The formula rewards depth of analysis.

### C: Average idea

```
evidence: 20 items, net_impact = 0
normalized = 0
raw_score  = 50
density    = 1.0
multiplier = 1.0
final      = 50
```

Confident neutral verdict.

### D: Weak idea with abundant evidence

```
evidence: 25 items, net_impact = -15
normalized = -15 / sqrt(25) = -3.0
raw_score  = 50 + (-3.0 * 8.0) = 26
density    = 1.25 -> clamped to 1.0
multiplier = 1.0
final      = round(50 + (26 - 50) * 1.0) = 26
```

High confidence in a low score.

## Score-as-we-go behavior

The skill computes the score after each bucket is collected, not just at the end. Scores fluctuate during a single analysis pass:

- After Working bucket only — score will lean above 50 (positive items, no negatives yet)
- After Not working added — drops as criticism enters
- After Missing added — drops further as gaps surface
- After Confusing added — final settled score

The density multiplier is recomputed at every step too, so the score also moves as more items accumulate (sparse → dense increases the multiplier toward 1.0).

This is intended — the user watches the verdict take shape rather than receiving a black-box final number.
