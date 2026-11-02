import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _renderer():
    spec = importlib.util.spec_from_file_location("render_readme", ROOT / "scripts" / "render_readme.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_readme_block_matches_results_csv():
    mod = _renderer()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert mod.START in readme and mod.END in readme
    regenerated = mod.replace_block(readme, mod.render_block(ROOT / "results" / "scoreboard.csv"))
    assert regenerated == readme


def test_block_says_no_scored_forecasts_when_csv_empty_or_missing(tmp_path):
    mod = _renderer()
    empty = tmp_path / "s.csv"
    empty.write_text("series,method,horizon,n,n_missing,mae,coverage,skill,n_skill\n", encoding="utf-8")
    assert "No scored forecasts yet." in mod.render_block(empty)
    assert "No scored forecasts yet." in mod.render_block(tmp_path / "missing.csv")


def test_block_renders_table_from_csv(tmp_path):
    mod = _renderer()
    csv = tmp_path / "s.csv"
    csv.write_text(
        "series,method,horizon,n,n_missing,mae,coverage,skill,n_skill\n"
        "weather_tmax,model,1,12,0,1.25,0.8,0.25,12\n"
        "weather_tmax,persistence,1,12,1,1.6,,,0\n", encoding="utf-8")
    block = mod.render_block(csv)
    assert "| weather_tmax | model | 1 | 12 | 0 | 1.250 | 0.80 | 0.25 |" in block
    assert "| weather_tmax | persistence | 1 | 12 | 1 | 1.600 | - | - |" in block
