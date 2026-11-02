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
    """Forecast O+1..O+7 from history truncated to days <= O; attach actuals from the full history.

    Origins with too little history are skipped. `actual` is NaN where the day was not observed."""
    hist = history.copy()
    hist.index = [pd.Timestamp(i).date() for i in hist.index]
    actuals = hist.dropna()
    rows = []
    for origin in origins:
        past = hist[[d <= origin for d in hist.index]]
        targets = [origin + timedelta(days=h) for h in HORIZONS]
        for f in forecasters:
            try:
                fc = f.forecast(past, targets)
            except InsufficientHistory:
                continue
            fc = apply_floor(fc, lower_bound)
            for target, r in fc.iterrows():
                t = pd.Timestamp(target).date()
                rows.append((origin.isoformat(), f.name, t.isoformat(), (t - origin).days,
                             float(r["point"]), float(r["lo"]), float(r["hi"]),
                             float(actuals[t]) if t in actuals.index else float("nan")))
    return pd.DataFrame(rows, columns=COLUMNS)
