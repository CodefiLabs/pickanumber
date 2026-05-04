# Don't Let the LLM Pick a Number: Seven Principles for Evidence-Based LLM Scoring

**Kevin Kirchner**
Codefi Foundation

**Version 0.8.0** (May 2, 2026) — extends prior versions with a six-model held-out cross-model grid, a 30-second synthetic calibration probe with a five-regime classifier, an honest treatment of when the v3 prompts over-correct on already-calibrated models, and a confirmed per-criterion regression (demo_quality) requiring a v4 prompt-side fix.

---

## Abstract

Don't let the LLM pick a number. Seven principles, grounded in classical psychometric theory, separate evidence collection from score computation: the LLM finds structured evidence; mathematical corrections derive calibrated scores. Cross-domain validation on 342 occupations scored by 9 models from 5 providers shows discrimination improvements of 21--58% (median 41%) over naive scoring, with preserved rank ordering (Spearman rho = 0.87) and strong cross-model agreement (rho = 0.77--0.93). A held-out cross-model evaluation on 77 hackathon submissions across **six** model families (gpt-5.5, deepseek-flash, gemini-3-flash, gemma4:31b-cloud, gpt-oss-20b, and nemotron) reveals a **calibration-conditional regime structure**: principled rescoring wins on every aggregate metric for the most-inflated model (gemini-3-flash, principled Pearson 0.538 vs naive 0.508; principled MAE 9.61 vs naive 16.86), can over-correct on already-calibrated models (3 of 6: gpt-5.5, deepseek-flash, gpt-oss-20b — naive wins on Pearson and MAE in all three), and fails to rescue weak signal (nemotron, both methods stuck at Pearson ≈0.36). The naive↔principled MAE divergence forms a clean six-point diagnostic curve tracking model-strength × calibration. We complement the formula with a 30-second synthetic *calibration probe* that classifies a model into one of five regimes — CALIBRATED, INFLATION_LIKELY, DEFLATION_LIKELY, PICKS_A_NUMBER, or JITTERY — using a 20-item rating prompt with no ground truth, predicting whether the methodology will help *before* the practitioner runs it. Formula ablation confirms that sqrt normalization and capped confidence regression are individually necessary and jointly sufficient. We also report a confirmed limitation: under the v3 prompts, all six models show worse demo_quality MAE under principled than naive — a per-criterion sparsity-collapse under the density multiplier that requires a per-criterion item floor before production deployment. The Spring 2026 reliability literature (Wu, DeLucia, Sage, RIFT, Style Bias Dominates, Preference Leakage, BenchGuard, and others) converges on the diagnosis from a half-dozen directions; this paper supplies the prescriptive answer plus the diagnostic kit needed to apply it responsibly.

---

## 1. Introduction

AI systems increasingly need to evaluate, score, and rank artifacts. Hackathon submissions, code review pull requests, customer service interactions, compliance documents, content moderation decisions --- across domains, organizations face the same question: can we automate evaluation that currently depends on scarce human expert judgment? The dominant default is seductively simple: ask an LLM to "rate this 0--100" and use the number it produces. This approach is fast to build. It is also, as we demonstrate empirically, unreliable.

Kahneman, Sibony, and Sunstein (2021) established that even human experts exhibit substantial unwanted variability (*noise*) in judgments that should ideally be identical. AI evaluators inherit this problem and amplify it through five structurally distinct failure modes:

**Score inflation.** LLM scorers produce median scores clustering in the 70--85 range regardless of quality. In our hackathon dataset, a naive AI scorer produced a mean weighted score of 74.65 compared to the human mean of 58.54 --- a 16.1-point gap --- with Spearman rank correlation of rho = 0.068 (p = 0.726), indicating essentially no agreement on relative ordering.

**The "everything is above average" problem.** RLHF training biases LLMs toward helpful, affirming outputs rather than discriminating ones. Xiong et al. (2024) document how RLHF induces overconfidence that persists after calibration attempts; Wei et al. (2025a) show poor calibration across tasks; the Spring 2026 wave (Sage, Style Bias Dominates, Preference Leakage --- detailed in Section 2) provides convergent independent evidence.

**Evidence-agnostic confidence.** A model that examined three files reports the same confidence as one that examined thirty, making self-reported confidence useless as a reliability indicator (Kadavath et al., 2022). Wu et al. (2026) sharpen this with multimodal evidence: their VLM judges produce score intervals covering 40--70% of the rating range despite producing reliable rank orderings on the same items --- ranking and scoring decouple.

**Cross-modal blindness.** When code and video are evaluated in isolation, cross-modal contradictions go undetected. Zhang et al. (2024) found that multimodal LLMs achieve only ~0.64 cross-modal consistency.

**Prompt-perturbation instability.** Surface-level rewordings of the judge prompt shift measured outcomes by 24.2 percentage points in safety benchmarks (Hendel et al., 2026); style features explain 76--92% of judge variance, far exceeding position bias (Liang et al., 2026).

These five failure modes are not theoretical --- they manifest in production systems built by expert practitioners. Karpathy's (2025) AI-exposure scoring system illustrates the point. The system scores 342 occupations for AI exposure using a single Gemini Flash call that returns a 0--10 score. Its rubric includes anchored examples at each score level, following established rubric design principles (Jonsson and Svingby, 2007) --- yet it still defaults to asking the LLM to pick a number. When we re-scored those same 342 occupations using our principled methodology (Section 5), the naive approach compressed scores into a bell curve centered at 5.3, while the evidence-based approach produced 21--58% greater score separation (median 41% across 9 models) with rho = 0.87 rank correlation. The failure is structural, not a matter of rubric quality.

The core insight, echoing the paper's title: **the LLM should never pick a number.** Instead, the LLM collects structured evidence --- discrete impact items with fixed severity scores --- and mathematical formulas compute calibrated scores from the evidence. We organize this insight into seven principles:

1. **Separate observation from scoring** --- the LLM finds evidence; math computes the score.
2. **Replace subjective confidence with evidence density** --- how much the model found, not how sure it claims to be.
3. **Use discrete impact items, not continuous scales** --- forces commitment, prevents middle-clustering.
4. **Apply diminishing returns normalization** --- prevents evidence farming from inflating scores.
5. **Regress uncertain evaluations toward the mean** --- low evidence produces conservative scores, not confident ones.
6. **Force multiple perspectives** --- prevents single-lens bias.
7. **Use cross-modal adversarial synthesis** --- independent analyses catch contradictions.

Principles 1--5 are empirically validated through cross-domain replication and formula ablation (Section 5). Principles 6 and 7 are architectural design principles supported by theoretical argument and prior work (Verga et al., 2024; Yang et al., 2026) but not yet individually ablated in our framework.

These principles draw on established psychometric theory: sqrt(n) normalization mirrors how standard error scales in classical test theory (Lord and Novick, 1968; Spearman, 1910; Brown, 1910), the confidence multiplier is inspired by empirical Bayes shrinkage toward a prior (Efron and Morris, 1977), and the discrete impact scale follows analytic rubric design for scoring reliability (Jonsson and Svingby, 2007).

The primary contribution of this paper is the scoring methodology itself --- the seven principles and their mathematical instantiation. We validate the framework through cross-domain replication (342 occupations, 9 models, 5 providers), a held-out cross-model agreement analysis on 77 hackathon submissions across **six** model families (Section 5.5), formula ablation isolating each component's contribution, and human baseline analysis establishing the reliability floor that automated evaluation must exceed.

A secondary contribution is a *calibration-conditional* reading of when the methodology helps and when it does not. Section 6.4 develops this: principled evidence-item rescoring closes the human-AI gap most decisively when models are inflated, can over-correct on already-calibrated models, and fails to rescue weak underlying signal. We organize the failure modes into a five-regime classification (Section 5.7) and ship a 30-second synthetic calibration probe that classifies a model into a regime *before* the practitioner runs the full pipeline.

A third contribution is an honest report of a confirmed limitation: under the v3 prompts, all six v3 models show worse demo_quality MAE under principled than naive — a per-criterion sparsity-collapse under the density multiplier that requires a per-criterion item floor before production deployment (Section 6.6). We document the regression rather than hide it because the confirmed-on-6-of-6 pattern is itself empirical evidence of how prompt design at the per-criterion level interacts with the formula.

---

## 2. Related Work

### 2.1 LLM-as-Judge Foundations

Zheng et al. (2023) established LLM-based evaluation with MT-Bench, demonstrating >80% human preference agreement while documenting position bias, verbosity bias, and self-enhancement bias. Wang et al. (2023) showed position bias severe enough to reverse rankings, supporting decomposed pointwise scoring over pairwise comparison. Li et al. (2024) and Li et al. (2025) provide comprehensive taxonomies identifying calibration as an open problem.

