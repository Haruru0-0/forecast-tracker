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
| weather_tmax | model | 1 | 9 | 0 | 2.556 (n=9) | 0.78 (n=9) | 0.34 (n=9) |
| weather_tmax | model | 2 | 8 | 0 | 3.483 (n=8) | 0.62 (n=8) | 0.12 (n=8) |
| weather_tmax | model | 3 | 7 | 0 | 3.198 (n=7) | 0.57 (n=7) | 0.07 (n=7) |
| weather_tmax | model | 4 | 6 | 0 | 3.746 (n=6) | 0.67 (n=6) | 0.01 (n=6) |
| weather_tmax | model | 5 | 5 | 0 | 4.353 (n=5) | 0.40 (n=5) | 0.13 (n=5) |
| weather_tmax | model | 6 | 4 | 0 | 4.576 (n=4) | 0.25 (n=4) | 0.07 (n=4) |
| weather_tmax | model | 7 | 3 | 0 | 3.021 (n=3) | 0.33 (n=3) | 0.04 (n=3) |
| weather_tmax | persistence | 1 | 9 | 0 | 3.867 (n=9) | 0.33 (n=9) | - (n=0) |
| weather_tmax | persistence | 2 | 8 | 0 | 3.975 (n=8) | 0.50 (n=8) | - (n=0) |
| weather_tmax | persistence | 3 | 7 | 0 | 3.429 (n=7) | 0.71 (n=7) | - (n=0) |
| weather_tmax | persistence | 4 | 6 | 0 | 3.767 (n=6) | 0.67 (n=6) | - (n=0) |
| weather_tmax | persistence | 5 | 5 | 0 | 5.000 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | persistence | 6 | 4 | 0 | 4.900 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | persistence | 7 | 3 | 0 | 3.833 (n=3) | 0.67 (n=3) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 9 | 0 | 3.856 (n=9) | 0.78 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 8 | 0 | 4.037 (n=8) | 0.75 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 7 | 0 | 4.386 (n=7) | 0.71 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 6 | 0 | 5.050 (n=6) | 0.67 (n=6) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 5 | 0 | 5.980 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 4 | 0 | 4.900 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 3 | 0 | 3.133 (n=3) | 1.00 (n=3) | - (n=0) |
| air_quality_aqi | model | 1 | 10 | 0 | 16.088 (n=10) | 0.70 (n=10) | 0.17 (n=10) |
| air_quality_aqi | model | 2 | 9 | 0 | 16.817 (n=9) | 0.56 (n=9) | 0.21 (n=9) |
| air_quality_aqi | model | 3 | 8 | 0 | 16.525 (n=8) | 0.62 (n=8) | 0.17 (n=8) |
| air_quality_aqi | model | 4 | 7 | 0 | 14.649 (n=7) | 0.43 (n=7) | -0.30 (n=7) |
| air_quality_aqi | model | 5 | 6 | 0 | 16.741 (n=6) | 0.67 (n=6) | 0.06 (n=6) |
| air_quality_aqi | model | 6 | 5 | 0 | 11.046 (n=5) | 0.80 (n=5) | 0.33 (n=5) |
| air_quality_aqi | model | 7 | 4 | 0 | 17.599 (n=4) | 0.25 (n=4) | -0.13 (n=4) |
| air_quality_aqi | persistence | 1 | 10 | 0 | 20.790 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | persistence | 2 | 9 | 0 | 22.118 (n=9) | 0.44 (n=9) | - (n=0) |
| air_quality_aqi | persistence | 3 | 8 | 0 | 19.987 (n=8) | 0.62 (n=8) | - (n=0) |
| air_quality_aqi | persistence | 4 | 7 | 0 | 11.271 (n=7) | 0.86 (n=7) | - (n=0) |
| air_quality_aqi | persistence | 5 | 6 | 0 | 17.837 (n=6) | 0.67 (n=6) | - (n=0) |
| air_quality_aqi | persistence | 6 | 5 | 0 | 16.587 (n=5) | 0.60 (n=5) | - (n=0) |
| air_quality_aqi | persistence | 7 | 4 | 0 | 16.693 (n=4) | 0.75 (n=4) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 10 | 0 | 19.285 (n=10) | 0.60 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 9 | 0 | 21.326 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 8 | 0 | 23.185 (n=8) | 0.50 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 7 | 0 | 21.420 (n=7) | 0.43 (n=7) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 6 | 0 | 20.316 (n=6) | 0.50 (n=6) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 5 | 0 | 16.587 (n=5) | 0.60 (n=5) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 4 | 0 | 15.583 (n=4) | 0.75 (n=4) | - (n=0) |
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
| river_discharge_cfs | model | 1 | 10 | 0 | 85.478 (n=10) | 1.00 (n=10) | -0.49 (n=10) |
| river_discharge_cfs | model | 2 | 9 | 0 | 103.831 (n=9) | 1.00 (n=9) | -0.88 (n=9) |
| river_discharge_cfs | model | 3 | 8 | 0 | 128.046 (n=8) | 1.00 (n=8) | -1.75 (n=8) |
| river_discharge_cfs | model | 4 | 7 | 0 | 187.568 (n=7) | 0.86 (n=7) | -3.06 (n=7) |
| river_discharge_cfs | model | 5 | 6 | 0 | 241.196 (n=6) | 1.00 (n=6) | -3.78 (n=6) |
| river_discharge_cfs | model | 6 | 5 | 0 | 222.117 (n=5) | 1.00 (n=5) | -3.06 (n=5) |
| river_discharge_cfs | model | 7 | 4 | 0 | 331.596 (n=4) | 0.75 (n=4) | -4.85 (n=4) |
| river_discharge_cfs | persistence | 1 | 10 | 0 | 89.272 (n=10) | 0.90 (n=10) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 9 | 0 | 101.344 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 8 | 0 | 94.453 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 7 | 0 | 96.091 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 6 | 0 | 94.684 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 5 | 0 | 54.774 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 4 | 0 | 56.697 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 10 | 0 | 57.498 (n=10) | 1.00 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 9 | 0 | 55.320 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 8 | 0 | 46.484 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 7 | 0 | 46.222 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 6 | 0 | 50.492 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 5 | 0 | 54.774 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 4 | 0 | 106.151 (n=4) | 1.00 (n=4) | - (n=0) |
<!-- results:end -->
