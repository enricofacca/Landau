# Architecture

The outer repository stays conventional; the AI/research control plane is self-contained.

```text
repository/
├── src/                 stable/promoted package
├── tests/               stable public tests
├── demos/               public examples
└── ai-tools/
    ├── config/          runtime, backends, account pools
    ├── agents/          coder/advisor role contracts
    ├── research/        stages, studies, attempts, competitions, log
    ├── workspaces/
    │   ├── experiments/ isolated active attempts
    │   └── prototypes/  reusable non-stable artifacts
    ├── scripts/         orchestration/control
    ├── tests/           workbench contract tests
    └── docs/
```

## Control model

```text
                         human
                           |
                  advisor/coordinator
                    /             \
             coder-a             coder-b ...
               |                   |
          ATTEMPT A1          ATTEMPT A2
               \                 /
             STUDY / TRACK under common criteria
                       |
                reviewed outcome
                  /            \
        record/prototype      promotion
             |                   |
 ai-tools/workspaces/*       src/ + tests/
```

## Layers

1. **Runtime/tool contract** — `ai-tools/config/runtime.toml`.
2. **Provider/account layer** — `ai-tools/config/backends.toml` and `ai-tools/config/accounts.toml`.
3. **Research control plane** — `ai-tools/research/`.
4. **Execution plane** — isolated experiment/prototype workspaces plus stable `src/`/`tests/`.
5. **Human control plane** — tmux attach, pause, interactive takeover, resume.

## Scientific state vs artifact disposition

These are orthogonal. A method can be `outcompeted` but still retain a useful reference implementation; a nonviable attempt remains in the record; a reusable but non-stable artifact lives under `ai-tools/workspaces/prototypes/`; only reviewed/hardened software is promoted to `src/` with permanent tests in `tests/`.

## Replicas on the same task

`STUDY` captures the question, `TRACK` the approach, and `ATTEMPT` an independent implementation. Multiple agents may attack the same track with different flavors. Attempt workspaces are isolated under `ai-tools/workspaces/experiments/<study>/<attempt>/`.

The advisor compares replicas inside a track before judging the track itself.

## Persistent identity and credentials

```text
coder-b
   ↓
backend = claude
   ↓
claude-pool
   ├── claude-personal
   └── claude-team
```

Agent identity is separate from provider and credential identity. For Claude, Personal and Team profiles may intentionally share the same `email_hint`; they remain distinct through profile id, subscription/workspace metadata, and separate `CLAUDE_CONFIG_DIR` contexts.

## Background + intervention

```bash
./ai-tools/scripts/start-workbench.sh --detach
./ai-tools/scripts/attach-workbench.sh coder-a
```

Each coder window has an autonomous pane plus a human control pane. Pause the autonomous loop before interactive takeover, then resume from repository state.
