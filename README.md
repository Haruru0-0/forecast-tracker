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
| weather_tmax | model | 1 | 5 | 0 | 2.455 (n=5) | 0.80 (n=5) | 0.11 (n=5) |
| weather_tmax | model | 2 | 4 | 0 | 2.963 (n=4) | 0.75 (n=4) | -0.09 (n=4) |
| weather_tmax | model | 3 | 3 | 0 | 2.508 (n=3) | 0.67 (n=3) | -0.37 (n=3) |
| weather_tmax | model | 4 | 2 | 0 | 3.374 (n=2) | 0.50 (n=2) | 0.26 (n=2) |
| weather_tmax | model | 5 | 1 | 0 | 4.686 (n=1) | 0.00 (n=1) | 0.40 (n=1) |
| weather_tmax | model | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 1 | 5 | 0 | 3.200 (n=5) | 0.40 (n=5) | - (n=0) |
| weather_tmax | persistence | 2 | 4 | 0 | 2.725 (n=4) | 0.50 (n=4) | - (n=0) |
| weather_tmax | persistence | 3 | 3 | 0 | 1.833 (n=3) | 1.00 (n=3) | - (n=0) |
| weather_tmax | persistence | 4 | 2 | 0 | 4.550 (n=2) | 0.50 (n=2) | - (n=0) |
| weather_tmax | persistence | 5 | 1 | 0 | 7.800 (n=1) | 0.00 (n=1) | - (n=0) |
| weather_tmax | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 5 | 0 | 2.760 (n=5) | 0.80 (n=5) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 4 | 0 | 2.850 (n=4) | 0.75 (n=4) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 3 | 0 | 3.267 (n=3) | 0.67 (n=3) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 2 | 0 | 4.700 (n=2) | 0.50 (n=2) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 1 | 0 | 9.000 (n=1) | 0.00 (n=1) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 1 | 6 | 0 | 17.183 (n=6) | 0.50 (n=6) | 0.12 (n=6) |
| air_quality_aqi | model | 2 | 5 | 0 | 20.688 (n=5) | 0.40 (n=5) | 0.11 (n=5) |
| air_quality_aqi | model | 3 | 4 | 0 | 19.062 (n=4) | 0.50 (n=4) | -0.01 (n=4) |
| air_quality_aqi | model | 4 | 3 | 0 | 16.319 (n=3) | 0.33 (n=3) | -0.88 (n=3) |
| air_quality_aqi | model | 5 | 2 | 0 | 20.649 (n=2) | 0.50 (n=2) | 0.10 (n=2) |
| air_quality_aqi | model | 6 | 1 | 0 | 0.733 (n=1) | 1.00 (n=1) | 0.89 (n=1) |
| air_quality_aqi | model | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 1 | 6 | 0 | 23.844 (n=6) | 0.33 (n=6) | - (n=0) |
| air_quality_aqi | persistence | 2 | 5 | 0 | 24.346 (n=5) | 0.40 (n=5) | - (n=0) |
| air_quality_aqi | persistence | 3 | 4 | 0 | 18.797 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | persistence | 4 | 3 | 0 | 8.674 (n=3) | 0.67 (n=3) | - (n=0) |
| air_quality_aqi | persistence | 5 | 2 | 0 | 29.011 (n=2) | 0.00 (n=2) | - (n=0) |
| air_quality_aqi | persistence | 6 | 1 | 0 | 6.687 (n=1) | 1.00 (n=1) | - (n=0) |
| air_quality_aqi | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 6 | 0 | 19.434 (n=6) | 0.50 (n=6) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 5 | 0 | 23.137 (n=5) | 0.40 (n=5) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 4 | 0 | 27.307 (n=4) | 0.25 (n=4) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 3 | 0 | 24.562 (n=3) | 0.33 (n=3) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 2 | 0 | 22.822 (n=2) | 0.50 (n=2) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 1 | 0 | 6.687 (n=1) | 1.00 (n=1) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 1 | 6 | 0 | 2323.014 (n=6) | 1.00 (n=6) | 0.45 (n=6) |
| electricity_peak_mw | model | 2 | 5 | 0 | 1692.014 (n=5) | 1.00 (n=5) | 0.66 (n=5) |
| electricity_peak_mw | model | 3 | 4 | 0 | 1667.055 (n=4) | 1.00 (n=4) | 0.66 (n=4) |
| electricity_peak_mw | model | 4 | 3 | 0 | 890.847 (n=3) | 1.00 (n=3) | 0.86 (n=3) |
| electricity_peak_mw | model | 5 | 2 | 0 | 599.305 (n=2) | 1.00 (n=2) | 0.93 (n=2) |
| electricity_peak_mw | model | 6 | 1 | 0 | 1939.014 (n=1) | 1.00 (n=1) | 0.83 (n=1) |
| electricity_peak_mw | model | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 1 | 6 | 0 | 4208.500 (n=6) | 0.67 (n=6) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 5 | 0 | 5286.200 (n=5) | 0.80 (n=5) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 4 | 0 | 6039.500 (n=4) | 0.75 (n=4) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 3 | 0 | 8810.333 (n=3) | 0.33 (n=3) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 2 | 0 | 11814.500 (n=2) | 0.50 (n=2) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 1 | 0 | 11266.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 6 | 0 | 4299.333 (n=6) | 1.00 (n=6) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 5 | 0 | 4931.200 (n=5) | 1.00 (n=5) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 4 | 0 | 4929.750 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 3 | 0 | 6212.667 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 2 | 0 | 8765.500 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 1 | 0 | 11266.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 1 | 6 | 0 | 98.411 (n=6) | 1.00 (n=6) | -0.77 (n=6) |
| river_discharge_cfs | model | 2 | 5 | 0 | 131.804 (n=5) | 1.00 (n=5) | -1.57 (n=5) |
| river_discharge_cfs | model | 3 | 4 | 0 | 194.651 (n=4) | 1.00 (n=4) | -4.97 (n=4) |
| river_discharge_cfs | model | 4 | 3 | 0 | 285.715 (n=3) | 0.67 (n=3) | -9.45 (n=3) |
| river_discharge_cfs | model | 5 | 2 | 0 | 319.018 (n=2) | 1.00 (n=2) | -10.69 (n=2) |
| river_discharge_cfs | model | 6 | 1 | 0 | 301.474 (n=1) | 1.00 (n=1) | -8.32 (n=1) |
| river_discharge_cfs | model | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 1 | 6 | 0 | 81.025 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 5 | 0 | 92.796 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 4 | 0 | 72.018 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 3 | 0 | 46.053 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 2 | 0 | 27.299 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 1 | 0 | 32.347 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 6 | 0 | 55.577 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 5 | 0 | 51.271 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 4 | 0 | 32.587 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 3 | 0 | 27.344 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 2 | 0 | 30.716 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 1 | 0 | 32.347 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
<!-- results:end -->
