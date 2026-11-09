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
| weather_tmax | model | 1 | 4 | 0 | 1.672 (n=4) | 1.00 (n=4) | -0.39 (n=4) |
| weather_tmax | model | 2 | 3 | 0 | 1.988 (n=3) | 1.00 (n=3) | -1.48 (n=3) |
| weather_tmax | model | 3 | 2 | 0 | 1.718 (n=2) | 1.00 (n=2) | -3.29 (n=2) |
| weather_tmax | model | 4 | 1 | 0 | 2.386 (n=1) | 1.00 (n=1) | -4.96 (n=1) |
| weather_tmax | model | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 1 | 4 | 0 | 2.650 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | persistence | 2 | 3 | 0 | 1.800 (n=3) | 0.67 (n=3) | - (n=0) |
| weather_tmax | persistence | 3 | 2 | 0 | 0.750 (n=2) | 1.00 (n=2) | - (n=0) |
| weather_tmax | persistence | 4 | 1 | 0 | 0.600 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 4 | 0 | 1.200 (n=4) | 1.00 (n=4) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 3 | 0 | 0.800 (n=3) | 1.00 (n=3) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 2 | 0 | 0.400 (n=2) | 1.00 (n=2) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 1 | 0 | 0.400 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 1 | 5 | 0 | 20.177 (n=5) | 0.40 (n=5) | 0.08 (n=5) |
| air_quality_aqi | model | 2 | 4 | 0 | 21.376 (n=4) | 0.50 (n=4) | 0.01 (n=4) |
| air_quality_aqi | model | 3 | 3 | 0 | 22.698 (n=3) | 0.33 (n=3) | 0.01 (n=3) |
| air_quality_aqi | model | 4 | 2 | 0 | 22.060 (n=2) | 0.00 (n=2) | -0.87 (n=2) |
| air_quality_aqi | model | 5 | 1 | 0 | 32.409 (n=1) | 0.00 (n=1) | -0.18 (n=1) |
| air_quality_aqi | model | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 1 | 5 | 0 | 23.321 (n=5) | 0.40 (n=5) | - (n=0) |
| air_quality_aqi | persistence | 2 | 4 | 0 | 21.661 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | persistence | 3 | 3 | 0 | 23.035 (n=3) | 0.33 (n=3) | - (n=0) |
| air_quality_aqi | persistence | 4 | 2 | 0 | 11.782 (n=2) | 0.50 (n=2) | - (n=0) |
| air_quality_aqi | persistence | 5 | 1 | 0 | 27.563 (n=1) | 0.00 (n=1) | - (n=0) |
| air_quality_aqi | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 5 | 0 | 21.983 (n=5) | 0.40 (n=5) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 4 | 0 | 27.250 (n=4) | 0.25 (n=4) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 3 | 0 | 34.181 (n=3) | 0.00 (n=3) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 2 | 0 | 33.500 (n=2) | 0.00 (n=2) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 1 | 0 | 38.958 (n=1) | 0.00 (n=1) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 1 | 5 | 0 | 2022.024 (n=5) | 1.00 (n=5) | 0.30 (n=5) |
| electricity_peak_mw | model | 2 | 4 | 0 | 1617.914 (n=4) | 1.00 (n=4) | 0.52 (n=4) |
| electricity_peak_mw | model | 3 | 3 | 0 | 1811.437 (n=3) | 1.00 (n=3) | 0.36 (n=3) |
| electricity_peak_mw | model | 4 | 2 | 0 | 1327.286 (n=2) | 1.00 (n=2) | 0.64 (n=2) |
| electricity_peak_mw | model | 5 | 1 | 0 | 737.714 (n=1) | 1.00 (n=1) | 0.88 (n=1) |
| electricity_peak_mw | model | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 1 | 5 | 0 | 3959.000 (n=5) | 0.60 (n=5) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 4 | 0 | 4340.500 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 3 | 0 | 5787.333 (n=3) | 0.67 (n=3) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 2 | 0 | 9086.500 (n=2) | 0.50 (n=2) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 1 | 0 | 9418.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 5 | 0 | 2906.000 (n=5) | 1.00 (n=5) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 4 | 0 | 3347.500 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 3 | 0 | 2817.667 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 2 | 0 | 3686.000 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 1 | 0 | 6265.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 1 | 5 | 0 | 112.008 (n=5) | 1.00 (n=5) | -0.86 (n=5) |
| river_discharge_cfs | model | 2 | 4 | 0 | 141.152 (n=4) | 1.00 (n=4) | -1.52 (n=4) |
| river_discharge_cfs | model | 3 | 3 | 0 | 186.531 (n=3) | 1.00 (n=3) | -4.71 (n=3) |
| river_discharge_cfs | model | 4 | 2 | 0 | 322.271 (n=2) | 0.50 (n=2) | -16.87 (n=2) |
| river_discharge_cfs | model | 5 | 1 | 0 | 373.233 (n=1) | 1.00 (n=1) | -11.83 (n=1) |
| river_discharge_cfs | model | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 1 | 5 | 0 | 93.524 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 4 | 0 | 103.688 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 3 | 0 | 40.897 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 2 | 0 | 18.033 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 1 | 0 | 35.246 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 5 | 0 | 60.223 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 4 | 0 | 56.002 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 3 | 0 | 32.666 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 2 | 0 | 24.842 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 1 | 0 | 29.084 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
<!-- results:end -->
