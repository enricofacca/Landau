#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
CTL=AI_ROOT/".workbench"/"control"
CTL.mkdir(parents=True,exist_ok=True)
ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["pause","resume","status"]); ap.add_argument("agent")
a=ap.parse_args(); p=CTL/f"{a.agent}.pause"
if a.action=="pause": p.write_text("paused by human\n"); print(f"{a.agent}: pause requested")
elif a.action=="resume":
    if p.exists(): p.unlink()
    print(f"{a.agent}: resumed")
else: print(f"{a.agent}: {'PAUSED' if p.exists() else 'running'}")