The response to documented biases has been progressive decomposition. G-Eval (Liu et al., 2023) established "reason first, score second" via chain-of-thought. FLASK (Ye et al., 2024) introduced 12-dimension criterion-level decomposition but still relies on LLM scoring per dimension. CheckEval (Lee et al., 2024) removes the LLM from final score computation by decomposing evaluation into binary checklist items --- the closest prior work to our approach --- but discards magnitude information: a critical security vulnerability and a minor typo are both single checklist items. Our system assigns impact scores from {+5 to -5}, preserving severity. RocketEval (Wei et al., 2025b) achieves 0.965 Spearman correlation with a three-stage pipeline but operates in a single modality, uses a single model family, and applies no statistical corrections.

### 2.2 The Spring 2026 Reliability Wave

A striking feature of the literature in the months leading up to this paper is the *sudden density* of independent work converging on the diagnosis our principles address. We catalog the wave by failure mode:

**Ranking-scoring decoupling.** Wu et al. (2026) report that multimodal judges produce reliable relative orderings while their absolute scores carry uncertainty intervals covering ~40% of the range for natural images and ~70% for math/charts. *Ranking is reliable, scoring is not* — practitioners who only need rankings get away with naive prompting; practitioners who need calibrated absolute scores cannot.

**Judge inconsistency.** Liu et al. (2025), in the Sage system, find that even Gemini 2.5 Pro and GPT-5 fail to maintain consistent preferences on nearly a quarter of difficult cases, attributing this to "situational preference." Sage shows that *explicit rubrics mitigate the problem* — supporting our Principle 3.

**Style bias dominates.** Liang et al. (2026) compare nine debiasing strategies across five judge models and find that style bias accounts for 76--92% of judge variance, dwarfing position bias. Surface-level fixes underperform; the structural fix is to remove the LLM from the number-picking step.

**Family contamination.** Li et al. (2026) confirm preference leakage at ICLR 2026: judges silently favor outputs from their own model lineage. Sun et al. (2026) quantify the same effect for self-preference. Our independence architecture --- using different model families for code and video evaluation --- mitigates this directly.

**Rubric failure taxonomy.** Qi et al. (2026) catalog eight rubric failure modes across three categories (Reliability, Content Validity, Consequential Validity), validated via grounded theory across five domains. The taxonomy's existence is itself an argument: rubric-based LLM scoring has enough categorizable pathologies to warrant a dedicated failure-mode language.

**Domain-specific evidence.** DeLucia et al. (2026) test medical chatbot completeness across three rubric granularities and report AUC 0.49--0.66 against clinician annotations regardless of rubric format. The paper's central claim --- that rubric structure alone does not save naive scoring --- is exactly the gap evidence-anchored aggregation fills.

**Decomposition convergence.** Multiple concurrent systems independently arrive at decomposition. RULERS (Rao and Callison-Burch, 2026) compiles rubrics into executable specifications. WIMPE (Wang et al., 2026) factorizes reference answers into weighted scoring points. RRD (Chen et al., 2026) recursively decomposes coarse rubrics with correlation-aware weighting (+17.7 points on JudgeBench, 160% on reward modeling). HumorRank (Bao et al., 2026) collects pairwise signals and aggregates via Bradley-Terry MLE, never letting the LLM pick a number. DeepRed (Vasilakopoulos et al., 2026) introduces partial-credit checkpoint scoring for CTF agents. Beyond Task Success (Koch and Wellbrock, 2026) and Eligibility-Aware Evidence Synthesis (Patel et al., 2026) independently use the phrase "evidence synthesis" in titles, suggesting "evidence-first evaluation" is becoming a recognized pattern.

**The structural answer.** What unites the wave is the implicit recognition that *a sufficiently smart prompt, applied to a sufficiently large model, does not produce a calibrated number*. The diagnostic literature names the symptoms; our methodology supplies the prescriptive structure: never let the LLM pick a number; collect evidence with discrete severity; let math compute the score. v0.8 of this paper adds the *diagnostic layer* — a regime classifier that tells the practitioner *before they run the methodology* whether their model is in a regime where the methodology will help.

### 2.3 Scoring Theory and Psychometrics

The statistical foundations for reliable scoring predate LLMs. Lord and Novick (1968) formalized that standard error scales as sigma/sqrt(n) --- measurement precision improves with the square root of observations. The Spearman-Brown prediction formula (Spearman, 1910; Brown, 1910) codifies the same principle for test reliability. When we compute `net_impact / sqrt(total_items)`, we apply this established relationship.

Efron and Morris (1977) demonstrated that shrinking estimates toward the population mean produces better predictions than using raw observations alone. Our confidence multiplier --- pulling scores toward 50 when evidence is sparse --- is inspired by this principle. The multiplier is a linear heuristic rather than a full Bayesian posterior computation, but the statistical motivation is identical: regularize uncertain estimates toward a neutral prior.

The gap: these well-established psychometric principles have not been systematically applied to LLM-based evaluation until the recent wave. Automated essay scoring (Shermis and Burstein, 2013) applies statistical corrections to scoring but predates LLMs and does not address the specific failure modes of neural language models.

### 2.4 Multi-Agent and Multi-Modal Evaluation

Verga et al. (2024) formalize PoLL (Panel of LLM evaluators), showing diverse model panels outperform single judges. PoLL aggregates via voting; our system applies sqrt normalization and confidence regression to the evidence collected across perspectives. Yang et al. (2026) demonstrate that adversarial conflict outperforms majority vote, validating our synthesis design.

Zhang et al. (2024) find ~0.64 cross-modal consistency in multimodal LLMs, motivating our separation of modality-specific analysis into independent passes. Wu et al. (2026) extend the cross-modal critique to score reliability specifically.

### 2.5 Industry Convergence

Three vendor moves in 2025--2026 signal that the structural critique has reached production. Amazon's Nova rubric-based LLM judge (AWS Machine Learning Blog, 2026) explicitly generates per-criterion rubrics with justifications and reports +49% on complex JudgeBench scenarios — a Principle 3 move at industry scale. Lechmazur's `lechmazur/writing` benchmark (2026) explicitly retired its 0--10 absolute rubric after 9,139 score rows and switched to Bradley-Terry pairwise tournaments. Mistral's Workflows release (April 2026) ships durable execution and `wait_for_input()` for human-in-the-loop, but conspicuously omits any scoring layer — the practitioner-facing lane for principled evaluation remains open. Vendors are abandoning naive numeric scoring in favor of either decomposed rubrics or pairwise tournaments. The principles in this paper unify both moves under a single statistical framework.

### 2.6 Summary

**Table 1.** Comparison of evaluation systems across methodological dimensions.

| System | Multi-model | Decomposed | Statistical corrections | Evidence-derived confidence | Multi-modal | Calibration diagnostic |
|--------|:-----------:|:----------:|:-----------------------:|:---------------------------:|:-----------:|:---------------------:|
| G-Eval (2023) | | Yes | | | | |
| FLASK (2024) | | Yes | | | | |
| CheckEval (2024) | | Yes (binary) | | | | |
| PoLL (2024) | Yes | | | | | |
| RocketEval (2025) | | Yes | | | | |
| RRD (2026) | | Yes (recursive) | Correlation weights | | | |
| RULERS (2026) | | Yes (executable) | Wasserstein | | | |
| WIMPE (2026) | | Yes (factorized) | LLM-graded weights | | | |
| HumorRank (2026) | | Yes (pairwise) | Bradley-Terry | | | |
| DeepRed (2026) | | Yes (checkpoint) | | | | |
| Conformal Judges (2026) | | | Conformal intervals | | | Yes (post-hoc) |
| **This paper (v0.8)** | **Yes** | **Yes** | **Yes (sqrt + shrinkage)** | **Yes** | **Yes** | **Yes (regime probe)** |

No prior system combines decomposed evidence extraction, statistical corrections, evidence-derived confidence, multi-model evaluation, multi-modal analysis, *and* an a-priori regime diagnostic.

---

## 3. System Architecture

The architecture implements a single constraint: **no pass may produce a score.** Each pass collects structured evidence; mathematical formulas compute final scores.

### 3.1 General Pipeline Pattern

The methodology generalizes as a four-stage pipeline applicable to any evaluation domain:

1. **Domain-specific evidence collection** (one or more independent passes). Each pass receives the artifact through a single modality or analytical lens, producing structured impact items with severity scores, evidence citations, and categorical labels. Passes operate independently --- no pass sees another's output.

2. **Adversarial synthesis.** A dedicated pass receives all evidence and cross-checks for contradictions, redundancy, and coverage gaps. The scoring formula (Section 4) is applied here.

3. **Confidence calibration.** Evidence density determines confidence; sparse evaluations regress toward the mean.

4. **Structured feedback.** Accumulated evidence generates actionable feedback. Non-scoring.

The key architectural invariant is *independence between evidence-collection passes*. Different passes may use different models, different modalities, or different analytical frameworks, but none may see another's findings. This prevents error correlation and enables adversarial cross-checking in the synthesis stage.

### 3.2 Hackathon Instantiation

We instantiate the general pattern for hackathon evaluation as a 4-pass pipeline.

