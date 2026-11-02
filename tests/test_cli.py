from datetime import datetime, timezone

import pandas as pd

from ftracker import cli
from ftracker.engine import RunReport
from ftracker.series import Series


def test_check_sources_survives_non_source_error(monkeypatch, capsys):
    def boom(s, e):
        raise RuntimeError("weird failure")

    def ok(s, e):
        return pd.Series([1.0], index=[e])

    monkeypatch.setattr(cli, "SERIES", {
        "a": Series("first", "u", "America/Chicago", ok),
        "b": Series("broken", "u", "America/Chicago", boom),
        "c": Series("third", "u", "America/Chicago", ok),
    })
    assert cli.check_sources() == 1
    out = capsys.readouterr().out
    assert "first (u): latest" in out
    assert "broken: ERROR RuntimeError: weird failure" in out
    assert "third (u): latest" in out


def test_site_command_writes_page(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "SERIES", {"a": Series("first", "u", "America/Chicago", lambda s, e: None)})
    assert cli.main(["site", "--data-dir", str(tmp_path / "data"), "--out", str(tmp_path / "site")]) == 0
    assert "STALE" in (tmp_path / "site" / "index.html").read_text(encoding="utf-8")


def test_site_command_writes_scoreboard_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "SERIES", {"a": Series("first", "u", "America/Chicago", lambda s, e: None)})
    args = ["site", "--data-dir", str(tmp_path / "data"), "--out", str(tmp_path / "site"),
            "--results-dir", str(tmp_path / "res" / "nested")]
    assert cli.main(args) == 0
    csv = tmp_path / "res" / "nested" / "scoreboard.csv"
    assert csv.read_text(encoding="utf-8").splitlines()[0].startswith("series,method,horizon")


def _stub_daily(monkeypatch, report):
    seen = {}

    def fake(root, registry, now, run_id, forecasters=None):
        seen.update(root=root, names=[s.name for s in registry.values()], now=now, run_id=run_id)
        return report

    monkeypatch.setattr(cli, "run_daily", fake)
    monkeypatch.setattr(cli, "SERIES", {"a": Series("first", "u", "America/Chicago", lambda s, e: None),
                                        "b": Series("second", "u", "America/Chicago", lambda s, e: None)})
    return seen


def test_daily_ok_exits_0_and_prints_summary(tmp_path, monkeypatch, capsys):
    seen = _stub_daily(monkeypatch, RunReport(issued={"first": 7, "second": 7}, scored={"first": 3, "second": 0}))
    monkeypatch.setenv("GITHUB_RUN_ID", "4242")
    assert cli.main(["daily", "--data-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "first: issued 7, scored 3" in out
    assert "second: issued 7, scored 0" in out
    assert seen["run_id"] == "4242" and seen["names"] == ["first", "second"]
    assert seen["root"] == tmp_path and seen["now"].tzinfo is not None


def test_daily_defaults_run_id_local(tmp_path, monkeypatch):
    seen = _stub_daily(monkeypatch, RunReport())
    monkeypatch.delenv("GITHUB_RUN_ID", raising=False)
    assert cli.main(["daily", "--data-dir", str(tmp_path)]) == 0
    assert seen["run_id"] == "local"


def test_daily_failure_exits_1_and_names_series(tmp_path, monkeypatch, capsys):
    _stub_daily(monkeypatch, RunReport(issued={"first": 0}, scored={"first": 0},
                                       failed={"first": "ValueError: boom"}))
    assert cli.main(["daily", "--data-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "first: issued 0, scored 0, FAILED ValueError: boom" in out
