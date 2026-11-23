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
| weather_tmax | model | 1 | 17 | 0 | 2.870 (n=17) | 0.71 (n=17) | 0.18 (n=17) |
| weather_tmax | model | 2 | 17 | 0 | 3.654 (n=17) | 0.59 (n=17) | 0.02 (n=17) |
| weather_tmax | model | 3 | 16 | 0 | 4.069 (n=16) | 0.38 (n=16) | -0.06 (n=16) |
| weather_tmax | model | 4 | 15 | 0 | 4.032 (n=15) | 0.53 (n=15) | 0.01 (n=15) |
| weather_tmax | model | 5 | 14 | 0 | 3.910 (n=14) | 0.43 (n=14) | -0.02 (n=14) |
| weather_tmax | model | 6 | 13 | 0 | 3.920 (n=13) | 0.38 (n=13) | -0.14 (n=13) |
| weather_tmax | model | 7 | 12 | 0 | 3.528 (n=12) | 0.50 (n=12) | -0.21 (n=12) |
| weather_tmax | persistence | 1 | 17 | 0 | 4.041 (n=17) | 0.29 (n=17) | - (n=0) |
| weather_tmax | persistence | 2 | 17 | 0 | 4.576 (n=17) | 0.29 (n=17) | - (n=0) |
| weather_tmax | persistence | 3 | 16 | 0 | 4.881 (n=16) | 0.44 (n=16) | - (n=0) |
| weather_tmax | persistence | 4 | 15 | 0 | 4.560 (n=15) | 0.53 (n=15) | - (n=0) |
| weather_tmax | persistence | 5 | 14 | 0 | 3.829 (n=14) | 0.71 (n=14) | - (n=0) |
| weather_tmax | persistence | 6 | 13 | 0 | 3.431 (n=13) | 0.69 (n=13) | - (n=0) |
| weather_tmax | persistence | 7 | 12 | 0 | 2.908 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 17 | 0 | 3.488 (n=17) | 0.82 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 17 | 0 | 3.724 (n=17) | 0.76 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 16 | 0 | 3.856 (n=16) | 0.75 (n=16) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 15 | 0 | 4.087 (n=15) | 0.73 (n=15) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 14 | 0 | 4.350 (n=14) | 0.71 (n=14) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 13 | 0 | 3.431 (n=13) | 0.69 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 12 | 0 | 5.650 (n=12) | 0.67 (n=12) | - (n=0) |
| air_quality_aqi | model | 1 | 19 | 0 | 14.951 (n=19) | 0.68 (n=19) | 0.26 (n=19) |
| air_quality_aqi | model | 2 | 18 | 0 | 15.401 (n=18) | 0.56 (n=18) | 0.34 (n=18) |
| air_quality_aqi | model | 3 | 17 | 0 | 16.003 (n=17) | 0.59 (n=17) | 0.34 (n=17) |
| air_quality_aqi | model | 4 | 16 | 0 | 14.905 (n=16) | 0.50 (n=16) | 0.26 (n=16) |
| air_quality_aqi | model | 5 | 15 | 0 | 13.291 (n=15) | 0.60 (n=15) | 0.42 (n=15) |
| air_quality_aqi | model | 6 | 14 | 0 | 11.974 (n=14) | 0.64 (n=14) | 0.46 (n=14) |
| air_quality_aqi | model | 7 | 13 | 0 | 14.559 (n=13) | 0.54 (n=13) | 0.20 (n=13) |
| air_quality_aqi | persistence | 1 | 19 | 0 | 20.098 (n=19) | 0.47 (n=19) | - (n=0) |
| air_quality_aqi | persistence | 2 | 18 | 0 | 24.061 (n=18) | 0.44 (n=18) | - (n=0) |
| air_quality_aqi | persistence | 3 | 17 | 0 | 24.234 (n=17) | 0.47 (n=17) | - (n=0) |
| air_quality_aqi | persistence | 4 | 16 | 0 | 20.199 (n=16) | 0.62 (n=16) | - (n=0) |
| air_quality_aqi | persistence | 5 | 15 | 0 | 22.901 (n=15) | 0.47 (n=15) | - (n=0) |
| air_quality_aqi | persistence | 6 | 14 | 0 | 22.219 (n=14) | 0.57 (n=14) | - (n=0) |
| air_quality_aqi | persistence | 7 | 13 | 0 | 24.034 (n=13) | 0.46 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 19 | 0 | 22.157 (n=19) | 0.58 (n=19) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 18 | 0 | 23.337 (n=18) | 0.56 (n=18) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 17 | 0 | 24.330 (n=17) | 0.53 (n=17) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 16 | 0 | 23.629 (n=16) | 0.50 (n=16) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 15 | 0 | 23.335 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 14 | 0 | 22.219 (n=14) | 0.57 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 13 | 0 | 18.252 (n=13) | 0.54 (n=13) | - (n=0) |
| electricity_peak_mw | model | 1 | 18 | 0 | 2428.829 (n=18) | 0.83 (n=18) | 0.00 (n=18) |
| electricity_peak_mw | model | 2 | 17 | 0 | 2149.998 (n=17) | 0.71 (n=17) | 0.26 (n=17) |
| electricity_peak_mw | model | 3 | 16 | 0 | 2653.566 (n=16) | 0.81 (n=16) | 0.21 (n=16) |
| electricity_peak_mw | model | 4 | 15 | 0 | 2179.933 (n=15) | 0.87 (n=15) | 0.41 (n=15) |
| electricity_peak_mw | model | 5 | 14 | 0 | 2349.679 (n=14) | 0.79 (n=14) | 0.37 (n=14) |
| electricity_peak_mw | model | 6 | 13 | 0 | 3119.012 (n=13) | 0.85 (n=13) | 0.22 (n=13) |
| electricity_peak_mw | model | 7 | 12 | 0 | 3947.694 (n=12) | 0.83 (n=12) | -0.01 (n=12) |
| electricity_peak_mw | persistence | 1 | 18 | 0 | 2432.056 (n=18) | 0.89 (n=18) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 17 | 0 | 2900.294 (n=17) | 0.94 (n=17) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 16 | 0 | 3351.438 (n=16) | 0.88 (n=16) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 15 | 0 | 3720.733 (n=15) | 0.87 (n=15) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 14 | 0 | 3743.857 (n=14) | 0.93 (n=14) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 13 | 0 | 3977.846 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 12 | 0 | 3909.083 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 18 | 0 | 3534.056 (n=18) | 1.00 (n=18) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 17 | 0 | 3835.706 (n=17) | 1.00 (n=17) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 16 | 0 | 3753.000 (n=16) | 1.00 (n=16) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 15 | 0 | 3768.333 (n=15) | 1.00 (n=15) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 14 | 0 | 3981.071 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 13 | 0 | 3977.846 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 12 | 0 | 6364.583 (n=12) | 1.00 (n=12) | - (n=0) |
| river_discharge_cfs | model | 1 | 17 | 0 | 214.624 (n=17) | 0.76 (n=17) | -0.76 (n=17) |
| river_discharge_cfs | model | 2 | 16 | 0 | 236.473 (n=16) | 0.69 (n=16) | -0.56 (n=16) |
| river_discharge_cfs | model | 3 | 15 | 0 | 236.146 (n=15) | 0.93 (n=15) | -0.53 (n=15) |
| river_discharge_cfs | model | 4 | 15 | 0 | 250.675 (n=15) | 0.87 (n=15) | -0.64 (n=15) |
| river_discharge_cfs | model | 5 | 14 | 0 | 233.840 (n=14) | 1.00 (n=14) | -0.44 (n=14) |
| river_discharge_cfs | model | 6 | 14 | 0 | 219.909 (n=14) | 1.00 (n=14) | -0.34 (n=14) |
| river_discharge_cfs | model | 7 | 13 | 0 | 286.970 (n=13) | 0.92 (n=13) | -0.51 (n=13) |
| river_discharge_cfs | persistence | 1 | 17 | 0 | 188.212 (n=17) | 0.76 (n=17) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 16 | 0 | 224.939 (n=16) | 0.75 (n=16) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 15 | 0 | 210.091 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 15 | 0 | 214.357 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 14 | 0 | 180.982 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 14 | 0 | 164.202 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 13 | 0 | 189.861 (n=13) | 0.92 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 17 | 0 | 122.174 (n=17) | 0.88 (n=17) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 16 | 0 | 151.758 (n=16) | 0.81 (n=16) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 15 | 0 | 154.103 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 15 | 0 | 153.210 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 14 | 0 | 162.798 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 14 | 0 | 164.202 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 13 | 0 | 202.805 (n=13) | 1.00 (n=13) | - (n=0) |
<!-- results:end -->
