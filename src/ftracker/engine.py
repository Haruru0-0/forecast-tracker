"""Daily engine: issue forecasts before the outcome is known, then score due outcomes.

Series are identified by ``Series.name`` everywhere (store paths, report keys, status.json).
Existing forecast, outcome and gap files are never modified.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from ftracker import store
from ftracker.models import (
    Forecaster,
    GBMForecaster,
    MAX_LEAD,
    InsufficientHistory,
    Persistence,
    SeasonalNaive,
)
from ftracker.series import Series, SourceError

HISTORY_DAYS = 730
HORIZONS = range(1, 8)
SCORE_LAG_DAYS = 2
ROW_COLUMNS = ["method", "target_date", "horizon", "point", "lo", "hi"]


@dataclass
class RunReport:
    issued: dict[str, int] = field(default_factory=dict)
    scored: dict[str, int] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.failed


class StaleHistory(Exception):
    """The last observed day is too old to forecast the full horizon."""


def _safe(text: object, limit: int = 200) -> str:
    """Short message without URLs, query strings or key-like values."""
    s = re.sub(r"https?://\S+", "<url>", str(text))
    s = re.sub(r"(?i)\b([\w-]*(?:key|token|secret|password)[\w-]*)\s*[=:]\s*\S+", r"\1=<redacted>", s)
    s = " ".join(s.split())
    return s[:limit]


def _require_aware(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")


def issue_forecasts(
    root: Path,
    series: Series,
    issue_date: date,
    now: datetime,
    run_id: str,
    forecasters: list[Forecaster],
) -> int:
    _require_aware(now)
    name = series.name
    if issue_date in store.issued_dates(root, name):
        return 0
    last_day = issue_date - timedelta(days=1)
    try:
        history = series.fetch_daily(last_day - timedelta(days=HISTORY_DAYS), last_day)
    except SourceError as exc:
        store.write_gap(root, name, issue_date, f"source error: {_safe(exc)}")
        raise
    history = history[[d <= last_day for d in history.index]]  # defence: nothing from the issue date on
    observed = history.dropna()
    if observed.empty:
        store.write_gap(root, name, issue_date, "no observed history")
        raise InsufficientHistory("no observed history")
    last_observed = max(observed.index)
    targets = [issue_date + timedelta(days=h) for h in HORIZONS]
    if (targets[-1] - last_observed).days > MAX_LEAD:
        reason = f"history stale: last observed {last_observed.isoformat()}"
        store.write_gap(root, name, issue_date, reason)
        raise StaleHistory(reason)
    frames = []
    try:
        for f in forecasters:
            out = f.forecast(history, targets)
            frame = out.reset_index().rename(columns={out.index.name or "index": "target_date"})
            frame["method"] = f.name
            frame["horizon"] = [(t - issue_date).days for t in frame["target_date"]]
            frames.append(frame[ROW_COLUMNS])
    except InsufficientHistory as exc:
        store.write_gap(root, name, issue_date, f"insufficient history: {_safe(exc)}")
        raise
    rows = pd.concat(frames, ignore_index=True)
    meta = {"run_id": run_id, "issued_at": now.isoformat(), "last_observed": last_observed.isoformat()}
    store.write_forecast(root, name, issue_date, rows, meta)
    return len(rows)


def score_outcomes(root: Path, series: Series, today: date, now: datetime) -> int:
    name = series.name
    forecasts = store.read_forecasts(root, name)
    if forecasts.empty:
        return 0
    scored = set(store.read_outcomes(root, name)["target_date"])
    cutoff = today - timedelta(days=SCORE_LAG_DAYS)
    due = sorted({t for t in forecasts["target_date"] if t <= cutoff and t not in scored})
    if not due:
        return 0
    values = series.fetch_daily(due[0], due[-1])  # SourceError propagates: stop scoring this series
    count = 0
    for t in due:
        v = values.get(t)
        value = None if v is None or pd.isna(v) else float(v)
        try:
            store.write_outcome(root, name, t, value, now)
        except store.AlreadyWritten:
            continue
        count += 1
    return count


def _last_issue(root: Path, name: str) -> str | None:
    df = store.read_forecasts(root, name)
    return None if df.empty else max(df["issue_date"]).isoformat()


def _write_status(root: Path, status: dict) -> None:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=root, prefix=".status-", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
        os.replace(tmp, root / "status.json")
    finally:
        Path(tmp).unlink(missing_ok=True)


def _describe(exc: Exception) -> str:
    return f"{type(exc).__name__}: {_safe(exc)}"


def run_daily(
    root: Path,
    registry: dict[str, Series],
    now: datetime,
    run_id: str,
    forecasters: list[Forecaster] | None = None,
) -> RunReport:
    _require_aware(now)
    if forecasters is None:
        forecasters = [SeasonalNaive(), Persistence(), GBMForecaster()]
    issue_date = now.astimezone(timezone.utc).date()
    report = RunReport()
    status: dict = {"last_run": now.isoformat(), "series": {}}
    for series in registry.values():
        name = series.name
        errors: list[str] = []
        try:
            report.issued[name] = issue_forecasts(root, series, issue_date, now, run_id, forecasters)
        except Exception as exc:  # isolate each series; type and message only
            report.issued[name] = 0
            errors.append(_describe(exc))
        try:
            report.scored[name] = score_outcomes(root, series, issue_date, now)
        except Exception as exc:
            report.scored[name] = 0
            errors.append(_describe(exc))
        if errors:
            report.failed[name] = "; ".join(errors)
        try:
            last_issue = _last_issue(root, name)
        except Exception as exc:
            last_issue = None
            errors.append(_describe(exc))
            report.failed[name] = "; ".join(errors)
        status["series"][name] = {"last_issue": last_issue, "error": report.failed.get(name)}
    _write_status(root, status)
    return report
