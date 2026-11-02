#!/usr/bin/env bash
# Usage: scripts/commit_and_push.sh <message> <path>...
# Commit the given paths as the Actions bot, rebase onto the remote tip, check
# the append-only rule on what is about to be published, then push to main.
set -euo pipefail

message="$1"
shift

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git add -- "$@"
if git diff --cached --quiet; then
  echo "Nothing to commit for: $*"
  exit 0
fi
git commit -m "$message"

for attempt in 1 2 3; do
  git fetch origin main
  base="$(git rev-parse origin/main)"
  git rebase origin/main
  # The sha changed with the rebase, so check again against the remote tip.
  # Deliberately incremental (base = remote tip), not the whole history scan that
  # CI runs: one bad commit anywhere in history must keep CI red, but must not
  # stop the bot from recording new data every day.
  python -m ftracker.immutability --base "$base"
  if git push origin HEAD:main; then
    exit 0
  fi
  echo "Push rejected (attempt $attempt of 3)."
  sleep $((attempt * 5))
done
echo "Push failed after 3 attempts." >&2
exit 1
