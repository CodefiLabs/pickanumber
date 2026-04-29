// The seven principles. Single source of truth — page renders from this,
// skills reference this. Keep numbers and titles aligned with the paper.

export const PRINCIPLES = [
	{
		n: 1,
		title: 'Separate observation from scoring',
		body: 'The LLM finds evidence. A formula, not the LLM, produces the score. The number is computed, not chosen.'
	},
	{
		n: 2,
		title: 'Discrete signed impact items',
		body: 'Every piece of evidence gets one of {+5, +3, +2, +1, −1, −2, −3, −5}. Forces commitment. Removes the 7-out-of-10 anchor.'
	},
	{
		n: 3,
		title: 'Diminishing returns (sqrt)',
		body: 'normalized = net_impact / sqrt(total_items). The 40th item adds less than the 4th. Evidence farming is punished.'
	},
	{
		n: 4,
		title: 'Density-weighted confidence',
		body: 'Confidence = how much evidence the scorer found, not how sure the scorer feels. Sparse runs are visibly low-confidence.'
	},
	{
		n: 5,
		title: 'Anchored center',
		body: 'Sparse-evidence runs regress toward 50. The multiplier never exceeds 1.0 — high evidence confirms, never amplifies beyond raw.'
	},
	{
		n: 6,
		title: 'Bounded scale with self-check',
		body: 'Final scores live in [0, 100]. Across criteria, the spread must be ≥ 20 — otherwise the evaluator was not discriminating.'
	},
	{
		n: 7,
		title: 'Separation of LLM and deterministic computation',
		body: 'Independent passes by different model families collect evidence. Math, not the LLM, combines them. Adversarial synthesis catches contradictions.'
	}
];
