# Don't Let the LLM Pick a Number: Seven Principles for Evidence-Based LLM Scoring

**Kevin Kirchner**
Codefi Foundation

---

## Abstract

Don't let the LLM pick a number. Seven principles, grounded in classical psychometric theory, separate evidence collection from score computation: the LLM finds structured evidence; mathematical corrections derive calibrated scores. Cross-domain validation on 342 occupations scored by 9 models from 5 providers shows discrimination improvements of 21--58% (median 41%) over naive scoring, with preserved rank ordering (Spearman rho = 0.87) and strong cross-model agreement (rho = 0.77--0.93). Formula ablation confirms that sqrt normalization and capped confidence regression are individually necessary and jointly sufficient. Human baseline analysis reveals inter-rater reliability far below accepted thresholds, establishing the floor that principled automation must exceed.

---

## 1. Introduction

AI systems increasingly need to evaluate, score, and rank artifacts. Hackathon submissions, code review pull requests, customer service interactions, compliance documents, content moderation decisions --- across domains, organizations face the same question: can we automate evaluation that currently depends on scarce human expert judgment? The dominant default is seductively simple: ask an LLM to "rate this 0--100" and use the number it produces. This approach is fast to build. It is also, as we demonstrate empirically, unreliable.

Kahneman, Sibony, and Sunstein (2021) established that even human experts exhibit substantial unwanted variability (*noise*) in judgments that should ideally be identical. AI evaluators inherit this problem and amplify it through four structurally distinct failure modes:

**Score inflation.** LLM scorers produce median scores clustering in the 70--85 range regardless of quality. In our dataset, a naive AI scorer produced a mean weighted score of 74.65 compared to the human mean of 58.54 --- a 16.1-point gap --- with Spearman rank correlation of rho = 0.068 (p = 0.726), indicating essentially no agreement on relative ordering.

**The "everything is above average" problem.** RLHF training biases LLMs toward helpful, affirming outputs rather than discriminating ones. Xiong et al. (2024) document how RLHF induces overconfidence that persists after calibration attempts; Wei et al. (2025a) show poor calibration across tasks.

**Evidence-agnostic confidence.** A model that examined three files reports the same confidence as one that examined thirty, making self-reported confidence useless as a reliability indicator (Kadavath et al., 2022).

**Cross-modal blindness.** When code and video are evaluated in isolation, cross-modal contradictions go undetected. Zhang et al.. (2024) found that multimodal LLMs achieve only ~0.64 cross-modal consistency.

These four failure modes are not theoretical --- they manifest in production systems built by expert practitioners. Karpathy's (2025) AI-exposure scoring system illustrates the point. The system scores 342 occupations for AI exposure using a single Gemini Flash call that returns a 0--10 score. Its rubric includes anchored examples at each score level, following established rubric design principles (Jonsson and Svingby, 2007) --- yet it still defaults to asking the LLM to pick a number. When we re-scored those same 342 occupations using our principled methodology (Section 5), the naive approach compressed scores into a bell curve centered at 5.3, while the evidence-based approach produced 21--58% greater score separation (median 41% across 9 models) with rho = 0.87 rank correlation. The failure is structural, not a matter of rubric quality.

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

The primary contribution of this paper is the scoring methodology itself --- the seven principles and their mathematical instantiation. We validate the framework through cross-domain replication (342 occupations, 9 models, 5 providers), formula ablation isolating each component's contribution, and human baseline analysis establishing the reliability floor that automated evaluation must exceed. The methodology was developed in the context of hackathon judging (17 submissions, 5 system versions over 3 days), which serves as the motivating application and provides the human comparison data (Appendices A and B).

---

## 2. Related Work

### 2.1 LLM-as-Judge Foundations

Zheng et al. (2023) established LLM-based evaluation with MT-Bench, demonstrating >80% human preference agreement while documenting position bias, verbosity bias, and self-enhancement bias. Wang et al. (2023) showed position bias severe enough to reverse rankings, supporting decomposed pointwise scoring over pairwise comparison. Li et al. (2024) and Li et al. (2025) provide comprehensive taxonomies identifying calibration as an open problem.

The response to documented biases has been progressive decomposition. G-Eval (Liu et al., 2023) established "reason first, score second" via chain-of-thought. FLASK (Ye et al., 2024) introduced 12-dimension criterion-level decomposition but still relies on LLM scoring per dimension. CheckEval (Lee et al., 2024) removes the LLM from final score computation by decomposing evaluation into binary checklist items --- the closest prior work to our approach --- but discards magnitude information: a critical security vulnerability and a minor typo are both single checklist items. Our system assigns impact scores from {+5 to -5}, preserving severity. RocketEval (Wei et al., 2025b) achieves 0.965 Spearman correlation with a three-stage pipeline but operates in a single modality, uses a single model family, and applies no statistical corrections. Its reweighting requires labeled training data absent in novel domains.

