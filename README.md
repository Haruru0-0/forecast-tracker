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
| weather_tmax | model | 1 | 8 | 0 | 2.801 (n=8) | 0.75 (n=8) | 0.31 (n=8) |
| weather_tmax | model | 2 | 7 | 0 | 3.679 (n=7) | 0.57 (n=7) | -0.06 (n=7) |
| weather_tmax | model | 3 | 6 | 0 | 3.700 (n=6) | 0.50 (n=6) | -0.17 (n=6) |
| weather_tmax | model | 4 | 5 | 0 | 4.286 (n=5) | 0.60 (n=5) | 0.04 (n=5) |
| weather_tmax | model | 5 | 4 | 0 | 5.297 (n=4) | 0.25 (n=4) | 0.12 (n=4) |
| weather_tmax | model | 6 | 3 | 0 | 5.476 (n=3) | 0.00 (n=3) | 0.12 (n=3) |
| weather_tmax | model | 7 | 2 | 0 | 3.631 (n=2) | 0.00 (n=2) | -0.25 (n=2) |
| weather_tmax | persistence | 1 | 8 | 0 | 4.100 (n=8) | 0.25 (n=8) | - (n=0) |
| weather_tmax | persistence | 2 | 7 | 0 | 3.457 (n=7) | 0.57 (n=7) | - (n=0) |
| weather_tmax | persistence | 3 | 6 | 0 | 3.150 (n=6) | 0.83 (n=6) | - (n=0) |
| weather_tmax | persistence | 4 | 5 | 0 | 4.460 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | persistence | 5 | 4 | 0 | 6.025 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | persistence | 6 | 3 | 0 | 6.200 (n=3) | 0.33 (n=3) | - (n=0) |
| weather_tmax | persistence | 7 | 2 | 0 | 5.500 (n=2) | 0.50 (n=2) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 8 | 0 | 4.088 (n=8) | 0.75 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 7 | 0 | 4.329 (n=7) | 0.71 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 6 | 0 | 4.783 (n=6) | 0.67 (n=6) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 5 | 0 | 5.660 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 4 | 0 | 6.975 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 3 | 0 | 6.200 (n=3) | 0.33 (n=3) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 2 | 0 | 2.900 (n=2) | 1.00 (n=2) | - (n=0) |
| air_quality_aqi | model | 1 | 9 | 0 | 16.079 (n=9) | 0.67 (n=9) | 0.20 (n=9) |
| air_quality_aqi | model | 2 | 8 | 0 | 15.807 (n=8) | 0.62 (n=8) | 0.30 (n=8) |
| air_quality_aqi | model | 3 | 7 | 0 | 14.898 (n=7) | 0.71 (n=7) | 0.24 (n=7) |
| air_quality_aqi | model | 4 | 6 | 0 | 13.656 (n=6) | 0.50 (n=6) | -0.20 (n=6) |
| air_quality_aqi | model | 5 | 5 | 0 | 14.490 (n=5) | 0.80 (n=5) | 0.30 (n=5) |
| air_quality_aqi | model | 6 | 4 | 0 | 9.276 (n=4) | 0.75 (n=4) | 0.48 (n=4) |
| air_quality_aqi | model | 7 | 3 | 0 | 16.206 (n=3) | 0.33 (n=3) | -0.30 (n=3) |
| air_quality_aqi | persistence | 1 | 9 | 0 | 22.049 (n=9) | 0.44 (n=9) | - (n=0) |
| air_quality_aqi | persistence | 2 | 8 | 0 | 22.513 (n=8) | 0.38 (n=8) | - (n=0) |
| air_quality_aqi | persistence | 3 | 7 | 0 | 19.497 (n=7) | 0.57 (n=7) | - (n=0) |
| air_quality_aqi | persistence | 4 | 6 | 0 | 11.344 (n=6) | 0.83 (n=6) | - (n=0) |
| air_quality_aqi | persistence | 5 | 5 | 0 | 20.796 (n=5) | 0.60 (n=5) | - (n=0) |
| air_quality_aqi | persistence | 6 | 4 | 0 | 17.818 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | persistence | 7 | 3 | 0 | 12.423 (n=3) | 1.00 (n=3) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 9 | 0 | 20.132 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 8 | 0 | 22.534 (n=8) | 0.50 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 7 | 0 | 24.830 (n=7) | 0.43 (n=7) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 6 | 0 | 23.045 (n=6) | 0.33 (n=6) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 5 | 0 | 22.046 (n=5) | 0.40 (n=5) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 4 | 0 | 17.818 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 3 | 0 | 12.819 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | model | 1 | 9 | 0 | 2666.777 (n=9) | 0.89 (n=9) | 0.20 (n=9) |
| electricity_peak_mw | model | 2 | 8 | 0 | 2579.943 (n=8) | 0.75 (n=8) | 0.41 (n=8) |
| electricity_peak_mw | model | 3 | 7 | 0 | 2750.557 (n=7) | 1.00 (n=7) | 0.48 (n=7) |
| electricity_peak_mw | model | 4 | 6 | 0 | 1899.454 (n=6) | 1.00 (n=6) | 0.71 (n=6) |
| electricity_peak_mw | model | 5 | 5 | 0 | 1536.415 (n=5) | 1.00 (n=5) | 0.80 (n=5) |
| electricity_peak_mw | model | 6 | 4 | 0 | 2443.125 (n=4) | 1.00 (n=4) | 0.69 (n=4) |
| electricity_peak_mw | model | 7 | 3 | 0 | 1312.526 (n=3) | 1.00 (n=3) | 0.81 (n=3) |
| electricity_peak_mw | persistence | 1 | 9 | 0 | 3339.000 (n=9) | 0.78 (n=9) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 8 | 0 | 4354.125 (n=8) | 0.88 (n=8) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 7 | 0 | 5325.571 (n=7) | 0.71 (n=7) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 6 | 0 | 6541.667 (n=6) | 0.67 (n=6) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 5 | 0 | 7850.000 (n=5) | 0.80 (n=5) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 4 | 0 | 8007.250 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 3 | 0 | 8411.000 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 9 | 0 | 5173.222 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 8 | 0 | 5677.375 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 7 | 0 | 5783.143 (n=7) | 1.00 (n=7) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 6 | 0 | 6566.833 (n=6) | 1.00 (n=6) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 5 | 0 | 7658.800 (n=5) | 1.00 (n=5) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 4 | 0 | 8007.250 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 3 | 0 | 6984.333 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | model | 1 | 9 | 0 | 90.109 (n=9) | 1.00 (n=9) | -0.68 (n=9) |
| river_discharge_cfs | model | 2 | 8 | 0 | 115.517 (n=8) | 1.00 (n=8) | -1.28 (n=8) |
| river_discharge_cfs | model | 3 | 7 | 0 | 139.720 (n=7) | 1.00 (n=7) | -2.50 (n=7) |
| river_discharge_cfs | model | 4 | 6 | 0 | 212.285 (n=6) | 0.83 (n=6) | -4.51 (n=6) |
| river_discharge_cfs | model | 5 | 5 | 0 | 267.151 (n=5) | 1.00 (n=5) | -5.35 (n=5) |
| river_discharge_cfs | model | 6 | 4 | 0 | 237.908 (n=4) | 1.00 (n=4) | -4.25 (n=4) |
| river_discharge_cfs | model | 7 | 3 | 0 | 276.575 (n=3) | 1.00 (n=3) | -3.08 (n=3) |
| river_discharge_cfs | persistence | 1 | 9 | 0 | 90.120 (n=9) | 0.89 (n=9) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 8 | 0 | 100.022 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 7 | 0 | 87.699 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 6 | 0 | 88.001 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 5 | 0 | 88.982 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 4 | 0 | 45.342 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 3 | 0 | 67.710 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 9 | 0 | 53.609 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 8 | 0 | 50.672 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 7 | 0 | 39.910 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 6 | 0 | 38.509 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 5 | 0 | 42.091 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 4 | 0 | 45.342 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 3 | 0 | 94.597 (n=3) | 1.00 (n=3) | - (n=0) |
<!-- results:end -->