**Pass 1: Code Analysis.** Deep codebase traversal organized by feature, not by file. The pass generates a feature inventory, then exhaustively verifies each claimed feature through five evaluation lenses: implementation quality, test coverage, error handling, architecture decisions, and documentation. Output: structured impact items, each with an impact score from {+5 to -5}, evidence citation (file:line), and criterion label.

**Pass 2: Video Analysis.** A native-video model provides structured observation: presenter confidence, energy, body language, whether limitations were acknowledged. A second model then interprets these observations skeptically, producing impact items with timestamp citations. Pass 2 has no access to Pass 1 output.

**Pass 3: Adversarial Synthesis.** Receives both pass outputs and performs cross-checking across four patterns: strong code + strong demo, strong code + weak demo (presentation gap), weak code + strong demo (catching "polished theater"), weak code + weak demo (conservative evaluation). The scoring formula (Section 4) is applied here.

**Pass 4: Team Feedback.** Tier-calibrated mentoring feedback from accumulated evidence. Non-scoring.

### 3.3 Prompt-Engineering Lessons and Their Empirical Limits

Across the development cycle, we observed that *prompt design materially affects whether the "evidence not numbers" instruction actually holds*. The lessons generalize to any practitioner adopting the methodology:

1. **Drop "perspectives" if you have them.** Multi-perspective prompts encourage models to re-state the same observation under different perspective labels — a single substantive finding becomes N items via labeling. Flat evidence with criterion labels is more honest.

2. **Token-order matters in JSON shape.** LLMs predict tokens left-to-right. If the JSON shape is `{score, reflection, confidence}`, the model commits to the number first and post-hoc rationalizes. Enforce `{reflection, evidence, criterion, impact}` — reasoning first, score last. The "evidence not numbers" principle implemented at the *output structure* level, not just the prompt-text level.

3. **Confidence on naive only.** Asking for confidence on the principled pass re-introduces "LLM picks a number" on the very dimension the methodology argues against. Keep confidence on the naive baseline (where it functions as a free overconfidence diagnostic) but remove it from principled (where evidence density is the structural confidence proxy).

4. **Symmetric source acknowledgment.** When the prompt describes the model as a "codebase evaluator" but feeds both codebase AND video observations, the model under-weights one source. Reword to "submission evaluator" with explicit dual-source acknowledgment.

**The empirical outcome and its limit.** We ran these prompts on six models (Section 5.5). The cross-model picture revealed a nuance: counter-bias instructions ("skeptic's eye", "two honest items > five invented", "README claims without code → negative item") are *correctly calibrated* for inflated models like gemini-3-flash but *over-correct* on already-calibrated models like gpt-5.5, deepseek-flash, and gpt-oss-20b. The trajectory is real progress on the most-broken case; it has not yet found the right setting for the well-calibrated case. Section 6.4 develops this as a *model-specific counter-bias dial* in future work.

The lesson generalizes: *getting the LLM out of the number-picking business is not just a math problem; it is a prompt-engineering problem*. The JSON output shape, the absence of perspective labels, the deliberate removal of confidence requests on principled passes, and *per-criterion item floors* (Section 6.6) all matter.

### 3.4 Computational Cost

The 4-pass pipeline requires approximately 25--45 minutes per submission, dominated by Pass 1's deep codebase traversal. Pass 2 runs in 5--10 minutes (video processing + skeptical interpretation). Passes 3--4 each require 2--5 minutes. Total API cost is approximately $10--25 per submission at current pricing, depending on repository size.

The calibration probe (Section 5.7) adds roughly 30 seconds per model and zero cost beyond a single inference call repeated 30 times on a 20-item synthetic prompt.

---

## 4. Scoring Methodology

### 4.1 Multi-Perspective Impact Scoring

Each submission is evaluated through a 25-cell matrix: 5 criteria, with up to 5 items per pass per criterion (under earlier prompt designs) or a flat evidence pool with criterion labels (under v3). **Criteria** define what is measured, with weights: impact and relevance (40%), demo quality (20%), feasibility (15%), innovation (15%), user experience (10%).

Each item is assigned a discrete score from {+5, +3, +2, +1, -1, -2, -3, -5}. The discrete scale forces commitment --- the evaluator cannot hedge with a 3.7 and must decide between +3 (significant) and +5 (major). Every item cites specific evidence (file:line or timestamp), making evaluation auditable.

### 4.2 The Scoring Formula

**Step 1: Aggregate.** `net_impact = sum(all_item_values)`, `total_items = count(all_items)`.

**Step 2: Normalize and scale.** `normalized_impact = net_impact / sqrt(total_items)`, `raw_score = 50 + (normalized_impact * 8.0)`, clamped [0, 100]. The sqrt denominator creates diminishing returns: 4 strong items (+3 each, net=+12, normalized=6.0) outweigh 16 mediocre items (+1 each, net=+16, normalized=4.0). This mirrors how standard error scales with 1/sqrt(n) in classical test theory.

**Step 3: Confidence-based regression.** `evidence_density = total_items / 20`, `confidence_multiplier = 0.75 + (0.25 * clamp(evidence_density, 0, 1))`, `final_score = round(50 + ((raw - 50) * confidence_multiplier))`. With zero evidence, the multiplier is 0.75: the score regresses 75% toward 50. With >= 20 items, the multiplier reaches 1.0 and the score stands. The multiplier **never exceeds 1.0** --- abundant evidence confirms but never amplifies.

**Step 4: Self-check.** All 5 criterion scores must span >= 20 points, ensuring the evaluator discriminates across dimensions.

### 4.3 Confidence as Evidence Density

LLMs are systematically overconfident due to RLHF (Xiong et al., 2024; Wei et al., 2025a; Kadavath et al., 2022). Self-reported confidence is uncorrelated with evaluation quality. We replace it with a behavioral proxy: `confidence = clamp(total_items / 20, 0, 1)`. This metric is quality-independent --- a terrible project with abundant evidence gets high confidence and a low score --- and observable: anyone can count the items and verify the metric.

A useful diagnostic falls out of this design. We deliberately preserve a model-self-reported confidence field on the naive baseline. The variable `model_confidence_mean` becomes a free overconfidence audit: plot it against `|naive_score - human_score|` and you have a calibration curve for the model on this task, with no extra API calls.

### 4.4 Worked Examples

**Strong submission, ample evidence.** net_impact = +25, total_items = 25. normalized = 25/sqrt(25) = 5.0. raw = 90. density = 1.25, multiplier = 1.0. **final = 90**, confidence = 1.0.

**Strong submission, sparse evidence.** net_impact = +25, total_items = 4. normalized = 12.5. raw = 150, clamped 100. density = 0.2, multiplier = 0.80. **final = 90**, confidence = 0.2. Sparse evidence pulls the score back and flags low confidence.

**Weak submission, ample evidence.** net_impact = -15, total_items = 25. normalized = -3.0. raw = 26. density = 1.25, multiplier = 1.0. **final = 26**, confidence = 1.0. High confidence in a low score.

### 4.5 Minimum Viable Adoption (and the Probe-First Refinement)

Not all domains require the full 4-pass pipeline. The formula ablation (Table 4) suggests that Principles 1, 4, and 5 --- separation of observation from scoring, sqrt normalization, and capped confidence regression --- form the critical trio. A practitioner who makes only these three changes to a naive LLM scorer captures the largest share of the methodology's improvement.

A sharper adoption rule, derived from Section 6.4 and operationalized via Section 5.7's calibration probe, is: *the full pipeline pays for itself when the model is in a regime that benefits from it*. The probe classifies a model into one of five regimes (CALIBRATED, INFLATION_LIKELY, DEFLATION_LIKELY, PICKS_A_NUMBER, JITTERY) using a 30-second synthetic test. Regime determines the recommended adoption depth. Practitioners with no prior calibration data should run the probe first.

---

## 5. Empirical Evaluation

We evaluate the framework through five analyses: cross-domain replication on 342 occupations (Section 5.2), cross-model agreement on 77 hackathon submissions across **six** model families (Section 5.5), formula ablation (Section 5.3), human baseline reliability (Section 5.4), and a calibration probe diagnostic (Section 5.7).

**Table 2.** Results summary across all experiments.

| Experiment | Key Metric | Value |
|------------|-----------|-------|
| Naive vs. principled (342 occupations) | Discrimination improvement (std dev ratio) | 21--58%, median 41% across 9 models |
| Naive vs. principled (342 occupations) | Rank preservation (Spearman rho) | 0.87 |
| Cross-model agreement on principled (9 models, occupations) | Pairwise Spearman rho range | 0.77--0.93 |
| **Six-model regime taxonomy (Cape Vibeathon)** | **Regimes identified** | **CALIBRATED, INFLATION_LIKELY, PICKS_A_NUMBER (+ de facto DEFLATION_LIKELY under v3)** |
| **gemini-3-flash principled (hackathon)** | **Pearson, MAE — principled vs naive** | **0.538 vs 0.508, 9.61 vs 16.86 (principled wins all)** |
| **gpt-5.5 / deepseek / gpt-oss principled (hackathon)** | **Naive wins on Pearson and MAE** | **3-of-6 over-correction pattern** |
| **nemotron principled (hackathon)** | **Both methods Pearson** | **≈ 0.36 (PICKS_A_NUMBER regime)** |
| **Naive↔Principled MAE divergence curve** | **6-point empirical curve** | **gpt-5.5 4.67 → nemotron 9.46 → deepseek 10.95 → gpt-oss 11.54 → gemma4 15.60 → gemini 17.85** |
| Formula ablation: without sqrt | Evidence farming score (net=+40, 50 items) | 113 (exceeds 100) |
| Formula ablation: production formula | Same profile | 95 (correctly bounded) |
| Human inter-rater reliability (Joplin) | Krippendorff's alpha | 0.16 |
| Human inter-rater reliability (St. Joseph) | Krippendorff's alpha | 0.04 |
| Human vs. naive AI (Joplin) | Spearman rho | 0.068 (p = 0.726) |
| Human vs. naive AI (Joplin) | Score inflation (AI - human mean) | +16.1 points |

