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
