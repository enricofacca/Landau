#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, subprocess, sys, tomllib
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
ROOT = AI_ROOT.parent
CFG = AI_ROOT / "config" / "runtime.toml"


def load():
    with CFG.open("rb") as f:
        return tomllib.load(f)


def python_executable(c):
    env = c.get("environment", {})
    p = env.get("python_executable", "python")
    q = (ROOT / p).resolve() if not Path(p).is_absolute() else Path(p)
    if q.exists():
        return str(q)
    return env.get("python_fallback", "python")


def resolve_argv(spec, c):
    py = python_executable(c)
    return [str(x).replace("{python}", py).replace("{root}", str(ROOT)) for x in spec.get("argv", [])]


ap = argparse.ArgumentParser(description="Run a command declared in ai-tools/config/runtime.toml")
ap.add_argument("program", nargs="?", help="program id, or 'list'")
ap.add_argument("args", nargs=argparse.REMAINDER)
a = ap.parse_args()
c = load(); programs = c.get("programs", {})
if not a.program or a.program == "list":
    for name, spec in programs.items():
        print(f"{name:20s} {spec.get('description','')}")
    raise SystemExit(0)
if a.program not in programs:
    raise SystemExit(f"Unknown program {a.program!r}; run: python ai-tools/scripts/run_allowed.py list")
spec = programs[a.program]
if a.args and not spec.get("allow_extra_args", False):
    raise SystemExit(f"Program {a.program!r} does not accept extra args")
argv = resolve_argv(spec, c) + a.args
print("[runtime]", " ".join(argv), flush=True)
raise SystemExit(subprocess.run(argv, cwd=ROOT, env=os.environ.copy()).returncode)
