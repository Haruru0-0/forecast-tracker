import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest
import responses

from ftracker.series import SourceError
from ftracker.sources import openmeteo

FIX = Path(__file__).parent / "fixtures"
TZ = "America/Chicago"
LAT, LON = 29.76, -95.37


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


@responses.activate
def test_weather_returns_daily_series_indexed_by_date():
    responses.add(responses.GET, openmeteo.ARCHIVE_URL, json=_load("openmeteo_weather.json"))
    s = openmeteo.fetch_weather(LAT, LON, TZ, date(2026, 10, 27), date(2026, 10, 31),
                                today=date(2026, 11, 20))
    assert list(s.index) == [date(2026, 10, d) for d in range(27, 32)]
    assert s.loc[date(2026, 10, 28)] == 27.1
    assert s.dtype == float


@responses.activate
def test_weather_merges_archive_with_recent_forecast_endpoint():
    responses.add(responses.GET, openmeteo.ARCHIVE_URL, json=_load("openmeteo_weather.json"))
    responses.add(responses.GET, openmeteo.FORECAST_URL, json=_load("openmeteo_weather_recent.json"))
    # today = 2026-11-02: archive covers through 10-31, recent covers 11-01 on.
    s = openmeteo.fetch_weather(LAT, LON, TZ, date(2026, 10, 29), date(2026, 11, 1),
                                today=date(2026, 11, 2))
    assert list(s.index) == [date(2026, 10, 29), date(2026, 10, 30), date(2026, 10, 31), date(2026, 11, 1)]
    assert list(s.values) == [28.3, 27.4, 27.8, 28.4]  # last value from the recent endpoint
    recent_call = [c for c in responses.calls if c.request.url.startswith(openmeteo.FORECAST_URL)][0]
    assert "past_days=" in recent_call.request.url


@responses.activate
def test_air_quality_uses_local_day_completeness():
    responses.add(responses.GET, openmeteo.AIR_URL, json=_load("openmeteo_air.json"))
    s = openmeteo.fetch_air_quality(LAT, LON, TZ, date(2026, 10, 30), date(2026, 11, 1))
    # Fixture spans 2026-10-30T00Z..2026-11-01T23Z. Chicago 10-30 and 10-31 are fully covered;
    # 11-01 (25 hours, ends 06Z on 11-02) is cut off at 23Z, so it is incomplete.
    assert not np.isnan(s.loc[date(2026, 10, 30)])
    assert not np.isnan(s.loc[date(2026, 10, 31)])
    assert np.isnan(s.loc[date(2026, 11, 1)])


@responses.activate
def test_http_failure_retries_then_raises_source_error():
    responses.add(responses.GET, openmeteo.AIR_URL, status=500)
    with pytest.raises(SourceError):
        openmeteo.fetch_air_quality(LAT, LON, TZ, date(2026, 10, 30), date(2026, 11, 1))
    assert len(responses.calls) == 3


@responses.activate
@pytest.mark.parametrize("end", [date(2026, 11, 2), date(2026, 11, 3)])
def test_weather_today_and_later_are_nan(end):
    responses.add(responses.GET, openmeteo.ARCHIVE_URL, json=_load("openmeteo_weather.json"))
    responses.add(responses.GET, openmeteo.FORECAST_URL, json=_load("openmeteo_weather_recent.json"))
    s = openmeteo.fetch_weather(LAT, LON, TZ, date(2026, 10, 31), end, today=date(2026, 11, 2))
    assert list(s.index)[-1] == end
    assert s.loc[date(2026, 11, 1)] == 28.4
    assert s.loc[date(2026, 11, 2):].isna().all()  # recorded forecast for 11-02 is 27.6; must not leak
    assert 27.6 not in s.values


@responses.activate
@pytest.mark.parametrize("end", [date(2026, 10, 31), date(2026, 11, 1)])
def test_air_quality_today_and_later_are_nan(end):
    responses.add(responses.GET, openmeteo.AIR_URL, json=_load("openmeteo_air.json"))
    # Chicago 10-31 is fully present in the fixture, but with today=10-31 it is not finished.
    s = openmeteo.fetch_air_quality(LAT, LON, TZ, date(2026, 10, 30), end, today=date(2026, 10, 31))
    assert not np.isnan(s.loc[date(2026, 10, 30)])
    assert s.loc[date(2026, 10, 31):].isna().all()
