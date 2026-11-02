"""Command line entry point: python -m ftracker.cli <command>."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ftracker.config import METRO
from ftracker.series import Series, SourceError
from ftracker.sources import openmeteo


def registry() -> list[Series]:
    """All registered series. Task 4 adds electricity demand and river level."""
    m = METRO
    return [
        Series("weather_tmax", "degC", m["tz"],
               lambda s, e: openmeteo.fetch_weather(m["lat"], m["lon"], m["tz"], s, e)),
        Series("air_quality_aqi", "US AQI", m["tz"],
               lambda s, e: openmeteo.fetch_air_quality(m["lat"], m["lon"], m["tz"], s, e)),
    ]


def check_sources(lookback_days: int = 10) -> int:
    """Print each series' most recent non-missing date. Returns 1 if any source fails."""
    failed = False
    for series in registry():
        today = datetime.now(ZoneInfo(series.tz)).date()
        try:
            data = series.fetch_daily(today - timedelta(days=lookback_days), today - timedelta(days=1)).dropna()
        except SourceError as exc:
            print(f"{series.name}: ERROR {exc}")
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
