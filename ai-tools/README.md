# AI research workbench

This directory is an **optional, self-contained development layer** around the normal Python repository. It is designed for one advisor plus one or more coding agents, competing tracks, independent replicas of the same task, durable hypothesis records, and reusable experimental prototypes.

Nothing here is required to import, install, test, or use the package in `../src/`.

## Boundary

```text
repository/
├── README.md             normal user-facing project README
├── pyproject.toml
├── src/                  stable/promoted software
├── tests/                stable public tests
├── demos/                public examples
└── ai-tools/             everything AI/research-workbench specific
    ├── config/
    ├── agents/
    ├── research/
    ├── workspaces/
    │   ├── experiments/
    │   └── prototypes/
    ├── scripts/
    ├── tests/            workbench contract tests
    └── docs/
```

The intended promotion path is:

```text
ai-tools/workspaces/experiments/
        ↓ reviewed evidence
ai-tools/workspaces/prototypes/
        ↓ hardening + permanent tests
src/
```

A failed/nonviable approach remains recorded under `ai-tools/research/` and its experimental workspace. A correct but inefficient or otherwise useful implementation may be retained under `ai-tools/workspaces/prototypes/` even if its scientific track is outcompeted.

## Bootstrap a cloned kit

From repository root:

```bash
python ai-tools/scripts/bootstrap.py \
  --name "My project" \
  --package my_project
```

Then edit:

```text
ai-tools/research/program.toml
ai-tools/research/stages/STAGE-0001/technical_note.md
ai-tools/research/stages/STAGE-0001/development_plan.md
ai-tools/config/runtime.toml
ai-tools/config/accounts.toml
```

The default account file uses only fake `@example.com` labels. It includes:

```text
Codex
  codex-primary    -> codex.one@example.com
  codex-secondary  -> codex.two@example.com

Claude Code (same login email, two subscription scopes)
  claude-personal  -> claude.same.user@example.com / Personal Pro/Max
  claude-team      -> claude.same.user@example.com / Example Research Team

Antigravity
  antigravity-primary   -> antigravity.one@example.com
  antigravity-secondary -> antigravity.two@example.com
```

For Claude, `email_hint` is deliberately identical in the Personal and Team examples. The workbench distinguishes them by profile id, `account_scope`, `workspace_hint`, and separate `CLAUDE_CONFIG_DIR` values.

## Start the laboratory

Configure backend CLI commands using `ai-tools/.env.example` or your shell environment, then:

```bash
./ai-tools/scripts/start-workbench.sh
```

or background mode:

```bash
./ai-tools/scripts/start-workbench.sh --detach
```

Attach later:

```bash
./ai-tools/scripts/attach-workbench.sh
./ai-tools/scripts/attach-workbench.sh coder-a
```

The tmux session contains one window per coding agent plus advisor and status windows. Each coder has an autonomous pane and a human-control pane.

## Common commands

```bash
python ai-tools/scripts/workbench.py status
python ai-tools/scripts/workbench.py validate
python ai-tools/scripts/workbench.py assignment coder-a
python ai-tools/scripts/run_allowed.py list
python ai-tools/scripts/run_allowed.py test
python ai-tools/scripts/run_allowed.py ai_contract
python ai-tools/scripts/account.py status
```

## Same task, multiple coding agents

`STUDY` stores the scientific/engineering question, `TRACK` stores an approach, and `ATTEMPT` stores an independent implementation replica. Multiple coders may work on the same `STUDY` and `TRACK` with different flavors without sharing an experimental workspace.

```text
STUDY-0001 / TRACK-A
├── ATTEMPT-0001 → coder-a → correctness-first
└── ATTEMPT-0002 → coder-b → independent/simplification-first
```

The advisor compares replicas inside a track before judging competing tracks.

See [`docs/HOW_TO_RUN_REPLICAS.md`](docs/HOW_TO_RUN_REPLICAS.md).

## Accounts and provider switching

Persistent identities are workbench roles (`coder-a`, `coder-b`, …), not providers or login accounts. A coder can change backend or credential profile without changing its assigned attempt or research history.

- Codex example: one external `CODEX_HOME` per account.
- Claude example: separate `CLAUDE_CONFIG_DIR` values; the default demonstrates Personal + Team subscriptions using the **same email**.
- Antigravity example: external isolated launchers / OS-keyring contexts.

Secrets stay outside the repository. Browser login remains interactive. Automatic failover is only for already-authenticated profiles and only when a provider wrapper positively reports the configured quota/capacity condition.

See [`docs/HOW_TO_MANAGE_ACCOUNTS.md`](docs/HOW_TO_MANAGE_ACCOUNTS.md) and [`docs/PROVIDERS.md`](docs/PROVIDERS.md).

## Add a new research stage

```bash
python ai-tools/scripts/workbench.py new-stage \
  --title "Temporal coarsening" \
  --goal "Test temporal condensation on the validated solver" \
  --tech path/to/technical_note.md \
  --plan path/to/development_plan.md
```

Stable software in `src/` is automatically available to later stages; explicitly preserved prototypes remain indexed under `ai-tools/research/reuse/components.toml`.

See [`docs/HOW_TO_ADD_A_STAGE.md`](docs/HOW_TO_ADD_A_STAGE.md).

## Documentation

- [`docs/START_A_CODER.md`](docs/START_A_CODER.md)
- [`docs/AGENTS.md`](docs/AGENTS.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/HOW_TO_RUN_REPLICAS.md`](docs/HOW_TO_RUN_REPLICAS.md)
- [`docs/HOW_TO_MANAGE_ACCOUNTS.md`](docs/HOW_TO_MANAGE_ACCOUNTS.md)
- [`docs/HOW_TO_ADD_A_BACKEND.md`](docs/HOW_TO_ADD_A_BACKEND.md)
- [`docs/HOW_TO_ADD_A_STAGE.md`](docs/HOW_TO_ADD_A_STAGE.md)
- [`docs/PROVIDERS.md`](docs/PROVIDERS.md)

## Workbench state versus public code

The core rule is: **research state belongs to `ai-tools/research/`; stable product state belongs to `src/` and `tests/`.** The repository remains useful and conventional even if `ai-tools/` is never opened.
