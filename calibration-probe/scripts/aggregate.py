#!/usr/bin/env python3
"""Calibration probe aggregator + regime classifier.

Reads N saved run-NNN.json files (each containing a "scores" array of integers
in the configured scale range), computes per-item and across-runs statistics,
classifies the model's number-picking behavior into one of five regimes
(CALIBRATED, INFLATION_LIKELY, DEFLATION_LIKELY, PICKS_A_NUMBER, JITTERY,
or AMBIGUOUS), and writes aggregate.json + REPORT.md.

This script is provider-agnostic: it does NOT make API calls. The agent
running the probe makes the calls in whatever runtime is available, saves
each repeat as run-NNN.json, then invokes this aggregator.

Usage:
    python3 aggregate.py \\
        --runs-dir runs-probes/<run-name> \\
        --items items/sentence-structure.json \\
        --out runs-probes/<run-name>

Per-run JSON shape (one file per repeat):
    { "scores": [3, 7, 2, 9, ...], "summary": "..." }            # success
    { "parse_failed": true, "error": "..." }                      # failure

Items file shape:
    {
      "name": "sentence-structure",
      "scale_min": 1,
      "scale_max": 10,
      "items": ["...", "...", ...]
    }

Origin: Section 5.7 + Appendix E of *Don't Let the LLM Pick a Number*.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_runs(runs_dir: Path) -> list[dict[str, Any]]:
    """Load every run-NNN.json file in lexical order."""
    files = sorted(runs_dir.glob("run-*.json"))
    runs: list[dict[str, Any]] = []
    for f in files:
        try:
            runs.append(load_json(f))
        except json.JSONDecodeError as e:
            runs.append({"parse_failed": True, "error": f"{f.name}: {e}"})
    return runs


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate(
    runs: list[dict[str, Any]],
    items: list[str],
    scale_min: int,
    scale_max: int,
) -> dict[str, Any]:
    """Compute per-item and across-runs statistics from N runs."""
    successful = [
        r for r in runs
        if not r.get("parse_failed") and isinstance(r.get("scores"), list)
    ]
    n_items = len(items)

    # Per-item stats
    per_item: list[dict[str, Any]] = []
    for i in range(n_items):
        item_scores = [r["scores"][i] for r in successful if i < len(r["scores"])]
        if item_scores:
            per_item.append({
                "index": i + 1,
                "item_text": items[i],
                "scores": item_scores,
                "n": len(item_scores),
                "mean": round(statistics.mean(item_scores), 4),
                "std": round(statistics.stdev(item_scores), 4) if len(item_scores) > 1 else 0.0,
                "min": min(item_scores),
                "max": max(item_scores),
                "range": max(item_scores) - min(item_scores),
                "mode": Counter(item_scores).most_common(1)[0][0],
            })
        else:
            per_item.append({
                "index": i + 1,
                "item_text": items[i],
                "scores": [],
                "n": 0,
            })

    # Across-runs distribution
    all_scores: list[int] = []
    for r in successful:
        for s in r.get("scores", []):
            if isinstance(s, (int, float)):
                all_scores.append(int(s))

    histogram = {s: 0 for s in range(scale_min, scale_max + 1)}
    for s in all_scores:
        if scale_min <= s <= scale_max:
            histogram[s] += 1

    n_total = len(all_scores)
    ceiling_threshold = scale_max - 1
    floor_threshold = scale_min + 1
    ceiling_count = sum(c for s, c in histogram.items() if s >= ceiling_threshold)
    floor_count = sum(c for s, c in histogram.items() if s <= floor_threshold)

    across_runs: dict[str, Any] = {}
    if all_scores:
        across_runs = {
            "n_total_scores": n_total,
            "mean": round(statistics.mean(all_scores), 4),
            "median": statistics.median(all_scores),
            "mode": Counter(all_scores).most_common(1)[0][0],
            "min": min(all_scores),
            "max": max(all_scores),
            "range": max(all_scores) - min(all_scores),
            "std": round(statistics.stdev(all_scores), 4) if n_total > 1 else 0.0,
            "histogram": histogram,
            "ceiling_count": ceiling_count,
            "ceiling_rate": round(ceiling_count / n_total, 4) if n_total else 0.0,
            "floor_count": floor_count,
            "floor_rate": round(floor_count / n_total, 4) if n_total else 0.0,
        }

    per_item_stds = [pi["std"] for pi in per_item if pi.get("n", 0) > 1]
    mean_per_item_std = round(statistics.mean(per_item_stds), 4) if per_item_stds else None

    return {
        "successful_runs": len(successful),
        "failed_runs": len(runs) - len(successful),
        "n_items": n_items,
        "per_item": per_item,
        "across_runs": across_runs,
        "mean_per_item_std": mean_per_item_std,
        "regime_guess": guess_regime(across_runs, mean_per_item_std),
    }


# ---------------------------------------------------------------------------
# Regime classifier
# ---------------------------------------------------------------------------

def guess_regime(across: dict[str, Any], mean_per_item_std: float | None) -> str:
    """Heuristic regime classifier from probe distribution shape.

    Order matters — JITTERY first because high per-item std makes the
    distribution-shape rules unreliable. Inflation/deflation before
    PICKS_A_NUMBER because a tight cluster at the ceiling is inflation,
    not picks-a-number.

    Heuristics, not certainties — sanity-check against the histogram.
    """
    if not across:
        return "AMBIGUOUS"

    ceiling_rate = across.get("ceiling_rate", 0.0)
    floor_rate = across.get("floor_rate", 0.0)
    range_ = across.get("range", 0)

    if mean_per_item_std is not None and mean_per_item_std >= 2.5:
        return "JITTERY"
    if ceiling_rate >= 0.25 and floor_rate < 0.05:
        return "INFLATION_LIKELY"
    if floor_rate >= 0.25 and ceiling_rate < 0.05:
        return "DEFLATION_LIKELY"
    if range_ <= 2:
        return "PICKS_A_NUMBER"
    if range_ >= 5 and floor_rate >= 0.05 and ceiling_rate < 0.35:
        return "CALIBRATED"
    return "AMBIGUOUS"


# ---------------------------------------------------------------------------
# Recommendation text
# ---------------------------------------------------------------------------

REGIME_RECOMMENDATIONS = {
    "CALIBRATED": (
        "Your model is in good shape. Use Principles 1, 4, 5 only — collect "
        "evidence, sqrt-normalize, regress sparse evaluations toward the mean. "
        "The full pipeline's counter-bias may over-correct on your model. Run "
        "a small naive-vs-principled comparison on 5–10 ground-truth items if "
        "you want to verify."
    ),
    "INFLATION_LIKELY": (
        "Your model defaults to praise. The full evidence-scoring pipeline is "
        "designed for exactly this case — it will close the gap to humans. "
        "Use the full counter-bias prompts."
    ),
    "DEFLATION_LIKELY": (
        "Your model defaults to criticism. The full pipeline will help, but "
        "turn DOWN the counter-bias instructions ('skeptic's eye', "
        "'don't inflate') — they will compound the deflation."
    ),
    "PICKS_A_NUMBER": (
        "Your model can't differentiate quality on this task. Range ≤ 2 means "
        "it gives essentially the same number to everything. The methodology "
        "cannot rescue this. Switch models, or accept that automated scoring "
        "on this task will be unreliable."
    ),
    "JITTERY": (
        "Your model is unstable. The same item gets very different scores "
        "run-to-run (per-item std ≥ 2.5). Reliability is the constraint, not "
        "calibration. Use ensembling (run the model 3–5 times and average) "
        "before reaching for the methodology."
    ),
    "AMBIGUOUS": (
        "The probe didn't classify cleanly. Default to the full pipeline with "
        "a post-hoc audit — track positive:negative item ratio per criterion "
        "and watch for either inflation (>2:1 positive) or over-correction "
        "(>2:1 negative)."
    ),
}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(out_dir: Path, items_payload: dict[str, Any], agg: dict[str, Any]) -> None:
    regime = agg.get("regime_guess", "AMBIGUOUS")
    lines = [
        "# Calibration Probe Report",
        "",
        f"Probe: {items_payload.get('name', '(unnamed)')}",
        f"Items: {agg['n_items']}",
        f"Successful runs: {agg['successful_runs']}",
        f"Failed runs: {agg['failed_runs']}",
        "",
        f"## Regime: **{regime}**",
        "",
        REGIME_RECOMMENDATIONS.get(regime, ""),
        "",
    ]

    across = agg.get("across_runs") or {}
    if across:
        lines.extend([
            "## Distribution (all scores across all runs)",
            "",
            f"- Total scores: {across['n_total_scores']}",
            f"- Mean: {across['mean']}",
            f"- Median: {across['median']}",
            f"- Mode: {across['mode']}",
            f"- Min/Max: {across['min']}/{across['max']}",
            f"- Range: {across['range']}",
            f"- Std: {across['std']}",
            f"- Ceiling rate (top 2 of scale): {across['ceiling_rate']:.4f} "
            f"({across['ceiling_count']}/{across['n_total_scores']})",
            f"- Floor rate (bottom 2 of scale): {across['floor_rate']:.4f} "
            f"({across['floor_count']}/{across['n_total_scores']})",
            "",
            "## Histogram",
            "",
            "| Score | Count | % |",
            "|---:|---:|---:|",
        ])
        n = across["n_total_scores"]
        for s, c in sorted(across["histogram"].items()):
            pct = c / n if n else 0
            lines.append(f"| {s} | {c} | {pct:.2%} |")

    if agg.get("mean_per_item_std") is not None:
        lines.extend([
            "",
            "## Test-Retest Stability",
            "",
            f"Mean per-item std across {agg['n_items']} items: "
            f"**{agg['mean_per_item_std']}**",
            "",
            "Lower = the model gives the same score for the same item across runs (locked in).",
            "Higher = scores vary a lot run-to-run for identical inputs (jittery / uncertain).",
        ])

    per_item_sorted = sorted(
        agg.get("per_item", []),
        key=lambda x: -(x.get("std") or 0.0),
    )[:5]
    if per_item_sorted and per_item_sorted[0].get("std", 0) > 0:
        lines.extend([
            "",
            "## Top 5 Most Variable Items",
            "",
            "| # | Item | Mean | Std | Min | Max | Mode |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ])
        for pi in per_item_sorted:
            text = pi.get("item_text", "")
            if len(text) > 60:
                text = text[:57] + "..."
            text = text.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {pi['index']} | {text} | {pi['mean']} | {pi['std']} | "
                f"{pi['min']} | {pi['max']} | {pi['mode']} |"
            )

    lines.extend([
        "",
        "## Regime Classifier Thresholds (in order)",
        "",
        "| # | Regime | Trigger condition |",
        "|---:|---|---|",
        "| 1 | JITTERY          | mean_per_item_std >= 2.5 |",
        "| 2 | INFLATION_LIKELY | ceiling_rate >= 0.25 AND floor_rate < 0.05 |",
        "| 3 | DEFLATION_LIKELY | floor_rate >= 0.25 AND ceiling_rate < 0.05 |",
        "| 4 | PICKS_A_NUMBER   | range <= 2 (after inflation/deflation rule out the extremes) |",
        "| 5 | CALIBRATED       | range >= 5 AND floor_rate >= 0.05 AND ceiling_rate < 0.35 |",
        "| 6 | AMBIGUOUS        | none of the above |",
    ])

    (out_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate calibration-probe runs and classify the regime.",
    )
    parser.add_argument(
        "--runs-dir",
        required=True,
        help="Directory containing run-NNN.json files (one per repeat).",
    )
    parser.add_argument(
        "--items",
        required=True,
        help="Path to the items JSON file used for the probe.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for aggregate.json + REPORT.md.",
    )

    args = parser.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    items_path = Path(args.items).resolve()
    out_dir = Path(args.out).resolve()

    if not runs_dir.exists():
        print(f"runs dir not found: {runs_dir}", file=sys.stderr)
        return 2
    if not items_path.exists():
        print(f"items file not found: {items_path}", file=sys.stderr)
        return 2

    items_payload = load_json(items_path)
    items = items_payload.get("items") or []
    scale_min = int(items_payload.get("scale_min", 1))
    scale_max = int(items_payload.get("scale_max", 10))

    runs = load_runs(runs_dir)
    if not runs:
        print(f"no run-NNN.json files found in {runs_dir}", file=sys.stderr)
        return 2

    agg = aggregate(runs, items, scale_min, scale_max)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "aggregate.json", {
        "items_name": items_payload.get("name"),
        "scale_min": scale_min,
        "scale_max": scale_max,
        "aggregate": agg,
    })
    write_report(out_dir, items_payload, agg)

    print(f"Regime: {agg['regime_guess']}")
    print(f"  successful_runs={agg['successful_runs']} failed={agg['failed_runs']}")
    if agg.get("across_runs"):
        ar = agg["across_runs"]
        print(
            f"  range={ar['range']} ceiling_rate={ar['ceiling_rate']:.3f} "
            f"floor_rate={ar['floor_rate']:.3f} mean_per_item_std={agg.get('mean_per_item_std')}"
        )
    print(f"Wrote {out_dir / 'aggregate.json'} and {out_dir / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
