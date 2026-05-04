---
name: hackathon-judge
description: Score a project submission (any code repo, optional demo video) using a four-pass evidence-based pipeline — code analysis, optional video analysis, adversarial synthesis, and mentoring feedback. Produces a 0-100 score per criterion plus structured strengths and concerns. Use this skill when judging a hackathon, demo day, internal review, vendor pilot, or any "score this submission" task that benefits from independent code-and-presentation evidence and reproducible math instead of a vibe number. Triggers on phrases like "judge this submission", "score this hackathon entry", "review this demo project", "evaluate this MVP", "rate this take-home", "is this ready to ship", or any request to score a code+pitch package against multiple criteria.
license: MIT
---

# Hackathon Judge — four-pass project scoring

Score a project submission with the methodology from *Don't Let the LLM Pick a Number*: independent passes collect bounded signed evidence; math computes the scores; a final pass turns the evidence into mentoring feedback for the team.

This skill is **generic by design** — there is nothing hackathon-specific in the math. "Hackathon" is the natural search term, but the same pipeline works for take-home interviews, demo-day judging, internal review boards, vendor pilots, and any project where someone built a thing and someone else needs to score it.

## When to use this

- A submission has both a **codebase** and an **optional demo video** (URL or transcript) — the four-pass shape gets the most value when both exist, but the skill degrades gracefully if only code is available.
- The user wants a defensible numeric score per criterion, not a vibe verdict.
- Multiple submissions need to be scored consistently (the formula is reproducible across runs and reviewers).
- The user wants the team to receive grounded mentoring feedback, not a leaderboard rank.

If the user just wants quick feedback on a draft (no codebase), use `what-works-feedback-judge`. If they want to design their own scoring rubric for a non-project domain, use `evidence-scoring`.

## The four passes

Each pass is a separate stage. They can be run together (full pipeline) or in isolation when iterating.

```
PASS 1  Code analysis           → pass1-code.json
PASS 2  Demo analysis (opt.)    → pass2-demo.json
PASS 3  Adversarial synthesis   → pass3-synthesis.json   (the scores)
PASS 4  Team feedback           → pass4-feedback.json    (mentoring report)
```

**Why separation matters.** Pass 1 reads the code without seeing the demo. Pass 2 watches the demo without seeing the code. Pass 3 synthesizes them adversarially — looking for contradictions (e.g., "demo claimed feature X works; code shows X is a stub"). If you let one pass leak into the next, you lose the cross-check that catches polish-without-substance and substance-without-polish.

## Pass 0 — Calibration preflight (recommended)

Before scoring submissions, run the `calibration-probe` skill on the candidate scoring model to determine its **regime**. The regime drives how strongly the counter-bias prompts in this skill should fire. Accept a `calibration_regime` parameter when invoking this skill (defaults to `unknown`):

| Regime | Behavior |
|---|---|
| `inflation_likely` | Run all four passes with full counter-bias prompts (the v3 default — "skeptic's eye", "two honest items > five invented", "README claims without code → negative item"). |
| `calibrated` | Run all four passes but **soften the counter-bias** — drop the explicit "skeptic's eye" instruction and the "don't inflate" override. The model already discriminates; pushing harder produces deflation. |
| `deflation_likely` | Same as `calibrated`. The model is already negative-skewed; counter-bias compounds the problem. |
| `picks_a_number` | **Halt.** The methodology cannot rescue a model that gives essentially the same score regardless of input. Switch models or tell the user to accept that automated scoring on this model will be unreliable. |
| `jittery` | **Halt or ensemble.** Run the candidate model 3–5 times and average each pass's output before applying the formula. The methodology assumes per-item variance is low; if it isn't, ensembling addresses the symptom, not the methodology. |
| `unknown` | Run all four passes, **flag the run as "untested model" in the final report**, and recommend the user run `calibration-probe` before deploying at scale. |

If the user has not run the probe, do not block on it — proceed with regime `unknown` and surface the flag. The probe is a recommendation, not a hard gate.

## The 5×5 evidence matrix

Default perspectives (rows): `requester / sme / end_user / production / adversary`
Default criteria (columns): `problem_fit / craft / depth / innovation / completeness`

Customize when the domain demands. A take-home for a security role might use perspectives `hiring_manager / future_teammate / on_call / adversary / candidate_themself`. A pitch evaluation might use criteria `problem_clarity / market_fit / moat / team / ask`. Forcing five perspectives × five criteria is the principle, not the specific labels.

For each `(perspective, criterion)` cell, the analysis pass collects up to **5** signed evidence items (`{+5, +3, +2, +1, −1, −2, −3, −5}`), each with concrete evidence — file:line or timestamp. **Hard cap 5 per cell.** Past 5 is padding; sqrt normalization gives diminishing returns anyway. **Floor 3 per cell** — fewer means the analyst didn't look hard enough.