Concurrent work reinforces urgency: Gu et al. (2025) provide empirical proof that identical inputs receive different scores across models; Huang et al. (2025) demonstrate that pointwise scoring creates ties in 67% of comparisons; Ni et al. (2025) show 13 LLM judges underperform humans by 12--23% on code evaluation. Spring 2026 adds sharper indictments: DeLucia et al. (2026) report AUC 0.49--0.66 for LLM judges on medical chatbot completeness across three rubric types; Elganayni et al. (2026) show naive scores are optimizable targets, with lenient-judge feedback yielding higher prompt-optimization gains than strict-judge feedback; Kim et al. (2026) find judge disagreement accounts for 44% of total evaluation variance; Gupta and Kumar (2026) expose transitivity violations in 33--67% of documents despite acceptable aggregate consistency; Qi et al. (2026) organize eight rubric failure modes into a validated taxonomy. The field is openly conceding the problem this paper addresses.

RULERS (Rao and Callison-Burch, 2026) is the closest existing system: it transforms rubrics into executable specifications with deterministic evidence verification and Wasserstein calibration. The key difference is that RULERS compiles rubrics into executable specs, whereas our system structurally separates evidence collection from mathematical score computation entirely. WIMPE (Wang et al., 2026) factorizes reference answers into weighted scoring points with LLM-graded weights; our fixed impact magnitudes and formula-driven aggregation remove the LLM from both item generation and weighting. HumorRank (Bao et al., 2026) converges on the same architectural principle from a different direction: it collects discrete pairwise signals and lets Bradley-Terry MLE compute scores, never letting the LLM pick a number directly.

### 2.2 Scoring Theory and Psychometrics

The statistical foundations for reliable scoring predate LLMs. Lord and Novick (1968) formalized that standard error scales as sigma/sqrt(n) --- measurement precision improves with the square root of observations. The Spearman-Brown prediction formula (Spearman, 1910; Brown, 1910) codifies the same principle for test reliability. When we compute `net_impact / sqrt(total_items)`, we apply this established relationship.

Efron and Morris (1977) demonstrated that shrinking estimates toward the population mean produces better predictions than using raw observations alone, using James-Stein estimators in the famous baseball batting average example. Our confidence multiplier --- pulling scores toward 50 when evidence is sparse --- is inspired by this principle: with limited evidence, a conservative estimate closer to the prior is more reliable than one that trusts the raw signal fully. The multiplier is a linear heuristic rather than a full Bayesian posterior computation, but the statistical motivation is identical: regularize uncertain estimates toward a neutral prior.

The gap: these well-established psychometric principles have not been systematically applied to LLM-based evaluation. Automated essay scoring (Shermis and Burstein, 2013) applies statistical corrections to scoring but predates LLMs and does not address the specific failure modes of neural language models.

### 2.3 Multi-Agent and Multi-Modal Evaluation

Verga et al. (2024) formalize PoLL (Panel of LLM evaluators), showing diverse model panels outperform single judges. PoLL aggregates via voting; our system applies sqrt normalization and confidence regression to the evidence collected across perspectives. Debate-based approaches (Chan et al., 2024; Li et al., 2023) assume discussion improves quality; we deliberately avoid inter-agent communication to preserve independence. Yang et al. (2026) demonstrate that adversarial conflict outperforms majority vote, validating our synthesis design.

Zhang et al. (2024) find ~0.64 cross-modal consistency in multimodal LLMs, motivating our separation of modality-specific analysis into independent passes. No existing system evaluates both code and video using different model families per modality.

### 2.4 Summary

**Table 1.** Comparison of evaluation systems across methodological dimensions.

| System | Multi-model | Decomposed | Statistical corrections | Evidence-derived confidence | Multi-modal |
|--------|:-----------:|:----------:|:-----------------------:|:---------------------------:|:-----------:|
| G-Eval (2023) | | Yes | | | |
| FLASK (2024) | | Yes | | | |
| CheckEval (2024) | | Yes (binary) | | | |
| PoLL (2024) | Yes | | | | |
| RocketEval (2025) | | Yes | | | |
| RULERS (2026) | | Yes (executable) | Wasserstein | | |
| **This paper** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

