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


def _upcoming(name: str, fc: pd.DataFrame, entry: dict | None, unit: str, today: date,
              newest_gap: date | None) -> str:
    if fc.empty:
        return "".join(['<article class="card">', _heading(name, unit), _status_note(entry),
                        '<p class="muted">no data yet</p></article>'])
    latest = fc[fc["issue_date"] == fc["issue_date"].max()]
    issued = latest["issue_date"].iloc[0]
    out = [f'<article class="card" data-last-issue="{_e(issued.isoformat())}">', _heading(name, unit),
           _status_note(entry), f'<p class="muted">issued {issued.isoformat()}</p>']
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


def _skill_cell(row: pd.Series) -> str:
    sk = row["skill"]
    return f'{"n/a" if pd.isna(sk) else f"{sk:.2f}"} (n={int(row["n_skill"])})'


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
.about li{margin:4px 0}.about a{color:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 16px}
.note.bad{color:var(--warn-fg);background:var(--warn-bg);border-radius:6px;padding:6px 10px;margin:6px 0;overflow-wrap:anywhere}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font-weight:600;color:var(--muted)}
svg.chart{display:block;width:100%;height:auto;max-width:600px;margin:6px 0}
svg.trend{width:120px;height:30px;vertical-align:middle}
.grid{stroke:var(--line);stroke-width:1}.tick{fill:var(--muted);font-size:21px}
.band{fill:var(--band)}.line{fill:none;stroke-width:2;stroke-linejoin:round}
.line.model{stroke:var(--accent)}.line.seasonal_naive{stroke:var(--seasonal_naive);stroke-dasharray:5 3}
.line.persistence{stroke:var(--persistence);stroke-dasharray:2 3}
.dot{fill:var(--accent)}.bar.model{fill:var(--accent)}.bar.seasonal_naive{fill:var(--seasonal_naive)}
.bar.persistence{fill:var(--persistence)}
tr.past td{color:var(--muted)}.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.85rem;color:var(--muted);margin:2px 0 10px}
.key::before{content:"";display:inline-block;width:14px;height:0;border-top:3px solid;margin-right:6px;vertical-align:middle}
.key.model::before{border-color:var(--accent)}.key.seasonal_naive::before{border-color:var(--seasonal_naive)}
.key.persistence::before{border-color:var(--persistence)}
td.m{white-space:normal}td.m .muted{display:block;white-space:nowrap;margin:0;font-size:.85em}
@media (max-width:480px){table{font-size:.85rem}th{white-space:normal;vertical-align:bottom}td.m{min-width:0}svg.trend{width:48px}th,td{padding:6px 3px}td:first-child{white-space:normal}.d{white-space:nowrap}td .muted{font-size:.8em}main{padding-top:16px}h1{font-size:1.35rem}.card{padding:10px}}
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

    data = {}
    for name in series_names:
        data[name] = (store.read_forecasts(root, name), store.read_outcomes(root, name))
    boards = {n: scoring.scoreboard(n, fc, oc) for n, (fc, oc) in data.items()}

    units = {n: _unit(n) for n in series_names}

    def newest_gap(n: str):
        g = store.read_gaps(root, n)
        return None if g.empty else g["issue_date"].max()

    upcoming = "".join(_upcoming(n, data[n][0], entries.get(n), units[n], today, newest_gap(n))
                       for n in series_names)

    score_cards = []
    for n in series_names:
        fc, oc = data[n]
        card = ['<article class="card">', _heading(n, units[n]), _status_note(entries.get(n))]
        if boards[n].empty:
            card.append('<p class="muted">no data yet</p>')
        else:
            card.append(_score_table(n, boards[n], fc, oc, trends=True, unit=units[n]))
            card.append(_gap_line(n, root))
        card.append("</article>")
        score_cards.append("".join(card))

    compare = []
    for n in series_names:
        compare.append('<article class="card">' + _heading(n, units[n]))
        if boards[n].empty:
            compare.append('<p class="muted">no data yet</p>')
        else:
            compare.append(_mae_bars(boards[n], f"{n}: mean absolute error by horizon, model vs baselines", units[n]))
            compare.append(_legend("model"))
            compare.append('<p class="muted">Mean absolute error per horizon, lower is better. Skill is '
                           'shown in the scoreboard above.</p>')
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
{_about(series_names, os.environ.get("GITHUB_REPOSITORY"))}
</main>
<script>{SCRIPT}</script>
</body></html>
"""
    page = page.replace("<th>", '<th scope="col">')
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(page, encoding="utf-8")
    return path
