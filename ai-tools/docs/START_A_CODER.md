# Start a coding agent

Open the repository in the coding agent and give it one stable instruction:

> Read `ai-tools/agents/CODER.md` and `ai-tools/research/assignments/<AGENT-ID>.md`. You own the listed attempt(s). Work directly in this repository, use `ai-tools/config/runtime.toml` for the shared environment/tools, preserve each attempt's declared flavor and isolated workspace, run and record the required experiments and tests, and continue until every parent study reaches a reviewed terminal state or the advisor/human explicitly terminates your attempt. Do not stop at intermediate milestones.

Example:

```text
Read ai-tools/agents/CODER.md and ai-tools/research/assignments/coder-a.md. Execute the assignment to its reviewed terminal condition; do not stop at intermediate milestones.
```

Autonomous loop:

```bash
python ai-tools/scripts/agent_loop.py --agent coder-a
```

Interactive takeover:

```bash
python ai-tools/scripts/control.py pause coder-a
python ai-tools/scripts/backend_runner.py --agent coder-a --mode interactive
python ai-tools/scripts/control.py resume coder-a
```
