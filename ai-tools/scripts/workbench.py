#!/usr/bin/env python3
from __future__ import annotations
import argparse, fcntl, hashlib, json, os, re, shutil, subprocess, sys, tempfile, tomllib
from datetime import datetime
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
ROOT = AI_ROOT.parent
RESEARCH = AI_ROOT / "research"
WORKSPACES = AI_ROOT / "workspaces"
EXPERIMENTS = WORKSPACES / "experiments"
PROTOTYPES = WORKSPACES / "prototypes"
STUDIES = RESEARCH / "studies"
ATTEMPTS = RESEARCH / "attempts"
STAGES = RESEARCH / "stages"
ASSIGNMENTS = RESEARCH / "assignments"
COMPETITIONS = RESEARCH / "competitions"
REUSE = RESEARCH / "reuse"
STATE = AI_ROOT / ".workbench"
DISPOSITIONS = {"undecided", "record_only", "preserve_prototype", "promotion_candidate", "promoted"}
STUDY_STATES = {"backlog", "active", "blocked", "validated", "falsified", "inconclusive", "superseded", "outcompeted", "nonviable"}
ATTEMPT_STATES = {"backlog", "active", "blocked", "stopped", "outperformed", "nonviable"}
STAGE_STATES = {"planning", "active", "review", "complete", "paused"}


def load_toml(p: Path):
    with p.open("rb") as f:
        return tomllib.load(f)

def cfg(): return load_toml(AI_ROOT / "project.toml")
def backend_cfg(): return load_toml(AI_ROOT / "config" / "backends.toml")
def runtime_cfg(): return load_toml(AI_ROOT / "config" / "runtime.toml")
def account_cfg():
    p = AI_ROOT / "config" / "accounts.toml"
    return load_toml(p) if p.exists() else {"policy": {}, "pools": [], "profiles": []}
def now(): return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f: f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def coder_defs(): return cfg().get("agents", {}).get("coders", [])
def coder_ids(): return [x["id"] for x in coder_defs()]
def coder_def(agent):
    for d in coder_defs():
        if d.get("id") == agent: return d
    raise SystemExit(f"Unknown coder {agent!r}; configured: {', '.join(coder_ids())}")
def backend_ids(): return sorted(backend_cfg().get("backends", {}).keys())

def account_state(agent):
    p=STATE/"accounts"/f"{agent}.json"
    if not p.exists(): return {"selected": None, "exhausted": []}
    try: return json.loads(p.read_text())
    except Exception: return {"selected": None, "exhausted": []}

def displayed_account_profile(agent):
    st=account_state(agent)
    d=coder_def(agent); pool_id=d.get("account_pool")
    ac=account_cfg(); pools={x.get("id"):x for x in ac.get("pools",[])}; profs={x.get("id"):x for x in ac.get("profiles",[])}
    def label(pid):
        p=profs.get(pid,{})
        bits=[]
        if p.get("email_hint"): bits.append(str(p["email_hint"]))
        if p.get("account_scope"): bits.append(str(p["account_scope"]))
        if p.get("workspace_hint"): bits.append(str(p["workspace_hint"]))
        return f"{pid} ({'; '.join(bits)})" if bits else pid
    if st.get("selected"):
        return label(st["selected"])
    pool=pools.get(pool_id,{})
    exhausted=set(st.get("exhausted",[]))
    for pid in pool.get("profiles",[]):
        if pid not in exhausted and profs.get(pid,{}).get("enabled",True):
            return f"auto:{label(pid)}"
    return "none"


def all_studies():
    out = []
    for st in sorted(STUDIES.glob("STUDY-*")):
        p = st / "status.toml"
        if p.exists(): out.append((st, load_toml(p)))
    return out

def study_record(sid):
    p = STUDIES / sid / "status.toml"
    if not p.exists(): raise SystemExit(f"Unknown study {sid}")
    return STUDIES / sid, load_toml(p)

def all_attempts():
    out = []
    if not ATTEMPTS.exists(): return out
    for at in sorted(ATTEMPTS.glob("ATTEMPT-*")):
        p = at / "status.toml"
        if p.exists(): out.append((at, load_toml(p)))
    return out

def attempts_for_study(sid): return [(p, d) for p, d in all_attempts() if d.get("study") == sid]
def all_stages():
    out=[]
    for st in sorted(STAGES.glob("STAGE-*")):
        p=st/"stage.toml"
        if p.exists(): out.append((st,load_toml(p)))
    return out

def competition_records():
    out=[]
    for p in sorted(COMPETITIONS.glob("COMP-*/competition.toml")) if COMPETITIONS.exists() else []:
        try: out.append((p.parent,load_toml(p)))
        except Exception: pass
    return out


def terminals(): return set(cfg()["workflow"]["terminal_study_states"])
def attempt_terminals(): return set(cfg()["workflow"].get("terminal_attempt_states", ["stopped", "outperformed", "nonviable"]))
def study_nonterminal(s): return s.get("status") not in terminals()
def attempt_nonterminal(a): return a.get("status") not in attempt_terminals()
def nonterminal(items=None):
    items=all_studies() if items is None else items
    return [(p,d) for p,d in items if study_nonterminal(d)]
