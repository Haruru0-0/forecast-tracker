# Decisions

See [[architecture]]. Reasons marked (inferred) were not stated.

- **Forecasts and outcomes are append-only,** so a forecast cannot be quietly rewritten after the answer is known. CI makes any violation keep every later run red.
- **README numbers come from generated results,** never typed by hand.
- **Commits are made as Ahmad** with no `Co-Authored-By` and no "Generated with Claude" line; never push without his explicit yes (from `CLAUDE.md`).
- **Houston is the metro** (`docs/metro.md` explains why).
- **The daily workflow only runs on `main`,** never overlaps and is never cancelled mid-run.
- **2026-11-02: mirrored to GitLab with the standard mirror workflow** (an earlier customised trigger was reverted).
