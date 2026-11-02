import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest
import responses

from ftracker.series import SourceError
from ftracker.sources import usgs

FIX = Path(__file__).parent / "fixtures"
TZ = "America/Chicago"
TODAY = date(2026, 11, 20)


def _payload(readings):
    """readings: list of (ISO datetime with offset, value string, qualifiers)."""
    return {"value": {"timeSeries": [{"values": [{"value": [
        {"value": v, "qualifiers": q, "dateTime": t} for t, v, q in readings]}]}]}}


def _day_readings(value="100"):
    """Four readings per hour for local (CDT, -05:00) 2026-10-30."""
    return [(f"2026-10-30T{h:02d}:{m:02d}:00.000-05:00", value, ["P"])
            for h in range(24) for m in (0, 15, 30, 45)]


def _in_hour(t, hour):
    return t.startswith(f"2026-10-30T{hour:02d}:")


def _fetch(start=date(2026, 10, 30), end=date(2026, 10, 30), today=TODAY):
    return usgs.fetch_usgs("08074000", "00060", TZ, start, end, today=today)


@responses.activate
def test_usgs_real_fixture_parses():
    # Real (trimmed) USGS response: 96 fifteen-minute readings. It is a 24 h slice that is not aligned
    # to the local day, so the day is incomplete (NaN) -- the point is that the real shape parses.
    fx = json.loads((FIX / "usgs.json").read_text(encoding="utf-8"))
    responses.add(responses.GET, usgs.URL, json=fx)
    s = _fetch()
    assert list(s.index) == [date(2026, 10, 30)]
    assert s.dtype == float


@responses.activate
def test_usgs_real_fixture_values_are_used():
    fx = json.loads((FIX / "usgs.json").read_text(encoding="utf-8"))
    rows = fx["value"]["timeSeries"][0]["values"][0]["value"]
    # Re-label the real values onto one complete local day to check the mean-of-hourly-means maths.
    relabeled = [(f"2026-10-30T{i // 4:02d}:{(i % 4) * 15:02d}:00.000-05:00", r["value"], r["qualifiers"])
                 for i, r in enumerate(rows)]
    responses.add(responses.GET, usgs.URL, json=_payload(relabeled))
    expected = np.mean([np.mean([float(rows[h * 4 + k]["value"]) for k in range(4)]) for h in range(24)])
    assert _fetch().loc[date(2026, 10, 30)] == pytest.approx(expected)


@responses.activate
def test_usgs_complete_day_mean_and_request_shape():
    responses.add(responses.GET, usgs.URL, json=_payload(_day_readings("100")))
    assert _fetch().loc[date(2026, 10, 30)] == 100.0
    url = responses.calls[0].request.url
    assert "format=json" in url and "parameterCd=00060" in url and "sites=08074000" in url


@responses.activate
def test_usgs_hour_needs_only_one_reading():
    readings = [r for r in _day_readings("50") if not (_in_hour(r[0], 3) and not r[0].endswith("03:00:00.000-05:00"))]
    assert sum(_in_hour(r[0], 3) for r in readings) == 1
    responses.add(responses.GET, usgs.URL, json=_payload(readings))
    assert _fetch().loc[date(2026, 10, 30)] == 50.0


@responses.activate
def test_usgs_hour_with_no_reading_makes_day_nan():
    readings = [r for r in _day_readings() if not _in_hour(r[0], 3)]
    responses.add(responses.GET, usgs.URL, json=_payload(readings))
    assert np.isnan(_fetch().loc[date(2026, 10, 30)])


@responses.activate
def test_usgs_sentinel_is_nan():
    # Every reading in hour 3 is the no-data sentinel: that hour is missing, so the day is NaN.
    readings = [(t, "-999999", q) if _in_hour(t, 3) else (t, v, q) for t, v, q in _day_readings()]
    responses.add(responses.GET, usgs.URL, json=_payload(readings))
    assert np.isnan(_fetch().loc[date(2026, 10, 30)])


@responses.activate
def test_usgs_sentinel_is_not_averaged_in():
    readings = _day_readings("100")
    readings[0] = (readings[0][0], "-999999.0", ["P"])  # one bad reading among four in hour 0
    responses.add(responses.GET, usgs.URL, json=_payload(readings))
    assert _fetch().loc[date(2026, 10, 30)] == 100.0


@responses.activate
@pytest.mark.parametrize("bad,quals", [("", ["P"]), ("Ice", ["P"]), ("Eqp", ["P"]), ("55", ["P", "Ice"])])
def test_usgs_non_numeric_or_flagged_value_is_nan(bad, quals):
    readings = [(t, bad, quals) if _in_hour(t, 3) else (t, v, q) for t, v, q in _day_readings()]
    responses.add(responses.GET, usgs.URL, json=_payload(readings))
    assert np.isnan(_fetch().loc[date(2026, 10, 30)])


@responses.activate
def test_usgs_no_time_series_returns_all_nan():
    responses.add(responses.GET, usgs.URL, json={"value": {"timeSeries": []}})
    s = _fetch(end=date(2026, 10, 31))
    assert list(s.index) == [date(2026, 10, 30), date(2026, 10, 31)]
    assert s.isna().all()


@responses.activate
def test_usgs_chunks_long_ranges_and_merges():
    # 91 days -> several windows; only the last one has data.
    for _ in range(3):
        responses.add(responses.GET, usgs.URL, json={"value": {"timeSeries": []}})
    responses.add(responses.GET, usgs.URL, json=_payload(_day_readings("100")))
    s = usgs.fetch_usgs("08074000", "00060", TZ, date(2026, 8, 1), date(2026, 10, 30), today=TODAY)
    assert len(responses.calls) == 4  # 91 days + 2 padding days = 93 -> ceil(93 / 30) windows
    starts = [c.request.url.split("startDT=")[1].split("&")[0] for c in responses.calls]
    assert len(set(starts)) == 4
    assert usgs.CHUNK_DAYS <= 60
    assert len(s) == 91 and s.loc[date(2026, 10, 30)] == 100.0
    assert s.drop(date(2026, 10, 30)).isna().all()


@responses.activate
def test_usgs_masks_today():
    responses.add(responses.GET, usgs.URL, json=_payload(_day_readings("100")))
    assert np.isnan(_fetch(today=date(2026, 10, 30)).loc[date(2026, 10, 30)])


@responses.activate
def test_usgs_malformed_payload_raises_source_error():
    responses.add(responses.GET, usgs.URL, json={"nope": 1})
    with pytest.raises(SourceError):
        _fetch()
