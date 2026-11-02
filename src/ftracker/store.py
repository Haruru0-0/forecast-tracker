"""Append-only JSON store for forecasts, outcomes and gaps."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

FORECAST_COLUMNS = ["issue_date", "method", "target_date", "horizon", "point", "lo", "hi"]
OUTCOME_COLUMNS = ["target_date", "value", "fetched_at"]
GAP_COLUMNS = ["issue_date", "reason"]


class AlreadyWritten(Exception):
    """Raised when a file for this key already exists."""


def _write_new(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except FileExistsError as e:
        raise AlreadyWritten(str(path)) from e
    return path


def _files(root: Path, kind: str, series: str) -> list[Path]:
    d = Path(root) / kind / series
    return sorted(d.glob("*.json")) if d.is_dir() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_forecast(root: Path, series: str, issue_date: date, rows: pd.DataFrame, meta: dict) -> Path:
    path = Path(root) / "forecasts" / series / f"{issue_date.isoformat()}.json"
    records = [
        {
            "method": str(r.method),
            "target_date": r.target_date.isoformat(),
            "horizon": int(r.horizon),
            "point": float(r.point),
            "lo": float(r.lo),
            "hi": float(r.hi),
        }
        for r in rows.itertuples(index=False)
    ]
    return _write_new(path, {"issue_date": issue_date.isoformat(), "meta": meta, "rows": records})


def read_forecasts(root: Path, series: str) -> pd.DataFrame:
    records = []
    for p in _files(root, "forecasts", series):
        doc = _load(p)
        issue = date.fromisoformat(doc["issue_date"])
        for r in doc["rows"]:
            records.append(
                {
                    "issue_date": issue,
                    "method": r["method"],
                    "target_date": date.fromisoformat(r["target_date"]),
                    "horizon": r["horizon"],
                    "point": r["point"],
                    "lo": r["lo"],
                    "hi": r["hi"],
                }
            )
    return pd.DataFrame(records, columns=FORECAST_COLUMNS)


def write_outcome(root: Path, series: str, target_date: date, value: float | None, fetched_at: datetime) -> Path:
    path = Path(root) / "outcomes" / series / f"{target_date.isoformat()}.json"
    payload = {
        "target_date": target_date.isoformat(),
        "value": None if value is None else float(value),
        "fetched_at": fetched_at.isoformat(),
    }
    return _write_new(path, payload)


def read_outcomes(root: Path, series: str) -> pd.DataFrame:
    records = []
    for p in _files(root, "outcomes", series):
        doc = _load(p)
        records.append(
            {
                "target_date": date.fromisoformat(doc["target_date"]),
                "value": float("nan") if doc["value"] is None else doc["value"],
                "fetched_at": datetime.fromisoformat(doc["fetched_at"]),
            }
        )
    return pd.DataFrame(records, columns=OUTCOME_COLUMNS)


def write_gap(root: Path, series: str, issue_date: date, reason: str) -> Path:
    path = Path(root) / "gaps" / series / f"{issue_date.isoformat()}.json"
    return _write_new(path, {"issue_date": issue_date.isoformat(), "reason": reason})


def read_gaps(root: Path, series: str) -> pd.DataFrame:
    records = []
    for p in _files(root, "gaps", series):
        doc = _load(p)
        records.append({"issue_date": date.fromisoformat(doc["issue_date"]), "reason": doc["reason"]})
    return pd.DataFrame(records, columns=GAP_COLUMNS)


def issued_dates(root: Path, series: str) -> set[date]:
    return {date.fromisoformat(p.stem) for kind in ("forecasts", "gaps") for p in _files(root, kind, series)}