def actionable(items=None): return [(p,d) for p,d in nonterminal(items) if d.get("status") != "blocked"]


def assigned_attempts(agent):
    coder_def(agent)
    return [(p,d) for p,d in all_attempts() if d.get("owner") == agent]
def open_attempts(agent):
    out=[]
    for p,a in assigned_attempts(agent):
        try: _,s=study_record(a.get("study"))
        except SystemExit: continue
        if attempt_nonterminal(a) and study_nonterminal(s): out.append((p,a))
    return out
def actionable_attempts(agent): return [(p,a) for p,a in open_attempts(agent) if a.get("status") != "blocked"]

def legacy_assigned(agent):
    """Backward-compatible single-owner studies with no ATTEMPT records."""
    coder_def(agent); out=[]
    for p,d in all_studies():
        if d.get("owner") == agent and not attempts_for_study(d.get("id")):
            out.append((p,d))
    return out

def legacy_nonterminal(agent): return nonterminal(legacy_assigned(agent))
def legacy_actionable(agent): return actionable(legacy_assigned(agent))

def agent_studies(agent, only_nonterminal=False):
    wanted=[]; seen=set()
    for _,a in assigned_attempts(agent):
        sid=a.get("study")
        if sid and sid not in seen:
            try: rec=study_record(sid)
            except SystemExit: continue
            if not only_nonterminal or study_nonterminal(rec[1]): wanted.append(rec)
            seen.add(sid)
    for rec in legacy_assigned(agent):
        sid=rec[1].get("id")
        if sid not in seen and (not only_nonterminal or study_nonterminal(rec[1])):
            wanted.append(rec); seen.add(sid)
    return wanted

def agent_has_open(agent): return bool(open_attempts(agent) or legacy_nonterminal(agent))
def agent_has_actionable(agent): return bool(actionable_attempts(agent) or legacy_actionable(agent))


def append_log(actor, study, kind, message):
    msg=" ".join(message.strip().splitlines()); p=RESEARCH/"LOG.md"; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a") as f:
        fcntl.flock(f.fileno(),fcntl.LOCK_EX); f.write(f"- {now()} | actor={actor} | study={study or '-'} | kind={kind} | {msg}\n"); f.flush(); os.fsync(f.fileno()); fcntl.flock(f.fileno(),fcntl.LOCK_UN)


def replace_top_field(path: Path, field: str, value):
    s=path.read_text(); encoded=json.dumps(value)
    pat=rf'(?m)^{re.escape(field)}\s*=\s*.*$'; repl=f'{field} = {encoded}'
    if re.search(pat,s): s=re.sub(pat,repl,s,count=1)
    else:
        m=re.search(r'(?m)^updated\s*=.*$',s)
        if m: s=s[:m.end()]+"\n"+repl+s[m.end():]
        else: s=repl+"\n"+s
    if field != "updated" and re.search(r'(?m)^updated\s*=',s):
        s=re.sub(r'(?m)^updated\s*=.*$',f'updated = {json.dumps(now())}',s,count=1)
    atomic_write(path,s)


def study_path(sid):
    p=STUDIES/sid/"status.toml"
    if not p.exists(): raise SystemExit(f"Unknown study {sid}")
    return p

def attempt_path(aid):
    p=ATTEMPTS/aid/"status.toml"
    if not p.exists(): raise SystemExit(f"Unknown attempt {aid}")
    return p

def stage_path(stage):
    p=STAGES/stage/"stage.toml"
    if not p.exists(): raise SystemExit(f"Unknown stage {stage}")
    return p


def render_assignment(agent):
    d=coder_def(agent); ats=sorted(assigned_attempts(agent),key=lambda x:x[1].get("id","")); legacy=sorted(legacy_assigned(agent),key=lambda x:(x[1].get("priority",999),x[1].get("id","")))
    lines=[f"# Assignment — {agent}","",f"**Role:** {d.get('label',agent)}",f"**Backend:** `{d.get('backend','custom')}`",f"**Account pool:** `{d.get('account_pool','none')}`",f"**Current credential:** `{displayed_account_profile(agent)}`","","## Mission","","Drive every assigned attempt/study until the parent study reaches a configured terminal scientific state or the advisor/human explicitly stops/outperforms/nonviables that attempt. Intermediate milestones are not completion.","","## Assigned attempts",""]
    if ats:
        for _,a in ats:
            _,s=study_record(a.get("study")); lines.append(f"- `{a.get('id')}` — attempt **{a.get('status')}** — study `{s.get('id')}` **{s.get('status')}** — track `{a.get('track',s.get('track','?'))}` — {a.get('label','')} — flavor: {a.get('flavor','')} — workspace `{a.get('experiment_dir','')}`")
    else: lines.append("- No explicit attempts assigned.")
    if legacy:
        lines += ["","## Legacy single-owner studies",""]
        for _,s in legacy: lines.append(f"- `{s.get('id')}` — **{s.get('status')}** — {s.get('title','')}")
    lines += ["","## Start / resume protocol","","1. Read `ai-tools/config/runtime.toml`; use its shared environment and named commands.","2. Read `ai-tools/agents/CODER.md`, `ai-tools/research/program.toml`, and the technical note/development plan for the parent stage.","3. Read your attempt record(s), parent study, linked competition, reuse registry, and `ai-tools/research/advice/LATEST.md`.","4. Work only in your attempt workspace unless an advisor/human explicitly promotes shared code.","5. Execute the next discriminating experiment, record evidence, and continue toward the parent study's terminal criteria.","6. Do not stop at a prototype, passing test, partial speedup, or temporary lead/loss.","7. Never delete failed code/history. Advisor/human decide retention/promotion.",""]
    text="\n".join(lines); atomic_write(ASSIGNMENTS/f"{agent}.md",text); return text


