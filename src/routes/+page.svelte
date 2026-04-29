<script>
	import { PRINCIPLES } from '$lib/principles.js';
	import { PER_CRITERION_PSEUDO, ACROSS_CRITERIA_PSEUDO } from '$lib/formula.js';

	/** @type {Record<string, 'idle' | 'copied' | 'error'>} */
	let copyState = $state({});

	const DEFAULT_INSTALL = 'npx skills add CodefiLabs/pickanumber/what-works-feedback-judge';

	const skills = [
		{
			id: 'evidence-scoring',
			name: 'evidence-scoring',
			tagline: 'The seven-principle methodology, generic.',
			body: "Bring your own domain. Define your matrix. The skill walks you through cataloging signed evidence items and runs the formula. The methodology, nothing prescribed about WHAT you score.",
			install: 'npx skills add CodefiLabs/pickanumber/evidence-scoring'
		},
		{
			id: 'what-works-feedback-judge',
			name: 'what-works-feedback-judge',
			tagline: 'A 4-question feedback loop. Score any draft.',
			body: "Pre-baked Working / Not working / Missing / Confusing application. Hand it any draft, spec, plan, or pitch and get a 0–100 readiness score plus four grouped action lists. Iterate; v1 → v2 score delta tells you whether the revision actually moved.",
			install: 'npx skills add CodefiLabs/pickanumber/what-works-feedback-judge'
		},
		{
			id: 'hackathon-judge',
			name: 'hackathon-judge',
			tagline: 'Four-pass project judging — code, demo, math, mentoring.',
			body: "Score any project submission with a codebase (and optional demo video) against a 5×5 evidence matrix. Independent passes prevent polish from masking thin code and vice versa. Math computes the scores; the team gets a grounded mentoring report.",
			install: 'npx skills add CodefiLabs/pickanumber/hackathon-judge'
		}
	];

	const calibration = [
		{ normalized: '+5.0', score: '~90', tier: 'Exceptional (5–10% of submissions)' },
		{ normalized: '+2.5', score: '~70', tier: 'Above average' },
		{ normalized: '0.0', score: '~50', tier: 'Average' },
		{ normalized: '−2.5', score: '~30', tier: 'Below average' },
		{ normalized: '−5.0', score: '~10', tier: 'Poor' }
	];

	const workedExamples = [
		{
			id: 'A',
			title: 'Strong, abundant evidence',
			given: 'net_impact = +25, total_items = 25',
			steps: [
				'normalized = 25 / sqrt(25) = 5.0',
				'raw = 50 + (5.0 × 8.0) = 90',
				'density = 25/20 = 1.25 → multiplier = 1.0',
				'final = 90, confidence = 1.0'
			]
		},
		{
			id: 'B',
			title: 'Strong, sparse evidence',
			given: 'net_impact = +25, total_items = 4',
			steps: [
				'normalized = 25 / sqrt(4) = 12.5',
				'raw = 50 + (12.5 × 8.0) = 150 → clamped 100',
				'density = 4/20 = 0.2 → multiplier = 0.80',
				'final = round(50 + 50 × 0.80) = 90, confidence = 0.2'
			]
		},
		{
			id: 'C',
			title: 'Average',
			given: 'net_impact = 0, total_items = 20',
			steps: [
				'normalized = 0',
				'raw = 50',
				'density = 1.0 → multiplier = 1.0',
				'final = 50, confidence = 1.0'
			]
		},
		{
			id: 'D',
			title: 'Weak, well-evidenced',
			given: 'net_impact = −15, total_items = 25',
			steps: [
				'normalized = −15 / sqrt(25) = −3.0',
				'raw = 50 + (−3.0 × 8.0) = 26',
				'density = 1.25 → multiplier = 1.0',
				'final = 26, confidence = 1.0  (high confidence in a low score)'
			]
		}
	];

	/** @param {string} key @param {string} text */
	async function copy(key, text) {
		try {
			await navigator.clipboard.writeText(text);
			copyState[key] = 'copied';
			setTimeout(() => (copyState[key] = 'idle'), 2000);
		} catch (e) {
			copyState[key] = 'error';
			setTimeout(() => (copyState[key] = 'idle'), 2000);
		}
	}
