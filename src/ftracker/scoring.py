"""Scoring of stored forecasts against settled outcomes."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

COLUMNS = ["series", "method", "horizon", "n", "n_missing", "mae", "coverage", "skill"]
BASELINES = ("seasonal_naive", "persistence")


def mae(y: Sequence[float], yhat: Sequence[float]) -> float:
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(yhat, float))))


def coverage(y, lo, hi) -> float:
    y, lo, hi = (np.asarray(a, float) for a in (y, lo, hi))
    return float(np.mean((y >= lo) & (y <= hi)))


def skill(model_mae: float, baseline_mae: float) -> float | None:
    if baseline_mae <= 1e-9:
        return None
    return 1 - model_mae / baseline_mae


def scoreboard(series: str, forecasts: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """One row per (method, horizon) with n, n_missing, mae, coverage, skill.

    Forecasts are left-joined to outcomes on target_date. A forecast with no
    outcome row yet is not counted at all; one whose outcome value is NaN counts
    in n_missing. mae and coverage use only the n scored forecasts and are NaN
    when n == 0. Horizons appear as rows whenever a forecast exists for them.

    skill is only set on method == "model" and is NaN (float, never None, so the
    column stays numeric) when undefined: a baseline has no scored pairs or its
    MAE is <= 1e-9 (see skill()). It is computed per horizon on the paired set of
    (issue_date, target_date) scored for the model and both baselines, against
    the lower baseline MAE.
    """
    if forecasts is None or forecasts.empty:
        return pd.DataFrame(columns=COLUMNS)

    out = outcomes[["target_date", "value"]].drop_duplicates("target_date", keep="last") \
        if outcomes is not None and not outcomes.empty else pd.DataFrame(columns=["target_date", "value"])
    df = forecasts.merge(out, on="target_date", how="left", indicator=True)
    df["settled"] = df["_merge"] == "both"
    df["scored"] = df["settled"] & df["value"].notna()

    rows = []
    for (method, horizon), g in df.groupby(["method", "horizon"], sort=True):
        s = g[g["scored"]]
        n = len(s)
        rows.append({
            "series": series, "method": method, "horizon": int(horizon), "n": n,
            "n_missing": int((g["settled"] & ~g["scored"]).sum()),
            "mae": mae(s["value"], s["point"]) if n else np.nan,
            "coverage": coverage(s["value"], s["lo"], s["hi"]) if n else np.nan,
            "skill": np.nan,
        })
    board = pd.DataFrame(rows, columns=COLUMNS)

    key = ["issue_date", "target_date"]
    for horizon, hg in df[df["scored"]].groupby("horizon"):
        parts = {m: hg[hg["method"] == m].set_index(key) for m in ("model", *BASELINES)}
        if any(p.empty for p in parts.values()):
            continue
        common = parts["model"].index
        for b in BASELINES:
            common = common.intersection(parts[b].index)
        if len(common) == 0:
            continue
        maes = {m: mae(p.loc[common, "value"], p.loc[common, "point"]) for m, p in parts.items()}
        sk = skill(maes["model"], min(maes[b] for b in BASELINES))
        if sk is not None:
            board.loc[(board["method"] == "model") & (board["horizon"] == int(horizon)), "skill"] = sk
    return board
