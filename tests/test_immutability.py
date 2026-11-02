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


# ---------- standalone, guard files, whole history ----------

import ast
import shutil
import sys

from ftracker import immutability
from ftracker.immutability import check_guard, check_whole_history

CHECKER = Path(immutability.__file__)


def test_checker_is_standard_library_only():
    tree = ast.parse(CHECKER.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    assert "ftracker" not in names
    assert names <= set(sys.stdlib_module_names) | {"__future__"}, names - set(sys.stdlib_module_names)


def test_no_literal_tab_in_checker_source():
    assert "\t" not in CHECKER.read_text(encoding="utf-8")


def _standalone(tmp_path: Path, repo: Path, *args: str) -> subprocess.CompletedProcess:
    copy = tmp_path / "standalone" / "immutability_base.py"
    copy.parent.mkdir(exist_ok=True)
    shutil.copy(CHECKER, copy)
    return subprocess.run([sys.executable, "-I", str(copy), "--repo", str(repo), *args],
                          capture_output=True, text=True, cwd=tmp_path / "standalone")


def test_standalone_copy_runs_outside_the_package(tmp_path, repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "add")
    ok = _standalone(tmp_path, repo, "--base", base)
    assert ok.returncode == 0, ok.stderr
    write(repo, "data/forecasts/s/2026-01-01.json", "x\n")
    commit(repo, "edit")
    bad = _standalone(tmp_path, repo, "--base", base)
    assert bad.returncode == 1 and "data/forecasts/s/2026-01-01.json" in bad.stderr


def test_guard_file_with_data_in_same_range_is_violation(repo):
    guards = ("src/ftracker/immutability.py", ".github/workflows/ci.yml", "scripts/commit_and_push.sh")
    for i, guard in enumerate(guards):
        base = git(repo, "rev-parse", "HEAD")
        write(repo, guard, f"changed {guard}\n")
        commit(repo, "guard")
        write(repo, f"data/forecasts/s/2026-05-0{i + 1}.json", "1\n")  # an add is enough
        commit(repo, "data")
        result = check_guard(repo, base)
        assert result and guard in result[0]
        assert main(["--base", base, "--guard", "--repo", str(repo)]) == 1
        assert check_immutable(repo, base) == []  # adds alone pass the append-only check


def test_guard_alone_or_data_alone_is_allowed(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, ".github/workflows/ci.yml", "x\n")
    commit(repo, "ci only")
    assert check_guard(repo, base) == []
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/outcomes/s/2026-01-09.json", "1\n")
    write(repo, "data/gaps/s/2026-01-09.json", "1\n")
    write(repo, "data/status.json", "{}\n")
    write(repo, "README.md", "readme\n")
    commit(repo, "data only")
    assert check_guard(repo, base) == []
    assert main(["--base", base, "--guard", "--repo", str(repo)]) == 0


def test_guard_lookalike_workflow_dir_is_not_a_guard(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, ".github/workflows_old/x.yml", "x\n")
    write(repo, "data/forecasts/s/2026-01-09.json", "1\n")
    commit(repo, "both")
    assert check_guard(repo, base) == []


def test_guard_all_zero_base_checks_nothing(repo):
    assert check_guard(repo, ZERO) == []


def test_whole_history_scan_fails_on_an_old_violation(repo):
    write(repo, "data/forecasts/s/2026-01-01.json", "tampered long ago\n")
    commit(repo, "old edit")
    for d in ("02", "03"):
        write(repo, f"data/forecasts/s/2026-01-{d}.json", "1\n")
        commit(repo, f"later {d}")
    recent = git(repo, "rev-parse", "HEAD~1")
    assert check_immutable(repo, recent) == []  # an incremental check no longer sees it
    result = check_whole_history(repo)
    assert result and "data/forecasts/s/2026-01-01.json" in result[0]
    assert main(["--whole-history", "--repo", str(repo)]) == 1


def test_whole_history_clean_repo_passes(repo):
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "add")
    assert check_whole_history(repo) == []
    assert main(["--whole-history", "--repo", str(repo)]) == 0


