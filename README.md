# Pickanumber

> Don't let the LLM pick a number.

**Pickanumber** is a methodology, a paper, and three installable skills for evidence-based LLM scoring. Ask an LLM to score something on a 0–10 scale and you'll get a 7. Ask again, you'll get a 7. The model isn't grading; it's anchoring. This repo fixes the problem the same way every time: **the LLM finds evidence; math computes the score.**

The methodology was calibrated on 18 hackathon submissions and 342 BLS occupations across 9 frontier models. The paper is in [`paper/paper.md`](./paper/paper.md). Worked rescoring case studies are in [`examples/`](./examples/).

## Quickstart

### Install a skill via skills.sh

Pick the one that matches your need:

```bash
# Generic seven-principle scoring methodology — bring your own domain
npx skills add CodefiLabs/pickanumber/evidence-scoring

# 4-question idea-readiness loop (Working / Not working / Missing / Confusing)
npx skills add CodefiLabs/pickanumber/what-works-feedback-judge

# Project-submission scoring — code, optional demo video, four-pass pipeline
npx skills add CodefiLabs/pickanumber/hackathon-judge
```

Now any [skills-aware](https://skills.sh) agent (Claude Code, Cursor, Goose, OpenCode, ...) can invoke them by name.

### Or use the web one-pager

The site at [pickanumber.codefi.io](https://pickanumber.codefi.io) walks through the seven principles, the formula, the worked examples, and the install commands. Static SvelteKit, no backend.

## What's in here

```
pickanumber/
├── paper/                            # the methodology paper
│   ├── paper.md                      # Don't Let the LLM Pick a Number — v0.7 draft
│   └── README.md                     # paper status + headline results
├── evidence-scoring/                 # generic methodology skill
│   └── SKILL.md
├── what-works-feedback-judge/        # 4-bucket idea-readiness skill
│   ├── SKILL.md
│   ├── scripts/score.py              # formula + persistence helper
│   └── references/formula.md
├── hackathon-judge/                  # project-submission scoring skill
│   └── SKILL.md
├── examples/                         # worked rescoring case studies
│   ├── impeccable-rescoring.md       # pbakaus/impeccable — 76 vs 59 separation
│   └── cua-bench-analysis.md         # trycua/cua-bench — partial fit (P7 satisfied)
├── src/                              # SvelteKit one-pager
│   ├── routes/+page.svelte
│   └── lib/
│       ├── formula.js                # canonical formula — single source of truth
│       └── principles.js             # the seven principles
├── static/favicon.svg
├── package.json
├── README.md
└── LICENSE
```

## The seven principles

1. **Separate observation from scoring** — the LLM finds evidence; math computes the score.
2. **Discrete signed impact items** — every observation gets one of `{+5, +3, +2, +1, −1, −2, −3, −5}`.
3. **Diminishing returns** — `normalized = net_impact / sqrt(total_items)`. Evidence farming is punished.
4. **Density-weighted confidence** — confidence = how much evidence the scorer found, not how sure the scorer feels.
5. **Anchored center** — sparse runs regress toward 50; the multiplier never exceeds 1.0.
6. **Bounded scale with self-check** — finals live in `[0, 100]`; across criteria, the spread must be ≥ 20.
7. **Separation of LLM and deterministic computation** — independent passes by different model families collect evidence; math combines them.

## The formula

```
# Per criterion (or pooled bucket)
net_impact         = sum(item.impact for item in items)
total_items        = len(items)
normalized         = net_impact / sqrt(total_items)
raw                = clamp(50 + normalized * 8.0, 0, 100)
density            = total_items / 20
multiplier         = 0.75 + 0.25 * clamp(density, 0, 1)   # never > 1.0
final              = round(50 + (raw - 50) * multiplier)
confidence         = clamp(density, 0, 1)

# Across criteria (matrix benchmarks)
overall_score      = round(sum(c.final * c.weight for c in criteria))
overall_confidence = min(c.confidence for c in criteria)
self_check_span    = max(c.final) − min(c.final)          # must be >= 20
```

## Develop the site

```bash
npm install
npm run dev          # http://localhost:5173
npm run build        # static build → ./build
npm run preview      # serve the production build
```

The site is static — `@sveltejs/adapter-static` builds to `build/` and deploys anywhere.

## Why three skills, not one?

Each one is the same methodology pointed at a different shape of input.

- **evidence-scoring** is the methodology bare. The user brings the domain (a hire, a vendor, a draft, a model output). They define the matrix. The skill walks them through cataloging signed evidence and runs the formula.
- **what-works-feedback-judge** is the simplest pre-baked application. Four buckets (Working / Not working / Missing / Confusing), one pooled score, save-and-iterate. Use it for any draft, plan, or pitch.
- **hackathon-judge** is the most structured application. Four-pass pipeline (code analysis → optional demo → adversarial synthesis → mentoring feedback) over a 5×5 matrix. Use it when there's a code submission and someone needs to score it consistently.

Pick the smallest one that fits.

## Credits

- **Methodology** — *Don't Let the LLM Pick a Number*, Kevin Kirchner / CodefiLabs
- **Calibration data** — 18 hackathon submissions (St. Joseph + Joplin events), 342 BLS occupations
- **Sister project** — [CodefiLabs/mybench](https://github.com/CodefiLabs/mybench) — same formula, applied to the personal-benchmark interview pattern
- **Skill ecosystem** — [skills.sh](https://skills.sh)

## License

MIT — see [LICENSE](./LICENSE). The methodology is released for any use; the markdown sources are MIT so the paper, skills, and examples can be remixed freely.