def render_status():
    c=cfg(); rows=sorted(all_studies(),key=lambda x:(x[1].get("priority",999),x[1].get("id",""))); nt=nonterminal(); blocked=[x for x in nt if x[1].get("status")=="blocked"]
    lines=["# Research status","",f"**Project:** {c['project']['name']}",f"**Updated:** {now()}",f"**Studies:** {len(rows)} total · {len(nt)} nonterminal · {len(blocked)} blocked",f"**Attempts:** {len(all_attempts())} total","","## Stages","","| Stage | Status | Base ref | Goal |","|---|---|---|---|"]
    for _,s in all_stages(): lines.append(f"| `{s.get('id')}` | **{s.get('status')}** | `{s.get('base_ref','')}` | {s.get('goal',{}).get('statement','')} |")
    lines += ["","## Agent portfolio","","| Agent | Backend | Account pool | Credential profile | Open attempts | Actionable | Assignment |","|---|---|---|---|---:|---:|---|"]
    for agent in coder_ids():
        d=coder_def(agent); oa=open_attempts(agent); aa=actionable_attempts(agent); lines.append(f"| `{agent}` | `{d.get('backend','custom')}` | `{d.get('account_pool','none')}` | `{displayed_account_profile(agent)}` | {len(oa)} | {len(aa)} | `ai-tools/research/assignments/{agent}.md` |"); render_assignment(agent)
    lines += ["","## Attempts / replicas","","| Attempt | Study | Track | Agent | State | Flavor | Workspace |","|---|---|---|---|---|---|---|"]
    for _,a in all_attempts():
        lines.append(f"| `{a.get('id')}` | `{a.get('study')}` | `{a.get('track','')}` | `{a.get('owner')}` | **{a.get('status')}** | {a.get('flavor','')} | `{a.get('experiment_dir','')}` |")
    lines += ["","## Studies","","| P | Study | Stage | Scientific state | Artifact disposition | Competition / track | Replicas | Title |","|---:|---|---|---|---|---|---|---|"]
    for _,d in rows:
        comp=f"{d.get('competition','')} / {d.get('track','')}" if d.get('competition') or d.get('track') else ""
        disp=d.get('artifact_disposition','undecided'); rec=d.get('disposition_recommended','undecided')
        if rec != 'undecided' and rec != disp: disp += f" (advisor→{rec})"
        reps=", ".join(a.get('id') for _,a in attempts_for_study(d.get('id'))) or d.get('owner','unassigned')
        lines.append(f"| {d.get('priority','')} | {d.get('id','?')} | `{d.get('stage','?')}` | **{d.get('status','?')}** | `{disp}` | {comp} | {reps} | {d.get('title','')} |")
    comps=competition_records()
    if comps:
        lines += ["","## Competitions",""]
        for cp,d in comps:
            lines += [f"### {d.get('id',cp.name)} — {d.get('title','')}","",f"Stage: `{d.get('stage','?')}` · Status: **{d.get('status','?')}**",""]
            for t in d.get("tracks",[]):
                reps=[a.get('id')+":"+a.get('owner','?') for _,a in attempts_for_study(t.get('study')) if a.get('track')==t.get('id')]
                lines.append(f"- `{t.get('id')}` → `{t.get('study')}` — {t.get('label','')} — replicas: {', '.join(reps) or 'none'}")
    lines += ["","## Next by coder",""]
    for agent in coder_ids():
        aa=actionable_attempts(agent); legacy=legacy_actionable(agent)
        if aa:
            a=aa[0][1]; _,s=study_record(a.get('study')); lines.append(f"- `{agent}`: `{a.get('id')}` on **{s.get('id')} — {s.get('title')}** (attempt `{a.get('status')}`, study `{s.get('status')}`).")
        elif legacy:
            s=legacy[0][1]; lines.append(f"- `{agent}`: legacy **{s.get('id')} — {s.get('title')}** (`{s.get('status')}`).")
        elif agent_has_open(agent): lines.append(f"- `{agent}`: all open work blocked; advisor resolution required.")
        else: lines.append(f"- `{agent}`: assignment terminal / empty.")
    lines += ["","## Latest advisor note",""]
    latest=RESEARCH/"advice"/"LATEST.md"
    if latest.exists(): lines += [x for x in latest.read_text().splitlines() if x.strip()][:14] or ["No advisor note."]
    lines += ["","## Recent log",""]
    lp=RESEARCH/"LOG.md"; logs=[x for x in lp.read_text().splitlines() if x.startswith("- ")][-14:] if lp.exists() else []; lines += logs or ["No log entries."]
    text="\n".join(lines)+"\n"; atomic_write(RESEARCH/"STATUS.md",text); return text


