import json
import re
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from ftracker import site, store

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
FETCHED = datetime(2026, 11, 1, tzinfo=timezone.utc)
D0 = date(2026, 9, 1)


def _rows(issue, model_off=1.0, base_off=2.0):
    """Forecast rows for one issue date: target value would be 10 + day offset."""
    out = []
    for h in range(1, 8):
        t = issue + timedelta(days=h)
        truth = 10.0 + t.toordinal() % 5
        for method, off in (("model", model_off), ("seasonal_naive", base_off), ("persistence", base_off)):
            out.append({"method": method, "target_date": t, "horizon": h,
                        "point": truth + off, "lo": truth + off - 3, "hi": truth + off + 3})
    return pd.DataFrame(out)


def make_data(root, name="s1", issues=14, outcomes=True, base_off=2.0, perfect_baseline=False):
    for i in range(issues):
        issue = D0 + timedelta(days=i)
        rows = _rows(issue, base_off=0.0 if perfect_baseline else base_off)
        store.write_forecast(root, name, issue, rows, {})
    if outcomes:
        for t in range(1, issues + 8):
            td = D0 + timedelta(days=t)
            store.write_outcome(root, name, td, 10.0 + td.toordinal() % 5, FETCHED)


def write_status(root, last_run, series=None):
    root.mkdir(parents=True, exist_ok=True)
    (root / "status.json").write_text(json.dumps({"last_run": last_run.isoformat(), "series": series or {}}))


def _markup(html):
    """The server-rendered page without the inline script, whose source names the texts it may show."""
    return re.sub(r"<script>.*?</script>", "", html, flags=re.S)


def build(tmp_path, names=("s1",), now=NOW):
    root = tmp_path / "data"
    root.mkdir(exist_ok=True)
    return root, lambda: site.build_site(root, tmp_path / "out", now, list(names)).read_text(encoding="utf-8")


def test_page_shows_last_run_time(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    last = NOW - timedelta(hours=5)
    write_status(root, last)
    html = page()
    assert "2026-11-02 07:00 UTC" in html
    assert "STALE" not in _markup(html)


def test_stale_banner_after_36_hours(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW - timedelta(hours=37))
    assert "STALE" in _markup(page())
    (root / "status.json").unlink()
    write_status(root, NOW - timedelta(hours=35))
    assert "STALE" not in _markup(page())


def test_below_14_scored_shows_count_and_no_trend(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=13)
    write_status(root, NOW)
    html = page()
    assert "13 scored" in html
    assert 'id="trend-s1-h1"' not in html


def test_at_14_scored_shows_trend(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=14)
    write_status(root, NOW)
    html = page()
    assert 'id="trend-s1-h1"' in html
    assert 'id="trend-s1-h7"' in html


def test_skill_shows_na_when_baseline_error_is_zero(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=5, perfect_baseline=True)
    write_status(root, NOW)
    html = page()
    assert "n/a (n=5)" in html


def test_skill_is_shown_with_its_sample_count(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=5)
    write_status(root, NOW)
    html = page()
    assert "0.50 (n=5)" in html  # model mae 1, baseline mae 2


def test_scores_listed_for_each_horizon_1_to_7(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=14)
    write_status(root, NOW)
    html = page()
    for h in range(1, 8):
        assert f'data-row="s1-h{h}"' in html


def test_failed_series_is_flagged(tmp_path):
    root, page = build(tmp_path, names=("s1", "s2"))
    make_data(root, "s1", issues=3)
    write_status(root, NOW, {"s1": {"last_issue": "2026-09-03", "error": None},
                             "s2": {"last_issue": None, "error": "source <down> & out"}})
    html = page()
    assert "no forecast issued" in html
    assert "source &lt;down&gt; &amp; out" in html
    assert "<down>" not in html


def test_backtest_section_labelled_and_only_when_present(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=5)
    write_status(root, NOW)
    assert "Backtest (historical, not live)" not in page()
    bt = []
    for i in range(20):
        origin = date(2025, 1, 1) + timedelta(days=i)
        for m in ("model", "seasonal_naive", "persistence"):
            for h in range(1, 8):
                t = origin + timedelta(days=h)
                bt.append({"origin": origin.isoformat(), "method": m, "target_date": t.isoformat(),
                           "horizon": h, "point": 5.0, "lo": 4.0, "hi": 6.0, "actual": 5.5})
    (root / "backtest").mkdir()
    pd.DataFrame(bt).to_csv(root / "backtest" / "s1.csv", index=False)
    html = page()
    assert "Backtest (historical, not live)" in html
    live_part = html.split("Backtest (historical, not live)")[0]
    assert 'data-row="s1-h1"' in live_part
    assert 'data-bt-row="s1-h1"' in html.split("Backtest (historical, not live)")[1]
    assert 'data-bt-row' not in live_part


def test_site_builds_with_no_data_and_shows_stale_banner(tmp_path):
    root, page = build(tmp_path, names=("s1", "s2"))
    html = page()
    assert "STALE" in _markup(html)
    for name in ("s1", "s2"):
        card = html.split(f"<h3>{name}</h3>", 1)[1].split("</article>", 1)[0]
        assert "no data yet" in card
    assert "Backtest (historical, not live)" not in html


def test_forecasts_without_outcomes_do_not_crash(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=2, outcomes=False)
    write_status(root, NOW)
    html = page()
    assert "0 scored" in html
    assert "Upcoming" in html


def test_upcoming_lists_latest_forecast_with_interval_and_unit(tmp_path, monkeypatch):
    from ftracker import registry
    from ftracker.series import Series
    monkeypatch.setitem(registry.SERIES, "x", Series("s1", "degC", "UTC", lambda a, b: None))
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW)
    html = page()
    last_issue = D0 + timedelta(days=2)
    assert f"issued {last_issue.isoformat()}" in html
    assert "degC" in html
    assert html.count('data-up-row="s1-h') == 7


