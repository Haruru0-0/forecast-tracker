# Gotchas

See [[architecture]].

- **Never edit files under `data/forecasts`, `data/outcomes` or `data/gaps`,** or the guard files (`immutability.py`, the workflows, `commit_and_push.sh`) in the same change as protected data. The check will fail.
- **`python -m ftracker.cli daily` needs `EIA_API_KEY`** in the environment.
- **The daily run commits to `main`,** so pull before pushing.
- **The README results block is generated:** run `python scripts/render_readme.py`, do not edit it.
- **`docs/ahmad-setup.md` lists one-time steps only Ahmad can do** (secret, Pages source, branch ruleset); it was written before the repo went live.
- **`.venv/` is in the working folder** (git-ignored). Install with `pip install -e ".[dev]"`.
- **`graphify.exe` is blocked on this machine;** use `python -m graphify update .`.
