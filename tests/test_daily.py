from datetime import date

import numpy as np
import pandas as pd
import pytest

from ftracker.daily import aggregate_local_days

TZ = "America/Chicago"


def _hourly(local_start: str, n: int, values=None) -> pd.Series:
    start = pd.Timestamp(local_start, tz=TZ).tz_convert("UTC")
    idx = pd.date_range(start, periods=n, freq="h")
    return pd.Series(np.arange(n, dtype=float) if values is None else values, index=idx)


def test_complete_day_is_aggregated():
    out = aggregate_local_days(_hourly("2026-06-01", 24), TZ, "mean")
    assert out.loc[date(2026, 6, 1)] == 11.5


def test_missing_hour_makes_day_nan():
    s = _hourly("2026-06-01", 24).drop(pd.Timestamp("2026-06-01 10:00", tz=TZ).tz_convert("UTC"))
    out = aggregate_local_days(s, TZ, "mean")
    assert np.isnan(out.loc[date(2026, 6, 1)])


def test_spring_forward_day_has_23_hours_and_is_valid():
    s = _hourly("2026-03-08", 23)
    out = aggregate_local_days(s, TZ, "mean")
    assert out.loc[date(2026, 3, 8)] == 11.0


def test_fall_back_day_has_25_hours_and_is_valid():
    s = _hourly("2026-11-01", 25)
    out = aggregate_local_days(s, TZ, "mean")
    assert out.loc[date(2026, 11, 1)] == 12.0


def test_max_and_mean_modes():
    s = _hourly("2026-06-01", 24, values=[1.0] * 23 + [25.0])
    assert aggregate_local_days(s, TZ, "max").loc[date(2026, 6, 1)] == 25.0
    assert aggregate_local_days(s, TZ, "mean").loc[date(2026, 6, 1)] == 2.0


def test_24_values_on_25_hour_day_is_nan():
    s = _hourly("2026-11-01", 24)
    assert np.isnan(aggregate_local_days(s, TZ, "mean").loc[date(2026, 11, 1)])


def test_24_values_from_midnight_on_23_hour_day_is_not_a_full_24_hour_day():
    # 24 hours from local midnight on the spring-forward day: 23 land on 03-08 (valid, the real
    # length) and the 24th spills into 03-09, which is incomplete.
    out = aggregate_local_days(_hourly("2026-03-08", 24), TZ, "mean")
    assert out.loc[date(2026, 3, 8)] == 11.0
    assert np.isnan(out.loc[date(2026, 3, 9)])


def test_22_values_on_23_hour_day_is_nan():
    out = aggregate_local_days(_hourly("2026-03-08", 22), TZ, "mean")
    assert np.isnan(out.loc[date(2026, 3, 8)])


def test_hourly_nan_makes_day_nan():
    vals = [1.0] * 24
    vals[5] = np.nan
    out = aggregate_local_days(_hourly("2026-06-01", 24, values=vals), TZ, "mean")
    assert np.isnan(out.loc[date(2026, 6, 1)])


def test_empty_series_returns_empty_series():
    empty = pd.Series([], index=pd.DatetimeIndex([], tz="UTC"), dtype=float)
    assert aggregate_local_days(empty, TZ, "mean").empty


def test_tz_naive_input_raises_value_error():
    s = pd.Series([1.0], index=pd.DatetimeIndex(["2026-06-01 00:00"]))
    with pytest.raises(ValueError):
        aggregate_local_days(s, TZ, "mean")
