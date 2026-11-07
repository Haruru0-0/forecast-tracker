# forecast-tracker

A self-updating forecast scoreboard. Every day a GitHub Actions job pulls fresh public data (Houston weather and air quality, ERCOT electricity demand, a Buffalo Bayou river gauge), issues 1 to 7 day forecasts from a gradient-boosting model and two baselines, and scores earlier forecasts once the real values arrive. The results are published as a static page on GitHub Pages, with every forecast kept in the repository so anyone can audit it.

Live page: https://haruru0-0.github.io/forecast-tracker/ (status header, section index, per-horizon scoreboard, model vs baseline, and a separate backtest).

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
| weather_tmax | model | 1 | 2 | 0 | 1.376 (n=2) | 1.00 (n=2) | 0.31 (n=2) |
| weather_tmax | model | 2 | 1 | 0 | 1.861 (n=1) | 1.00 (n=1) | -0.43 (n=1) |
| weather_tmax | model | 3 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 4 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 1 | 2 | 0 | 2.650 (n=2) | 0.50 (n=2) | - (n=0) |
| weather_tmax | persistence | 2 | 1 | 0 | 1.300 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | persistence | 3 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 2 | 0 | 2.000 (n=2) | 1.00 (n=2) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 1 | 0 | 1.600 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 1 | 3 | 0 | 21.542 (n=3) | 0.33 (n=3) | -0.51 (n=3) |
| air_quality_aqi | model | 2 | 2 | 0 | 13.257 (n=2) | 1.00 (n=2) | -0.52 (n=2) |
| air_quality_aqi | model | 3 | 1 | 0 | 32.309 (n=1) | 0.00 (n=1) | -0.14 (n=1) |
| air_quality_aqi | model | 4 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 1 | 3 | 0 | 27.743 (n=3) | 0.33 (n=3) | - (n=0) |
| air_quality_aqi | persistence | 2 | 2 | 0 | 8.697 (n=2) | 1.00 (n=2) | - (n=0) |
| air_quality_aqi | persistence | 3 | 1 | 0 | 28.397 (n=1) | 0.00 (n=1) | - (n=0) |
| air_quality_aqi | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 3 | 0 | 14.306 (n=3) | 0.67 (n=3) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 2 | 0 | 21.000 (n=2) | 0.50 (n=2) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 1 | 0 | 35.542 (n=1) | 0.00 (n=1) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 1 | 3 | 0 | 2299.118 (n=3) | 1.00 (n=3) | 0.04 (n=3) |
| electricity_peak_mw | model | 2 | 2 | 0 | 1762.943 (n=2) | 1.00 (n=2) | 0.41 (n=2) |
| electricity_peak_mw | model | 3 | 1 | 0 | 1219.667 (n=1) | 1.00 (n=1) | -0.13 (n=1) |
| electricity_peak_mw | model | 4 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 1 | 3 | 0 | 3744.667 (n=3) | 0.67 (n=3) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 2 | 0 | 4806.000 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 1 | 0 | 2197.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 3 | 0 | 2386.000 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 2 | 0 | 3009.000 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 1 | 0 | 1081.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 1 | 3 | 0 | 51.129 (n=3) | 1.00 (n=3) | 0.39 (n=3) |
| river_discharge_cfs | model | 2 | 2 | 0 | 54.708 (n=2) | 1.00 (n=2) | 0.33 (n=2) |
| river_discharge_cfs | model | 3 | 1 | 0 | 169.014 (n=1) | 1.00 (n=1) | -9.01 (n=1) |
| river_discharge_cfs | model | 4 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 1 | 3 | 0 | 89.547 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 2 | 0 | 81.455 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 1 | 0 | 16.880 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 3 | 0 | 83.810 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 2 | 0 | 87.163 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 1 | 0 | 48.315 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
<!-- results:end -->