### 5.1 Datasets

**Hackathon submissions (St. Joseph + Joplin).** 17 submissions from a St. Joseph vibeathon event (2--4 human judges each), and 31 submissions from a separate Joplin event (5 judges). The St. Joseph judges had access to AI observation summaries during judging (contamination noted throughout); the Joplin comparison is uncontaminated. These data provide the human baseline analysis (Appendix B).

**Hackathon submissions (Cape Vibeathon).** A larger and more recent dataset: 77 submissions from the Cape Girardeau vibeathon event, each with code, demo video, and 264 human-judge score rows (3.4 judges per submission). This dataset is the substrate for the cross-model agreement analysis in Section 5.5. The Cape submissions were never seen during methodology development; they function as a held-out validation set.

**BLS occupations.** 342 occupations from the Bureau of Labor Statistics Occupational Outlook Handbook, originally scored for AI exposure by Karpathy's (2025) system using a single Gemini Flash call returning a 0--10 score. We re-scored all 342 occupations using the principled methodology across 9 models from 5 providers (Anthropic, Google, OpenAI, xAI, Zhipu).

### 5.2 Cross-Domain Replication: 342 Occupations

The strongest test of a scoring methodology is whether it generalizes beyond its development domain. We applied the principled framework to Karpathy's AI-exposure scoring task with no modifications to the formula or principles --- only the evaluation criteria and evidence format were adapted.

**Single-model comparison (Gemini Flash).** Naive: mean = 5.31, std = 2.26. Principled: mean = 3.84, std = 3.18. Discrimination ratio = 1.41 (41% improvement). Spearman rho = 0.87. The principled distribution is bimodal: physical jobs cluster near 0 (91 occupations scored 0; roofers, firefighters, agricultural workers) while digital jobs cluster near 10 (19 scored 10; web developers, data scientists). The naive distribution is a bell curve centered at 5.3 --- the characteristic compression of RLHF-trained scoring.

**Discrimination vs. accuracy.** Higher standard deviation alone does not prove better scores --- a random number generator achieves maximal discrimination. We argue the increased discrimination is meaningful for three reasons: (1) rank ordering is preserved (rho = 0.87); (2) the extremes are interpretable; and (3) the naive method's bell curve centered at 5.3 is a known RLHF artifact, not a signal about the underlying distribution.

**Rank disagreements tell a compelling story.** While overall rank correlation is high (rho = 0.87), the cases where naive and principled scoring diverge most are interpretable:

| Occupation | Naive Score | Principled Score | Interpretation |
|-----------|:-----------:|:----------------:|----------------|
| Producers and Directors | 7 | 1.0 | Creative/interpersonal core despite digital tools |
| Kindergarten Teachers | 6 | 0.1 | Physical, interpersonal; AI exposure minimal |
| High School Teachers | 7 | 1.23 | Physical classroom; digital component limited |
| Craft Artists | 6 | 0.53 | Physical medium; AI assists design, not creation |
| Actors | 7 | 1.8 | Physical performance; digital post-production only |

The naive scorer assigns moderate-high scores based on surface-level keyword association (teachers use computers; directors use software). The principled approach, forced to enumerate specific evidence items for and against AI exposure, recognizes that the core work of these occupations is physical or interpersonal.

**Multi-model replication (9 models, 5 providers).** We ran identical evidence-gathering prompts through 9 models. Discrimination improvement over the naive baseline ranged from 21% (GLM-5) to 58% (Sonnet 4.5), with a median of 41%.

**Table 3.** Cross-model comparison on 342 occupations.

| Model | Provider | Mean | Std Dev | Discrim. Improvement | At 0 | At 10 | Avg Items |
|-------|----------|:----:|:-------:|:--------------------:|:----:|:-----:|:---------:|
| Karpathy (naive) | Google | 5.31 | 2.26 | --- | 0 | 1 | --- |
| GLM-5 | Zhipu | 3.03 | 2.73 | 21% | 102 | 9 | 16.9 |
| GPT-5.4 Mini | OpenAI | 6.16 | 3.05 | 35% | 18 | 64 | 18.8 |
| Claude Haiku 4.5 | Anthropic | 4.48 | 3.17 | 40% | 59 | 23 | 19.8 |
| Gemini 3 Flash | Google | 3.84 | 3.18 | 41% | 82 | 25 | 17.3 |
| Claude Opus 4.6 | Anthropic | 4.64 | 3.19 | 41% | 55 | 40 | 18.5 |
| GPT-5.4 | OpenAI | 4.33 | 3.34 | 48% | 78 | 37 | 20.2 |
| Gemini 3.1 Pro | Google | 4.75 | 3.39 | 50% | 63 | 43 | 15.3 |
| Grok 4.20 Beta | xAI | 3.45 | 3.53 | 56% | 122 | 34 | 22.9 |
| Claude Sonnet 4.5 | Anthropic | 3.97 | 3.56 | 58% | 101 | 43 | 19.9 |

Four findings: every model beats naive scoring on discrimination; strong rank agreement across models (Spearman rho 0.77--0.93); no capability-discrimination correlation; provider biases become visible (OpenAI more optimistic, Anthropic / Google / xAI / Zhipu more conservative).

**Prompt confound.** The improvement observed here confounds richer evidence-gathering prompts with the mathematical formula. A "structured prompt, simple aggregation" control would isolate each contribution and is the first priority in future work.

### 5.3 Formula Ablation

We compute scores under eight formula variants applied to four constructed evidence profiles --- profiles designed to exercise the formula's edge cases.

**Table 4.** Formula ablation: final scores under each variant. **Bold** cells indicate pathological behavior.

| Variant | Strong + ample (net=+25, n=25) | Strong + sparse (net=+25, n=4) | Weak + ample (net=-15, n=25) | Evidence farming (net=+40, n=50) |
|---------|:---:|:---:|:---:|:---:|
| **A: Old linear** (no sqrt, mult 0.75--1.25) | **100** | 84 | **20** | **113** |
| **B: Production** (sqrt, mult 0.75--1.0) | 90 | 90 | 26 | 95 |
| C: Linear norm (net/n) | 58 | 90 | 45 | 56 |
| D: Log norm (net/ln(n)) | **100** | 90 | 13 | **100** |
| E: No confidence (mult=1.0) | 90 | **100** | 26 | 95 |
| F: Amplifying (mult 0.75--1.25) | **100** | 93 | **20** | **107** |
| G: Scale 6.0 | 80 | 90 | 32 | 83 |
| H: Scale 10.0 | **100** | 90 | **20** | **100** |

Variant A (old linear) demonstrates the inflation bug: without sqrt normalization, net_impact scales linearly with item count and the evidence-farming profile produces a score of 113 — exceeding the scale maximum. Variant B (production) is correctly bounded. Variant C (linear normalization) over-penalizes volume. Variant E (no confidence) fails on sparse evidence: without regression, the sparse profile (4 items) scores 100. Variant F (amplifying confidence) reintroduces the inflation bug. The two corrections — sqrt normalization and capped regression — are individually necessary and jointly sufficient.

### 5.4 Human Baseline Analysis

**Inter-rater reliability.** Joplin (5 judges, 31 submissions): Krippendorff's alpha = 0.16 (ordinal), ICC(2,1) = 0.0. St. Joseph (4 judges, 17 submissions): alpha = 0.04, ICC(2,1) = 0.0. Both fall far below the 0.667 acceptability threshold (Krippendorff, 2004). For context, academic peer review achieves ICC ~0.2--0.3 (Bornmann et al., 2010).

**Score inflation and judge leniency.** Random intercepts range from +12.9 to -15.2 in Joplin --- a 28-point spread in baseline generosity across judges evaluating the same submissions. This is noise in the Kahneman et al. (2021) sense: unwanted variability reflecting nothing about submission quality.

**Human vs. naive AI (Joplin, uncontaminated).** Spearman rho = 0.068 (p = 0.726). AI mean = 74.65 vs. human mean = 58.54. Low human-AI correlation is expected when human inter-rater reliability is itself poor.