No prior system combines decomposed evidence extraction, statistical corrections, evidence-derived confidence, multi-model evaluation, and multi-modal analysis. Concurrent work (RULERS, WIMPE, HumorRank, and the Spring 2026 diagnostic literature) converges on the same structural conclusion from multiple directions. The critical distinction is that the LLM never directly produces a score: evidence collection and score computation are structurally separated.

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

We instantiate the general pattern for hackathon evaluation as a 4-pass pipeline. The specific model assignments below reflect the production deployment; the architecture is model-agnostic and can substitute any capable LLM at each stage.

**Pass 1: Code Analysis.** Deep codebase traversal organized by feature, not by file. The pass generates a feature inventory, then exhaustively verifies each claimed feature through five evaluation lenses: implementation quality, test coverage, error handling, architecture decisions, and documentation. Cross-cutting concerns (security, performance, accessibility) are evaluated separately. Output: structured impact items, each with an impact score from {+5 to -5}, evidence citation (file:line), perspective label, and criterion label. Hard cap: 5 items per perspective per criterion.

**Pass 2: Video Analysis.** A native-video model provides structured observation: presenter confidence, energy, body language, whether limitations were acknowledged. A second model then interprets these observations skeptically, producing impact items with timestamp citations. Pass 2 has no access to Pass 1 output.

**Pass 3: Adversarial Synthesis.** Receives both pass outputs and performs cross-checking across four patterns: strong code + strong demo (high confidence), strong code + weak demo (presentation gap), weak code + strong demo (catching "polished theater"), weak code + weak demo (conservative evaluation). The scoring formula (Section 4) is applied here.

**Pass 4: Team Feedback.** Tier-calibrated mentoring feedback from accumulated evidence. Non-scoring.

The independence principle is amplified by using different model families for code and video analysis, which contribute different training biases and systematic errors, architecturally distinct from running the same model twice.

### 3.3 Computational Cost

The 4-pass pipeline requires approximately 25--45 minutes per submission, dominated by Pass 1's deep codebase traversal. Pass 2 runs in 5--10 minutes (video processing + skeptical interpretation). Passes 3--4 each require 2--5 minutes. Total API cost is approximately $10--25 per submission at current pricing, depending on repository size. For comparison, each human judge requires 15--30 minutes per submission; the AI system evaluates through 25 distinct perspective-criterion cells that no human judge could systematically cover.

---

## 4. Scoring Methodology

### 4.1 Multi-Perspective Impact Scoring

Each submission is evaluated through a 25-cell matrix: 5 perspectives x 5 criteria. **Perspectives** represent stakeholder viewpoints: hackathon judge, business analyst, software engineer, UX designer, and craftsperson. **Criteria** define what is measured, with weights: impact and relevance (40%), demo quality (20%), feasibility (15%), innovation (15%), user experience (10%).

Each cell contains up to 5 impact items per pass, assigned discrete scores from {+5, +3, +2, +1, -1, -2, -3, -5}. The discrete scale forces commitment --- the evaluator cannot hedge with a 3.7 and must decide between +3 (significant) and +5 (major). Every item cites specific evidence (file:line or timestamp), making evaluation auditable.

### 4.2 The Scoring Formula

**Step 1: Aggregate.** `net_impact = sum(all_item_values)`, `total_items = count(all_items)`.

**Step 2: Normalize and scale.** `normalized_impact = net_impact / sqrt(total_items)`, `raw_score = 50 + (normalized_impact * 8.0)`, clamped [0, 100]. The sqrt denominator creates diminishing returns: 4 strong items (+3 each, net=+12, normalized=6.0) outweigh 16 mediocre items (+1 each, net=+16, normalized=4.0). This mirrors how standard error scales with 1/sqrt(n) in classical test theory. The scaling constant 8.0 was selected from a range of 4.0--12.0 tested in increments of 2.0, choosing the value that maps normalized_impact +5.0 to a score of 90 (exceptional), 0.0 to 50 (average), and -5.0 to 10 (poor). Values below 8.0 compressed scores into the 30--70 range; values above 8.0 produced frequent clamping at the boundaries.

**Step 3: Confidence-based regression.** `evidence_density = total_items / 20`, `confidence_multiplier = 0.75 + (0.25 * clamp(evidence_density, 0, 1))`, `final_score = round(50 + ((raw - 50) * confidence_multiplier))`. This is inspired by Bayesian shrinkage toward a neutral prior (Efron and Morris, 1977): with sparse evidence, the score regresses toward 50; as evidence accumulates, the raw score is increasingly trusted. With zero evidence, the multiplier is 0.75: the score regresses 75% toward 50. With >= 20 items, the multiplier reaches 1.0 and the score stands. The multiplier **never exceeds 1.0** --- abundant evidence confirms but never amplifies.

