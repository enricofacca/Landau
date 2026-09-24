# Credential profiles, browser login, and account failover

The default `ai-tools/config/accounts.toml` is a worked example. All email addresses are fake `@example.com` labels; none is used as a credential.

```text
Codex
  codex-primary    -> codex.one@example.com
  codex-secondary  -> codex.two@example.com

Claude Code — same email, two subscription scopes
  claude-personal  -> claude.same.user@example.com / Personal Pro/Max
  claude-team      -> claude.same.user@example.com / Example Research Team

Antigravity
  antigravity-primary   -> antigravity.one@example.com
  antigravity-secondary -> antigravity.two@example.com
```

The Claude example is intentionally different: **email is not the unique key**. The workbench distinguishes the two subscriptions by profile id, `account_scope`, `workspace_hint`, and a separate authentication context.

Never commit passwords, API keys, cookies, refresh tokens, `auth.json` contents, browser-session files, or keyring exports.

## What to edit after cloning

Open `ai-tools/config/accounts.toml` and replace the fake labels/hints. Keep authentication material outside the repository.

Prepare non-secret external directories:

```bash
python ai-tools/scripts/prepare_account_profiles.py          # dry-run
python ai-tools/scripts/prepare_account_profiles.py --apply  # dirs/config only; never credentials
```

Inspect a one-time login hint:

```bash
python ai-tools/scripts/account.py login-hint codex-primary
python ai-tools/scripts/account.py login-hint claude-personal
python ai-tools/scripts/account.py login-hint claude-team
python ai-tools/scripts/account.py login-hint antigravity-primary
```

## Codex: one `CODEX_HOME` per account

Default contexts:

```text
~/.agent-accounts/codex/account-1
~/.agent-accounts/codex/account-2
```

Each may use:

```toml
cli_auth_credentials_store = "file"
```

Then authenticate once per account:

```bash
CODEX_HOME="$HOME/.agent-accounts/codex/account-1" codex login
CODEX_HOME="$HOME/.agent-accounts/codex/account-2" codex login
```

The runner injects the selected `CODEX_HOME` automatically.

## Claude Code: same email, Personal + Team

The defaults intentionally use:

```toml
id = "claude-personal"
email_hint = "claude.same.user@example.com"
account_scope = "personal"
workspace_hint = "Personal Pro/Max -- REPLACE ME"
auth_context = "~/.agent-accounts/claude/personal"

id = "claude-team"
email_hint = "claude.same.user@example.com"
account_scope = "team"
workspace_hint = "Example Research Team -- REPLACE ME"
auth_context = "~/.agent-accounts/claude/team"
```

Authenticate the two isolated contexts separately:

```bash
CLAUDE_CONFIG_DIR="$HOME/.agent-accounts/claude/personal" claude
# complete browser/OAuth login and select/authorize the personal subscription

CLAUDE_CONFIG_DIR="$HOME/.agent-accounts/claude/team" claude
# same login email is fine; select/authorize the intended Team workspace
```

The workbench's identity is therefore not `email_hint`. It is the profile record plus its isolated `CLAUDE_CONFIG_DIR`.

If you belong to multiple teams with the same login, add one profile per team, for example:

```toml
[[profiles]]
id = "claude-team-lab"
backend = "claude"
email_hint = "claude.same.user@example.com"
account_scope = "team"
workspace_hint = "Numerics Lab"
auth_strategy = "claude_config_dir"
auth_context = "~/.agent-accounts/claude/team-lab"
enabled = true
```

and add that profile to the desired Claude pool.

## Antigravity: isolate the OS-keyring context

Account-based Antigravity authentication is treated as an external OS/user/keyring concern. The repository stores only launcher paths, for example:

```text
~/.local/bin/agy-account-1
~/.local/bin/agy-account-2
```

A Linux launcher might conceptually do:

```bash
exec sudo -u agy-account-1 -H agy "$@"
```

Use the equivalent isolation mechanism appropriate for your OS. See `ai-tools/scripts/antigravity_isolated_launcher.example.sh`.

## Persistent coder identity

The persistent identity is the workbench role, not provider or subscription:

```text
coder-b
  backend = claude
  account_pool = claude-pool
      ├─ claude-personal
      └─ claude-team
```

A failover does not change the study, attempt, code workspace, or research history.

## Inspect/select profiles

```bash
python ai-tools/scripts/account.py list
python ai-tools/scripts/account.py status
python ai-tools/scripts/account.py current coder-b
python ai-tools/scripts/account.py select coder-b claude-team
python ai-tools/scripts/account.py reset coder-b
```

`list`/`login-hint` show `email_hint`, `account_scope`, and `workspace_hint`, so Personal and Team remain distinguishable even with the same email.

## Failover contract

Exit code `75` is reserved for a **positively identified** quota/account-capacity exhaustion event. Only then may the runner mark the current profile exhausted and try the next enabled profile.

Do not map generic crashes, coding failures, login-required states, network errors, or provider denials to `75`. Browser reauthentication remains interactive.

Use account pools only where the provider and relevant subscription/account terms permit it; the mechanism is for legitimate operational continuity, not bypassing access controls or plan restrictions.
