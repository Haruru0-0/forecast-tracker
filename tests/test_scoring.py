from datetime import date, datetime

import numpy as np
import pandas as pd

from ftracker.scoring import coverage, mae, scoreboard, skill

COLS = ["series", "method", "horizon", "n", "n_missing", "mae", "coverage", "skill"]


def _fc(rows):
    return pd.DataFrame(
        [
            {"issue_date": date(2026, 1, 1), "method": m, "target_date": date(2026, 1, 1 + h),
             "horizon": h, "point": p, "lo": lo, "hi": hi}
            for m, h, p, lo, hi in rows
        ]
    )


def _out(vals):
    return pd.DataFrame(
        [{"target_date": date(2026, 1, d), "value": v, "fetched_at": datetime(2026, 2, 1)}
         for d, v in vals]
    )


def test_mae():
    assert mae([1, 2, 3], [2, 2, 5]) == 1.0


def test_coverage():
    assert coverage([1, 2, 3], [0, 2.5, 2], [2, 3, 4]) == 2 / 3


def test_skill():
    assert skill(0.5, 1.0) == 0.5
    assert skill(1.0, 0.0) is None


def test_scoreboard_splits_by_horizon_and_counts_missing():
    fc = pd.concat([
        _fc([("model", 1, 1.0, 0, 2)]).assign(issue_date=date(2026, 1, 1)),
        _fc([("model", 1, 1.0, 0, 2)]).assign(issue_date=date(2025, 12, 31), target_date=date(2026, 1, 3)),
        _fc([("model", 1, 1.0, 0, 2)]).assign(issue_date=date(2025, 12, 30), target_date=date(2026, 1, 4)),
        _fc([("model", 2, 1.0, 0, 2)]).assign(target_date=date(2026, 1, 5)),
    ], ignore_index=True)
    out = _out([(2, 1.0), (3, np.nan), (4, 3.0), (5, 1.0)])
    sb = scoreboard("s", fc, out)
    assert list(sb.columns) == COLS
    h1 = sb[(sb.method == "model") & (sb.horizon == 1)].iloc[0]
    assert h1.n == 2 and h1.n_missing == 1
    assert h1.mae == 1.0
    h2 = sb[(sb.method == "model") & (sb.horizon == 2)].iloc[0]
    assert h2.n == 1 and h2.mae == 0.0


def test_skill_uses_better_baseline():
    fc = _fc([("model", 1, 2.0, 0, 5), ("seasonal_naive", 1, 3.0, 0, 5), ("persistence", 1, 5.0, 0, 5)])
    sb = scoreboard("s", fc, _out([(2, 1.0)]))
    m = sb[sb.method == "model"].iloc[0]
    assert m.mae == 1.0 and m.skill == 0.5
    assert sb[sb.method != "model"].skill.isna().all()


def test_forecast_without_outcome_is_not_counted():
    fc = _fc([("model", 1, 1.0, 0, 2), ("model", 2, 1.0, 0, 2)])
    sb = scoreboard("s", fc, _out([(2, 1.0)]))
    h2 = sb[sb.horizon == 2].iloc[0]
    assert h2.n == 0 and h2.n_missing == 0 and np.isnan(h2.mae) and np.isnan(h2.coverage)
    assert sb[sb.horizon == 1].iloc[0].n == 1


def test_empty_inputs():
    sb = scoreboard("s", pd.DataFrame(), pd.DataFrame())
    assert list(sb.columns) == COLS and sb.empty
