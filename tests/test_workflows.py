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
