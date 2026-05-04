# Paper

`paper.md` is the **v0.8.0** draft of *Don't Let the LLM Pick a Number: Seven Principles for Evidence-Based LLM Scoring*.

**Status:** working draft, May 2026. The mirrored draft keeps the body of the paper plus appendices A–E (emotional-judgment gap, human baseline statistics, industry convergence, calibration-conditional decision rule, calibration probe spec). A trimmed reference list is implied throughout the body; the full reference list with arXiv IDs lives in the working paper repository.

**What's new in v0.8.0 (vs prior versions):**
- **Six-model held-out grid** on the Cape Vibeathon dataset: gpt-5.5, deepseek-flash, gemini-3-flash, gemma4:31b-cloud, gpt-oss-20b, nemotron. Replaces the four-model grid in earlier versions.
- **Five-regime taxonomy** (CALIBRATED, INFLATION_LIKELY, DEFLATION_LIKELY, PICKS_A_NUMBER, JITTERY) with empirical exemplars from the six-model grid.
- **30-second calibration probe** as a preflight diagnostic — answers "is my model in a regime where the methodology helps?" without ground truth (Section 5.7, Appendix E).
- **3-of-6 over-correction pattern** documented honestly: gpt-5.5, deepseek-flash, gpt-oss-20b are CALIBRATED naive distributions where the v3 counter-bias prompts over-correct. Future-work item: model-specific counter-bias dial.
- **Demo_quality regression** confirmed across 6/6 models — a per-criterion sparsity collapse under the density multiplier. Per-criterion item floor proposed as the v4 fix (Section 6.6).
- **Six-point naive↔principled MAE divergence curve**: gpt-5.5 4.67 → nemotron 9.46 → deepseek 10.95 → gpt-oss 11.54 → gemma4 15.60 → gemini 17.85.

**Datasets:**
- 17 hackathon submissions (St. Joseph vibeathon)
- 31 hackathon submissions (Joplin event)
- 77 hackathon submissions (Cape Girardeau vibeathon, 264 human-judge score rows, 6-model held-out grid)
- 342 BLS occupations from the Occupational Outlook Handbook (re-scored across 9 models from 5 providers)

**Key results (v0.8):**
- Discrimination improvement vs naive scoring: 21–58% (median 41%) across 9 models on 342 occupations
- Rank preservation: Spearman rho = 0.87
- Cross-model agreement (occupations): rho 0.77–0.93
- Cross-model regime taxonomy (Cape Vibeathon, n=77): four regimes empirically named across six models
- gemini-3-flash principled wins everything: Pearson 0.508 → 0.538, MAE 16.86 → 9.61
- Formula ablation: sqrt normalization + capped confidence regression are individually necessary and jointly sufficient
- Calibration probe predicts the regime in 30 seconds with no ground truth (validation in v0.8.x)

**Worked rescoring case studies:**
- `examples/impeccable-rescoring.md` — `pbakaus/impeccable` UI quality benchmark; before/after separation 76 vs 59 with stable runs
- `examples/cua-bench-analysis.md` — `trycua/cua-bench` computer-use agent benchmark; partial fit (P7 satisfied, P2–P6 wide open)

If you'd like a citation-ready PDF, email `kevin@codefiworks.com`.
