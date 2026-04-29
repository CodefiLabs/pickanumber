# Paper

`paper.md` is the v0.7 draft of *Don't Let the LLM Pick a Number: Seven Principles for Evidence-Based LLM Scoring*.

**Status:** working draft. The v0.7 mirrored here keeps the body of the paper but trims the bibliography and appendices to keep the file readable as repository content. The full reference list (Bao 2026, Bornmann 2010, Brown 1910, Chan 2024, DeLucia 2026, Efron & Morris 1977, Elganayni 2026, Gu 2025, Gupta & Kumar 2026, Gupta 2026, Huang 2025, Jonsson & Svingby 2007, Kadavath 2022, Kahneman/Sibony/Sunstein 2021, Karpathy 2025, Kim 2026, Krippendorff 2004, Lee 2024, Li 2023, Li 2024, Li 2025, Liu 2023, Lord & Novick 1968, Ni 2025, Qi 2026, Rao & Callison-Burch 2026, Shermis & Burstein 2013, Spearman 1910, Verga 2024, Wang 2023, Wang 2026, Wei 2025a, Wei 2025b, Xiong 2024, Yang 2026, Ye 2024, Zhang 2024, Zheng 2023) and the full appendices (emotional-judgment-gap analysis with all 26 dimensions; per-criterion Krippendorff's alpha tables; judge leniency intercepts) live in the working paper repository at `PROJ-ai-judge-scoring/drafts/draft-attempt-v1/paper-v7.md`.

**Datasets:**
- 17 hackathon submissions (St. Joseph vibeathon)
- 31 hackathon submissions (Joplin event)
- 342 BLS occupations from the Occupational Outlook Handbook (re-scored across 9 models from 5 providers)

**Key results:**
- Discrimination improvement vs naive scoring: 21–58% (median 41%) across 9 models
- Rank preservation: Spearman rho = 0.87
- Cross-model agreement: rho 0.77–0.93
- Formula ablation: sqrt normalization + capped confidence regression are individually necessary and jointly sufficient

**Worked rescoring case studies:**
- `examples/impeccable-rescoring.md` — `pbakaus/impeccable` UI quality benchmark; before/after separation 76 vs 59 with stable runs
- `examples/cua-bench-analysis.md` — `trycua/cua-bench` computer-use agent benchmark; partial fit (P7 satisfied, P2–P6 wide open)

If you'd like a citation-ready PDF, email `kevin@codefiworks.com`.
