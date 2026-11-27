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
| weather_tmax | model | 1 | 21 | 0 | 3.707 (n=21) | 0.62 (n=21) | 0.06 (n=21) |
| weather_tmax | model | 2 | 20 | 0 | 4.518 (n=20) | 0.50 (n=20) | -0.17 (n=20) |
| weather_tmax | model | 3 | 19 | 0 | 4.880 (n=19) | 0.32 (n=19) | -0.09 (n=19) |
| weather_tmax | model | 4 | 18 | 0 | 4.594 (n=18) | 0.50 (n=18) | -0.03 (n=18) |
| weather_tmax | model | 5 | 17 | 0 | 4.025 (n=17) | 0.41 (n=17) | 0.02 (n=17) |
| weather_tmax | model | 6 | 17 | 0 | 4.764 (n=17) | 0.29 (n=17) | -0.26 (n=17) |
| weather_tmax | model | 7 | 16 | 0 | 4.644 (n=16) | 0.44 (n=16) | -0.43 (n=16) |
| weather_tmax | persistence | 1 | 21 | 0 | 4.348 (n=21) | 0.29 (n=21) | - (n=0) |
| weather_tmax | persistence | 2 | 20 | 0 | 5.165 (n=20) | 0.25 (n=20) | - (n=0) |
| weather_tmax | persistence | 3 | 19 | 0 | 5.384 (n=19) | 0.37 (n=19) | - (n=0) |
| weather_tmax | persistence | 4 | 18 | 0 | 4.806 (n=18) | 0.50 (n=18) | - (n=0) |
| weather_tmax | persistence | 5 | 17 | 0 | 4.088 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | persistence | 6 | 17 | 0 | 3.794 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | persistence | 7 | 16 | 0 | 3.256 (n=16) | 0.75 (n=16) | - (n=0) |
| weather_tmax | seasonal_naive | 1 | 21 | 0 | 3.962 (n=21) | 0.76 (n=21) | - (n=0) |
| weather_tmax | seasonal_naive | 2 | 20 | 0 | 3.855 (n=20) | 0.75 (n=20) | - (n=0) |
| weather_tmax | seasonal_naive | 3 | 19 | 0 | 4.463 (n=19) | 0.68 (n=19) | - (n=0) |
| weather_tmax | seasonal_naive | 4 | 18 | 0 | 4.456 (n=18) | 0.67 (n=18) | - (n=0) |
| weather_tmax | seasonal_naive | 5 | 17 | 0 | 4.518 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 6 | 17 | 0 | 3.794 (n=17) | 0.71 (n=17) | - (n=0) |
| weather_tmax | seasonal_naive | 7 | 16 | 0 | 5.706 (n=16) | 0.56 (n=16) | - (n=0) |
| air_quality_aqi | model | 1 | 23 | 0 | 13.845 (n=23) | 0.74 (n=23) | 0.27 (n=23) |
| air_quality_aqi | model | 2 | 22 | 0 | 14.682 (n=22) | 0.59 (n=22) | 0.35 (n=22) |
| air_quality_aqi | model | 3 | 21 | 0 | 15.005 (n=21) | 0.62 (n=21) | 0.34 (n=21) |
| air_quality_aqi | model | 4 | 20 | 0 | 13.218 (n=20) | 0.60 (n=20) | 0.30 (n=20) |
| air_quality_aqi | model | 5 | 19 | 0 | 11.859 (n=19) | 0.68 (n=19) | 0.45 (n=19) |
| air_quality_aqi | model | 6 | 18 | 0 | 10.575 (n=18) | 0.72 (n=18) | 0.52 (n=18) |
| air_quality_aqi | model | 7 | 17 | 0 | 12.759 (n=17) | 0.65 (n=17) | 0.25 (n=17) |
| air_quality_aqi | persistence | 1 | 23 | 0 | 19.062 (n=23) | 0.52 (n=23) | - (n=0) |
| air_quality_aqi | persistence | 2 | 22 | 0 | 22.584 (n=22) | 0.50 (n=22) | - (n=0) |
| air_quality_aqi | persistence | 3 | 21 | 0 | 22.626 (n=21) | 0.52 (n=21) | - (n=0) |
| air_quality_aqi | persistence | 4 | 20 | 0 | 18.980 (n=20) | 0.65 (n=20) | - (n=0) |
| air_quality_aqi | persistence | 5 | 19 | 0 | 21.683 (n=19) | 0.53 (n=19) | - (n=0) |
| air_quality_aqi | persistence | 6 | 18 | 0 | 22.082 (n=18) | 0.56 (n=18) | - (n=0) |
| air_quality_aqi | persistence | 7 | 17 | 0 | 23.170 (n=17) | 0.53 (n=17) | - (n=0) |
| air_quality_aqi | seasonal_naive | 1 | 23 | 0 | 22.061 (n=23) | 0.57 (n=23) | - (n=0) |
| air_quality_aqi | seasonal_naive | 2 | 22 | 0 | 23.022 (n=22) | 0.55 (n=22) | - (n=0) |
| air_quality_aqi | seasonal_naive | 3 | 21 | 0 | 23.810 (n=21) | 0.52 (n=21) | - (n=0) |
| air_quality_aqi | seasonal_naive | 4 | 20 | 0 | 23.224 (n=20) | 0.50 (n=20) | - (n=0) |
| air_quality_aqi | seasonal_naive | 5 | 19 | 0 | 22.970 (n=19) | 0.53 (n=19) | - (n=0) |
| air_quality_aqi | seasonal_naive | 6 | 18 | 0 | 22.082 (n=18) | 0.56 (n=18) | - (n=0) |
| air_quality_aqi | seasonal_naive | 7 | 17 | 0 | 16.928 (n=17) | 0.65 (n=17) | - (n=0) |
| electricity_peak_mw | model | 1 | 22 | 0 | 2454.679 (n=22) | 0.82 (n=22) | 0.03 (n=22) |
| electricity_peak_mw | model | 2 | 21 | 0 | 2260.520 (n=21) | 0.76 (n=21) | 0.23 (n=21) |
| electricity_peak_mw | model | 3 | 20 | 0 | 2656.835 (n=20) | 0.85 (n=20) | 0.20 (n=20) |
| electricity_peak_mw | model | 4 | 19 | 0 | 2258.031 (n=19) | 0.89 (n=19) | 0.37 (n=19) |
| electricity_peak_mw | model | 5 | 18 | 0 | 2457.322 (n=18) | 0.83 (n=18) | 0.33 (n=18) |
| electricity_peak_mw | model | 6 | 17 | 0 | 3181.668 (n=17) | 0.88 (n=17) | 0.17 (n=17) |
| electricity_peak_mw | model | 7 | 16 | 0 | 4027.626 (n=16) | 0.75 (n=16) | -0.04 (n=16) |
| electricity_peak_mw | persistence | 1 | 22 | 0 | 2520.818 (n=22) | 0.82 (n=22) | - (n=0) |
| electricity_peak_mw | persistence | 2 | 21 | 0 | 2921.286 (n=21) | 0.86 (n=21) | - (n=0) |
| electricity_peak_mw | persistence | 3 | 20 | 0 | 3318.750 (n=20) | 0.85 (n=20) | - (n=0) |
| electricity_peak_mw | persistence | 4 | 19 | 0 | 3598.895 (n=19) | 0.79 (n=19) | - (n=0) |
| electricity_peak_mw | persistence | 5 | 18 | 0 | 3659.444 (n=18) | 0.83 (n=18) | - (n=0) |
| electricity_peak_mw | persistence | 6 | 17 | 0 | 3839.529 (n=17) | 0.94 (n=17) | - (n=0) |
| electricity_peak_mw | persistence | 7 | 16 | 0 | 3859.250 (n=16) | 1.00 (n=16) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 1 | 22 | 0 | 3507.864 (n=22) | 0.95 (n=22) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 2 | 21 | 0 | 3750.810 (n=21) | 0.95 (n=21) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 3 | 20 | 0 | 3680.400 (n=20) | 0.95 (n=20) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 4 | 19 | 0 | 3688.684 (n=19) | 0.95 (n=19) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 5 | 18 | 0 | 3849.722 (n=18) | 0.94 (n=18) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 6 | 17 | 0 | 3839.529 (n=17) | 0.94 (n=17) | - (n=0) |
| electricity_peak_mw | seasonal_naive | 7 | 16 | 0 | 5552.312 (n=16) | 1.00 (n=16) | - (n=0) |
| river_discharge_cfs | model | 1 | 21 | 0 | 196.093 (n=21) | 0.81 (n=21) | -0.21 (n=21) |
| river_discharge_cfs | model | 2 | 20 | 0 | 242.262 (n=20) | 0.65 (n=20) | -0.22 (n=20) |
| river_discharge_cfs | model | 3 | 19 | 0 | 279.214 (n=19) | 0.79 (n=19) | -0.40 (n=19) |
| river_discharge_cfs | model | 4 | 18 | 0 | 277.879 (n=18) | 0.78 (n=18) | -0.31 (n=18) |
| river_discharge_cfs | model | 5 | 17 | 0 | 276.471 (n=17) | 0.88 (n=17) | -0.29 (n=17) |
| river_discharge_cfs | model | 6 | 16 | 0 | 258.712 (n=16) | 0.94 (n=16) | -0.23 (n=16) |
| river_discharge_cfs | model | 7 | 15 | 0 | 281.988 (n=15) | 0.87 (n=15) | -0.55 (n=15) |
| river_discharge_cfs | persistence | 1 | 21 | 0 | 161.767 (n=21) | 0.81 (n=21) | - (n=0) |
| river_discharge_cfs | persistence | 2 | 20 | 0 | 198.129 (n=20) | 0.80 (n=20) | - (n=0) |
| river_discharge_cfs | persistence | 3 | 19 | 0 | 198.932 (n=19) | 0.84 (n=19) | - (n=0) |
| river_discharge_cfs | persistence | 4 | 18 | 0 | 211.520 (n=18) | 0.83 (n=18) | - (n=0) |
| river_discharge_cfs | persistence | 5 | 17 | 0 | 220.759 (n=17) | 0.82 (n=17) | - (n=0) |
| river_discharge_cfs | persistence | 6 | 16 | 0 | 210.660 (n=16) | 0.75 (n=16) | - (n=0) |
| river_discharge_cfs | persistence | 7 | 15 | 0 | 216.173 (n=15) | 0.87 (n=15) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 1 | 21 | 0 | 200.317 (n=21) | 0.81 (n=21) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 2 | 20 | 0 | 227.892 (n=20) | 0.70 (n=20) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 3 | 19 | 0 | 233.750 (n=19) | 0.68 (n=19) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 4 | 18 | 0 | 217.492 (n=18) | 0.72 (n=18) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 5 | 17 | 0 | 215.149 (n=17) | 0.71 (n=17) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 6 | 16 | 0 | 210.660 (n=16) | 0.75 (n=16) | - (n=0) |
| river_discharge_cfs | seasonal_naive | 7 | 15 | 0 | 182.433 (n=15) | 1.00 (n=15) | - (n=0) |
<!-- results:end -->
