"""Forecasters: seasonal-naive and persistence baselines plus a LightGBM model.

Common contract: ``forecast(history, target_dates)`` returns a DataFrame indexed by
``target_date`` with columns ``point, lo, hi`` (80% interval).  ``history`` is indexed by
``date`` and may hold NaN.  The origin is the last non-NaN day; lead = (target - origin).days.

Interval rule (all three methods): the 10th and 90th percentiles of the method's own past
residuals (actual - forecast) for the same lead are added to the point forecast.  Residuals
come from a rolling origin over the last ``window`` days of history (window = 120, or a third
of the history when it is shorter): every target day inside the window is forecast from an
origin ``lead`` days earlier using only data up to that origin.  For the GBM the models used
for those residuals are fitted once on rows whose targets end before the window starts, so no
residual is scored on data its model saw.  A lead with fewer than MIN_RESIDUALS residuals pools
the residuals of neighbouring leads (radius growing until enough).  Because residuals can be
biased, lo is clipped to <= point and hi to >= point.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

import lightgbm as lgb
import numpy as np
import pandas as pd

MIN_HISTORY = 60
RESIDUAL_WINDOW = 120
MIN_RESIDUALS = 20
LAGS = 14
QUANTILES = (0.10, 0.90)


class InsufficientHistory(Exception):
    """Fewer than MIN_HISTORY non-NaN days of history."""


class Forecaster(Protocol):
    name: str

    def forecast(self, history: pd.Series, target_dates: list[date]) -> pd.DataFrame: ...


def _daily_array(history: pd.Series) -> tuple[np.ndarray, date]:
    """Reindex to consecutive days; return (values, first date), trailing NaN trimmed."""
    s = history.astype(float).dropna()
    if len(s) < MIN_HISTORY:
        raise InsufficientHistory(f"{len(s)} non-NaN days, need {MIN_HISTORY}")
    full = s.set_axis(pd.to_datetime(pd.Index(s.index))).sort_index()
    full = full[~full.index.duplicated(keep="last")]
    full = full.reindex(pd.date_range(full.index[0], full.index[-1], freq="D"))
    return full.to_numpy(), full.index[0].date()


def _ffill(y: np.ndarray) -> np.ndarray:
    return pd.Series(y).ffill().to_numpy()


class _Base:
    name: str
    max_lead: int | None = None

    def _prepare(self, y: np.ndarray, start: date, window: int):
        raise NotImplementedError

    def _point(self, state, y: np.ndarray, start: date, origin: int, lead: int) -> float:
        raise NotImplementedError

    def _residuals_for_lead(self, state, y, start, last, window, lead) -> np.ndarray:
        """Rolling-origin residuals (actual - forecast) for targets in the last `window` days."""
        res = []
        for t in range(max(last - window + 1, lead), last + 1):
            if np.isnan(y[t]):
                continue
            o = t - lead
            if np.isnan(y[: o + 1]).all():
                continue
            res.append(y[t] - self._point(state, y, start, o, lead))
        return np.asarray(res, dtype=float)

    def forecast(self, history: pd.Series, target_dates: list[date]) -> pd.DataFrame:
        y, start = _daily_array(history)
        last = len(y) - 1
        origin_date = start + timedelta(days=last)
        days = [pd.Timestamp(t).date() for t in target_dates]
        leads = [(d - origin_date).days for d in days]
        for lead in leads:
            if lead < 1 or (self.max_lead is not None and lead > self.max_lead):
                raise ValueError(f"lead {lead} outside supported range for {self.name}")
        window = min(RESIDUAL_WINDOW, len(y) // 3)
        state = self._prepare(y, start, window)
        top = self.max_lead or max(8, max(leads, default=1))
        cache: dict[int, np.ndarray] = {}

        def resid(h: int) -> np.ndarray:
            if h not in cache:
                cache[h] = self._residuals_for_lead(state, y, start, last, window, h)
            return cache[h]

        rows = []
        for d, lead in zip(days, leads):
            point = float(self._point(state, y, start, last, lead))
            pooled = resid(lead)
            radius = 0
            while len(pooled) < MIN_RESIDUALS and radius < top:
                radius += 1
                extra = [resid(h) for h in (lead - radius, lead + radius) if 1 <= h <= top]
                pooled = np.concatenate([pooled, *extra])
            if len(pooled) == 0:
                raise InsufficientHistory("no residuals available to calibrate the interval")
            q_lo, q_hi = np.quantile(pooled, QUANTILES)
            rows.append((d, point, min(point + q_lo, point), max(point + q_hi, point)))
        return pd.DataFrame(rows, columns=["target_date", "point", "lo", "hi"]).set_index("target_date")


class Persistence(_Base):
    def __init__(self, name: str = "persistence"):
        self.name = name

    def _prepare(self, y, start, window):
        return _ffill(y)

    def _point(self, state, y, start, origin, lead):
        return state[origin]


class SeasonalNaive(_Base):
    def __init__(self, name: str = "seasonal_naive"):
        self.name = name

    def _prepare(self, y, start, window):
        return _ffill(y)

    def _point(self, state, y, start, origin, lead):
        j = origin + lead - 7 * (-(-lead // 7))  # latest same-weekday day at or before the origin
        while j >= 0 and np.isnan(y[j]):
            j -= 7
        return y[j] if j >= 0 else state[origin]


class GBMForecaster(_Base):
    """One LightGBM model per lead 1..8 on lag features (lags 1-14, day of week, day of year).

    The target is y[origin+lead] - y[origin] (change from the last value, so level shifts
    need no extrapolation); the last value is added back.  Lags are raw values.  Models are
    fitted lazily for the leads actually requested.
    """

    max_lead = 8

    def __init__(self, name: str = "model", n_estimators: int = 150):
        self.name = name
        self.n_estimators = n_estimators

    def _params(self) -> dict:
        return {
            "objective": "regression", "learning_rate": 0.05, "num_leaves": 15, "max_depth": 5,
            "min_data_in_leaf": 5, "bagging_fraction": 0.8, "bagging_freq": 1,
            "feature_fraction": 0.8, "seed": 0, "num_threads": 2, "deterministic": True,
            "force_row_wise": True, "verbose": -1,
        }

    @staticmethod
    def _features(y, start, origins: np.ndarray, lead: int) -> np.ndarray:
        X = np.full((len(origins), LAGS + 2), np.nan)
        for k in range(LAGS):
            pos = origins - k
            ok = pos >= 0
            X[ok, k] = y[pos[ok]]
        days = pd.to_datetime(start) + pd.to_timedelta(origins + lead, unit="D")
        X[:, LAGS] = days.dayofweek
        X[:, LAGS + 1] = days.dayofyear
        return X

    def _prepare(self, y, start, window):
        return {"yf": _ffill(y), "window": window, "final": {}, "cutoff": {}}

    def _model(self, state, y, start, lead, which):
        store = state[which]
        if lead not in store:
            max_target = len(y) - 1 if which == "final" else len(y) - 1 - state["window"]
            yf = state["yf"]
            origins = np.arange(0, max_target - lead + 1)
            origins = origins[~np.isnan(yf[origins]) & ~np.isnan(y[origins + lead])]
            model = None
            if len(origins) >= 10:
                data = lgb.Dataset(
                    self._features(y, start, origins, lead), y[origins + lead] - yf[origins],
                    params={"verbose": -1},
                )
                model = lgb.train(self._params(), data, num_boost_round=self.n_estimators)
            store[lead] = model
        return store[lead]

    def _predict(self, model, state, y, start, origins: np.ndarray, lead: int) -> np.ndarray:
        return state["yf"][origins] + model.predict(self._features(y, start, origins, lead))

    def _point(self, state, y, start, origin, lead):
        model = self._model(state, y, start, lead, "final")
        if model is None:
            raise InsufficientHistory("too few training rows for the GBM")
        return float(self._predict(model, state, y, start, np.array([origin]), lead)[0])

    def _residuals_for_lead(self, state, y, start, last, window, lead):
        model = self._model(state, y, start, lead, "cutoff")
        if model is None:
            return np.array([])
        targets = np.arange(max(last - window + 1, lead), last + 1)
        origins = targets - lead
        keep = ~np.isnan(y[targets]) & ~np.isnan(state["yf"][origins])
        targets, origins = targets[keep], origins[keep]
        if len(origins) == 0:
            return np.array([])
        return y[targets] - self._predict(model, state, y, start, origins, lead)
