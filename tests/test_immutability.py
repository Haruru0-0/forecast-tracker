import subprocess
from pathlib import Path

import pytest

from ftracker.immutability import check_immutable, main

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


def test_gaps_modification_is_violation(repo):
    write(repo, "data/gaps/s/2026-01-01.json", '{"g": 1}\n')
    base = commit(repo, "gap")
    write(repo, "data/gaps/s/2026-01-01.json", '{"g": 2}\n')
    commit(repo, "edit gap")
    assert check_immutable(repo, base)


def test_mode_change_is_violation(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "update-index", "--chmod=+x", "data/forecasts/s/2026-01-01.json")
    git(repo, "commit", "-m", "chmod")
    result = check_immutable(repo, base)
    assert result and "data/forecasts/s/2026-01-01.json" in result[0]


def test_type_change_is_violation(repo):
    base = git(repo, "rev-parse", "HEAD")
    oid = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"], cwd=repo, input="target",
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    git(repo, "update-index", "--cacheinfo", f"120000,{oid},data/forecasts/s/2026-01-01.json")
    git(repo, "commit", "-m", "symlink")
    result = check_immutable(repo, base)
    assert result and "data/forecasts/s/2026-01-01.json" in result[0]


def test_lookalike_directory_is_allowed(repo):
    write(repo, "data/forecasts_old/s/x.json", "1\n")
    base = commit(repo, "old")
    write(repo, "data/forecasts_old/s/x.json", "2\n")
    commit(repo, "edit old")
    assert check_immutable(repo, base) == []


def test_add_then_edit_across_two_commits_is_violation(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/forecasts/s/2026-02-01.json", "1\n")
    commit(repo, "add")
    write(repo, "data/forecasts/s/2026-02-01.json", "2\n")
    commit(repo, "edit")
    result = check_immutable(repo, base)
    assert result and all("2026-02-01" in r for r in result)


def test_multi_commit_clean_range_is_allowed(repo):
    base = git(repo, "rev-parse", "HEAD")
    for d in ("02", "03"):
        write(repo, f"data/forecasts/s/2026-01-{d}.json", "1\n")
        commit(repo, f"add {d}")
    assert check_immutable(repo, base) == []


def _branch_merge(repo, bad: bool):
    base = git(repo, "rev-parse", "HEAD")
    main_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    git(repo, "checkout", "-q", "-b", "side")
    if bad:
        write(repo, "data/forecasts/s/2026-01-01.json", "tampered\n")
    else:
        write(repo, "data/forecasts/s/2026-03-01.json", "1\n")
    commit(repo, "side")
    git(repo, "checkout", "-q", main_branch)
    write(repo, "data/forecasts/s/2026-04-01.json", "1\n")
    commit(repo, "main")
    git(repo, "merge", "--no-ff", "-m", "merge", "side")
    return base


def test_clean_merge_commit_is_allowed(repo):
    assert check_immutable(repo, _branch_merge(repo, bad=False)) == []


def test_violation_inside_merged_branch_is_detected(repo):
    assert check_immutable(repo, _branch_merge(repo, bad=True))


def test_main_exit_codes(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "add")
    assert main(["--base", base, "--repo", str(repo)]) == 0
    write(repo, "data/forecasts/s/2026-01-01.json", "x\n")
    commit(repo, "edit")
    assert main(["--base", base, "--repo", str(repo)]) == 1


def test_empty_base_is_an_error(repo):
    with pytest.raises(ValueError):
        check_immutable(repo, "")
    assert main(["--base", "", "--repo", str(repo)]) != 0
