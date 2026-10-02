#!/usr/bin/env bash
# Point git at the versioned hooks in .githooks/ (pre-push: gitleaks + tests).
# Run once per Mac checkout or worktree. Do NOT run it in the droplet's
# /root/nemo-repo: growth/publish_state.sh pushes from there unattended, the
# box has no gitleaks or server/node_modules in that checkout, and a failing
# hook would silently stop the daily state publish. CI covers those pushes.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "hooks installed: $(ls .githooks | tr '\n' ' ')"
