# How to add the next research/development stage

Use a new stage when the project has a new mathematical/technical question or development phase that builds on the software already promoted or preserved from earlier work.

## 1. Finish your mathematical discussion outside the agent loop

Produce a concise technical note and, optionally, a development plan. The note should state the formulation, assumptions, interfaces to existing code, and unresolved questions. The plan should state candidate approaches and validation criteria.

## 2. Create the stage

```bash
python ai-tools/scripts/workbench.py new-stage \
  --title "Temporal coarsening" \
  --goal "Determine whether the frozen-coefficient DtN reduction is accurate and cheaper" \
  --tech path/to/technical_note.md \
  --plan path/to/development_plan.md
```

This snapshots the current Git `HEAD` as the software baseline when possible and creates:

```text
ai-tools/research/stages/STAGE-XXXX/
  stage.toml
  technical_note.md
  development_plan.md
```

## 3. Create studies inside the stage

```bash
python ai-tools/scripts/workbench.py new-study \
  --stage STAGE-0002 \
  --title "Frozen gamma DtN" \
  --hypothesis "..." \
  --owner coder-a
```

Create a competition if two or more tracks answer the same question under common metrics. Existing `src/` code is the stable baseline. Reusable non-stable assets may also be taken from `ai-tools/workspaces/prototypes/`, but their registered limitations remain in force.

## 4. Run / compare / retain

Coding agents work until studies become terminal. The advisor compares evidence and recommends what should happen to each artifact. Terminal scientific state and code retention are separate decisions.

## 5. Decide artifact disposition

Advisor recommendation:

```bash
python ai-tools/scripts/workbench.py disposition STUDY-0007 preserve_prototype \
  --actor advisor --reason "Correct and reusable diagnostic; too slow for stable solver"
```

Human decision:

```bash
python ai-tools/scripts/workbench.py disposition STUDY-0007 preserve_prototype \
  --actor human --reason "Keep for future cross-checks"
```

Possible dispositions:

- `record_only`: keep the study/code/history, do not treat it as reusable infrastructure;
- `preserve_prototype`: extract/register useful pieces under `ai-tools/workspaces/prototypes/`;
- `promotion_candidate`: worth hardening toward `src/`;
- `promoted`: reviewed stable code has entered `src/` with permanent tests.

Nothing is erased merely because an approach was wrong, slow, or outcompeted.
