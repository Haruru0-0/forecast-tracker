from datetime import date

import pandas as pd

from ftracker import config, registry
from ftracker.series import Series
from ftracker.sources import usgs


def test_registry_has_four_series_with_expected_names_and_tz():
    assert set(registry.SERIES) == {"weather", "air_quality", "electricity", "river"}
    assert all(isinstance(s, Series) for s in registry.SERIES.values())
    assert {k: s.name for k, s in registry.SERIES.items()} == {
        "weather": "weather_tmax", "air_quality": "air_quality_aqi",
        "electricity": "electricity_peak_mw", "river": "river_discharge_cfs"}
    assert all(s.tz == "America/Chicago" for s in registry.SERIES.values())


def test_registry_reads_config_at_call_time(monkeypatch):
    seen = {}

    def fake(site, parameter, tz, start, end):
        seen["site"] = site
        return pd.Series(dtype=float)

    monkeypatch.setattr(usgs, "fetch_usgs", fake)
    monkeypatch.setitem(config.METRO, "usgs_site", "99999999")
    registry.SERIES["river"].fetch_daily(date(2026, 10, 1), date(2026, 10, 2))
    assert seen["site"] == "99999999"
