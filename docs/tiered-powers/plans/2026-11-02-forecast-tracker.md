# Forecast Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use tiered-powers:subagent-driven-development (recommended) or tiered-powers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public, self-updating page that publishes 1 to 7 day forecasts for four US series (weather, air quality, electricity demand, river level) before the outcome is known, then scores them against what happened and against naive baselines.

**Architecture:** A small Python package (`ftracker`) with one plug-in `Series` per topic and one engine. A daily GitHub Actions job issues forecasts, scores forecasts whose outcome has settled, commits append-only data files, builds a static `index.html` and deploys it to GitHub Pages. A git-based check fails CI if any past forecast or outcome file is modified or removed.

**Tech Stack:** Python 3.12, pandas, numpy, requests, lightgbm, pytest, `responses` (HTTP mocking), pyyaml, GitHub Actions, GitHub Pages. Data: Open-Meteo (weather, air quality), EIA open data (electricity), USGS Water Services (river).

**Spec:** `docs/tiered-powers/specs/2026-11-02-forecast-tracker-design.md`

## Global Constraints

- Python 3.12; package under `src/ftracker`; tests in `tests/`; test-first.
- Free data only, no paid APIs. EIA needs a free key, read from the environment variable `EIA_API_KEY` (a GitHub secret), never committed.
- Free hosting only: GitHub Actions for the daily job, static GitHub Pages for the page. The repository is public; the daily job pushes straight to `main`; force-push and branch deletion are blocked on `main`.
- Four series, US data: weather, air quality, electricity demand, river level. One metro area, chosen so all four sources have reliable data nearby.
- Forecasts: horizons 1 to 7 days at daily resolution; forecast target days are issue date +1 to +7, using only data up to the end of the previous complete day.
- Every forecast has an 80% prediction interval. Baselines always run alongside the model: seasonal naive ("same day last week") and persistence ("same as yesterday").
- One forecast file per series per issue date; a repeated or retried run never overwrites it. A late or back-filled run is issued under its own, later date.
- Past forecast and outcome files are never edited or removed. Engine bugs are fixed for future issue dates only.
- A target is scored after a two-day settling lag using the value the source publishes then; the value and fetch time are stored in an append-only outcome file, separate from the forecast. Later revisions are ignored.
- Scores are shown per horizon (1 to 7), never averaged across horizons. Trend lines appear only once a series and horizon has 14 scored forecasts; below that the page shows counts only. Every number on the page has its sample count next to it.
- Skill is shown as undefined ("n/a") when the baseline error is near zero.
- The page shows the time of the last run and a visible warning when it is older than 36 hours. Missing data is recorded as a gap, never filled in or hidden.
- Each series runs independently. The job commits whatever succeeded, flags failed or gapped series, then exits with an error if any series failed so GitHub emails Ahmad.
- The backtest section is part of version 1 but built last, clearly labelled, and stored separately from the live record.
- Size: the whole repository stays well under a few hundred MB for a year of running.
- Commits are authored as Ahmad: no `Co-Authored-By` and no "Generated with Claude" lines. Never push without Ahmad's explicit yes.
- Any number in the README comes from generated results, never typed by hand.

## Review Focus

Failure modes the spec implies but a first read would skip, most likely first. Each has a test in the task named in brackets.

1. A local day with a missing hour (or a 23- or 25-hour DST day) must become a gap or a correct value, never a silently shortened average. [Task 3]
2. Source sentinels and bad values (USGS `-999999`, ice-affected or negative readings, empty EIA pages) become missing, not data. [Task 4]
3. The job runs twice on the same day, or is retried after a partial failure: nothing existing is overwritten and the second run exits cleanly. [Task 7]
4. Yesterday's value is missing, or today's data is partly observed: a forecast is still issued from the last observed day, and the model never sees data from the issue date. [Task 7]
5. Every source is down: gaps are written, the exit code is non-zero, status is updated, and the site still builds and shows the stale warning. [Tasks 7 and 8]

---

## File Structure

