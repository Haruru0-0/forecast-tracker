# Metro choice: Houston, TX

| Item | Value |
|---|---|
| Metro | Houston, TX (29.76 N, 95.37 W), timezone `America/Chicago` |
| EIA balancing authority | `ERCO` (ERCOT), hourly demand, MWh per hour |
| USGS gauge | `08074000` Buffalo Bayou at Houston, TX, parameter `00060` (discharge), ft3/s |
| Weather | Open-Meteo, daily maximum 2 m temperature, degC |
| Air quality | Open-Meteo, daily mean US AQI (from hourly values) |

## Why Houston

- The area is served by one balancing authority. ERCOT covers almost all of Texas, so which BA serves the metro is unambiguous (unlike metros split across PJM/MISO subregions). The series is statewide demand, though, so Houston weather is only a partial driver of it.
- USGS gauge 08074000 sits in central Houston, is a long-running continuous discharge station, and reports parameter 00060 in ft3/s.
- A single timezone, and it has both DST transitions, which exercises the local-day logic.

## Checks done by hand (2026-11-02)

- USGS instantaneous values API (public, no key) for site 08074000, parameter 00060: returned 15-minute readings in ft3/s through 2026-11-02 01:15 local, so data reaches yesterday. The daily-values service had no rows for the last three days, so the engine should aggregate the instantaneous values itself (Task 4).
- Open-Meteo: both series return values through yesterday (`ftracker.cli check-sources`).
- EIA `ERCO` is a documented EIA-930 balancing authority code. EIA data needs an API key, so freshness could not be checked here; Task 4 must confirm it with the project key in CI.
