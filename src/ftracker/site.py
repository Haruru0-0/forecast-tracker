"""Static scoreboard page: one self-contained index.html with inline SVG charts, no scripts."""

from __future__ import annotations

import html
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from ftracker import registry, scoring, store

STALE_AFTER = timedelta(hours=36)
MIN_TREND = 14
METHODS = ("model", "seasonal_naive", "persistence")
METHOD_LABEL = {"model": "model", "seasonal_naive": "seasonal naive", "persistence": "persistence"}
BACKTEST_TITLE = "Backtest (historical, not live)"


def _e(x: object) -> str:
    return html.escape(str(x), quote=True)


def _num(v: float) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:.2f}"


def _unit(name: str) -> str:
    for s in registry.SERIES.values():
        if s.name == name:
            return s.unit
    return ""


def _read_status(root: Path) -> dict | None:
    try:
        doc = json.loads((Path(root) / "status.json").read_text(encoding="utf-8"))
        datetime.fromisoformat(doc["last_run"])
        return doc
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def all_scoreboards(root: Path, series_names: list[str]) -> pd.DataFrame:
    frames = []
    for name in series_names:
        board = scoring.scoreboard(name, store.read_forecasts(root, name), store.read_outcomes(root, name))
        if not board.empty:
            frames.append(board)
    if not frames:
        return pd.DataFrame(columns=scoring.COLUMNS)
    return pd.concat(frames, ignore_index=True)[scoring.COLUMNS]


def _backtest_board(root: Path, name: str) -> pd.DataFrame | None:
    path = Path(root) / "backtest" / f"{name}.csv"
    if not path.is_file():
        return None
    df = pd.read_csv(path)
    for col in ("origin", "target_date"):
        df[col] = pd.to_datetime(df[col]).dt.date
    forecasts = df.rename(columns={"origin": "issue_date"})[store.FORECAST_COLUMNS]
    outcomes = df[["target_date", "actual"]].rename(columns={"actual": "value"}).drop_duplicates("target_date")
    return scoring.scoreboard(name, forecasts, outcomes)


# ---------- charts ----------

def _fan_chart(rows: pd.DataFrame, label: str) -> str:
    """Model point with 80% band, baselines as dashed lines, over the 7 target days."""
    w, h, left, right, top, bottom = 600, 210, 60, 14, 12, 34
    series = {m: rows[rows["method"] == m].sort_values("horizon") for m in METHODS}
    vals = [v for m in METHODS for col in ("point", "lo", "hi") for v in series[m][col]
            if m == "model" or col == "point"]
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    horizons = sorted(rows["horizon"].unique())
    n = len(horizons)

    def x(hz: int) -> float:
        i = horizons.index(hz)
        return left + (w - left - right) * (i / (n - 1) if n > 1 else 0.5)

    def y(v: float) -> float:
        return top + (h - top - bottom) * (1 - (v - lo) / (hi - lo))

    parts = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{_e(label)}">']
    for v in (lo + pad, hi - pad):
        parts.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
                     f'<text class="tick" x="{left - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{_num(v)}</text>')
    m = series["model"]
    if len(m):
        upper = [f"{x(int(r.horizon)):.1f},{y(r.hi):.1f}" for r in m.itertuples()]
        lower = [f"{x(int(r.horizon)):.1f},{y(r.lo):.1f}" for r in reversed(list(m.itertuples()))]
        parts.append(f'<polygon class="band" points="{" ".join(upper + lower)}"/>')
    for method in ("seasonal_naive", "persistence"):
        b = series[method]
        if len(b):
            pts = " ".join(f"{x(int(r.horizon)):.1f},{y(r.point):.1f}" for r in b.itertuples())
            parts.append(f'<polyline class="line {method}" points="{pts}"/>')
    if len(m):
        pts = " ".join(f"{x(int(r.horizon)):.1f},{y(r.point):.1f}" for r in m.itertuples())
        parts.append(f'<polyline class="line model" points="{pts}"/>')
        for r in m.itertuples():
            parts.append(f'<circle class="dot" cx="{x(int(r.horizon)):.1f}" cy="{y(r.point):.1f}" r="3"/>')
    for hz in horizons:
        parts.append(f'<text class="tick" x="{x(hz):.1f}" y="{h - 10}" text-anchor="middle">+{hz}d</text>')
    parts.append("</svg>")
    return "".join(parts)


