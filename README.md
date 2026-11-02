# forecast-tracker

A self-updating forecast scoreboard. Every day a GitHub Actions job pulls fresh public data (Houston weather and air quality, ERCOT electricity demand, a Buffalo Bayou river gauge), issues 1 to 7 day forecasts from a gradient-boosting model and two baselines, and scores earlier forecasts once the real values arrive. The results are published as a static page on GitHub Pages, with every forecast kept in the repository so anyone can audit it.

Live page: the URL appears here after the first deploy.

## How forecasts are kept honest

Forecast and outcome files are append-only: a published row is never edited or deleted, so a forecast cannot be quietly rewritten after the answer is known. CI runs `python -m ftracker.immutability` on every push and pull request and fails if any existing data row was changed or removed, and the daily workflow runs the same check before it pushes.

## Series

- `weather_tmax`: daily maximum temperature in Houston (Open-Meteo), degC
- `air_quality_aqi`: daily mean US AQI in Houston (Open-Meteo)
- `electricity_peak_mw`: daily peak ERCOT demand (EIA), MW
- `river_discharge_cfs`: Buffalo Bayou discharge at Houston (USGS 08074000), ft3/s

See `docs/metro.md` for why Houston.

## Run locally

```
pip install -e ".[dev]"
pytest
python -m ftracker.cli daily    # needs EIA_API_KEY in the environment
python -m ftracker.cli site     # builds site/ and results/scoreboard.csv
python scripts/render_readme.py # refreshes the results block below
```

## Results

<!-- results:start -->
| series | method | horizon | n | n missing | MAE (n) | coverage (n) | skill (n) |
|---|---|---|---|---|---|---|---|
| air_quality_aqi | model | 1 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 2 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 3 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 4 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 1 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 2 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 3 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 1 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 2 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 3 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 4 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 1 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 2 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 3 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 1 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 2 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 3 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 4 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 1 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 2 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 3 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
<!-- results:end -->