</script>

<svelte:head>
	<title>Don't Let the LLM Pick a Number — pickanumber</title>
	<meta
		name="description"
		content="A methodology paper, three installable skills, and worked rescoring case studies. The LLM finds evidence; math computes the score."
	/>
	<link rel="canonical" href="https://pickanumber.codefi.io/" />
	<meta name="theme-color" content="#fcfaf6" media="(prefers-color-scheme: light)" />
	<meta name="theme-color" content="#1f1a14" media="(prefers-color-scheme: dark)" />

	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://pickanumber.codefi.io/" />
	<meta property="og:title" content="Don't Let the LLM Pick a Number" />
	<meta
		property="og:description"
		content="The LLM finds evidence. Math computes the score. A methodology paper, three installable skills, and worked rescoring case studies."
	/>
	<meta property="og:image" content="https://pickanumber.codefi.io/og.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="Don't Let the LLM Pick a Number" />
	<meta
		name="twitter:description"
		content="The LLM finds evidence. Math computes the score."
	/>
	<meta name="twitter:image" content="https://pickanumber.codefi.io/og.png" />
</svelte:head>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ HERO                                                          │
     ╰──────────────────────────────────────────────────────────────╯ -->
<header class="border-b border-rule">
	<div class="container-prose pt-12 pb-20 lg:pt-20 lg:pb-28">
		<div class="flex flex-wrap items-center justify-between gap-y-3">
			<div class="flex items-center gap-3">
				<div
					class="flex h-9 w-9 items-center justify-center rounded-md border-[1.5px] border-ink-strong text-base font-bold text-ink-strong"
				>
					P
				</div>
				<span class="font-mono text-sm font-semibold text-ink">pickanumber</span>
				<span class="tag">v0.7 · draft</span>
			</div>
			<nav class="flex items-center gap-4 text-sm sm:gap-6">
				<a class="hidden text-ink-soft transition hover:text-ink md:inline" href="#problem"
					>Problem</a
				>
				<a class="hidden text-ink-soft transition hover:text-ink sm:inline" href="#principles"
					>Principles</a
				>
				<a class="hidden text-ink-soft transition hover:text-ink md:inline" href="#formula"
					>Formula</a
				>
				<a class="hidden text-ink-soft transition hover:text-ink lg:inline" href="#examples"
					>Examples</a
				>
				<a class="text-ink-soft transition hover:text-ink" href="#install">Install</a>
				<a
					class="text-ink-soft transition hover:text-ink"
					href="https://github.com/CodefiLabs/pickanumber"
					target="_blank"
					rel="noopener">GitHub</a
				>
			</nav>
		</div>

		<div class="mt-16 max-w-3xl lg:mt-24">
			<!-- Receipts strip — the calibration numbers are the trust anchor -->
			<div class="flex flex-wrap items-baseline gap-x-5 gap-y-1 text-sm text-ink-soft">
				<span><span class="tabular font-mono text-base font-semibold text-ink-strong">18</span> hackathons</span>
				<span class="text-ink-faint" aria-hidden="true">·</span>
				<span><span class="tabular font-mono text-base font-semibold text-ink-strong">342</span> BLS occupations</span>
				<span class="text-ink-faint" aria-hidden="true">·</span>
				<span><span class="tabular font-mono text-base font-semibold text-ink-strong">9</span> frontier models</span>
			</div>

			<h1 class="mt-6 text-display font-bold text-ink-strong">
				Don't let the LLM<br class="hidden sm:inline" />
				<span class="text-mark">pick a number.</span>
			</h1>
			<p class="mt-6 text-lg leading-relaxed text-ink-soft lg:text-xl">
				Ask an LLM to score something on a 0–10 scale and you'll get a 7. Ask again, you'll get a 7.
				Vary the input and you'll still get a 7. The model isn't grading — it's anchoring. This is a
				methodology and a working set of tools that fix the problem the same way every time:
				<strong class="font-semibold text-ink-strong">the LLM finds evidence; math computes the score.</strong>
			</p>

			<!-- Hero install — the conversion lives above the fold -->
			<div class="mt-10">
				<p class="font-mono text-xs uppercase tracking-wider text-ink-faint">Install the default skill</p>
				<button
					onclick={() => copy('hero', DEFAULT_INSTALL)}
					title={DEFAULT_INSTALL}
					class="group mt-3 flex w-full items-center justify-between gap-3 rounded-md border border-ink-strong bg-ink-strong px-4 py-3.5 font-mono text-xs text-paper transition hover:bg-ink sm:text-sm"
				>
					<span class="min-w-0 flex-1 truncate text-left">
						<span class="text-mark">$</span> {DEFAULT_INSTALL}
					</span>
					{#if copyState.hero === 'copied'}
						<span class="shrink-0 font-semibold text-paper">✓ copied</span>
					{:else if copyState.hero === 'error'}
						<span class="shrink-0 font-semibold text-paper">select manually</span>
					{:else}
						<svg
							width="14"
							height="14"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							class="shrink-0 text-paper-sunk transition group-hover:text-paper"
							aria-hidden="true"
							><rect x="9" y="9" width="13" height="13" rx="2" /><path
								d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"
							/></svg
						>
					{/if}
				</button>
				<div class="mt-4 flex flex-wrap items-baseline gap-x-6 gap-y-2 text-sm">
					<a
						href="#install"
						class="text-ink-soft underline underline-offset-[6px] decoration-ink-faint hover:decoration-ink-strong hover:text-ink-strong"
						>Or pick a different skill ↓</a
					>
					<a
						href="#problem"
						class="text-ink-faint underline underline-offset-[6px] decoration-ink-faint/60 hover:decoration-ink-soft hover:text-ink-soft"
						>see the problem first ↓</a
					>
				</div>
			</div>
		</div>
	</div>
</header>

<main>
<!-- ╭──────────────────────────────────────────────────────────────╮
     │ PROBLEM                                                       │
     ╰──────────────────────────────────────────────────────────────╯ -->
<section id="problem" class="border-b border-rule py-16 lg:py-20">
	<div class="container-prose">
		<div class="grid gap-x-10 gap-y-12 lg:grid-cols-3">
			<div>
				<h2 class="text-2xl font-semibold leading-[1.15] text-ink-strong">
					LLMs anchor to 7-out-of-10.
				</h2>
				<p class="mt-4 text-ink-soft">
					Across 18 hackathon submissions and 342 BLS occupations, models picked numbers in a tight
					band centered on 7. Variance was high run-to-run, but the central tendency stayed
					locked. Calibration was decoration, not signal.
				</p>
			</div>
			<div>
				<h2 class="text-2xl font-semibold leading-[1.15] text-ink-strong">
					Asking nicely doesn't help.
				</h2>
				<p class="mt-4 text-ink-soft">
					"Be honest." "Use the full scale." "A 4 means genuinely excellent." We tried all of it.
					Public benchmarks like
					<a class="underline underline-offset-4 decoration-ink-faint hover:decoration-ink-strong" href="https://github.com/lechmazur/writing" target="_blank" rel="noopener">lechmazur/writing</a> retired their absolute rubric scoring after 9,139 score rows showed it. The pattern is the model, not the prompt.
				</p>
			</div>
			<div>
				<h2 class="text-2xl font-semibold leading-[1.15] text-ink-strong">
					Don't ask for a number. Ask for evidence.
				</h2>
				<p class="mt-4 text-ink-soft">
					LLMs <em>are</em> reliable at one thing: finding bounded, signed observations with file:line or
					timestamp evidence. Collect those. Run them through a formula. The number you get out is
					stable across reruns, calibrated, and defensible.
				</p>
			</div>
		</div>
	</div>
</section>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ PRINCIPLES                                                    │
     ╰──────────────────────────────────────────────────────────────╯ -->
<section id="principles" class="border-b border-rule py-24 lg:py-32">
	<div class="container-prose">
		<h2 class="text-section font-semibold text-ink-strong">Seven principles.</h2>
		<p class="mt-4 max-w-3xl text-ink-soft">
			Each one rules out a way the LLM-pick-a-number failure mode sneaks back in. Together they
			define a scoring pipeline you can defend against an adversary who's read the prompt.
		</p>

		<ol class="mt-14 grid gap-x-12 gap-y-2 sm:grid-cols-2">
			{#each PRINCIPLES as p}
				<li class="grid grid-cols-[2.5rem_1fr] items-baseline gap-x-3 border-t border-rule py-5">
					<span class="font-mono text-sm font-semibold text-ink-faint">0{p.n}</span>
					<div>
						<h3 class="text-base font-semibold leading-snug text-ink-strong">{p.title}</h3>
						<p class="mt-2 text-sm leading-relaxed text-ink-soft">{p.body}</p>
					</div>
				</li>
			{/each}
		</ol>
	</div>
</section>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ FORMULA                                                       │
     ╰──────────────────────────────────────────────────────────────╯ -->
<section id="formula" class="border-b border-rule py-24 lg:py-32">
	<div class="container-prose">
		<h2 class="text-section font-semibold text-ink-strong">
			Discrete impact → diminishing returns → confidence-weighted.
		</h2>
		<p class="mt-4 max-w-3xl text-ink-soft">
			Two application patterns. Use the <strong class="font-semibold text-ink-strong">pooled</strong>
			variant for simple checkers (one bucket of evidence, one final score). Use the <strong class="font-semibold text-ink-strong">per-criterion</strong>
			variant for matrix benchmarks (formula runs once per criterion; weighted average produces the
			overall).
		</p>

		<div class="mt-10 grid gap-4 lg:grid-cols-2">
			<pre
				class="overflow-x-auto rounded-md bg-ink-strong p-5 font-mono text-xs leading-relaxed text-paper"><code
					>{PER_CRITERION_PSEUDO}</code
				></pre>

			<pre
				class="overflow-x-auto rounded-md bg-ink-strong p-5 font-mono text-xs leading-relaxed text-paper"><code
					>{ACROSS_CRITERIA_PSEUDO}</code
				></pre>
		</div>

		<p class="mt-6 max-w-3xl text-sm text-ink-faint">
			Discrete impact set: <span class="font-mono text-ink">{`{+5, +3, +2, +1, −1, −2, −3, −5}`}</span>. Hard
			cap of 5 items per perspective per criterion per pass. The multiplier never exceeds 1.0
			(confirms, never amplifies). Sparse evidence is <em>visibly</em> low-confidence, not silently confident.
		</p>

		<!-- Calibration table -->
		<div class="mt-12">
			<h3 class="text-2xl font-semibold leading-[1.15] text-ink-strong">Calibration anchors.</h3>
			<p class="mt-3 max-w-3xl text-ink-soft">
				The 8.0 scale factor was tuned to put scores at familiar landmarks. The numbers below are
				not opinions — they fall out of the formula given each <span class="font-mono">normalized_impact</span>.
			</p>

			<div class="mt-6 overflow-x-auto rounded-lg border border-rule">
				<table class="w-full border-collapse text-left text-sm">
					<thead class="bg-paper-sunk">
						<tr>
							<th class="border-b border-r border-rule px-4 py-3 font-mono text-ink-faint">normalized_impact</th>
							<th class="border-b border-r border-rule px-4 py-3 font-mono text-ink-faint">→ raw_score</th>
							<th class="border-b border-rule px-4 py-3 text-ink-faint">tier</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-rule bg-paper">
						{#each calibration as row}
							<tr>
								<td class="border-r border-rule px-4 py-3 font-mono text-ink">{row.normalized}</td>
								<td class="border-r border-rule px-4 py-3 font-mono text-ink-strong">{row.score}</td>
								<td class="px-4 py-3 text-ink-soft">{row.tier}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</section>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ WORKED EXAMPLES                                               │
     ╰──────────────────────────────────────────────────────────────╯ -->
<section id="examples" class="border-b border-rule py-24 lg:py-32">
	<div class="container-prose">
		<h2 class="text-section font-semibold text-ink-strong">Run the math by hand.</h2>
		<p class="mt-4 max-w-3xl text-ink-soft">
			Four small examples + one real-world rescoring. The toy cases show how the pieces interact;
			the rescoring shows what changes when an existing benchmark drops the LLM-picks-a-number
			step.
		</p>

		<!-- Worked examples — numbered ledger, one ruled row each. -->
		<ol class="mt-12 grid gap-x-12 gap-y-2 lg:grid-cols-2">
			{#each workedExamples as ex}
				<li class="grid grid-cols-[2rem_1fr] items-baseline gap-x-4 border-t border-rule py-5">
					<span class="font-mono text-sm font-semibold text-ink-faint">{ex.id}</span>
					<div>
						<h3 class="text-base font-semibold leading-snug text-ink-strong">{ex.title}</h3>
						<p class="mt-2 font-mono text-xs text-ink-soft">given · {ex.given}</p>
						<ul class="mt-2 space-y-0.5 font-mono text-xs leading-relaxed text-ink">
							{#each ex.steps as s}
								<li>· {s}</li>
							{/each}
						</ul>
					</div>
				</li>
			{/each}
		</ol>

		<!-- Rescoring case study — ruled annotation, not a card stack. -->
		<div class="mt-20 border-t-2 border-ink-strong pt-8">
			<div class="flex flex-wrap items-baseline justify-between gap-4">
				<h3 class="text-2xl font-semibold leading-[1.15] text-ink-strong">
					Rescoring case study: <span class="font-mono">pbakaus/impeccable</span>
				</h3>
				<a
					class="text-sm text-ink-soft underline underline-offset-4 decoration-ink-faint hover:decoration-ink-strong hover:text-ink-strong"
					href="https://github.com/CodefiLabs/pickanumber/blob/main/examples/impeccable-rescoring.md"
					target="_blank"
					rel="noopener">full analysis →</a
				>
			</div>
			<p class="mt-4 max-w-3xl leading-relaxed text-ink-soft">
				Paul Bakaus' frontend-design skill bundle scored UIs on the 10 Nielsen heuristics, 0–4 each,
				summed to a 0–40 band. Two judges (an LLM pass + a deterministic detector with 24 antipattern
				rules) ran in isolation — exactly the right architecture. But the LLM still picked the
				numbers. We replaced that step with signed-evidence-item collection and ran the standard
				formula.
			</p>
			<div class="mt-6 flex flex-wrap items-baseline gap-x-3 gap-y-2 font-mono text-sm text-ink-soft">
				<span>vanilla</span>
				<span class="tabular text-3xl font-bold text-ink-strong">76</span>
				<span aria-hidden="true">→</span>
				<span>rescored</span>
				<span class="tabular text-3xl font-bold text-ink-strong">59</span>
				<span class="text-ink-faint" aria-hidden="true">·</span>
				<span>Δ</span>
				<span class="tabular text-3xl font-bold text-mark">17 pts</span>
			</div>
			<p class="mt-3 max-w-3xl text-sm text-ink-soft">
				Stable across runs. The page wasn't bad — but it wasn't 76. The vanilla score was carrying
				ambient charity.
			</p>
		</div>

		<!-- cua-bench callout — companion analysis, lighter ruled. -->
		<div class="mt-12 border-t border-rule pt-8">
			<div class="flex flex-wrap items-baseline justify-between gap-4">
				<h3 class="text-base font-semibold text-ink-strong">
					Companion analysis: <span class="font-mono">trycua/cua-bench</span>
				</h3>
				<a
					class="text-sm text-ink-soft underline underline-offset-4 decoration-ink-faint hover:decoration-ink-strong hover:text-ink-strong"
					href="https://github.com/CodefiLabs/pickanumber/blob/main/examples/cua-bench-analysis.md"
					target="_blank"
					rel="noopener">full analysis →</a
				>
			</div>
			<p class="mt-3 max-w-3xl leading-relaxed text-ink-soft">
				Computer-use agent benchmark. Reward is a deterministic float — no LLM in the scoring path,
				so principle 7 is satisfied by construction. The remaining opportunity is principles 2–6:
				signed multi-signal evidence accumulation instead of single-signal pass/fail. The honest
				take: not every benchmark needs the full methodology. cua-bench is a partial fit, not a
				slam-dunk like impeccable.
			</p>
		</div>
	</div>
</section>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ INSTALL — three skills                                        │
     ╰──────────────────────────────────────────────────────────────╯ -->
<section id="install" class="border-b border-rule py-24 lg:py-32">
	<div class="container-prose">
		<h2 class="text-section font-semibold text-ink-strong">Three ways to use it.</h2>
		<p class="mt-4 max-w-3xl text-ink-soft">
			One repo, three skills. Pick the one that matches your need. All three are
			<a class="underline underline-offset-4 decoration-ink-faint hover:decoration-ink-strong" href="https://skills.sh" target="_blank" rel="noopener">skills.sh</a>-installable into Claude Code, Cursor, Goose, OpenCode, and any other skills-aware agent.
		</p>

		<!-- Decision aid in code-comment voice -->
		<p class="mt-6 max-w-3xl font-mono text-sm leading-relaxed text-ink-soft">
			<span class="text-ink-faint">// not sure?</span>
			<span class="text-ink-strong">what-works-feedback-judge</span> is the simplest.
			<span class="text-ink-strong">hackathon-judge</span> if you have a code submission.
			<span class="text-ink-strong">evidence-scoring</span> if you're bringing your own domain.
		</p>

		<div class="mt-10 space-y-6">
			{#each skills as s}
				<div class="rounded-lg border border-rule bg-paper p-6 lg:p-8">
					<div class="flex flex-wrap items-baseline justify-between gap-4">
						<div>
							<h3 class="font-mono text-base font-semibold text-ink-strong">{s.name}</h3>
							<p class="mt-1 text-sm italic text-ink-soft">{s.tagline}</p>
						</div>
						<a
							class="text-sm text-ink-soft underline underline-offset-4 decoration-ink-faint hover:decoration-ink-strong hover:text-ink-strong"
							href="https://github.com/CodefiLabs/pickanumber/tree/main/{s.id}"
							target="_blank"
							rel="noopener">SKILL.md →</a
						>
					</div>
					<p class="mt-4 leading-relaxed text-ink-soft">{s.body}</p>
					<button
						onclick={() => copy(s.id, s.install)}
						title={s.install}
						class="group mt-5 flex w-full items-center justify-between gap-3 rounded-md border border-rule bg-paper-sunk px-4 py-3 font-mono text-xs text-ink transition hover:border-ink-soft sm:text-sm"
					>
						<span class="min-w-0 flex-1 truncate text-left">
							<span class="text-ink-faint">$</span> {s.install}
						</span>
						{#if copyState[s.id] === 'copied'}
							<span class="shrink-0 font-semibold text-ink-strong">✓ copied</span>
						{:else if copyState[s.id] === 'error'}
							<span class="shrink-0 font-semibold text-ink-strong">select manually</span>
						{:else}
							<svg
								width="14"
								height="14"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								class="shrink-0 text-ink-faint transition group-hover:text-ink"
								aria-hidden="true"
								><rect x="9" y="9" width="13" height="13" rx="2" /><path
									d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"
								/></svg
							>
						{/if}
					</button>
				</div>
			{/each}
		</div>
	</div>
</section>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ PAPER                                                         │
     ╰──────────────────────────────────────────────────────────────╯ -->
<section class="border-b border-rule py-24 lg:py-32">
	<div class="container-prose">
		<div class="grid gap-12 lg:grid-cols-[1fr_2fr] lg:gap-16">
			<div>
				<h2 class="text-section font-semibold text-ink-strong">The paper.</h2>
				<p class="mt-4 text-ink-soft">
					<em>Don't Let the LLM Pick a Number</em> — methodology paper. Calibrated on 18 hackathon
					submissions and 342 BLS occupations across 9 models. Includes the full derivation, ablations,
					and the impeccable rescoring case study.
				</p>
			</div>
			<div class="rounded-lg border border-rule bg-paper p-6 lg:p-8">
				<dl class="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
					<dt class="text-ink-faint">Title</dt>
					<dd class="text-ink-strong">Don't Let the LLM Pick a Number</dd>
					<dt class="text-ink-faint">Status</dt>
					<dd class="text-ink">v0.7 draft</dd>
					<dt class="text-ink-faint">Length</dt>
					<dd class="text-ink">~9k words + appendices</dd>
					<dt class="text-ink-faint">Calibrated on</dt>
					<dd class="text-ink">18 hackathons, 342 BLS occupations</dd>
					<dt class="text-ink-faint">Models tested</dt>
					<dd class="text-ink">9 frontier models</dd>
					<dt class="text-ink-faint">License</dt>
					<dd class="text-ink">MIT (markdown source)</dd>
				</dl>
				<a
					class="btn btn-primary mt-6 w-full"
					href="https://github.com/CodefiLabs/pickanumber/blob/main/paper/paper.md"
					target="_blank"
					rel="noopener"
				>
					Read the paper
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
						><path d="M5 12h14M12 5l7 7-7 7" /></svg
					>
				</a>
			</div>
		</div>
	</div>
</section>
</main>

<!-- ╭──────────────────────────────────────────────────────────────╮
     │ FOOTER                                                        │
     ╰──────────────────────────────────────────────────────────────╯ -->
<footer class="bg-paper py-12">
	<div class="container-prose">
		<div
			class="flex flex-col gap-6 border-t border-rule pt-10 sm:flex-row sm:items-center sm:justify-between"
		>
			<div class="flex items-center gap-3">
				<div
					class="flex h-7 w-7 items-center justify-center rounded border-[1.5px] border-ink-strong text-xs font-bold text-ink-strong"
				>
					P
				</div>
				<span class="font-mono text-xs text-ink-soft">pickanumber · codefilabs</span>
			</div>

			<div class="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
				<a
					class="text-ink-faint transition hover:text-ink"
					href="https://github.com/CodefiLabs/pickanumber"
					target="_blank"
					rel="noopener">GitHub</a
				>
				<a
					class="text-ink-faint transition hover:text-ink"
					href="https://skills.sh/CodefiLabs/pickanumber"
					target="_blank"
					rel="noopener">skills.sh</a
				>
				<a
					class="text-ink-faint transition hover:text-ink"
					href="https://github.com/CodefiLabs/mybench"
					target="_blank"
					rel="noopener">MyBench</a
				>
				<span class="text-ink-faint">·</span>
				<span class="text-ink-faint">MIT</span>
			</div>
		</div>

		<p class="mt-8 max-w-2xl text-xs leading-relaxed text-ink-faint">
			Methodology calibrated on 18 hackathon submissions and 342 BLS occupations across 9 frontier
			models. Worked rescoring case studies on <span class="font-mono">pbakaus/impeccable</span> and
			<span class="font-mono">trycua/cua-bench</span>. Pairwise diagnostic pattern borrows from
			<span class="font-mono">lechmazur/writing-style</span>. Built by Kevin Kirchner at CodefiLabs.
		</p>
	</div>
</footer>