The evidence density threshold of 20 items is a calibrated hyperparameter, not a theoretical derivation. It reflects the evaluation matrix structure (5 criteria x ~4 items each). The formula's behavior is continuous around this threshold --- there is no discontinuity at 20 items --- and preliminary analysis of the 342-occupation dataset suggests scores are stable within +/-1 point for thresholds between 15 and 25.

**Step 4: Self-check.** All 5 criterion scores must span >= 20 points, ensuring the evaluator discriminates across dimensions.

### 4.3 Confidence as Evidence Density

LLMs are systematically overconfident due to RLHF (Xiong et al., 2024; Wei et al., 2025a; Kadavath et al., 2022). Self-reported confidence is uncorrelated with evaluation quality. We replace it with a behavioral proxy: `confidence = clamp(total_items / 20, 0, 1)`. This metric is quality-independent --- a terrible project with abundant evidence gets high confidence and a low score --- and observable: anyone can count the items and verify the metric.

### 4.4 Worked Examples

**Strong submission, ample evidence.** net_impact = +25, total_items = 25. normalized = 25/sqrt(25) = 5.0. raw = 90. density = 1.25, multiplier = 1.0. **final = 90**, confidence = 1.0.

**Strong submission, sparse evidence.** net_impact = +25, total_items = 4. normalized = 12.5. raw = 150, clamped 100. density = 0.2, multiplier = 0.80. **final = 90**, confidence = 0.2. Sparse evidence pulls the score back and flags low confidence.

**Weak submission, ample evidence.** net_impact = -15, total_items = 25. normalized = -3.0. raw = 26. density = 1.25, multiplier = 1.0. **final = 26**, confidence = 1.0. High confidence in a low score.

### 4.5 Minimum Viable Adoption

Not all domains require the full 4-pass pipeline. The formula ablation (Table 4) suggests that Principles 1, 4, and 5 --- separation of observation from scoring, sqrt normalization, and capped confidence regression --- form the critical trio. A practitioner who makes only these three changes to a naive LLM scorer (collect structured evidence items instead of requesting a score, normalize by sqrt of item count, regress sparse evaluations toward the mean) captures the largest share of the methodology's improvement. Principles 2 and 3 (evidence density confidence, discrete scales) reinforce the core three. Principles 6 and 7 (multiple perspectives, cross-modal synthesis) add robustness in complex evaluation domains but are not prerequisites for improvement.

---

## 5. Empirical Evaluation

We evaluate the framework through three analyses: cross-domain replication on 342 occupations (Section 5.2), analytical formula ablation (Section 5.3), and human baseline reliability (Section 5.4). Table 2 summarizes headline results.

**Table 2.** Results summary across all experiments.

| Experiment | Key Metric | Value |
|------------|-----------|-------|
| Naive vs. principled (342 occupations) | Discrimination improvement (std dev ratio) | 21--58%, median 41% across 9 models |
| Naive vs. principled (342 occupations) | Rank preservation (Spearman rho) | 0.87 |
| Cross-model agreement (9 models) | Pairwise Spearman rho range | 0.77--0.93 |
| Formula ablation: without sqrt | Evidence farming score (net=+40, 50 items) | 113 (exceeds 100) |
| Formula ablation: production formula | Same profile | 95 (correctly bounded) |
| Human inter-rater reliability (Joplin) | Krippendorff's alpha | 0.16 |
| Human inter-rater reliability (St. Joseph) | Krippendorff's alpha | 0.04 |
| Human vs. naive AI (Joplin) | Spearman rho | 0.068 (p = 0.726) |
| Human vs. naive AI (Joplin) | Score inflation (AI - human mean) | +16.1 points |

### 5.1 Datasets

**Hackathon submissions.** The motivating dataset comprises 17 submissions from a St. Joseph vibeathon event, each with a source code repository and demo video, evaluated by 2--4 human judges. Additional human scores are available from a separate Joplin event (31 submissions, 5 judges). The St. Joseph judges had access to AI observation summaries during judging (contamination noted throughout); the Joplin comparison is uncontaminated. These data provide the human baseline analysis (Appendix B) and motivated the system's iterative development through five versions over three days: from a naive approach (LLM assigns scores directly) to the principled system (LLM collects evidence, formula computes scores).

