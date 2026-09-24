#!/usr/bin/env python3
"""Prepare non-secret external auth directories declared in ai-tools/config/accounts.toml.

Default behavior is dry-run. Use --apply to create directories and the Codex
config.toml needed for per-CODEX_HOME file credential storage. This script never
logs in, writes credentials, edits keyrings, or automates browser authentication.
"""
from __future__ import annotations
import argparse, tomllib
from pathlib import Path

AI_ROOT=Path(__file__).resolve().parents[1]
ROOT=AI_ROOT.parent
with (AI_ROOT/'config'/'accounts.toml').open('rb') as f:
    cfg=tomllib.load(f)

ap=argparse.ArgumentParser()
ap.add_argument('--apply',action='store_true',help='create non-secret external directories/config files')
ap.add_argument('--profile',action='append',default=[],help='limit to one or more profile ids')
a=ap.parse_args()
selected=set(a.profile)

for p in cfg.get('profiles',[]):
    if selected and p.get('id') not in selected:
        continue
    pid=p['id']; strategy=p.get('auth_strategy','selector_only')
    print(f"\n[{pid}] {p.get('email_hint','-')}  strategy={strategy}")
    if p.get('login_hint'):
        print(f"  login: {p['login_hint']}")
    if strategy in {'codex_home','claude_config_dir'}:
        path=Path(p['auth_context']).expanduser()
        print(f"  external directory: {path}")
        if a.apply:
            path.mkdir(parents=True,exist_ok=True)
            print("  created/verified directory")
        if strategy=='codex_home':
            c=path/'config.toml'
            if a.apply and not c.exists():
                c.write_text('cli_auth_credentials_store = "file"\n')
                print(f"  wrote {c} (non-secret config only)")
            elif c.exists():
                print(f"  existing {c}; not overwritten")
            else:
                print(f"  would create {c} with cli_auth_credentials_store=\"file\"")
    elif strategy=='isolated_launcher':
        launcher=Path(p['launcher']).expanduser()
        print(f"  isolated launcher: {launcher}")
        print(f"  exists: {launcher.exists()}")
    else:
        print("  provider-specific selector/wrapper; no filesystem preparation")

if not a.apply:
    print("\nDry-run only. Re-run with --apply to create non-secret Codex/Claude directories.")
