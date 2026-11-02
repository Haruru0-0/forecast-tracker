"""Series registry types shared by all data sources."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import pandas as pd


class SourceError(Exception):
    """A data source failed after retries or returned unusable data."""


@dataclass(frozen=True)
class Series:
    name: str
    unit: str
    tz: str
    # fetch_daily(start, end): floats indexed by datetime.date, both ends inclusive, NaN where missing.
    fetch_daily: Callable[[date, date], pd.Series]
    # Physical floor (for example 0 for a flow or a demand); None when the quantity has none.
    lower_bound: float | None = None


def apply_floor(frame: pd.DataFrame, floor: float | None) -> pd.DataFrame:
    """Clip point and lo at ``floor``, then raise hi to point where needed, so lo <= point <= hi.

    NaN stays NaN. Returns a new frame; ``frame`` is not changed."""
    out = frame.copy()
    if floor is None:
        return out
    out["point"] = out["point"].astype(float).clip(lower=floor)
    out["lo"] = out["lo"].astype(float).clip(lower=floor)
    out["hi"] = out["hi"].astype(float)
    low_hi = out["hi"] < out["point"]
    out.loc[low_hi, "hi"] = out.loc[low_hi, "point"]
    return out