**BLS occupations.** 342 occupations from the Bureau of Labor Statistics Occupational Outlook Handbook, originally scored for AI exposure by Karpathy's (2025) system using a single Gemini Flash call returning a 0--10 score. We re-scored all 342 occupations using the principled methodology across 9 models from 5 providers (Anthropic, Google, OpenAI, xAI, Zhipu). This dataset provides the primary cross-domain validation: a completely different evaluation domain --- occupational analysis rather than hackathon judging --- using the same seven principles.

### 5.2 Cross-Domain Replication: 342 Occupations

The strongest test of a scoring methodology is whether it generalizes beyond its development domain. We applied the principled framework to Karpathy's AI-exposure scoring task with no modifications to the formula or principles --- only the evaluation criteria and evidence format were adapted.

**Single-model comparison (Gemini Flash).** Naive: mean = 5.31, std = 2.26. Principled: mean = 3.84, std = 3.18. Discrimination ratio = 1.41 (41% improvement). Spearman rho = 0.87. The principled distribution is bimodal: physical jobs cluster near 0 (91 occupations scored 0; roofers, firefighters, agricultural workers) while digital jobs cluster near 10 (19 scored 10; web developers, data scientists). The naive distribution is a bell curve centered at 5.3 --- the characteristic compression of RLHF-trained scoring.

The variance difference between distributions is substantial: the principled approach produces a variance ratio of 1.98 (principled variance / naive variance). We report this descriptively rather than via F-test, as the principled distribution's bimodal structure violates the normality assumption required for formal variance-ratio testing. The convergent evidence from all 9 models (multi-model replication, below) provides stronger support for the variance difference than any single statistical test.

The bimodal structure likely reflects the genuine distribution of AI exposure across occupations --- physical labor and digital knowledge work are fundamentally different on this dimension. This interpretation is strengthened by the convergence of all 9 models from 5 independent providers: every model produces bimodal or heavy-tailed distributions despite different architectures, training data, and RLHF implementations. If the bimodal pattern were a scoring artifact, we would not expect it to emerge consistently across models with different systematic biases. The principled approach's contribution is *revealing* this structure by preventing the score compression that RLHF-trained models impose.

**Discrimination vs. accuracy.** Higher standard deviation alone does not prove better scores --- a random number generator achieves maximal discrimination. We argue the increased discrimination is meaningful for three reasons: (1) rank ordering is preserved (rho = 0.87), indicating the principled structure is consistent with naive scoring, not random; (2) the extremes are interpretable --- roofers at 0 and web developers at 10 match expert intuition about occupational AI exposure; and (3) the naive method's bell curve centered at 5.3 is a known RLHF artifact (Xiong et al., 2024), not a signal about the underlying distribution. Without ground-truth labels for "correct" AI-exposure scores, we cannot prove accuracy in the absolute sense --- only that the principled approach produces more interpretable discrimination while preserving the ordinal structure that the naive method captures.

**Why discrimination matters beyond rescaling.** A skeptic could note that rho = 0.87 means the principled method mostly agrees with the naive approach on ordering, and argue that the formula merely rescales existing signal. Two considerations answer this. First, 13% of pairwise rankings change --- and these are precisely the cases where keyword-level reasoning fails (see rank disagreement table below). Second, the naive approach provides no mechanism for confidence calibration: a score based on 3 evidence items and one based on 30 carry equal weight. The principled formula's confidence regression addresses this directly, producing conservative scores when evidence is sparse and full-confidence scores only when the evidence base is substantial. In high-stakes evaluation contexts --- hiring, funding, compliance --- the difference between "probably right" and "calibrated with known confidence" is the difference between a toy and a tool.

**Rank disagreements tell a compelling story.** While overall rank correlation is high (rho = 0.87), the cases where naive and principled scoring diverge most are interpretable:

| Occupation | Naive Score | Principled Score | Interpretation |
|-----------|:-----------:|:----------------:|----------------|
| Producers and Directors | 7 | 1.0 | Creative/interpersonal core despite digital tools |
| Kindergarten Teachers | 6 | 0.1 | Physical, interpersonal; AI exposure minimal |
| High School Teachers | 7 | 1.23 | Physical classroom; digital component limited |
| Craft Artists | 6 | 0.53 | Physical medium; AI assists design, not creation |
| Actors | 7 | 1.8 | Physical performance; digital post-production only |

