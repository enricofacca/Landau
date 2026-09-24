# Prototypes: reusable but not stable

This directory is the explicit middle layer between active AI research workspaces and stable public code.

- `ai-tools/workspaces/experiments/STUDY-XXXX/`: isolated exploratory work.
- `ai-tools/workspaces/prototypes/`: reusable components that are not yet part of the stable public implementation.
- `src/`: reviewed/promoted code covered by permanent tests in `tests/`.

A scientifically falsified or outcompeted study may still produce a valuable prototype. Conversely, a validated idea may still have implementation code too rough to promote. These decisions remain separate.

Every retained prototype should record its source study and known limitations in `ai-tools/research/reuse/components.toml`.
