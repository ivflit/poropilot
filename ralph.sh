#!/usr/bin/env bash
#
# Ralph loop — autonomous iteration for BIG, complex tasks only.
#
# Most tasks don't need this: just do them normally. Only run Ralph on a task
# flagged `Ralph: yes` in tasks.md (and labelled `ralph` on its issue).
#
# Usage:  ./ralph.sh <task-id> [max-iterations]
#   e.g.  ./ralph.sh T3
#         ./ralph.sh T3 20
#
# Requires the `claude` CLI and a clean-ish git tree. Each iteration lets the
# agent edit files AND run commands autonomously (tests, git) — that's the point,
# but it's why this is opt-in and for local use only.
#
set -euo pipefail

TASK_ID="${1:?usage: ./ralph.sh <task-id> [max-iterations]}"
MAX_ITERS="${2:-15}"

read -r -d '' PROMPT <<EOF || true
You are working on the PoroPilot project. Read CLAUDE.md, CONTEXT.md,
docs/ARCHITECTURE.md and tasks.md first.

Work ONLY on task ${TASK_ID} in tasks.md. Then:
1. Load the relevant skill (fastapi-python for backend, vue3-frontend for frontend).
2. Find the FIRST unchecked acceptance-criterion checkbox for ${TASK_ID}.
3. Implement just enough to satisfy it, following the conventions in CLAUDE.md.
4. Run the tests (backend: cd backend && python -m unittest discover;
   frontend: cd frontend && npx playwright test). Add or adjust tests as needed.
5. ONLY if the tests pass, tick that checkbox in tasks.md ([ ] -> [x]).
6. Commit with a short, present-tense, plain UK-English message.
   Do NOT mention AI, Claude, or co-authorship in the message.

If every acceptance criterion for ${TASK_ID} is already ticked, reply with
exactly RALPH_DONE and change nothing.
EOF

echo "⚠️  Ralph runs the agent with autonomous edit + command permissions."
echo "    Task: ${TASK_ID} · max iterations: ${MAX_ITERS}"
echo

for (( i = 1; i <= MAX_ITERS; i++ )); do
  echo "──────────── Ralph iteration ${i}/${MAX_ITERS} (${TASK_ID}) ────────────"
  output="$(claude -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee /dev/tty)" || true
  if grep -q "RALPH_DONE" <<< "$output"; then
    echo
    echo "✅ Ralph finished — all acceptance criteria for ${TASK_ID} are ticked."
    exit 0
  fi
done

echo
echo "⚠️  Hit the iteration cap (${MAX_ITERS}) without RALPH_DONE — review manually."
exit 1
