import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from ftracker import engine, store
from ftracker.series import Series, SourceError

ISSUE = date(2026, 11, 3)
NOW = datetime(2026, 11, 3, 6, 0, tzinfo=timezone.utc)


def make_series(name="s1", values=None, down=False, missing=(), poison_from=None, calls=None):
    """Fake series: value = day ordinal, NaN for `missing`, poison 9999 from `poison_from`."""
    calls = [] if calls is None else calls

    def fetch(start, end):
        calls.append((start, end))
        if down:
            raise SourceError("boom https://x.test/api?api_key=SECRET")
        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        vals = []
        for d in days:
            if d in missing:
                vals.append(np.nan)
            elif poison_from is not None and d >= poison_from:
                vals.append(9999.0)
            elif values is not None and d in values:
                vals.append(values[d])
            else:
                vals.append(float(d.toordinal() % 7))
        return pd.Series(vals, index=days, dtype=float)

    return Series(name, "u", "UTC", fetch)


class Stub:
    def __init__(self, name="stub"):
        self.name = name
        self.histories = []

    def forecast(self, history, target_dates):
        self.histories.append(history)
        return pd.DataFrame(
            {"point": 1.0, "lo": 0.5, "hi": 1.5},
            index=pd.Index(list(target_dates), name="target_date"),
        )


def test_forecast_uses_only_data_before_issue_date(tmp_path):
    stub = Stub()
    calls = []
    s = make_series(poison_from=ISSUE, calls=calls)
    engine.issue_forecasts(tmp_path, s, ISSUE, NOW, "r1", [stub])
    assert stub.histories[0].index.max() == ISSUE - timedelta(days=1)
    assert (stub.histories[0] < 9999).all()
    assert all(end < ISSUE for _, end in calls)


def test_issues_seven_horizons_with_expected_target_dates(tmp_path):
    n = engine.issue_forecasts(tmp_path, make_series(), ISSUE, NOW, "r1", [Stub("a"), Stub("b")])
    assert n == 14
    df = store.read_forecasts(tmp_path, "s1")
    one = df[df.method == "a"].sort_values("horizon")
    assert list(one.target_date) == [date(2026, 11, 4) + timedelta(days=i) for i in range(7)]
    assert list(one.horizon) == list(range(1, 8))
    doc = json.loads((tmp_path / "forecasts" / "s1" / "2026-11-03.json").read_text())
    assert doc["meta"]["run_id"] == "r1" and "issued_at" in doc["meta"]


def test_second_run_same_day_writes_nothing_and_does_not_fail(tmp_path):
    reg = {"s1": make_series()}
    r1 = engine.run_daily(tmp_path, reg, NOW, "r1", [Stub()])
    path = tmp_path / "forecasts" / "s1" / "2026-11-03.json"
    before = path.read_bytes()
    r2 = engine.run_daily(tmp_path, reg, NOW, "r2", [Stub()])
    assert r1.issued["s1"] == 7 and r2.issued["s1"] == 0
    assert r2.ok
    assert path.read_bytes() == before


def test_missing_yesterday_still_issues_from_last_observed(tmp_path):
    s = make_series(missing={ISSUE - timedelta(days=1)})
    engine.issue_forecasts(tmp_path, s, ISSUE, NOW, "r1", [Stub()])
    doc = json.loads((tmp_path / "forecasts" / "s1" / "2026-11-03.json").read_text())
    assert doc["meta"]["last_observed"] == (ISSUE - timedelta(days=2)).isoformat()


def test_stale_history_writes_gap(tmp_path):
    s = make_series(missing={ISSUE - timedelta(days=i) for i in range(1, 6)})
    report = engine.run_daily(tmp_path, {"s1": s}, NOW, "r1", [Stub()])
    gaps = store.read_gaps(tmp_path, "s1")
    assert gaps.reason.iloc[0] == f"history stale: last observed {ISSUE - timedelta(days=6)}"
    assert not report.ok and "s1" in report.failed
    assert store.read_forecasts(tmp_path, "s1").empty


def test_source_down_writes_gap_and_reports_failure(tmp_path):
    report = engine.run_daily(tmp_path, {"s1": make_series(down=True)}, NOW, "r1", [Stub()])
    assert not report.ok
    gaps = store.read_gaps(tmp_path, "s1")
    assert len(gaps) == 1
    assert "SECRET" not in gaps.reason.iloc[0] and "api_key" not in gaps.reason.iloc[0] and "?" not in gaps.reason.iloc[0]
    assert "SECRET" not in report.failed["s1"]


