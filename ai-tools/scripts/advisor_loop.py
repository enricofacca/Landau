#!/usr/bin/env python3
import os, subprocess, sys, time, tomllib
from datetime import datetime
from pathlib import Path

AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
WB=AI_ROOT/"scripts"/"workbench.py"
ADVICE=AI_ROOT/"research"/"advice"

def wb(*a,capture=False):
    return subprocess.run([sys.executable,str(WB),*a],cwd=ROOT,text=True,capture_output=capture)

with (AI_ROOT/"project.toml").open("rb") as f:
    cfg=tomllib.load(f)
env=cfg["agents"]["advisor"]["command_env"]
cmd=os.environ.get(env,"").strip()
if not cmd:
    raise SystemExit(f"{env} is not set; export a batch advisor command that reads stdin.")

poll=int(cfg["workflow"].get("advisor_poll_seconds",45))
ADVICE.mkdir(exist_ok=True)
print(f"Advisor watcher active; poll={poll}s",flush=True)

while True:
    if wb("advisor-needed").returncode==0:
        pr=wb("prompt","advisor",capture=True).stdout
        r=subprocess.run(cmd,shell=True,cwd=ROOT,input=pr,text=True,capture_output=True)
        output=(r.stdout or "") + (("\n[stderr]\n"+r.stderr) if r.stderr else "")
        print("\n=== ADVISOR REVIEW ===\n"+output,flush=True)
        stamp=datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        hist=ADVICE/f"{stamp}.md"
        review=f"# Advisor review — {stamp}\n\n{output.strip()}\n"
        hist.write_text(review); (ADVICE/"LATEST.md").write_text(review)
        wb("log","--actor","advisor","--kind","review" if r.returncode==0 else "failure","--message",f"advisor review archived at {hist.relative_to(ROOT)} (exit={r.returncode})")
        wb("mark-advisor-reviewed")
        wb("status",capture=True)
    time.sleep(poll)
