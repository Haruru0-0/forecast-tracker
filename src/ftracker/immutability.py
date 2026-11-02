"""Fail when a commit range edits, deletes or renames protected history files.

Standard library only: CI copies this file out of the base revision and runs it standalone
(``python immutability_base.py --base <sha>``), so it must never import ``ftracker``.

Modes:
  --base B            every commit in B..HEAD (and the net diff) may only add protected files
  --base B --guard    B..HEAD must not change a guard file (the checker, the workflows, the
                      push script) and touch protected data in the same range
  --whole-history     the per-commit check from each root commit, so an old violation keeps
                      every later run red
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROTECTED: tuple[str, ...] = ("data/forecasts", "data/outcomes", "data/gaps")
GUARD: tuple[str, ...] = ("src/ftracker/immutability.py", ".github/workflows", "scripts/commit_and_push.sh")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def _non_add(output: str, found: dict[str, str]) -> None:
    for line in output.splitlines():
        status, _, path = line.partition("\t")
        if status and status != "A":
            found.setdefault(path, status)


def _is_zero(base: str) -> bool:
    return set(base) == {"0"}


def _require_base(base: str) -> None:
    if not base:
        raise ValueError("base revision is required (empty value given)")


def check_immutable(repo: Path, base: str, head: str = "HEAD") -> list[str]:
    """Return one message per protected path changed in any way other than added.

    Checks the net diff base..head and every commit in the range (merge commits
    against their first parent), so add-then-edit inside one push is caught.
    """
    _require_base(base)
    if _is_zero(base):
        return []  # first push of a branch: nothing to compare against
    net = _git(repo, "diff", "--name-status", "--no-renames", base, head, "--", *PROTECTED)
    per_commit = _git(
        repo, "log", "--no-renames", "--name-status", "--format=", "--full-history",
        "--diff-merges=first-parent", f"{base}..{head}", "--", *PROTECTED,
    )
    found: dict[str, str] = {}
    _non_add(net, found)
    _non_add(per_commit, found)
    return [f"{path}: {status} (protected files may only be added)" for path, status in found.items()]


def _touched(repo: Path, base: str, head: str, paths: tuple[str, ...]) -> list[str]:
    net = _git(repo, "diff", "--name-only", "--no-renames", base, head, "--", *paths)
    per_commit = _git(
        repo, "log", "--no-renames", "--name-only", "--format=", "--full-history",
        "--diff-merges=first-parent", f"{base}..{head}", "--", *paths,
    )
    return sorted({p for p in (net + "\n" + per_commit).splitlines() if p.strip()})


def check_guard(repo: Path, base: str, head: str = "HEAD") -> list[str]:
    """Return a message when base..head changes a guard file and touches protected data.

    The data side is the net diff base..head only. Per-commit diffs would count the bot's
    data that a merge (``git pull`` without ``--rebase``) brings in against its first
    parent, although that data is already in base. Add-then-edit or add-then-delete inside
    the range is still caught by the per-commit scan in ``check_immutable``.
    """
    _require_base(base)
    if _is_zero(base):
        return []
    guard = _touched(repo, base, head, GUARD)
    net_data = _git(repo, "diff", "--name-only", "--no-renames", base, head, "--", *PROTECTED)
    data = sorted({p for p in net_data.splitlines() if p.strip()})
    if guard and data:
        return [f"guard files changed in the same push as protected data: {', '.join(guard)} "
                f"together with {len(data)} file(s) under {', '.join(PROTECTED)}"]
    return []


def roots(repo: Path, head: str = "HEAD") -> list[str]:
    return _git(repo, "rev-list", "--max-parents=0", head).split()


def check_whole_history(repo: Path, head: str = "HEAD") -> list[str]:
    """The per-commit check from every root commit (a root commit can only add files)."""
    out: list[str] = []
    for root in roots(repo, head):
        for v in check_immutable(repo, root, head):
            if v not in out:
                out.append(v)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--guard", action="store_true",
                        help="fail when guard files and protected data change in the same range")
    parser.add_argument("--whole-history", action="store_true",
                        help="check every commit since the root commit(s); --base is ignored")
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    try:
        if args.whole_history:
            violations = check_whole_history(repo, args.head)
        elif args.base is None:
            raise ValueError("--base is required unless --whole-history is given")
        elif args.guard:
            violations = check_guard(repo, args.base, args.head)
        else:
            violations = check_immutable(repo, args.base, args.head)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"IMMUTABILITY CHECK ERROR: {exc}", file=sys.stderr)
        return 2
    for v in violations:
        print(f"IMMUTABILITY VIOLATION: {v}", file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
