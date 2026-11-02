# Setup steps only Ahmad can do

The code is finished locally; nothing below has been done for you.

1. **Create the public GitHub repository and push.** Create an empty public repo, add it as `origin`, and push `main`. Pushing needs your explicit yes.
2. **Create the free EIA API key** at https://www.eia.gov/opendata/ and save it as the repository secret `EIA_API_KEY` (Settings > Secrets and variables > Actions). Never commit the key.
3. **Set the Pages source** to "GitHub Actions" (Settings > Pages > Build and deployment).
4. **Turn on branch protection for `main`** that blocks force-push and deletion (Settings > Branches). The append-only rule depends on history never being rewritten. Do not require pull requests, because the daily workflow pushes straight to `main`.
5. **Run the daily workflow once by hand** (Actions > daily > Run workflow). Confirm it ends green, that a `data:` commit appeared, and that the Pages URL loads the scoreboard. Then put that URL in the "Live page" line of `README.md`.