def stage_material(stage_ids):
    out=[]
    for sid in sorted(set(x for x in stage_ids if x)):
        d=STAGES/sid
        for name in ["stage.toml","technical_note.md","development_plan.md"]:
            p=d/name
            if p.exists(): out.append(f"\n## ai-tools/research/stages/{sid}/{name}\n{p.read_text()}")
    return "".join(out)

def study_material(items, attempt_items=None):
    material=[]; comps=set(); stages=[]
    for st,d in sorted(items,key=lambda x:(x[1].get("priority",999),x[1].get("id",""))):
        stages.append(d.get("stage"))
        for name in ["status.toml","idea.md","plan.md","runs.toml","verdict.md"]:
            q=st/name
            if q.exists(): material.append(f"\n## {st.name}/{name}\n{q.read_text()}")
        comp=d.get("competition")
        if comp and comp not in comps:
            cp=COMPETITIONS/comp
            for name in ["competition.toml","RESULTS.md"]:
                q=cp/name
                if q.exists(): material.append(f"\n## ai-tools/research/competitions/{comp}/{name}\n{q.read_text()}")
            comps.add(comp)
    if attempt_items is not None:
        for at,a in attempt_items:
            q=at/"status.toml"
            if q.exists(): material.append(f"\n## ai-tools/research/attempts/{at.name}/status.toml\n{q.read_text()}")
            exp=ROOT/a.get("experiment_dir","")
            readme=exp/"README.md"
            if readme.exists(): material.append(f"\n## {readme.relative_to(ROOT)}\n{readme.read_text()}")
    return stage_material(stages)+"".join(material)


def role_prompt(role,agent=None):
    render_status(); common=(AI_ROOT/"docs"/"AGENTS.md").read_text(); program=(RESEARCH/"program.toml").read_text(); status=(RESEARCH/"STATUS.md").read_text(); runtime=(AI_ROOT/"config"/"runtime.toml").read_text(); reuse=(REUSE/"components.toml").read_text() if (REUSE/"components.toml").exists() else ""; latest=(RESEARCH/"advice"/"LATEST.md").read_text() if (RESEARCH/"advice"/"LATEST.md").exists() else ""
    if role=="coder":
        if not agent: raise SystemExit("coder prompt requires --agent")
        d=coder_def(agent); assignment=render_assignment(agent); role_doc=(AI_ROOT/"agents"/"CODER.md").read_text(); candidates=agent_studies(agent,only_nonterminal=True); ats=assigned_attempts(agent); inst=f"You are {agent} using backend {d.get('backend','custom')}. Work on your assigned replica(s) now. Preserve the declared flavor and workspace isolation. Continue until the parent study is terminal or advisor/human explicitly terminates the attempt."
        identity=f"# Runtime role: coder\n# Agent id: {agent}\n# Backend: {d.get('backend','custom')}\n# Account pool: {d.get('account_pool','none')}\n\n# Explicit assignment\n{assignment}"
    else:
        role_doc=(AI_ROOT/"agents"/"ADVISOR.md").read_text(); candidates=nonterminal(); ats=all_attempts(); inst="Review the whole portfolio now. Compare replicas within each track before comparing tracks; resolve blockers; prescribe next actions; and separately recommend scientific state and artifact retention."
        identity="# Runtime role: advisor / coordinator"
    accounts=(AI_ROOT/"config"/"accounts.toml").read_text() if (AI_ROOT/"config"/"accounts.toml").exists() else ""
    return "\n\n".join([identity,common,role_doc,"# Runtime/tool contract\n"+runtime,"# Non-secret account-pool contract\n"+accounts,"# Program\n"+program,"# Dashboard\n"+status,"# Reusable component registry\n"+reuse,"# Latest advisor note\n"+latest,"# Stage / study / competition / assigned-attempt material\n"+study_material(candidates,ats),"# Current instruction\n"+inst])


def next_numeric(prefix, dirs):
    nums=[]
    for p in dirs:
        m=re.fullmatch(rf"{prefix}-(\d+)",p.name)
        if m: nums.append(int(m.group(1)))
    return f"{prefix}-{max(nums,default=0)+1:04d}"
def git_ref():
    try: return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception: return "UNCOMMITTED"


def new_stage(title,goal,tech=None,plan=None):
    sid=next_numeric("STAGE",STAGES.glob("STAGE-*")); d=STAGES/sid; d.mkdir(parents=True); stamp=now(); base=git_ref()
    (d/"stage.toml").write_text(f'''schema_version = 1\nid = "{sid}"\ntitle = {json.dumps(title)}\nstatus = "planning"\ncreated = {json.dumps(stamp)}\nupdated = {json.dumps(stamp)}\nbase_ref = {json.dumps(base)}\ninherits = []\n\n[goal]\nstatement = {json.dumps(goal)}\n\n[inputs]\ntechnical_note = "ai-tools/research/stages/{sid}/technical_note.md"\ndevelopment_plan = "ai-tools/research/stages/{sid}/development_plan.md"\n\n[software]\nstable_base = "src/"\nreusable_prototypes = "ai-tools/workspaces/prototypes/"\n''')
    if tech: shutil.copyfile(tech,d/"technical_note.md")
    else: (d/"technical_note.md").write_text(f"# {sid} — Technical note\n\n{goal}\n\n## Formulation\n\nREPLACE.\n\n## Interfaces to existing software\n\nREPLACE.\n")
    if plan: shutil.copyfile(plan,d/"development_plan.md")
    else: (d/"development_plan.md").write_text(f"# {sid} — Development plan\n\n## Objective\n\n{goal}\n\n## Candidate approaches\n\nREPLACE.\n\n## Validation / exit criteria\n\nREPLACE.\n")
    append_log("human","-","stage",f"Created {sid}: {title}; base_ref={base}"); render_status(); return sid


