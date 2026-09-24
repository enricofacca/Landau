#!/usr/bin/env python3
import os, subprocess, sys, time, tomllib
from pathlib import Path
AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
WB=AI_ROOT/"scripts"/"workbench.py"
with (AI_ROOT/"project.toml").open("rb") as f:
    cfg=tomllib.load(f)
refresh=int(cfg["workflow"].get("status_refresh_seconds",2))
try:
    while True:
        r=subprocess.run([sys.executable,str(WB),"status"],cwd=ROOT,text=True,capture_output=True)
        os.system("clear")
        print(r.stdout or r.stderr)
        print("[status] Ctrl-C to exit")
        time.sleep(refresh)
except KeyboardInterrupt:
    pass