def test_page_is_self_contained_and_explains_immutability(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW)
    html = page()
    assert "<script src" not in html and "http://" not in html.replace("http://www.w3.org/2000/svg", "")
    assert "never edited" in html and "CI fails if a past file changes" in html
    assert html.index("Upcoming") < html.index("Scoreboard") < html.index("Model vs baseline")


def test_text_from_files_is_escaped(tmp_path):
    root, page = build(tmp_path, names=("a&b",))
    make_data(root, "a&b", issues=2)
    store.write_gap(root, "a&b", date(2026, 9, 20), "bad <b>reason</b>")
    write_status(root, NOW)
    html = page()
    assert "a&amp;b" in html
    assert "<b>reason" not in html and "bad &lt;b&gt;reason" in html


def test_all_scoreboards_concatenates_series(tmp_path):
    root = tmp_path / "data"
    make_data(root, "s1", issues=3)
    make_data(root, "s2", issues=3)
    df = site.all_scoreboards(root, ["s1", "s2"])
    assert set(df["series"]) == {"s1", "s2"}
    assert list(df.columns) == ["series", "method", "horizon", "n", "n_missing", "mae", "coverage", "skill", "n_skill"]
    assert site.all_scoreboards(root, ["nothing"]).empty


def test_stale_boundary_is_exactly_36_hours(tmp_path):
    root, page = build(tmp_path)
    write_status(root, NOW - timedelta(hours=36))
    assert "STALE" not in _markup(page())
    write_status(root, NOW - timedelta(hours=36, seconds=1))
    assert "STALE" in _markup(page())


def test_naive_last_run_is_treated_as_utc(tmp_path):
    root, page = build(tmp_path)
    (root / "status.json").write_text(json.dumps({"last_run": "2026-11-02T00:00:00", "series": {}}))
    html = page()
    assert "2026-11-02 00:00 UTC" in html and "STALE" not in _markup(html)
    (root / "status.json").write_text(json.dumps({"last_run": "2026-10-31T00:00:00", "series": {}}))
    assert "STALE" in _markup(page())


