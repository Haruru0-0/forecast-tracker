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
| weather_tmax | model | 1 | 13 | 0 | 2.904 (n=13) | 0.69 (n=13) | 0.26 (n=13) |
| weather_tmax | model | 2 | 12 | 0 | 3.905 (n=12) | 0.50 (n=12) | 0.06 (n=12) |
| weather_tmax | model | 3 | 11 | 0 | 3.959 (n=11) | 0.45 (n=11) | 0.09 (n=11) |
| weather_tmax | model | 4 | 10 | 0 | 3.912 (n=10) | 0.60 (n=10) | 0.02 (n=10) |
| weather_tmax | model | 5 | 9 | 0 | 3.996 (n=9) | 0.44 (n=9) | -0.12 (n=9) |
| weather_tmax | model | 6 | 8 | 0 | 4.847 (n=8) | 0.25 (n=8) | -0.25 (n=8) |
| weather_tmax | model | 7 | 7 | 0 | 4.572 (n=7) | 0.29 (n=7) | -0.06 (n=7) |
| weather_tmax | persistence | 1 | 13 | 0 | 3.900 (n=13) | 0.38 (n=13) | - (n=0) |
| weather_tmax | persistence | 2 | 12 | 0 | 4.292 (n=12) | 0.42 (n=12) | - (n=0) |
| weather_tmax | persistence | 3 | 11 | 0 | 4.355 (n=11) | 0.55 (n=11) | - (n=0) |
| weather_tmax | persistence | 4 | 10 | 0 | 4.010 (n=10) | 0.60 (n=10) | - (n=0) |
| weather_tmax | persistence | 5 | 9 | 0 | 3.578 (n=9) | 0.78 (n=9) | - (n=0) |
| weather_tmax | persistence | 6 | 8 | 0 | 3.862 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | persistence | 7 | 7 | 0 | 4.314 (n=7) | 0.57 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 13 | 0 | 4.023 (n=13) | 0.77 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 12 | 0 | 4.158 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 11 | 0 | 4.391 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 10 | 0 | 4.790 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 9 | 0 | 5.278 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 8 | 0 | 3.862 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 7 | 0 | 6.586 (n=7) | 0.57 (n=7) | - (n=0) |
| air_quality_aqi | model | 1 | 14 | 0 | 15.716 (n=14) | 0.64 (n=14) | 0.26 (n=14) |
| air_quality_aqi | model | 2 | 13 | 0 | 16.223 (n=13) | 0.54 (n=13) | 0.30 (n=13) |
| air_quality_aqi | model | 3 | 12 | 0 | 17.333 (n=12) | 0.58 (n=12) | 0.22 (n=12) |
| air_quality_aqi | model | 4 | 11 | 0 | 15.173 (n=11) | 0.45 (n=11) | 0.03 (n=11) |
| air_quality_aqi | model | 5 | 10 | 0 | 15.104 (n=10) | 0.60 (n=10) | 0.26 (n=10) |
| air_quality_aqi | model | 6 | 9 | 0 | 12.776 (n=9) | 0.67 (n=9) | 0.40 (n=9) |
| air_quality_aqi | model | 7 | 8 | 0 | 15.583 (n=8) | 0.50 (n=8) | 0.22 (n=8) |
| air_quality_aqi | persistence | 1 | 14 | 0 | 21.138 (n=14) | 0.43 (n=14) | - (n=0) |
| air_quality_aqi | persistence | 2 | 13 | 0 | 23.373 (n=13) | 0.46 (n=13) | - (n=0) |
| air_quality_aqi | persistence | 3 | 12 | 0 | 22.300 (n=12) | 0.58 (n=12) | - (n=0) |
| air_quality_aqi | persistence | 4 | 11 | 0 | 15.646 (n=11) | 0.73 (n=11) | - (n=0) |
| air_quality_aqi | persistence | 5 | 10 | 0 | 20.365 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | persistence | 6 | 9 | 0 | 21.340 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | persistence | 7 | 8 | 0 | 25.815 (n=8) | 0.38 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 14 | 0 | 21.570 (n=14) | 0.57 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 13 | 0 | 23.159 (n=13) | 0.54 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 12 | 0 | 24.550 (n=12) | 0.50 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 11 | 0 | 23.551 (n=11) | 0.45 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 10 | 0 | 23.102 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 9 | 0 | 21.340 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 8 | 0 | 19.862 (n=8) | 0.62 (n=8) | - (n=0) |
| electricity_peak_mw | model | 1 | 13 | 0 | 2827.154 (n=13) | 0.85 (n=13) | 0.11 (n=13) |
| electricity_peak_mw | model | 2 | 12 | 0 | 2163.588 (n=12) | 0.75 (n=12) | 0.42 (n=12) |
| electricity_peak_mw | model | 3 | 12 | 0 | 2678.444 (n=12) | 0.92 (n=12) | 0.35 (n=12) |
| electricity_peak_mw | model | 4 | 11 | 0 | 2232.207 (n=11) | 0.91 (n=11) | 0.51 (n=11) |
| electricity_peak_mw | model | 5 | 10 | 0 | 1811.435 (n=10) | 1.00 (n=10) | 0.58 (n=10) |
| electricity_peak_mw | model | 6 | 9 | 0 | 2827.334 (n=9) | 1.00 (n=9) | 0.42 (n=9) |
| electricity_peak_mw | model | 7 | 8 | 0 | 3071.400 (n=8) | 1.00 (n=8) | 0.42 (n=8) |
| electricity_peak_mw | persistence | 1 | 13 | 0 | 3161.231 (n=13) | 0.85 (n=13) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 12 | 0 | 3733.333 (n=12) | 0.92 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 12 | 0 | 4152.333 (n=12) | 0.83 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 11 | 0 | 4578.727 (n=11) | 0.82 (n=11) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 10 | 0 | 4282.500 (n=10) | 0.90 (n=10) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 9 | 0 | 4912.000 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 8 | 0 | 5274.250 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 13 | 0 | 4301.385 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 12 | 0 | 4792.667 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 12 | 0 | 4388.417 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 11 | 0 | 4689.091 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 10 | 0 | 5047.300 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 9 | 0 | 4912.000 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 8 | 0 | 6899.000 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | model | 1 | 14 | 0 | 173.595 (n=14) | 0.86 (n=14) | -0.26 (n=14) |
| river_discharge_cfs | model | 2 | 13 | 0 | 174.187 (n=13) | 0.85 (n=13) | -0.22 (n=13) |
| river_discharge_cfs | model | 3 | 12 | 0 | 170.085 (n=12) | 1.00 (n=12) | -0.18 (n=12) |
| river_discharge_cfs | model | 4 | 11 | 0 | 230.903 (n=11) | 0.91 (n=11) | -0.51 (n=11) |
| river_discharge_cfs | model | 5 | 10 | 0 | 281.044 (n=10) | 1.00 (n=10) | -0.69 (n=10) |
| river_discharge_cfs | model | 6 | 9 | 0 | 264.093 (n=9) | 1.00 (n=9) | -0.46 (n=9) |
| river_discharge_cfs | model | 7 | 8 | 0 | 336.261 (n=8) | 0.88 (n=8) | -0.72 (n=8) |
| river_discharge_cfs | persistence | 1 | 14 | 0 | 174.482 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 13 | 0 | 174.451 (n=13) | 0.85 (n=13) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 12 | 0 | 143.997 (n=12) | 0.92 (n=12) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 11 | 0 | 156.922 (n=11) | 0.82 (n=11) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 10 | 0 | 188.506 (n=10) | 0.80 (n=10) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 9 | 0 | 181.375 (n=9) | 0.78 (n=9) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 8 | 0 | 195.733 (n=8) | 0.88 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 14 | 0 | 138.106 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 13 | 0 | 142.799 (n=13) | 0.85 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 12 | 0 | 144.198 (n=12) | 0.83 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 11 | 0 | 152.914 (n=11) | 0.82 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 10 | 0 | 166.146 (n=10) | 0.80 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 9 | 0 | 181.375 (n=9) | 0.78 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 8 | 0 | 219.091 (n=8) | 1.00 (n=8) | - (n=0) |
<!-- results:end -->
