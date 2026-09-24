# Coding-agent backends, account profiles, and permissions

The research protocol is provider-independent. `ai-tools/project.toml` assigns each persistent coder role a backend and account pool; provider/account may change without changing study or attempt identity.

## Default account examples

`ai-tools/config/accounts.toml` contains fake labels only:

```text
Codex:       codex.one@example.com / codex.two@example.com
Claude:      claude.same.user@example.com for BOTH Personal and Team profiles
Antigravity: antigravity.one@example.com / antigravity.two@example.com
```

The Claude duplication is intentional. Email is descriptive metadata, not a unique credential key.

Default auth strategies:

```text
Codex        codex_home         -> CODEX_HOME
Claude Code  claude_config_dir  -> CLAUDE_CONFIG_DIR
Antigravity  isolated_launcher  -> WORKBENCH_ACCOUNT_LAUNCHER
```

See `ai-tools/docs/HOW_TO_MANAGE_ACCOUNTS.md`.

## Shared runtime contract

Configure the Python environment and common executable workflows once in `ai-tools/config/runtime.toml`. Prefer invoking declared commands through:

```bash
python ai-tools/scripts/run_allowed.py <program> ...
```

Provider sandboxes/approval systems remain authoritative; the repository contract does not override them.

## Local backend command example

Adapt flags to the installed CLI versions:

```bash
export CODEX_BATCH_CMD='codex exec --full-auto "$(cat)"'
export CODEX_INTERACTIVE_CMD='codex'

export CLAUDE_BATCH_CMD='claude -p "$(cat)"'
export CLAUDE_INTERACTIVE_CMD='claude'

export ANTIGRAVITY_BATCH_CMD='"$WORKBENCH_ACCOUNT_LAUNCHER" -p "$(cat)"'
export ANTIGRAVITY_INTERACTIVE_CMD='"$WORKBENCH_ACCOUNT_LAUNCHER"'
```

The repository's `ai-tools/.env.example` is the editable starting point.

## Switch provider/account pool without changing work

```bash
python ai-tools/scripts/workbench.py set-backend coder-a claude
python ai-tools/scripts/workbench.py set-account-pool coder-a claude-pool
```

For the default Claude pool, profile selection may then move between `claude-personal` and `claude-team` even though both show the same email.

## Interactive takeover

```bash
python ai-tools/scripts/control.py pause coder-a
python ai-tools/scripts/backend_runner.py --agent coder-a --mode interactive
python ai-tools/scripts/control.py resume coder-a
```

## Permission summary

```bash
python ai-tools/scripts/provider_setup.py antigravity
python ai-tools/scripts/provider_setup.py claude
python ai-tools/scripts/provider_setup.py codex
```

## Failover contract

A wrapper may return exit code `75` only for a positively identified quota/account-capacity exhaustion condition. Generic failures and login-required states must not trigger automatic profile rotation.