```
CLAUDE.md                          project conventions (Task 1)
pyproject.toml                     package, deps, pytest config (Task 1)
src/ftracker/
  store.py        append-only forecast/outcome/gap files (Task 1)
  immutability.py git-based check on protected data dirs (Task 2)
  daily.py        hourly -> local-day aggregation (Task 3)
  config.py       metro area and source ids (Task 3)
  sources/openmeteo.py  weather, air quality (Task 3)
  sources/eia.py, sources/usgs.py  (Task 4)
  series.py       Series dataclass, SourceError (Task 3); registry.py (Task 4)
  models.py       Forecaster protocol, baselines, GBM (Task 5)
  scoring.py      mae, coverage, skill, scoreboard (Task 6)
  engine.py       issue, score, run_daily, status.json (Task 7)
  site.py         static page builder (Task 8)
  cli.py          daily, site, check-sources, readme (Tasks 3, 9)
  backtest.py     rolling-origin backtest (Task 10)
data/forecasts|outcomes|gaps/<series>/<YYYY-MM-DD>.json   protected, append-only
data/backtest/<series>.csv, data/status.json              mutable, not protected
.github/workflows/ci.yml, daily.yml
tests/  (one test file per module, fixtures in tests/fixtures/)
```

---

### Task 1: Repository, store

**Files:**
- Create: `CLAUDE.md`, `pyproject.toml`, `.gitignore`, `src/ftracker/__init__.py`, `src/ftracker/store.py`, `tests/test_store.py`

**Tier:** sonnet — several files and a design choice (file format), but small.

**Interfaces:**
- Produces (all in `ftracker.store`, `root` is the `data/` directory):
  - `class AlreadyWritten(Exception)`
  - `write_forecast(root: Path, series: str, issue_date: date, rows: pd.DataFrame, meta: dict) -> Path` — `rows` columns: `method, target_date, horizon, point, lo, hi`; `meta` holds at least `run_id, issued_at, last_observed`. Writes `forecasts/<series>/<issue_date>.json`; raises `AlreadyWritten` if it exists.
  - `read_forecasts(root: Path, series: str) -> pd.DataFrame` — columns `issue_date, method, target_date, horizon, point, lo, hi`, dates as `datetime.date`.
  - `write_outcome(root, series, target_date: date, value: float | None, fetched_at: datetime) -> Path` — `outcomes/<series>/<target_date>.json`; `None` is stored as JSON null; raises `AlreadyWritten`.
  - `read_outcomes(root, series) -> pd.DataFrame` — columns `target_date, value, fetched_at` (value NaN for null).
  - `write_gap(root, series, issue_date: date, reason: str) -> Path` — `gaps/<series>/<issue_date>.json`; raises `AlreadyWritten`.
  - `read_gaps(root, series) -> pd.DataFrame` — columns `issue_date, reason`.
  - `issued_dates(root, series) -> set[date]` — issue dates that already have a forecast or gap file.

- [ ] **Step 1:** `git init -b main` in the repo folder; set the repo-local git author to Ahmad's name and email (copy `user.name` and `user.email` from `C:\Users\ahmad\Documents\Github\malware-classifier`). Write `CLAUDE.md` with the Global Constraints that concern conventions (test-first, commits as Ahmad with no attribution lines, never push without a yes, README numbers from generated results). Write `pyproject.toml` (package `ftracker` in `src/`, pytest `testpaths = ["tests"]`, `pythonpath = ["src"]`) and a `.gitignore` for the Python virtual environment, caches and `site/`.
- [ ] **Step 2:** Create the virtual environment, install the dependencies from Tech Stack, and run `pytest` to confirm it reports "no tests ran" without errors.
- [ ] **Step 3: Write the failing tests** in `tests/test_store.py`:
  - `test_write_forecast_path`: the returned path ends with `forecasts/weather/2026-11-03.json`.
  - `test_write_forecast_refuses_overwrite`: a second call raises `AlreadyWritten` and the file bytes are unchanged.
  - `test_forecast_roundtrip`: `read_forecasts` returns the columns `["issue_date","method","target_date","horizon","point","lo","hi"]` and the same values written.
  - `test_outcome_null_roundtrip`: `write_outcome(..., None, ...)` reads back as NaN; a second write for the same date raises `AlreadyWritten`.
  - `test_gap_roundtrip_and_issued_dates`: after one forecast on 2026-11-03 and one gap on 2026-11-04, `issued_dates` is `{date(2026,11,3), date(2026,11,4)}`.
  - `test_read_empty_series_returns_empty_frame_with_columns`.
