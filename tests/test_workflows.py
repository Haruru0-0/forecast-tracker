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


# ---------- CI: checker from the base revision, guard files, whole history ----------

def _ci_steps():
    doc = yaml.safe_load(CI.read_text(encoding="utf-8"))
    return [s for job in doc["jobs"].values() for s in job["steps"]]


def _imm_bodies():
    steps = _ci_steps()
    push = next(s for s in steps if s.get("name") == "Immutability check (push)")
    pr = next(s for s in steps if s.get("name") == "Immutability check (pull request)")
    return push, pr


def test_ci_runs_checker_copied_from_base_revision():
    push, pr = _imm_bodies()
    assert push["if"] == "github.event_name == 'push'"
    assert pr["if"] == "github.event_name == 'pull_request'"
    for step, expr in ((push, "${{ github.event.before }}"), (pr, "${{ github.event.pull_request.base.sha }}")):
        body = step["run"]
        assert body.splitlines()[0] == f'BASE="{expr}"'
        assert 'checker="$RUNNER_TEMP/immutability_base.py"' in body
        assert 'git show "$BASE:src/ftracker/immutability.py" > "$checker"' in body
        assert 'python "$checker"' in body
        assert 'run_base --base "$BASE"' in body
        assert 'run_modes --base "$BASE" --guard' in body
        assert "run_modes --whole-history" in body
    # identical apart from the BASE line, so the two events cannot drift apart
    assert push["run"].splitlines()[1:] == pr["run"].splitlines()[1:]
    steps = _ci_steps()
    assert steps.index(push) < steps.index(next(s for s in steps if s.get("run") == "pytest"))


def _git(repo, *args):
    import subprocess

    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _commit(repo, msg):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


def _ci_repo(tmp_path):
    git, write, commit = _git, _write, _commit
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "commit.gpgsign", "false")
    write(repo, "src/ftracker/immutability.py",
          (ROOT / "src" / "ftracker" / "immutability.py").read_text(encoding="utf-8"))
    write(repo, "data/forecasts/s/2026-01-01.json", "1\n")
    base = commit(repo, "base")
    return repo, base, commit, write


def _run_ci_body(tmp_path, repo, base):
    import os
    import shutil
    import subprocess
    import sys

    import pytest

    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available, so the CI step cannot be executed")
    push, _ = _imm_bodies()
    body = push["run"].replace("${{ github.event.before }}", base)
    temp = tmp_path / "runner_temp"
    temp.mkdir(exist_ok=True)
    env = dict(os.environ, RUNNER_TEMP=temp.as_posix(),
               PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    return subprocess.run([bash, "-eo", "pipefail", "-c", body], cwd=repo, env=env, capture_output=True, text=True)


def test_ci_body_uses_base_checker_even_if_head_disables_it(tmp_path):
    repo, base, commit, write = _ci_repo(tmp_path)
    write(repo, "src/ftracker/immutability.py", "import sys\nsys.exit(0)\n")
    write(repo, "data/forecasts/s/2026-01-01.json", "tampered\n")
    commit(repo, "disable the checker and edit history")
    done = _run_ci_body(tmp_path, repo, base)
    assert done.returncode != 0
    assert "Using the checker from the base revision" in done.stdout
    assert "data/forecasts/s/2026-01-01.json" in done.stderr


def test_ci_body_passes_a_clean_push(tmp_path):
    repo, base, commit, write = _ci_repo(tmp_path)
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "add")
    done = _run_ci_body(tmp_path, repo, base)
    assert done.returncode == 0, done.stdout + done.stderr


def test_ci_body_fails_on_guard_file_plus_data(tmp_path):
    repo, base, commit, write = _ci_repo(tmp_path)
    write(repo, "scripts/commit_and_push.sh", "echo changed\n")
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "script and data together")
    done = _run_ci_body(tmp_path, repo, base)
    assert done.returncode != 0 and "guard files changed" in done.stderr


def test_ci_body_whole_history_stays_red_after_an_old_violation(tmp_path):
    repo, _, commit, write = _ci_repo(tmp_path)
    write(repo, "data/forecasts/s/2026-01-01.json", "tampered\n")
    commit(repo, "old edit")
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    base = commit(repo, "later")
    write(repo, "data/forecasts/s/2026-01-03.json", "1\n")
    commit(repo, "newest")  # this push only adds; the old edit is outside base..HEAD
    done = _run_ci_body(tmp_path, repo, base)
    assert done.returncode != 0 and "data/forecasts/s/2026-01-01.json" in done.stderr


def test_ci_body_falls_back_to_head_checker_on_first_push(tmp_path):
    repo, _, commit, write = _ci_repo(tmp_path)
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "add")
    done = _run_ci_body(tmp_path, repo, "0" * 40)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "using the HEAD version" in done.stdout


def test_ci_body_falls_back_when_base_has_no_checker(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    _write(repo, "README.md", "no checker yet\n")
    base = _commit(repo, "before the checker existed")
    _write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    _commit(repo, "add")
    done = _run_ci_body(tmp_path, repo, base)
    assert "using the HEAD version" in done.stdout
    assert done.returncode == 0, done.stdout + done.stderr


def test_commit_script_stays_incremental_and_says_why():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'base="$(git rev-parse origin/main)"' in text
    assert "--whole-history" not in text
    assert "whole history" in text.lower()


def test_daily_renders_readme_after_site_and_commits_it_with_results():
    _, _, steps = _daily()
    site = _idx(steps, "ftracker.cli site")
    results = _script_idx(steps, "results")
    body = steps[results]["run"]
    assert site < results
    assert "python scripts/render_readme.py" in body
    assert body.index("python scripts/render_readme.py") < body.index("commit_and_push.sh")
    paths = body.split("commit_and_push.sh", 1)[1].split("\n", 1)[0].split()
    assert paths[-2:] == ["results", "README.md"]
    assert not any("render_readme" in s.get("run", "") for i, s in enumerate(steps) if i != results)