def new_study(title,hypothesis,priority,owner,competition=None,track=None,stage="STAGE-0001"):
    if owner not in {"unassigned","shared"}: coder_def(owner)
    stage_path(stage); sid=next_numeric("STUDY",STUDIES.glob("STUDY-*")); d=STUDIES/sid; d.mkdir(parents=True); stamp=now(); extras=""
    if competition: extras+=f"competition = {json.dumps(competition)}\n"
    if track: extras+=f"track = {json.dumps(track)}\n"
    (d/"status.toml").write_text(f'''schema_version = 4\nid = "{sid}"\ntitle = {json.dumps(title)}\nstatus = "backlog"\npriority = {priority}\nowner = {json.dumps(owner)}\ncreated = {json.dumps(stamp)}\nupdated = {json.dumps(stamp)}\nstage = {json.dumps(stage)}\nartifact_disposition = "undecided"\ndisposition_recommended = "undecided"\ndisposition_approved_by = ""\ndisposition_reason = ""\n{extras}\n[hypothesis]\nstatement = {json.dumps(hypothesis)}\n\n[decision_rule]\nvalidate_when = ["REPLACE: concrete acceptance criterion"]\nfalsify_when = ["REPLACE: concrete rejection criterion"]\n\n[links]\nexperiment_dir = "ai-tools/workspaces/experiments/{sid}"\n''')
    (d/"idea.md").write_text(f"# {sid} — Idea\n\n{hypothesis}\n"); (d/"plan.md").write_text(f"# {sid} — Plan\n\n## Next decisive experiment\n\nDefine it here.\n"); (d/"runs.toml").write_text("schema_version = 1\n"); (d/"verdict.md").write_text(f"# {sid} — Verdict\n\nStatus: **not yet terminal**\n")
    e=EXPERIMENTS/sid; e.mkdir(parents=True); (e/"README.md").write_text(f"# Experimental workspace for {sid}\n\nUse per-attempt subdirectories when multiple coding agents work on this study.\n")
    append_log("human",sid,"plan",f"Created study: {title}; stage={stage}; owner={owner}"); render_status(); return sid


def new_attempt(study,owner,flavor,label=None,track=None,status="active"):
    coder_def(owner); st,sd=study_record(study)
    if status not in ATTEMPT_STATES: raise SystemExit("invalid attempt status")
    track=track or sd.get("track","")
    aid=next_numeric("ATTEMPT",ATTEMPTS.glob("ATTEMPT-*")); d=ATTEMPTS/aid; d.mkdir(parents=True); stamp=now(); exp=EXPERIMENTS/study/aid; exp.mkdir(parents=True,exist_ok=True)
    label=label or f"Replica {aid}"
    (d/"status.toml").write_text(f'''schema_version = 1\nid = "{aid}"\nstudy = {json.dumps(study)}\ntrack = {json.dumps(track)}\nowner = {json.dumps(owner)}\nstatus = {json.dumps(status)}\ncreated = {json.dumps(stamp)}\nupdated = {json.dumps(stamp)}\nlabel = {json.dumps(label)}\nflavor = {json.dumps(flavor)}\nindependent_implementation = true\nexperiment_dir = {json.dumps(str(exp.relative_to(ROOT)))}\n''')
    (exp/"README.md").write_text(f"# Experimental workspace for {aid}\n\nParent study: `{study}`  \nOwner: `{owner}`\n\nFlavor: {flavor}\n\nDo not write into another replica's workspace.\n")
    if sd.get("owner") not in {"shared","unassigned"}: replace_top_field(st/"status.toml","owner","shared")
    elif sd.get("owner")=="unassigned": replace_top_field(st/"status.toml","owner","shared")
    append_log("human",study,"assignment",f"Created {aid}; owner={owner}; track={track}; flavor={flavor}"); render_status(); return aid


def assign_study(sid,agent):
    coder_def(agent); p=study_path(sid); old=load_toml(p).get("owner","unassigned")
    if attempts_for_study(sid): raise SystemExit(f"{sid} has explicit attempts; reassign an attempt instead of the shared study")
    replace_top_field(p,"owner",agent); append_log("human",sid,"assignment",f"owner {old} -> {agent}"); render_status()
def assign_attempt(aid,agent):
    coder_def(agent); p=attempt_path(aid); d=load_toml(p); old=d.get("owner"); replace_top_field(p,"owner",agent); append_log("human",d.get("study","-"),"assignment",f"{aid} owner {old} -> {agent}"); render_status()


