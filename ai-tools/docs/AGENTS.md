# Shared agent protocol

The repository is the source of truth. Chat/session history is disposable.

## Read this first

All agents must read:

1. `ai-tools/config/runtime.toml` — the single execution/tool environment contract;
2. `ai-tools/research/program.toml` — global scientific/engineering objective;
3. the current stage under `ai-tools/research/stages/`;
4. assigned study records and any competition record;
5. `ai-tools/research/advice/LATEST.md` and `ai-tools/research/STATUS.md`.

Do not repeatedly ask the human which Python environment, test command, or standard project program to use if it is already declared in `ai-tools/config/runtime.toml`.

## Source-of-truth order

1. `ai-tools/research/program.toml`
2. `ai-tools/research/stages/*/stage.toml` plus its technical note/development plan
3. `ai-tools/research/studies/*/status.toml`
4. `ai-tools/research/competitions/*/competition.toml`
5. executable evidence: tests, benchmark scripts, run references, reproducible commands
6. terminal `verdict.md` files and `ai-tools/research/DECISIONS.md`
7. `ai-tools/research/LOG.md` for chronology/handoffs

Never silently rewrite history to fit a later interpretation.

## Scientific state and code value are separate

A study has a scientific state (`validated`, `falsified`, `outcompeted`, etc.) and a separate artifact disposition.

- A false hypothesis may still yield valuable code.
- A correct idea may still have unusable implementation code.
- A slow method may remain useful as a reference/cross-check.
- A completely broken attempt should remain traceable even if no code is promoted.

The study directory is never deleted merely because the approach failed.

Artifact dispositions:

- `record_only`
- `preserve_prototype`
- `promotion_candidate`
- `promoted`

The advisor recommends a disposition; by default the human approves the final disposition.

## Scientific invariants

- Every activated hypothesis keeps one stable `STUDY-XXXX` directory.
- `validated` requires the stated validation criteria to be met by reproducible evidence.
- `falsified` requires the stated rejection criterion to be met by reproducible evidence.
- `inconclusive` and `blocked` are nonterminal by default.
- `outcompeted` is a reviewed competitive stop, not a coder's subjective judgment.
- `nonviable` is a reviewed engineering/formulation stop when the approach cannot become meaningfully testable after documented debugging or violates a hard feasibility constraint; it is not scientific falsification.
- A failed coding attempt is not, by itself, a scientific falsification.
- Preserve important negative results and failure modes.
- Reference heavy artifacts in `runs.toml`; do not duplicate them.

## Code zones

- `ai-tools/workspaces/experiments/STUDY-XXXX/`: active isolated work owned by one study/coder.
- `ai-tools/workspaces/prototypes/`: reusable but explicitly non-stable components extracted from studies.
- `src/`: reviewed stable implementation.
- `tests/`: permanent public regression/unit tests.
- `demos/`: imports only stable code from `src/` unless a demo explicitly declares itself experimental.

Promotion is a reviewed event. Do not move rough code directly from an experiment into `src/` merely because it worked once.

## Stage invariants

A new mathematical/development phase gets a new `STAGE-XXXX`. The stage records the software baseline it inherited plus its technical note and development plan. Later stages may reuse `src/` and registered prototypes without erasing the provenance of earlier studies.

## Competition invariants

- Competing tracks use the same declared cases and metrics whenever comparison is claimed.
- Do not cherry-pick cases or silently change metrics after seeing outcomes.
- Missing evidence must be reported as missing, not inferred.
- A temporary lead does not terminate another track.
- The advisor/human may stop a track as `outcompeted` only under the declared comparison rule and minimum evidence.

## Log protocol

Append concise events to `ai-tools/research/LOG.md` with `actor`, `study`, `kind`, and a self-contained message.

Useful kinds: `plan`, `result`, `failure`, `blocker`, `decision-request`, `review`, `comparison`, `promotion`, `retention`, `assignment`, `stage`.

## Replica-aware execution

A coding agent normally owns an `ATTEMPT`, not the scientific study itself. Multiple attempts may point to the same study/track. Treat each attempt workspace as isolated speculative work until advisor/human review promotes shared code.

Provider/account changes do not create a new scientific attempt by themselves. The persistent workbench agent and attempt continue across legitimate credential-profile failover.
