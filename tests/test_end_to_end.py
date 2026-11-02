"""Engine -> site -> immutability checker, on fabricated deterministic series."""

import json
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ftracker import engine, site, store
from ftracker.immutability import check_immutable, check_whole_history
from ftracker.series import Series

DAY1 = datetime(2026, 11, 3, 10, 17, tzinfo=timezone.utc)


def _series(name: str, level: float, lower_bound: float | None) -> Series:
    def fetch(start: date, end: date) -> pd.Series:
        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        vals = [level + 5 * np.sin(d.toordinal() / 9.0) + (d.toordinal() % 7) for d in days]
        return pd.Series(vals, index=days, dtype=float)

    return Series(name, "u", "UTC", fetch, lower_bound=lower_bound)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def commit_all(repo: Path, msg: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


def test_two_daily_runs_build_a_page_and_pass_the_checker_until_a_file_is_edited(tmp_path):
    registry = {"temp": _series("e2e_temp", 20.0, None), "flow": _series("e2e_flow", 3.0, 0.0)}
    repo = tmp_path / "repo"
    data = repo / "data"
    data.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "commit.gpgsign", "false")

    r1 = engine.run_daily(data, registry, DAY1, "run-1")
    assert r1.ok and r1.issued == {"e2e_temp": 21, "e2e_flow": 21}
    day1 = commit_all(repo, "day 1")
    r2 = engine.run_daily(data, registry, DAY1 + timedelta(days=1), "run-2")
    assert r2.ok and r2.issued == {"e2e_temp": 21, "e2e_flow": 21}
    commit_all(repo, "day 2")

    for name in ("e2e_temp", "e2e_flow"):
        fc = store.read_forecasts(data, name)
        assert sorted(set(fc["issue_date"])) == [date(2026, 11, 3), date(2026, 11, 4)]
        assert ((fc["lo"] <= fc["point"]) & (fc["point"] <= fc["hi"])).all()
    assert (store.read_forecasts(data, "e2e_flow")[["point", "lo"]] >= 0).all().all()
    assert json.loads((data / "status.json").read_text())["last_run"] == (DAY1 + timedelta(days=1)).isoformat()

    page = site.build_site(data, tmp_path / "site", DAY1 + timedelta(days=1, hours=1), ["e2e_temp", "e2e_flow"])
    html = page.read_text(encoding="utf-8")
    assert html.count("days tracked: 2; gap days: 0") == 2
    assert 'data-last-issue="2026-11-04"' in html and "<script src" not in html

    assert check_immutable(repo, day1) == []
    assert check_whole_history(repo) == []

    edited = data / "forecasts" / "e2e_temp" / "2026-11-03.json"
    doc = json.loads(edited.read_text(encoding="utf-8"))
    doc["rows"][0]["point"] = 999.0
    edited.write_text(json.dumps(doc), encoding="utf-8")
    commit_all(repo, "quietly improve an old forecast")
    for found in (check_immutable(repo, day1), check_whole_history(repo)):
        assert len(found) == 1 and "data/forecasts/e2e_temp/2026-11-03.json: M" in found[0]
