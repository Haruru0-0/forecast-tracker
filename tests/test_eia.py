"""EIA fixtures are HAND-BUILT from the documented v2 response format (no API key was available)."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest
import responses

from ftracker import registry
from ftracker.series import SourceError
from ftracker.sources import eia

FIX = Path(__file__).parent / "fixtures"
TZ = "America/Chicago"
KEY = "SECRET-KEY-123"
TODAY = date(2026, 11, 20)


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _fetch(start=date(2026, 10, 30), end=date(2026, 10, 31), today=TODAY):
    return eia.fetch_eia_demand(KEY, "ERCO", TZ, start, end, today=today)


def test_eia_missing_key_raises_without_network(monkeypatch):
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    with responses.RequestsMock():  # nothing registered: any request fails the test
        with pytest.raises(SourceError, match="EIA_API_KEY not set"):
            registry.SERIES["electricity"].fetch_daily(date(2026, 10, 30), date(2026, 10, 31))


@responses.activate
def test_eia_collects_all_pages(monkeypatch):
    # Fixture: 72 hourly rows, 2026-10-30T00Z..2026-11-01T23Z; page 1 holds 48, page 2 the other 24.
    monkeypatch.setattr(eia, "PAGE_LENGTH", 48)
    responses.add(responses.GET, eia.URL, json=_load("eia_page1.json"))
    responses.add(responses.GET, eia.URL, json=_load("eia_page2.json"))
    s = _fetch(end=date(2026, 11, 1))
    assert len(responses.calls) == 2
    assert "offset=0" in responses.calls[0].request.url
    assert "offset=48" in responses.calls[1].request.url
    assert "length=48" in responses.calls[0].request.url
    assert f"api_key={KEY}" in responses.calls[0].request.url
    # Oct 30 and Oct 31 local days lie entirely in page 1; Nov 1 (25 h, DST ends) is cut off at 23Z.
    assert s.loc[date(2026, 10, 30)] == 40280.0
    assert s.loc[date(2026, 10, 31)] == 40520.0
    assert np.isnan(s.loc[date(2026, 11, 1)])


@responses.activate
def test_eia_rows_from_second_page_are_used(monkeypatch):
    monkeypatch.setattr(eia, "PAGE_LENGTH", 48)
    p1, p2 = _load("eia_page1.json"), _load("eia_page2.json")
    # Move the Oct 31 rows into page 2 only: the day is complete only if page 2 was fetched.
    keep = [r for r in p1["response"]["data"] if r["period"] <= "2026-10-31T04"]
    rest = [r for r in p1["response"]["data"] if r["period"] > "2026-10-31T04"]
    p1["response"]["data"] = keep[:24]
    p1["response"]["total"] = str(len(keep))
    p2["response"]["data"] = keep[24:]
    p2["response"]["total"] = str(len(keep))
    assert rest  # sanity: fixture had extra rows we dropped
    monkeypatch.setattr(eia, "PAGE_LENGTH", 24)
    responses.add(responses.GET, eia.URL, json=p1)
    responses.add(responses.GET, eia.URL, json=p2)
    s = _fetch(end=date(2026, 10, 30))
    assert len(responses.calls) == 2
    assert s.loc[date(2026, 10, 30)] == 40280.0  # hour 28 (last row of the day) sits on page 2


@responses.activate
def test_eia_peak_is_max_per_local_day():
    rows = []
    for h in range(24):  # Chicago 2026-10-30 = 05Z .. 04Z next day
        utc = 5 + h
        period = f"2026-10-30T{utc:02d}" if utc < 24 else f"2026-10-31T{utc - 24:02d}"
        rows.append({"period": period, "respondent": "ERCO", "type": "D",
                     "value": "60000" if h == 10 else "40000"})
    responses.add(responses.GET, eia.URL, json={"response": {"total": "24", "data": rows}})
    s = _fetch(end=date(2026, 10, 30))
    assert s.loc[date(2026, 10, 30)] == 60000.0


@responses.activate
def test_eia_empty_response_returns_all_nan_for_range():
    responses.add(responses.GET, eia.URL, json={"response": {"total": "0", "data": []}})
    s = _fetch(start=date(2026, 10, 28), end=date(2026, 10, 31))
    assert list(s.index) == [date(2026, 10, d) for d in range(28, 32)]
    assert s.isna().all()
    assert s.dtype == float


@responses.activate
def test_eia_masks_today_and_later():
    responses.add(responses.GET, eia.URL, json=_load("eia_page1.json"))
    s = _fetch(today=date(2026, 10, 31))
    assert s.loc[date(2026, 10, 30)] == 40280.0
    assert np.isnan(s.loc[date(2026, 10, 31)])


@responses.activate
def test_eia_error_never_leaks_key():
    responses.add(responses.GET, eia.URL, status=403)
    with pytest.raises(SourceError) as ei:
        _fetch()
    assert KEY not in str(ei.value)


@responses.activate
def test_eia_malformed_payload_raises_source_error():
    responses.add(responses.GET, eia.URL, json={"error": "bad"})
    with pytest.raises(SourceError):
        _fetch()


def _peak_day_rows(skip_hour=None, null_hour=None, value_at=None):
    """24 rows for Chicago 2026-10-30 (05Z .. 04Z next day); hour 10 is the 60000 spike."""
    rows = []
    for h in range(24):
        if h == skip_hour:
            continue
        utc = 5 + h
        period = f"2026-10-30T{utc:02d}" if utc < 24 else f"2026-10-31T{utc - 24:02d}"
        value = "60000" if h == 10 else "40000"
        if h == null_hour:
            value = None
        if value_at and h in value_at:
            value = value_at[h]
        rows.append({"period": period, "respondent": "ERCO", "type": "D", "value": value})
    return rows


def _serve(rows, total=None):
    resp = {"data": rows}
    if total is not None:
        resp["total"] = str(total)
    responses.add(responses.GET, eia.URL, json={"response": resp})


@responses.activate
def test_eia_day_with_missing_hour_is_nan_not_partial_peak():
    _serve(_peak_day_rows(skip_hour=20), total=23)
    assert np.isnan(_fetch(end=date(2026, 10, 30)).loc[date(2026, 10, 30)])


@responses.activate
def test_eia_day_with_null_value_is_nan_not_partial_peak():
    _serve(_peak_day_rows(null_hour=20), total=24)
    assert np.isnan(_fetch(end=date(2026, 10, 30)).loc[date(2026, 10, 30)])


@responses.activate
@pytest.mark.parametrize("bad", ["0", "-300"])
def test_eia_non_positive_demand_is_nan(bad):
    _serve(_peak_day_rows(value_at={20: bad}), total=24)
    assert np.isnan(_fetch(end=date(2026, 10, 30)).loc[date(2026, 10, 30)])


@responses.activate
def test_eia_duplicate_periods_keep_first():
    rows = _peak_day_rows()
    rows.append(dict(rows[10], value="99999"))  # duplicate of the spike hour, later row loses
    rows.append(dict(rows[0], value="70000"))
    _serve(rows, total=len(rows))
    assert _fetch(end=date(2026, 10, 30)).loc[date(2026, 10, 30)] == 60000.0


@responses.activate
def test_eia_pages_until_empty_when_total_missing(monkeypatch):
    monkeypatch.setattr(eia, "PAGE_LENGTH", 12)
    rows = _peak_day_rows()
    _serve(rows[:12])
    _serve(rows[12:])
    _serve([])
    s = _fetch(end=date(2026, 10, 30))
    assert len(responses.calls) == 3
    assert s.loc[date(2026, 10, 30)] == 60000.0
