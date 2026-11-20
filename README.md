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
| weather_tmax | model | 1 | 15 | 0 | 2.805 (n=15) | 0.73 (n=15) | 0.25 (n=15) |
| weather_tmax | model | 2 | 14 | 0 | 3.606 (n=14) | 0.57 (n=14) | 0.07 (n=14) |
| weather_tmax | model | 3 | 13 | 0 | 3.777 (n=13) | 0.46 (n=13) | 0.06 (n=13) |
| weather_tmax | model | 4 | 12 | 0 | 3.679 (n=12) | 0.58 (n=12) | 0.04 (n=12) |
| weather_tmax | model | 5 | 11 | 0 | 3.771 (n=11) | 0.45 (n=11) | -0.12 (n=11) |
| weather_tmax | model | 6 | 10 | 0 | 4.580 (n=10) | 0.30 (n=10) | -0.32 (n=10) |
| weather_tmax | model | 7 | 9 | 0 | 4.494 (n=9) | 0.33 (n=9) | -0.21 (n=9) |
| weather_tmax | persistence | 1 | 15 | 0 | 4.007 (n=15) | 0.33 (n=15) | - (n=0) |
| weather_tmax | persistence | 2 | 14 | 0 | 4.343 (n=14) | 0.36 (n=14) | - (n=0) |
| weather_tmax | persistence | 3 | 13 | 0 | 4.454 (n=13) | 0.54 (n=13) | - (n=0) |
| weather_tmax | persistence | 4 | 12 | 0 | 3.850 (n=12) | 0.67 (n=12) | - (n=0) |
| weather_tmax | persistence | 5 | 11 | 0 | 3.355 (n=11) | 0.82 (n=11) | - (n=0) |
| weather_tmax | persistence | 6 | 10 | 0 | 3.470 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | persistence | 7 | 9 | 0 | 3.711 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 15 | 0 | 3.760 (n=15) | 0.80 (n=15) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 14 | 0 | 3.857 (n=14) | 0.79 (n=14) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 13 | 0 | 4.031 (n=13) | 0.77 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 12 | 0 | 4.333 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 11 | 0 | 4.691 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 10 | 0 | 3.470 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 9 | 0 | 6.311 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | model | 1 | 16 | 0 | 15.014 (n=16) | 0.69 (n=16) | 0.24 (n=16) |
| air_quality_aqi | model | 2 | 15 | 0 | 15.539 (n=15) | 0.53 (n=15) | 0.31 (n=15) |
| air_quality_aqi | model | 3 | 14 | 0 | 16.690 (n=14) | 0.57 (n=14) | 0.23 (n=14) |
| air_quality_aqi | model | 4 | 13 | 0 | 15.549 (n=13) | 0.46 (n=13) | 0.13 (n=13) |
| air_quality_aqi | model | 5 | 12 | 0 | 14.556 (n=12) | 0.58 (n=12) | 0.36 (n=12) |
| air_quality_aqi | model | 6 | 11 | 0 | 12.647 (n=11) | 0.64 (n=11) | 0.45 (n=11) |
| air_quality_aqi | model | 7 | 10 | 0 | 15.226 (n=10) | 0.50 (n=10) | 0.16 (n=10) |
| air_quality_aqi | persistence | 1 | 16 | 0 | 19.652 (n=16) | 0.50 (n=16) | - (n=0) |
| air_quality_aqi | persistence | 2 | 15 | 0 | 22.662 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | persistence | 3 | 14 | 0 | 21.588 (n=14) | 0.57 (n=14) | - (n=0) |
| air_quality_aqi | persistence | 4 | 13 | 0 | 17.918 (n=13) | 0.69 (n=13) | - (n=0) |
| air_quality_aqi | persistence | 5 | 12 | 0 | 22.766 (n=12) | 0.42 (n=12) | - (n=0) |
| air_quality_aqi | persistence | 6 | 11 | 0 | 22.922 (n=11) | 0.55 (n=11) | - (n=0) |
| air_quality_aqi | persistence | 7 | 10 | 0 | 25.498 (n=10) | 0.40 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 16 | 0 | 22.629 (n=16) | 0.56 (n=16) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 15 | 0 | 24.076 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 14 | 0 | 25.335 (n=14) | 0.50 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 13 | 0 | 24.550 (n=13) | 0.46 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 12 | 0 | 24.259 (n=12) | 0.50 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 11 | 0 | 22.922 (n=11) | 0.55 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 10 | 0 | 18.040 (n=10) | 0.60 (n=10) | - (n=0) |
| electricity_peak_mw | model | 1 | 15 | 0 | 2831.801 (n=15) | 0.80 (n=15) | -0.01 (n=15) |
| electricity_peak_mw | model | 2 | 14 | 0 | 2462.718 (n=14) | 0.64 (n=14) | 0.28 (n=14) |
| electricity_peak_mw | model | 3 | 13 | 0 | 2747.353 (n=13) | 0.85 (n=13) | 0.31 (n=13) |
| electricity_peak_mw | model | 4 | 12 | 0 | 2460.512 (n=12) | 0.83 (n=12) | 0.43 (n=12) |
| electricity_peak_mw | model | 5 | 12 | 0 | 2224.484 (n=12) | 0.83 (n=12) | 0.45 (n=12) |
| electricity_peak_mw | model | 6 | 11 | 0 | 3215.012 (n=11) | 0.91 (n=11) | 0.25 (n=11) |
| electricity_peak_mw | model | 7 | 10 | 0 | 3602.855 (n=10) | 1.00 (n=10) | 0.16 (n=10) |
| electricity_peak_mw | persistence | 1 | 15 | 0 | 2806.267 (n=15) | 0.87 (n=15) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 14 | 0 | 3435.286 (n=14) | 0.93 (n=14) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 13 | 0 | 3990.846 (n=13) | 0.85 (n=13) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 12 | 0 | 4423.500 (n=12) | 0.83 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 12 | 0 | 4024.250 (n=12) | 0.92 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 11 | 0 | 4296.909 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 10 | 0 | 4265.900 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 15 | 0 | 3931.733 (n=15) | 1.00 (n=15) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 14 | 0 | 4326.429 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 13 | 0 | 4262.385 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 12 | 0 | 4324.000 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 12 | 0 | 4460.917 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 11 | 0 | 4296.909 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 10 | 0 | 6665.600 (n=10) | 1.00 (n=10) | - (n=0) |
| river_discharge_cfs | model | 1 | 15 | 0 | 171.581 (n=15) | 0.87 (n=15) | -0.30 (n=15) |
| river_discharge_cfs | model | 2 | 14 | 0 | 198.801 (n=14) | 0.79 (n=14) | -0.19 (n=14) |
| river_discharge_cfs | model | 3 | 14 | 0 | 196.494 (n=14) | 1.00 (n=14) | -0.22 (n=14) |
| river_discharge_cfs | model | 4 | 13 | 0 | 242.358 (n=13) | 0.92 (n=13) | -0.42 (n=13) |
| river_discharge_cfs | model | 5 | 12 | 0 | 258.164 (n=12) | 1.00 (n=12) | -0.41 (n=12) |
| river_discharge_cfs | model | 6 | 11 | 0 | 248.012 (n=11) | 1.00 (n=11) | -0.26 (n=11) |
| river_discharge_cfs | model | 7 | 10 | 0 | 310.600 (n=10) | 0.90 (n=10) | -0.33 (n=10) |
| river_discharge_cfs | persistence | 1 | 15 | 0 | 193.334 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 14 | 0 | 198.949 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 14 | 0 | 178.209 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 13 | 0 | 183.114 (n=13) | 0.85 (n=13) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 12 | 0 | 194.518 (n=12) | 0.83 (n=12) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 11 | 0 | 196.652 (n=11) | 0.73 (n=11) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 10 | 0 | 232.881 (n=10) | 0.90 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 15 | 0 | 131.856 (n=15) | 0.87 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 14 | 0 | 167.345 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 14 | 0 | 161.513 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 13 | 0 | 170.220 (n=13) | 0.77 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 12 | 0 | 182.688 (n=12) | 0.75 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 11 | 0 | 196.652 (n=11) | 0.73 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 10 | 0 | 233.808 (n=10) | 1.00 (n=10) | - (n=0) |
<!-- results:end -->