**Per-criterion floor (≥ 2 items per criterion across all perspectives).** This is a stronger floor than the per-cell minimum and it exists for a structural reason: under sparse evidence, the density multiplier collapses a criterion's score toward 50, which inflates per-criterion MAE on whichever criterion the model has the least to say about. The fix is to require **at least 2 honest items per criterion summed across all 5 perspectives** before the run can be scored. If the model genuinely cannot find 2 items for a criterion, it should explicitly downweight that criterion in the report rather than letting the formula cluster the score near 50. (See `paper/paper.md` Section 6.6 for the empirical rationale — confirmed regression on 6 of 6 v3 models.)

Default criterion weights (sum to 1.0):

| Criterion       | Weight | Why                                       |
|-----------------|--------|-------------------------------------------|
| problem_fit     | 0.30   | Did it solve the stated problem at all?   |
| craft           | 0.20   | Is it well-built?                         |
| depth           | 0.20   | Engineering/AI integration depth?         |
| innovation      | 0.15   | Genuinely novel?                          |
| completeness    | 0.15   | Is it actually shipped, end-to-end?       |

Adjust per submission category. A pure research entry bumps `innovation`; a production-bound MVP bumps `completeness` and `craft`.

## PASS 1 — Code Analysis

**Goal:** for each `(perspective, criterion)` cell, find evidence items grounded in actual files. No inflation, no fabrication. Read every claimed feature exhaustively before moving to cross-cutting concerns.

**Three steps, in order:**

1. **Feature inventory.** Read README, all `.md` docs, any submission-artifacts directory, `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` / `composer.json` / `pyproject.toml`. Extract every claimed feature verbatim. Record claims that aren't yet verified as `unconfirmed`.

2. **Per-feature exhaustive traversal.** For each feature: locate ALL backing files via Glob/Grep (routes, controllers, services, models, migrations, frontend, styles, tests). Read every file completely — skimming misses the evidence that separates good scores from great. Evaluate that feature's depth across all 5 perspectives. Assign impact items as you go, with file:line evidence. If a feature is claimed but unimplemented, that's a negative item — README claims without code backing undermine integrity.

3. **Cross-cutting concerns.** After all features: env management (`.env.example`, hardcoded secrets), auth/security patterns spanning features, CI/CD config, deploy readiness, tests not yet covered.

**Hard rules:**

- Do NOT assign a final 0–100 score in Pass 1. The number comes from the formula in Pass 3.
- Each item must include: short specific description, impact in `{+5, +3, +2, +1, −1, −2, −3, −5}`, evidence as `path:line — what it shows`.
- "Good code" is not an item. "Well-structured JWT refresh logic with proper expiry handling at `auth/middleware.ts:47`" is.
- Confidence measures evidence quantity, not project quality. A weak project with abundant evidence gets high confidence and a low score — that's the formula working.
- **Per-criterion floor: at least 2 items per criterion across all 5 perspectives.** If you genuinely cannot produce 2 items for a criterion, explicitly downweight that criterion in the report rather than letting the density multiplier collapse it toward 50. (Empirically validated regression on 6 of 6 v3 models — see `paper/paper.md` Section 6.6.)
- **If `calibration_regime` is `calibrated`, soften counter-bias.** Drop the "skeptic's eye" instruction and the "don't inflate" override; collect evidence symmetrically. The full counter-bias prompts over-correct on already-calibrated models. The empirical signature: principled scores deflate below naive on models that didn't need correction.
- **If `calibration_regime` is `unknown`, flag the run.** Add `"untested_model": true` to `pass3-synthesis.json` and surface it in the final report so the user knows to run `calibration-probe` before deploying at scale.

**Output:** `./_judge/<submission-slug>/pass1-code.json`

```json
{
  "pass": 1,
  "type": "code",
  "timestamp": "<ISO-8601>",
  "criteria": {
    "problem_fit": {
      "perspectives": {
        "requester": {
          "observations": "...",
          "positive_items": [{"item": "...", "impact": 3, "evidence": "<file:line>"}],
          "negative_items": [{"item": "...", "impact": -2, "evidence": "<file:line>"}]
        },
        "sme":        {"observations": "...", "positive_items": [], "negative_items": []},
        "end_user":   {"observations": "...", "positive_items": [], "negative_items": []},
        "production": {"observations": "...", "positive_items": [], "negative_items": []},
        "adversary":  {"observations": "...", "positive_items": [], "negative_items": []}
      },
      "net_impact": 0,
      "total_items": 0,
      "red_flags": [],
      "summary": "..."
    },
    "craft":        { "...": "..." },
    "depth":        { "...": "..." },
    "innovation":   { "...": "..." },
    "completeness": { "...": "..." }
  },
  "summary": "Direct, opinionated. What's genuinely good? What's smoke and mirrors?"
}
```

