#!/usr/bin/env python3
from __future__ import annotations
import argparse, tomllib
from pathlib import Path
AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
with (AI_ROOT/"config"/"backends.toml").open("rb") as f: backends=tomllib.load(f).get("backends",{})
with (AI_ROOT/"config"/"runtime.toml").open("rb") as f: runtime=tomllib.load(f)
with (AI_ROOT/"config"/"accounts.toml").open("rb") as f: accounts=tomllib.load(f)
ap=argparse.ArgumentParser(description="Print provider permission/setup hints derived from repository config")
ap.add_argument("provider", choices=sorted(backends)); a=ap.parse_args()
b=backends[a.provider]
py=runtime["environment"].get("python_executable",".venv/bin/python")
print(f"Provider: {a.provider} — {b.get('label',a.provider)}")
print(f"Workspace: {ROOT}")
print(f"Project Python declared in ai-tools/config/runtime.toml: {py}")
print("Common execution gateway: python ai-tools/scripts/run_allowed.py <program> ...")
print("Declared standard programs:")
for name,spec in runtime.get("programs",{}).items():
    print(f"  - {name}: {spec.get('description','')}")
print("\nRepository-level authorization:")
pol=runtime.get("policy",{})
for key,val in pol.items(): print(f"  {key} = {val}")
note=b.get("permission_note")
if note: print(f"\nProvider note: {note}")
profiles=[p for p in accounts.get("profiles",[]) if p.get("backend")==a.provider]
if profiles:
    print("\nConfigured example account profiles (email_hint is display-only):")
    for p in profiles:
        detail=p.get("auth_context") or p.get("launcher") or "-"
        print(f"  - {p.get('id')}: {p.get('email_hint','-')} scope={p.get('account_scope','-')} workspace={p.get('workspace_hint','-')} strategy={p.get('auth_strategy','selector_only')} context={detail}")
    print(f"Run: python ai-tools/scripts/account.py login-hint {profiles[0].get('id')}")
print("\nConfigure the provider to read/write this repository and, where possible, allow the stable run_allowed.py command prefix.")
print("Provider sandbox/approval controls remain authoritative; this script does not change them.")
