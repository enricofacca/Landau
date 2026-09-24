from pathlib import Path
import os, subprocess, sys, tomllib

ROOT = Path(__file__).resolve().parents[3]
AI = ROOT / "ai-tools"


def load(path):
    with path.open("rb") as f:
        return tomllib.load(f)


def test_public_root_stays_conventional():
    assert (ROOT / "src").is_dir()
    assert (ROOT / "tests").is_dir()
    assert (ROOT / "demos").is_dir()
    assert (ROOT / "pyproject.toml").exists()
    assert (ROOT / "README.md").exists()
    for hidden_workflow_dir in ["config", "agents", "research", "scripts", "experiments", "prototypes"]:
        assert not (ROOT / hidden_workflow_dir).exists()
    assert AI.is_dir()


def test_ai_tools_are_self_contained():
    required = [
        AI / "README.md",
        AI / "docs" / "AGENTS.md",
        AI / "docs" / "START_A_CODER.md",
        AI / "docs" / "HOW_TO_ADD_A_STAGE.md",
        AI / "docs" / "HOW_TO_ADD_A_BACKEND.md",
        AI / "docs" / "HOW_TO_RUN_REPLICAS.md",
        AI / "docs" / "HOW_TO_MANAGE_ACCOUNTS.md",
        AI / "docs" / "PROVIDERS.md",
        AI / "config" / "runtime.toml",
        AI / "config" / "backends.toml",
        AI / "config" / "accounts.toml",
        AI / "agents" / "CODER.md",
        AI / "agents" / "ADVISOR.md",
        AI / "research" / "program.toml",
        AI / "research" / "LOG.md",
        AI / "research" / "reuse" / "components.toml",
        AI / "research" / "stages" / "STAGE-0001" / "stage.toml",
        AI / "research" / "assignments" / "coder-a.md",
        AI / "research" / "assignments" / "coder-b.md",
        AI / "research" / "competitions" / "COMP-0001" / "competition.toml",
        AI / "research" / "attempts" / "ATTEMPT-0001" / "status.toml",
        AI / "research" / "attempts" / "ATTEMPT-0002" / "status.toml",
        AI / "workspaces" / "prototypes" / "README.md",
        AI / "workspaces" / "experiments" / "README.md",
        AI / "scripts" / "run_allowed.py",
        AI / "scripts" / "backend_runner.py",
        AI / "scripts" / "control.py",
        AI / "scripts" / "account.py",
        AI / "scripts" / "prepare_account_profiles.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    assert not missing, missing


def test_backends_runtime_and_account_pools_are_centralized():
    cfg = load(AI / "project.toml")
    backends = load(AI / "config" / "backends.toml")["backends"]
    runtime = load(AI / "config" / "runtime.toml")
    accounts = load(AI / "config" / "accounts.toml")
    pools = {x["id"]: x for x in accounts["pools"]}
    profiles = {x["id"]: x for x in accounts["profiles"]}
    for coder in cfg["agents"]["coders"]:
        assert coder["backend"] in backends
        assert coder["account_pool"] in pools
        assert pools[coder["account_pool"]]["backend"] == coder["backend"]
    for pool in pools.values():
        assert all(p in profiles for p in pool["profiles"])
    assert {"python", "test", "ai_contract", "validate"} <= set(runtime["programs"])
    assert runtime["environment"]["python_executable"]
    assert accounts["policy"]["secrets_in_repository"] is False


def test_attempts_isolate_multiple_agents_on_same_study():
    attempts = [load(p) for p in (AI / "research" / "attempts").glob("ATTEMPT-*/status.toml")]
    reps = [x for x in attempts if x["study"] == "STUDY-0001" and x["track"] == "TRACK-A"]
    assert len(reps) >= 2
    assert len({x["owner"] for x in reps}) >= 2
    assert len({x["experiment_dir"] for x in reps}) == len(reps)
    for x in reps:
        assert (ROOT / x["experiment_dir"]).is_dir()
        assert x["experiment_dir"].startswith("ai-tools/workspaces/experiments/")
        assert x["flavor"]


def test_studies_have_stage_and_retention_state():
    cfg = load(AI / "project.toml")
    agents = {x["id"] for x in cfg["agents"]["coders"]}
    stages = {p.parent.name for p in (AI / "research" / "stages").glob("STAGE-*/stage.toml")}
    for p in (AI / "research" / "studies").glob("STUDY-*/status.toml"):
        d = load(p)
        assert d["owner"] in agents | {"unassigned", "shared"}
        assert d["stage"] in stages
        assert d["artifact_disposition"] in {"undecided", "record_only", "preserve_prototype", "promotion_candidate", "promoted"}
        assert "disposition_recommended" in d


def test_competition_tracks_and_attempts_are_consistent():
    comp = load(AI / "research" / "competitions" / "COMP-0001" / "competition.toml")
    assert comp["replication"]["allow_multiple_attempts_per_track"]
    tracks = {t["id"]: t for t in comp["tracks"]}
    for track in tracks.values():
        st = load(AI / "research" / "studies" / track["study"] / "status.toml")
        assert st["competition"] == comp["id"] and st["track"] == track["id"] and st["stage"] == comp["stage"]
    for p in (AI / "research" / "attempts").glob("ATTEMPT-*/status.toml"):
        a = load(p)
        assert a["track"] in tracks
        assert a["study"] == tracks[a["track"]]["study"]


def test_account_failover_uses_standard_exit_code(tmp_path):
    wrapper = tmp_path / "fake-provider.sh"
    wrapper.write_text('#!/usr/bin/env bash\nif [ "$WORKBENCH_ACCOUNT_SELECTOR" = primary ]; then exit 75; fi\nexit 0\n')
    wrapper.chmod(0o755)
    subprocess.run([sys.executable, str(AI / "scripts" / "account.py"), "reset", "coder-a"], cwd=ROOT, check=True, capture_output=True, text=True)
    env = os.environ.copy()
    env["CODEX_BATCH_CMD"] = str(wrapper)
    r = subprocess.run([sys.executable, str(AI / "scripts" / "backend_runner.py"), "--agent", "coder-a", "--mode", "batch"], cwd=ROOT, input="test prompt", text=True, env=env, capture_output=True)
    assert r.returncode == 0, r.stderr
    status = subprocess.check_output([sys.executable, str(AI / "scripts" / "account.py"), "status"], cwd=ROOT, text=True)
    assert "coder-a" in status and "codex-secondary" in status
    subprocess.run([sys.executable, str(AI / "scripts" / "account.py"), "reset", "coder-a"], cwd=ROOT, check=True, capture_output=True, text=True)


def test_default_account_examples_include_same_email_claude_personal_and_team():
    accounts = load(AI / "config" / "accounts.toml")
    profiles = {x["id"]: x for x in accounts["profiles"]}
    expected = {
        "codex-primary": ("codex", "codex_home", "codex.one@example.com"),
        "codex-secondary": ("codex", "codex_home", "codex.two@example.com"),
        "antigravity-primary": ("antigravity", "isolated_launcher", "antigravity.one@example.com"),
        "antigravity-secondary": ("antigravity", "isolated_launcher", "antigravity.two@example.com"),
    }
    for pid, (backend, strategy, email) in expected.items():
        p = profiles[pid]
        assert p["backend"] == backend
        assert p["auth_strategy"] == strategy
        assert p["email_hint"] == email
        assert email.endswith("@example.com")

    personal = profiles["claude-personal"]
    team = profiles["claude-team"]
    assert personal["email_hint"] == team["email_hint"] == "claude.same.user@example.com"
    assert personal["account_scope"] == "personal"
    assert team["account_scope"] == "team"
    assert personal["auth_context"] != team["auth_context"]
    assert personal["workspace_hint"] != team["workspace_hint"]
    assert personal["auth_strategy"] == team["auth_strategy"] == "claude_config_dir"
    for p in profiles.values():
        assert "password" not in p and "token" not in p and "api_key" not in p


def test_runner_injects_codex_auth_context(tmp_path):
    wrapper = tmp_path / "check-codex-env.sh"
    wrapper.write_text('#!/usr/bin/env bash\n[ -n "$CODEX_HOME" ] || exit 41\n[ "$WORKBENCH_AUTH_STRATEGY" = codex_home ] || exit 42\n[ "$WORKBENCH_ACCOUNT_EMAIL_HINT" = codex.one@example.com ] || exit 43\nexit 0\n')
    wrapper.chmod(0o755)
    subprocess.run([sys.executable, str(AI / "scripts" / "account.py"), "reset", "coder-a"], cwd=ROOT, check=True, capture_output=True, text=True)
    env = os.environ.copy()
    env["CODEX_BATCH_CMD"] = str(wrapper)
    r = subprocess.run([sys.executable, str(AI / "scripts" / "backend_runner.py"), "--agent", "coder-a", "--mode", "batch"], cwd=ROOT, input="test prompt", text=True, env=env, capture_output=True)
    assert r.returncode == 0, (r.stdout, r.stderr)
    subprocess.run([sys.executable, str(AI / "scripts" / "account.py"), "reset", "coder-a"], cwd=ROOT, check=True, capture_output=True, text=True)
