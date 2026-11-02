"""Command line entry point: python -m ftracker.cli <command>."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ftracker.engine import run_daily
from ftracker.registry import SERIES


def check_sources(lookback_days: int = 10) -> int:
    """Print each series' most recent non-missing date. Returns 1 if any source fails."""
    failed = False
    for series in SERIES.values():
        today = datetime.now(ZoneInfo(series.tz)).date()
        try:
            data = series.fetch_daily(today - timedelta(days=lookback_days), today - timedelta(days=1)).dropna()
        except Exception as exc:  # one broken series must never end the loop; type and message only
            print(f"{series.name}: ERROR {type(exc).__name__}: {exc}")
            failed = True
            continue
        latest = data.index.max() if len(data) else None
        print(f"{series.name} ({series.unit}): latest {latest if latest else 'none'}")
        failed = failed or latest is None
    return 1 if failed else 0


def daily(data_dir: Path) -> int:
    """Issue and score forecasts for every series. Returns 1 if any series failed."""
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    report = run_daily(Path(data_dir), SERIES, datetime.now(timezone.utc), run_id)
    for name in report.issued:
        line = f"{name}: issued {report.issued[name]}, scored {report.scored.get(name, 0)}"
        if name in report.failed:
            line += f", FAILED {report.failed[name]}"
        print(line)
    for name, why in report.failed.items():
        if name not in report.issued:
            print(f"{name}: FAILED {why}")
    return 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ftracker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-sources")
    daily_cmd = sub.add_parser("daily", help="issue and score today's forecasts")
    daily_cmd.add_argument("--data-dir", default="data", help="data directory (default: data)")
    site_cmd = sub.add_parser("site", help="build the static scoreboard page and results/scoreboard.csv")
    site_cmd.add_argument("--data-dir", default="data", help="data directory (default: data)")
    site_cmd.add_argument("--results-dir", default="results", help="results directory (default: results)")
    site_cmd.add_argument("--out", default="site", help="output directory (default: site)")
    args = parser.parse_args(argv)
    if args.command == "check-sources":
        return check_sources()
    if args.command == "daily":
        return daily(Path(args.data_dir))
    if args.command == "site":
        from ftracker.site import all_scoreboards, build_site

        names = [s.name for s in SERIES.values()]
        print(build_site(Path(args.data_dir), Path(args.out), datetime.now(timezone.utc), names))
        results = Path(args.results_dir)
        results.mkdir(parents=True, exist_ok=True)
        all_scoreboards(Path(args.data_dir), names).to_csv(results / "scoreboard.csv", index=False)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
