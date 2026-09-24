#!/usr/bin/env bash
set -euo pipefail
AI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$AI_ROOT/.." && pwd)"
cd "$ROOT"
NAME="$(python -c 'import tomllib,re; d=tomllib.load(open("ai-tools/project.toml","rb")); print(re.sub(r"[^A-Za-z0-9_-]+","-",d["project"]["name"]).strip("-").lower() or "research")')"
SESSION="rw-${NAME}"
if [ $# -gt 0 ]; then tmux select-window -t "$SESSION:$1"; fi
exec tmux attach-session -t "$SESSION"
