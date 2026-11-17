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
| weather_tmax | model | 1 | 12 | 0 | 3.000 (n=12) | 0.67 (n=12) | 0.27 (n=12) |
| weather_tmax | model | 2 | 11 | 0 | 3.634 (n=11) | 0.55 (n=11) | 0.11 (n=11) |
| weather_tmax | model | 3 | 10 | 0 | 3.669 (n=10) | 0.50 (n=10) | 0.13 (n=10) |
| weather_tmax | model | 4 | 9 | 0 | 3.584 (n=9) | 0.67 (n=9) | 0.08 (n=9) |
| weather_tmax | model | 5 | 8 | 0 | 3.702 (n=8) | 0.50 (n=8) | -0.09 (n=8) |
| weather_tmax | model | 6 | 7 | 0 | 4.641 (n=7) | 0.29 (n=7) | -0.07 (n=7) |
| weather_tmax | model | 7 | 6 | 0 | 4.454 (n=6) | 0.33 (n=6) | 0.06 (n=6) |
| weather_tmax | persistence | 1 | 12 | 0 | 4.125 (n=12) | 0.33 (n=12) | - (n=0) |
| weather_tmax | persistence | 2 | 11 | 0 | 4.100 (n=11) | 0.45 (n=11) | - (n=0) |
| weather_tmax | persistence | 3 | 10 | 0 | 4.200 (n=10) | 0.60 (n=10) | - (n=0) |
| weather_tmax | persistence | 4 | 9 | 0 | 3.900 (n=9) | 0.56 (n=9) | - (n=0) |
| weather_tmax | persistence | 5 | 8 | 0 | 3.400 (n=8) | 0.75 (n=8) | - (n=0) |
| weather_tmax | persistence | 6 | 7 | 0 | 4.329 (n=7) | 0.57 (n=7) | - (n=0) |
| weather_tmax | persistence | 7 | 6 | 0 | 4.717 (n=6) | 0.50 (n=6) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 12 | 0 | 4.267 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 11 | 0 | 4.436 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 10 | 0 | 4.720 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 9 | 0 | 5.200 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 8 | 0 | 5.800 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 7 | 0 | 4.329 (n=7) | 0.57 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 6 | 0 | 5.817 (n=6) | 0.67 (n=6) | - (n=0) |
| air_quality_aqi | model | 1 | 13 | 0 | 15.572 (n=13) | 0.69 (n=13) | 0.26 (n=13) |
| air_quality_aqi | model | 2 | 12 | 0 | 15.659 (n=12) | 0.58 (n=12) | 0.31 (n=12) |
| air_quality_aqi | model | 3 | 11 | 0 | 16.087 (n=11) | 0.64 (n=11) | 0.20 (n=11) |
| air_quality_aqi | model | 4 | 10 | 0 | 14.548 (n=10) | 0.50 (n=10) | -0.10 (n=10) |
| air_quality_aqi | model | 5 | 9 | 0 | 14.000 (n=9) | 0.67 (n=9) | 0.24 (n=9) |
| air_quality_aqi | model | 6 | 8 | 0 | 11.872 (n=8) | 0.75 (n=8) | 0.42 (n=8) |
| air_quality_aqi | model | 7 | 7 | 0 | 15.453 (n=7) | 0.43 (n=7) | -0.04 (n=7) |
| air_quality_aqi | persistence | 1 | 13 | 0 | 21.117 (n=13) | 0.46 (n=13) | - (n=0) |
| air_quality_aqi | persistence | 2 | 12 | 0 | 22.689 (n=12) | 0.50 (n=12) | - (n=0) |
| air_quality_aqi | persistence | 3 | 11 | 0 | 19.998 (n=11) | 0.64 (n=11) | - (n=0) |
| air_quality_aqi | persistence | 4 | 10 | 0 | 13.181 (n=10) | 0.80 (n=10) | - (n=0) |
| air_quality_aqi | persistence | 5 | 9 | 0 | 18.387 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | persistence | 6 | 8 | 0 | 20.424 (n=8) | 0.62 (n=8) | - (n=0) |
| air_quality_aqi | persistence | 7 | 7 | 0 | 26.045 (n=7) | 0.43 (n=7) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 13 | 0 | 21.024 (n=13) | 0.62 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 12 | 0 | 22.700 (n=12) | 0.58 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 11 | 0 | 24.176 (n=11) | 0.55 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 10 | 0 | 23.040 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 9 | 0 | 22.484 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 8 | 0 | 20.424 (n=8) | 0.62 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 7 | 0 | 14.890 (n=7) | 0.71 (n=7) | - (n=0) |
| electricity_peak_mw | model | 1 | 12 | 0 | 2755.557 (n=12) | 0.83 (n=12) | 0.15 (n=12) |
| electricity_peak_mw | model | 2 | 12 | 0 | 2163.588 (n=12) | 0.75 (n=12) | 0.42 (n=12) |
| electricity_peak_mw | model | 3 | 11 | 0 | 2405.608 (n=11) | 1.00 (n=11) | 0.44 (n=11) |
| electricity_peak_mw | model | 4 | 10 | 0 | 2023.017 (n=10) | 1.00 (n=10) | 0.58 (n=10) |
| electricity_peak_mw | model | 5 | 9 | 0 | 1671.829 (n=9) | 1.00 (n=9) | 0.65 (n=9) |
| electricity_peak_mw | model | 6 | 8 | 0 | 2528.967 (n=8) | 1.00 (n=8) | 0.54 (n=8) |
| electricity_peak_mw | model | 7 | 7 | 0 | 2270.829 (n=7) | 1.00 (n=7) | 0.61 (n=7) |
| electricity_peak_mw | persistence | 1 | 12 | 0 | 3249.833 (n=12) | 0.83 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 12 | 0 | 3733.333 (n=12) | 0.92 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 11 | 0 | 4273.909 (n=11) | 0.82 (n=11) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 10 | 0 | 4766.100 (n=10) | 0.80 (n=10) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 9 | 0 | 4713.111 (n=9) | 0.89 (n=9) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 8 | 0 | 5515.250 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 7 | 0 | 5775.143 (n=7) | 1.00 (n=7) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 12 | 0 | 4652.667 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 12 | 0 | 4792.667 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 11 | 0 | 4779.545 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 10 | 0 | 5149.400 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 9 | 0 | 5598.556 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 8 | 0 | 5515.250 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 7 | 0 | 6107.000 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | model | 1 | 13 | 0 | 128.685 (n=13) | 0.92 (n=13) | -0.39 (n=13) |
| river_discharge_cfs | model | 2 | 12 | 0 | 135.651 (n=12) | 0.92 (n=12) | -0.45 (n=12) |
| river_discharge_cfs | model | 3 | 11 | 0 | 129.585 (n=11) | 1.00 (n=11) | -0.43 (n=11) |
| river_discharge_cfs | model | 4 | 10 | 0 | 202.443 (n=10) | 0.90 (n=10) | -1.13 (n=10) |
| river_discharge_cfs | model | 5 | 9 | 0 | 248.052 (n=9) | 1.00 (n=9) | -1.41 (n=9) |
| river_discharge_cfs | model | 6 | 8 | 0 | 225.644 (n=8) | 1.00 (n=8) | -1.01 (n=8) |
| river_discharge_cfs | model | 7 | 7 | 0 | 319.319 (n=7) | 0.86 (n=7) | -1.79 (n=7) |
| river_discharge_cfs | persistence | 1 | 13 | 0 | 131.407 (n=13) | 0.85 (n=13) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 12 | 0 | 130.088 (n=12) | 0.92 (n=12) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 11 | 0 | 100.557 (n=11) | 1.00 (n=11) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 10 | 0 | 122.453 (n=10) | 0.90 (n=10) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 9 | 0 | 131.287 (n=9) | 0.89 (n=9) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 8 | 0 | 112.327 (n=8) | 0.88 (n=8) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 7 | 0 | 114.615 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 13 | 0 | 92.287 (n=13) | 0.92 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 12 | 0 | 93.552 (n=12) | 0.92 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 11 | 0 | 90.601 (n=11) | 0.91 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 10 | 0 | 94.830 (n=10) | 0.90 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 9 | 0 | 103.078 (n=9) | 0.89 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 8 | 0 | 112.327 (n=8) | 0.88 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 7 | 0 | 144.074 (n=7) | 1.00 (n=7) | - (n=0) |
<!-- results:end -->
