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
| weather_tmax | model | 1 | 11 | 0 | 2.613 (n=11) | 0.73 (n=11) | 0.31 (n=11) |
| weather_tmax | model | 2 | 10 | 0 | 3.385 (n=10) | 0.60 (n=10) | 0.10 (n=10) |
| weather_tmax | model | 3 | 9 | 0 | 3.384 (n=9) | 0.56 (n=9) | 0.14 (n=9) |
| weather_tmax | model | 4 | 8 | 0 | 3.122 (n=8) | 0.75 (n=8) | 0.13 (n=8) |
| weather_tmax | model | 5 | 7 | 0 | 3.447 (n=7) | 0.57 (n=7) | 0.08 (n=7) |
| weather_tmax | model | 6 | 6 | 0 | 4.297 (n=6) | 0.33 (n=6) | 0.04 (n=6) |
| weather_tmax | model | 7 | 5 | 0 | 3.637 (n=5) | 0.40 (n=5) | 0.10 (n=5) |
| weather_tmax | persistence | 1 | 11 | 0 | 3.782 (n=11) | 0.36 (n=11) | - (n=0) |
| weather_tmax | persistence | 2 | 10 | 0 | 3.770 (n=10) | 0.50 (n=10) | - (n=0) |
| weather_tmax | persistence | 3 | 9 | 0 | 3.944 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | persistence | 4 | 8 | 0 | 3.575 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | persistence | 5 | 7 | 0 | 3.757 (n=7) | 0.71 (n=7) | - (n=0) |
| weather_tmax | persistence | 6 | 6 | 0 | 4.483 (n=6) | 0.50 (n=6) | - (n=0) |
| weather_tmax | persistence | 7 | 5 | 0 | 4.020 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 11 | 0 | 4.291 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 10 | 0 | 4.480 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 9 | 0 | 4.800 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 8 | 0 | 5.350 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 7 | 0 | 6.057 (n=7) | 0.57 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 6 | 0 | 4.483 (n=6) | 0.50 (n=6) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 5 | 0 | 4.380 (n=5) | 0.80 (n=5) | - (n=0) |
| air_quality_aqi | model | 1 | 12 | 0 | 14.513 (n=12) | 0.75 (n=12) | 0.28 (n=12) |
| air_quality_aqi | model | 2 | 11 | 0 | 14.443 (n=11) | 0.64 (n=11) | 0.29 (n=11) |
| air_quality_aqi | model | 3 | 10 | 0 | 15.017 (n=10) | 0.70 (n=10) | 0.16 (n=10) |
| air_quality_aqi | model | 4 | 9 | 0 | 13.242 (n=9) | 0.56 (n=9) | -0.27 (n=9) |
| air_quality_aqi | model | 5 | 8 | 0 | 13.214 (n=8) | 0.75 (n=8) | 0.23 (n=8) |
| air_quality_aqi | model | 6 | 7 | 0 | 10.107 (n=7) | 0.86 (n=7) | 0.49 (n=7) |
| air_quality_aqi | model | 7 | 6 | 0 | 13.269 (n=6) | 0.50 (n=6) | -0.09 (n=6) |
| air_quality_aqi | persistence | 1 | 12 | 0 | 20.234 (n=12) | 0.50 (n=12) | - (n=0) |
| air_quality_aqi | persistence | 2 | 11 | 0 | 20.411 (n=11) | 0.55 (n=11) | - (n=0) |
| air_quality_aqi | persistence | 3 | 10 | 0 | 17.956 (n=10) | 0.70 (n=10) | - (n=0) |
| air_quality_aqi | persistence | 4 | 9 | 0 | 10.391 (n=9) | 0.89 (n=9) | - (n=0) |
| air_quality_aqi | persistence | 5 | 8 | 0 | 17.086 (n=8) | 0.62 (n=8) | - (n=0) |
| air_quality_aqi | persistence | 6 | 7 | 0 | 19.866 (n=7) | 0.57 (n=7) | - (n=0) |
| air_quality_aqi | persistence | 7 | 6 | 0 | 20.621 (n=6) | 0.50 (n=6) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 12 | 0 | 20.748 (n=12) | 0.58 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 11 | 0 | 22.551 (n=11) | 0.55 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 10 | 0 | 24.160 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 9 | 0 | 22.896 (n=9) | 0.44 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 8 | 0 | 22.253 (n=8) | 0.50 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 7 | 0 | 19.866 (n=7) | 0.57 (n=7) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 6 | 0 | 12.201 (n=6) | 0.83 (n=6) | - (n=0) |
| electricity_peak_mw | model | 1 | 12 | 0 | 2755.557 (n=12) | 0.83 (n=12) | 0.15 (n=12) |
| electricity_peak_mw | model | 2 | 11 | 0 | 2315.783 (n=11) | 0.73 (n=11) | 0.41 (n=11) |
| electricity_peak_mw | model | 3 | 10 | 0 | 2510.538 (n=10) | 1.00 (n=10) | 0.45 (n=10) |
| electricity_peak_mw | model | 4 | 9 | 0 | 2098.314 (n=9) | 1.00 (n=9) | 0.60 (n=9) |
| electricity_peak_mw | model | 5 | 8 | 0 | 1792.020 (n=8) | 1.00 (n=8) | 0.65 (n=8) |
| electricity_peak_mw | model | 6 | 7 | 0 | 2420.546 (n=7) | 1.00 (n=7) | 0.59 (n=7) |
| electricity_peak_mw | model | 7 | 6 | 0 | 1847.575 (n=6) | 1.00 (n=6) | 0.68 (n=6) |
| electricity_peak_mw | persistence | 1 | 12 | 0 | 3249.833 (n=12) | 0.83 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 11 | 0 | 3912.455 (n=11) | 0.91 (n=11) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 10 | 0 | 4536.000 (n=10) | 0.80 (n=10) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 9 | 0 | 5224.000 (n=9) | 0.78 (n=9) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 8 | 0 | 5181.500 (n=8) | 0.88 (n=8) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 7 | 0 | 5900.286 (n=7) | 1.00 (n=7) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 6 | 0 | 6575.667 (n=6) | 1.00 (n=6) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 12 | 0 | 4652.667 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 11 | 0 | 4972.000 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 10 | 0 | 4975.500 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 9 | 0 | 5408.222 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 8 | 0 | 5945.875 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 7 | 0 | 5900.286 (n=7) | 1.00 (n=7) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 6 | 0 | 5717.167 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | model | 1 | 12 | 0 | 103.316 (n=12) | 1.00 (n=12) | -0.92 (n=12) |
| river_discharge_cfs | model | 2 | 11 | 0 | 114.057 (n=11) | 0.91 (n=11) | -1.21 (n=11) |
| river_discharge_cfs | model | 3 | 10 | 0 | 112.044 (n=10) | 1.00 (n=10) | -1.53 (n=10) |
| river_discharge_cfs | model | 4 | 9 | 0 | 178.643 (n=9) | 0.89 (n=9) | -3.08 (n=9) |
| river_discharge_cfs | model | 5 | 8 | 0 | 229.681 (n=8) | 1.00 (n=8) | -3.92 (n=8) |
| river_discharge_cfs | model | 6 | 7 | 0 | 205.454 (n=7) | 1.00 (n=7) | -3.18 (n=7) |
| river_discharge_cfs | model | 7 | 6 | 0 | 312.899 (n=6) | 0.83 (n=6) | -6.67 (n=6) |
| river_discharge_cfs | persistence | 1 | 12 | 0 | 100.878 (n=12) | 0.92 (n=12) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 11 | 0 | 104.388 (n=11) | 1.00 (n=11) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 10 | 0 | 81.356 (n=10) | 1.00 (n=10) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 9 | 0 | 81.121 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 8 | 0 | 82.108 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 7 | 0 | 49.156 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 6 | 0 | 40.814 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 12 | 0 | 53.767 (n=12) | 1.00 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 11 | 0 | 51.646 (n=11) | 1.00 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 10 | 0 | 44.209 (n=10) | 1.00 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 9 | 0 | 43.753 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 8 | 0 | 46.647 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 7 | 0 | 49.156 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 6 | 0 | 81.058 (n=6) | 1.00 (n=6) | - (n=0) |
<!-- results:end -->
