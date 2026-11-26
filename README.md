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
| weather_tmax | model | 1 | 20 | 0 | 3.530 (n=20) | 0.65 (n=20) | 0.06 (n=20) |
| weather_tmax | model | 2 | 19 | 0 | 4.144 (n=19) | 0.53 (n=19) | -0.14 (n=19) |
| weather_tmax | model | 3 | 18 | 0 | 4.486 (n=18) | 0.33 (n=18) | -0.05 (n=18) |
| weather_tmax | model | 4 | 17 | 0 | 4.133 (n=17) | 0.53 (n=17) | 0.03 (n=17) |
| weather_tmax | model | 5 | 17 | 0 | 4.025 (n=17) | 0.41 (n=17) | 0.02 (n=17) |
| weather_tmax | model | 6 | 16 | 0 | 4.418 (n=16) | 0.31 (n=16) | -0.19 (n=16) |
| weather_tmax | model | 7 | 15 | 0 | 4.101 (n=15) | 0.47 (n=15) | -0.29 (n=15) |
| weather_tmax | persistence | 1 | 20 | 0 | 4.505 (n=20) | 0.25 (n=20) | - (n=0) |
| weather_tmax | persistence | 2 | 19 | 0 | 4.832 (n=19) | 0.26 (n=19) | - (n=0) |
| weather_tmax | persistence | 3 | 18 | 0 | 5.167 (n=18) | 0.39 (n=18) | - (n=0) |
| weather_tmax | persistence | 4 | 17 | 0 | 4.606 (n=17) | 0.53 (n=17) | - (n=0) |
| weather_tmax | persistence | 5 | 17 | 0 | 4.088 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | persistence | 6 | 16 | 0 | 3.719 (n=16) | 0.69 (n=16) | - (n=0) |
| weather_tmax | persistence | 7 | 15 | 0 | 3.173 (n=15) | 0.73 (n=15) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 20 | 0 | 3.760 (n=20) | 0.80 (n=20) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 19 | 0 | 3.637 (n=19) | 0.79 (n=19) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 18 | 0 | 4.267 (n=18) | 0.72 (n=18) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 17 | 0 | 4.247 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 17 | 0 | 4.518 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 16 | 0 | 3.719 (n=16) | 0.69 (n=16) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 15 | 0 | 5.513 (n=15) | 0.60 (n=15) | - (n=0) |
| air_quality_aqi | model | 1 | 22 | 0 | 14.156 (n=22) | 0.73 (n=22) | 0.28 (n=22) |
| air_quality_aqi | model | 2 | 21 | 0 | 15.009 (n=21) | 0.57 (n=21) | 0.35 (n=21) |
| air_quality_aqi | model | 3 | 20 | 0 | 14.756 (n=20) | 0.65 (n=20) | 0.33 (n=20) |
| air_quality_aqi | model | 4 | 19 | 0 | 13.826 (n=19) | 0.58 (n=19) | 0.29 (n=19) |
| air_quality_aqi | model | 5 | 18 | 0 | 12.379 (n=18) | 0.67 (n=18) | 0.45 (n=18) |
| air_quality_aqi | model | 6 | 17 | 0 | 10.969 (n=17) | 0.71 (n=17) | 0.52 (n=17) |
| air_quality_aqi | model | 7 | 16 | 0 | 12.893 (n=16) | 0.62 (n=16) | 0.23 (n=16) |
| air_quality_aqi | persistence | 1 | 22 | 0 | 19.738 (n=22) | 0.50 (n=22) | - (n=0) |
| air_quality_aqi | persistence | 2 | 21 | 0 | 22.977 (n=21) | 0.48 (n=21) | - (n=0) |
| air_quality_aqi | persistence | 3 | 20 | 0 | 22.030 (n=20) | 0.55 (n=20) | - (n=0) |
| air_quality_aqi | persistence | 4 | 19 | 0 | 19.576 (n=19) | 0.63 (n=19) | - (n=0) |
| air_quality_aqi | persistence | 5 | 18 | 0 | 22.668 (n=18) | 0.50 (n=18) | - (n=0) |
| air_quality_aqi | persistence | 6 | 17 | 0 | 23.067 (n=17) | 0.53 (n=17) | - (n=0) |
| air_quality_aqi | persistence | 7 | 16 | 0 | 23.376 (n=16) | 0.50 (n=16) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 22 | 0 | 22.821 (n=22) | 0.55 (n=22) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 21 | 0 | 23.864 (n=21) | 0.52 (n=21) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 20 | 0 | 24.734 (n=20) | 0.50 (n=20) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 19 | 0 | 24.166 (n=19) | 0.47 (n=19) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 18 | 0 | 23.950 (n=18) | 0.50 (n=18) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 17 | 0 | 23.067 (n=17) | 0.53 (n=17) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 16 | 0 | 16.829 (n=16) | 0.62 (n=16) | - (n=0) |
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
| river_discharge_cfs | model | 1 | 20 | 0 | 205.787 (n=20) | 0.80 (n=20) | -0.22 (n=20) |
| river_discharge_cfs | model | 2 | 19 | 0 | 251.049 (n=19) | 0.63 (n=19) | -0.22 (n=19) |
| river_discharge_cfs | model | 3 | 18 | 0 | 286.783 (n=18) | 0.78 (n=18) | -0.40 (n=18) |
| river_discharge_cfs | model | 4 | 17 | 0 | 279.122 (n=17) | 0.76 (n=17) | -0.32 (n=17) |
| river_discharge_cfs | model | 5 | 16 | 0 | 270.238 (n=16) | 0.88 (n=16) | -0.30 (n=16) |
| river_discharge_cfs | model | 6 | 15 | 0 | 246.907 (n=15) | 0.93 (n=15) | -0.21 (n=15) |
| river_discharge_cfs | model | 7 | 15 | 0 | 281.988 (n=15) | 0.87 (n=15) | -0.55 (n=15) |
| river_discharge_cfs | persistence | 1 | 20 | 0 | 168.540 (n=20) | 0.80 (n=20) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 19 | 0 | 205.631 (n=19) | 0.79 (n=19) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 18 | 0 | 204.876 (n=18) | 0.83 (n=18) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 17 | 0 | 216.833 (n=17) | 0.82 (n=17) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 16 | 0 | 222.534 (n=16) | 0.81 (n=16) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 15 | 0 | 203.345 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 15 | 0 | 216.173 (n=15) | 0.87 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 20 | 0 | 194.314 (n=20) | 0.80 (n=20) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 19 | 0 | 223.023 (n=19) | 0.68 (n=19) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 18 | 0 | 228.937 (n=18) | 0.67 (n=18) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 17 | 0 | 211.439 (n=17) | 0.71 (n=17) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 16 | 0 | 208.572 (n=16) | 0.69 (n=16) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 15 | 0 | 203.345 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 15 | 0 | 182.433 (n=15) | 1.00 (n=15) | - (n=0) |
<!-- results:end -->
