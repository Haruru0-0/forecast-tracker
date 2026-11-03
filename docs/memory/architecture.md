# Architecture

See [[features-built]] and [[gotchas]]. Python 3.12, package `src/ftracker`, tests in `tests/`.

## Modules (`src/ftracker/`)
`sources/` (data pulls: Open-Meteo, EIA, USGS), `series.py`, `registry.py` and `config.py` (what is forecast), `models.py` (forecasting methods), `engine.py` (issues forecasts), `daily.py` (the daily run), `scoring.py` (scores outcomes), `backtest.py` (separate backtest), `store.py` (append-only files), `site.py` (builds the static page), `immutability.py` (the guard), `cli.py` (`daily`, `site`).

## Data and output
- Series: `weather_tmax`, `air_quality_aqi`, `electricity_peak_mw`, `river_discharge_cfs`, all for Houston (see `docs/metro.md`). Horizons 1 to 7 days; methods `model`, `persistence`, `seasonal_naive`.
- `data/forecasts`, `data/outcomes`, `data/gaps` are the protected append-only stores; `data/backtest/`, `data/status.json` and `results/scoreboard.csv` are generated.
- `scripts/render_readme.py` rewrites the results block in the README; `scripts/commit_and_push.sh` does the CI commit.

## CI (`.github/workflows/`)
- `daily.yml`: cron `17 10 * * *`, only on `main`, one run at a time and never cancelled; pulls data, issues forecasts, scores, builds the site and deploys to GitHub Pages. Needs the `EIA_API_KEY` repository secret.
- `ci.yml`: tests and the immutability check. `mirror-to-gitlab.yml`: standard mirror (push and nightly).