def test_whole_history_checks_every_root(repo):
    main_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    git(repo, "checkout", "-q", "--orphan", "other")
    git(repo, "rm", "-rq", "--cached", ".")
    for p in list(repo.glob("data/**/*.json")):
        p.unlink()
    write(repo, "data/gaps/o/1.json", "1\n")
    commit(repo, "other root")
    write(repo, "data/gaps/o/1.json", "2\n")
    commit(repo, "edit on other root")
    git(repo, "checkout", "-q", main_branch)
    git(repo, "merge", "-q", "--allow-unrelated-histories", "-m", "join", "other")
    assert len(immutability.roots(repo)) == 2
    assert any("data/gaps/o/1.json" in v for v in check_whole_history(repo))


def test_main_requires_base_or_whole_history(repo):
    assert main(["--repo", str(repo)]) == 2


# ---------- guard rule: data side is the net diff; shallow clones are refused ----------

def _pull_with_merge(repo):
    """Workflow edited locally, the bot's daily data commit pulled in with a merge (no --rebase)."""
    main_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    git(repo, "checkout", "-q", "-b", "bot")
    write(repo, "data/forecasts/s/2026-06-01.json", "1\n")
    write(repo, "data/outcomes/s/2026-06-01.json", "1\n")
    bot_tip = commit(repo, "data: daily")
    git(repo, "checkout", "-q", main_branch)
    write(repo, ".github/workflows/ci.yml", "edited\n")
    commit(repo, "ci: edit workflow")
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge remote-tracking branch origin/main", "bot")
    return bot_tip  # the remote tip before the push, i.e. github.event.before


def test_guard_ignores_bot_data_brought_in_by_a_merge(repo):
    before = _pull_with_merge(repo)
    assert check_guard(repo, before) == []
    assert check_immutable(repo, before) == []
    assert main(["--base", before, "--guard", "--repo", str(repo)]) == 0


def test_guard_still_fails_when_the_net_diff_has_guard_and_new_data(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "scripts/commit_and_push.sh", "changed\n")
    write(repo, "data/gaps/s/2026-06-01.json", "1\n")
    commit(repo, "both in one commit")
    result = check_guard(repo, base)
    assert result and "scripts/commit_and_push.sh" in result[0]


def test_guard_still_fails_when_the_net_diff_has_guard_and_edited_data(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, ".github/workflows/ci.yml", "changed\n")
    commit(repo, "ci")
    write(repo, "data/forecasts/s/2026-01-01.json", "tampered\n")
    commit(repo, "edit")
    assert check_guard(repo, base)
    assert main(["--base", base, "--guard", "--repo", str(repo)]) == 1


def test_guard_passes_data_only_and_guard_only_pushes(repo):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "data/forecasts/s/2026-06-02.json", "1\n")
    commit(repo, "data only")
    assert check_guard(repo, base) == []
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "src/ftracker/immutability.py", "changed\n")
    write(repo, ".github/workflows/daily.yml", "changed\n")
    commit(repo, "guard only")
    assert check_guard(repo, base) == []


def test_whole_history_refuses_a_shallow_clone(tmp_path, repo):
    write(repo, "data/forecasts/s/2026-01-01.json", "tampered\n")
    commit(repo, "old edit")
    write(repo, "data/forecasts/s/2026-01-02.json", "1\n")
    commit(repo, "later")
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", repo.as_uri(), str(shallow)],
                   check=True, capture_output=True, text=True)
    assert git(shallow, "rev-parse", "--is-shallow-repository") == "true"
    with pytest.raises(ValueError, match="shallow"):
        check_whole_history(shallow)
    assert main(["--whole-history", "--repo", str(shallow)]) == 2
    standalone = _standalone(tmp_path, shallow, "--whole-history")
    assert standalone.returncode == 2 and "shallow" in standalone.stderr
