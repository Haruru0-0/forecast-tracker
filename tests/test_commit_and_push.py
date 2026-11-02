"""Run scripts/commit_and_push.sh for real against a bare remote in tmp_path."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
GIT = shutil.which("git")

pytestmark = pytest.mark.skipif(BASH is None or GIT is None,
                                reason="bash and git are needed to run commit_and_push.sh")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _identity(repo: Path) -> None:
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "commit.gpgsign", "false")


@pytest.fixture
def env(tmp_path):
    """A bare remote with one seeded commit on main, two clones, and the script plus a checker copy."""
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", str(remote))
    seed = tmp_path / "seed"
    git(tmp_path, "clone", "-q", str(remote), str(seed))
    _identity(seed)
    git(seed, "checkout", "-q", "-b", "main")
    write(seed, "data/forecasts/s/2026-01-01.json", "1\n")
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "seed")
    git(seed, "push", "-q", "origin", "main")
    clones = []
    for name in ("a", "b"):
        c = tmp_path / name
        git(tmp_path, "clone", "-q", str(remote), str(c))
        _identity(c)
        clones.append(c)
    tools = tmp_path / "tools"
    tools.mkdir()
    shutil.copy(ROOT / "scripts" / "commit_and_push.sh", tools / "commit_and_push.sh")
    shutil.copy(ROOT / "src" / "ftracker" / "immutability.py", tools / "immutability_standalone.py")
    return remote, clones[0], clones[1], tools


def run_script(clone: Path, tools: Path, message: str, *paths: str) -> subprocess.CompletedProcess:
    environ = dict(os.environ,
                   IMMUTABILITY_CHECKER=(tools / "immutability_standalone.py").as_posix(),
                   PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    return subprocess.run([BASH, (tools / "commit_and_push.sh").as_posix(), message, *paths],
                          cwd=clone, env=environ, capture_output=True, text=True, timeout=120)


def remote_tip(remote: Path) -> str:
    return git(remote, "rev-parse", "main")


def remote_files(remote: Path) -> list[str]:
    return git(remote, "ls-tree", "-r", "--name-only", "main").splitlines()


def test_new_data_file_is_committed_and_reaches_the_remote(env):
    remote, a, _, tools = env
    write(a, "data/forecasts/s/2026-01-02.json", "2\n")
    done = run_script(a, tools, "data: day 2", "data")
    assert done.returncode == 0, done.stdout + done.stderr
    assert git(remote, "log", "-1", "--format=%s %an", "main") == "data: day 2 github-actions[bot]"
    assert "data/forecasts/s/2026-01-02.json" in remote_files(remote)


def test_nothing_to_commit_exits_0_and_pushes_nothing(env):
    remote, a, _, tools = env
    before = remote_tip(remote)
    done = run_script(a, tools, "data: nothing", "data")
    assert done.returncode == 0, done.stderr
    assert "Nothing to commit" in done.stdout
    assert remote_tip(remote) == before


def test_modified_protected_file_fails_and_nothing_reaches_the_remote(env):
    remote, a, _, tools = env
    before = remote_tip(remote)
    write(a, "data/forecasts/s/2026-01-01.json", "tampered\n")
    done = run_script(a, tools, "data: tamper", "data")
    assert done.returncode != 0
    assert "IMMUTABILITY VIOLATION" in done.stderr and "2026-01-01.json" in done.stderr
    assert remote_tip(remote) == before


def test_remote_moved_since_clone_is_rebased_and_pushed(env):
    remote, a, b, tools = env
    write(b, "data/forecasts/s/2026-01-03.json", "3\n")
    git(b, "add", "-A")
    git(b, "commit", "-q", "-m", "from b")
    git(b, "push", "-q", "origin", "HEAD:main")
    b_tip = remote_tip(remote)
    write(a, "data/forecasts/s/2026-01-02.json", "2\n")
    done = run_script(a, tools, "data: from a", "data")
    assert done.returncode == 0, done.stdout + done.stderr
    assert git(remote, "rev-parse", "main^") == b_tip  # rebased on top, no merge commit
    files = remote_files(remote)
    assert "data/forecasts/s/2026-01-02.json" in files and "data/forecasts/s/2026-01-03.json" in files


def test_rejected_push_is_retried(env):
    remote, a, _, tools = env
    marker = (remote / "rejected-once").as_posix()
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\n"
                    f'if [ ! -e "{marker}" ]; then touch "{marker}"; echo "rejecting once" >&2; exit 1; fi\n'
                    "exit 0\n", encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    write(a, "data/forecasts/s/2026-01-02.json", "2\n")
    done = run_script(a, tools, "data: retried", "data")
    assert Path(marker).exists(), "the hook did not run, so the retry was not exercised"
    assert done.returncode == 0, done.stdout + done.stderr
    assert "Push rejected (attempt 1 of 3)." in done.stdout
    assert git(remote, "log", "-1", "--format=%s", "main") == "data: retried"


def test_production_default_is_the_installed_module():
    text = (ROOT / "scripts" / "commit_and_push.sh").read_text(encoding="utf-8")
    assert 'python -m ftracker.immutability --base "$base"' in text
    assert '${IMMUTABILITY_CHECKER:-}' in text
