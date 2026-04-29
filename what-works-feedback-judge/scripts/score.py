#!/usr/bin/env python3
"""
Score helper for the what-works-feedback-judge skill.

Computes the canonical formula on 4-bucket evidence:
  - working      magnitudes {+1, +2, +3, +5}
  - not_working  magnitudes {-1, -2, -3, -5}
  - missing      magnitudes {-1, -2, -3, -5}   (tagged "add" downstream)
  - confusing    magnitudes {-1, -2, -3}        (tagged "clarify" downstream; -5 NOT allowed)

Also handles JSON persistence to ./_judge/<slug>.json by default,
appending a new pass to existing files so iterations accumulate.
Override the directory with the JUDGE_DIR environment variable.

Formula (from paper/paper.md):
  net_impact     = sum of all evidence values
  total_items    = count of all items
  normalized     = net_impact / sqrt(total_items)        (0 if total_items == 0)
  raw_score      = clamp(50 + normalized * 8.0, 0, 100)
  density        = total_items / 20
  multiplier     = 0.75 + 0.25 * clamp(density, 0, 1)    (max 1.0 — confirms, never amplifies)
  final          = round(50 + (raw_score - 50) * multiplier)

Usage:
  # Compute score from evidence JSON on stdin
  echo '{"working":[{"value":3,"text":"..."}], ...}' | python3 score.py

  # Compute and save (appends a pass to <slug>.json)
  python3 score.py --save --slug my-idea --title "My Idea" --input evidence.json

  # Load and print existing state for slug
  python3 score.py --load --slug my-idea

  # Use a custom output directory
  JUDGE_DIR=/tmp/judge python3 score.py --save --slug my-idea --input evidence.json
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Default location is ./_judge/ relative to the current working directory.
# Override with $JUDGE_DIR for centralized storage across projects, testing,
# or alternate setups.
JUDGE_DIR = Path(os.environ.get("JUDGE_DIR", "./_judge"))

ALLOWED_MAGNITUDES = {
    "working":     {1, 2, 3, 5},
    "not_working": {-1, -2, -3, -5},
    "missing":     {-1, -2, -3, -5},
    "confusing":   {-1, -2, -3},
}

BUCKET_ORDER = ("working", "not_working", "missing", "confusing")


def compute_scores(evidence: dict) -> dict:
    """Run the formula on evidence buckets. Return a scores dict.

    Validates that each item's magnitude is allowed for its bucket — surfaces
    miscalibration early instead of silently producing a wrong score.
    """
    all_values = []
    for bucket in BUCKET_ORDER:
        for item in evidence.get(bucket, []):
            value = item.get("value")
            if value is None:
                raise ValueError(f"Item in bucket '{bucket}' missing 'value' field: {item}")
            if value not in ALLOWED_MAGNITUDES[bucket]:
                raise ValueError(
                    f"Invalid magnitude {value} for bucket '{bucket}'. "
                    f"Allowed: {sorted(ALLOWED_MAGNITUDES[bucket])}. "
                    f"Item text: {item.get('text', '<no text>')}"
                )
            all_values.append(value)

    total_items = len(all_values)
    net_impact = sum(all_values)

    if total_items == 0:
        normalized = 0.0
    else:
        normalized = net_impact / math.sqrt(total_items)

    raw_score = 50 + (normalized * 8.0)
    raw_score = max(0.0, min(100.0, raw_score))

    density = total_items / 20
    density_clamped = max(0.0, min(1.0, density))
    multiplier = 0.75 + (0.25 * density_clamped)

    deviation = raw_score - 50
    final = round(50 + (deviation * multiplier))

    return {
        "net_impact": net_impact,
        "total_items": total_items,
        "normalized": round(normalized, 3),
        "raw_score": round(raw_score, 2),
        "density": round(density, 3),
        "multiplier": round(multiplier, 3),
        "final": final,
        "confidence": round(density_clamped, 2),
    }


def load_idea(slug: str) -> dict | None:
    """Load existing JSON for slug, or None if it doesn't exist."""
    path = JUDGE_DIR / f"{slug}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_pass(slug: str, title: str, evidence: dict, scores: dict, summary: str = "") -> dict:
    """Append a pass to <JUDGE_DIR>/<slug>.json. Create file if needed."""
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = JUDGE_DIR / f"{slug}.json"

    now = datetime.now(timezone.utc).isoformat()

    existing = load_idea(slug)
    if existing is None:
        doc = {
            "id": slug,
            "title": title,
            "created": now,
            "passes": [],
        }
    else:
        doc = existing
        if title and title != slug:
            doc["title"] = title

    next_version = len(doc["passes"]) + 1
    doc["passes"].append({
        "version": next_version,
        "timestamp": now,
        "summary": summary,
        "evidence": evidence,
        "scores": scores,
    })

    path.write_text(json.dumps(doc, indent=2))
    return doc


def normalize_evidence(payload: dict) -> dict:
    """Accept either a flat evidence dict or a wrapper {"evidence": {...}}."""
    if "evidence" in payload and isinstance(payload["evidence"], dict):
        evidence = payload["evidence"]
    else:
        evidence = payload

    for bucket in BUCKET_ORDER:
        evidence.setdefault(bucket, [])

    return evidence


def main():
    parser = argparse.ArgumentParser(
        description="Score 4-bucket evidence using the AI-judge formula. Optionally persist a pass.",
    )
    parser.add_argument("--save", action="store_true",
                        help="Append a new pass to the slug's JSON file in $JUDGE_DIR (default ./_judge/).")
    parser.add_argument("--load", action="store_true",
                        help="Load and print current state for slug.")
    parser.add_argument("--slug", help="Slug for the idea (kebab-case, e.g., agent-hq-pricing).")
    parser.add_argument("--title", help="Human-readable title (used on first save).")
    parser.add_argument("--summary", default="", help="Optional one-line summary of this pass.")
    parser.add_argument("--input", help="Path to evidence JSON file (default: stdin).")
    args = parser.parse_args()

    if args.load:
        if not args.slug:
            print("--load requires --slug", file=sys.stderr)
            sys.exit(2)
        existing = load_idea(args.slug)
        if existing is None:
            print(json.dumps({"error": "not_found", "slug": args.slug}))
            sys.exit(0)
        print(json.dumps(existing, indent=2))
        return

    if args.input:
        payload = json.loads(Path(args.input).read_text())
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            print("No evidence provided. Pipe JSON to stdin or pass --input.", file=sys.stderr)
            sys.exit(2)
        payload = json.loads(raw)

    evidence = normalize_evidence(payload)
    scores = compute_scores(evidence)

    if args.save:
        if not args.slug:
            print("--save requires --slug", file=sys.stderr)
            sys.exit(2)
        title = args.title or args.slug.replace("-", " ").title()
        doc = save_pass(args.slug, title, evidence, scores, summary=args.summary)
        print(json.dumps({
            "scores": scores,
            "saved_to": str(JUDGE_DIR / f"{args.slug}.json"),
            "version": doc["passes"][-1]["version"],
            "passes_total": len(doc["passes"]),
        }, indent=2))
    else:
        print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