def test_one_failing_series_does_not_stop_the_others(tmp_path):
    reg = {"bad": make_series("bad", down=True), "good": make_series("good")}
    report = engine.run_daily(tmp_path, reg, NOW, "r1", [Stub()])
    assert set(report.failed) == {"bad"}
    assert report.issued["good"] == 7
    assert not store.read_forecasts(tmp_path, "good").empty


def test_all_sources_down_reports_failures_writes_gaps_and_updates_status(tmp_path):
    reg = {n: make_series(n, down=True) for n in ("a", "b")}
    report = engine.run_daily(tmp_path, reg, NOW, "r1", [Stub()])
    assert not report.ok
    for n in reg:
        assert len(store.read_gaps(tmp_path, n)) == 1
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["last_run"] == NOW.isoformat()
    assert set(status["series"]) == {"a", "b"}
    assert status["series"]["a"]["last_issue"] is None
    assert status["series"]["a"]["error"]


def test_status_keeps_last_issue_after_failed_run(tmp_path):
    engine.run_daily(tmp_path, {"s1": make_series()}, NOW, "r1", [Stub()])
    later = NOW + timedelta(days=1)
    engine.run_daily(tmp_path, {"s1": make_series(down=True)}, later, "r2", [Stub()])
    st = json.loads((tmp_path / "status.json").read_text())["series"]["s1"]
    assert st["last_issue"] == "2026-11-03" and st["error"]


def test_naive_now_rejected(tmp_path):
    with pytest.raises(ValueError):
        engine.run_daily(tmp_path, {"s1": make_series()}, datetime(2026, 11, 3, 6), "r1", [Stub()])


def _issue_then(tmp_path, s):
    engine.issue_forecasts(tmp_path, s, ISSUE, NOW, "r1", [Stub()])


def test_outcome_scored_only_after_two_day_lag(tmp_path):
    s = make_series()
    _issue_then(tmp_path, s)
    assert engine.score_outcomes(tmp_path, s, date(2026, 11, 5), NOW) == 0
    assert engine.score_outcomes(tmp_path, s, date(2026, 11, 6), NOW) == 1
    out = store.read_outcomes(tmp_path, "s1")
    assert list(out.target_date) == [date(2026, 11, 4)]
    assert out.value.iloc[0] == float(date(2026, 11, 4).toordinal() % 7)


def test_missing_outcome_value_is_stored_as_null(tmp_path):
    s = make_series(missing={date(2026, 11, 4)})
    _issue_then(tmp_path, s)
    assert engine.score_outcomes(tmp_path, s, date(2026, 11, 6), NOW) == 1
    doc = json.loads((tmp_path / "outcomes" / "s1" / "2026-11-04.json").read_text())
    assert doc["value"] is None


def test_scoring_does_not_overwrite_existing_outcome(tmp_path):
    s = make_series()
    _issue_then(tmp_path, s)
    store.write_outcome(tmp_path, "s1", date(2026, 11, 4), 42.0, NOW)
    path = tmp_path / "outcomes" / "s1" / "2026-11-04.json"
    before = path.read_bytes()
    assert engine.score_outcomes(tmp_path, s, date(2026, 11, 6), NOW) == 0
    assert path.read_bytes() == before


def test_scoring_source_error_fails_series_but_not_others(tmp_path):
    good = make_series("good")
    bad = make_series("bad")
    _issue_then(tmp_path, bad)
    engine.issue_forecasts(tmp_path, good, ISSUE, NOW, "r1", [Stub()])
    bad_down = make_series("bad", down=True)
    later = datetime(2026, 11, 8, 6, tzinfo=timezone.utc)
    report = engine.run_daily(tmp_path, {"bad": bad_down, "good": good}, later, "r2", [Stub()])
    assert "bad" in report.failed and "good" not in report.failed
    assert report.scored["good"] > 0


class Boom(Stub):
    def forecast(self, history, target_dates):
        raise RuntimeError("lightgbm exploded")


def test_unexpected_forecaster_error_writes_gap_and_fails(tmp_path):
    report = engine.run_daily(tmp_path, {"s1": make_series()}, NOW, "r1", [Boom()])
    assert not report.ok
    gaps = store.read_gaps(tmp_path, "s1")
    assert len(gaps) == 1 and gaps.reason.iloc[0].startswith("RuntimeError: lightgbm exploded")
    assert store.read_forecasts(tmp_path, "s1").empty


