"""Open-Meteo weather (daily max temperature) and air quality (daily mean US AQI)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from ftracker.daily import aggregate_local_days
from ftracker.series import SourceError
from ftracker.sources import get_json

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
ARCHIVE_LAG_DAYS = 2  # the archive trails today by about two days


def _daily_series(payload: dict, start: date, end: date) -> pd.Series:
    try:
        days = payload["daily"]["time"]
        vals = payload["daily"]["temperature_2m_max"]
    except KeyError as exc:
        raise SourceError(f"Open-Meteo response missing {exc}") from exc
    idx = [date.fromisoformat(d) for d in days]
    s = pd.Series([float("nan") if v is None else float(v) for v in vals], index=idx, dtype=float)
    return s[(s.index >= start) & (s.index <= end)]


def _mask_unfinished(s: pd.Series, today: date) -> pd.Series:
    """Today and later are not finished observations (the APIs serve forecasts there): NaN."""
    s = s.copy()
    s[[d >= today for d in s.index]] = float("nan")
    return s


def fetch_weather(lat: float, lon: float, tz: str, start: date, end: date,
                  *, today: date | None = None) -> pd.Series:
    """Daily maximum 2 m temperature (deg C) per local day, start..end inclusive.

    The archive covers up to today - ARCHIVE_LAG_DAYS; later days come from the forecast
    endpoint's past_days window. Archive values win where both exist.
    """
    today = today or datetime.now(ZoneInfo(tz)).date()
    archive_end = min(end, today - timedelta(days=ARCHIVE_LAG_DAYS))
    parts = []
    base = {"latitude": lat, "longitude": lon, "daily": "temperature_2m_max", "timezone": tz}
    if start <= archive_end:
        payload = get_json(ARCHIVE_URL, {**base, "start_date": start.isoformat(),
                                         "end_date": archive_end.isoformat()})
        parts.append(_daily_series(payload, start, archive_end))
    recent_start = max(start, archive_end + timedelta(days=1))
    if recent_start <= end:
        payload = get_json(FORECAST_URL, {**base, "past_days": max((today - recent_start).days, 0),
                                          "forecast_days": 1})
        parts.append(_daily_series(payload, recent_start, end))
    full = pd.Index([start + timedelta(days=i) for i in range((end - start).days + 1)])
    out = pd.concat(parts) if parts else pd.Series(dtype=float)
    out = out[~out.index.duplicated(keep="first")]
    return _mask_unfinished(out.reindex(full).astype(float), today)


def fetch_air_quality(lat: float, lon: float, tz: str, start: date, end: date,
                      *, today: date | None = None) -> pd.Series:
    """Daily mean US AQI per local day; days lacking any hour, and today or later, are NaN."""
    today = today or datetime.now(ZoneInfo(tz)).date()
    params = {"latitude": lat, "longitude": lon, "hourly": "us_aqi", "timezone": "GMT",
              # pad one UTC day each side so edge local days are fully covered
              "start_date": (start - timedelta(days=1)).isoformat(),
              "end_date": (end + timedelta(days=1)).isoformat()}
    payload = get_json(AIR_URL, params)
    try:
        times = pd.to_datetime(payload["hourly"]["time"], utc=True)
        vals = payload["hourly"]["us_aqi"]
    except KeyError as exc:
        raise SourceError(f"Open-Meteo response missing {exc}") from exc
    hourly = pd.Series([float("nan") if v is None else float(v) for v in vals], index=times, dtype=float)
    daily = aggregate_local_days(hourly, tz, "mean")
    full = pd.Index([start + timedelta(days=i) for i in range((end - start).days + 1)])
    return _mask_unfinished(daily.reindex(full).astype(float), today)
