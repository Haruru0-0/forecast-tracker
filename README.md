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
| weather_tmax | model | 2 | 16 | 0 | 3.643 (n=16) | 0.56 (n=16) | -0.02 (n=16) |
| weather_tmax | model | 3 | 15 | 0 | 3.962 (n=15) | 0.40 (n=15) | -0.07 (n=15) |
| weather_tmax | model | 4 | 14 | 0 | 3.828 (n=14) | 0.57 (n=14) | 0.02 (n=14) |
| weather_tmax | model | 5 | 13 | 0 | 3.638 (n=13) | 0.46 (n=13) | -0.06 (n=13) |
| weather_tmax | model | 6 | 12 | 0 | 3.887 (n=12) | 0.42 (n=12) | -0.28 (n=12) |
| weather_tmax | model | 7 | 11 | 0 | 3.796 (n=11) | 0.45 (n=11) | -0.22 (n=11) |
| weather_tmax | persistence | 1 | 17 | 0 | 4.041 (n=17) | 0.29 (n=17) | - (n=0) |
| weather_tmax | persistence | 2 | 16 | 0 | 4.500 (n=16) | 0.31 (n=16) | - (n=0) |
| weather_tmax | persistence | 3 | 15 | 0 | 4.787 (n=15) | 0.47 (n=15) | - (n=0) |
| weather_tmax | persistence | 4 | 14 | 0 | 4.286 (n=14) | 0.57 (n=14) | - (n=0) |
| weather_tmax | persistence | 5 | 13 | 0 | 3.431 (n=13) | 0.77 (n=13) | - (n=0) |
| weather_tmax | persistence | 6 | 12 | 0 | 3.025 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | persistence | 7 | 11 | 0 | 3.109 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 17 | 0 | 3.488 (n=17) | 0.82 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 16 | 0 | 3.556 (n=16) | 0.81 (n=16) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 15 | 0 | 3.687 (n=15) | 0.80 (n=15) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 14 | 0 | 3.921 (n=14) | 0.79 (n=14) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 13 | 0 | 4.192 (n=13) | 0.77 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 12 | 0 | 3.025 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 11 | 0 | 5.927 (n=11) | 0.64 (n=11) | - (n=0) |
| air_quality_aqi | model | 1 | 18 | 0 | 14.201 (n=18) | 0.72 (n=18) | 0.27 (n=18) |
| air_quality_aqi | model | 2 | 17 | 0 | 14.205 (n=17) | 0.59 (n=17) | 0.37 (n=17) |
| air_quality_aqi | model | 3 | 16 | 0 | 15.281 (n=16) | 0.62 (n=16) | 0.32 (n=16) |
| air_quality_aqi | model | 4 | 15 | 0 | 14.202 (n=15) | 0.53 (n=15) | 0.20 (n=15) |
| air_quality_aqi | model | 5 | 14 | 0 | 12.666 (n=14) | 0.64 (n=14) | 0.38 (n=14) |
| air_quality_aqi | model | 6 | 13 | 0 | 11.251 (n=13) | 0.69 (n=13) | 0.47 (n=13) |
| air_quality_aqi | model | 7 | 12 | 0 | 13.053 (n=12) | 0.58 (n=12) | 0.33 (n=12) |
| air_quality_aqi | persistence | 1 | 18 | 0 | 19.515 (n=18) | 0.50 (n=18) | - (n=0) |
| air_quality_aqi | persistence | 2 | 17 | 0 | 23.131 (n=17) | 0.47 (n=17) | - (n=0) |
| air_quality_aqi | persistence | 3 | 16 | 0 | 22.348 (n=16) | 0.50 (n=16) | - (n=0) |
| air_quality_aqi | persistence | 4 | 15 | 0 | 17.790 (n=15) | 0.67 (n=15) | - (n=0) |
| air_quality_aqi | persistence | 5 | 14 | 0 | 20.505 (n=14) | 0.50 (n=14) | - (n=0) |
| air_quality_aqi | persistence | 6 | 13 | 0 | 21.242 (n=13) | 0.62 (n=13) | - (n=0) |
| air_quality_aqi | persistence | 7 | 12 | 0 | 23.974 (n=12) | 0.50 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 18 | 0 | 21.448 (n=18) | 0.61 (n=18) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 17 | 0 | 22.656 (n=17) | 0.59 (n=17) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 16 | 0 | 23.668 (n=16) | 0.56 (n=16) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 15 | 0 | 22.876 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 14 | 0 | 22.507 (n=14) | 0.57 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 13 | 0 | 21.242 (n=13) | 0.62 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 12 | 0 | 19.595 (n=12) | 0.50 (n=12) | - (n=0) |
| electricity_peak_mw | model | 1 | 17 | 0 | 2566.742 (n=17) | 0.82 (n=17) | -0.01 (n=17) |
| electricity_peak_mw | model | 2 | 16 | 0 | 2221.054 (n=16) | 0.69 (n=16) | 0.28 (n=16) |
| electricity_peak_mw | model | 3 | 15 | 0 | 2753.610 (n=15) | 0.80 (n=15) | 0.23 (n=15) |
| electricity_peak_mw | model | 4 | 14 | 0 | 2294.194 (n=14) | 0.86 (n=14) | 0.41 (n=14) |
| electricity_peak_mw | model | 5 | 13 | 0 | 2242.132 (n=13) | 0.85 (n=13) | 0.43 (n=13) |
| electricity_peak_mw | model | 6 | 12 | 0 | 3293.616 (n=12) | 0.83 (n=12) | 0.20 (n=12) |
| electricity_peak_mw | model | 7 | 12 | 0 | 3947.694 (n=12) | 0.83 (n=12) | -0.01 (n=12) |
| electricity_peak_mw | persistence | 1 | 17 | 0 | 2547.647 (n=17) | 0.88 (n=17) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 16 | 0 | 3079.062 (n=16) | 0.94 (n=16) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 15 | 0 | 3562.600 (n=15) | 0.87 (n=15) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 14 | 0 | 3980.429 (n=14) | 0.86 (n=14) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 13 | 0 | 3944.385 (n=13) | 0.92 (n=13) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 12 | 0 | 4141.583 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 12 | 0 | 3909.083 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 17 | 0 | 3623.529 (n=17) | 1.00 (n=17) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 16 | 0 | 3949.625 (n=16) | 1.00 (n=16) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 15 | 0 | 3869.000 (n=15) | 1.00 (n=15) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 14 | 0 | 3893.714 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 13 | 0 | 4132.462 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 12 | 0 | 4141.583 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 12 | 0 | 6364.583 (n=12) | 1.00 (n=12) | - (n=0) |
| river_discharge_cfs | model | 1 | 16 | 0 | 207.612 (n=16) | 0.81 (n=16) | -0.64 (n=16) |
| river_discharge_cfs | model | 2 | 15 | 0 | 218.642 (n=15) | 0.73 (n=15) | -0.38 (n=15) |
| river_discharge_cfs | model | 3 | 15 | 0 | 236.146 (n=15) | 0.93 (n=15) | -0.53 (n=15) |
| river_discharge_cfs | model | 4 | 14 | 0 | 226.641 (n=14) | 0.93 (n=14) | -0.41 (n=14) |
| river_discharge_cfs | model | 5 | 14 | 0 | 233.840 (n=14) | 1.00 (n=14) | -0.44 (n=14) |
| river_discharge_cfs | model | 6 | 13 | 0 | 232.126 (n=13) | 1.00 (n=13) | -0.34 (n=13) |
| river_discharge_cfs | model | 7 | 12 | 0 | 297.433 (n=12) | 0.92 (n=12) | -0.46 (n=12) |
| river_discharge_cfs | persistence | 1 | 16 | 0 | 193.700 (n=16) | 0.75 (n=16) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 15 | 0 | 224.705 (n=15) | 0.73 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 15 | 0 | 210.091 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 14 | 0 | 180.689 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 14 | 0 | 180.982 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 13 | 0 | 173.083 (n=13) | 0.77 (n=13) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 12 | 0 | 203.924 (n=12) | 0.92 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 16 | 0 | 126.763 (n=16) | 0.88 (n=16) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 15 | 0 | 158.625 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 15 | 0 | 154.103 (n=15) | 0.80 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 14 | 0 | 160.672 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 14 | 0 | 162.798 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 13 | 0 | 173.083 (n=13) | 0.77 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 12 | 0 | 212.976 (n=12) | 1.00 (n=12) | - (n=0) |
<!-- results:end -->
