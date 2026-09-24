#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, sys, tomllib
from pathlib import Path

AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
ACCOUNT=AI_ROOT/'scripts'/'account.py'

def load(path):
    with path.open('rb') as f: return tomllib.load(f)
def coder(cfg,agent):
    for d in cfg.get('agents',{}).get('coders',[]):
        if d.get('id')==agent: return d
    raise SystemExit(f'Unknown coder {agent}')
def current_profile(agent):
    r=subprocess.run([sys.executable,str(ACCOUNT),'current',agent],cwd=ROOT,text=True,capture_output=True)
    if r.returncode: return None
    return json.loads(r.stdout)
def mark_exhausted(agent,profile):
    return subprocess.run([sys.executable,str(ACCOUNT),'mark-exhausted',agent,profile],cwd=ROOT,text=True,capture_output=True)

def run_once(cmd,mode,prompt,transport,env,agent):
    if mode=='batch':
        if transport=='stdin': return subprocess.run(cmd,shell=True,cwd=ROOT,input=prompt,text=True,env=env)
        if transport=='file':
            p=AI_ROOT/'.workbench'/'prompts'/f'{agent}-batch.md'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(prompt); env['WORKBENCH_PROMPT_FILE']=str(p)
            return subprocess.run(cmd,shell=True,cwd=ROOT,text=True,env=env)
        raise SystemExit(f'Unsupported prompt_transport={transport!r}')
    return subprocess.run(cmd,shell=True,cwd=ROOT,env=env)

ap=argparse.ArgumentParser(); ap.add_argument('--agent',required=True); ap.add_argument('--mode',choices=['batch','interactive'],default='batch'); ap.add_argument('--prompt-file'); a=ap.parse_args()
project=load(AI_ROOT/'project.toml'); backends=load(AI_ROOT/'config'/'backends.toml').get('backends',{}); account_cfg=load(AI_ROOT/'config'/'accounts.toml') if (AI_ROOT/'config'/'accounts.toml').exists() else {'policy':{}}
d=coder(project,a.agent); backend_id=d.get('backend','custom')
if backend_id not in backends: raise SystemExit(f'Unknown backend {backend_id!r}')
b=backends[backend_id]; env_name=b.get('batch_command_env') if a.mode=='batch' else b.get('interactive_command_env'); cmd=os.environ.get(env_name or '','').strip()
if not cmd: raise SystemExit(f'{env_name} is not set for backend {backend_id!r}')

prompt=''
if a.mode=='batch': prompt=Path(a.prompt_file).read_text() if a.prompt_file else sys.stdin.read()
else:
    wb=subprocess.run([sys.executable,str(AI_ROOT/'scripts'/'workbench.py'),'prompt','coder','--agent',a.agent],cwd=ROOT,text=True,capture_output=True)
    p=AI_ROOT/'.workbench'/'prompts'/f'{a.agent}-interactive.md'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(wb.stdout)

policy=account_cfg.get('policy',{}); quota_code=int(policy.get('quota_exhausted_exit_code',75)); failover=bool(policy.get('automatic_failover',True)); attempted=[]
while True:
    prof=current_profile(a.agent) if d.get('account_pool') else None
    if d.get('account_pool') and not prof:
        print(f'No non-exhausted credential profile remains for {a.agent} ({d.get("account_pool")}).',file=sys.stderr); raise SystemExit(75)
    env=os.environ.copy(); env['WORKBENCH_ROOT']=str(ROOT); env['WORKBENCH_AGENT_ID']=a.agent; env['WORKBENCH_BACKEND']=backend_id
    if prof:
        env['WORKBENCH_ACCOUNT_PROFILE']=prof['id']
        env['WORKBENCH_ACCOUNT_SELECTOR']=str(prof.get('selector',prof['id']))
        env['WORKBENCH_ACCOUNT_EMAIL_HINT']=str(prof.get('email_hint',''))
        env['WORKBENCH_AUTH_STRATEGY']=str(prof.get('auth_strategy','selector_only'))
        attempted.append(prof['id'])

        strategy=prof.get('auth_strategy','selector_only')
        context=str(prof.get('auth_context','')).strip()
        if context:
            context=str(Path(context).expanduser())
            env['WORKBENCH_AUTH_CONTEXT']=context
        if strategy=='codex_home':
            if not context:
                raise SystemExit(f"Credential profile {prof['id']} requires auth_context for codex_home")
            env['CODEX_HOME']=context
        elif strategy=='claude_config_dir':
            if not context:
                raise SystemExit(f"Credential profile {prof['id']} requires auth_context for claude_config_dir")
            env['CLAUDE_CONFIG_DIR']=context
        elif strategy=='isolated_launcher':
            launcher=str(prof.get('launcher','')).strip()
            if not launcher:
                raise SystemExit(f"Credential profile {prof['id']} requires launcher for isolated_launcher")
            env['WORKBENCH_ACCOUNT_LAUNCHER']=str(Path(launcher).expanduser())
        elif strategy!='selector_only':
            raise SystemExit(f"Unsupported auth_strategy={strategy!r} for profile {prof['id']}")
    if a.mode=='interactive':
        env['WORKBENCH_PROMPT_FILE']=str(AI_ROOT/'.workbench'/'prompts'/f'{a.agent}-interactive.md')
        print(f"Interactive backend: {backend_id} / {a.agent} / profile={(prof or {}).get('id','none')}")
        print(f"Assignment prompt: {Path(env['WORKBENCH_PROMPT_FILE']).relative_to(ROOT)}")
    r=run_once(cmd,a.mode,prompt,b.get('prompt_transport','stdin'),env,a.agent)
    if r.returncode != quota_code or not prof or not failover: raise SystemExit(r.returncode)
    m=mark_exhausted(a.agent,prof['id']); print(f"[{a.agent}] credential profile {prof['id']} reported quota exhaustion; {m.stdout.strip()}",file=sys.stderr)
    nxt=current_profile(a.agent)
    if not nxt or nxt.get('id') in attempted: raise SystemExit(quota_code)
    print(f"[{a.agent}] retrying with credential profile {nxt['id']}",file=sys.stderr)