The naive scorer assigns moderate-high scores based on surface-level keyword association (teachers use computers; directors use software). The principled approach, forced to enumerate specific evidence items for and against AI exposure, recognizes that the core work of these occupations is physical or interpersonal. The 13% of rankings that change are precisely the cases where keyword-level reasoning fails and evidence-level reasoning succeeds.

**Multi-model replication (9 models, 5 providers).** We ran identical evidence-gathering prompts through 9 models spanning a range of capability levels. Discrimination improvement over the naive baseline ranged from 21% (GLM-5, std 2.73 vs. 2.26) to 58% (Sonnet 4.5, std 3.56 vs. 2.26), with a median of 41% across all 9 models. Even the weakest-performing model still achieves meaningful improvement over naive scoring.

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

Four findings:

1. **Every model beats naive scoring on discrimination.** All 9 principled runs produce higher std dev (2.73--3.56) than the naive baseline (2.26). The methodology improves score spread regardless of model, with improvements ranging from 21% to 58%.

2. **Strong rank agreement across models.** Spearman rho ranges 0.77--0.93 across all 36 model pairs. The ordering is stable even when exact scores differ.

3. **No capability-discrimination correlation.** Model capability shows no systematic relationship with mean score or discrimination. The methodology normalizes across capability levels.

4. **Provider biases become visible.** OpenAI models are more optimistic (means 4.3--6.2) than Anthropic (3.97--4.64), Google (3.84--4.75), and xAI/Zhipu (3.03--3.45). The principled methodology surfaces these biases rather than hiding them inside opaque scores.

**Prompt confound.** The improvement observed here confounds two changes: (a) a richer evidence-gathering prompt that asks for 10--20 discrete impact items with severity ratings, and (b) the mathematical formula applied to the collected evidence. Disentangling these contributions requires a "structured prompt, no formula" control --- using the evidence-gathering prompt but computing scores as a simple mean of impact items --- that isolates the formula's contribution from the prompt's contribution. This control requires no additional API calls, only recomputation from existing evidence data, and is the first priority in future work (Section 7).

### 5.3 Formula Ablation

The cross-domain replication demonstrates that the full pipeline works. To understand *why* it works, we need to isolate each mathematical component's contribution. We compute scores under eight formula variants applied to four constructed evidence profiles --- profiles designed to exercise the formula's edge cases (strong/weak evidence crossed with ample/sparse items) rather than drawn from specific submissions. This analytical approach has the advantage of requiring zero additional pipeline runs: all variants operate on the same impact items. Running the 8 variants on the actual 342-occupation evidence data is a natural next step (Section 7) that would transform this analytical illustration into full empirical validation.

**Table 4.** Formula ablation: final scores under each variant for four evidence profiles. **Bold** cells indicate pathological behavior (scores exceeding 100 or maximally confident sparse evaluations).

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

**Variant A (old linear) demonstrates the inflation bug.** Without sqrt normalization, net_impact scales linearly with item count. The evidence-farming profile produces a score of 113 --- exceeding the scale maximum. This was the actual production bug discovered and fixed during iterative development.

**Variant B (production) is correctly bounded.** sqrt normalization reduces the farming profile to normalized_impact = 5.66, and the capped multiplier preserves the score at 95. No profile exceeds 100.

**Variant C (linear normalization) over-penalizes volume.** Linear division suppresses the strong+ample profile to 58 --- a clearly strong submission should score well above average. Linear normalization treats the 20th item as adding the same noise as the 4th, violating the diminishing-returns principle.

**Variant E (no confidence) fails on sparse evidence.** Without regression, the sparse profile (4 items) scores 100 --- the system is maximally confident about an evaluation based on minimal evidence. This is exactly the failure mode Principle 5 addresses.

**Variant F (amplifying confidence) reintroduces the inflation bug.** Even with sqrt normalization, allowing the multiplier to exceed 1.0 pushes the farming profile to 107. The two corrections --- sqrt normalization and capped regression --- are individually necessary and jointly sufficient.

### 5.4 Human Baseline Analysis

Human inter-rater reliability contextualizes the floor that principled automation must exceed. We analyze scoring data from two hackathon events (detailed statistics in Appendix B).

**Inter-rater reliability.** Joplin (5 judges, 31 submissions): Krippendorff's alpha = 0.16 (ordinal), ICC(2,1) = 0.0, mean pairwise weighted kappa = 0.16 (range 0.007--0.34). St. Joseph (4 judges, 17 submissions): alpha = 0.04, ICC(2,1) = 0.0, mean pairwise kappa = 0.01 (range -0.30 to 0.43). Both fall far below the 0.667 acceptability threshold (Krippendorff, 2004). For context, academic peer review achieves ICC ~0.2--0.3 (Bornmann et al., 2010).

