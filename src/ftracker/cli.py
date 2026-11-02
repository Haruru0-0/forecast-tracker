"""Command line entry point: python -m ftracker.cli <command>."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ftracker.registry import SERIES
from ftracker.series import SourceError


def check_sources(lookback_days: int = 10) -> int:
    """Print each series' most recent non-missing date. Returns 1 if any source fails."""
    failed = False
    for series in SERIES.values():
        today = datetime.now(ZoneInfo(series.tz)).date()
        try:
            data = series.fetch_daily(today - timedelta(days=lookback_days), today - timedelta(days=1)).dropna()
        except (SourceError, ValueError, TypeError, KeyError) as exc:  # a bad payload must not end the loop
            print(f"{series.name}: ERROR {type(exc).__name__}: {exc}")
            failed = True
            continue
        latest = data.index.max() if len(data) else None
        print(f"{series.name} ({series.unit}): latest {latest if latest else 'none'}")
        failed = failed or latest is None
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ftracker")
    parser.add_argument("command", choices=["check-sources"])
    args = parser.parse_args(argv)
    if args.command == "check-sources":
        return check_sources()
    return 2


if __name__ == "__main__":
    sys.exit(main())