def set_backend(agent,backend):
    coder_def(agent)
    if backend not in backend_ids(): raise SystemExit(f"Unknown backend {backend}; available: {', '.join(backend_ids())}")
    _replace_coder_field(agent,"backend",backend); append_log("human","-","assignment",f"backend {agent} -> {backend}"); render_status()
def _replace_coder_field(agent,field,value):
    p=AI_ROOT/"project.toml"; s=p.read_text(); blocks=re.split(r'(?=\[\[agents\.coders\]\])',s); changed=False
    for i,b in enumerate(blocks):
        if b.startswith("[[agents.coders]]") and re.search(rf'(?m)^id\s*=\s*{re.escape(json.dumps(agent))}\s*$',b):
            if re.search(rf'(?m)^{re.escape(field)}\s*=',b): b=re.sub(rf'(?m)^{re.escape(field)}\s*=.*$',f'{field} = {json.dumps(value)}',b,count=1)
            else: b=b.replace(f'id = {json.dumps(agent)}',f'id = {json.dumps(agent)}\n{field} = {json.dumps(value)}',1)
            blocks[i]=b; changed=True; break
    if not changed: raise SystemExit(f"Could not update {field} for {agent}")
    atomic_write(p,"".join(blocks))
def set_account_pool(agent,pool):
    coder_def(agent); pools={x.get("id"):x for x in account_cfg().get("pools",[])}
    if pool not in pools: raise SystemExit(f"Unknown account pool {pool}")
    _replace_coder_field(agent,"account_pool",pool); append_log("human","-","assignment",f"account pool {agent} -> {pool}"); render_status()


def set_disposition(sid,disposition,actor,reason):
    if disposition not in DISPOSITIONS-{"undecided"}: raise SystemExit("invalid disposition")
    p=study_path(sid)
    if actor=="advisor": replace_top_field(p,"disposition_recommended",disposition); append_log(actor,sid,"retention",f"recommend {disposition}: {reason}")
    elif actor=="human": replace_top_field(p,"artifact_disposition",disposition); replace_top_field(p,"disposition_approved_by","human"); replace_top_field(p,"disposition_reason",reason); append_log(actor,sid,"retention",f"approved {disposition}: {reason}")
    else: raise SystemExit("disposition actor must be advisor or human")
    render_status()

def register_reuse(sid,name,path,capability,limitations):
    d=load_toml(study_path(sid)); disp=d.get("artifact_disposition","undecided")
    if disp not in {"preserve_prototype","promotion_candidate","promoted"}: raise SystemExit(f"{sid} disposition={disp}; human must approve reusable disposition first")
    p=REUSE/"components.toml"; block=f'''\n[[components]]\nid = {json.dumps(name)}\nsource_study = {json.dumps(sid)}\nstage = {json.dumps(d.get('stage',''))}\npath = {json.dumps(path)}\ndisposition = {json.dumps(disp)}\ncapability = {json.dumps(capability)}\nlimitations = {json.dumps(limitations)}\nregistered = {json.dumps(now())}\n'''
    with p.open("a") as f: f.write(block)
    append_log("human",sid,"retention",f"registered reusable component {name} at {path}"); render_status()


def digest():
    h=hashlib.sha256(); paths=[RESEARCH/"LOG.md",REUSE/"components.toml"]
    for st,_ in all_studies(): paths.extend([st/"status.toml",st/"runs.toml"])
    for at,_ in all_attempts(): paths.append(at/"status.toml")
    for st,_ in all_stages(): paths.extend([st/"stage.toml",st/"technical_note.md",st/"development_plan.md"])
    for cp,_ in competition_records(): paths.extend([cp/"competition.toml",cp/"RESULTS.md"])
    for p in paths:
        if p.exists(): h.update(str(p.relative_to(ROOT)).encode()); h.update(p.read_bytes())
    return h.hexdigest()
def advisor_needed():
    p=STATE/"advisor_state.json"
    if not p.exists(): return True
    try: old=json.loads(p.read_text())
    except Exception: return True
    return old.get("digest") != digest()
def mark_reviewed(): STATE.mkdir(exist_ok=True); atomic_write(STATE/"advisor_state.json",json.dumps({"digest":digest(),"at":now()},indent=2))


