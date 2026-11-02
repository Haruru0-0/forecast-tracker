# Forecast Tracker: design

Date: 2026-11-02. Owner: Ahmad Kanaan. Status: draft for approval.

## Intent and why

A public, self-updating page that publishes forecasts for several real-world measurements (weather, air quality, electricity demand, river level) **before** the outcome is known, then scores them against what actually happened. It is a data science portfolio project, the second one after `malware-classifier`.

The point is trust. Most portfolio forecasting projects show one backtest chart that nobody can check. This one keeps a time-stamped record of predictions that cannot be edited afterwards, so a visitor can see for themselves whether the forecasts are any good and whether they beat a simple guess. It keeps running after Ahmad stops working on it.

## What the visitor sees

One page with three things together (Ahmad's choice, "a mix of all"):

1. **Upcoming forecasts** for each series, with an uncertainty range.
2. **Scoreboard**: past forecasts scored against actual outcomes, over time, per series.
3. **Model vs baseline**: whether the model beats a naive guess such as "same as last week".

## Goals

- Four series in the first version, all US data (Ahmad's choice): **weather, air quality, electricity demand, river level**.
- One shared engine; a series is a small plug-in (data source, target definition, baseline). Adding a fifth series should not need changes to the engine.
- Every forecast is stored with a timestamp before its outcome exists and is never changed afterwards.
- Every forecast has a prediction interval, and the scoreboard reports whether the intervals are honest (coverage).
- Runs unattended every day on GitHub Actions (Ahmad's choice), at no cost.
- Tests first, like `malware-classifier`.

## Non-goals

- Beating state-of-the-art forecasters. A model that loses to its baseline is a valid, publishable result and must be shown as such.
- Real-time or sub-daily forecasting.
- User accounts, uploads, or any interactive modelling by visitors.
- Financial or trading use. Electricity numbers are demand, not prices.

## Anti-goals (Ahmad's choices: what would make this a failure even if it runs)

- **Looks like a toy**: a chart with no scoring, so nobody can tell whether the forecasts are good. Scoring, baseline comparison and sample sizes must be on the page.
- **Breaks silently**: the daily job fails for days and nobody notices. A failed or stale run must be visible on the page and must notify Ahmad. Missing data is recorded as a gap, never filled in or hidden.
- **Forecasts can be edited**: any change to a past forecast destroys the point of the project. The rule must be enforced by a check, not by promise.

## Constraints

- Python 3.12, tests in `tests/`, package under `src/` (same layout as `malware-classifier`).
- Free data only, no paid APIs. Sources known to be free and open: Open-Meteo (weather, air quality; no key), EIA open data (electricity demand; free API key), USGS Water Services (river level; no key).
- Free hosting only: GitHub Actions for the daily job, static GitHub Pages for the page. This requires a public repository.
- Small data. The whole repository stays well under a few hundred MB for a year of running.
- The EIA key is a secret stored in GitHub, created by Ahmad. Never committed to the repo.
- Ahmad's conventions from `malware-classifier` carry over: commits are authored as Ahmad, nothing is pushed without his explicit yes, and any number shown in the README comes from generated results, never typed by hand.

## Decisions made by Ahmad

- Page shows upcoming forecasts, scoreboard and baseline comparison together.
- Topics: weather, air quality, electricity demand, river level.
- Region: United States.
- Runs on GitHub Actions.
- Tools and forecasting methods are left to the builder.
- Order: this project first, then a data-quality auditor as a separate project.
- Version 1 includes a backtest section, built last. Live tracking is the first milestone; the backtest is clearly labelled and stored separately from the live record.
- The repository is public, and the daily job pushes straight to `main`.

## My calls (not yet agreed with Ahmad; check these)

- **Hosting**: static GitHub Pages, because the daily job already commits results and a static page never sleeps. Streamlit Cloud was the alternative.
- **Horizon**: forecasts for the next 1 to 7 days at daily resolution (daily maximum temperature, daily mean air-quality index, daily peak or mean electricity demand, daily mean river level or stage).
- **Location**: one US metro area chosen so that all four sources have reliable data nearby (builder picks and documents it).
- **Baselines**: seasonal naive ("same day last week") and persistence ("same as yesterday"); the scoreboard reports skill relative to the better of the two.
- **Scores**: mean absolute error, skill versus baseline, prediction-interval coverage, and a sample count next to every number so early results are not over-read.
- **Immutability**: forecasts are written as append-only files, one per issue date, and a CI check fails if an already-committed forecast file is modified or removed. Git commit time is the timestamp of record.
- **Failure visibility**: the page shows the date of the last successful run and a visible warning when it is older than 36 hours; a failed Actions run also notifies Ahmad by GitHub's normal notification.
- **Repository and trust**: the repo is public. The daily job pushes to `main` with the built-in GitHub token. Force-push and branch deletion are blocked on `main`. Each forecast file records the workflow run id and issue time, so GitHub's own run record backs up the commit time. An external anchor such as signed tags is not required for version 1.
- **Where the immutability check runs**: on every push to `main` (including the bot's own) and every pull request. Past forecast and outcome files are never edited or removed. A bug in the engine is fixed for future issue dates only; a mistaken forecast stays in the record and is annotated by a new file, not changed.
- **One forecast per series per issue date**: a retried or repeated run skips an issue date that already has a file and never overwrites it. A late or back-filled run is issued under its own, later date. Forecasts use only data up to the end of the previous complete day, for target days issue date +1 to +7.
- **Outcomes and revisions**: a target is scored after a two-day settling lag, using the value the source publishes at that time. The value and its fetch time are stored in an append-only outcome file, separate from the forecast. Later source revisions are ignored for scoring.
- **Per-series failure handling**: each series runs independently. The job commits whatever succeeded, flags failed or gapped series on the page, then exits with an error if any series failed, so GitHub emails Ahmad.
- **Sample thresholds**: trend lines appear once a series and horizon has 14 scored forecasts; below that the page shows counts only.
- **Scoreboard detail**: scores are shown per horizon (1 to 7 days), not averaged across horizons. Prediction intervals target 80% coverage. Skill is undefined, and shown as such, when the baseline error is near zero.
- **"Day" definition**: each series uses the local time zone of the chosen metro area; the choice is documented by the builder.
- **Cold start**: in the first weeks there are few scored forecasts, so the page shows "days tracked" and withholds trend lines until a minimum sample exists. The backtest section (Ahmad's decision, built last) fills the gap, clearly labelled as backtest and kept separate from live results.

## Left to the builder

- Forecasting methods and libraries (a statistical method, gradient boosting, or both), as long as every forecast has an interval and the baselines are always run alongside.
- Exact target definition per series, the specific metro area and gauge, and the data-retrieval details, including rate limits and retries.
- Storage format of forecasts and outcomes (for example CSV or Parquet files in the repo).
- Charting library and page design, within the three-part layout above.
- Repository name, directory layout, and how the CI check for immutability is implemented.
- Whether the daily job runs once or in two steps (issue forecasts, then score yesterday's).

## Success looks like

After a month of unattended running: the page is live, the last-run date is current, every series has a growing record of scored live forecasts with sample sizes, the model-versus-baseline comparison is honest (including where the model loses), and a modified past forecast would make CI fail.