**Score inflation and judge leniency.** Both events show scores significantly above the scale midpoint (p < 0.05 for all criteria). Kruskal-Wallis tests confirm significant leniency differences (Joplin: H = 39.9, p < 0.001; St. Joseph: H = 15.3, p = 0.002). Random intercepts range from +12.9 to -15.2 in Joplin --- a 28-point spread in baseline generosity across judges evaluating the same submissions. This is noise in the Kahneman et al. (2021) sense: unwanted variability reflecting nothing about submission quality.

**Human vs. naive AI (Joplin, uncontaminated).** Spearman rho = 0.068 (p = 0.726). AI mean = 74.65 vs. human mean = 58.54. Low human-AI correlation is expected when human inter-rater reliability is itself poor --- humans do not reliably agree with each other (alpha = 0.16), so disagreement with the AI is unsurprising.

**Methodological caveats.** These human reliability estimates should be interpreted with appropriate caution. The panel sizes are small (4--5 judges), the number of submissions per judge is unbalanced (1--4 judges per submission at St. Joseph), the author served as one judge (potential conflict of interest), and the Joplin event used a social judging format where judges could observe each other's reactions (potential conformity pressure). These fragilities mean the specific alpha values (0.04, 0.16) are better understood as order-of-magnitude evidence that human hackathon judging is unreliable than as precise estimates. The broader finding --- that human inter-rater agreement falls far below accepted thresholds --- is robust to these methodological concerns, as it is consistent with published peer review reliability data (Bornmann et al., 2010).

---

## 6. Discussion

### 6.1 Design Decisions

**Discrete impact scores vs. continuous scales.** The set {+5, +3, +2, +1, -1, -2, -3, -5} forces magnitude commitment. A continuous scale allows hedging with +2.3, producing the same middle-clustering that plagues direct score assignment. The gaps in the scale (no +4, no -4) are deliberate: they force categorization rather than interpolation.

**sqrt normalization vs. alternatives.** Linear normalization (net/items) penalizes volume too aggressively --- it treats the 20th item as adding the same noise as the 4th (Table 4, variant C). Log normalization provides weaker diminishing returns, producing clamping at extremes (variant D). sqrt is the natural choice from classical test theory and the Pareto-optimal trade-off in our ablation.

**Downward-only regression.** Capping the multiplier at 1.0 rather than allowing 1.25 prevents the inflation failure mode demonstrated in variants A and F. This asymmetry is justified: sparse evidence should produce conservative scores, but abundant evidence should never amplify beyond what the evidence supports.

### 6.2 Limitations

**Head-to-head experiment incomplete.** The comparison of naive vs. principled scoring on the same 17 hackathon submissions --- the most direct within-domain validation --- remains to be executed. Current empirical evidence comes from the cross-domain replication (342 occupations) and human baseline analysis. This experiment is computationally inexpensive (re-running the naive pipeline on 17 submissions) and is prioritized as the first item in future work.

**Prompt confound not disentangled.** The observed improvement in the Karpathy replication confounds richer evidence-gathering prompts with the mathematical formula. A "structured prompt, simple aggregation" control would isolate each contribution. This control requires no additional API calls --- only recomputation from existing evidence data --- and is the second priority in future work.

**Principles 6 and 7 not individually ablated.** The formula ablation (Section 5.3) isolates Principles 1, 3, 4, and 5. Principles 6 (multiple perspectives) and 7 (cross-modal synthesis) are architectural properties of the pipeline that require pipeline-level ablation (e.g., 1 perspective vs. 5, single-pass vs. multi-pass). These are presented as design principles supported by theoretical argument (Verga et al., 2024; Yang et al., 2026) and prior work on multi-agent evaluation, but they have not been individually validated in our framework.

**Single-evaluator reliability.** Each submission receives one evaluation per system version. Inter-run agreement --- how much the same version varies on repeated runs --- has not been measured. Given that LLM outputs are stochastic, demonstrating test-retest consistency is necessary to fully support the reliability claims.

**No confidence intervals on key statistics.** The headline metrics (rho = 0.87, discrimination ratio range 1.21--1.58, cross-model rho 0.77--0.93) are reported without bootstrap confidence intervals. Bootstrap CIs require only resampling of existing data and are computationally trivial.

**Small primary dataset.** 17 hackathon submissions provide limited statistical power. The Karpathy replication (342 occupations) partially compensates.