**Methodological caveats.** Panel sizes are small (4--5 judges); the author served as one judge (potential conflict of interest). The specific alpha values are better understood as order-of-magnitude evidence than precise estimates. The broader finding — that human inter-rater agreement falls far below accepted thresholds — is robust to these methodological concerns.

### 5.5 Cross-Model Agreement and Calibration-Conditional Findings (Six-Model v3 Grid)

The 9-model occupation analysis (Section 5.2) shows that *principled scoring produces strong rank agreement across models* on a domain where naive scoring is known to be RLHF-compressed. We extend the cross-model story with a held-out hackathon evaluation: 77 submissions from the Cape Girardeau vibeathon, scored by 264 human judges, evaluated under both naive and principled methods using **six** model families:

- **gpt-5.5** (well-calibrated frontier)
- **deepseek-flash** (calibrated frontier-adjacent)
- **gemini-3-flash** (capable but uncalibrated; inflated naive distribution)
- **gemma4:31b-cloud** (weak/sparse, intermediate)
- **gpt-oss-20b** (open-weight, calibrated naive)
- **nemotron** (weak open-weight, picks-a-number regime)

The same Gemini observer pass produced video observations for all six. Submissions never appeared in the development data; the methodology was fixed before evaluation.

**Table 5.** Six-model v3 grid (vs human, n=77). Bolded cells indicate the regime-defining metric for each model.

| Model | Naive Pearson | Principled Pearson | Naive MAE | Principled MAE | Naive Range | Principled Range | Top-10 overlap (P) | Regime |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.5 | **0.608** | 0.514 | **8.93** | 10.03 | 55.0 | 62.0 | 3 | CALIBRATED — naive wins |
| deepseek-flash | **0.583** | 0.468 | **10.48** | 14.92 | 50.5 | **86.85** | 5 | CALIBRATED, principled over-corrects |
| gemini-3-flash | 0.508 | **0.538** | 16.86 | **9.61** | **73.5** | 64.8 | 5 | INFLATION — principled wins all |
| gemma4 | 0.476 | 0.380 | 14.46 | **11.69** | 67.0 | 63.45 | 4 | WEAK — split |
| gpt-oss-20b | 0.453 | 0.355 | **9.86** | 14.64 | 41.5 | 67.8 | 5 | CALIBRATED, principled over-corrects |
| nemotron | **0.361** | 0.371 | 10.64 | 13.36 | **44.5** (compressed) | 56.4 | 3 | PICKS_A_NUMBER — both fail |
| Existing AI baseline | 0.491 | --- | 14.07 | --- | 67.78 | --- | 2 | reference |

Five findings emerge:

**Finding 1: Principled wins everything when naive is inflated.** gemini-3-flash exhibits the most inflated naive distribution in the grid: range 73.5, multiple submissions at 100 / 98 / 96.5. Under principled, every aggregate metric improves: Pearson 0.508 → 0.538, MAE 16.86 → 9.61, top-10 overlap 3 → 5. This is the clean "what the methodology was designed for" outcome.

**Finding 2: Principled over-corrects on already-calibrated models.** gpt-5.5, deepseek-flash, and gpt-oss-20b all show the same pattern: naive Pearson higher than principled Pearson and naive MAE lower than principled MAE. The v3 counter-bias instructions were tuned against gemini-class inflation; on already-calibrated models they pull principled too far down. On deepseek-flash, the principled range balloons to 86.85 — a clear deflation signature.

**Finding 3: nemotron is the textbook PICKS_A_NUMBER case.** Naive Pearson 0.361 is the lowest in the grid. Naive range is 44.5 (the narrowest). 19 of 77 submissions land in the 70--85 band on naive — a textbook "picks a number around 75" pattern. Principled barely moves the Pearson (+0.01) and makes MAE worse (10.64 → 13.36). When the underlying signal is weak and clustered around a single number, the methodology cannot rescue it.

**Finding 4: gemma4 is genuinely split.** Principled MAE wins (14.46 → 11.69), but principled Pearson loses (0.476 → 0.380). The formula is doing useful absolute-error work without rescuing rank correlation.

**Finding 5: The naive↔principled MAE divergence is a six-point diagnostic curve.**

| Model | Naive↔Principled MAE | Interpretation |
|---|---:|---|
| gpt-5.5 | 4.67 | Methods agree closely (calibrated) |
| nemotron | 9.46 | Methods agree on weak signal (both fail) |
| deepseek-flash | 10.95 | Mild divergence (over-correction) |
| gpt-oss-20b | 11.54 | Moderate divergence (over-correction) |
| gemma4 | 15.60 | Large divergence (weak model deflation) |
| gemini-3-flash | 17.85 | Largest divergence (correctly fixing inflation) |

The divergence tracks model-strength × naive-calibration. The diagnostic value: *if a practitioner observes large naive↔principled MAE divergence on their data, exactly one of naive or principled is wrong*, and the next step is to determine which.

**The calibration-conditional thesis is now empirically grounded across six models.** Section 6.4 develops the regime taxonomy that makes this actionable.

### 5.6 Adjacent Empirical Studies (cross-references)

Three cross-domain rescoring studies are summarized in companion writeups (`examples/`). (1) An *impeccable rescoring analysis* applies Principles 1--5 to Bakaus' (2025) Nielsen heuristics scoring system, showing how the same agent reaching the same end state via different paths receives identical scores under the existing pipeline (1.0 success) but 76 vs. 59 under signed evidence items. (2) A *cua-bench analysis* notes that Principle 7 (deterministic separation) is satisfied by construction in cua-bench's runner architecture, while Principles 2--6 remain wide open --- the methodology generalizes to deterministic agent benchmarks via richer multi-signal evidence, not via adding an LLM judge. (3) A *karpathy-jobs distribution analysis* documents the 9-model bimodal pattern across 342 occupations as the cleanest single visual signature of the bell-curve-to-bimodal transition.

### 5.7 Calibration Probe: A 30-Second Synthetic Diagnostic

**Motivation.** The six-model grid in Section 5.5 demonstrates that the methodology's value is regime-dependent, and that running the full pipeline (77 submissions × naive + principled × Gemini observer) takes hours and costs real money. A practitioner who wants to know *whether to invest in the full pipeline* needs a much cheaper diagnostic. We introduce one.

**The probe.** A *calibration probe* is a synthetic rating prompt with no ground truth, applied to a model many times under the same prompt and items, with the goal of classifying the model's *number-picking behavior shape* — its rating distribution — into one of five regimes. The reference implementation accepts a system prompt, an items file (default: 20 generic English sentences spanning quality levels), a temperature, and a repeat count.

**Five regimes.**

| Regime | Definition | Methodology recommendation |
|---|---|---|
| **CALIBRATED** | range ≥ 5 (1-10 scale), floor_rate ≥ 0.05, ceiling_rate < 0.35 | Lighter touch (Principles 1, 4, 5). Model already discriminates; full pipeline may over-correct. |
| **INFLATION_LIKELY** | ceiling_rate ≥ 0.25 AND floor_rate < 0.05 | Full pipeline. Methodology is designed for exactly this case. |
| **DEFLATION_LIKELY** | floor_rate ≥ 0.25 AND ceiling_rate < 0.05 | Caution: methodology may over-correct. Lighter touch + audit. |
| **PICKS_A_NUMBER** | range ≤ 2 (after extremes ruled out) | Methodology cannot rescue. Switch model or accept that signal is weak. |
| **JITTERY** | mean per-item std ≥ 2.5 | Weak model; reliability is the constraint. Use ensembling over methodology. |
| AMBIGUOUS | none of the above | Default: full pipeline with audit. |

The classifier checks regimes in this order: JITTERY → INFLATION_LIKELY → DEFLATION_LIKELY → PICKS_A_NUMBER → CALIBRATED → AMBIGUOUS. Order matters because high per-item std makes the distribution-shape rules unreliable (so JITTERY is checked first), and extreme-cluster cases must be classified as inflation/deflation before falling into PICKS_A_NUMBER.

**Predictive validity (predicted, not yet validated).** The six v3 models in Section 5.5 should classify cleanly into the regimes:

| Model | Section 5.5 behavior | Predicted probe regime |
|---|---|---|
| gpt-5.5 | Naive wins, methods agree | CALIBRATED |
| deepseek-flash | Naive wins, principled deflates | CALIBRATED |
| gpt-oss-20b | Naive wins, principled deflates | CALIBRATED |
| gemma4 | Split — principled MAE wins, naive Pearson wins | CALIBRATED or AMBIGUOUS |
| gemini-3-flash | Principled wins all; naive 100s/98s | INFLATION_LIKELY |
| nemotron | Both Pearson ≈ 0.36, naive range 44.5, mode in 70--85 | PICKS_A_NUMBER |

A successful validation looks like five of six predictions landing.

**Why a 30-second probe is a contribution.** Naive vs. principled comparison on a real domain takes hours and requires ground truth. The probe takes 30 seconds, requires zero ground truth, and answers the question *"is my model in a regime where the methodology will help?"* — a strictly weaker but strictly cheaper question. The probe is **not** a replacement for the full evaluation; it is a preflight check. Practitioners who run the probe and observe CALIBRATED can deploy lighter touch confidently. Practitioners who observe INFLATION_LIKELY can deploy the full pipeline confidently. Practitioners who observe PICKS_A_NUMBER or JITTERY know their model is the bottleneck, not the methodology.

