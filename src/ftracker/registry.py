"""The tracked series. Fetch closures read config and the environment at call time."""

from __future__ import annotations

import os
from datetime import date

import pandas as pd

from ftracker import config
from ftracker.series import Series, SourceError
from ftracker.sources import eia, openmeteo, usgs


def _weather(start: date, end: date) -> pd.Series:
    m = config.METRO
    return openmeteo.fetch_weather(m["lat"], m["lon"], m["tz"], start, end)


def _air_quality(start: date, end: date) -> pd.Series:
    m = config.METRO
    return openmeteo.fetch_air_quality(m["lat"], m["lon"], m["tz"], start, end)


def _electricity(start: date, end: date) -> pd.Series:
    key = os.environ.get("EIA_API_KEY")
    if not key:
        raise SourceError("EIA_API_KEY not set")
    m = config.METRO
    return eia.fetch_eia_demand(key, m["eia_respondent"], m["tz"], start, end)


def _river(start: date, end: date) -> pd.Series:
    m = config.METRO
    return usgs.fetch_usgs(m["usgs_site"], m["usgs_parameter"], m["tz"], start, end)


def _tz() -> str:
    return config.METRO["tz"]


SERIES: dict[str, Series] = {
    "weather": Series("weather_tmax", "degC", _tz(), _weather),
    "air_quality": Series("air_quality_aqi", "US AQI", _tz(), _air_quality),
    "electricity": Series("electricity_peak_mw", "MW", _tz(), _electricity),
    "river": Series("river_discharge_cfs", "ft3/s", _tz(), _river),
}
