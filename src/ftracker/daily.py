"""Aggregate hourly UTC values into complete local days."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


def _expected_hours(day, tz: str) -> int:
    zone = ZoneInfo(tz)
    start = datetime.combine(day, time.min, zone).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
    return round((end - start).total_seconds() / 3600)


def aggregate_local_days(hourly: pd.Series, tz: str, how: Literal["mean", "max"]) -> pd.Series:
    """Daily mean/max per local calendar day; days without every hour are NaN.

    A local day expects 23, 24 or 25 hours depending on DST. Missing (NaN) hourly values count as absent.
    """
    if how not in ("mean", "max"):
        raise ValueError(f"how must be 'mean' or 'max', got {how!r}")
    if not isinstance(hourly.index, pd.DatetimeIndex) or hourly.index.tz is None:
        raise ValueError("hourly must have a tz-aware (UTC) DatetimeIndex")
    present = hourly.dropna()
    present = present[~present.index.duplicated(keep="first")]
    if present.empty:
        return pd.Series(dtype=float)
    local_days = present.index.tz_convert(tz).date
    grouped = present.groupby(local_days)
    values = grouped.agg(how)
    counts = grouped.size()
    out = {}
    for day in values.index:
        ok = counts.loc[day] == _expected_hours(day, tz)
        out[day] = float(values.loc[day]) if ok else np.nan
    return pd.Series(out, dtype=float)