def test_retry_after_gap_reports_gap_in_status_but_stays_ok(tmp_path):
    engine.run_daily(tmp_path, {"s1": make_series(down=True)}, NOW, "r1", [Stub()])
    report = engine.run_daily(tmp_path, {"s1": make_series()}, NOW, "r2", [Stub()])
    assert report.ok and report.issued["s1"] == 0
    err = json.loads((tmp_path / "status.json").read_text())["series"]["s1"]["error"]
    assert err.startswith("today's issue is a gap: ")
    assert "SECRET" not in err


def test_safe_strips_schemeless_query_string(tmp_path):
    def fetch(start, end):
        raise SourceError("url: /v2/x?frequency=daily&api_key=SECRET")

    s = Series("s1", "u", "UTC", fetch)
    report = engine.run_daily(tmp_path, {"s1": s}, NOW, "r1", [Stub()])
    gap = store.read_gaps(tmp_path, "s1").reason.iloc[0]
    status = (tmp_path / "status.json").read_text()
    for text in (gap, report.failed["s1"], status):
        assert "SECRET" not in text and "api_key" not in text


def test_stale_boundary_lead_10_issues_lead_11_gaps(tmp_path):
    ok_series = make_series("ok", missing={ISSUE - timedelta(days=i) for i in (1, 2)})
    assert engine.issue_forecasts(tmp_path, ok_series, ISSUE, NOW, "r", [Stub()]) == 7
    stale = make_series("stale", missing={ISSUE - timedelta(days=i) for i in (1, 2, 3)})
    with pytest.raises(engine.StaleHistory):
        engine.issue_forecasts(tmp_path, stale, ISSUE, NOW, "r", [Stub()])
    assert store.read_gaps(tmp_path, "stale").reason.iloc[0].startswith("history stale")


def test_registry_key_differs_from_series_name(tmp_path):
    report = engine.run_daily(tmp_path, {"weather": make_series("weather_tmax")}, NOW, "r1", [Stub()])
    assert (tmp_path / "forecasts" / "weather_tmax" / "2026-11-03.json").exists()
    assert not (tmp_path / "forecasts" / "weather").exists()
    assert set(report.issued) == {"weather_tmax"}
    assert set(json.loads((tmp_path / "status.json").read_text())["series"]) == {"weather_tmax"}


def test_score_outcomes_rejects_naive_now(tmp_path):
    with pytest.raises(ValueError):
        engine.score_outcomes(tmp_path, make_series(), date(2026, 11, 6), datetime(2026, 11, 6))


def test_default_forecasters_end_to_end(tmp_path):
    import time

    start = ISSUE - timedelta(days=800)
    vals = {start + timedelta(days=i): 10.0 + (i % 7) + 0.01 * i for i in range(801)}
    s = make_series("syn", values=vals)
    t0 = time.time()
    report = engine.run_daily(tmp_path, {"syn": s}, NOW, "r1")
    assert report.ok and report.issued["syn"] == 21
    df = store.read_forecasts(tmp_path, "syn")
    assert set(df.method) == {"seasonal_naive", "persistence", "model"} and len(df) == 21
    assert ((df.lo <= df.point) & (df.point <= df.hi)).all()
    assert time.time() - t0 < 30


class Negative(Stub):
    """Returns values below zero so the physical floor must be applied."""

    def forecast(self, history, target_dates):
        n = len(target_dates)
        return pd.DataFrame(
            {"point": [-1.0] * (n - 1) + [2.0], "lo": [-2.0] * (n - 1) + [1.0], "hi": [-0.5] * (n - 2) + [0.5, 3.0]},
            index=pd.Index(list(target_dates), name="target_date"),
        )


def test_lower_bound_clips_point_lo_and_keeps_order(tmp_path):
    base = make_series()
    s = Series("s1", "u", "UTC", base.fetch_daily, lower_bound=0.0)
    engine.issue_forecasts(tmp_path, s, ISSUE, NOW, "r1", [Negative()])
    df = store.read_forecasts(tmp_path, "s1").sort_values("horizon")
    assert (df.point >= 0).all() and (df.lo >= 0).all()
    assert ((df.lo <= df.point) & (df.point <= df.hi)).all()
    assert list(df.point) == [0.0] * 6 + [2.0]
    assert list(df.hi) == [0.0] * 5 + [0.5, 3.0]
    assert df.lo.iloc[-1] == 1.0  # values above the floor are left alone


def test_no_lower_bound_leaves_values_alone(tmp_path):
    engine.issue_forecasts(tmp_path, make_series(), ISSUE, NOW, "r1", [Negative()])
    df = store.read_forecasts(tmp_path, "s1").sort_values("horizon")
    assert df.point.iloc[0] == -1.0 and df.lo.iloc[0] == -2.0
