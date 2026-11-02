import subprocess
from pathlib import Path

import pytest

from ftracker.immutability import check_immutable

ZERO = "0" * 40


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def commit(repo: Path, msg: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    write(tmp_path, "data/forecasts/s/2026-01-01.json", '{"a": 1}\n')
    write(tmp_path, "data/outcomes/s/2026-01-01.json", '{"b": 1}\n')
    write(tmp_path, "data/status.json", "{}\n")
    commit(tmp_path, "base")
    return tmp_path


def test_new_file_is_allowed(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/forecasts/s/2026-01-02.json", '{"a": 2}\n')
    commit(repo, "add")
    assert check_immutable(repo, base) == []


def test_modified_forecast_is_violation(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/forecasts/s/2026-01-01.json", '{"a": 99}\n')
    commit(repo, "edit")
    result = check_immutable(repo, base)
    assert len(result) == 1
    assert "data/forecasts/s/2026-01-01.json" in result[0]


def test_deleted_outcome_is_violation(repo):
    base = git(repo, "rev-parse", "HEAD")
    (repo / "data/outcomes/s/2026-01-01.json").unlink()
    commit(repo, "delete")
    result = check_immutable(repo, base)
    assert len(result) == 1
    assert "data/outcomes/s/2026-01-01.json" in result[0]


def test_renamed_forecast_is_violation(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "mv", "data/forecasts/s/2026-01-01.json", "data/forecasts/s/2026-01-05.json")
    commit(repo, "rename")
    result = check_immutable(repo, base)
    assert len(result) == 1
    assert "data/forecasts/s/2026-01-01.json" in result[0]


def test_changes_outside_protected_dirs_are_allowed(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/status.json", '{"ok": true}\n')
    commit(repo, "status")
    assert check_immutable(repo, base) == []


def test_all_zero_base_sha_checks_nothing(repo):
    assert check_immutable(repo, ZERO) == []