**Probe item design.** The default 20-item probe asks for sentence-structure ratings on a 1--10 scale, with items deliberately spanning quality from "Me go store" (broken) to grammatically immaculate prose. Sentence-structure was chosen as a domain-neutral test that any sufficiently capable LLM should handle competently — the probe tests the *number-picking shape*, not domain knowledge. Practitioners who want to test domain-specific calibration can substitute their own items file.

**Acknowledged limitation: domain transfer.** A model that probes CALIBRATED on sentence-structure might still inflate on hackathon submissions, because hackathon-positivity is in the training data. Probe-as-preflight is a cheap-but-imperfect signal; probe-plus-domain-validation (10--15 ground-truth items) is the more defensible flow.

---

## 6. Discussion

### 6.1 Design Decisions

**Discrete impact scores vs. continuous scales.** The set {+5, +3, +2, +1, -1, -2, -3, -5} forces magnitude commitment. A continuous scale allows hedging with +2.3, producing the same middle-clustering that plagues direct score assignment. The gaps in the scale (no +4, no -4) are deliberate: they force categorization rather than interpolation.

**sqrt normalization vs. alternatives.** Linear normalization (net/items) penalizes volume too aggressively (Table 4, variant C). Log normalization provides weaker diminishing returns, producing clamping at extremes (variant D). sqrt is the natural choice from classical test theory and the Pareto-optimal trade-off in our ablation.

**Downward-only regression.** Capping the multiplier at 1.0 rather than allowing 1.25 prevents the inflation failure mode demonstrated in variants A and F. Sparse evidence should produce conservative scores, but abundant evidence should never amplify beyond what the evidence supports.

**JSON output shape.** *The order of fields in the JSON output structure affects whether the score commits to evidence or to a number-pick*. Practitioners adopting the methodology should specify reflection-first, evidence-second, score-last in the JSON shape, even when the prompt text instructs the same thing in prose.

**Probe-as-preflight.** Section 5.7's calibration probe is a design decision as much as a diagnostic: the methodology is shipped with its limitations made measurable. The probe costs 30 seconds and returns a regime label; deploying without it is a choice, not an oversight.

### 6.2 Limitations

**Head-to-head experiment incomplete on the original 17 submissions.** The within-domain comparison of naive vs. principled on the original 17 St. Joseph submissions remains pending. The Cape Vibeathon analysis (Section 5.5) is a stronger held-out validation but uses different submissions.

**Prompt confound not disentangled.** The observed improvement in the Karpathy replication confounds richer evidence-gathering prompts with the mathematical formula. A "structured prompt, simple aggregation" control would isolate each contribution.

**Principles 6 and 7 not individually ablated.** The formula ablation (Section 5.3) isolates Principles 1, 3, 4, and 5. Principles 6 (multiple perspectives) and 7 (cross-modal synthesis) are presented as design principles supported by theoretical argument and prior work; pipeline-level ablation is needed to validate them individually.

**Single-evaluator reliability.** Each submission receives one evaluation per system version. Inter-run agreement (test-retest) has not been measured systematically.

**No confidence intervals on key statistics.** Headline metrics are reported without bootstrap confidence intervals.

**Probe predictive validity not yet measured.** Section 5.7 predicts how the six v3 models should classify under the probe but has not yet run the probe on those models. The validation is the highest-priority empirical task in v0.8.x.

**Demo_quality regression (confirmed limitation, see Section 6.6).** Under v3 prompts, all six models show worse demo_quality MAE under principled than naive — a confirmed regression that requires a per-criterion item floor before production deployment.

**Author-as-judge.** Kevin Kirchner served as both paper author and human judge in the original 17-submission St. Joseph dataset. This concern does not extend to the Cape Vibeathon analysis (no author scoring).

**Additive scoring limitation.** The formula allows positive items to offset critical negatives. In domains where a single finding is dispositive (e.g., a critical security vulnerability), a pass-fail circuit-breaker is needed alongside the scoring formula.

**Emotional judgment gaps.** Human judges assess dimensions — presenter presence, emotional resonance, authenticity, team dynamics — that AI systems address only partially. This remains an honest limitation rather than a solved problem.

### 6.3 Generalizability

The seven principles address failure modes that are not specific to hackathon judging. The five validated principles transfer to new domains through mechanical adaptation; the two design principles (6 and 7) degrade gracefully in single-modality or single-perspective settings.

Adapting the framework involves five steps: (1) define a perspective-criterion matrix (or a flat criterion-only structure), (2) specify the evidence format, (3) calibrate three parameters (evidence density denominator, scaling constant, regression strength) on 5--10 representative artifacts, (4) design the independence architecture, and (5) **run the calibration probe on the candidate model to confirm it is in a regime where the methodology helps**. Step 5 makes generalization decisions evidence-based rather than aspirational.

### 6.4 When Naive Wins: A Regime Taxonomy and the Over-Correction Pattern

A central methodological honest moment in this version is recognizing that *the principled formula is not always better than the naive baseline* — confirmed across **six models**. Section 5.5 demonstrated that gpt-5.5, deepseek-flash, and gpt-oss-20b naive all beat their own principled runs on Pearson and MAE, while gemini-3-flash principled beat naive on every metric, and nemotron showed both methods stuck near Pearson 0.36 on a compressed range. The pattern resolves under a single explanation: *the formula pays for itself when model calibration is the bottleneck, and can over-correct when calibration is already adequate*.

**The regime taxonomy.** With six v3 models we can now name the regimes empirically:

| Regime | Empirical exemplars | Formula behavior |
|---|---|---|
| **CALIBRATED** | gpt-5.5 (Pearson 0.608), deepseek-flash (0.583), gpt-oss-20b (0.453, calibrated naive) | Naive wins on Pearson and MAE. Principled may over-correct via counter-bias. |
| **INFLATION_LIKELY** | gemini-3-flash (range 73.5, multiple 100s/98s, naive MAE 16.86) | Principled wins everything. Methodology was designed for this case. |
| **WEAK / SPLIT** | gemma4 (Pearson 0.476/0.380; MAE 14.46/11.69) | MAE improves under principled, Pearson does not. Mixed signal; lighter touch + audit. |
| **PICKS_A_NUMBER** | nemotron (Pearson ≈0.36 both methods, range 44.5) | Methodology cannot rescue. Switch model or accept weak signal. |
| **DEFLATION_LIKELY** (de facto, observed under v3 over-correction) | deepseek-flash principled (range 86.85) | The v3 counter-bias overshooting on a calibrated model produces a *deflation signature* even on a model that is not intrinsically deflated. |

**The 3-of-6 over-correction pattern.** Three of six models show principled losing to naive on the headline metrics: gpt-5.5, deepseek-flash, gpt-oss-20b. All three have CALIBRATED naive distributions. The v3 counter-bias instructions ("skeptic's eye", "two honest items > five invented", "README claims without code → negative item") are correctly calibrated for inflated models and over-correct on already-calibrated models. The fix is not to remove the counter-bias (gemini benefits from it) but to make it *model-conditional*. Future work item: a model-specific counter-bias dial driven by a probe-derived regime label.

**Why this happens.** When the model is well-calibrated on the task, asking it for richer evidence collection introduces opportunity for asymmetric item lists *in the negative direction* under v3's strong counter-bias prompts. The formula faithfully aggregates the asymmetric items, producing deflation. The model's *calibrated number-pick* was already a better summary than the *uncalibrated, counter-bias-tilted evidence collection*. When the model is inflated, the counter-bias overrides the model's miscalibration; the items are asymmetric in informative ways, and the formula does the work the model could not.

**The fix: model-conditional counter-bias and item-side caps.** Two complementary moves:

1. **Probe-driven counter-bias dial.** Use the regime label (Section 5.7) to choose the counter-bias strength: full strength on INFLATION_LIKELY, half on AMBIGUOUS / WEAK, off on CALIBRATED.

2. **Positive:negative ratio cap per criterion** (e.g., maximum 2:1 in either direction). Prevents asymmetric evidence in either direction.

**The reframe: contribution is conditional, but stronger for it.** The thesis is not "principled always beats naive." The thesis is: *the formula closes the gap when calibration is the bottleneck (INFLATION_LIKELY), preserves rank correlation under over-correction (CALIBRATED with v3), provides MAE work without rank rescue under weak signal (WEAK / SPLIT), and cannot rescue intrinsically weak models (PICKS_A_NUMBER, JITTERY)*. This conditional framing is *more honest* than the unconditional version and *more useful* to practitioners.

**Diagnostic tools, not just a formula.** A practical implication is that the methodology should ship with calibration diagnostics:

