from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from ftracker.models import GBMForecaster, InsufficientHistory, Persistence, SeasonalNaive

START = date(2025, 1, 1)


def make_series(n=400, seed=0, noise=0.5):
    rng = np.random.default_rng(seed)
    days = [START + timedelta(days=i) for i in range(n)]
    vals = 10 + 5 * np.sin(2 * np.pi * np.arange(n) / 7) + rng.normal(0, noise, n)
    return pd.Series(vals, index=days, name="y")


def all_forecasters():
    return [SeasonalNaive(), Persistence(), GBMForecaster()]


def test_names():
    assert [f.name for f in all_forecasters()] == ["seasonal_naive", "persistence", "model"]


def test_persistence_point_is_last_value():
    s = make_series(100)
    origin = s.index[-1]
    out = Persistence().forecast(s, [origin + timedelta(days=2), origin + timedelta(days=8)])
    assert out.index.name == "target_date"
    assert list(out.columns) == ["point", "lo", "hi"]
    assert out["point"].tolist() == [s.iloc[-1], s.iloc[-1]]


def test_persistence_ignores_trailing_nan():
    s = make_series(100)
    last_valid = s.iloc[-3]
    s.iloc[-2:] = np.nan
    origin = s.index[-3]
    out = Persistence().forecast(s, [origin + timedelta(days=3)])
    assert out["point"].iloc[0] == last_valid


def test_seasonal_naive_uses_same_weekday():
    s = make_series(100)
    origin = s.index[-1]
    for lead in (2, 8):
        target = origin + timedelta(days=lead)
        out = SeasonalNaive().forecast(s, [target])
        expected_day = target - timedelta(days=7 * ((lead + 6) // 7))
        assert expected_day <= origin and expected_day.weekday() == target.weekday()
        assert out["point"].iloc[0] == s[expected_day]


def test_seasonal_naive_skips_missing_same_weekday():
    s = make_series(100)
    origin = s.index[-1]
    target = origin + timedelta(days=2)
    same = target - timedelta(days=7)
    s[same] = np.nan
    out = SeasonalNaive().forecast(s, [target])
    assert out["point"].iloc[0] == s[same - timedelta(days=7)]


@pytest.mark.parametrize("f", all_forecasters(), ids=lambda f: f.name)
def test_interval_orders(f):
    s = make_series(300)
    origin = s.index[-1]
    targets = [origin + timedelta(days=d) for d in range(2, 9)]
    out = f.forecast(s, targets)
    assert list(out.index) == targets
    assert (out["lo"] <= out["point"]).all() and (out["point"] <= out["hi"]).all()
    assert (out["hi"] > out["lo"]).all()


def test_nan_gaps_inside_history_are_allowed():
    s = make_series(300)
    s.iloc[[50, 120, 121, 200, 298]] = np.nan
    origin = s.index[-1]
    for f in all_forecasters():
        out = f.forecast(s, [origin + timedelta(days=2)])
        assert np.isfinite(out.to_numpy()).all()


def test_gbm_is_deterministic():
    s = make_series(300)
    t = [s.index[-1] + timedelta(days=d) for d in (1, 5)]
    a = GBMForecaster().forecast(s, t)
    b = GBMForecaster().forecast(s, t)
    pd.testing.assert_frame_equal(a, b)


def _backtest(f, s, n_held=60, lead=1):
    rows = []
    for i in range(n_held):
        cut = len(s) - n_held + i - lead + 1  # history length
        hist = s.iloc[:cut]
        target = s.index[cut - 1] + timedelta(days=lead)
        fc = f.forecast(hist, [target]).iloc[0]
        rows.append((s[target], fc["point"], fc["lo"], fc["hi"]))
    return pd.DataFrame(rows, columns=["y", "point", "lo", "hi"])


def test_interval_coverage_is_near_80_percent():
    s = make_series(400, seed=1)
    bt = _backtest(GBMForecaster(), s)
    coverage = ((bt["y"] >= bt["lo"]) & (bt["y"] <= bt["hi"])).mean()
    assert 0.65 <= coverage <= 0.95, coverage


def test_model_beats_persistence_on_weekly_pattern():
    s = make_series(400, seed=2)
    mae_model = (_backtest(GBMForecaster(), s)["point"] - s.iloc[-60:].to_numpy()).abs().mean()
    mae_pers = (_backtest(Persistence(), s)["point"] - s.iloc[-60:].to_numpy()).abs().mean()
    assert mae_model < mae_pers


def test_short_history_raises_insufficient_history():
    s = make_series(59)
    target = [s.index[-1] + timedelta(days=2)]
    for f in all_forecasters():
        with pytest.raises(InsufficientHistory):
            f.forecast(s, target)


def test_sixty_days_is_enough():
    s = make_series(60)
    target = [s.index[-1] + timedelta(days=2)]
    for f in all_forecasters():
        assert len(f.forecast(s, target)) == 1


def test_bad_leads_rejected():
    s = make_series(100)
    with pytest.raises(ValueError):
        Persistence().forecast(s, [s.index[-1]])
    with pytest.raises(ValueError):
        GBMForecaster().forecast(s, [s.index[-1] + timedelta(days=11)])


def test_gbm_tolerates_two_missing_days_before_the_engine_window():
    s = make_series(300)
    s.iloc[-2:] = np.nan
    origin = s.index[-3]
    targets = [origin + timedelta(days=d) for d in range(4, 11)]  # D+1..D+7, leads 4..10
    assert (targets[-1] - origin).days == 10
    out = GBMForecaster().forecast(s, targets)
    assert len(out) == 7 and np.isfinite(out.to_numpy()).all()
    assert (out["lo"] <= out["point"]).all() and (out["point"] <= out["hi"]).all()


def test_gbm_lead_11_and_lead_0_raise():
    s = make_series(100)
    with pytest.raises(ValueError, match="1..10"):
        GBMForecaster().forecast(s, [s.index[-1] + timedelta(days=11)])
    with pytest.raises(ValueError):
        GBMForecaster().forecast(s, [s.index[-1]])


def test_seasonal_naive_leads_7_and_14_boundaries():
    s = make_series(100)
    origin = s.index[-1]
    out = SeasonalNaive().forecast(s, [origin + timedelta(days=7), origin + timedelta(days=14)])
    assert out["point"].iloc[0] == s[origin]
    assert out["point"].iloc[1] == s[origin]