def validate():
    errs=[]; c=cfg(); ids=coder_ids(); stages={d.get('id') for _,d in all_stages()}; backs=set(backend_ids()); ac=account_cfg(); pools={x.get('id'):x for x in ac.get('pools',[])}; profiles={x.get('id'):x for x in ac.get('profiles',[])}
    if c["project"]["name"]=="CHANGE_ME": errs.append("ai-tools/project.toml: project.name still CHANGE_ME")
    if len(ids)!=len(set(ids)): errs.append("ai-tools/project.toml: duplicate coder ids")
    for d in coder_defs():
        if d.get("backend") not in backs: errs.append(f"{d.get('id')}: unknown backend {d.get('backend')}")
        pool=d.get("account_pool")
        if pool:
            if pool not in pools: errs.append(f"{d.get('id')}: unknown account pool {pool}")
            elif pools[pool].get("backend") != d.get("backend"): errs.append(f"{d.get('id')}: account pool {pool} backend mismatch")
    for pid,pool in pools.items():
        for prof in pool.get("profiles",[]):
            if prof not in profiles: errs.append(f"account pool {pid}: missing profile {prof}")
            elif profiles[prof].get("backend") != pool.get("backend"): errs.append(f"account pool {pid}: profile {prof} backend mismatch")
    for st,d in all_studies():
        if d.get("id")!=st.name: errs.append(f"{st.name}: id mismatch")
        if d.get("status") not in STUDY_STATES: errs.append(f"{st.name}: invalid status")
        if d.get("owner") not in ids+["unassigned","shared"]: errs.append(f"{st.name}: unknown owner {d.get('owner')}")
        if d.get("stage") not in stages: errs.append(f"{st.name}: unknown stage {d.get('stage')}")
        if d.get("artifact_disposition","undecided") not in DISPOSITIONS: errs.append(f"{st.name}: invalid artifact disposition")
        if d.get("disposition_recommended","undecided") not in DISPOSITIONS: errs.append(f"{st.name}: invalid advisor disposition recommendation")
        for name in ["idea.md","plan.md","runs.toml","verdict.md"]:
            if not (st/name).exists(): errs.append(f"{st.name}: missing {name}")
    for at,a in all_attempts():
        if a.get("id") != at.name: errs.append(f"{at.name}: attempt id mismatch")
        if a.get("owner") not in ids: errs.append(f"{at.name}: unknown owner {a.get('owner')}")
        if a.get("status") not in ATTEMPT_STATES: errs.append(f"{at.name}: invalid attempt status")
        sp=STUDIES/str(a.get("study"))/"status.toml"
        if not sp.exists(): errs.append(f"{at.name}: missing study {a.get('study')}")
        else:
            sd=load_toml(sp)
            if sd.get("track") and a.get("track") != sd.get("track"): errs.append(f"{at.name}: track mismatch with {a.get('study')}")
        exp=ROOT/str(a.get("experiment_dir",""))
        if not exp.is_dir(): errs.append(f"{at.name}: missing experiment_dir {a.get('experiment_dir')}")
    for st,d in all_stages():
        if d.get("id")!=st.name: errs.append(f"{st.name}: stage id mismatch")
        if d.get("status") not in STAGE_STATES: errs.append(f"{st.name}: invalid stage status")
        for name in ["technical_note.md","development_plan.md"]:
            if not (st/name).exists(): errs.append(f"{st.name}: missing {name}")
    for cp,d in competition_records():
        if d.get("stage") not in stages: errs.append(f"{cp.name}: unknown stage {d.get('stage')}")
        track_ids=set()
        for t in d.get("tracks",[]):
            sid=t.get("study"); track_ids.add(t.get("id")); sp=STUDIES/str(sid)/"status.toml"
            if not sp.exists(): errs.append(f"{cp.name}: missing track study {sid}")
            else:
                sd=load_toml(sp)
                if sd.get("competition")!=d.get("id") or sd.get("track")!=t.get("id"): errs.append(f"{cp.name}: study linkage mismatch for {sid}")
        for _,a in all_attempts():
            if a.get("study") in {t.get("study") for t in d.get("tracks",[])} and a.get("track") not in track_ids: errs.append(f"{cp.name}: attempt {a.get('id')} points to unknown track {a.get('track')}")
    if not (AI_ROOT/"config"/"runtime.toml").exists(): errs.append("missing ai-tools/config/runtime.toml")
    if not (AI_ROOT/"config"/"accounts.toml").exists(): errs.append("missing ai-tools/config/accounts.toml")
    return errs


p=argparse.ArgumentParser(); sp=p.add_subparsers(dest="cmd",required=True)
for name in ["status","has-open","advisor-needed","advisor-current","mark-advisor-reviewed","validate","list-agents","list-backends"]: sp.add_parser(name)
q=sp.add_parser("agent-has-open"); q.add_argument("agent")
q=sp.add_parser("agent-has-actionable"); q.add_argument("agent")
q=sp.add_parser("prompt"); q.add_argument("role",choices=["coder","advisor"]); q.add_argument("--agent")
q=sp.add_parser("assignment"); q.add_argument("agent")
q=sp.add_parser("log"); q.add_argument("--actor",required=True); q.add_argument("--study",default="-"); q.add_argument("--kind",required=True); q.add_argument("--message",required=True)
q=sp.add_parser("set-status"); q.add_argument("study"); q.add_argument("status",choices=sorted(STUDY_STATES)); q.add_argument("--reason",required=True); q.add_argument("--actor",default="human")
q=sp.add_parser("set-attempt-status"); q.add_argument("attempt"); q.add_argument("status",choices=sorted(ATTEMPT_STATES)); q.add_argument("--reason",required=True); q.add_argument("--actor",default="human")
q=sp.add_parser("assign"); q.add_argument("study"); q.add_argument("agent")
q=sp.add_parser("assign-attempt"); q.add_argument("attempt"); q.add_argument("agent")
q=sp.add_parser("set-backend"); q.add_argument("agent"); q.add_argument("backend")
q=sp.add_parser("set-account-pool"); q.add_argument("agent"); q.add_argument("pool")
q=sp.add_parser("disposition"); q.add_argument("study"); q.add_argument("disposition",choices=sorted(DISPOSITIONS-{"undecided"})); q.add_argument("--actor",choices=["advisor","human"],required=True); q.add_argument("--reason",required=True)
q=sp.add_parser("register-reuse"); q.add_argument("study"); q.add_argument("--name",required=True); q.add_argument("--path",required=True); q.add_argument("--capability",required=True); q.add_argument("--limitations",default="")
q=sp.add_parser("new-stage"); q.add_argument("--title",required=True); q.add_argument("--goal",required=True); q.add_argument("--tech"); q.add_argument("--plan")
q=sp.add_parser("set-stage-status"); q.add_argument("stage"); q.add_argument("status",choices=sorted(STAGE_STATES)); q.add_argument("--reason",required=True); q.add_argument("--actor",default="human")
q=sp.add_parser("new-study"); q.add_argument("--title",required=True); q.add_argument("--hypothesis",required=True); q.add_argument("--priority",type=int,default=10); q.add_argument("--owner",default="unassigned"); q.add_argument("--competition"); q.add_argument("--track"); q.add_argument("--stage",default="STAGE-0001")
q=sp.add_parser("new-attempt"); q.add_argument("--study",required=True); q.add_argument("--owner",required=True); q.add_argument("--flavor",required=True); q.add_argument("--label"); q.add_argument("--track"); q.add_argument("--status",default="active",choices=sorted(ATTEMPT_STATES))
a=p.parse_args()

