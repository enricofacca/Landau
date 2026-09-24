# Assignment — coder-a

**Role:** Track A replica 1
**Backend:** `codex`
**Account pool:** `codex-pool`
**Current credential:** `auto:codex-primary (codex.one@example.com)`

## Mission

Drive every assigned attempt/study until the parent study reaches a configured terminal scientific state or the advisor/human explicitly stops/outperforms/nonviables that attempt. Intermediate milestones are not completion.

## Assigned attempts

- `ATTEMPT-0001` — attempt **active** — study `STUDY-0001` **backlog** — track `TRACK-A` — Independent replica A1 — flavor: Correctness-first; minimal architecture changes; preserve a simple reference implementation. — workspace `ai-tools/workspaces/experiments/STUDY-0001/ATTEMPT-0001`

## Start / resume protocol

1. Read `ai-tools/config/runtime.toml`; use its shared environment and named commands.
2. Read `ai-tools/agents/CODER.md`, `ai-tools/research/program.toml`, and the technical note/development plan for the parent stage.
3. Read your attempt record(s), parent study, linked competition, reuse registry, and `ai-tools/research/advice/LATEST.md`.
4. Work only in your attempt workspace unless an advisor/human explicitly promotes shared code.
5. Execute the next discriminating experiment, record evidence, and continue toward the parent study's terminal criteria.
6. Do not stop at a prototype, passing test, partial speedup, or temporary lead/loss.
7. Never delete failed code/history. Advisor/human decide retention/promotion.
