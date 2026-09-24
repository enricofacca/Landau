# How to add or swap a coding-agent backend

A coder id (`coder-a`, `coder-b`, ...) is a durable research role. The backend and account profile are replaceable infrastructure.

## Add a backend

Add one block to `ai-tools/config/backends.toml`:

```toml
[backends.my_agent]
label = "My coding agent"
batch_command_env = "MY_AGENT_BATCH_CMD"
interactive_command_env = "MY_AGENT_INTERACTIVE_CMD"
prompt_transport = "stdin"
permission_note = "Configure this provider to read/write the repo and execute the run_allowed.py gateway."
```

Then define the commands in your local shell/profile (never commit credentials):

```bash
export MY_AGENT_BATCH_CMD='...'
export MY_AGENT_INTERACTIVE_CMD='...'
```

Assign it without changing the study:

```bash
python ai-tools/scripts/workbench.py set-backend coder-a my_agent
```

## Add account profiles for the backend

Add an ordered pool plus one or more non-secret profile records to `ai-tools/config/accounts.toml`.

A generic example:

```toml
[[pools]]
id = "my-agent-pool"
backend = "my_agent"
strategy = "ordered"
profiles = ["my-agent-primary", "my-agent-secondary"]

[[profiles]]
id = "my-agent-primary"
backend = "my_agent"
email_hint = "my.agent.one@example.com" # REPLACE_ME; display-only
auth_strategy = "selector_only"
selector = "primary"
enabled = true
```

If the provider has an official environment variable that isolates its auth/config store, add support for it in `ai-tools/scripts/backend_runner.py` as a new `auth_strategy`. Otherwise keep provider-specific selection in a local wrapper outside the repository.

Existing built-in examples are:

- `codex_home` -> injects `CODEX_HOME`;
- `claude_config_dir` -> injects `CLAUDE_CONFIG_DIR`;
- `isolated_launcher` -> injects `WORKBENCH_ACCOUNT_LAUNCHER`;
- `selector_only` -> local wrapper interprets `WORKBENCH_ACCOUNT_SELECTOR`.

## Permission model

`ai-tools/config/runtime.toml` is the repository-level source of truth for the Python environment and standard executable programs. Provider-specific sandbox/approval settings remain external and authoritative.

Prefer granting the provider:

1. read/write access to this repository;
2. permission to invoke `python ai-tools/scripts/run_allowed.py ...`;
3. only additional shell access that the project really needs.

This lets the list of standard programs evolve in one place without rewriting every agent prompt or provider configuration.

## Interactive takeover

Pause the autonomous role before opening the provider TUI:

```bash
python ai-tools/scripts/control.py pause coder-a
python ai-tools/scripts/backend_runner.py --agent coder-a --mode interactive
python ai-tools/scripts/control.py resume coder-a
```

The repository prompt/state and selected credential profile are regenerated/applied when the interactive session starts.

## Backend and account pool are separate

After switching backend, select a compatible account pool:

```bash
python ai-tools/scripts/workbench.py set-backend coder-a codex
python ai-tools/scripts/workbench.py set-account-pool coder-a codex-pool
```

Then inspect the active profile and its login hint:

```bash
python ai-tools/scripts/account.py status
python ai-tools/scripts/account.py login-hint codex-primary
```
