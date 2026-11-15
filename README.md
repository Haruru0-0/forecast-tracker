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
| weather_tmax | model | 1 | 10 | 0 | 2.458 (n=10) | 0.80 (n=10) | 0.32 (n=10) |
| weather_tmax | model | 2 | 9 | 0 | 3.101 (n=9) | 0.67 (n=9) | 0.16 (n=9) |
| weather_tmax | model | 3 | 8 | 0 | 3.221 (n=8) | 0.62 (n=8) | 0.17 (n=8) |
| weather_tmax | model | 4 | 7 | 0 | 3.275 (n=7) | 0.71 (n=7) | 0.16 (n=7) |
| weather_tmax | model | 5 | 6 | 0 | 3.717 (n=6) | 0.50 (n=6) | 0.11 (n=6) |
| weather_tmax | model | 6 | 5 | 0 | 3.931 (n=5) | 0.40 (n=5) | 0.06 (n=5) |
| weather_tmax | model | 7 | 4 | 0 | 2.779 (n=4) | 0.50 (n=4) | 0.11 (n=4) |
| weather_tmax | persistence | 1 | 10 | 0 | 3.640 (n=10) | 0.40 (n=10) | - (n=0) |
| weather_tmax | persistence | 2 | 9 | 0 | 3.711 (n=9) | 0.56 (n=9) | - (n=0) |
| weather_tmax | persistence | 3 | 8 | 0 | 3.900 (n=8) | 0.62 (n=8) | - (n=0) |
| weather_tmax | persistence | 4 | 7 | 0 | 3.900 (n=7) | 0.57 (n=7) | - (n=0) |
| weather_tmax | persistence | 5 | 6 | 0 | 4.183 (n=6) | 0.67 (n=6) | - (n=0) |
| weather_tmax | persistence | 6 | 5 | 0 | 4.180 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | persistence | 7 | 4 | 0 | 3.225 (n=4) | 0.75 (n=4) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 10 | 0 | 3.820 (n=10) | 0.80 (n=10) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 9 | 0 | 3.978 (n=9) | 0.78 (n=9) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 8 | 0 | 4.275 (n=8) | 0.75 (n=8) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 7 | 0 | 4.829 (n=7) | 0.71 (n=7) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 6 | 0 | 5.567 (n=6) | 0.67 (n=6) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 5 | 0 | 4.180 (n=5) | 0.60 (n=5) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 4 | 0 | 3.125 (n=4) | 1.00 (n=4) | - (n=0) |
| air_quality_aqi | model | 1 | 11 | 0 | 15.068 (n=11) | 0.73 (n=11) | 0.22 (n=11) |
| air_quality_aqi | model | 2 | 10 | 0 | 15.788 (n=10) | 0.60 (n=10) | 0.23 (n=10) |
| air_quality_aqi | model | 3 | 9 | 0 | 16.094 (n=9) | 0.67 (n=9) | 0.11 (n=9) |
| air_quality_aqi | model | 4 | 8 | 0 | 14.565 (n=8) | 0.50 (n=8) | -0.35 (n=8) |
| air_quality_aqi | model | 5 | 7 | 0 | 14.381 (n=7) | 0.71 (n=7) | 0.25 (n=7) |
| air_quality_aqi | model | 6 | 6 | 0 | 11.739 (n=6) | 0.83 (n=6) | 0.31 (n=6) |
| air_quality_aqi | model | 7 | 5 | 0 | 15.498 (n=5) | 0.40 (n=5) | -0.09 (n=5) |
| air_quality_aqi | persistence | 1 | 11 | 0 | 19.691 (n=11) | 0.55 (n=11) | - (n=0) |
| air_quality_aqi | persistence | 2 | 10 | 0 | 20.564 (n=10) | 0.50 (n=10) | - (n=0) |
| air_quality_aqi | persistence | 3 | 9 | 0 | 18.090 (n=9) | 0.67 (n=9) | - (n=0) |
| air_quality_aqi | persistence | 4 | 8 | 0 | 10.784 (n=8) | 0.88 (n=8) | - (n=0) |
| air_quality_aqi | persistence | 5 | 7 | 0 | 19.128 (n=7) | 0.57 (n=7) | - (n=0) |
| air_quality_aqi | persistence | 6 | 6 | 0 | 17.003 (n=6) | 0.67 (n=6) | - (n=0) |
| air_quality_aqi | persistence | 7 | 5 | 0 | 18.896 (n=5) | 0.60 (n=5) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 11 | 0 | 19.267 (n=11) | 0.64 (n=11) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 10 | 0 | 21.102 (n=10) | 0.60 (n=10) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 9 | 0 | 22.729 (n=9) | 0.56 (n=9) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 8 | 0 | 21.128 (n=8) | 0.50 (n=8) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 7 | 0 | 20.140 (n=7) | 0.57 (n=7) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 6 | 0 | 17.003 (n=6) | 0.67 (n=6) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 5 | 0 | 14.258 (n=5) | 0.80 (n=5) | - (n=0) |
| electricity_peak_mw | model | 1 | 11 | 0 | 2554.495 (n=11) | 0.91 (n=11) | 0.18 (n=11) |
| electricity_peak_mw | model | 2 | 10 | 0 | 2222.843 (n=10) | 0.80 (n=10) | 0.42 (n=10) |
| electricity_peak_mw | model | 3 | 9 | 0 | 2497.303 (n=9) | 1.00 (n=9) | 0.48 (n=9) |
| electricity_peak_mw | model | 4 | 8 | 0 | 1892.096 (n=8) | 1.00 (n=8) | 0.66 (n=8) |
| electricity_peak_mw | model | 5 | 7 | 0 | 1331.351 (n=7) | 1.00 (n=7) | 0.77 (n=7) |
| electricity_peak_mw | model | 6 | 6 | 0 | 1997.714 (n=6) | 1.00 (n=6) | 0.69 (n=6) |
| electricity_peak_mw | model | 7 | 5 | 0 | 1333.435 (n=5) | 1.00 (n=5) | 0.74 (n=5) |
| electricity_peak_mw | persistence | 1 | 11 | 0 | 3098.636 (n=11) | 0.82 (n=11) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 10 | 0 | 3823.400 (n=10) | 0.90 (n=10) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 9 | 0 | 4761.667 (n=9) | 0.78 (n=9) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 8 | 0 | 5604.000 (n=8) | 0.75 (n=8) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 7 | 0 | 5874.571 (n=7) | 0.86 (n=7) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 6 | 0 | 6520.667 (n=6) | 1.00 (n=6) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 5 | 0 | 6733.600 (n=5) | 1.00 (n=5) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 11 | 0 | 4877.636 (n=11) | 1.00 (n=11) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 10 | 0 | 5251.400 (n=10) | 1.00 (n=10) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 9 | 0 | 5286.333 (n=9) | 1.00 (n=9) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 8 | 0 | 5812.000 (n=8) | 1.00 (n=8) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 7 | 0 | 6484.143 (n=7) | 1.00 (n=7) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 6 | 0 | 6520.667 (n=6) | 1.00 (n=6) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 5 | 0 | 5172.000 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | model | 1 | 11 | 0 | 94.342 (n=11) | 1.00 (n=11) | -0.69 (n=11) |
| river_discharge_cfs | model | 2 | 10 | 0 | 99.248 (n=10) | 1.00 (n=10) | -0.85 (n=10) |
| river_discharge_cfs | model | 3 | 9 | 0 | 116.865 (n=9) | 1.00 (n=9) | -1.56 (n=9) |
| river_discharge_cfs | model | 4 | 8 | 0 | 181.673 (n=8) | 0.88 (n=8) | -3.02 (n=8) |
| river_discharge_cfs | model | 5 | 7 | 0 | 238.955 (n=7) | 1.00 (n=7) | -3.90 (n=7) |
| river_discharge_cfs | model | 6 | 6 | 0 | 207.494 (n=6) | 1.00 (n=6) | -2.99 (n=6) |
| river_discharge_cfs | model | 7 | 5 | 0 | 313.236 (n=5) | 0.80 (n=5) | -5.68 (n=5) |
| river_discharge_cfs | persistence | 1 | 11 | 0 | 99.810 (n=11) | 0.91 (n=11) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 10 | 0 | 91.542 (n=10) | 1.00 (n=10) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 9 | 0 | 86.953 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 8 | 0 | 91.174 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 7 | 0 | 89.680 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 6 | 0 | 52.016 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 5 | 0 | 46.863 (n=5) | 1.00 (n=5) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 11 | 0 | 55.746 (n=11) | 1.00 (n=11) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 10 | 0 | 53.610 (n=10) | 1.00 (n=10) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 9 | 0 | 45.566 (n=9) | 1.00 (n=9) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 8 | 0 | 45.222 (n=8) | 1.00 (n=8) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 7 | 0 | 48.740 (n=7) | 1.00 (n=7) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 6 | 0 | 52.016 (n=6) | 1.00 (n=6) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 5 | 0 | 96.686 (n=5) | 1.00 (n=5) | - (n=0) |
<!-- results:end -->