**No ground truth.** "Correct" hackathon scores are inherently subjective. All comparisons are relative.

**Human score contamination.** St. Joseph judges had AI observation summaries visible, creating anchoring effects. The Joplin comparison is uncontaminated but uses the naive AI baseline.

**Author-as-judge.** Kevin Kirchner served as both paper author and human judge (all 17 St. Joseph submissions, 1 Joplin submission), creating potential conflict of interest in the human comparison data.

**Additive scoring limitation.** The formula allows positive items to offset critical negatives. In domains where a single finding is dispositive (e.g., a critical security vulnerability), a pass-fail circuit-breaker is needed alongside the scoring formula.

**Emotional judgment gaps.** Human judges assess dimensions --- presenter presence, emotional resonance, authenticity, team dynamics --- that AI systems address only partially. Of 26 emotional judgment dimensions catalogued in Appendix A, approximately 3 receive partial coverage through the video analysis pipeline. This remains an honest limitation rather than a solved problem, and is primarily relevant to hackathon and presentation-style evaluation domains.

### 6.3 Generalizability

The seven principles address failure modes --- inflation, undifferentiated confidence, single-perspective bias --- that are not specific to hackathon judging. The five validated principles transfer to new domains through mechanical adaptation; the two design principles (6 and 7) degrade gracefully in single-modality or single-perspective settings.

Adapting the framework involves four steps: define a perspective-criterion matrix, specify the evidence format, calibrate three parameters (evidence density denominator, scaling constant, regression strength) on 5--10 representative artifacts, and design the independence architecture.

The Karpathy replication empirically validates cross-domain transfer: the same methodology applied to occupational analysis produces the same pattern of improved discrimination with preserved rank ordering, across 9 models and 5 providers.

---

## 7. Conclusion

The default approach to LLM-based evaluation --- asking the model to assign a score --- inherits and amplifies the noise Kahneman et al. (2021) documented in human judgment. Seven principles, grounded in classical psychometric theory, address four structural failure modes: score inflation, undifferentiated confidence, single-perspective bias, and cross-modal blindness.

The mathematical core is a scoring formula where LLMs collect structured evidence and statistical corrections compute calibrated scores. Formula ablation confirms that sqrt normalization and capped confidence regression are individually necessary and jointly sufficient: removing either reintroduces pathological failure modes. Cross-domain validation on 342 occupations across 9 models and 5 providers demonstrates that the methodology generalizes: discrimination improvement ranges from 21% to 58% (median 41%), with every model producing improved separation while maintaining strong cross-model rank agreement (rho = 0.77--0.93).

The practical contribution is both methodological and cautionary. The methodology provides a concrete, deployable alternative to naive LLM scoring --- and practitioners can adopt its core benefits through three changes alone (Principle 1: separate evidence from scoring; Principle 4: normalize by sqrt of item count; Principle 5: regress sparse evaluations toward the mean). The caution: human evaluation is itself unreliable (alpha = 0.04--0.16 in our data), and the goal of automated evaluation should not be matching human scores but exceeding human consistency.

**Future work.** We organize remaining work into two tiers. *Recomputation from existing data* (no new API calls): (1) Disentangle evidence elicitation from mathematical correction via a prompt-only control that computes scores as a simple mean of existing evidence items. (2) Run formula ablation (8 variants) on the real 342-occupation evidence to supplement the analytical profiles. (3) Compute bootstrap 95% confidence intervals on headline statistics. (4) Conduct sensitivity analysis on the evidence density threshold. *Experiments requiring new data*: (5) Complete the within-domain head-to-head comparison on 17 hackathon submissions. (6) Measure inter-run reliability (3--5 repeated runs on a sample of occupations). (7) Ablate Principles 6 and 7 at the pipeline level. (8) Adapt to additional domains (customer service QA, code review, legal evaluation). (9) Design a pass-fail circuit-breaker for compliance-critical domains.

The field's current trajectory --- asking ever-more-capable models to assign scores, then calibrating after the fact --- treats the symptom rather than the disease. Reliability emerges not from model capability but from methodological structure: separating observation from scoring, grounding confidence in evidence, and applying the statistical corrections that psychometricians have understood for decades. The path forward requires the discipline to never let the LLM pick a number.

---

*Full reference list, appendices on emotional judgment dimensions, and per-criterion human reliability tables are kept with the working paper drafts in PROJ-ai-judge-scoring. This file mirrors the v0.7 draft as of April 2026.*
