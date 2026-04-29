# Product

## Register

brand

## Users

Technical readers evaluating evidence-based scoring methodologies — engineers building LLM eval pipelines, AI/ML practitioners, hackathon judges, benchmark authors, paper readers. They are skeptical by default and respect rigor over polish. They've already seen LLMs return 7-out-of-10 a thousand times and want a fix that doesn't hand-wave. They arrive from GitHub, Hacker News, X, or a citing paper. The win condition is a single command: `npx skills add CodefiLabs/pickanumber/...`.

## Product Purpose

This is a brand surface, but the **product is the skill download**. The page exists to:

1. Convince the visitor the LLM-pick-a-number problem is real (not their imagination).
2. Show that the methodology + formula are simple, defensible, and already calibrated.
3. Drive an installable skill into their agent (`npx skills add ...`).

Success is `skills add` invocations, not pageviews. Everything that doesn't help that conversion is decoration.

## Brand Personality

**Build-in-public tinkerer.** Open-source maker who will publicly rescore other people's work to make the point (the `pbakaus/impeccable` and `trycua/cua-bench` case studies are personality, not just content). Transparent, iterative, willing to ship a v0.7 draft and call it that. Confident in the methodology because the math is the math, not because the copy says so.

Three words: **rigorous, candid, hands-on.**

Voice cues: short declarative sentences. No marketing softeners. Code samples and formulas are first-class, not buried. Show the receipts (90+ submissions across 3 hackathons, 342 BLS occupations, 9 models). Don't apologize for being a draft.

## Anti-references

- **Generic SaaS landings** — gradient hero, three-up feature cards, "trusted by" logos, hero-metric template. Already avoided.
- **AI-tool tropes** — neon glows, dark glassmorphism, gradient-text headlines, "powered by AI" badges. Already avoided.
- **Academic-paper-as-PDF dump** — walls of LaTeX with zero design effort. We're rigorous, not dusty.
- **Closed enterprise marketing** — anything that hides the math behind a "request a demo" CTA. The opposite of build-in-public.

## Design Principles

1. **The receipts are the design.** Worked examples, calibration tables, real rescoring case studies — those carry the page. Decoration doesn't.
2. **Practice what you preach.** A page about scoring rigor cannot itself be designed by vibes. Every visual choice should hold up under a critique pass.
3. **Code and math are first-class.** Formulas and `npx` commands are content, not asides. Render them with the same care as the headline.
4. **Confidence without swagger.** State what the methodology does and what it doesn't (cua-bench is "partial fit"). Honesty is the brand.
5. **One conversion, no ceremony.** The path from "I get the problem" to "the skill is installing" should be three clicks max. Don't gate it behind a sign-up.

## Accessibility & Inclusion

No explicit WCAG target stated. Implicit: technical-readers-everywhere, so don't undermine basic ergonomics — sufficient contrast (the warm-paper palette has plenty of headroom), keyboard-navigable, semantic landmarks, focus-visible, no motion that ignores `prefers-reduced-motion`. Don't ship anything that would fail axe on a section.
