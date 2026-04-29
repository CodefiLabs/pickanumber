// The canonical scoring formula. Single source of truth.
// The page renders from this; the skills reference this; the tests assert this.
//
// Origin: PROJ-ai-judge-scoring/data/SCORING-FORMULA.md
// Paper:  Don't Let the LLM Pick a Number (CodefiLabs/pickanumber)

/** The fixed discrete impact set every evidence item must use. */
export const IMPACT_SET = [+5, +3, +2, +1, -1, -2, -3, -5];

/** The defaults the production system was calibrated against. */
export const DEFAULTS = {
	scaleFactor: 8.0,        // raw_score = 50 + normalized * scaleFactor
	densityDenom: 20,        // density = total_items / densityDenom
	multiplierMin: 0.75,     // sparse evidence pulls toward 50
	multiplierGain: 0.25,    // density 1.0 → multiplier 1.00 (never amplifies)
	itemCapPerCell: 5,       // max items per perspective × criterion × pass
	itemMinPerCell: 3,       // target floor per perspective × criterion × pass
	selfCheckSpan: 20        // max(final) − min(final) across criteria must be ≥ 20
};

/**
 * Score a flat pool of evidence items against the canonical formula.
 *
 * @param {Array<{impact:number}>} items
 * @param {object} [opts] override DEFAULTS keys
 * @returns {{
 *   net_impact: number, total_items: number,
 *   normalized_impact: number, raw_score: number,
 *   evidence_density: number, confidence_multiplier: number,
 *   final_score: number, confidence: number
 * }}
 */
export function score(items, opts = {}) {
	const o = { ...DEFAULTS, ...opts };
	const total_items = items.length;
	const net_impact = items.reduce((s, it) => s + (it.impact ?? 0), 0);

	const normalized_impact = total_items === 0 ? 0 : net_impact / Math.sqrt(total_items);
	const raw_unclamped = 50 + normalized_impact * o.scaleFactor;
	const raw_score = Math.max(0, Math.min(100, raw_unclamped));

	const evidence_density = total_items / o.densityDenom;
	const dClamped = Math.max(0, Math.min(1, evidence_density));
	const confidence_multiplier = o.multiplierMin + o.multiplierGain * dClamped;

	const final_score = Math.round(50 + (raw_score - 50) * confidence_multiplier);
	const confidence = dClamped;

	return {
		net_impact,
		total_items,
		normalized_impact,
		raw_score,
		evidence_density,
		confidence_multiplier,
		final_score,
		confidence
	};
}

/**
 * Score a 5×5 matrix benchmark — formula runs once per criterion, then a
 * weighted average produces the overall score. Includes the self-check.
 *
 * @param {{
 *   criteria: Array<{ key: string, weight: number, items: Array<{impact:number}> }>
 * }} input
 */
export function scoreMatrix(input) {
	const per = input.criteria.map((c) => ({
		key: c.key,
		weight: c.weight,
		...score(c.items)
	}));

	const totalWeight = per.reduce((s, p) => s + p.weight, 0);
	const overall_score = Math.round(
		per.reduce((s, p) => s + p.final_score * p.weight, 0) / (totalWeight || 1)
	);
	const overall_confidence = per.reduce((m, p) => Math.min(m, p.confidence), 1);

	const finals = per.map((p) => p.final_score);
	const span = Math.max(...finals) - Math.min(...finals);
	const self_check_passed = span >= DEFAULTS.selfCheckSpan;

	return { per_criterion: per, overall_score, overall_confidence, self_check_span: span, self_check_passed };
}

/** The pseudocode block the page renders verbatim. Source = this comment. */
export const PER_CRITERION_PSEUDO = `# Per criterion
net_impact         = sum(item.impact for item in items)
total_items        = len(items)
normalized         = net_impact / sqrt(total_items)
raw                = clamp(50 + normalized * 8.0, 0, 100)
density            = total_items / 20
multiplier         = 0.75 + 0.25 * clamp(density, 0, 1)   # never > 1.0
final              = round(50 + (raw - 50) * multiplier)
confidence         = clamp(density, 0, 1)`;

export const ACROSS_CRITERIA_PSEUDO = `# Across criteria (overall)
overall_score       = round(sum(c.final * c.weight))
overall_confidence  = min(c.confidence for c in criteria)
self_check_span     = max(c.final) - min(c.final)
                      # must be >= 20`;
