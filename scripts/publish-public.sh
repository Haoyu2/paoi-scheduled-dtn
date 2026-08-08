#!/bin/bash
# Publish the CURRENT tree to the public artifact repo as ONE curated commit
# (child of the public main), without exposing the dev history.
#   ./scripts/publish-public.sh "Public artifact v1.1: camera-ready"
#   ROOT=1 ./scripts/publish-public.sh "Public artifact v1.0"   # parentless root (force-push)
# Remotes: origin = Haoyu2/paoi-scheduled-dtn-dev (private, full history)
#          public = UNO-Networks-Lab/paoi-scheduled-dtn (curated)
# PRIVATE_PATHS are tracked in dev but stripped from the public tree.
set -euo pipefail
MSG="${1:?usage: publish-public.sh \"commit message\"}"
PRIVATE_PATHS=(paper/cover-letter.md)

# Build the public tree = HEAD tree minus PRIVATE_PATHS, via a temp index.
TMPIDX=$(mktemp)
trap 'rm -f "$TMPIDX"' EXIT
GIT_INDEX_FILE="$TMPIDX" git read-tree HEAD
GIT_INDEX_FILE="$TMPIDX" git rm -q --cached --ignore-unmatch -- "${PRIVATE_PATHS[@]}"
TREE=$(GIT_INDEX_FILE="$TMPIDX" git write-tree)

if [ "${ROOT:-0}" = "1" ]; then
  NEW=$(git commit-tree "$TREE" -m "$MSG")
  git push --force public "${NEW}:refs/heads/main"
  echo "published ROOT ${NEW} -> public/main (force)"
else
  git fetch public
  PARENT=$(git rev-parse public/main)
  NEW=$(git commit-tree "$TREE" -p "$PARENT" -m "$MSG")
  git push public "${NEW}:refs/heads/main"
  echo "published ${NEW} -> public/main (parent ${PARENT})"
fi
echo "tag it with: git push public ${NEW}:refs/tags/<vX.Y-...>"
