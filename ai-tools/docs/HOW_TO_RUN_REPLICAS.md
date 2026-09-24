# Multiple coding agents on the same task

The hierarchy is:

```text
STAGE
  └─ COMPETITION
      ├─ TRACK-A -> STUDY-0001
      │    ├─ ATTEMPT-0001 -> coder-a, flavor A1
      │    └─ ATTEMPT-0002 -> coder-b, flavor A2
      └─ TRACK-B -> STUDY-0002
           └─ ATTEMPT-0003 -> coder-c
```

A **study/track** is the scientific/algorithmic idea. An **attempt** is one concrete independent implementation of it. Multiple attempts can therefore compete on the same exact task without creating duplicate scientific hypotheses.

Create another replica:

```bash
python ai-tools/scripts/workbench.py new-attempt \
  --study STUDY-0001 \
  --owner coder-c \
  --label "A3 alternative discretization" \
  --flavor "Preserve mathematical formulation; independently redesign data layout and solver interface"
```

The new agent receives its own workspace under `ai-tools/workspaces/experiments/STUDY-0001/ATTEMPT-XXXX/`.

The advisor should first compare replicas within the track. A weak attempt can be marked `outperformed` while the parent track remains active. Only evidence about the underlying method should drive `falsified`, `outcompeted`, or `nonviable` at study level.
