from pathlib import Path

import yaml

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def test_ci_runs_on_push_and_pull_request_and_checks_immutability():
    text = CI.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    triggers = doc.get("on", doc.get(True))  # PyYAML parses bare `on` as True
    assert "push" in triggers
    assert "pull_request" in triggers
    steps = [s for job in doc["jobs"].values() for s in job["steps"]]
    assert any("ftracker.immutability" in s.get("run", "") for s in steps)


def test_ci_check_wiring():
    doc = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = [s for job in doc["jobs"].values() for s in job["steps"]]
    assert not any("continue-on-error" in s for s in steps)
    runs = [s["run"] for s in steps if "ftracker.immutability" in s.get("run", "")]
    assert any("github.event.before" in r for r in runs)
    assert any("github.event.pull_request.base.sha" in r for r in runs)
    first_imm = next(i for i, s in enumerate(steps) if "ftracker.immutability" in s.get("run", ""))
    pytest_at = next(i for i, s in enumerate(steps) if s.get("run") == "pytest")
    assert first_imm < pytest_at
    assert any(s.get("run") == 'pip install -e ".[dev]"' for s in steps)
