#!/usr/bin/env bash
set -euo pipefail
AI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$AI_ROOT/.." && pwd)"
cd "$ROOT"
python ai-tools/scripts/workbench.py status >/dev/null
python ai-tools/scripts/workbench.py validate
python ai-tools/scripts/run_allowed.py test
python ai-tools/scripts/run_allowed.py ai_contract
python - <<'PY'
import tomllib
from pathlib import Path
for p in [
    Path('ai-tools/project.toml'),
    Path('ai-tools/config/runtime.toml'),
    Path('ai-tools/config/backends.toml'),
    Path('ai-tools/config/accounts.toml'),
    Path('ai-tools/research/stages/STAGE-0001/stage.toml'),
    Path('ai-tools/research/studies/STUDY-0001/status.toml'),
    Path('ai-tools/research/attempts/ATTEMPT-0001/status.toml'),
]:
    with p.open('rb') as f: tomllib.load(f)
print('TOML parse: OK')
PY
