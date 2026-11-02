from datetime import date, timedelta

import numpy as np
import pandas as pd

from ftracker import cli
from ftracker.backtest import COLUMNS, run_backtest
from ftracker.models import InsufficientHistory, Persistence, SeasonalNaive
from ftracker.series import Series

START = date(2025, 1, 1)


def _history(n: int = 200) -> pd.Series:
    idx = [START + timedelta(days=i) for i in range(n)]
    return pd.Series(10 + np.sin(np.arange(n) / 7.0), index=idx)


class Stub:
    name = "stub"

    def __init__(self):
        self.seen = []

    def forecast(self, history, target_dates):
        origin = max(history.index)
        self.seen.append((origin, history.index.max(), list(target_dates)))
        return pd.DataFrame({"point": 1.0, "lo": 0.5, "hi": 1.5}, index=pd.Index(target_dates, name="target_date"))


def test_no_leakage():
    stub = Stub()
    origins = [START + timedelta(days=d) for d in (100, 110, 120)]
    run_backtest(_history(), [stub], origins)
    assert [s[0] for s in stub.seen] == origins
    for origin, last, targets in stub.seen:
        assert last <= origin
        assert targets == [origin + timedelta(days=h) for h in range(1, 8)]


def test_backtest_rows_per_origin():
    origins = [START + timedelta(days=d) for d in (100, 107)]
    hist = _history()
    out = run_backtest(hist, [SeasonalNaive(), Persistence()], origins)
    assert list(out.columns) == COLUMNS == ["origin", "method", "target_date", "horizon", "point", "lo", "hi", "actual"]
    assert len(out) == 2 * 2 * 7
    for (origin, method), g in out.groupby(["origin", "method"]):
        assert sorted(g["horizon"]) == list(range(1, 8))
    row = out[(out["origin"] == origins[0].isoformat()) & (out["horizon"] == 3) & (out["method"] == "persistence")].iloc[0]
    target = origins[0] + timedelta(days=3)
    assert row["target_date"] == target.isoformat()
    assert row["actual"] == hist[target]


def test_missing_actual_is_nan():
    hist = _history(120)
    origin = hist.index.max() - timedelta(days=2)
    out = run_backtest(hist, [Persistence()], [origin])
    assert out["actual"].isna().sum() == 5
    assert out["actual"].notna().sum() == 2


def test_origins_without_enough_history_are_skipped():
    hist = _history()
    early, late = START + timedelta(days=10), START + timedelta(days=100)
    out = run_backtest(hist, [SeasonalNaive()], [early, late])
    assert set(out["origin"]) == {late.isoformat()}
    assert run_backtest(hist, [SeasonalNaive()], [early]).empty


def test_insufficient_history_exception_is_what_is_skipped():
    class Boom:
        name = "boom"

        def forecast(self, history, target_dates):
            raise InsufficientHistory("no")

    out = run_backtest(_history(), [Boom()], [START + timedelta(days=100)])
    assert list(out.columns) == COLUMNS and out.empty


def test_backtest_writes_only_under_data_backtest(tmp_path, monkeypatch):
    hist = _history(400)
    series = Series("toy", "u", "UTC", lambda s, e: hist[(hist.index >= s) & (hist.index <= e)])
    bad = Series("broken", "u", "UTC", lambda s, e: (_ for _ in ()).throw(RuntimeError("secret-free failure")))
    monkeypatch.setattr(cli, "SERIES", {"a": series, "b": bad})
    monkeypatch.setattr(cli, "default_forecasters", lambda: [SeasonalNaive(), Persistence()])
    monkeypatch.setattr(cli, "_today", lambda tz: START + timedelta(days=380))
    rc = cli.main(["backtest", "--series", "all", "--days", "30", "--step", "7", "--data-dir", str(tmp_path)])
    assert rc == 1
    files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert files == ["backtest/toy.csv"]
    out = pd.read_csv(tmp_path / "backtest" / "toy.csv")
    assert list(out.columns) == COLUMNS
    assert out["origin"].nunique() >= 4
    assert pd.to_datetime(out["origin"]).max().date() <= START + timedelta(days=379 - 7)


def test_cli_single_series_by_name(tmp_path, monkeypatch):
    hist = _history(400)
    series = Series("toy", "u", "UTC", lambda s, e: hist[(hist.index >= s) & (hist.index <= e)])
    monkeypatch.setattr(cli, "SERIES", {"a": series})
    monkeypatch.setattr(cli, "default_forecasters", lambda: [Persistence()])
    monkeypatch.setattr(cli, "_today", lambda tz: START + timedelta(days=380))
    assert cli.main(["backtest", "--series", "toy", "--days", "14", "--data-dir", str(tmp_path)]) == 0
    assert cli.main(["backtest", "--series", "nope", "--data-dir", str(tmp_path)]) == 2