## PASS 2 — Demo Analysis (optional)

If a demo video URL or transcript is provided, run this pass. If not, skip and proceed to Pass 3 with `pass2-demo.json` written as `{"video_failed": true, "video_failed_reason": "..."}` — Pass 3 will mark the run as requiring intervention rather than scoring blind.

**Inputs accepted:**
- Public video URL (YouTube, MP4, Loom, etc.) — analyze via the harness's video-capable model
- Local video file path — analyze via local processing
- Pre-extracted transcript with timestamps

**Goal:** transform raw demo observations into structured impact items across the same 5×5 matrix. The transcript/video analysis tool describes what it saw; this pass interprets meaning through the perspective lenses.

**Apply a skeptic's eye to every observation:**
- "Presenter showed the dashboard" → was the data real or sample?
- "Features were demonstrated" → live working or pre-arranged clicks?
- "AI integration shown" → single API call or sophisticated multi-step?
- "Claimed scaling story" → architecture explained or buzzwords?

**Evidence rules:**
- Use timestamps: `1:23 — presenter explains...`
- If the demo analysis is vague, confidence must be LOW — sparse evidence is honest signal
- Do NOT fabricate items the demo didn't show
- Better 2 honest items than 5 invented ones

**Output:** `./_judge/<submission-slug>/pass2-demo.json` (same matrix shape as Pass 1)

## PASS 3 — Adversarial Synthesis

**This pass produces the scores.** It does not re-read the codebase or rewatch the video. All evidence is already captured in pass1 and pass2.

**Step 1 — Read inputs:**
1. Read `pass1-code.json`
2. Read `pass2-demo.json`
3. If `video_failed === true`: write the **intervention-required** output and stop. Do not score blind when demo evidence is missing — `craft` and `completeness` cannot be fairly assessed from code alone.

**Step 2 — Run the formula per criterion (5 times):**

```
items = pass1.items[criterion] ∪ pass2.items[criterion]   # all perspectives, both passes
net_impact         = sum(item.impact)
total_items        = len(items)
normalized         = net_impact / sqrt(total_items)        # 0 if total_items == 0
raw_score          = clamp(50 + normalized * 8.0, 0, 100)
density            = total_items / 20
multiplier         = 0.75 + 0.25 * clamp(density, 0, 1)    # never > 1.0
final_score        = round(50 + (raw_score - 50) * multiplier)
confidence         = clamp(density, 0, 1)
```

**Calibration anchors** (these are math, not opinion):

| normalized_impact | final_score (high density) |
|---|---|
| +5.0 | ~90 |
| +2.5 | ~70 |
|  0.0 | ~50 |
| −2.5 | ~30 |
| −5.0 | ~10 |

**Step 3 — Adversarial synthesis principles** (apply before writing scores):

- **Code positive + demo negative** — possible AI-generated code the team doesn't understand. Demo negatives correctly pull `net_impact` down.
- **Demo polished + code thin** — don't be fooled by presentation. Code negatives dominate `net_impact` appropriately.
- **Both agree strong** — high `total_items` → density near 1.0 → multiplier 1.0 → score unchanged from raw. This is where 85+ scores come from.
- **Both agree weak** — do not soften in synthesis. Large negative `net_impact` must produce a low `raw_score`.

**Step 4 — Self-check (mandatory):**

The 5 final scores must span at least **20 points**. Different criteria measure different things; no real project excels equally at all. If the spread is smaller, re-examine your impact items — you weren't being discriminating enough.

**Step 5 — Group strengths and concerns by tier:**
- `exceptional_critical` (|impact| = 5)
- `high_impact` (|impact| = 3)
- `medium_impact` (|impact| = 2)
- `low_impact` (|impact| = 1)

**Output:** `./_judge/<submission-slug>/pass3-synthesis.json` — the canonical scoreboard.

```json
{
  "pass": 3,
  "type": "synthesis",
  "timestamp": "<ISO-8601>",
  "requires_intervention": false,
  "scores": {
    "problem_fit":  { "score": 78, "confidence": 0.85, "raw_score": 75.6, "multiplier": 1.0, "synthesis_reasoning": "net_impact 16, total_items 25 → normalized +3.2 → raw 75.6, density 1.25 → multiplier 1.0 → final 76. Strong problem framing in both code architecture and demo; minor gaps in market validation held it back." },
    "craft":        { "...": "..." },
    "depth":        { "...": "..." },
    "innovation":   { "...": "..." },
    "completeness": { "...": "..." }
  },
  "overall_score": 72,
  "overall_confidence": 0.78,
  "self_check_span": 28,
  "self_check_passed": true,
  "key_strengths": {
    "exceptional_critical": ["+5: <description> (source: code, criterion: depth)"],
    "high_impact": [],
    "medium_impact": [],
    "low_impact": []
  },
  "key_concerns": {
    "exceptional_critical": [],
    "high_impact": [],
    "medium_impact": [],
    "low_impact": []
  },
  "overall_summary": "Direct, unapologetic assessment.",
  "tier": "Strong | Average | Below average | Exceptional | Poor",
  "reality_check": "Where does this land in the spectrum?"
}
```

