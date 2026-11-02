"""Project configuration: the single tracked metro area. See docs/metro.md for the reasoning."""

METRO = {
    "name": "Houston, TX",
    "lat": 29.76,
    "lon": -95.37,
    "tz": "America/Chicago",
    "eia_respondent": "ERCO",   # EIA-930 balancing authority: ERCOT
    "usgs_site": "08074000",    # Buffalo Bayou at Houston, TX
    "usgs_parameter": "00060",  # discharge, ft3/s
}
