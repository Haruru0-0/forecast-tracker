"""Regenerate the results block in README.md from results/scoreboard.csv.

Usage: python scripts/render_readme.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

START = "<!-- results:start -->"
END = "<!-- results:end -->"
ROOT = Path(__file__).resolve().parents[1]
HEADER = "| series | method | horizon | n | n missing | MAE (n) | coverage (n) | skill (n) |"


def _fmt(value: object, digits: int) -> str:
    return "-" if pd.isna(value) else f"{float(value):.{digits}f}"


def _with_n(value: object, digits: int, n: object) -> str:
    """A number with the sample count it rests on; '-' alone when there is no number."""
    return "-" if pd.isna(value) else f"{float(value):.{digits}f} (n={int(n)})"


def render_block(csv_path: Path) -> str:
    """Markdown for the results block, without the markers."""
    try:
        board = pd.read_csv(csv_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        board = pd.DataFrame()
    if board.empty:
        return "No scored forecasts yet."
    lines = [HEADER, "|---|---|---|---|---|---|---|---|"]
    for r in board.itertuples(index=False):
        lines.append(
            f"| {r.series} | {r.method} | {int(r.horizon)} | {int(r.n)} | {int(r.n_missing)} "
            f"| {_with_n(r.mae, 3, r.n)} | {_with_n(r.coverage, 2, r.n)} | {_fmt(r.skill, 2)} (n={int(r.n_skill)}) |"
        )
    return "\n".join(lines)


def replace_block(readme: str, block: str) -> str:
    start = readme.index(START) + len(START)
    end = readme.index(END)
    return f"{readme[:start]}\n{block}\n{readme[end:]}"


def main() -> int:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    new = replace_block(text, render_block(ROOT / "results" / "scoreboard.csv"))
    path.write_text(new, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