## PASS 4 — Team Feedback

**Audience: the team. Not the judges.** The tone is mentoring, not scoring. Every sentence carries real information; no platitudes.

**Read all three earlier passes.** Use the structured impact items for grounded specificity (file references, timestamps); use the synthesis output for tier-appropriate calibration.

**Tone calibration by tier:**

- **Exceptional** — peer-to-peer advice. What would it take to make this real? Viability, feasibility, desirability.
- **Strong** — acknowledge wins genuinely; push on areas close to leveling up.
- **Average** — foundational growth advice with specific practices they can adopt.
- **Below average / Poor** — focus on 1–2 fundamental things with heavy encouragement. Do not pile on.

**Write feedback across four dimensions:**

1. **Submission craft** — scope discipline, shipping completeness, README/docs quality
2. **Engineering** — architecture, error handling, testing, integration depth
3. **Demo and presentation** — what worked in the pitch, what would land better
4. **Going further** — problem validation, user desirability, path to viability

**Hard rules:**

- Reference actual code files and timestamps the team can revisit. Vague praise isn't actionable; specific pointers are.
- Use `key_strengths` from Pass 3 as anchors for genuine praise.
- Use `key_concerns` from Pass 3 as anchors for growth areas. Frame as "here's the next level" not "this is bad."
- Total word count ≤ 800. Density over length.

**Score visibility is a config decision.** Some judging contexts deliberately hide numerical scores from the team (preventing leaderboard gaming, focusing them on growth); others share scores freely (transparency, calibration). Default in this skill is **share the per-criterion scores and the overall** — but ask the user before Pass 4 if they want them hidden, and respect their answer. The original vibeathon system that this pattern was modeled on hides scores; that's a reasonable choice, not the only one.

**Output:** `./_judge/<submission-slug>/pass4-feedback.json`

## Running the pipeline

The skill expects a working directory with the submission code already checked out (or a path passed in). All four passes write to `./_judge/<submission-slug>/`.

The user can drive any subset:

- **All four** — full evaluation. Provide submission path + (optional) video URL/path.
- **Code only** — judge a take-home with no demo. Pass 2 is skipped; Pass 3 must mark intervention-required if `craft` or `completeness` need demo evidence.
- **Synthesis re-run** — re-run Pass 3 after editing `pass1-code.json` or `pass2-demo.json` directly. Useful when a human reviewer corrects an item.
- **Just feedback** — run Pass 4 against existing pass1/2/3. Useful when synthesis is final and you only want to regenerate the team-facing report.

## When to override defaults

- **The submission category genuinely has different criteria.** A pitch deck doesn't have `craft` or `depth` the way code does — substitute `problem_clarity / market_fit / moat / team / ask`. Update the weights to match.
- **The submission has no demo and never will.** Drop Pass 2; reduce weights on `completeness` (which leans on demo evidence). Be honest about it in the report.
- **You only have code, not a video, but the demo IS expected.** Run Pass 1, write Pass 2 as `video_failed: true` with reason, let Pass 3 mark intervention-required, and notify the user. Don't fake it.

## Reference

- Methodology paper: `paper/paper.md` in CodefiLabs/pickanumber
- Sister skills: `calibration-probe` (preflight regime classifier — run before this skill), `evidence-scoring` (generic methodology), `what-works-feedback-judge` (4-bucket idea-readiness)
- Worked example of formula behavior: `examples/impeccable-rescoring.md`
- Per-criterion floor + counter-bias dial rationale: `paper/paper.md` Sections 6.4 (regime taxonomy) and 6.6 (demo_quality regression on 6/6 v3 models)

## Done

When all four passes are written, present a one-page summary to the user:

- Overall score + confidence + tier + self-check pass/fail
- **Calibration regime** of the scoring model (CALIBRATED / INFLATION_LIKELY / etc., or "untested" if the probe was not run). Untested runs should carry a visible flag.
- Per-criterion scoreboard (table) — flag any criterion that hit the per-criterion item floor (≥ 2 items rule)
- Top 3 strengths and top 3 concerns (from Pass 3 grouping)
- Pointer to `./_judge/<submission-slug>/pass4-feedback.json` for the team-facing report
- One sentence: should this team get the next round / merge / pilot?

Then stop. The deliverable is the four JSON files plus the summary; what the user does with them is their call.
