import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"


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


DAILY = ROOT / ".github" / "workflows" / "daily.yml"


def _daily():
    text = DAILY.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    job = next(iter(doc["jobs"].values()))
    return text, doc, job["steps"]


def _idx(steps, needle, key="run"):
    return next(i for i, s in enumerate(steps) if needle in str(s.get(key, "")))


def test_daily_has_schedule_and_manual_trigger():
    _, doc, _ = _daily()
    triggers = doc.get("on", doc.get(True))
    assert "workflow_dispatch" in triggers
    minute, hour, *rest = triggers["schedule"][0]["cron"].split()
    assert hour == "10" and rest == ["*", "*", "*"]


def test_daily_permissions_are_contents_write_pages_write_id_token_write():
    _, doc, _ = _daily()
    assert doc["permissions"] == {"contents": "write", "pages": "write", "id-token": "write"}


def test_daily_reads_eia_key_from_secret_never_literal():
    text, _, steps = _daily()
    assert "secrets.EIA_API_KEY" in text
    daily_step = steps[_idx(steps, "ftracker.cli daily")]
    assert daily_step["env"]["EIA_API_KEY"] == "${{ secrets.EIA_API_KEY }}"
    assert not re.search(r"[A-Za-z0-9]{32}", text)


def test_daily_never_force_pushes():
    _, _, steps = _daily()
    pushes = [s["run"] for s in steps if "git push" in s.get("run", "")]
    assert pushes
    for run in pushes:
        assert "--force" not in run and not re.search(r"\s-f", run) and "--force-with-lease" not in run


def test_daily_serializes_runs_without_cancelling():
    _, doc, _ = _daily()
    assert doc["concurrency"]["group"]
    assert doc["concurrency"]["cancel-in-progress"] is False


def test_daily_commits_data_before_failing_the_job():
    _, _, steps = _daily()
    push = _idx(steps, "git push")
    assert _idx(steps, "ftracker.immutability") < push
    assert _idx(steps, "git rev-parse HEAD") < _idx(steps, "git commit") < _idx(steps, "ftracker.immutability") < push
    assert _idx(steps, "ftracker.cli daily") < _idx(steps, "ftracker.cli site") < _idx(steps, "git commit")
    assert push < _idx(steps, "upload-pages-artifact", "uses") < _idx(steps, "deploy-pages", "uses")
    assert push < len(steps) - 1
    daily = steps[_idx(steps, "ftracker.cli daily")]
    assert daily.get("id") and "continue-on-error" not in daily
    assert "exit 1" in steps[-1]["run"] and daily["id"] in steps[-1]["run"]
    assert "github-pages" in str(_daily()[1]["jobs"])
