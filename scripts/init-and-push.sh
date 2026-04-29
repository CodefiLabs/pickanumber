#!/usr/bin/env bash
# Run this on your Mac (NOT in the agent sandbox).
# It cleans up any stale state, makes the first commit, creates the GitHub repo
# under CodefiLabs, and pushes.
#
# Prereqs: gh authenticated and a member of the CodefiLabs org.
#   gh auth status         # confirm
#   gh auth refresh -h github.com -s repo,read:org   # if needed

set -euo pipefail

cd "$(dirname "$0")/.."

# 1. Clean up any sandbox detritus
rm -f .git/index.lock 2>/dev/null || true
rm -f vite.config.js.timestamp-*.mjs 2>/dev/null || true
rm -rf .svelte-kit build node_modules 2>/dev/null || true

# 2. Init git if needed (idempotent)
if [ ! -d .git ]; then
  git init -b main
fi

# 3. Ensure git identity is set on this repo
git config user.email "kevin@codefiworks.com"
git config user.name  "Kevin Kirchner"

# 4. Stage + commit
git add -A
git commit -m "Initial commit — pickanumber v0.1

Methodology paper, three skills.sh-installable skills, and worked
rescoring case studies for evidence-based LLM scoring.

Skills:
- evidence-scoring          — generic seven-principle methodology
- what-works-feedback-judge — 4-bucket idea readiness checker
- hackathon-judge           — 4-pass project submission scorer

The seven principles, the formula, and the discrete impact set
{+5, +3, +2, +1, -1, -2, -3, -5} are imported unchanged from
PROJ-ai-judge-scoring (Don't Let the LLM Pick a Number).

The site at src/routes/+page.svelte renders from the same
src/lib/formula.js + src/lib/principles.js that the skills
reference, so the math doesn't drift between the page and the
skill bundles.

Calibrated on 18 hackathon submissions and 342 BLS occupations
across 9 frontier models. Worked rescoring case studies on
pbakaus/impeccable (76 vs 59 separation) and trycua/cua-bench
(partial fit — P7 satisfied, P2-P6 wide open)."

# 5. Create the GitHub repo in CodefiLabs and push
gh repo create CodefiLabs/pickanumber \
  --public \
  --source=. \
  --remote=origin \
  --description="Don't let the LLM pick a number. Methodology, paper, and skills.sh-installable skills for evidence-based LLM scoring." \
  --homepage="https://pickanumber.codefi.io" \
  --push

echo ""
echo "✓ Pushed to https://github.com/CodefiLabs/pickanumber"
echo "✓ skills.sh will index the three SKILL.md files within ~24h:"
echo "    https://skills.sh/CodefiLabs/pickanumber/evidence-scoring"
echo "    https://skills.sh/CodefiLabs/pickanumber/what-works-feedback-judge"
echo "    https://skills.sh/CodefiLabs/pickanumber/hackathon-judge"
echo ""
echo "Next steps:"
echo "  1. npm install && npm run dev   # local preview at http://localhost:5173"
echo "  2. Set up Vercel / Netlify / Cloudflare Pages for pickanumber.codefi.io"
echo "  3. Add 'pickanumber', 'ai-evaluation', 'llm-as-judge' topics on the GitHub repo"