- [ ] **Step 4:** Run `pytest tests/test_store.py -v`. Expected: FAIL (module missing).
- [ ] **Step 5:** Implement the functions above in `src/ftracker/store.py`. Use JSON files; open with exclusive-create mode so overwriting is impossible even under a race.
- [ ] **Step 6:** Run `pytest -v`. Expected: all PASS.
- [ ] **Step 7: Commit** everything including the spec and this plan: `git add -A && git commit -m "chore: scaffold project, append-only store"`.

---

### Task 2: Immutability check and CI

**Files:**
- Create: `src/ftracker/immutability.py`, `tests/test_immutability.py`, `.github/workflows/ci.yml`, `tests/test_workflows.py`

**Tier:** sonnet — git plumbing and a workflow, several files.

**Interfaces:**
- Consumes: the protected directories `data/forecasts`, `data/outcomes`, `data/gaps`.
- Produces: `PROTECTED: tuple[str, ...]`; `check_immutable(repo: Path, base: str, head: str = "HEAD") -> list[str]` returning one message per violating path; `main(argv) -> int` (exit 1 if violations), runnable as `python -m ftracker.immutability --base <sha>`.

- [ ] **Step 1: Write the failing tests** using a temporary git repository fixture:
  - `test_new_file_is_allowed` returns `[]`.
  - `test_modified_forecast_is_violation` returns one entry naming the file.
  - `test_deleted_outcome_is_violation`.
  - `test_renamed_forecast_is_violation` (rename counts as delete plus add; run git diff with rename detection off).
  - `test_changes_outside_protected_dirs_are_allowed` (editing `data/status.json`).
  - `test_all_zero_base_sha_checks_nothing` (GitHub passes `0000000000000000000000000000000000000000` on a branch's first push) returns `[]`.
- [ ] **Step 2:** Run them; expected FAIL.
- [ ] **Step 3:** Implement with `git diff --name-status --no-renames base head -- <PROTECTED>`; any status other than `A` is a violation.
- [ ] **Step 4:** Write `.github/workflows/ci.yml`: triggers `push` and `pull_request` (so the bot's own pushes are checked too); steps checkout with `fetch-depth: 0`, set up Python 3.12, install, `pytest`, then the immutability check with base `${{ github.event.before }}` for pushes and the PR base SHA for pull requests.
- [ ] **Step 5:** In `tests/test_workflows.py` add `test_ci_runs_on_push_and_pull_request_and_checks_immutability`: parse the YAML and assert both triggers exist and the text `ftracker.immutability` appears in a step.
- [ ] **Step 6:** Run `pytest -v`; expected all PASS. Commit: `feat: immutability check and CI workflow`.

---

### Task 3: Local-day aggregation, metro config, Open-Meteo sources

**Files:**
- Create: `src/ftracker/series.py`, `src/ftracker/daily.py`, `src/ftracker/config.py`, `src/ftracker/sources/__init__.py`, `src/ftracker/sources/openmeteo.py`, `src/ftracker/cli.py`, `docs/metro.md`, `tests/test_daily.py`, `tests/test_openmeteo.py`, `tests/fixtures/openmeteo_weather.json`, `tests/fixtures/openmeteo_air.json`

**Tier:** sonnet — design choices and live-API verification.

**Interfaces:**
- Produces:
  - `class SourceError(Exception)` and `@dataclass(frozen=True) class Series` with fields `name: str`, `unit: str`, `tz: str`, `fetch_daily: Callable[[date, date], pd.Series]` in `ftracker.series`. `fetch_daily(start, end)` returns floats indexed by `datetime.date`, both ends inclusive, NaN where missing.
  - `aggregate_local_days(hourly: pd.Series, tz: str, how: Literal["mean","max"]) -> pd.Series` in `ftracker.daily`. `hourly` has a UTC `DatetimeIndex`. A local day is complete only if it has the expected number of hours (23, 24 or 25 for that tz and date); incomplete days are NaN.
  - `fetch_weather(lat, lon, tz, start, end) -> pd.Series` (daily maximum temperature, °C) and `fetch_air_quality(lat, lon, tz, start, end) -> pd.Series` (daily mean US AQI, from hourly values via `aggregate_local_days`).
  - `config.METRO: dict` with keys `name, lat, lon, tz, eia_respondent, usgs_site, usgs_parameter`.

- [ ] **Step 1: Choose the metro area.** Pick one US metro where a USGS gauge and an EIA balancing authority both serve the area. Check by hand that each source has data up to yesterday. Record the choice, the ids, the unit of each series and the reason in `docs/metro.md`; fill `config.METRO`.
- [ ] **Step 2: Write the failing tests** in `tests/test_daily.py`:
  - `test_complete_day_is_aggregated`: 24 hourly values for 2026-06-01 in `America/Chicago` give the expected mean.
  - `test_missing_hour_makes_day_nan` (23 of 24 hours on a normal day).
  - `test_spring_forward_day_has_23_hours_and_is_valid` (2026-03-08, `America/Chicago`, 23 values).
  - `test_fall_back_day_has_25_hours_and_is_valid` (2026-11-01, 25 values).
  - `test_max_and_mean_modes`.
- [ ] **Step 3:** In `tests/test_openmeteo.py`, with `responses` serving recorded fixtures (save a trimmed real response for each endpoint):
  - `test_weather_returns_daily_series_indexed_by_date`.
  - `test_air_quality_uses_local_day_completeness`.
  - `test_http_failure_retries_then_raises_source_error` (three attempts, then `SourceError`).
- [ ] **Step 4:** Run; expected FAIL. Implement. Use `requests` with a timeout and three retries with backoff; the retry helper lives in `sources/__init__.py` for reuse in Task 4.
- [ ] **Step 5:** Add the `check-sources` command to `cli.py`: prints, for each registered series, its most recent non-missing date (the registry arrives in Task 4; until then the command lists the two Open-Meteo series). Run it once against the real APIs and confirm both print yesterday or the day before.
- [ ] **Step 6:** Run `pytest -v`; expected all PASS. Commit: `feat: local-day aggregation, metro config, Open-Meteo sources`.

---

### Task 4: EIA and USGS sources, registry

**Files:**
- Create: `src/ftracker/sources/eia.py`, `src/ftracker/sources/usgs.py`, `src/ftracker/registry.py`, `tests/test_eia.py`, `tests/test_usgs.py`, `tests/test_registry.py`, `tests/fixtures/eia_page1.json`, `tests/fixtures/eia_page2.json`, `tests/fixtures/usgs.json`

**Tier:** sonnet — API details and sentinel handling.

**Interfaces:**
- Consumes: `Series`, `SourceError`, `aggregate_local_days`, retry helper, `config.METRO`.
- Produces:
  - `fetch_eia_demand(api_key: str, respondent: str, tz: str, start: date, end: date) -> pd.Series` — daily **peak** hourly demand (MW) per local day.
  - `fetch_usgs(site: str, parameter: str, tz: str, start: date, end: date) -> pd.Series` — daily mean of the chosen parameter per local day.
  - `registry.SERIES: dict[str, Series]` with keys `weather`, `air_quality`, `electricity`, `river`. The electricity `fetch_daily` reads `EIA_API_KEY` at call time and raises `SourceError("EIA_API_KEY not set")` if missing, with no network call.

- [ ] **Step 1: Write the failing tests:**
  - `test_eia_missing_key_raises_without_network` (no `responses` mock registered, so any request fails the test).
  - `test_eia_collects_all_pages` (page 1 has the API's row limit and a continuation, page 2 the rest).
  - `test_eia_peak_is_max_per_local_day`.
  - `test_eia_empty_response_returns_all_nan_for_range`.
  - `test_usgs_sentinel_is_nan` (value `-999999` becomes NaN).
  - `test_usgs_non_numeric_or_flagged_value_is_nan` (an ice-affected reading such as an empty or `"Ice"` value).
  - `test_registry_has_four_series_with_expected_names_and_tz`.
- [ ] **Step 2:** Run; expected FAIL. Implement; update `check-sources` to use the registry.
- [ ] **Step 3:** With a real key in the environment, run `python -m ftracker.cli check-sources` and confirm all four series show a recent date. If Ahmad has not created an EIA key yet, mark this step blocked, leave it unchecked and continue; the electricity series will record gaps until the key exists.
- [ ] **Step 4:** Run `pytest -v`; expected all PASS. Commit: `feat: EIA and USGS sources, series registry`.

---

### Task 5: Forecasters

**Files:**
- Create: `src/ftracker/models.py`, `tests/test_models.py`

**Tier:** sonnet — modelling choices with interval calibration.

**Interfaces:**
- Produces in `ftracker.models`:
  - `class InsufficientHistory(Exception)`.
  - `class Forecaster(Protocol)`: `name: str`; `forecast(self, history: pd.Series, target_dates: list[date]) -> pd.DataFrame` indexed by `target_date` with columns `point, lo, hi` (80% interval). `history` is indexed by `date`, may contain NaN; the last non-NaN day is the origin and lead = `(target - origin).days`.
  - `SeasonalNaive(name="seasonal_naive")`: point = the last observed value on the same weekday at or before the origin.
  - `Persistence(name="persistence")`: point = last non-NaN value.
  - `GBMForecaster(name="model")`: LightGBM on lag features (lags 1 to 14, day of week, day of year) with one model per lead 1 to 8 (the engine uses leads 2 to 8, the backtest leads 1 to 7).
  - Intervals for all three: the 10th and 90th percentiles of that forecaster's own past residuals for the same lead, computed by rolling-origin over the last 120 days of history, added to the point forecast. Fewer than 60 non-NaN days raises `InsufficientHistory`.

- [ ] **Step 1: Write the failing tests** on synthetic data (weekly sine pattern plus seeded noise, 400 days):
  - `test_persistence_point_is_last_value` and `test_persistence_ignores_trailing_nan`.
  - `test_seasonal_naive_uses_same_weekday` (lead 2 and lead 8 both resolve to the right weekday).
  - `test_interval_orders` (`lo <= point <= hi` for all three).
  - `test_interval_coverage_is_near_80_percent` (rolling backtest of the model on 60 held-out days: coverage between 0.65 and 0.95).
  - `test_model_beats_persistence_on_weekly_pattern` (model MAE below persistence MAE on the held-out days).
  - `test_short_history_raises_insufficient_history` (59 days).
- [ ] **Step 2:** Run; expected FAIL. Implement. LightGBM settings are the builder's call; keep fitting under about 20 seconds per series on a CI runner.
- [ ] **Step 3:** Run `pytest tests/test_models.py -v`; expected PASS. Commit: `feat: baselines and gradient-boosting forecaster with intervals`.

---

### Task 6: Scoring

**Files:**
- Create: `src/ftracker/scoring.py`, `tests/test_scoring.py`

**Tier:** sonnet — signatures with exact numeric tests.

**Interfaces:**
- Produces in `ftracker.scoring`:
  - `mae(y: Sequence[float], yhat: Sequence[float]) -> float`
  - `coverage(y, lo, hi) -> float`
  - `skill(model_mae: float, baseline_mae: float) -> float | None` — `1 - model_mae/baseline_mae`; `None` when `baseline_mae <= 1e-9`.
  - `scoreboard(series: str, forecasts: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame` — inputs as returned by `store.read_forecasts` and `store.read_outcomes`; one row per `(method, horizon)` with columns `series, method, horizon, n, n_missing, mae, coverage, skill`. `skill` is filled only on `method == "model"`, against the lower MAE of the two baselines at that horizon. Rows with a null outcome count in `n_missing`, not `n`.

- [ ] **Step 1: Write the failing tests:**
  - `test_mae`: `mae([1,2,3],[2,2,5]) == 1.0`.
  - `test_coverage`: `coverage([1,2,3],[0,2.5,2],[2,3,4]) == 2/3`.
  - `test_skill`: `skill(0.5, 1.0) == 0.5`; `skill(1.0, 0.0) is None`.
  - `test_scoreboard_splits_by_horizon_and_counts_missing`: three forecasts at horizon 1, one outcome null: `n == 2`, `n_missing == 1`.
  - `test_skill_uses_better_baseline`: model MAE 1, seasonal naive 2, persistence 4 gives skill 0.5.
  - `test_forecast_without_outcome_is_not_counted` (target date not yet settled).
- [ ] **Step 2:** Run; expected FAIL. Implement. Run; expected PASS. Commit: `feat: scoring`.

---

### Task 7: Engine

**Files:**
- Create: `src/ftracker/engine.py`, `tests/test_engine.py`

**Tier:** sonnet — multi-module integration and failure handling.

**Interfaces:**
- Consumes: `store`, `models`, `Series`, `SourceError`, `InsufficientHistory`.
- Produces in `ftracker.engine`:
  - `@dataclass class RunReport: issued: dict[str,int]; scored: dict[str,int]; failed: dict[str,str]`, with property `ok -> bool` (`not failed`).
  - `issue_forecasts(root: Path, series: Series, issue_date: date, now: datetime, run_id: str, forecasters: list[Forecaster]) -> int` — returns rows written, 0 if `issue_date` is already in `store.issued_dates`. Fetches history ending at `issue_date - 1` (about 730 days back), writes a gap and re-raises on `SourceError` or `InsufficientHistory`. Writes target days `issue_date + 1` to `+ 7` as horizons 1 to 7, with `last_observed` in `meta`.
  - `score_outcomes(root: Path, series: Series, today: date, now: datetime) -> int` — for each forecast target date `T` with `T + 2 days <= today` and no outcome file yet, fetch `T` and write the outcome (null if missing); a `SourceError` stops scoring that series for this run and raises.
  - `run_daily(root: Path, registry: dict[str, Series], now: datetime, run_id: str, forecasters: list[Forecaster] | None = None) -> RunReport` — issue date is `now`'s UTC date; every series is isolated in try/except; always rewrites `root/status.json` as `{"last_run": <ISO time>, "series": {<name>: {"last_issue": "YYYY-MM-DD" | null, "error": <str> | null}}}`.
  - `ftracker.cli daily` calls `run_daily` and exits 1 when `report.ok` is false (wired in Task 9).

- [ ] **Step 1: Write the failing tests** with a fake in-memory `Series` and stub forecasters (the stub records the `history` it receives):
  - `test_forecast_uses_only_data_before_issue_date`: the stub's `history.index.max() == issue_date - 1 day`, and the fake series would return a poisoned value for the issue date itself.
  - `test_issues_seven_horizons_with_expected_target_dates` (issue 2026-11-03 gives targets 2026-11-04 to 2026-11-10, horizons 1 to 7).
  - `test_second_run_same_day_writes_nothing_and_does_not_fail`: file bytes unchanged, `issued[series] == 0`, `report.ok`.
  - `test_missing_yesterday_still_issues_from_last_observed` (`meta.last_observed` is two days before the issue date).
  - `test_source_down_writes_gap_and_reports_failure`.
  - `test_one_failing_series_does_not_stop_the_others`.
  - `test_all_sources_down_reports_failures_writes_gaps_and_updates_status`: `report.ok` is false, a gap file exists for every series, `status.json` has the new `last_run`.
  - `test_outcome_scored_only_after_two_day_lag` (target 2026-11-04 is scored on 2026-11-06, not 2026-11-05).
  - `test_missing_outcome_value_is_stored_as_null`.
  - `test_scoring_does_not_overwrite_existing_outcome`.
- [ ] **Step 2:** Run; expected FAIL. Implement.
- [ ] **Step 3:** Run `pytest -v`; expected all PASS. Commit: `feat: daily engine with per-series isolation`.

---

### Task 8: Static page

**Files:**
- Create: `src/ftracker/site.py`, `tests/test_site.py`

**Tier:** sonnet — multi-part page with display rules.

**Interfaces:**
- Consumes: `store` readers, `scoring.scoreboard`, `status.json`, optional `data/backtest/<series>.csv`.
- Produces: `build_site(root: Path, out_dir: Path, now: datetime, series_names: list[str]) -> Path` writing a single self-contained `out_dir/index.html` and returning its path. The page has three parts: upcoming forecasts with intervals, scoreboard per horizon with sample counts, and model versus baseline. Chart implementation (inline SVG or a pinned CDN script) is the builder's call. Required, test-visible elements:
  - the last run time, and a banner with the text `STALE` when `now` is more than 36 hours after `status.json`'s `last_run`;
  - per series and horizon: `n`, MAE, coverage, skill (`n/a` when undefined);
  - for a series with fewer than 14 scored forecasts at a horizon: the text `<n> scored` and no element with id `trend-<series>-h<horizon>`; at 14 or more, that element is present;
  - a per-series note `no forecast issued` when its latest status has an error;
  - a section headed `Backtest (historical, not live)` only when backtest data exists.

- [ ] **Step 1: Write the failing tests** against a data directory fabricated in `tmp_path`:
  - `test_page_shows_last_run_time`.
  - `test_stale_banner_after_36_hours` (37 hours: banner; 35 hours: none).
  - `test_below_14_scored_shows_count_and_no_trend`.
  - `test_at_14_scored_shows_trend`.
  - `test_skill_shows_na_when_baseline_error_is_zero`.
  - `test_scores_listed_for_each_horizon_1_to_7`.
  - `test_failed_series_is_flagged`.
  - `test_backtest_section_labelled_and_only_when_present`.
  - `test_site_builds_with_no_data_and_shows_stale_banner` (empty `data/`, no `status.json`).
- [ ] **Step 2:** Run; expected FAIL. Implement. Run; expected PASS.
- [ ] **Step 3:** Add `ftracker.cli site --out site` and open the generated page once in the browser pane with fabricated data to check the layout at desktop and phone width. Commit: `feat: static scoreboard page`.

---

### Task 9: CLI, daily workflow, README

**Files:**
- Modify: `src/ftracker/cli.py`, `tests/test_workflows.py`
- Create: `.github/workflows/daily.yml`, `README.md`, `scripts/render_readme.py`, `tests/test_readme.py`

**Tier:** sonnet — workflow permissions and generated docs.

**Interfaces:**
- Consumes: `engine.run_daily`, `site.build_site`, `registry.SERIES`, `scoring.scoreboard`.
- Produces: CLI commands (all accept `--data-dir`, default `data`) `daily` (runs `run_daily` with `run_id` from `GITHUB_RUN_ID`, exit 1 if any series failed), `site`, `check-sources`; `scripts/render_readme.py` writes a results block between `<!-- results:start -->` and `<!-- results:end -->` from `results/scoreboard.csv`, which `ftracker.cli site` also writes (to `--results-dir`, default `results`).

- [ ] **Step 1: Write the failing tests** in `tests/test_workflows.py`:
  - `test_daily_has_schedule_and_manual_trigger` (a `cron` entry at about 10:00 UTC and `workflow_dispatch`).
  - `test_daily_permissions_are_contents_write_pages_write_id_token_write`.
  - `test_daily_reads_eia_key_from_secret_never_literal` (the text `secrets.EIA_API_KEY` is present; no 32-character literal key).
  - `test_daily_never_force_pushes` (no `--force` and no `-f` push).
  - `test_daily_commits_data_before_failing_the_job`: the commit-and-push step appears before the step that exits non-zero.
- [ ] **Step 2:** In `tests/test_readme.py` add `test_readme_block_matches_results_csv` (regenerating the block gives the file as committed, as in the malware project).
- [ ] **Step 3:** Run; expected FAIL. Write `daily.yml`: checkout, Python 3.12, install, run the daily command with the failure deferred (record the exit code), commit and push `data/` and `results/` as the Actions bot, build the site, upload and deploy to Pages, and finally fail the job if the daily command failed. Write `README.md` with a short description, the link to the live page (placeholder until Ahmad deploys), the immutability rule explained in two sentences, and the generated results block.
- [ ] **Step 4:** Run `pytest -v`; expected all PASS. Commit: `feat: daily workflow, CLI, README`.
- [ ] **Step 5: Handoff note to Ahmad (do not perform).** Write `docs/ahmad-setup.md` listing the steps only he can do: create the public GitHub repo and push (needs his yes), create the free EIA API key and save it as the `EIA_API_KEY` secret, set Pages source to "GitHub Actions", turn on branch protection that blocks force-push and deletion on `main`, and run the daily workflow once by hand. Commit: `docs: setup steps for Ahmad`.

---

### Task 10: Backtest

**Files:**
- Create: `src/ftracker/backtest.py`, `tests/test_backtest.py`
- Modify: `src/ftracker/cli.py`, `src/ftracker/site.py`

**Tier:** sonnet — leakage-safe validation.

**Interfaces:**
- Consumes: `Forecaster`, `Series.fetch_daily`, `scoring.scoreboard`.
- Produces: `run_backtest(history: pd.Series, forecasters: list[Forecaster], origins: list[date]) -> pd.DataFrame` with the same columns as `store.read_forecasts` plus `actual`; for each origin `O`, forecasts targets `O+1 .. O+7` using history up to `O` only (horizon 1 to 7 measured from `O`). CLI `backtest --series <name> --days 180` writes `data/backtest/<series>.csv`. The site shows the backtest scoreboard under the heading from Task 8.

- [ ] **Step 1: Write the failing tests:**
  - `test_no_leakage`: a stub forecaster asserts `history.index.max() <= origin` for every origin.
  - `test_backtest_rows_per_origin` (one row per method, target and origin, horizons 1 to 7).
  - `test_backtest_writes_only_under_data_backtest` (no file appears under `forecasts/`, `outcomes/` or `gaps/`).
  - `test_origins_without_enough_history_are_skipped`.
- [ ] **Step 2:** Run; expected FAIL. Implement; wire the CLI and the site section. Run `pytest -v`; expected all PASS.
- [ ] **Step 3:** Run the backtest once against real data for all series that have a source available, check the page labels it as not live, and commit: `feat: labelled backtest section`.

---

### Task 11: End-to-end dry run

**Files:** none created; run and report.

**Tier:** haiku — run a named command and report the output.

- [ ] **Step 1:** Run the commands below one at a time and report the pass count or output of each. Do not change any file.

```bash
pytest -v
python -m ftracker.cli daily --data-dir /tmp/ft-dry
python -m ftracker.cli daily --data-dir /tmp/ft-dry
python -m ftracker.cli site --data-dir /tmp/ft-dry --results-dir /tmp/ft-results --out /tmp/ft-site
python -m ftracker.immutability --base HEAD~1
```

- [ ] **Step 2:** Report: the test pass count and any failure; the first `daily` run's issued count per series and any failed series; whether the second `daily` run issued 0 and exited 0; whether `/tmp/ft-site/index.html` exists and which series it lists; the immutability output.

---

## Self-review notes

- **Spec coverage:** immutability (Tasks 1, 2), failure visibility and stale banner (7, 8, 9), per-series isolation (7), cold start counts and 14 threshold (8), backtest (10), outcomes lag and null outcomes (7), baselines and per-horizon scoring (5, 6, 8), public repo and the EIA key (9 handoff).
- **Plan decisions to confirm:** the stale banner uses the time of the last run, and a failed series is flagged separately by its own latest status; the issue date is the UTC date of the run (about 10:00 UTC, after midnight in every US time zone); history for fitting is about two years.
