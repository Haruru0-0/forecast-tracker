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


SCRIPT = ROOT / "scripts" / "commit_and_push.sh"


def _script_idx(steps, path):
    return next(i for i, s in enumerate(steps)
                if "commit_and_push.sh" in s.get("run", "")
                and re.search(rf"\b{path}\b", s["run"].split("commit_and_push.sh")[1]))


def test_daily_has_schedule_and_manual_trigger():
    _, doc, _ = _daily()
    triggers = doc.get("on", doc.get(True))
    assert "workflow_dispatch" in triggers
    minute, hour, *rest = triggers["schedule"][0]["cron"].split()
    assert minute == "17" and hour == "10" and rest == ["*", "*", "*"]


def test_daily_job_only_runs_on_main():
    _, doc, _ = _daily()
    assert next(iter(doc["jobs"].values()))["if"] == "github.ref == 'refs/heads/main'"


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
    assert not any("git push" in s.get("run", "") for s in steps)  # only the script pushes
    script = SCRIPT.read_text(encoding="utf-8")
    assert "push origin HEAD:main" in script
    assert "--force" not in script and not re.search(r"\s-f\b", script)


def test_daily_serializes_runs_without_cancelling():
    _, doc, _ = _daily()
    assert doc["concurrency"]["group"]
    assert doc["concurrency"]["cancel-in-progress"] is False


def test_daily_commits_data_first_then_site_then_results_then_pages():
    _, doc, steps = _daily()
    d = _idx(steps, "ftracker.cli daily")
    data = _script_idx(steps, "data")
    site = _idx(steps, "ftracker.cli site")
    results = _script_idx(steps, "results")
    up = _idx(steps, "upload-pages-artifact", "uses")
    dep = _idx(steps, "deploy-pages", "uses")
    assert d < data < site < results < up < dep < len(steps) - 1
    assert steps[d]["id"] == "daily" and "continue-on-error" not in steps[d]
    assert steps[site]["id"] == "site" and "continue-on-error" not in steps[site]
    assert "set +e" in steps[d]["run"] and "set +e" in steps[site]["run"]
    assert "exit_code=$?" in steps[d]["run"] and "exit_code=$?" in steps[site]["run"]
    assert "steps.site.outputs.exit_code" in steps[results]["run"]
    assert "github-pages" in str(next(iter(doc["jobs"].values()))["environment"])


def test_daily_checkout_has_full_history():
    _, _, steps = _daily()
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["fetch-depth"] == 0


def test_daily_final_step_always_runs_and_fails_on_either_exit_code():
    _, _, steps = _daily()
    last = steps[-1]
    assert "!cancelled()" in last["if"] or "always()" in last["if"]
    assert "exit 1" in last["run"]
    assert "steps.daily.outputs.exit_code" in last["run"] and "steps.site.outputs.exit_code" in last["run"]


def test_daily_no_step_between_daily_and_last_is_skippable_except_pages():
    _, _, steps = _daily()
    d = _idx(steps, "ftracker.cli daily")
    for s in steps[d:-1]:
        if "if" in s:
            assert str(s.get("uses", "")).startswith(("actions/upload-pages-artifact", "actions/deploy-pages"))
            assert s["if"] == "steps.site.outputs.exit_code == '0'"


def test_commit_script_checks_rebases_and_never_forces():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert "ftracker.immutability --base" in text
    assert "git rebase origin/main" in text
    assert "git push origin HEAD:main" in text
    assert "--force" not in text and not re.search(r"\s-f\b", text)
    assert text.index("ftracker.immutability --base") < text.index("git push origin HEAD:main")
    assert "EIA_API_KEY" not in text


def test_commit_script_passes_bash_syntax_check():
    import shutil
    import subprocess

    import pytest

    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available, so the script syntax cannot be checked")
    done = subprocess.run([bash, "-n", str(SCRIPT)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