1. *Pre-flight calibration probe* (Section 5.7): 30-second synthetic test, classifies into one of five regimes.
2. *Confidence-weighted naive variant*: collect the model's self-reported confidence on each naive score; if `naive_weighted_conf_weighted` closes a gap to humans that the unweighted naive does not, the model knows when it's wrong.
3. *Item-side asymmetry audit*: for any principled run, log positive:negative item counts per criterion. Ratios >2:1 in *either* direction are flags.
4. *Naive↔Principled MAE divergence diagnostic*: if the divergence is small (< 5), methods agree and naive is fine; if large (> 12), exactly one method is wrong and ground truth is needed to know which.

These diagnostics make the conditional framing actionable rather than philosophical.

### 6.5 The Field's Current Trajectory

Section 2.2 catalogs the Spring 2026 wave. The trajectory is unmistakable: the field is openly conceding that frontier LLM judges are unreliable scoring primitives. What remains contested is the prescriptive answer. Three families have emerged:

- **Better calibration of the same number-pick** (conformal prediction approaches): post-hoc intervals around the LLM's score.
- **Better aggregation across panels of number-picks** (PoLL, criteria ensembling): variance reduction via ensembling, but the LLM still picks numbers per panelist.
- **Decomposition + math** (this paper, RULERS, RRD, HumorRank, DeepRed, CheckEval): the LLM does not pick numbers; structural separation between evidence and computation.

The first two families are surface-level fixes; the third is structural. The empirical evidence consistently favors the third. This paper supplies the unifying psychometric framework for the third family, with the calibration-conditional caveat developed in Section 6.4 and the regime probe operationalizing it.

### 6.6 Demo_quality Regression: A Confirmed Limitation Requiring v4 Prompt Fix

A confirmed cross-model regression deserves its own discussion section because the failure pattern is identical across all six v3 models we tested. Under v3 prompts, naive demo_quality MAE is uniformly better than principled demo_quality MAE:

| Model | Naive demo_quality MAE | Principled demo_quality MAE | Regression |
|---|---:|---:|---:|
| gpt-5.5 | 13.55 | 26.53 | +12.98 |
| deepseek-flash | 16.52 | 29.44 | +12.92 |
| gemini-3-flash | 15.45 | 23.43 | +7.98 |
| gemma4 | 18.04 | 29.61 | +11.57 |
| gpt-oss-20b | 13.50 | 24.74 | +11.24 |
| nemotron | 16.10 | 26.98 | +10.88 |

The pattern is universal — every model loses 8--13 MAE points on demo_quality going naive→principled. No other criterion shows this universal regression.

**The mechanism.** Demo quality is the criterion most likely to have *zero or one items* per submission under v3's flat evidence list. A sparse criterion with 0--1 items has `evidence_density` close to 0 for that criterion when computed locally, and the density multiplier pulls the criterion's contribution hard toward 50. Worse: when criterion-level density is low and the formula is computed across all criteria pooled, the multiplier averages out, *but the criterion's signal contribution is dominated by the noise of its 0--1 items*. The result: demo_quality scores for sparse-evidence submissions cluster near 50, while their human scores span the full range — and MAE balloons.

**The fix (proposed).** Two complementary moves:

1. **Per-criterion item floor.** Require at least 2 items per criterion in the v4 prompts. Models that can only justify 1 item should write 2 (forcing more careful examination) or downweight the criterion explicitly. One-line prompt addition.

2. **Density-multiplier floor at the criterion level.** When computing per-criterion scores, apply a minimum density multiplier of 0.6 (or similar) so that even a 0-item criterion produces a calibrated regression rather than dominating noise.

Both are testable on existing evidence data (no new API calls required).

**Why we report this rather than hide it.** A 6-of-6 universal regression on a single criterion is empirical evidence about how prompt design at the per-criterion level interacts with the formula. Hiding the regression would be dishonest and less useful; reporting it gives the next practitioner a known failure mode to fix on their first deployment.

---

## 7. Conclusion

The default approach to LLM-based evaluation --- asking the model to assign a score --- inherits and amplifies the noise Kahneman et al. (2021) documented in human judgment. Seven principles, grounded in classical psychometric theory, address five structural failure modes: score inflation, undifferentiated confidence, single-perspective bias, cross-modal blindness, and prompt-perturbation instability.

The mathematical core is a scoring formula where LLMs collect structured evidence and statistical corrections compute calibrated scores. Formula ablation confirms that sqrt normalization and capped confidence regression are individually necessary and jointly sufficient. Cross-domain validation on 342 occupations across 9 models and 5 providers demonstrates that the methodology generalizes: discrimination improvement ranges from 21% to 58% (median 41%), with strong cross-model rank agreement (rho = 0.77--0.93).

A held-out cross-model evaluation on 77 hackathon submissions across **six** model families surfaces a calibration-conditional regime structure: principled rescoring wins on every aggregate metric for the most-inflated model (gemini-3-flash), can over-correct on already-calibrated models (3 of 6: gpt-5.5, deepseek-flash, gpt-oss-20b), and cannot rescue intrinsically weak models (nemotron, PICKS_A_NUMBER). The naive↔principled MAE divergence forms a clean six-point diagnostic curve. We complement the formula with a 30-second synthetic *calibration probe* that classifies a model into one of five regimes — CALIBRATED, INFLATION_LIKELY, DEFLATION_LIKELY, PICKS_A_NUMBER, or JITTERY — *before* the practitioner runs the full pipeline.

The practical contribution is methodological, cautionary, conditional, and diagnostic. The methodology provides a concrete, deployable alternative to naive LLM scoring --- and practitioners can adopt its core benefits through three changes alone (Principle 1: separate evidence from scoring; Principle 4: normalize by sqrt of item count; Principle 5: regress sparse evaluations toward the mean). The caution: human evaluation is itself unreliable (alpha = 0.04--0.16 in our data), and the goal of automated evaluation should not be matching human scores but exceeding human consistency. The conditional: the formula pays for itself when model calibration is the bottleneck; lighter touch is preferable when calibration is already adequate. The diagnostic: a 30-second probe tells practitioners *before they run the methodology* whether their model is in the helpful regime. A confirmed limitation: the v3 prompts produce a per-criterion demo_quality regression on all six models tested, requiring a per-criterion item floor before v0.8 production deployment.

**Future work.** We organize remaining work into three tiers.

*Recomputation from existing data* (no new API calls):

1. **Run the calibration probe on the six v3 models in Section 5.5 and validate the regime predictions.**
2. **Implement the per-criterion item floor (Section 6.6) as a v4 prompt revision and recompute demo_quality MAE on existing evidence data.**
3. Disentangle evidence elicitation from mathematical correction via a prompt-only control that computes scores as a simple mean of existing evidence items.
4. Run formula ablation (8 variants) on the real 342-occupation evidence to supplement the analytical profiles.
5. Compute bootstrap 95% confidence intervals on headline statistics across all six v3 models.
6. Conduct sensitivity analysis on the evidence density threshold.
7. Audit gpt-5.5, deepseek-flash, and gpt-oss-20b principled item lists for positive:negative ratio asymmetry.
8. Cross-tabulate `model_confidence_mean` (naive) against `|naive - human|` --- a free overconfidence diagnostic from existing data.

*Experiments requiring modest new data*:

9. **Implement and test the model-specific counter-bias dial** driven by probe-derived regime labels.
10. **Implement and test the positive:negative ratio cap** (Section 6.4) as a fix for principled over-correction on calibrated models.
11. Complete the within-domain head-to-head comparison on the original 17 hackathon submissions.
12. Measure inter-run reliability (3--5 repeated runs on a sample of items).
13. Run the v3 prompts on the original 9-model occupation grid; compare cross-model agreement to the v2 numbers reported in Section 5.2.

*Experiments requiring significant new data*:

14. Ablate Principles 6 and 7 at the pipeline level.
15. Adapt to additional domains (customer service QA, code review, legal evaluation, medical chatbot completeness).
16. Design a pass-fail circuit-breaker for compliance-critical domains.
17. Validate the calibration-conditional decision rule on a multi-domain test bed.
18. Build a probe item library spanning multiple domains (sentence-structure, business-viability, code-readability, headline-strength) and measure whether regime labels are model properties or domain properties.

The field's current trajectory --- asking ever-more-capable models to assign scores, then calibrating after the fact --- treats the symptom rather than the disease. Reliability emerges not from model capability but from methodological structure: separating observation from scoring, grounding confidence in evidence, applying the statistical corrections that psychometricians have understood for decades, *and* shipping a 30-second probe so practitioners know when calibration is the bottleneck. The path forward requires the discipline to never let the LLM pick a number --- and the wisdom to know which regime your model is in before deciding how much structure to apply.

---

*Appendices on emotional judgment dimensions (A), per-criterion human reliability tables (B), industry convergence brief (C), the calibration-conditional decision rule (D), and the calibration probe specification (E) follow the same structure as the working paper drafts. This file mirrors the v0.8.0 draft as of May 2026.*

---

## Appendix A: Emotional Judgment Gap Analysis

**Table A1.** Emotional judgment dimensions assessed by human judges but largely absent from AI evaluation.

