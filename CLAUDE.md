# forecast-tracker

Self-updating forecast scoreboard. Forecasts are append-only; outcomes are scored later.

## Conventions

- Python 3.12, package in `src/ftracker`, tests in `tests/`, test-first.
- Commits are made as Ahmad: no `Co-Authored-By` and no "Generated with Claude" lines. Never push without his explicit yes.
- README numbers come from generated results, never typed by hand.
- Stored forecast, outcome and gap files are never overwritten.
