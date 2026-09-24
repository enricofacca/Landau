#!/usr/bin/env bash
set -euo pipefail
AI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$AI_ROOT/.." && pwd)"
cd "$ROOT"
DETACH=0
if [ "${1:-}" = "--detach" ]; then DETACH=1; fi
if ! command -v tmux >/dev/null 2>&1; then echo "tmux is required" >&2; exit 2; fi
NAME="$(python -c 'import tomllib,re; d=tomllib.load(open("ai-tools/project.toml","rb")); print(re.sub(r"[^A-Za-z0-9_-]+","-",d["project"]["name"]).strip("-").lower() or "research")')"
SESSION="rw-${NAME}"
if tmux has-session -t "$SESSION" 2>/dev/null; then
  [ "$DETACH" -eq 1 ] && { echo "Session already running: $SESSION"; exit 0; }
  exec tmux attach-session -t "$SESSION"
fi
mapfile -t AGENTS < <(python ai-tools/scripts/workbench.py list-agents)
[ "${#AGENTS[@]}" -gt 0 ] || { echo "No coding agents configured" >&2; exit 2; }
FIRST="${AGENTS[0]}"

make_coder_window() {
  local agent="$1"
  if ! tmux list-windows -t "$SESSION" -F '#W' 2>/dev/null | grep -qx "$agent"; then
    tmux new-window -t "$SESSION" -n "$agent"
  fi
  tmux send-keys -t "$SESSION:$agent.0" "cd '$ROOT'; python ai-tools/scripts/agent_loop.py --agent '$agent'" C-m
  tmux split-window -h -t "$SESSION:$agent" "cd '$ROOT'; echo 'CONTROL PANE for $agent'; echo 'account: python ai-tools/scripts/account.py current $agent'; echo 'accounts: python ai-tools/scripts/account.py status'; echo 'pause: python ai-tools/scripts/control.py pause $agent'; echo 'interactive: python ai-tools/scripts/backend_runner.py --agent $agent --mode interactive'; echo 'resume: python ai-tools/scripts/control.py resume $agent'; exec \"${SHELL:-/bin/bash}\""
  tmux select-layout -t "$SESSION:$agent" even-horizontal >/dev/null
}

tmux new-session -d -s "$SESSION" -n bootstrap "cd '$ROOT'; exec \"${SHELL:-/bin/bash}\""
for agent in "${AGENTS[@]}"; do make_coder_window "$agent"; done
tmux kill-window -t "$SESSION:bootstrap"
tmux new-window -t "$SESSION" -n advisor "cd '$ROOT'; python ai-tools/scripts/advisor_loop.py; exec \"${SHELL:-/bin/bash}\""
tmux new-window -t "$SESSION" -n status "cd '$ROOT'; python ai-tools/scripts/status_watch.py"
tmux select-window -t "$SESSION:$FIRST"
if [ "$DETACH" -eq 1 ]; then
  echo "Workbench running in background tmux session: $SESSION"
  echo "Attach: ./ai-tools/scripts/attach-workbench.sh"
else
  exec tmux attach-session -t "$SESSION"
fi
