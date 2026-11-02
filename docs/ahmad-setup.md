# Setup steps only Ahmad can do

The code is finished locally on the branch `feat/forecast-tracker`; nothing below has been done for you. Do the steps in this order: the secret, Pages and the ruleset must exist BEFORE the first push, otherwise the first scheduled run is red and the record starts without its protections.

1. **Confirm two choices before anything is pushed.** Pick the licence for the repository (none is committed yet), and confirm the commit author name and email in the history (`git log --format="%an <%ae>"`) are the ones you want public. Both are your call.
2. **Merge `feat/forecast-tracker` into `main`.** This is your decision; nothing has been merged for you. The daily workflow only runs on `main`.
3. **Create the public GitHub repository, empty.** Do not push yet. Add it as `origin` locally.
4. **Create the free EIA API key** at https://www.eia.gov/opendata/ and save it as the repository secret `EIA_API_KEY` (Settings > Secrets and variables > Actions). Never commit the key. Until the secret exists, the electricity series fails every day with `SourceError: EIA_API_KEY not set`, a gap file is written for it, and the daily job ends red every day (the other series are still recorded).
5. **Set the Pages source** to "GitHub Actions" (Settings > Pages > Build and deployment).
6. **Add a ruleset for `main`** (Settings > Rules > Rulesets > New branch ruleset): target the default branch, turn on "Block force pushes" and "Restrict deletions", and leave the bypass list EMPTY, so the rule also applies to you as admin. The append-only rule depends on history never being rewritten. Do not require pull requests, because the daily workflow pushes straight to `main`.
7. **Push `main`.** Pushing needs your explicit yes.
8. **Run the daily workflow once by hand** (Actions > daily > Run workflow). Confirm it ends green (or red only because of the EIA key, if you skipped step 4), that a `data:` commit appeared, and that the Pages URL loads the scoreboard. Then put that URL in the "Live page" line of `README.md`.

Notes: allow Actions under Settings > Actions > General. GitHub may disable scheduled workflows after 60 days without repository activity, so if the page stops updating, check the Actions tab and re-enable the workflow; the page itself shows a STALE banner once the last run is more than 36 hours old, even if nothing rebuilds it.
