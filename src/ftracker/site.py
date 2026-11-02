"""Static scoreboard page: one self-contained index.html with inline SVG charts.

The page is correct without scripts at build time. A small inline script (no external files)
re-checks staleness against the viewer's clock, because a page that stopped being rebuilt
would otherwise keep its last "fresh" look forever."""

from __future__ import annotations

import html
import json
import math
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from ftracker import config, registry, scoring, store

STALE_AFTER = timedelta(hours=36)
MIN_TREND = 14
METHODS = ("model", "seasonal_naive", "persistence")
METHOD_LABEL = {"model": "model", "seasonal_naive": "seasonal naive", "persistence": "persistence"}
BACKTEST_TITLE = "Backtest (historical, not live)"


def _e(x: object) -> str:
    return html.escape(str(x), quote=True)


def _num(v: float) -> str:
    if v is None or pd.isna(v) or not math.isfinite(v):
        return "n/a"
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:.2f}"


def _unit(name: str) -> str:
    for s in registry.SERIES.values():
        if s.name == name:
            return s.unit
    return ""


def _read_status(root: Path) -> tuple[dict | None, str]:
    """Return (status, problem). problem is "missing" or "unreadable" when status is None."""
    path = Path(root) / "status.json"
    if not path.is_file():
        return None, "missing"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        datetime.fromisoformat(doc["last_run"])
    except (OSError, ValueError, KeyError, TypeError):
        return None, "unreadable"
    return doc, ""


def _entries(status: dict | None) -> dict:
    series = (status or {}).get("series")
    if not isinstance(series, dict):
        return {}
    return {k: v for k, v in series.items() if isinstance(v, dict)}


def _heading(name: str, unit: str) -> str:
    u = f' <span class="unit">({_e(unit)})</span>' if unit else ""
    return f"<h3>{_e(name)}{u}</h3>"


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

def _fan_chart(rows: pd.DataFrame, label: str, unit: str = "") -> str:
    """Model point with 80% band, baselines as dashed lines, over the 7 target days.

    Points whose values are not finite are skipped, so no "nan" reaches the SVG."""
    w, h, left, right, top, bottom = 600, 220, 72, 26, 28, 36
    rows = rows[rows["point"].map(math.isfinite)]
    series = {m: rows[rows["method"] == m].sort_values("horizon") for m in METHODS}
    band = series["model"][series["model"]["lo"].map(math.isfinite) & series["model"]["hi"].map(math.isfinite)]
    vals = [v for m in METHODS for v in series[m]["point"]] + list(band["lo"]) + list(band["hi"])
    if not vals:
        return '<p class="muted">no finite forecast values to chart</p>'
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

    parts = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{_e(label)}">',
             f'<text class="tick" x="2" y="18">{_e(unit)}</text>']
    for v in (lo + pad, hi - pad):
        parts.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
                     f'<text class="tick" x="{left - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{_num(v)}</text>')
    m = series["model"]
    if len(band) > 1:
        upper = [f"{x(int(r.horizon)):.1f},{y(r.hi):.1f}" for r in band.itertuples()]
        lower = [f"{x(int(r.horizon)):.1f},{y(r.lo):.1f}" for r in reversed(list(band.itertuples()))]
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
            parts.append(f'<circle class="dot" cx="{x(int(r.horizon)):.1f}" cy="{y(r.point):.1f}" r="4.5">'
                         f'<title>+{int(r.horizon)}d: {_num(r.point)} {_e(unit)}, 80% {_num(r.lo)} to {_num(r.hi)}'
                         '</title></circle>')
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
    vals = [v for v in errors if math.isfinite(v)]
    top = max(vals, default=0.0) or 1.0
    n = len(vals)
    pts = " ".join(f"{2 + (w - 4) * i / max(n - 1, 1):.1f},{h - 3 - (h - 6) * v / top:.1f}" for i, v in enumerate(vals))
    return (f'<svg id="{_e(dom_id)}" class="trend" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="absolute error over time, {n} forecasts, max {_num(top)}">'
            f'<polyline class="line model" points="{pts}"/></svg>')


