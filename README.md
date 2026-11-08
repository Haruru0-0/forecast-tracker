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
| weather_tmax | model | 1 | 3 | 0 | 1.948 (n=3) | 1.00 (n=3) | -0.33 (n=3) |
| weather_tmax | model | 2 | 2 | 0 | 1.614 (n=2) | 1.00 (n=2) | -0.61 (n=2) |
| weather_tmax | model | 3 | 1 | 0 | 2.587 (n=1) | 1.00 (n=1) | -11.94 (n=1) |
| weather_tmax | model | 4 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | model | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 1 | 3 | 0 | 2.967 (n=3) | 0.33 (n=3) | - (n=0) |
| weather_tmax | persistence | 2 | 2 | 0 | 1.100 (n=2) | 1.00 (n=2) | - (n=0) |
| weather_tmax | persistence | 3 | 1 | 0 | 0.200 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | persistence | 4 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 3 | 0 | 1.467 (n=3) | 1.00 (n=3) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 2 | 0 | 1.000 (n=2) | 1.00 (n=2) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 1 | 0 | 0.400 (n=1) | 1.00 (n=1) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 1 | 4 | 0 | 22.315 (n=4) | 0.25 (n=4) | -0.26 (n=4) |
| air_quality_aqi | model | 2 | 3 | 0 | 17.172 (n=3) | 0.67 (n=3) | -0.11 (n=3) |
| air_quality_aqi | model | 3 | 2 | 0 | 20.184 (n=2) | 0.50 (n=2) | -0.25 (n=2) |
| air_quality_aqi | model | 4 | 1 | 0 | 22.999 (n=1) | 0.00 (n=1) | -0.16 (n=1) |
| air_quality_aqi | model | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | model | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 1 | 4 | 0 | 28.943 (n=4) | 0.25 (n=4) | - (n=0) |
| air_quality_aqi | persistence | 2 | 3 | 0 | 15.437 (n=3) | 0.67 (n=3) | - (n=0) |
| air_quality_aqi | persistence | 3 | 2 | 0 | 16.198 (n=2) | 0.50 (n=2) | - (n=0) |
| air_quality_aqi | persistence | 4 | 1 | 0 | 19.772 (n=1) | 0.00 (n=1) | - (n=0) |
| air_quality_aqi | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 4 | 0 | 17.740 (n=4) | 0.50 (n=4) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 3 | 0 | 23.347 (n=3) | 0.33 (n=3) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 2 | 0 | 31.792 (n=2) | 0.00 (n=2) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 1 | 0 | 28.042 (n=1) | 0.00 (n=1) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 1 | 4 | 0 | 2262.911 (n=4) | 1.00 (n=4) | -0.10 (n=4) |
| electricity_peak_mw | model | 2 | 3 | 0 | 1326.956 (n=3) | 1.00 (n=3) | 0.44 (n=3) |
| electricity_peak_mw | model | 3 | 2 | 0 | 2088.043 (n=2) | 1.00 (n=2) | -0.91 (n=2) |
| electricity_peak_mw | model | 4 | 1 | 0 | 1188.272 (n=1) | 1.00 (n=1) | -0.07 (n=1) |
| electricity_peak_mw | model | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | model | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 1 | 4 | 0 | 3143.500 (n=4) | 0.75 (n=4) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 3 | 0 | 4138.000 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 2 | 0 | 5476.000 (n=2) | 0.50 (n=2) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 1 | 0 | 5810.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 4 | 0 | 2066.250 (n=4) | 1.00 (n=4) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 3 | 0 | 2375.000 (n=3) | 1.00 (n=3) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 2 | 0 | 1094.000 (n=2) | 1.00 (n=2) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 1 | 0 | 1107.000 (n=1) | 1.00 (n=1) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 1 | 4 | 0 | 95.655 (n=4) | 1.00 (n=4) | -0.41 (n=4) |
| river_discharge_cfs | model | 2 | 3 | 0 | 101.855 (n=3) | 1.00 (n=3) | -0.57 (n=3) |
| river_discharge_cfs | model | 3 | 2 | 0 | 151.523 (n=2) | 1.00 (n=2) | -16.12 (n=2) |
| river_discharge_cfs | model | 4 | 1 | 0 | 280.165 (n=1) | 1.00 (n=1) | -19.28 (n=1) |
| river_discharge_cfs | model | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | model | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 1 | 4 | 0 | 103.873 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 3 | 0 | 82.157 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 2 | 0 | 8.849 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 1 | 0 | 13.814 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | persistence | 7 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 4 | 0 | 68.008 (n=4) | 1.00 (n=4) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 3 | 0 | 64.975 (n=3) | 1.00 (n=3) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 2 | 0 | 34.457 (n=2) | 1.00 (n=2) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 1 | 0 | 20.600 (n=1) | 1.00 (n=1) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 0 | 0 | - | - | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 0 | 0 | - | - | - (n=0) |
<!-- results:end -->
