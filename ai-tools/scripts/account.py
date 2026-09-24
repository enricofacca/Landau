#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, tomllib
from pathlib import Path

AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
STATE=AI_ROOT/'.workbench'/'accounts'

def load(path):
    with path.open('rb') as f: return tomllib.load(f)
def project(): return load(AI_ROOT/'project.toml')
def accounts(): return load(AI_ROOT/'config'/'accounts.toml')
def coder(agent):
    for d in project().get('agents',{}).get('coders',[]):
        if d.get('id')==agent: return d
    raise SystemExit(f'Unknown coder {agent}')
def pools(): return {x['id']:x for x in accounts().get('pools',[])}
def profiles(): return {x['id']:x for x in accounts().get('profiles',[])}
def state_path(agent): return STATE/f'{agent}.json'
def read_state(agent):
    p=state_path(agent)
    if not p.exists(): return {'selected':None,'exhausted':[]}
    try: return json.loads(p.read_text())
    except Exception: return {'selected':None,'exhausted':[]}
def write_state(agent,s):
    STATE.mkdir(parents=True,exist_ok=True); state_path(agent).write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
def eligible(agent):
    d=coder(agent); pool_id=d.get('account_pool')
    if not pool_id: return []
    pool=pools().get(pool_id)
    if not pool: raise SystemExit(f'Unknown account pool {pool_id}')
    if pool.get('backend') != d.get('backend'): raise SystemExit(f'Pool/backend mismatch for {agent}')
    pr=profiles(); return [pr[x] for x in pool.get('profiles',[]) if x in pr and pr[x].get('enabled',True)]
def choose(agent):
    s=read_state(agent); cand=eligible(agent); exhausted=set(s.get('exhausted',[])); ids=[x['id'] for x in cand]
    if s.get('selected') in ids and s.get('selected') not in exhausted: return next(x for x in cand if x['id']==s['selected'])
    for x in cand:
        if x['id'] not in exhausted:
            s['selected']=x['id']; write_state(agent,s); return x
    return None

def mark(agent,profile):
    s=read_state(agent); ex=set(s.get('exhausted',[])); ex.add(profile); s['exhausted']=sorted(ex)
    if s.get('selected')==profile: s['selected']=None
    write_state(agent,s)

def select(agent,profile):
    ids={x['id'] for x in eligible(agent)}
    if profile not in ids: raise SystemExit(f'{profile} is not in the configured pool for {agent}')
    s=read_state(agent); s['selected']=profile; s['exhausted']=[x for x in s.get('exhausted',[]) if x!=profile]; write_state(agent,s)

def reset(agent): write_state(agent,{'selected':None,'exhausted':[]})

ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
for n in ['list','status']: sub.add_parser(n)
q=sub.add_parser('login-hint'); q.add_argument('profile')
q=sub.add_parser('current'); q.add_argument('agent')
q=sub.add_parser('select'); q.add_argument('agent'); q.add_argument('profile')
q=sub.add_parser('mark-exhausted'); q.add_argument('agent'); q.add_argument('profile',nargs='?')
q=sub.add_parser('reset'); q.add_argument('agent')
a=ap.parse_args()
if a.cmd=='list':
    pr=profiles()
    for pid,pool in pools().items():
        print(f"{pid}: backend={pool.get('backend')}")
        for x in pool.get('profiles',[]):
            p=pr.get(x,{})
            print(f"  - {x}: email={p.get('email_hint','-')} scope={p.get('account_scope','-')} workspace={p.get('workspace_hint','-')} strategy={p.get('auth_strategy','selector_only')} enabled={p.get('enabled',True)}")
elif a.cmd=='status':
    for d in project().get('agents',{}).get('coders',[]):
        p=choose(d['id']); s=read_state(d['id'])
        email=(p or {}).get('email_hint','-')
        strategy=(p or {}).get('auth_strategy','-')
        print(f"{d['id']}: backend={d.get('backend')} pool={d.get('account_pool','none')} current={(p or {}).get('id','none')} email={email} strategy={strategy} exhausted={','.join(s.get('exhausted',[])) or '-'}")
elif a.cmd=='login-hint':
    p=profiles().get(a.profile)
    if not p: raise SystemExit(f'Unknown profile {a.profile}')
    print(f"profile: {p['id']}")
    print(f"backend: {p.get('backend','-')}")
    print(f"email_hint: {p.get('email_hint','-')}")
    if p.get('account_scope'): print(f"account_scope: {p['account_scope']}")
    if p.get('workspace_hint'): print(f"workspace_hint: {p['workspace_hint']}")
    print(f"auth_strategy: {p.get('auth_strategy','selector_only')}")
    if p.get('auth_context'): print(f"auth_context: {p['auth_context']}")
    if p.get('launcher'): print(f"launcher: {p['launcher']}")
    print(f"login: {p.get('login_hint','No login hint configured; use the provider-supported interactive login flow.')}")
elif a.cmd=='current':
    p=choose(a.agent)
    if not p: raise SystemExit(2)
    print(json.dumps(p))
elif a.cmd=='select': select(a.agent,a.profile); print(a.profile)
elif a.cmd=='mark-exhausted':
    p=a.profile or (choose(a.agent) or {}).get('id')
    if not p: raise SystemExit('No current profile')
    mark(a.agent,p); nxt=choose(a.agent); print(f"marked {p} exhausted; next={(nxt or {}).get('id','none')}")
elif a.cmd=='reset': reset(a.agent); print(f'reset {a.agent}')
