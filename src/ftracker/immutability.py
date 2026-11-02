"""Fail when a commit range edits, deletes or renames protected history files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROTECTED: tuple[str, ...] = ("data/forecasts", "data/outcomes", "data/gaps")
ZERO_SHA = "0" * 40


def check_immutable(repo: Path, base: str, head: str = "HEAD") -> list[str]:
    """Return one message per protected path changed in any way other than added."""
    if not base or set(base) == {"0"}:
        return []  # first push of a branch: nothing to compare against
    out = subprocess.run(
        ["git", "diff", "--name-status", "--no-renames", base, head, "--", *PROTECTED],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout
    violations = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if status != "A":
            violations.append(f"{path}: {status} (protected files may only be added)")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    violations = check_immutable(Path(args.repo), args.base, args.head)
    for v in violations:
        print(f"IMMUTABILITY VIOLATION: {v}", file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