def _mae_bars(board: pd.DataFrame, label: str, unit: str = "") -> str:
    sub = board[board["mae"].map(lambda v: pd.notna(v) and math.isfinite(v))]
    if sub.empty:
        return '<p class="muted">no scored forecasts yet</p>'
    horizons = sorted(sub["horizon"].unique())
    top = float(sub["mae"].max()) or 1.0
    w, h, left, bottom, top_pad = 600, 232, 72, 36, 44
    group = (w - left - 10) / len(horizons)
    bar = min(18.0, group / 4)
    parts = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{_e(label)}">',
             f'<text class="tick" x="2" y="18">MAE ({_e(unit)})</text>',
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
                         f'MAE {_num(v)} {_e(unit)}, n={int(r["n"].iloc[0])}</title></rect>')
        parts.append(f'<text class="tick" x="{left + group * gi + group / 2:.1f}" y="{h - 10}" '
                     f'text-anchor="middle">+{hz}d</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------- sections ----------

def _status_note(entry: dict | None) -> str:
    if entry and entry.get("error"):
        return f'<p class="note bad">no forecast issued: {_e(entry["error"])}</p>'
    return ""


def _tracked(fc: pd.DataFrame, gaps: pd.DataFrame) -> str:
    """Cold-start context: distinct issue dates with a forecast file, and gap days."""
    days = fc["issue_date"].nunique() if not fc.empty else 0
    gap_days = gaps["issue_date"].nunique() if not gaps.empty else 0
    return f'<p class="muted tracked">days tracked: {days}; gap days: {gap_days}</p>'


WHAT = {
    "weather_tmax": "Daily high temperature",
    "air_quality_aqi": "Daily mean air quality index",
    "electricity_peak_mw": "Daily peak electricity demand",
    "river_discharge_cfs": "Daily mean river flow",
}


def _what(name: str) -> str:
    return f'<p class="what">{_e(WHAT[name])}, {_e(config.METRO["name"])}</p>' if name in WHAT else ""


def _upcoming(name: str, fc: pd.DataFrame, entry: dict | None, unit: str, today: date,
              gaps: pd.DataFrame) -> str:
    newest_gap = None if gaps.empty else gaps["issue_date"].max()
    if fc.empty:
        return "".join(['<article class="card">', _heading(name, unit), _what(name), _status_note(entry),
                        '<p class="empty">no data yet. The first forecast appears after the next daily run.</p>',
                        _tracked(fc, gaps), "</article>"])
    latest = fc[fc["issue_date"] == fc["issue_date"].max()]
    issued = latest["issue_date"].iloc[0]
    out = [f'<article class="card" data-last-issue="{_e(issued.isoformat())}">', _heading(name, unit),
           _what(name), _status_note(entry), f'<p class="muted">issued {issued.isoformat()}</p>', _tracked(fc, gaps)]
    models = latest[latest["method"] == "model"]
    past = int((models["target_date"] < today).sum())
    if past:
        which = "targets in the past" if past == len(models) else f"{past} of {len(models)} targets in the past"
        out.append(f'<p class="note bad" data-past-note>last forecast issued {(today - issued).days} days ago; '
                   f'{which}</p>')
    else:
        out.append('<p class="note bad" data-past-note hidden></p>')
    if newest_gap is not None and newest_gap > issued:
        out.append(f'<p class="note bad">no forecast since {issued.isoformat()}; newer gap on '
                   f'{newest_gap.isoformat()}</p>')
    out.append(_fan_chart(latest, f"{name} forecast for the next days", unit))
    out.append(_legend("model (line, 80% band)"))
    unit_h = _e(unit) if unit else "units"
    out.append(f'<div class="scroll"><table><thead><tr><th>Day</th><th>Model, 80% interval ({unit_h})</th>'
               f'<th>Seasonal naive ({unit_h})</th><th>Persistence ({unit_h})</th></tr></thead><tbody>')
    piv = {m: latest[latest["method"] == m].set_index("horizon") for m in METHODS}
    for hz in sorted(piv["model"].index):
        m = piv["model"].loc[hz]

        def base(method: str) -> str:
            p = piv[method]
            return _num(p.loc[hz, "point"]) if hz in p.index else "n/a"

        is_past = m["target_date"] < today
        out.append(f'<tr data-up-row="{_e(name)}-h{hz}" data-target="{_e(m["target_date"].isoformat())}"'
                   f'{" class=past" if is_past else ""}>'
                   f'<td><span class="d">{m["target_date"].isoformat()}</span> <span class="muted">(+{hz}d){", past" if is_past else ""}</span></td>'
                   f'<td class="m"><strong>{_num(m["point"])}</strong> <span class="muted">{_num(m["lo"])} to {_num(m["hi"])}</span></td>'
                   f'<td>{base("seasonal_naive")}</td><td>{base("persistence")}</td></tr>')
    out.append("</tbody></table></div></article>")
    return "".join(out)


def _verdict(board: pd.DataFrame) -> str:
    """One headline sentence per series: at how many horizons the model beats the better baseline."""
    m = board[(board["method"] == "model") & board["skill"].notna() & (board["n_skill"] > 0)]
    if m.empty:
        return ""
    wins = int((m["skill"] > 0).sum())
    return (f'<p class="verdict">Model beats the better baseline at <em>{wins} of {len(m)}</em> horizons.</p>')


def _skill_cell(row: pd.Series) -> str:
    sk = row["skill"]
    kind = "" if pd.isna(sk) else (" pos" if sk > 0 else " neg" if sk < 0 else "")
    return f'<span class="skill{kind}">{"n/a" if pd.isna(sk) else f"{sk:.2f}"} (n={int(row["n_skill"])})</span>'


def _score_table(name: str, board: pd.DataFrame, fc: pd.DataFrame, oc: pd.DataFrame, trends: bool,
                 unit: str = "") -> str:
    model = board[board["method"] == "model"].sort_values("horizon")
    attr = "data-row" if trends else "data-bt-row"
    rows = []
    for r in model.itertuples():
        hz = int(r.horizon)
        extra = ""
        if trends:
            if r.n >= MIN_TREND:
                od = oc[["target_date", "value"]].drop_duplicates("target_date", keep="last")
                m = fc[(fc["method"] == "model") & (fc["horizon"] == hz)].merge(od, on="target_date")
                m = m[m["value"].notna()].sort_values("target_date")
                extra = _trend_chart(f"trend-{name}-h{hz}", (m["value"] - m["point"]).abs().reset_index(drop=True))
            else:
                extra = f"{int(r.n)} scored"
        cov = "n/a" if pd.isna(r.coverage) else f"{r.coverage * 100:.0f}%"
        rows.append(f'<tr {attr}="{_e(name)}-h{hz}"><td>+{hz}d</td><td>{int(r.n)}</td><td>{_num(r.mae)}</td>'
                    f'<td>{cov}</td><td>{_skill_cell(pd.Series(r._asdict()))}</td>'
                    + (f"<td>{extra}</td>" if trends else "") + "</tr>")
    mae_h = f"MAE ({_e(unit)})" if unit else "MAE"
    head = f"<th>Horizon</th><th>n</th><th>{mae_h}</th><th>Coverage (80%)</th><th>Skill (n)</th>"
    head += "<th>Trend</th>" if trends else ""
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


CSS = """
/* Layout: a dark instrument-style masthead with live status, a sticky section index, then
   two-column cards (one column on phones). Colour tokens first; dark values override them. */
:root{--bg:#eef2f1;--surface:#fff;--fg:#0f1b1f;--muted:#55656c;--line:#d5dedb;--soft:#e7eeec;
--accent:#008a7e;--band:rgba(0,138,126,.15);--seasonal_naive:#b8520a;--persistence:#4f69b0;
--mast-bg:#0f1b1f;--mast-fg:#eaf3f1;--mast-muted:#9db3b0;--live:#34d399;
--good:#0b6e3a;--good-bg:#e0f3e8;--bad:#9b2222;--bad-bg:#fbe9e7;--bad-line:#e9b3ac;
--sans:"Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",sans-serif;
--mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,"Liberation Mono",monospace}
@media (prefers-color-scheme:dark){:root{--bg:#0b1215;--surface:#131c20;--fg:#e6eeee;--muted:#94a6a8;--line:#26343a;
--soft:#1b272c;--accent:#10a597;--band:rgba(16,165,151,.22);--seasonal_naive:#d9772a;--persistence:#6f8bd6;
--mast-bg:#16232a;--mast-fg:#eaf3f1;--mast-muted:#8fa5a6;--good:#5fd49a;--good-bg:#12301f;
--bad:#ffb4ab;--bad-bg:#3a1a19;--bad-line:#7a3a36}}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 var(--sans);font-variant-numeric:tabular-nums;
-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-underline-offset:3px}
.wrap{max-width:1120px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));
padding-right:max(16px,env(safe-area-inset-right,0px))}
.mast{background:var(--mast-bg);color:var(--mast-fg);padding-block:36px 28px}
.mast h1{font-size:clamp(1.9rem,4.5vw,2.9rem);line-height:1.05;letter-spacing:-.025em;margin:0 0 10px;font-weight:700}
.lede{max-width:62ch;margin:0;color:var(--mast-muted);font-size:1.02rem}
.status{display:inline-flex;align-items:center;gap:8px;font:600 .8rem/1 var(--mono);letter-spacing:.04em;
text-transform:uppercase;color:var(--mast-fg);margin:0 0 18px}
.status::before{content:"";width:9px;height:9px;border-radius:50%;background:var(--live);box-shadow:0 0 0 4px rgba(52,211,153,.18)}
.status.stale::before{background:#f87171;box-shadow:0 0 0 4px rgba(248,113,113,.2)}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;margin:28px 0 0;background:rgba(255,255,255,.12);
border:1px solid rgba(255,255,255,.12);border-radius:10px;overflow:hidden}
.stat{background:var(--mast-bg);padding:14px 16px;min-width:0}
.stat b{display:block;font:700 1.6rem/1.1 var(--mono);letter-spacing:-.02em}
.stat span{display:block;margin-top:4px;font-size:.78rem;color:var(--mast-muted);text-transform:uppercase;letter-spacing:.06em}
nav.index{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
nav.index .wrap{display:flex;gap:4px;overflow-x:auto;padding-block:8px;scrollbar-width:none}
nav.index a{white-space:nowrap;text-decoration:none;color:var(--muted);font-size:.9rem;font-weight:600;padding:6px 12px;border-radius:999px}
nav.index a:hover,nav.index a:focus-visible{background:var(--soft);color:var(--fg);outline:none}
main{padding-block:8px 64px}
section{padding-top:40px}
h2{font-size:1.35rem;letter-spacing:-.01em;margin:0 0 6px}
.rule,.muted{color:var(--muted)}
.rule{max-width:78ch;margin:0 0 18px;font-size:.95rem}
.muted{margin:2px 0 8px;font-size:.88rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr));gap:16px;align-items:start}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px;min-width:0}
h3{font:600 .95rem/1.3 var(--mono);margin:0 0 2px;overflow-wrap:anywhere;letter-spacing:-.01em}
.unit{color:var(--muted);font-weight:400}
.what{margin:0 0 10px;color:var(--muted);font-size:.9rem}
.tracked{font:.78rem var(--mono);letter-spacing:.02em}
.banner,.note.bad{background:var(--bad-bg);color:var(--bad);border:1px solid var(--bad-line);border-radius:10px;
padding:10px 14px;margin:14px 0;overflow-wrap:anywhere}
.note.bad{padding:7px 11px;margin:8px 0;font-size:.9rem;border-radius:8px}
.banner{margin:0;border-radius:0;border-width:0 0 1px}
.verdict{margin:0 0 6px;font-weight:600}
.verdict em{font-style:normal;font-family:var(--mono)}
.empty{border:1px dashed var(--line);border-radius:10px;padding:14px;color:var(--muted);margin:8px 0;font-size:.92rem}
.scroll{overflow-x:auto;margin:6px -4px 0;padding:0 4px}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:right;padding:8px 8px;border-bottom:1px solid var(--soft);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font:600 .68rem var(--mono);text-transform:uppercase;letter-spacing:.04em;color:var(--muted);border-bottom:1px solid var(--line);white-space:normal;vertical-align:bottom}
tbody tr:last-child td{border-bottom:0}
td.m strong{font-family:var(--mono);color:var(--accent)}
tr.past td{color:var(--muted)}
.skill{display:inline-block;font:600 .8rem var(--mono);padding:2px 8px;border-radius:999px;background:var(--soft);color:var(--muted)}
.skill.pos{background:var(--good-bg);color:var(--good)}.skill.pos::before{content:"\\25B2  "}
.skill.neg{background:var(--bad-bg);color:var(--bad)}.skill.neg::before{content:"\\25BC  "}
svg.chart{display:block;width:100%;height:auto;margin:8px 0 4px}
svg.trend{width:120px;height:30px;vertical-align:middle}
.grid{stroke:var(--line);stroke-width:1;stroke-dasharray:2 4}.tick{fill:var(--muted);font:20px var(--mono)}
.band{fill:var(--band)}.line{fill:none;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}
.line.model{stroke:var(--accent);stroke-width:3}.line.seasonal_naive{stroke:var(--seasonal_naive);stroke-dasharray:6 4}
.line.persistence{stroke:var(--persistence);stroke-dasharray:1 5}
.dot{fill:var(--accent);stroke:var(--surface);stroke-width:2.5}
.bar{rx:3px}.bar.model{fill:var(--accent)}.bar.seasonal_naive{fill:var(--seasonal_naive)}.bar.persistence{fill:var(--persistence)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.82rem;color:var(--muted);margin:2px 0 10px}
.key::before{content:"";display:inline-block;width:16px;height:0;border-top:3px solid;margin-right:6px;vertical-align:middle}
.key.model::before{border-color:var(--accent)}.key.seasonal_naive::before{border-color:var(--seasonal_naive);border-top-style:dashed}
.key.persistence::before{border-color:var(--persistence);border-top-style:dotted}
td.m{white-space:normal}td.m .muted{display:block;white-space:nowrap;margin:0;font-size:.8em}
.about ul{padding-left:1.2em;margin:6px 0 14px}.about li{margin:6px 0}
footer{color:var(--muted);font-size:.85rem;padding-bottom:40px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media (max-width:640px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.mast{padding-block:24px 20px}
.card{padding:14px;border-radius:12px}section{padding-top:32px}th,td{padding:7px 4px}table{font-size:.84rem}
th{white-space:normal;vertical-align:bottom}td:first-child{white-space:normal}.d{white-space:nowrap}svg.trend{width:48px}}
"""


# Re-checks staleness with the viewer's clock. Uses only textContent, classList and hidden;
# never innerHTML. The page data reaches it only through data attributes.
SCRIPT = """
(function () {
  "use strict";
  var HOUR = 3600000, DAY = 86400000, STALE_AFTER = 36 * HOUR;
  var now = Date.now();
  var today = new Date(now).toISOString().slice(0, 10);
  var banner = document.getElementById("stale-banner");
  if (banner) {
    var last = Date.parse(banner.getAttribute("data-last-run") || "");
    if (Number.isFinite(last) && now - last > STALE_AFTER) {
      var strong = document.createElement("strong");
      strong.textContent = "STALE";
      banner.textContent = "";
      banner.appendChild(strong);
      banner.appendChild(document.createTextNode(" the last run was " + Math.floor((now - last) / HOUR) +
        " hours ago; scores below may be out of date."));
      banner.hidden = false;
      var pill = document.getElementById("live-status");
      if (pill) {
        pill.classList.add("stale");
        pill.firstChild.textContent = "Stale ";
      }
    }
  }
  var cards = document.querySelectorAll("[data-last-issue]");
  for (var i = 0; i < cards.length; i++) {
    var card = cards[i], issued = card.getAttribute("data-last-issue") || "";
    var rows = card.querySelectorAll("tr[data-target]"), past = 0;
    for (var j = 0; j < rows.length; j++) {
      var row = rows[j];
      if ((row.getAttribute("data-target") || "") < today) {
        past++;
        if (!row.classList.contains("past")) {
          row.classList.add("past");
          var label = row.querySelector("td .muted");
          if (label) { label.textContent = label.textContent + ", past"; }
        }
      }
    }
    var note = card.querySelector("[data-past-note]");
    var issuedMs = Date.parse(issued + "T00:00:00Z");
    if (past && note && Number.isFinite(issuedMs)) {
      var days = Math.round((Date.parse(today + "T00:00:00Z") - issuedMs) / DAY);
      var which = past === rows.length ? "targets in the past" : past + " of " + rows.length + " targets in the past";
      note.textContent = "last forecast issued " + days + " days ago; " + which;
      note.hidden = false;
    }
  }
})();
"""


def _gap_line(name: str, root: Path) -> str:
    gaps = store.read_gaps(root, name)
    if gaps.empty:
        return ""
    last = gaps.sort_values("issue_date").iloc[-1]
    return (f'<p class="muted">{len(gaps)} gap day(s); latest {last["issue_date"].isoformat()}: '
            f'{_e(last["reason"])}</p>')


def _definitions() -> dict[str, str]:
    """One line per series name: what is measured, unit, source, how a local day is formed."""
    m = config.METRO
    tz = m["tz"]
    return {
        "weather_tmax": (f"Daily maximum air temperature at 2 m, in degC, from the Open-Meteo weather API. "
                         f"The day is the local calendar day in {tz}, as Open-Meteo computes it for that time zone."),
        "air_quality_aqi": ("Daily mean US AQI from the Open-Meteo air-quality API. This is a modelled estimate "
                            "(Open-Meteo / Copernicus CAMS), not a sensor reading. A local day "
                            f"({tz}) is the mean of its hourly values and is left empty if any hour is missing."),
        "electricity_peak_mw": (f"Daily peak of hourly electricity demand, in MW, for the EIA-930 balancing authority "
                                f"{m['eia_respondent']} (the whole balancing area, not only the metro), from the EIA "
                                f"API. A local day ({tz}) is its highest hourly value and is left empty if any hour "
                                "is missing."),
        "river_discharge_cfs": (f"Daily mean river discharge, in ft3/s, at USGS gauge {m['usgs_site']} (parameter "
                                f"{m['usgs_parameter']}), from USGS instantaneous values (15-minute readings). "
                                "Readings are averaged into hourly means; a local day "
                                f"({tz}) is the mean of its hourly means and is left empty if any hour is missing."),
    }


SOURCES = (
    ("Open-Meteo", "https://open-meteo.com/", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
    ("USGS Water Data", "https://waterdata.usgs.gov/", "public domain",
     "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits"),
    ("U.S. Energy Information Administration (EIA)", "https://www.eia.gov/opendata/", "public data",
     "https://www.eia.gov/about/copyrights_reuse.php"),
)
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def _about(series_names: list[str], repository: str | None) -> str:
    defs = _definitions()
    items = "".join(f"<li><strong>{_e(n)}</strong> ({_e(_unit(n) or 'no unit')}): {_e(defs[n])}</li>"
                    for n in series_names if n in defs)
    sources = "".join(f'<li><a href="{_e(url)}">{_e(name)}</a>, <a href="{_e(lic_url)}">{_e(lic)}</a></li>'
                      for name, url, lic, lic_url in SOURCES)
    repo = ""
    if repository and _REPO.fullmatch(repository):
        url = f"https://github.com/{repository}"
        repo = f'<p>Code and the full record: <a href="{_e(url)}">{_e(url)}</a></p>'
    return (f'<h2 id="about">About this data</h2><article class="card about">'
            f'<p>Metro: <strong>{_e(config.METRO["name"])}</strong>.</p>'
            f"<ul>{items}</ul>"
            f"<p>Sources and licences:</p><ul>{sources}</ul>{repo}"
            "<p>The timestamp of record for each forecast is the time of the git commit that added it.</p>"
            "</article>")


def build_site(root: Path, out_dir: Path, now: datetime, series_names: list[str]) -> Path:
    root, out_dir = Path(root), Path(out_dir)
    now = _utc(now)
    status, problem = _read_status(root)
    entries = _entries(status)
    today = now.date()

    last_run_txt = "never"
    status_class, status_word = " stale", "Stale"
    if status is None:
        banner = ('<div id="stale-banner" class="banner" role="alert" data-last-run="">'
                  f'<strong>STALE</strong> no run recorded yet (status.json is {_e(problem)}).</div>')
    else:
        last = _utc(datetime.fromisoformat(status["last_run"]))
        last_run_txt = last.strftime("%Y-%m-%d %H:%M UTC")
        attr = f'id="stale-banner" class="banner" role="alert" data-last-run="{_e(last.isoformat())}"'
        if now - last > STALE_AFTER:
            hours = int((now - last).total_seconds() // 3600)
            banner = (f'<div {attr}><strong>STALE</strong> the last run was {hours} hours ago; '
                      'scores below may be out of date.</div>')
        else:  # hidden, and filled in by the script once the viewer's clock says it is stale
            banner = f"<div {attr} hidden></div>"
            status_class, status_word = "", "Live"

    data = {}
    for name in series_names:
        data[name] = (store.read_forecasts(root, name), store.read_outcomes(root, name))
    boards = {n: scoring.scoreboard(n, fc, oc) for n, (fc, oc) in data.items()}

    units = {n: _unit(n) for n in series_names}

    upcoming = "".join(_upcoming(n, data[n][0], entries.get(n), units[n], today, store.read_gaps(root, n))
                       for n in series_names)

    score_cards = []
    for n in series_names:
        fc, oc = data[n]
        card = ['<article class="card">', _heading(n, units[n]), _what(n), _status_note(entries.get(n))]
        if boards[n].empty:
            card.append('<p class="empty">no data yet. Scores start once the first outcomes arrive '
                        '(a target is scored two days after it ends).</p>')
        else:
            card.append(_score_table(n, boards[n], fc, oc, trends=True, unit=units[n]))
            card.append(_gap_line(n, root))
        card.append("</article>")
        score_cards.append("".join(card))

    compare = []
    for n in series_names:
        compare.append('<article class="card">' + _heading(n, units[n]) + _what(n))
        if boards[n].empty:
            compare.append('<p class="empty">no data yet. The comparison appears with the first scored forecasts.</p>')
        else:
            compare.append(_verdict(boards[n]))
            bars = _mae_bars(boards[n], f"{n}: mean absolute error by horizon, model vs baselines", units[n])
            if bars.startswith("<svg"):
                compare.append(bars)
                compare.append(_legend("model"))
                compare.append('<p class="muted">Mean absolute error per horizon, lower is better. Skill is '
                               'shown in the scoreboard above.</p>')
            else:
                compare.append('<p class="empty">no scored forecasts yet. The bars appear with the first outcomes.</p>')
        compare.append("</article>")

    backtest = []
    for n in series_names:
        try:
            bb = _backtest_board(root, n)
        except Exception:  # unusable file: say so, never break the deploy
            backtest.append('<article class="card">' + _heading(n, units[n]) + '<p class="note bad">backtest file '
                            'is unreadable or lacks required columns (origin, method, target_date, horizon, '
                            'point, lo, hi, actual)</p></article>')
            continue
        if bb is not None and not bb.empty:
            backtest.append('<article class="card">' + _heading(n, units[n])
                            + _score_table(n, bb, pd.DataFrame(), pd.DataFrame(), trends=False, unit=units[n])
                            + "</article>")
    saved = sum(int((data[n][0]["method"] == "model").sum()) for n in series_names if not data[n][0].empty)
    scored = sum(int(boards[n].loc[boards[n]["method"] == "model", "n"].sum()) for n in series_names
                 if not boards[n].empty)
    days = max((int(data[n][0]["issue_date"].nunique()) for n in series_names if not data[n][0].empty), default=0)
    stats = ('<div class="stats">'
             + "".join(f'<div class="stat"><b>{v:,}</b><span>{label}</span></div>'
                       for v, label in ((len(series_names), "series"), (days, "days tracked"),
                                        (saved, "forecasts saved"), (scored, "forecasts scored")))
             + "</div>")
    nav_backtest = '<a href="#backtest">Backtest</a>' if backtest else ""
    backtest_html = ""
    if backtest:
        backtest_html = (f'<section id="backtest"><h2>{BACKTEST_TITLE}</h2>'
                         '<p class="rule">Walk-forward replay on past data. Kept apart from the live numbers above. '
                         'Each replayed forecast is issued the day after its origin; horizon counted from the issue '
                         'date, as in the live record; origin is the last observed day.</p>'
                         f'<div class="cards">{"".join(backtest)}</div></section>')

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Forecast tracker</title><style>{CSS}</style></head>
<body>
<header class="mast"><div class="wrap">
<p id="live-status" class="status{status_class}">{status_word} <span>&middot; last run {_e(last_run_txt)}</span></p>
<h1>Forecast tracker</h1>
<p class="lede">Forecasts for {_e(config.METRO["name"])} are saved before the outcome is known, never edited, and
scored against two naive baselines. A model that loses to them is shown losing.</p>
{stats}
</div></header>
{banner}
<nav class="index" aria-label="Sections"><div class="wrap">
<a href="#forecasts">Forecasts</a><a href="#scoreboard">Scores</a><a href="#baseline">Vs baseline</a>{nav_backtest}<a href="#about">About</a>
</div></nav>
<main class="wrap">
<section id="forecasts"><h2>Upcoming forecasts</h2>
<p class="rule">Every forecast is saved before its outcome is known and never edited. CI fails if a past file changes.</p>
<div class="cards">{upcoming}</div></section>
<section id="scoreboard"><h2>Scoreboard per horizon</h2>
<p class="rule">n is the number of scored forecasts. Skill compares the model with the better baseline on the days all three were scored (n shown with it); n/a when undefined.</p>
<div class="cards">{"".join(score_cards)}</div></section>
<section id="baseline"><h2>Model vs baseline</h2><div class="cards">{"".join(compare)}</div></section>
{backtest_html}
<section>{_about(series_names, os.environ.get("GITHUB_REPOSITORY"))}</section>
</main>
<script>{SCRIPT}</script>
</body></html>
"""
    page = page.replace("<th>", '<th scope="col">')
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(page, encoding="utf-8")
    return path
