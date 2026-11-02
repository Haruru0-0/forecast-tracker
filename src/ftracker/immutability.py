"""Fail when a commit range edits, deletes or renames protected history files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROTECTED: tuple[str, ...] = ("data/forecasts", "data/outcomes", "data/gaps")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def _non_add(output: str, found: dict[str, str]) -> None:
    for line in output.splitlines():
        status, _, path = line.partition("	")
        if status and status != "A":
            found.setdefault(path, status)


def check_immutable(repo: Path, base: str, head: str = "HEAD") -> list[str]:
    """Return one message per protected path changed in any way other than added.

    Checks the net diff base..head and every commit in the range (merge commits
    against their first parent), so add-then-edit inside one push is caught.
    """
    if not base:
        raise ValueError("base revision is required (empty value given)")
    if set(base) == {"0"}:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    try:
        violations = check_immutable(Path(args.repo), args.base, args.head)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"IMMUTABILITY CHECK ERROR: {exc}", file=sys.stderr)
        return 2
    for v in violations:
        print(f"IMMUTABILITY VIOLATION: {v}", file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
