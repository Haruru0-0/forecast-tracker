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
| weather_tmax | model | 1 | 16 | 0 | 2.764 (n=16) | 0.75 (n=16) | 0.24 (n=16) |
| weather_tmax | model | 2 | 15 | 0 | 3.657 (n=15) | 0.53 (n=15) | 0.02 (n=15) |
| weather_tmax | model | 3 | 14 | 0 | 3.861 (n=14) | 0.43 (n=14) | 0.00 (n=14) |
| weather_tmax | model | 4 | 13 | 0 | 3.572 (n=13) | 0.62 (n=13) | 0.12 (n=13) |
| weather_tmax | model | 5 | 12 | 0 | 3.506 (n=12) | 0.50 (n=12) | -0.11 (n=12) |
| weather_tmax | model | 6 | 11 | 0 | 4.185 (n=11) | 0.36 (n=11) | -0.30 (n=11) |
| weather_tmax | model | 7 | 10 | 0 | 4.116 (n=10) | 0.40 (n=10) | -0.22 (n=10) |
| weather_tmax | persistence | 1 | 16 | 0 | 4.038 (n=16) | 0.31 (n=16) | - (n=0) |
| weather_tmax | persistence | 2 | 15 | 0 | 4.493 (n=15) | 0.33 (n=15) | - (n=0) |
| weather_tmax | persistence | 3 | 14 | 0 | 4.650 (n=14) | 0.50 (n=14) | - (n=0) |
| weather_tmax | persistence | 4 | 13 | 0 | 4.054 (n=13) | 0.62 (n=13) | - (n=0) |
| weather_tmax | persistence | 5 | 12 | 0 | 3.167 (n=12) | 0.83 (n=12) | - (n=0) |
| weather_tmax | persistence | 6 | 11 | 0 | 3.209 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | persistence | 7 | 10 | 0 | 3.370 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 16 | 0 | 3.631 (n=16) | 0.81 (n=16) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 15 | 0 | 3.713 (n=15) | 0.80 (n=15) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 14 | 0 | 3.864 (n=14) | 0.79 (n=14) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 13 | 0 | 4.131 (n=13) | 0.77 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 12 | 0 | 4.442 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 11 | 0 | 3.209 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 10 | 0 | 6.050 (n=10) | 0.60 (n=10) | - (n=0) |
| air_quality_aqi | model | 1 | 17 | 0 | 14.374 (n=17) | 0.71 (n=17) | 0.28 (n=17) |
| air_quality_aqi | model | 2 | 16 | 0 | 14.925 (n=16) | 0.56 (n=16) | 0.35 (n=16) |
| air_quality_aqi | model | 3 | 15 | 0 | 15.626 (n=15) | 0.60 (n=15) | 0.29 (n=15) |
| air_quality_aqi | model | 4 | 14 | 0 | 14.726 (n=14) | 0.50 (n=14) | 0.13 (n=14) |
| air_quality_aqi | model | 5 | 13 | 0 | 13.527 (n=13) | 0.62 (n=13) | 0.37 (n=13) |
| air_quality_aqi | model | 6 | 12 | 0 | 11.868 (n=12) | 0.67 (n=12) | 0.48 (n=12) |
| air_quality_aqi | model | 7 | 11 | 0 | 13.969 (n=11) | 0.55 (n=11) | 0.28 (n=11) |
| air_quality_aqi | persistence | 1 | 17 | 0 | 19.898 (n=17) | 0.47 (n=17) | - (n=0) |
| air_quality_aqi | persistence | 2 | 16 | 0 | 22.855 (n=16) | 0.50 (n=16) | - (n=0) |
| air_quality_aqi | persistence | 3 | 15 | 0 | 21.874 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | persistence | 4 | 14 | 0 | 16.948 (n=14) | 0.71 (n=14) | - (n=0) |
| air_quality_aqi | persistence | 5 | 13 | 0 | 21.463 (n=13) | 0.46 (n=13) | - (n=0) |
| air_quality_aqi | persistence | 6 | 12 | 0 | 22.835 (n=12) | 0.58 (n=12) | - (n=0) |
| air_quality_aqi | persistence | 7 | 11 | 0 | 24.502 (n=11) | 0.45 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 17 | 0 | 22.585 (n=17) | 0.59 (n=17) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 16 | 0 | 23.939 (n=16) | 0.56 (n=16) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 15 | 0 | 25.104 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 14 | 0 | 24.359 (n=14) | 0.50 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 13 | 0 | 24.075 (n=13) | 0.54 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 12 | 0 | 22.835 (n=12) | 0.58 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 11 | 0 | 19.449 (n=11) | 0.55 (n=11) | - (n=0) |
| electricity_peak_mw | model | 1 | 16 | 0 | 2698.906 (n=16) | 0.81 (n=16) | -0.02 (n=16) |
| electricity_peak_mw | model | 2 | 15 | 0 | 2363.610 (n=15) | 0.67 (n=15) | 0.27 (n=15) |
| electricity_peak_mw | model | 3 | 14 | 0 | 2860.291 (n=14) | 0.79 (n=14) | 0.24 (n=14) |
| electricity_peak_mw | model | 4 | 13 | 0 | 2312.058 (n=13) | 0.85 (n=13) | 0.45 (n=13) |
| electricity_peak_mw | model | 5 | 12 | 0 | 2224.484 (n=12) | 0.83 (n=12) | 0.45 (n=12) |
| electricity_peak_mw | model | 6 | 12 | 0 | 3293.616 (n=12) | 0.83 (n=12) | 0.20 (n=12) |
| electricity_peak_mw | model | 7 | 11 | 0 | 3796.908 (n=11) | 0.91 (n=11) | 0.07 (n=11) |
| electricity_peak_mw | persistence | 1 | 16 | 0 | 2648.562 (n=16) | 0.88 (n=16) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 15 | 0 | 3231.733 (n=15) | 0.93 (n=15) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 14 | 0 | 3753.643 (n=14) | 0.86 (n=14) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 13 | 0 | 4274.000 (n=13) | 0.85 (n=13) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 12 | 0 | 4024.250 (n=12) | 0.92 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 12 | 0 | 4141.583 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 11 | 0 | 4089.273 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 16 | 0 | 3838.062 (n=16) | 1.00 (n=16) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 15 | 0 | 4200.200 (n=15) | 1.00 (n=15) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 14 | 0 | 4131.714 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 13 | 0 | 4178.538 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 12 | 0 | 4460.917 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 12 | 0 | 4141.583 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 11 | 0 | 6688.636 (n=11) | 1.00 (n=11) | - (n=0) |
| river_discharge_cfs | model | 1 | 15 | 0 | 171.581 (n=15) | 0.87 (n=15) | -0.30 (n=15) |
| river_discharge_cfs | model | 2 | 15 | 0 | 218.642 (n=15) | 0.73 (n=15) | -0.38 (n=15) |
| river_discharge_cfs | model | 3 | 14 | 0 | 196.494 (n=14) | 1.00 (n=14) | -0.22 (n=14) |
| river_discharge_cfs | model | 4 | 14 | 0 | 226.641 (n=14) | 0.93 (n=14) | -0.41 (n=14) |
| river_discharge_cfs | model | 5 | 13 | 0 | 239.054 (n=13) | 1.00 (n=13) | -0.39 (n=13) |
| river_discharge_cfs | model | 6 | 12 | 0 | 234.932 (n=12) | 1.00 (n=12) | -0.28 (n=12) |
| river_discharge_cfs | model | 7 | 11 | 0 | 284.598 (n=11) | 0.91 (n=11) | -0.30 (n=11) |
| river_discharge_cfs | persistence | 1 | 15 | 0 | 193.334 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 15 | 0 | 224.705 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 14 | 0 | 178.209 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 14 | 0 | 180.689 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 13 | 0 | 188.902 (n=13) | 0.85 (n=13) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 12 | 0 | 183.310 (n=12) | 0.75 (n=12) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 11 | 0 | 219.317 (n=11) | 0.91 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 15 | 0 | 131.856 (n=15) | 0.87 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 15 | 0 | 158.625 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 14 | 0 | 161.513 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 14 | 0 | 160.672 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 13 | 0 | 171.446 (n=13) | 0.77 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 12 | 0 | 183.310 (n=12) | 0.75 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 11 | 0 | 224.284 (n=11) | 1.00 (n=11) | - (n=0) |
<!-- results:end -->
