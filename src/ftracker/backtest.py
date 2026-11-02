"""Walk-forward backtest: replay the forecasters on past origins, using only data up to each origin.

Output is kept apart from the live record (data/backtest/, never forecasts/, outcomes/ or gaps/).
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ftracker.models import Forecaster, GBMForecaster, InsufficientHistory, Persistence, SeasonalNaive
from ftracker.series import apply_floor

COLUMNS = ["origin", "method", "target_date", "horizon", "point", "lo", "hi", "actual"]
HORIZONS = range(1, 8)


def default_forecasters() -> list[Forecaster]:
    return [SeasonalNaive(), Persistence(), GBMForecaster()]


def run_backtest(history: pd.Series, forecasters: list[Forecaster], origins: list[date],
                 lower_bound: float | None = None) -> pd.DataFrame:
    """Replay the live schedule on each origin O (the last observed day).

    The live engine issues on day D from history ending D-1 and targets D+1..D+7. Here the
    issue date is O+1, so the forecasters see history <= O and forecast O+2..O+8 (leads 2..8),
    and ``horizon = (target_date - (O + 1 day)).days`` runs 1..7 exactly as in the live record.
    The ``origin`` column holds O. Origins with too little history are skipped. ``actual`` is
    NaN where the day was not observed."""
    hist = history.copy()
    hist.index = [pd.Timestamp(i).date() for i in hist.index]
    actuals = hist.dropna()
    rows = []
    for origin in origins:
        past = hist[[d <= origin for d in hist.index]]
        issue = origin + timedelta(days=1)
        targets = [issue + timedelta(days=h) for h in HORIZONS]
        for f in forecasters:
            try:
                fc = f.forecast(past, targets)
            except InsufficientHistory:
                continue
            fc = apply_floor(fc, lower_bound)
            for target, r in fc.iterrows():
                t = pd.Timestamp(target).date()
                rows.append((origin.isoformat(), f.name, t.isoformat(), (t - issue).days,
                             float(r["point"]), float(r["lo"]), float(r["hi"]),
                             float(actuals[t]) if t in actuals.index else float("nan")))
    return pd.DataFrame(rows, columns=COLUMNS)
