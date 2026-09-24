#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, subprocess, sys, time, tomllib
from pathlib import Path
AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent; WB=AI_ROOT/'scripts'/'workbench.py'; RUNNER=AI_ROOT/'scripts'/'backend_runner.py'; CTL=AI_ROOT/'.workbench'/'control'
def wb(*a,capture=False): return subprocess.run([sys.executable,str(WB),*a],cwd=ROOT,text=True,capture_output=capture)
def cfg():
    with (AI_ROOT/'project.toml').open('rb') as f: return tomllib.load(f)
def owned_files(agent):
    files=[]
    for p in (AI_ROOT/'research'/'attempts').glob('ATTEMPT-*/status.toml'):
        try:
            with p.open('rb') as f: d=tomllib.load(f)
        except Exception: continue
        if d.get('owner')==agent:
            files.append(p); sid=d.get('study'); st=AI_ROOT/'research'/'studies'/str(sid)
            if st.exists(): files += [x for x in st.glob('*') if x.is_file()]
            exp=ROOT/str(d.get('experiment_dir',''))
            if exp.exists(): files += [x for x in exp.rglob('*') if x.is_file()]
    # backward-compatible single-owner studies
    for p in (AI_ROOT/'research'/'studies').glob('STUDY-*/status.toml'):
        try:
            with p.open('rb') as f: d=tomllib.load(f)
        except Exception: continue
        if d.get('owner')==agent:
            sid=p.parent.name; has_attempt=False
            for ap in (AI_ROOT/'research'/'attempts').glob('ATTEMPT-*/status.toml'):
                try:
                    with ap.open('rb') as f: ad=tomllib.load(f)
                    if ad.get('study')==sid: has_attempt=True; break
                except Exception: pass
            if not has_attempt: files += [x for x in p.parent.glob('*') if x.is_file()]
    return sorted(set(files))
def state(agent):
    h=hashlib.sha256()
    for p in owned_files(agent): h.update(str(p.relative_to(ROOT)).encode()); h.update(p.read_bytes())
    return h.hexdigest()
ap=argparse.ArgumentParser(); ap.add_argument('--agent',required=True); a=ap.parse_args(); c=cfg(); pause=int(c['workflow'].get('coder_pause_seconds',2)); stall_limit=int(c['workflow'].get('max_coder_stall_cycles_before_escalation',3)); stalls=0; iteration=0
print(f'Coder loop active: {a.agent}',flush=True)
while wb('agent-has-open',a.agent).returncode==0:
    pause_file=CTL/f'{a.agent}.pause'
    if pause_file.exists(): print(f'[{a.agent}] paused for human takeover',flush=True); time.sleep(max(2,pause)); continue
    if wb('agent-has-actionable',a.agent).returncode!=0:
        print(f'[{a.agent}] open work blocked; waiting for advisor/state change',flush=True); time.sleep(max(5,pause)); continue
    iteration+=1; before=state(a.agent); pr=wb('prompt','coder','--agent',a.agent,capture=True).stdout
    print(f'\n=== {a.agent} ITERATION {iteration} ===',flush=True)
    r=subprocess.run([sys.executable,str(RUNNER),'--agent',a.agent,'--mode','batch'],cwd=ROOT,input=pr,text=True)
    if r.returncode: wb('log','--actor','system','--kind','failure','--message',f'{a.agent} backend exit={r.returncode}')
    wb('status',capture=True); after=state(a.agent)
    if after==before:
        stalls+=1; wb('log','--actor','system','--kind','blocker','--message',f'{a.agent} produced no durable assigned-state change ({stalls}/{stall_limit}); advisor review requested')
        if stalls>=stall_limit: print(f'[{a.agent}] stalled; advisor intervention/state change required',flush=True); stalls=0
    else: stalls=0
    time.sleep(pause)
print(f'[{a.agent}] all assigned attempts/studies terminal or no longer assigned.')
raise SystemExit(wb('validate').returncode)
