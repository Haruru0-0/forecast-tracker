import pandas as pd

from ftracker import cli
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
    assert cli.main(["site", "--root", str(tmp_path / "data"), "--out", str(tmp_path / "site")]) == 0
    assert "STALE" in (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