def _legend(model_label: str = "model") -> str:
    return (f'<p class="legend"><span class="key model">{model_label}</span>'
            '<span class="key seasonal_naive">seasonal naive</span>'
            '<span class="key persistence">persistence</span></p>')


def _trend_chart(dom_id: str, errors: pd.Series) -> str:
    w, h = 140, 34
    vals = list(errors)
    top = max(vals) or 1.0
    n = len(vals)
    pts = " ".join(f"{2 + (w - 4) * i / (n - 1):.1f},{h - 3 - (h - 6) * v / top:.1f}" for i, v in enumerate(vals))
    return (f'<svg id="{_e(dom_id)}" class="trend" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="absolute error over time, {n} forecasts, max {_num(top)}">'
            f'<polyline class="line model" points="{pts}"/></svg>')


def _mae_bars(board: pd.DataFrame, label: str) -> str:
    sub = board[board["mae"].notna()]
    if sub.empty:
        return '<p class="muted">no scored forecasts yet</p>'
    horizons = sorted(sub["horizon"].unique())
    top = float(sub["mae"].max()) or 1.0
    w, h, left, bottom, top_pad = 600, 210, 60, 34, 14
    group = (w - left - 10) / len(horizons)
    bar = min(18.0, group / 4)
    parts = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{_e(label)}">',
             f'<line class="grid" x1="{left}" x2="{w - 10}" y1="{h - bottom}" y2="{h - bottom}"/>',
             f'<text class="tick" x="{left - 6}" y="{top_pad + 4}" text-anchor="end">{_num(top)}</text>',
             f'<text class="tick" x="{left - 6}" y="{h - bottom + 4}" text-anchor="end">0</text>']
    for gi, hz in enumerate(horizons):
        gx = left + group * gi + group / 2 - bar * 1.5
        for mi, method in enumerate(METHODS):
            r = sub[(sub["horizon"] == hz) & (sub["method"] == method)]
            if r.empty:
                continue
            v = float(r["mae"].iloc[0])
            bh = (h - bottom - top_pad) * v / top
            parts.append(f'<rect class="bar {method}" x="{gx + bar * mi:.1f}" y="{h - bottom - bh:.1f}" '
                         f'width="{bar - 2:.1f}" height="{bh:.1f}"><title>{METHOD_LABEL[method]} h{hz}: '
                         f'MAE {_num(v)}, n={int(r["n"].iloc[0])}</title></rect>')
        parts.append(f'<text class="tick" x="{left + group * gi + group / 2:.1f}" y="{h - 10}" '
                     f'text-anchor="middle">+{hz}d</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------- sections ----------

def _status_note(entry: dict | None) -> str:
    if entry and entry.get("error"):
        return f'<p class="note bad">no forecast issued: {_e(entry["error"])}</p>'
    return ""


def _upcoming(name: str, fc: pd.DataFrame, entry: dict | None, unit: str) -> str:
    out = [f'<article class="card"><h3>{_e(name)}{f" <span class=unit>({_e(unit)})</span>" if unit else ""}</h3>',
           _status_note(entry)]
    if fc.empty:
        out.append('<p class="muted">no data yet</p></article>')
        return "".join(out)
    latest = fc[fc["issue_date"] == fc["issue_date"].max()]
    out.append(f'<p class="muted">issued {latest["issue_date"].iloc[0].isoformat()}</p>')
    out.append(_fan_chart(latest, f"{name} forecast for the next days"))
    out.append(_legend("model (line, 80% band)"))
    unit_h = _e(unit) if unit else "units"
    out.append(f'<div class="scroll"><table><thead><tr><th>Day</th><th>Model, 80% interval ({unit_h})</th>'
               '<th>Seasonal naive</th><th>Persistence</th></tr></thead><tbody>')
    piv = {m: latest[latest["method"] == m].set_index("horizon") for m in METHODS}
    for hz in sorted(piv["model"].index):
        m = piv["model"].loc[hz]

        def base(method: str) -> str:
            p = piv[method]
            return _num(p.loc[hz, "point"]) if hz in p.index else "n/a"

        out.append(f'<tr data-up-row="{_e(name)}-h{hz}"><td>{m["target_date"].isoformat()} (+{hz}d)</td>'
                   f'<td class="m"><strong>{_num(m["point"])}</strong> <span class="muted">{_num(m["lo"])} to {_num(m["hi"])}</span></td>'
                   f'<td>{base("seasonal_naive")}</td><td>{base("persistence")}</td></tr>')
    out.append("</tbody></table></div></article>")
    return "".join(out)


def _skill_cell(row: pd.Series) -> str:
    sk = row["skill"]
    return f'{"n/a" if pd.isna(sk) else f"{sk:.2f}"} (n={int(row["n_skill"])})'


def _score_table(name: str, board: pd.DataFrame, fc: pd.DataFrame, oc: pd.DataFrame, trends: bool) -> str:
    model = board[board["method"] == "model"].sort_values("horizon")
    attr = "data-row" if trends else "data-bt-row"
    rows = []
    for r in model.itertuples():
        hz = int(r.horizon)
        extra = ""
        if trends:
            if r.n >= MIN_TREND:
                m = fc[(fc["method"] == "model") & (fc["horizon"] == hz)].merge(oc, on="target_date")
                m = m[m["value"].notna()].sort_values("target_date")
                extra = _trend_chart(f"trend-{name}-h{hz}", (m["value"] - m["point"]).abs().reset_index(drop=True))
            else:
                extra = f"{int(r.n)} scored"
        cov = "n/a" if pd.isna(r.coverage) else f"{r.coverage * 100:.0f}%"
        rows.append(f'<tr {attr}="{_e(name)}-h{hz}"><td>+{hz}d</td><td>{int(r.n)}</td><td>{_num(r.mae)}</td>'
                    f'<td>{cov}</td><td>{_skill_cell(pd.Series(r._asdict()))}</td>'
                    + (f"<td>{extra}</td>" if trends else "") + "</tr>")
    head = "<th>Horizon</th><th>n</th><th>MAE</th><th>Coverage (80%)</th><th>Skill (n)</th>"
    head += "<th>Trend</th>" if trends else ""
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


CSS = """
:root{--bg:#fbfbf9;--fg:#1d2327;--muted:#5d666d;--card:#fff;--line:#dfe2e0;--accent:#1b6ac9;--band:rgba(27,106,201,.16);
--seasonal_naive:#c2570c;--persistence:#6d7b88;--warn-bg:#fdeaea;--warn-fg:#8f1d1d;--warn-line:#e4a3a3}
@media (prefers-color-scheme:dark){:root{--bg:#14181b;--fg:#e8eaeb;--muted:#9aa3a9;--card:#1c2226;--line:#2e373c;
--accent:#6aa7f5;--band:rgba(106,167,245,.2);--seasonal_naive:#f09a52;--persistence:#9aa7b4;
--warn-bg:#3a1c1c;--warn-fg:#ffb3b3;--warn-line:#7a3a3a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
font-variant-numeric:tabular-nums}
main{max-width:960px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.2rem;margin:36px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:1.02rem;margin:0 0 4px;overflow-wrap:anywhere}
.unit,.muted{color:var(--muted);font-weight:400}.muted{margin:2px 0 8px;font-size:.9rem}
.rule{color:var(--muted);margin:8px 0}
.banner{background:var(--warn-bg);color:var(--warn-fg);border:1px solid var(--warn-line);border-radius:8px;padding:10px 14px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 16px}
.note.bad{color:var(--warn-fg);background:var(--warn-bg);border-radius:6px;padding:6px 10px;margin:6px 0;overflow-wrap:anywhere}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font-weight:600;color:var(--muted)}
svg.chart{display:block;width:100%;height:auto;max-width:600px;margin:6px 0}
svg.trend{width:120px;height:30px;vertical-align:middle}
.grid{stroke:var(--line);stroke-width:1}.tick{fill:var(--muted);font-size:16px}
.band{fill:var(--band)}.line{fill:none;stroke-width:2;stroke-linejoin:round}
.line.model{stroke:var(--accent)}.line.seasonal_naive{stroke:var(--seasonal_naive);stroke-dasharray:5 3}
.line.persistence{stroke:var(--persistence);stroke-dasharray:2 3}
.dot{fill:var(--accent)}.bar.model{fill:var(--accent)}.bar.seasonal_naive{fill:var(--seasonal_naive)}
.bar.persistence{fill:var(--persistence)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.85rem;color:var(--muted);margin:2px 0 10px}
.key::before{content:"";display:inline-block;width:14px;height:0;border-top:3px solid;margin-right:6px;vertical-align:middle}
.key.model::before{border-color:var(--accent)}.key.seasonal_naive::before{border-color:var(--seasonal_naive)}
.key.persistence::before{border-color:var(--persistence)}
td.m{white-space:normal}td.m .muted{display:block;white-space:nowrap;margin:0;font-size:.85em}
@media (max-width:480px){table{font-size:.85rem}th{white-space:normal;vertical-align:bottom}td.m{min-width:0}svg.trend{width:56px}th,td{padding:6px 4px}td:first-child{white-space:normal}main{padding-top:16px}h1{font-size:1.35rem}.card{padding:10px}}
"""


def _gap_line(name: str, root: Path) -> str:
    gaps = store.read_gaps(root, name)
    if gaps.empty:
        return ""
    last = gaps.sort_values("issue_date").iloc[-1]
    return (f'<p class="muted">{len(gaps)} gap day(s); latest {last["issue_date"].isoformat()}: '
            f'{_e(last["reason"])}</p>')


def build_site(root: Path, out_dir: Path, now: datetime, series_names: list[str]) -> Path:
    root, out_dir = Path(root), Path(out_dir)
    now = _utc(now)
    status = _read_status(root)
    entries = (status or {}).get("series", {})

    banner, last_run_txt = "", "never"
    if status is None:
        banner = '<div class="banner" role="alert"><strong>STALE</strong> no run recorded yet (status.json is missing).</div>'
    else:
        last = _utc(datetime.fromisoformat(status["last_run"]))
        last_run_txt = last.strftime("%Y-%m-%d %H:%M UTC")
        if now - last > STALE_AFTER:
            hours = int((now - last).total_seconds() // 3600)
            banner = (f'<div class="banner" role="alert"><strong>STALE</strong> the last run was {hours} hours ago; '
                      'scores below may be out of date.</div>')

    data = {}
    for name in series_names:
        data[name] = (store.read_forecasts(root, name), store.read_outcomes(root, name))
    boards = {n: scoring.scoreboard(n, fc, oc) for n, (fc, oc) in data.items()}

    upcoming = "".join(_upcoming(n, data[n][0], entries.get(n), _unit(n)) for n in series_names)

    score_cards = []
    for n in series_names:
        fc, oc = data[n]
        card = [f'<article class="card"><h3>{_e(n)}</h3>', _status_note(entries.get(n))]
        if boards[n].empty:
            card.append('<p class="muted">no data yet</p>')
        else:
            card.append(_score_table(n, boards[n], fc, oc, trends=True))
            card.append(_gap_line(n, root))
        card.append("</article>")
        score_cards.append("".join(card))

    compare = []
    for n in series_names:
        compare.append(f'<article class="card"><h3>{_e(n)}</h3>')
        if boards[n].empty:
            compare.append('<p class="muted">no data yet</p>')
        else:
            compare.append(_mae_bars(boards[n], f"{n}: mean absolute error by horizon, model vs baselines"))
            compare.append(_legend("model"))
            compare.append('<p class="muted">Mean absolute error per horizon, lower is better. Skill is '
                           'shown in the scoreboard above.</p>')
        compare.append("</article>")

    backtest = []
    for n in series_names:
        bb = _backtest_board(root, n)
        if bb is not None and not bb.empty:
            backtest.append(f'<article class="card"><h3>{_e(n)}</h3>'
                            + _score_table(n, bb, pd.DataFrame(), pd.DataFrame(), trends=False) + "</article>")
    backtest_html = ""
    if backtest:
        backtest_html = (f"<h2>{BACKTEST_TITLE}</h2>"
                         '<p class="rule">Walk-forward replay on past data. Kept apart from the live numbers above.</p>'
                         + "".join(backtest))

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Forecast tracker</title><style>{CSS}</style></head>
<body><main>
<h1>Forecast tracker</h1>
<p class="muted">Last run: {_e(last_run_txt)}</p>
{banner}
<p class="rule">Every forecast is saved before its outcome is known and never edited. CI fails if a past file changes.</p>
<h2>Upcoming forecasts</h2>{upcoming}
<h2>Scoreboard per horizon</h2>
<p class="rule">n is the number of scored forecasts. Skill compares the model with the better baseline on the days all three were scored (n shown with it); n/a when undefined.</p>
{"".join(score_cards)}
<h2>Model vs baseline</h2>{"".join(compare)}
{backtest_html}
</main></body></html>
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(page, encoding="utf-8")
    return path
