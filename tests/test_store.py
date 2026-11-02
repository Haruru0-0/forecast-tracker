from datetime import date, datetime

import pandas as pd
import pytest

from ftracker.store import (
    AlreadyWritten,
    issued_dates,
    read_forecasts,
    read_gaps,
    read_outcomes,
    write_forecast,
    write_gap,
    write_outcome,
)

COLS = ["issue_date", "method", "target_date", "horizon", "point", "lo", "hi"]
META = {"run_id": "r1", "issued_at": "2026-11-03T06:00:00", "last_observed": "2026-11-02"}


def _rows():
    return pd.DataFrame(
        {
            "method": ["naive", "naive"],
            "target_date": [date(2026, 11, 4), date(2026, 11, 5)],
            "horizon": [1, 2],
            "point": [10.5, 11.0],
            "lo": [9.0, 9.5],
            "hi": [12.0, 12.5],
        }
    )


def test_write_forecast_path(tmp_path):
    p = write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows(), META)
    assert p.as_posix().endswith("forecasts/weather/2026-11-03.json")


def test_write_forecast_refuses_overwrite(tmp_path):
    p = write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows(), META)
    before = p.read_bytes()
    with pytest.raises(AlreadyWritten):
        write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows().assign(point=0.0), META)
    assert p.read_bytes() == before


def test_forecast_roundtrip(tmp_path):
    write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows(), META)
    df = read_forecasts(tmp_path, "weather")
    assert list(df.columns) == COLS
    assert len(df) == 2
    assert set(df["issue_date"]) == {date(2026, 11, 3)}
    assert list(df["target_date"]) == [date(2026, 11, 4), date(2026, 11, 5)]
    assert list(df["method"]) == ["naive", "naive"]
    assert list(df["horizon"]) == [1, 2]
    assert list(df["point"]) == [10.5, 11.0]
    assert list(df["lo"]) == [9.0, 9.5]
    assert list(df["hi"]) == [12.0, 12.5]


def test_outcome_null_roundtrip(tmp_path):
    fetched = datetime(2026, 11, 5, 6, 0, 0)
    write_outcome(tmp_path, "weather", date(2026, 11, 4), None, fetched)
    df = read_outcomes(tmp_path, "weather")
    assert list(df.columns) == ["target_date", "value", "fetched_at"]
    assert df["target_date"].iloc[0] == date(2026, 11, 4)
    assert pd.isna(df["value"].iloc[0])
    with pytest.raises(AlreadyWritten):
        write_outcome(tmp_path, "weather", date(2026, 11, 4), 3.0, fetched)


def test_gap_roundtrip_and_issued_dates(tmp_path):
    write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows(), META)
    write_gap(tmp_path, "weather", date(2026, 11, 4), "source down")
    gaps = read_gaps(tmp_path, "weather")
    assert list(gaps.columns) == ["issue_date", "reason"]
    assert gaps["reason"].iloc[0] == "source down"
    assert issued_dates(tmp_path, "weather") == {date(2026, 11, 3), date(2026, 11, 4)}
    with pytest.raises(AlreadyWritten):
        write_gap(tmp_path, "weather", date(2026, 11, 4), "again")


def test_read_empty_series_returns_empty_frame_with_columns(tmp_path):
    f = read_forecasts(tmp_path, "nope")
    assert f.empty and list(f.columns) == COLS
    o = read_outcomes(tmp_path, "nope")
    assert o.empty and list(o.columns) == ["target_date", "value", "fetched_at"]
    g = read_gaps(tmp_path, "nope")
    assert g.empty and list(g.columns) == ["issue_date", "reason"]
    assert issued_dates(tmp_path, "nope") == set()


def test_failed_write_leaves_no_file_and_retry_succeeds(tmp_path):
    bad_meta = {**META, "issued_at": datetime(2026, 11, 3, 6, 0)}
    with pytest.raises(TypeError):
        write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows(), bad_meta)
    d = tmp_path / "forecasts" / "weather"
    assert not d.exists() or list(d.iterdir()) == []
    assert issued_dates(tmp_path, "weather") == set()
    p = write_forecast(tmp_path, "weather", date(2026, 11, 3), _rows(), META)
    assert p.exists()
    assert [x.name for x in d.iterdir()] == ["2026-11-03.json"]


def test_refused_overwrite_leaves_no_temp_file(tmp_path):
    write_gap(tmp_path, "weather", date(2026, 11, 4), "a")
    with pytest.raises(AlreadyWritten):
        write_gap(tmp_path, "weather", date(2026, 11, 4), "b")
    assert [x.name for x in (tmp_path / "gaps" / "weather").iterdir()] == ["2026-11-04.json"]