if a.cmd=="status": print(render_status())
elif a.cmd=="has-open": render_status(); raise SystemExit(0 if nonterminal() else 1)
elif a.cmd=="agent-has-open": raise SystemExit(0 if agent_has_open(a.agent) else 1)
elif a.cmd=="agent-has-actionable": raise SystemExit(0 if agent_has_actionable(a.agent) else 1)
elif a.cmd=="advisor-needed": raise SystemExit(0 if advisor_needed() else 1)
elif a.cmd=="advisor-current": raise SystemExit(1 if advisor_needed() else 0)
elif a.cmd=="mark-advisor-reviewed": mark_reviewed()
elif a.cmd=="prompt": print(role_prompt(a.role,a.agent))
elif a.cmd=="assignment": print(render_assignment(a.agent))
elif a.cmd=="list-agents": print("\n".join(coder_ids()))
elif a.cmd=="list-backends": print("\n".join(backend_ids()))
elif a.cmd=="log":
    allowed=set(coder_ids())|{"advisor","human","system"}
    if a.actor not in allowed: raise SystemExit(f"Unknown actor {a.actor}")
    append_log(a.actor,a.study,a.kind,a.message); render_status()
elif a.cmd=="set-status":
    allowed=set(coder_ids())|{"advisor","human","system"}
    if a.actor not in allowed: raise SystemExit(f"Unknown actor {a.actor}")
    if a.status in {"outcompeted","nonviable"} and a.actor not in {"advisor","human","system"}: raise SystemExit(f"{a.status} requires advisor/human review")
    replace_top_field(study_path(a.study),"status",a.status); append_log(a.actor,a.study,"status",f"status -> {a.status}: {a.reason}"); render_status()
elif a.cmd=="set-attempt-status":
    allowed=set(coder_ids())|{"advisor","human","system"}
    if a.actor not in allowed: raise SystemExit(f"Unknown actor {a.actor}")
    if a.status in attempt_terminals() and a.actor not in {"advisor","human","system"}: raise SystemExit(f"terminal attempt state {a.status} requires advisor/human review")
    apath=attempt_path(a.attempt); ad=load_toml(apath); replace_top_field(apath,"status",a.status); append_log(a.actor,ad.get("study","-"),"attempt",f"{a.attempt} -> {a.status}: {a.reason}"); render_status()
elif a.cmd=="assign": assign_study(a.study,a.agent)
elif a.cmd=="assign-attempt": assign_attempt(a.attempt,a.agent)
elif a.cmd=="set-backend": set_backend(a.agent,a.backend)
elif a.cmd=="set-account-pool": set_account_pool(a.agent,a.pool)
elif a.cmd=="disposition": set_disposition(a.study,a.disposition,a.actor,a.reason)
elif a.cmd=="register-reuse": register_reuse(a.study,a.name,a.path,a.capability,a.limitations)
elif a.cmd=="new-stage": print(new_stage(a.title,a.goal,a.tech,a.plan))
elif a.cmd=="set-stage-status":
    if a.actor not in set(coder_ids())|{"advisor","human","system"}: raise SystemExit("unknown actor")
    replace_top_field(stage_path(a.stage),"status",a.status); append_log(a.actor,"-","stage",f"{a.stage} status -> {a.status}: {a.reason}"); render_status()
elif a.cmd=="new-study": print(new_study(a.title,a.hypothesis,a.priority,a.owner,a.competition,a.track,a.stage))
elif a.cmd=="new-attempt": print(new_attempt(a.study,a.owner,a.flavor,a.label,a.track,a.status))
elif a.cmd=="validate":
    render_status(); errs=validate()
    if errs: print("Repository contract: FAIL\n"+"\n".join("- "+x for x in errs)); raise SystemExit(1)
    print("Repository contract: OK")
