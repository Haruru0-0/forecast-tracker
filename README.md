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
| weather_tmax | model | 1 | 7 | 0 | 3.180 (n=7) | 0.71 (n=7) | 0.18 (n=7) |
| weather_tmax | model | 2 | 6 | 0 | 3.964 (n=6) | 0.50 (n=6) | -0.12 (n=6) |
| weather_tmax | model | 3 | 5 | 0 | 3.750 (n=5) | 0.60 (n=5) | -0.10 (n=5) |
| weather_tmax | model | 4 | 4 | 0 | 4.657 (n=4) | 0.50 (n=4) | 0.03 (n=4) |
| weather_tmax | model | 5 | 3 | 0 | 5.867 (n=3) | 0.00 (n=3) | 0.16 (n=3) |
| weather_tmax | model | 6 | 2 | 0 | 6.271 (n=2) | 0.00 (n=2) | 0.26 (n=2) |
| weather_tmax | model | 7 | 1 | 0 | 3.247 (n=1) | 0.00 (n=1) | -1.50 (n=1) |
| weather_tmax | persistence | 1 | 7 | 0 | 3.900 (n=7) | 0.29 (n=7) | - (n=0) |
| weather_tmax | persistence | 2 | 6 | 0 | 3.533 (n=6) | 0.50 (n=6) | - (n=0) |
| weather_tmax | persistence | 3 | 5 | 0 | 3.420 (n=5) | 0.80 (n=5) | - (n=0) |
| weather_tmax | persistence | 4 | 4 | 0 | 4.825 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | persistence | 5 | 3 | 0 | 7.000 (n=3) | 0.33 (n=3) | - (n=0) |
| weather_tmax | persistence | 6 | 2 | 0 | 8.500 (n=2) | 0.00 (n=2) | - (n=0) |
| weather_tmax | persistence | 7 | 1 | 0 | 4.900 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 7 | 0 | 4.371 (n=7) | 0.71 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 6 | 0 | 4.700 (n=6) | 0.67 (n=6) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 5 | 0 | 5.320 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 4 | 0 | 6.550 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 3 | 0 | 8.600 (n=3) | 0.33 (n=3) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 2 | 0 | 8.500 (n=2) | 0.00 (n=2) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 1 | 0 | 1.300 (n=1) | 1.00 (n=1) | - (n=0) |
| air_quality_aqi | model | 1 | 8 | 0 | 15.880 (n=8) | 0.62 (n=8) | 0.20 (n=8) |
| air_quality_aqi | model | 2 | 7 | 0 | 15.151 (n=7) | 0.57 (n=7) | 0.33 (n=7) |
| air_quality_aqi | model | 3 | 6 | 0 | 15.897 (n=6) | 0.67 (n=6) | 0.19 (n=6) |
| air_quality_aqi | model | 4 | 5 | 0 | 11.809 (n=5) | 0.60 (n=5) | -0.02 (n=5) |
| air_quality_aqi | model | 5 | 4 | 0 | 15.390 (n=4) | 0.75 (n=4) | 0.28 (n=4) |
| air_quality_aqi | model | 6 | 3 | 0 | 8.952 (n=3) | 0.67 (n=3) | 0.45 (n=3) |
| air_quality_aqi | model | 7 | 2 | 0 | 14.374 (n=2) | 0.50 (n=2) | -0.53 (n=2) |
| air_quality_aqi | persistence | 1 | 8 | 0 | 23.351 (n=8) | 0.38 (n=8) | - (n=0) |
| air_quality_aqi | persistence | 2 | 7 | 0 | 23.431 (n=7) | 0.29 (n=7) | - (n=0) |
| air_quality_aqi | persistence | 3 | 6 | 0 | 19.719 (n=6) | 0.50 (n=6) | - (n=0) |
| air_quality_aqi | persistence | 4 | 5 | 0 | 11.538 (n=5) | 0.80 (n=5) | - (n=0) |
| air_quality_aqi | persistence | 5 | 4 | 0 | 21.245 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | persistence | 6 | 3 | 0 | 16.368 (n=3) | 0.67 (n=3) | - (n=0) |
| air_quality_aqi | persistence | 7 | 2 | 0 | 9.364 (n=2) | 1.00 (n=2) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 8 | 0 | 19.878 (n=8) | 0.50 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 7 | 0 | 22.586 (n=7) | 0.43 (n=7) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 6 | 0 | 25.274 (n=6) | 0.33 (n=6) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 5 | 0 | 23.221 (n=5) | 0.40 (n=5) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 4 | 0 | 22.015 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 3 | 0 | 16.368 (n=3) | 0.67 (n=3) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 2 | 0 | 11.375 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | model | 1 | 8 | 0 | 2909.304 (n=8) | 0.88 (n=8) | 0.15 (n=8) |
| electricity_peak_mw | model | 2 | 7 | 0 | 2601.872 (n=7) | 0.71 (n=7) | 0.40 (n=7) |
| electricity_peak_mw | model | 3 | 6 | 0 | 2799.916 (n=6) | 1.00 (n=6) | 0.52 (n=6) |
| electricity_peak_mw | model | 4 | 5 | 0 | 1748.591 (n=5) | 1.00 (n=5) | 0.76 (n=5) |
| electricity_peak_mw | model | 5 | 4 | 0 | 1634.084 (n=4) | 1.00 (n=4) | 0.81 (n=4) |
| electricity_peak_mw | model | 6 | 3 | 0 | 3104.048 (n=3) | 1.00 (n=3) | 0.69 (n=3) |
| electricity_peak_mw | model | 7 | 2 | 0 | 1779.949 (n=2) | 1.00 (n=2) | 0.74 (n=2) |
| electricity_peak_mw | persistence | 1 | 8 | 0 | 3429.000 (n=8) | 0.75 (n=8) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 7 | 0 | 4337.143 (n=7) | 0.86 (n=7) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 6 | 0 | 5775.667 (n=6) | 0.67 (n=6) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 5 | 0 | 7653.400 (n=5) | 0.60 (n=5) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 4 | 0 | 8663.500 (n=4) | 0.75 (n=4) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 3 | 0 | 9902.000 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 2 | 0 | 10724.000 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 8 | 0 | 5529.500 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 7 | 0 | 6156.571 (n=7) | 1.00 (n=7) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 6 | 0 | 6359.833 (n=6) | 1.00 (n=6) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 5 | 0 | 7415.600 (n=5) | 1.00 (n=5) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 4 | 0 | 8992.750 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 3 | 0 | 9902.000 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 2 | 0 | 6846.500 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | model | 1 | 8 | 0 | 83.006 (n=8) | 1.00 (n=8) | -0.72 (n=8) |
| river_discharge_cfs | model | 2 | 7 | 0 | 108.665 (n=7) | 1.00 (n=7) | -1.46 (n=7) |
| river_discharge_cfs | model | 3 | 6 | 0 | 143.603 (n=6) | 1.00 (n=6) | -3.71 (n=6) |
| river_discharge_cfs | model | 4 | 5 | 0 | 243.133 (n=5) | 0.80 (n=5) | -8.04 (n=5) |
| river_discharge_cfs | model | 5 | 4 | 0 | 296.509 (n=4) | 1.00 (n=4) | -9.41 (n=4) |
| river_discharge_cfs | model | 6 | 3 | 0 | 291.932 (n=3) | 1.00 (n=3) | -9.33 (n=3) |
| river_discharge_cfs | model | 7 | 2 | 0 | 318.514 (n=2) | 1.00 (n=2) | -13.72 (n=2) |
| river_discharge_cfs | persistence | 1 | 8 | 0 | 72.366 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 7 | 0 | 76.889 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 6 | 0 | 58.175 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 5 | 0 | 56.919 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 4 | 0 | 58.048 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 3 | 0 | 28.269 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 2 | 0 | 21.638 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 8 | 0 | 48.240 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 7 | 0 | 44.117 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 6 | 0 | 30.468 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 5 | 0 | 26.898 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 4 | 0 | 28.473 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 3 | 0 | 28.269 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 2 | 0 | 30.608 (n=2) | 1.00 (n=2) | - (n=0) |
<!-- results:end -->
