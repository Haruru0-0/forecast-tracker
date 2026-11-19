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
| weather_tmax | model | 1 | 14 | 0 | 2.768 (n=14) | 0.71 (n=14) | 0.29 (n=14) |
| weather_tmax | model | 2 | 13 | 0 | 3.670 (n=13) | 0.54 (n=13) | 0.11 (n=13) |
| weather_tmax | model | 3 | 12 | 0 | 4.061 (n=12) | 0.42 (n=12) | 0.06 (n=12) |
| weather_tmax | model | 4 | 11 | 0 | 3.854 (n=11) | 0.55 (n=11) | 0.04 (n=11) |
| weather_tmax | model | 5 | 10 | 0 | 3.927 (n=10) | 0.40 (n=10) | -0.11 (n=10) |
| weather_tmax | model | 6 | 9 | 0 | 4.763 (n=9) | 0.22 (n=9) | -0.26 (n=9) |
| weather_tmax | model | 7 | 8 | 0 | 4.709 (n=8) | 0.25 (n=8) | -0.15 (n=8) |
| weather_tmax | persistence | 1 | 14 | 0 | 3.893 (n=14) | 0.36 (n=14) | - (n=0) |
| weather_tmax | persistence | 2 | 13 | 0 | 4.200 (n=13) | 0.38 (n=13) | - (n=0) |
| weather_tmax | persistence | 3 | 12 | 0 | 4.367 (n=12) | 0.58 (n=12) | - (n=0) |
| weather_tmax | persistence | 4 | 11 | 0 | 4.009 (n=11) | 0.64 (n=11) | - (n=0) |
| weather_tmax | persistence | 5 | 10 | 0 | 3.530 (n=10) | 0.80 (n=10) | - (n=0) |
| weather_tmax | persistence | 6 | 9 | 0 | 3.778 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | persistence | 7 | 8 | 0 | 4.088 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 14 | 0 | 3.986 (n=14) | 0.79 (n=14) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 13 | 0 | 4.108 (n=13) | 0.77 (n=13) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 12 | 0 | 4.317 (n=12) | 0.75 (n=12) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 11 | 0 | 4.673 (n=11) | 0.73 (n=11) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 10 | 0 | 5.100 (n=10) | 0.70 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 9 | 0 | 3.778 (n=9) | 0.67 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 8 | 0 | 6.762 (n=8) | 0.50 (n=8) | - (n=0) |
| air_quality_aqi | model | 1 | 15 | 0 | 15.536 (n=15) | 0.67 (n=15) | 0.22 (n=15) |
| air_quality_aqi | model | 2 | 14 | 0 | 16.531 (n=14) | 0.50 (n=14) | 0.28 (n=14) |
| air_quality_aqi | model | 3 | 13 | 0 | 17.555 (n=13) | 0.54 (n=13) | 0.23 (n=13) |
| air_quality_aqi | model | 4 | 12 | 0 | 16.201 (n=12) | 0.42 (n=12) | 0.11 (n=12) |
| air_quality_aqi | model | 5 | 11 | 0 | 15.337 (n=11) | 0.55 (n=11) | 0.30 (n=11) |
| air_quality_aqi | model | 6 | 10 | 0 | 13.441 (n=10) | 0.60 (n=10) | 0.41 (n=10) |
| air_quality_aqi | model | 7 | 9 | 0 | 16.199 (n=9) | 0.44 (n=9) | 0.18 (n=9) |
| air_quality_aqi | persistence | 1 | 15 | 0 | 19.865 (n=15) | 0.47 (n=15) | - (n=0) |
| air_quality_aqi | persistence | 2 | 14 | 0 | 23.097 (n=14) | 0.50 (n=14) | - (n=0) |
| air_quality_aqi | persistence | 3 | 13 | 0 | 22.867 (n=13) | 0.54 (n=13) | - (n=0) |
| air_quality_aqi | persistence | 4 | 12 | 0 | 18.151 (n=12) | 0.67 (n=12) | - (n=0) |
| air_quality_aqi | persistence | 5 | 11 | 0 | 22.002 (n=11) | 0.45 (n=11) | - (n=0) |
| air_quality_aqi | persistence | 6 | 10 | 0 | 22.831 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | persistence | 7 | 9 | 0 | 25.919 (n=9) | 0.33 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 15 | 0 | 22.549 (n=15) | 0.53 (n=15) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 14 | 0 | 24.094 (n=14) | 0.50 (n=14) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 13 | 0 | 25.450 (n=13) | 0.46 (n=13) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 12 | 0 | 24.609 (n=12) | 0.42 (n=12) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 11 | 0 | 24.297 (n=11) | 0.45 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 10 | 0 | 22.831 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 9 | 0 | 19.859 (n=9) | 0.56 (n=9) | - (n=0) |
| electricity_peak_mw | model | 1 | 14 | 0 | 3020.591 (n=14) | 0.79 (n=14) | -0.01 (n=14) |
| electricity_peak_mw | model | 2 | 13 | 0 | 2335.334 (n=13) | 0.69 (n=13) | 0.35 (n=13) |
| electricity_peak_mw | model | 3 | 12 | 0 | 2678.444 (n=12) | 0.92 (n=12) | 0.35 (n=12) |
| electricity_peak_mw | model | 4 | 12 | 0 | 2460.512 (n=12) | 0.83 (n=12) | 0.43 (n=12) |
| electricity_peak_mw | model | 5 | 11 | 0 | 2077.681 (n=11) | 0.91 (n=11) | 0.50 (n=11) |
| electricity_peak_mw | model | 6 | 10 | 0 | 3104.352 (n=10) | 1.00 (n=10) | 0.30 (n=10) |
| electricity_peak_mw | model | 7 | 9 | 0 | 3389.316 (n=9) | 1.00 (n=9) | 0.28 (n=9) |
| electricity_peak_mw | persistence | 1 | 14 | 0 | 3003.500 (n=14) | 0.86 (n=14) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 13 | 0 | 3615.154 (n=13) | 0.92 (n=13) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 12 | 0 | 4152.333 (n=12) | 0.83 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 12 | 0 | 4423.500 (n=12) | 0.83 (n=12) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 11 | 0 | 4130.091 (n=11) | 0.91 (n=11) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 10 | 0 | 4451.600 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 9 | 0 | 4689.667 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 14 | 0 | 4016.143 (n=14) | 1.00 (n=14) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 13 | 0 | 4447.692 (n=13) | 1.00 (n=13) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 12 | 0 | 4388.417 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 12 | 0 | 4324.000 (n=12) | 1.00 (n=12) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 11 | 0 | 4616.455 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 10 | 0 | 4451.600 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 9 | 0 | 6842.556 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | model | 1 | 14 | 0 | 173.595 (n=14) | 0.86 (n=14) | -0.26 (n=14) |
| river_discharge_cfs | model | 2 | 14 | 0 | 198.801 (n=14) | 0.79 (n=14) | -0.19 (n=14) |
| river_discharge_cfs | model | 3 | 13 | 0 | 193.162 (n=13) | 1.00 (n=13) | -0.13 (n=13) |
| river_discharge_cfs | model | 4 | 12 | 0 | 243.842 (n=12) | 0.92 (n=12) | -0.37 (n=12) |
| river_discharge_cfs | model | 5 | 11 | 0 | 275.513 (n=11) | 1.00 (n=11) | -0.41 (n=11) |
| river_discharge_cfs | model | 6 | 10 | 0 | 271.407 (n=10) | 1.00 (n=10) | -0.28 (n=10) |
| river_discharge_cfs | model | 7 | 9 | 0 | 337.650 (n=9) | 0.89 (n=9) | -0.46 (n=9) |
| river_discharge_cfs | persistence | 1 | 14 | 0 | 174.482 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 14 | 0 | 198.949 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 13 | 0 | 170.595 (n=13) | 0.85 (n=13) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 12 | 0 | 177.579 (n=12) | 0.83 (n=12) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 11 | 0 | 197.241 (n=11) | 0.82 (n=11) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 10 | 0 | 211.882 (n=10) | 0.70 (n=10) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 9 | 0 | 231.399 (n=9) | 0.89 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 14 | 0 | 138.106 (n=14) | 0.86 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 14 | 0 | 167.345 (n=14) | 0.79 (n=14) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 13 | 0 | 170.525 (n=13) | 0.77 (n=13) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 12 | 0 | 180.709 (n=12) | 0.75 (n=12) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 11 | 0 | 195.264 (n=11) | 0.73 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 10 | 0 | 211.882 (n=10) | 0.70 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 9 | 0 | 244.129 (n=9) | 1.00 (n=9) | - (n=0) |
<!-- results:end -->