def test_corrupt_status_json_says_unreadable_and_is_stale(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    for bad in ("{not json", "[1, 2]", '"text"', json.dumps({"series": {}}), json.dumps({"last_run": 5})):
        (root / "status.json").write_text(bad)
        html = page()
        assert "STALE" in _markup(html) and "status.json is unreadable" in html


def test_status_with_malformed_series_does_not_crash(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    for series in ([], "oops", {"s1": "oops"}, {"s1": ["x"]}, {"s1": None}):
        (root / "status.json").write_text(json.dumps({"last_run": NOW.isoformat(), "series": series}))
        html = page()
        assert "STALE" not in _markup(html) and "no forecast issued" not in html


def test_old_forecast_is_flagged_not_hidden(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)  # last issue 2026-09-03, now is 2026-11-02
    store.write_gap(root, "s1", date(2026, 10, 1), "source down")
    write_status(root, NOW, {"s1": {"last_issue": "2026-09-03", "error": "boom"}})
    html = page()
    assert "last forecast issued 60 days ago; targets in the past" in html
    assert "newer gap on 2026-10-01" in html
    assert html.count('class=past') == 7
    assert html.count('data-up-row="s1-h') == 7
    assert "no forecast issued: boom" in html


def test_fresh_forecast_has_no_past_flag(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=1)
    write_status(root, NOW)
    # issue 2026-09-01 vs now 2026-11-02 is old; use a now right after the issue instead
    html = site.build_site(root, tmp_path / "o2", datetime(2026, 9, 2, 8, tzinfo=timezone.utc), ["s1"]).read_text(encoding="utf-8")
    assert "targets in the past" not in _markup(html)


def test_units_in_headings_headers_and_charts(tmp_path, monkeypatch):
    from ftracker import registry
    from ftracker.series import Series
    monkeypatch.setitem(registry.SERIES, "x", Series("s1", "degC", "UTC", lambda a, b: None))
    root, page = build(tmp_path)
    make_data(root, issues=5)
    write_status(root, NOW)
    html = page()
    assert html.count("<h3>s1 <span class=\"unit\">(degC)</span></h3>") == 3
    assert "MAE (degC)" in html
    assert "Seasonal naive (degC)" in html and "Persistence (degC)" in html
    assert ">MAE (degC)</text>" in html  # bar chart axis label
    assert '<text class="tick" x="2" y="18">degC</text>' in html  # fan chart axis label


def test_backtest_numbers_and_live_numbers_stay_separate(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=5)
    write_status(root, NOW)
    bt = [{"origin": (date(2025, 1, 1) + timedelta(days=i)).isoformat(), "method": m,
           "target_date": (date(2025, 1, 1) + timedelta(days=i + h)).isoformat(), "horizon": h,
           "point": 5.0, "lo": 4.0, "hi": 6.0, "actual": 5.5}
          for i in range(20) for m in ("model", "seasonal_naive", "persistence") for h in range(1, 8)]
    before = page()
    (root / "backtest").mkdir()
    pd.DataFrame(bt).to_csv(root / "backtest" / "s1.csv", index=False)
    after = page()
    head, tail = after.split("Backtest (historical, not live)")
    assert head.count("<td>5</td>") == before.count("<td>5</td>")
    row = tail.split('data-bt-row="s1-h1"')[1].split("</tr>")[0]
    assert "<td>0.50</td>" in row and "<td>100%</td>" in row
    live = head.split('data-row="s1-h1"')[1].split("</tr>")[0]
    assert "<td>5</td>" in live and "<td>1.00</td>" in live and "<td>0.50</td>" not in live


def test_backtest_with_missing_columns_does_not_crash(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW)
    (root / "backtest").mkdir()
    pd.DataFrame({"origin": ["2025-01-01"], "method": ["model"]}).to_csv(root / "backtest" / "s1.csv", index=False)
    html = page()
    assert "Backtest (historical, not live)" in html
    assert "unreadable or lacks required columns" in html
    (root / "backtest" / "s1.csv").write_bytes(b"")
    assert "unreadable or lacks required columns" in page()


def test_nan_forecast_values_never_reach_the_page(tmp_path):
    root, page = build(tmp_path)
    nan = float("nan")
    rows = _rows(D0)
    rows.loc[(rows.method == "model") & (rows.horizon == 3), ["point", "lo", "hi"]] = nan
    rows.loc[(rows.method == "persistence") & (rows.horizon == 2), "point"] = nan
    rows.loc[(rows.method == "model") & (rows.horizon == 5), ["lo", "hi"]] = nan
    store.write_forecast(root, "s1", D0, rows, {})
    write_status(root, NOW)
    html = page()
    assert "nan" not in html.lower().replace("seasonal naive", "")
    assert "n/a" in html


# ---------- client-side stale check (the page may stop being rebuilt) ----------

def _banner(html):
    m = re.search(r'<div id="stale-banner"[^>]*>', html)
    assert m, "banner container missing"
    return m.group(0)


def test_banner_container_is_hidden_when_fresh_and_carries_last_run(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW - timedelta(hours=5))
    tag = _banner(page())
    assert " hidden" in tag
    assert f'data-last-run="{(NOW - timedelta(hours=5)).isoformat()}"' in tag


def test_banner_container_is_visible_when_stale(tmp_path):
    root, page = build(tmp_path)
    write_status(root, NOW - timedelta(days=3))
    html = page()
    tag = _banner(html)
    assert "hidden" not in tag and 'data-last-run="2026-10-30T12:00:00+00:00"' in tag
    assert "the last run was 72 hours ago" in _markup(html)
    (root / "status.json").unlink()
    tag = _banner(page())
    assert "hidden" not in tag and 'data-last-run=""' in tag


def test_rows_and_cards_carry_dates_for_the_script(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW)
    html = page()
    last_issue = D0 + timedelta(days=2)
    assert f'data-last-issue="{last_issue.isoformat()}"' in html
    for h in range(1, 8):
        assert f'data-target="{(last_issue + timedelta(days=h)).isoformat()}"' in html
    assert _markup(html).count("data-past-note") == 1


def test_past_note_placeholder_is_hidden_when_nothing_is_past(tmp_path):
    root, _ = build(tmp_path)
    make_data(root, issues=1)
    write_status(root, NOW)
    html = site.build_site(root, tmp_path / "o2", datetime(2026, 9, 2, 8, tzinfo=timezone.utc), ["s1"]).read_text(
        encoding="utf-8")
    assert '<p class="note bad" data-past-note hidden></p>' in html


def test_inline_script_is_present_safe_and_self_contained(tmp_path):
    root, page = build(tmp_path, names=("a&b",))
    make_data(root, "a&b", issues=3)
    write_status(root, NOW)
    html = page()
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S)
    assert scripts == [site.SCRIPT]  # one inline script, the constant: no page data inside it
    assert "<script src" not in html and "innerHTML" not in site.SCRIPT and "eval(" not in site.SCRIPT
    assert "Date.now()" in site.SCRIPT and "36 * HOUR" in site.SCRIPT
    assert 'getElementById("stale-banner")' in site.SCRIPT and "data-last-run" in site.SCRIPT
    assert "data-target" in site.SCRIPT and "data-last-issue" in site.SCRIPT and "data-past-note" in site.SCRIPT
    assert not re.search(r"<link[^>]+href=[\"']?https?:", html)
    assert "@font-face" not in html and "fonts.googleapis" not in html and "url(" not in html
    assert "http://" not in html.replace("http://www.w3.org/2000/svg", "")
    assert not re.search(r"src=", html)  # no external resource of any kind; plain <a href> links are fine
    assert "a&amp;b" in html and "a&b" not in _markup(html)


# ---------- about this data ----------

def _about_html(tmp_path, monkeypatch, repo=None, names=("weather_tmax", "air_quality_aqi",
                                                         "electricity_peak_mw", "river_discharge_cfs")):
    if repo is None:
        monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    else:
        monkeypatch.setenv("GITHUB_REPOSITORY", repo)
    root, page = build(tmp_path, names=names)
    write_status(root, NOW)
    html = page()
    assert "About this data" in html
    return html.split('<h2 id="about">About this data</h2>', 1)[1].split("</main>")[0]


def test_about_names_the_metro_from_config(tmp_path, monkeypatch):
    from ftracker import config
    monkeypatch.setitem(config.METRO, "name", "Test <City> & Co")
    about = _about_html(tmp_path, monkeypatch)
    assert "Test &lt;City&gt; &amp; Co" in about and "<City>" not in about


def test_about_defines_every_series(tmp_path, monkeypatch):
    about = _about_html(tmp_path, monkeypatch)
    for name, words in {"weather_tmax": ("maximum", "degC", "Open-Meteo", "local calendar day"),
                        "air_quality_aqi": ("US AQI", "modelled estimate", "Copernicus CAMS", "not a sensor reading"),
                        "electricity_peak_mw": ("peak", "MW", "EIA", "highest hourly value"),
                        "river_discharge_cfs": ("discharge", "ft3/s", "USGS", "mean of its hourly means")}.items():
        item = about.split(f"<strong>{name}</strong>", 1)[1].split("</li>", 1)[0]
        for w in words:
            assert w in item, (name, w)


def test_about_credits_sources_with_licence_links(tmp_path, monkeypatch):
    about = _about_html(tmp_path, monkeypatch)
    assert '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>' in about
    assert ">public domain</a>" in about and "usgs.gov" in about
    assert ">public data</a>" in about and "eia.gov" in about
    assert "Open-Meteo" in about


def test_about_links_repository_only_when_set(tmp_path, monkeypatch):
    assert "github.com" not in _about_html(tmp_path, monkeypatch)
    (tmp_path / "b").mkdir()
    (tmp_path / "c").mkdir()
    about = _about_html(tmp_path / "b", monkeypatch, repo="ahmad/forecast-tracker")
    assert '<a href="https://github.com/ahmad/forecast-tracker">' in about
    bad = _about_html(tmp_path / "c", monkeypatch, repo='x/y"><script>alert(1)</script>')
    assert "github.com" not in bad and "<script>alert" not in bad


def test_about_says_commit_time_is_the_timestamp_of_record(tmp_path, monkeypatch):
    about = _about_html(tmp_path, monkeypatch)
    assert "timestamp of record for each forecast is the time of the git commit" in about


def test_about_skips_unknown_series_and_escapes(tmp_path, monkeypatch):
    about = _about_html(tmp_path, monkeypatch, names=("a&b",))
    assert "a&b" not in about and "<li><strong>" not in about.split("Sources")[0]


# ---------- cold start ----------

def test_days_tracked_and_gap_days_per_series(tmp_path):
    root, page = build(tmp_path, names=("s1", "s2"))
    make_data(root, "s1", issues=4)
    store.write_gap(root, "s1", date(2026, 9, 10), "source down")
    store.write_gap(root, "s1", date(2026, 9, 11), "source down")
    store.write_gap(root, "s2", date(2026, 9, 10), "no key")
    write_status(root, NOW)
    html = page()
    up = html.split("<h2>Upcoming forecasts</h2>", 1)[1].split("<h2>", 1)[0]
    s1 = up.split("<h3>s1</h3>", 1)[1].split("</article>", 1)[0]
    s2 = up.split("<h3>s2</h3>", 1)[1].split("</article>", 1)[0]
    assert "days tracked: 4; gap days: 2" in s1
    assert "days tracked: 0; gap days: 1" in s2 and "no data yet" in s2


def test_backtest_text_explains_horizon_and_origin(tmp_path):
    root, page = build(tmp_path)
    make_data(root, issues=3)
    write_status(root, NOW)
    bt = [{"origin": "2025-01-01", "method": m, "target_date": (date(2025, 1, 2) + timedelta(days=h)).isoformat(),
           "horizon": h, "point": 5.0, "lo": 4.0, "hi": 6.0, "actual": 5.5}
          for m in ("model", "seasonal_naive", "persistence") for h in range(1, 8)]
    (root / "backtest").mkdir()
    pd.DataFrame(bt).to_csv(root / "backtest" / "s1.csv", index=False)
    tail = page().split("Backtest (historical, not live)")[1]
    assert "horizon counted from the issue date, as in the live record; origin is the last observed day" in tail
