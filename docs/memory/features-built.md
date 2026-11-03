# Features built

Structure: [[architecture]].

- Daily job that pulls public data (Houston weather and air quality, ERCOT electricity demand, Buffalo Bayou river gauge), issues 1 to 7 day forecasts, scores earlier ones against outcomes and republishes.
- Public page with status header, section index, two-column cards, skill pills, a per-horizon scoreboard, model-versus-baseline comparison, a verdict line and a separate backtest (redesigned in commit b0c1928).
- Append-only forecast, outcome and gap files, enforced by `immutability.py` in CI (checks each commit and the net diff, and guards the checker and workflows).
- README results block generated from real scores; `results/scoreboard.csv` exported.
- Test suite covering models, scoring, store, sources, site, CLI, README rendering and an end-to-end run.
- Daily data commits appear in history ("data: daily run ...", "results: daily run ...").
