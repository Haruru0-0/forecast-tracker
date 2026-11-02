"""USGS instantaneous values (15-minute readings) aggregated to a daily mean per local day.

The daily-values service lags by several days, so the instantaneous-values service is used.
Rule: readings are averaged into hourly means (an hour needs at least one valid reading), then
a local day is the mean of its hourly means and needs every hour (see aggregate_local_days).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from ftracker.daily import aggregate_local_days
from ftracker.series import SourceError
from ftracker.sources import get_json
from ftracker.sources.openmeteo import _mask_unfinished

URL = "https://waterservices.usgs.gov/nwis/iv/"
CHUNK_DAYS = 30  # the instantaneous service limits the range per request; stay well inside it
NO_DATA = -999999.0
BAD_QUALIFIERS = {"Ice", "Eqp", "Ssn", "Mnt", "Dis", "Bkw", "Zfl", "Rat", "Fld"}  # ice, equipment, etc.


def _readings(payload: dict) -> list[tuple[str, float]]:
    try:
        series = payload["value"]["timeSeries"]
        out = []
        for ts in series:
            for block in ts["values"]:
                for r in block["value"]:
                    out.append((r["dateTime"], _number(r["value"], r.get("qualifiers") or [])))
        return out
    except (KeyError, TypeError) as exc:
        raise SourceError(f"USGS response has unexpected shape: {type(exc).__name__}") from None


def _number(raw, qualifiers) -> float:
    """NaN for empty, non-numeric (e.g. "Ice"), sentinel or flagged readings."""
    if BAD_QUALIFIERS.intersection(qualifiers):
        return float("nan")
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return float("nan")
    return float("nan") if v == NO_DATA else v


def fetch_usgs(site: str, parameter: str, tz: str, start: date, end: date,
               *, today: date | None = None) -> pd.Series:
    """Daily mean of `parameter` per local day, start..end inclusive; incomplete days are NaN."""
    today = today or datetime.now(ZoneInfo(tz)).date()
    # pad one UTC day each side so edge local days are fully covered
    lo, hi = start - timedelta(days=1), end + timedelta(days=1)
    readings: list[tuple[str, float]] = []
    chunk_start = lo
    while chunk_start <= hi:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS - 1), hi)
        payload = get_json(URL, {
            "format": "json", "sites": site, "parameterCd": parameter,
            "startDT": f"{chunk_start.isoformat()}T00:00Z",
            "endDT": f"{(chunk_end + timedelta(days=1)).isoformat()}T00:00Z",
        })
        readings.extend(_readings(payload))
        chunk_start = chunk_end + timedelta(days=1)
    full = pd.Index([start + timedelta(days=i) for i in range((end - start).days + 1)])
    if not readings:
        return pd.Series(float("nan"), index=full, dtype=float)
    try:
        times = pd.to_datetime([t for t, _ in readings], utc=True)
    except (ValueError, TypeError) as exc:
        raise SourceError(f"USGS timestamp unparseable: {type(exc).__name__}") from None
    raw = pd.Series([v for _, v in readings], index=times, dtype=float).sort_index()
    raw = raw[~raw.index.duplicated(keep="first")]
    hourly = raw.resample("1h").mean()  # NaN where an hour has no valid reading
    daily = aggregate_local_days(hourly, tz, "mean")
    return _mask_unfinished(daily.reindex(full).astype(float), today)
