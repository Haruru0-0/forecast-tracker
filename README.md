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
| weather_tmax | model | 1 | 18 | 0 | 2.855 (n=18) | 0.72 (n=18) | 0.26 (n=18) |
| weather_tmax | model | 2 | 17 | 0 | 3.654 (n=17) | 0.59 (n=17) | 0.02 (n=17) |
| weather_tmax | model | 3 | 17 | 0 | 4.141 (n=17) | 0.35 (n=17) | 0.02 (n=17) |
| weather_tmax | model | 4 | 16 | 0 | 4.222 (n=16) | 0.50 (n=16) | 0.05 (n=16) |
| weather_tmax | model | 5 | 15 | 0 | 4.066 (n=15) | 0.40 (n=15) | 0.04 (n=15) |
| weather_tmax | model | 6 | 14 | 0 | 4.025 (n=14) | 0.36 (n=14) | -0.02 (n=14) |
| weather_tmax | model | 7 | 13 | 0 | 3.524 (n=13) | 0.54 (n=13) | -0.02 (n=13) |
| weather_tmax | persistence | 1 | 18 | 0 | 4.044 (n=18) | 0.28 (n=18) | - (n=0) |
| weather_tmax | persistence | 2 | 17 | 0 | 4.576 (n=17) | 0.29 (n=17) | - (n=0) |
| weather_tmax | persistence | 3 | 17 | 0 | 5.024 (n=17) | 0.41 (n=17) | - (n=0) |
| weather_tmax | persistence | 4 | 16 | 0 | 4.762 (n=16) | 0.50 (n=16) | - (n=0) |
| weather_tmax | persistence | 5 | 15 | 0 | 4.233 (n=15) | 0.67 (n=15) | - (n=0) |
| weather_tmax | persistence | 6 | 14 | 0 | 3.936 (n=14) | 0.64 (n=14) | - (n=0) |
| weather_tmax | persistence | 7 | 13 | 0 | 3.438 (n=13) | 0.69 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 18 | 0 | 3.856 (n=18) | 0.78 (n=18) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 17 | 0 | 3.724 (n=17) | 0.76 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 17 | 0 | 4.224 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 16 | 0 | 4.463 (n=16) | 0.69 (n=16) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 15 | 0 | 4.733 (n=15) | 0.67 (n=15) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 14 | 0 | 3.936 (n=14) | 0.64 (n=14) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 13 | 0 | 5.685 (n=13) | 0.62 (n=13) | - (n=0) |
| air_quality_aqi | model | 1 | 20 | 0 | 14.658 (n=20) | 0.70 (n=20) | 0.25 (n=20) |
| air_quality_aqi | model | 2 | 19 | 0 | 15.080 (n=19) | 0.58 (n=19) | 0.35 (n=19) |
| air_quality_aqi | model | 3 | 18 | 0 | 15.814 (n=18) | 0.61 (n=18) | 0.34 (n=18) |
| air_quality_aqi | model | 4 | 17 | 0 | 14.595 (n=17) | 0.53 (n=17) | 0.31 (n=17) |
| air_quality_aqi | model | 5 | 16 | 0 | 13.331 (n=16) | 0.62 (n=16) | 0.44 (n=16) |
| air_quality_aqi | model | 6 | 15 | 0 | 11.823 (n=15) | 0.67 (n=15) | 0.49 (n=15) |
| air_quality_aqi | model | 7 | 14 | 0 | 13.935 (n=14) | 0.57 (n=14) | 0.22 (n=14) |
| air_quality_aqi | persistence | 1 | 20 | 0 | 19.426 (n=20) | 0.50 (n=20) | - (n=0) |
| air_quality_aqi | persistence | 2 | 19 | 0 | 23.341 (n=19) | 0.47 (n=19) | - (n=0) |
| air_quality_aqi | persistence | 3 | 18 | 0 | 23.980 (n=18) | 0.50 (n=18) | - (n=0) |
| air_quality_aqi | persistence | 4 | 17 | 0 | 21.023 (n=17) | 0.59 (n=17) | - (n=0) |
| air_quality_aqi | persistence | 5 | 16 | 0 | 23.728 (n=16) | 0.44 (n=16) | - (n=0) |
| air_quality_aqi | persistence | 6 | 15 | 0 | 23.154 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | persistence | 7 | 14 | 0 | 23.368 (n=14) | 0.50 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 20 | 0 | 22.861 (n=20) | 0.55 (n=20) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 19 | 0 | 24.016 (n=19) | 0.53 (n=19) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 18 | 0 | 24.992 (n=18) | 0.50 (n=18) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 17 | 0 | 24.371 (n=17) | 0.47 (n=17) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 16 | 0 | 24.142 (n=16) | 0.50 (n=16) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 15 | 0 | 23.154 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 14 | 0 | 17.799 (n=14) | 0.57 (n=14) | - (n=0) |
| electricity_peak_mw | model | 1 | 19 | 0 | 2311.697 (n=19) | 0.84 (n=19) | 0.00 (n=19) |
| electricity_peak_mw | model | 2 | 18 | 0 | 2041.706 (n=18) | 0.72 (n=18) | 0.26 (n=18) |
| electricity_peak_mw | model | 3 | 17 | 0 | 2570.955 (n=17) | 0.82 (n=17) | 0.20 (n=17) |
| electricity_peak_mw | model | 4 | 16 | 0 | 2103.821 (n=16) | 0.88 (n=16) | 0.40 (n=16) |
| electricity_peak_mw | model | 5 | 15 | 0 | 2199.617 (n=15) | 0.80 (n=15) | 0.38 (n=15) |
| electricity_peak_mw | model | 6 | 14 | 0 | 3037.518 (n=14) | 0.86 (n=14) | 0.18 (n=14) |
| electricity_peak_mw | model | 7 | 13 | 0 | 3999.478 (n=13) | 0.77 (n=13) | -0.05 (n=13) |
| electricity_peak_mw | persistence | 1 | 19 | 0 | 2315.789 (n=19) | 0.89 (n=19) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 18 | 0 | 2754.889 (n=18) | 0.94 (n=18) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 17 | 0 | 3196.059 (n=17) | 0.88 (n=17) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 16 | 0 | 3523.562 (n=16) | 0.88 (n=16) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 15 | 0 | 3538.600 (n=15) | 0.93 (n=15) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 14 | 0 | 3721.357 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 13 | 0 | 3820.923 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 19 | 0 | 3368.421 (n=19) | 1.00 (n=19) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 18 | 0 | 3644.111 (n=18) | 1.00 (n=18) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 17 | 0 | 3555.000 (n=17) | 1.00 (n=17) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 16 | 0 | 3557.000 (n=16) | 1.00 (n=16) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 15 | 0 | 3741.467 (n=15) | 1.00 (n=15) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 14 | 0 | 3721.357 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 13 | 0 | 6062.154 (n=13) | 1.00 (n=13) | - (n=0) |
| river_discharge_cfs | model | 1 | 18 | 0 | 215.763 (n=18) | 0.78 (n=18) | -0.50 (n=18) |
| river_discharge_cfs | model | 2 | 17 | 0 | 251.276 (n=17) | 0.65 (n=17) | -0.45 (n=17) |
| river_discharge_cfs | model | 3 | 16 | 0 | 260.636 (n=16) | 0.88 (n=16) | -0.48 (n=16) |
| river_discharge_cfs | model | 4 | 15 | 0 | 250.675 (n=15) | 0.87 (n=15) | -0.64 (n=15) |
| river_discharge_cfs | model | 5 | 15 | 0 | 251.273 (n=15) | 0.93 (n=15) | -0.35 (n=15) |
| river_discharge_cfs | model | 6 | 14 | 0 | 219.909 (n=14) | 1.00 (n=14) | -0.34 (n=14) |
| river_discharge_cfs | model | 7 | 14 | 0 | 266.540 (n=14) | 0.93 (n=14) | -0.50 (n=14) |
| river_discharge_cfs | persistence | 1 | 18 | 0 | 181.401 (n=18) | 0.78 (n=18) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 17 | 0 | 219.752 (n=17) | 0.76 (n=17) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 16 | 0 | 213.510 (n=16) | 0.81 (n=16) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 15 | 0 | 214.357 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 15 | 0 | 217.054 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 14 | 0 | 164.202 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 14 | 0 | 177.185 (n=14) | 0.93 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 18 | 0 | 143.887 (n=18) | 0.83 (n=18) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 17 | 0 | 173.008 (n=17) | 0.76 (n=17) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 16 | 0 | 176.534 (n=16) | 0.75 (n=16) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 15 | 0 | 153.210 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 15 | 0 | 186.145 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 14 | 0 | 164.202 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 14 | 0 | 191.284 (n=14) | 1.00 (n=14) | - (n=0) |
<!-- results:end -->
