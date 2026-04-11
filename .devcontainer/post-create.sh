#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
./.venv/bin/pip install -e ./wandas[dev]
curl -fsSL https://claude.ai/install.sh | bash

if [ -f /workspaces/wandas-agent/.claude/settings.json ]; then
  mkdir -p ~/.claude
  cp /workspaces/wandas-agent/.claude/settings.json ~/.claude/settings.json
fi