"""EIA-930 hourly electricity demand (v2 API): daily peak per local day."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from ftracker.daily import aggregate_local_days
from ftracker.series import SourceError
from ftracker.sources import get_json
from ftracker.sources.openmeteo import _mask_unfinished

URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
PAGE_LENGTH = 5000  # the API returns at most 5000 rows per request


def _redact(text: str, api_key: str) -> str:
    return text.replace(api_key, "***") if api_key else text


def _rows(api_key: str, respondent: str, start: date, end: date) -> list[dict]:
    """All hourly demand rows for the UTC window, following offset paging."""
    params = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": respondent,
        "facets[type][]": "D",  # demand
        "start": f"{start.isoformat()}T00",
        "end": f"{end.isoformat()}T23",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": PAGE_LENGTH,
    }
    rows: list[dict] = []
    while True:
        try:
            payload = get_json(URL, {**params, "offset": len(rows)})
        except SourceError as exc:
            # requests puts the full URL, query string included, in its messages: never leak the key.
            raise SourceError(_redact(str(exc), api_key)) from None
        try:
            resp = payload["response"]
            page = resp["data"]
            total = int(resp.get("total", len(page)))
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceError(f"EIA response has unexpected shape: {type(exc).__name__}") from None
        rows.extend(page)
        if not page or len(rows) >= total:
            return rows


def fetch_eia_demand(api_key: str, respondent: str, tz: str, start: date, end: date,
                     *, today: date | None = None) -> pd.Series:
    """Daily peak hourly demand (MW) per local day, start..end inclusive.

    A local day needs all of its hours; otherwise it is NaN, as are today and later days.
    """
    today = today or datetime.now(ZoneInfo(tz)).date()
    # pad one UTC day each side so edge local days are fully covered
    rows = _rows(api_key, respondent, start - timedelta(days=1), end + timedelta(days=1))
    full = pd.Index([start + timedelta(days=i) for i in range((end - start).days + 1)])
    try:
        times = pd.to_datetime([r["period"] for r in rows], format="%Y-%m-%dT%H", utc=True)
        vals = [float("nan") if r.get("value") in (None, "") else float(r["value"]) for r in rows]
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"EIA row has unexpected shape: {type(exc).__name__}") from None
    hourly = pd.Series(vals, index=times, dtype=float)
    if hourly.empty:
        daily = pd.Series(dtype=float)
    else:
        daily = aggregate_local_days(hourly, tz, "max")
    return _mask_unfinished(daily.reindex(full).astype(float), today)