| Category | Dimensions | AI Coverage | Gap |
|----------|-----------|:-----------:|:---:|
| Presenter Presence & Delivery | Confidence, enthusiasm, vocal dynamics, pacing, body language | 1 partial | 5 |
| Emotional Resonance & Storytelling | Narrative arc, emotional hook, build journey, impact demonstration, audience connection | 2 partial | 4 |
| Authenticity & Trust | Genuineness, passion, trust signals, appropriate humility | 0 | 4 |
| Team Dynamics | Multi-presenter chemistry, role clarity, collaborative energy, complementary strengths | 0 | 4 |
| Entertainment & Engagement | Humor, audience engagement, memorability, "wow factor" | 1 partial | 3 |
| Production Aesthetics | Visual design, slide quality, demo flow, audio quality | 2 | 2 |
| **Total** | **26** | **~3 partial** | **~20** |

The video analysis pipeline addresses the highest-priority gaps through behavioral observation and skeptical interpretation. Three formalized criteria — Presenter Presence (10% of demo quality weight), Emotional Storytelling (10%), and Authenticity (5%) — provide structured partial coverage.

---

## Appendix B: Detailed Human Baseline Statistics

**Per-criterion reliability.** Krippendorff's alpha by criterion ranges from 0.0 to 0.37. No single criterion achieves acceptable reliability at either event.

| Criterion | Joplin | St. Joseph |
|-----------|:------:|:----------:|
| Impact & Relevance | 0.00 | 0.05 |
| Demo Quality | 0.05 | 0.26 |
| Feasibility | 0.36 | 0.05 |
| Innovation | 0.37 | 0.12 |
| User Experience | 0.20 | 0.34 |

**Judge leniency intercepts** (Joplin): random intercept estimates range from +12.86 (Charles Elliott) to -15.18 (Lori Worthington) — a 28-point spread in baseline generosity across judges evaluating the same submissions.

**Score inflation.** Joplin weighted mean = 60.97 vs. midpoint 55.0 (t = 3.46, p < 0.001). St. Joseph weighted mean = 73.86 vs. midpoint 55.0 (t = 10.53, p < 0.001).

**Human vs. AI per-criterion correlations (Joplin).** Spearman rho by criterion: impact relevance = 0.229, demo quality = 0.126, feasibility = 0.178, innovation = 0.091, user experience = -0.013. All non-significant.

---

## Appendix C: Industry Convergence Brief

**Vendor moves.** Amazon Nova rubric-based LLM judge (AWS ML Blog, 2026) generates per-criterion rubrics with justifications and reports +49% on complex JudgeBench scenarios. Mistral Workflows (April 2026) ships durable execution and `wait_for_input()` for human-in-the-loop, conspicuously omits any scoring layer. Apple Foundation models (early 2026) use rubric-based reward modeling in post-training.

**Open-source convergence.** Lechmazur/writing (2026) retired its 0--10 absolute rubric after 9,139 score rows and switched to Bradley-Terry pairwise tournaments. Karpathy/jobs (2025) provides the cleanest "before" signal for naive LLM scoring. Cua-bench (2026) satisfies Principle 7 by construction. Impeccable (Bakaus, 2025) keeps 10-integer LLM scoring inside an otherwise-clean architecture; a worked rescoring is in `examples/impeccable-rescoring.md`.

**The pattern.** Decomposition-first and pairwise-first trajectories. Both reject the naive single-LLM number-pick. The principles of this paper unify both moves under a single statistical framework.

---

## Appendix D: The Calibration-Conditional Decision Rule (Probe-Driven)

```
function adoption_recommendation(model, task, items_file=DEFAULT_PROBE):
    regime = run_calibration_probe(model, items_file, repeats=30)

    if regime in {"PICKS_A_NUMBER", "JITTERY"}:
        return "SWITCH_MODEL_OR_ACCEPT_WEAK_SIGNAL"

    if regime == "INFLATION_LIKELY":
        return "FULL_PIPELINE_FULL_COUNTER_BIAS"

    if regime == "DEFLATION_LIKELY":
        return "FULL_PIPELINE_REDUCED_COUNTER_BIAS"

    if regime == "CALIBRATED":
        return "LIGHTER_TOUCH_OR_FULL_PIPELINE_NO_COUNTER_BIAS"

    return "FULL_PIPELINE_WITH_AUDIT"   # AMBIGUOUS regime
```

**Worked example (six-model deployment).** Run the probe on each candidate model. gpt-5.5, deepseek-flash, gpt-oss-20b → CALIBRATED → lighter touch. gemini-3-flash → INFLATION_LIKELY → full pipeline + full counter-bias. gemma4 → AMBIGUOUS → full pipeline + audit. nemotron → PICKS_A_NUMBER → switch model or accept weak signal. Six model-specific deployment recommendations, derived in ~3 minutes total of probe time.

This rule is *empirical*, anchored in the six-model Cape Vibeathon evaluation (Section 5.5).

---

## Appendix E: Calibration Probe Specification

### E.1 Item file format (JSON)

```json
{
  "name": "sentence-structure",
  "scale_min": 1,
  "scale_max": 10,
  "items": [
    "Me go store yesterday and buyed milk and breaded.",
    "I went to the store yesterday and bought milk and bread.",
    "Yesterday, having concluded my workday with what could only be described as the kind of weariness that settles into one's bones, I made the deliberate decision to visit the local market.",
    "..."
  ]
}
```

The default 20 items span quality from broken fragments (rated ~1--2) through mediocre but functional (~5--6) to carefully constructed (~9--10). A model using the full scale should produce some 1s, some 5s, and some 9s/10s.

### E.2 System prompt

The default system prompt instructs the model to rate each sentence on a 1--10 scale for sentence structure quality, defining bands explicitly: 1--2 broken or ungrammatical, 3--4 present but flawed, 5--6 average, 7--8 above average, 9--10 exceptional. The prompt emphasizes that the *full scale should be used*.

### E.3 Output structure

```
runs-probes/<run_name>/
├── probe-config.json      # what was run
├── user-prompt.txt        # exact rendered prompt for reproducibility
├── run-001.json           # per-run scores + raw response
├── ...
├── run-NNN.json
├── aggregate.json         # per-item mean/std/mode/range + across-runs distribution stats
└── REPORT.md              # human-readable summary with regime guess, histogram, top-5 most variable items
```

### E.4 Five-regime classifier rules

The classifier checks regimes in this order; first match wins.

| # | Regime | Rule |
|---|---|---|
| 1 | JITTERY | mean_per_item_std ≥ 2.5 |
| 2 | INFLATION_LIKELY | ceiling_rate ≥ 0.25 AND floor_rate < 0.05 |
| 3 | DEFLATION_LIKELY | floor_rate ≥ 0.25 AND ceiling_rate < 0.05 |
| 4 | PICKS_A_NUMBER | range ≤ 2 (after inflation/deflation rule out the extremes) |
| 5 | CALIBRATED | range ≥ 5 AND floor_rate ≥ 0.05 AND ceiling_rate < 0.35 |
| 6 | AMBIGUOUS | none of the above |

Where `ceiling_rate` = fraction of all (item × repeat) ratings at the scale maximum, `floor_rate` = fraction at the scale minimum, `range` = max − min across all ratings, `mean_per_item_std` = average within-item standard deviation across repeats.

**Order of checks matters.** JITTERY is checked first because high per-item std makes the distribution-shape rules unreliable. Extreme-cluster cases (lots of 10s, no 1s) must be classified as INFLATION_LIKELY before falling into PICKS_A_NUMBER, because a tight cluster *at the ceiling* is a different problem than a tight cluster in the middle.

### E.5 Recommended invocation

```
python3 probe.py \
  --prompt prompts/sentence-structure-system.md \
  --items items/sentence-structure.json \
  --temperature 0.7 \
  --repeats 30 \
  --out runs-probes/<model-name>-sentence-30reps-temp07
```

Rationale for defaults:
- Temperature 0.7 elicits the model's natural distribution. Temperature 0 collapses to mode-only.
- Repeats 30 is sufficient for stable per-item std estimates. Repeats 100 gives a tighter distribution but adds 3x cost.
- Default 20-item sentence-structure prompt is domain-neutral; substitute domain-specific items if the practitioner suspects domain-specific miscalibration.

### E.6 Validation protocol

1. Run the probe on the six v3 models at temperature 0.7, repeats 30.
2. Compare the regime label to the predicted label in Section 5.7.
3. Five of six matching is sufficient for the probe to be a useful preflight diagnostic.
4. If the probe fails to predict more than two of six, the diagnostic is domain-specific; build a probe item library spanning multiple domains.

### E.7 Honest caveat

The probe measures *generic* number-picking on a synthetic task. A model classified CALIBRATED on sentence-structure could still inflate on hackathon submissions because hackathon-positivity is in the training data. The probe likely catches the worst cases (extreme inflation, extreme clustering, weak signal) but may miss domain-specific miscalibration. Probe-as-preflight is a cheap-but-imperfect signal; the most defensible flow is probe + 10--15 ground-truth items in the deployment domain.
