#!/usr/bin/env python3
import argparse, re, subprocess
from pathlib import Path
AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
p=argparse.ArgumentParser(); p.add_argument("--name",required=True); p.add_argument("--package",required=True); a=p.parse_args()
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",a.package): p.error("--package must be a valid Python identifier")
pt=AI_ROOT/"project.toml"; s=pt.read_text().replace('name = "CHANGE_ME"',f'name = "{a.name}"',1).replace('package = "project_code"',f'package = "{a.package}"',1); pt.write_text(s)
pp=ROOT/"pyproject.toml"; pp.write_text(pp.read_text().replace('name = "project-code"',f'name = "{a.package.replace("_","-")}"',1))

readme=ROOT/"README.md"
if readme.exists():
    txt=readme.read_text()
    txt=re.sub(r"(?m)^# CHANGE_ME$",f"# {a.name}",txt,count=1)
    readme.write_text(txt)
old=ROOT/"src"/"project_code"; new=ROOT/"src"/a.package
if old.exists() and old!=new: old.rename(new)
for rel in ["tests/test_smoke.py","demos/smoke_demo.py"]:
    q=ROOT/rel
    if q.exists(): q.write_text(q.read_text().replace("project_code",a.package))
# Put a concrete baseline into the initial stage when possible.
sp=AI_ROOT/"research"/"stages"/"STAGE-0001"/"stage.toml"
if sp.exists():
    try: ref=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception: ref="UNCOMMITTED"
    x=sp.read_text().replace('base_ref = "TEMPLATE"',f'base_ref = "{ref}"',1); sp.write_text(x)
print(f"Configured {a.name} ({a.package}).")
print("Next: edit ai-tools/research/program.toml and STAGE-0001 technical_note/development_plan.")
print("Then configure ai-tools/config/runtime.toml and provider command environment variables.")
print("Replace the fake @example.com email_hint/workspace hints in ai-tools/config/accounts.toml.")
print("Run python ai-tools/scripts/prepare_account_profiles.py to inspect account setup, then --apply if desired.")
print("Start with ./ai-tools/scripts/start-workbench.sh [--detach].")
