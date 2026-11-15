"""
==============================================================================
 report.py  —  turn the analysis Results into files you can read and share
==============================================================================

Files written into the run folder:
  report.html     the main result: one page with a verdict tile per experiment,
                  a list of every problem found, then a section per experiment
                  with its findings, charts and tables. Open it in a browser.
                  Follows the browser's light/dark setting.
  summary.md      the same verdicts and findings as Markdown, plus the
                  "Results log" table in the format of clamshell_validation.md
                  section 13, ready to paste into your notes.
  results_log.csv the results-log rows, for a spreadsheet.
  results.json    everything (verdicts, findings, tables), for scripts.

LIBRARIES USED
--------------
- html.escape: makes text safe to put inside HTML (turns "<" into "&lt;").
- csv: writes comma-separated files with correct quoting.
- json: writes structured data.
==============================================================================
"""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path

from .analysis import FAIL, PASS, WARN
from .palette import VERDICT_ICON

LOG_COLUMNS = ["exp", "condition", "gain", "rate", "ch", "offset_uV", "rms_uV", "pp_uV", "pp_rms", "notes"]
LOG_HEADERS = ["Exp", "Condition", "Gain", "Mode/Rate", "Ch", "Offset (µV)", "Noise (µVrms)", "Noise (µVpp)",
               "pp/rms", "Notes"]                       # same headings as section 13 of the plan


def _e(text) -> str:
    """Escape any value for HTML."""
    return html.escape(str(text))


def _pill(verdict: str) -> str:
    """A verdict badge: icon + word, coloured by status (never colour alone)."""
    v = str(verdict)
    return f'<span class="pill {v.lower()}">{VERDICT_ICON.get(v, "")} {_e(v)}</span>'


def _num(v, digits=4):
    """Format numbers for the results log."""
    if v is None or v == "":
        return ""
    try:
        return f"{float(v):.{digits}g}"
    except (TypeError, ValueError):
        return str(v)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
CSS = """
:root { color-scheme: light;
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --line:#e1e0d9;
  --good:#006300; --good-bg:#e3f3e3; --warn:#7a5200; --warn-bg:#fdf1d3; --bad:#b3261e; --bad-bg:#fbe4e2;
  --info:#52514e; --info-bg:#efeeea; --accent:#2a78d6; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#898781; --line:#2c2c2a;
  --good:#5fd35f; --good-bg:#12301a; --warn:#fab219; --warn-bg:#352a0e; --bad:#f08a8a; --bad-bg:#3a1716;
  --info:#c3c2b7; --info-bg:#262624; --accent:#5598e7; } }
:root[data-theme="dark"] { color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#898781; --line:#2c2c2a;
  --good:#5fd35f; --good-bg:#12301a; --warn:#fab219; --warn-bg:#352a0e; --bad:#f08a8a; --bad-bg:#3a1716;
  --info:#c3c2b7; --info-bg:#262624; --accent:#5598e7; }
* { box-sizing: border-box; }
body { margin:0; background:var(--page); color:var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1080px; margin: 0 auto; padding: 32px 16px 80px; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 20px; margin: 0; }
h3 { font-size: 15px; margin: 22px 0 8px; color: var(--ink2); }
.meta { color: var(--ink2); font-size: 13px; }
a { color: var(--accent); }
.tiles { display:grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; margin: 22px 0; }
.tile { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:12px 14px;
  text-decoration:none; color:inherit; display:block; }
.tile:hover { border-color: var(--muted); }
.tile .id { font-weight:700; font-size: 18px; margin-right: 6px; }
.tile .name { font-weight:600; }
.tile .head { color:var(--ink2); font-size: 13px; margin-top: 6px; }
.pill { display:inline-block; font-size:12px; font-weight:700; padding:1px 8px; border-radius:999px;
  white-space:nowrap; }
.pill.pass { color:var(--good); background:var(--good-bg); }
.pill.warn { color:var(--warn); background:var(--warn-bg); }
.pill.fail { color:var(--bad); background:var(--bad-bg); }
.pill.info, .pill.skip { color:var(--info); background:var(--info-bg); }
section.exp { background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:20px;
  margin: 18px 0; }
.exp-head { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.goal { margin: 10px 0 2px; } .method { color:var(--ink2); font-size: 13px; margin: 2px 0 0; }
ul.findings { list-style:none; padding:0; margin: 14px 0 0; }
ul.findings li { display:flex; gap:10px; align-items:baseline; padding: 4px 0; border-top:1px solid var(--line); }
ul.findings li:first-child { border-top: 0; }
figure { margin: 18px 0 0; } figure img { width:100%; height:auto; border-radius:8px; border:1px solid var(--line); }
figcaption { color:var(--ink2); font-size:13px; margin-top: 4px; }
.tablewrap { overflow-x:auto; margin-top: 6px; border:1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width:100%; font-size: 13px; font-variant-numeric: tabular-nums; }
th, td { padding: 5px 9px; text-align:left; border-bottom:1px solid var(--line); white-space:nowrap; }
th { color:var(--ink2); font-weight:600; background:var(--page); position: sticky; top: 0; }
td.wrap { white-space: normal; min-width: 260px; }
.note { color:var(--muted); font-size: 12px; margin: 4px 0 0; }
details { margin-top: 10px; } summary { cursor:pointer; color:var(--ink2); }
.issues li { margin: 4px 0; }
"""


def _table_html(t) -> str:
    """One Table -> HTML. Long text columns wrap; verdict cells become pills; long tables start folded."""
    head = "".join(f"<th>{_e(c)}</th>" for c in t.columns)                    # header row cells
    body = []                                                                 # one <tr> string per row
    for row in t.rows:
        cells = []                                                            # <td> strings of this row
        for j, v in enumerate(row):                                           # j = column index
            if t.verdict_col is not None and j == t.verdict_col:              # the verdict column
                cells.append(f"<td>{_pill(v)}</td>")                          # draw as a badge
            else:
                cls = ' class="wrap"' if isinstance(v, str) and len(v) > 40 else ""   # long text may wrap
                cells.append(f"<td{cls}>{_e(v)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    inner = (f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody>'
             f'</table></div>' + (f'<p class="note">{_e(t.note)}</p>' if t.note else ""))   # table + note
    if len(t.rows) > 24:                                                      # long table: collapsible
        return f"<details><summary>{_e(t.title)} ({len(t.rows)} rows)</summary>{inner}</details>"
    return f"<h3>{_e(t.title)}</h3>{inner}"                                   # short table: always visible


def _figure_html(fig) -> str:
    """A chart as <picture>: the browser shows the dark PNG in dark mode, the light PNG otherwise."""
    return (f'<figure><picture><source srcset="{_e(fig["dark"])}" media="(prefers-color-scheme: dark)">'
            f'<img src="{_e(fig["light"])}" alt="{_e(fig["title"])}" loading="lazy"></picture>'
            f'<figcaption><b>{_e(fig["title"])}.</b> {_e(fig.get("caption", ""))}</figcaption></figure>')


def write_html(path: Path, results: list, meta: dict):
    """
    Build report.html: header, one tile per experiment, "Things to look at"
    (every WARN/FAIL finding, FAIL first), a section per experiment, and the
    run details. The page is a single file; the charts are PNGs next to it
    in figures/.
    """
    tiles, issues, sections = [], [], []                                      # HTML pieces
    for r in results:                                                         # each experiment
        tiles.append(f'<a class="tile" href="#exp-{r.id}"><div><span class="id">{_e(r.id)}</span>'
                     f'<span class="name">{_e(r.name)}</span></div><div style="margin-top:6px">{_pill(r.verdict)}'
                     f'</div><div class="head">{_e(r.headline or "")}</div></a>')   # tile links to its section
        for v, text in r.findings:                                            # collect problems
            if v in (FAIL, WARN):
                issues.append((0 if v == FAIL else 1, r.id, v, text))         # 0 sorts before 1 -> FAIL first
        parts = [f'<div class="exp-head"><h2>{_e(r.id)} · {_e(r.name)}</h2>{_pill(r.verdict)}'
                 f'<span class="meta">clamshell_validation.md §{_e(r.section)}</span></div>',
                 f'<p class="goal">{_e(r.goal)}</p><p class="method">{_e(r.method)}</p>']   # heading, goal, method
        if r.findings:                                                        # bullet list of findings
            parts.append('<ul class="findings">' + "".join(f"<li>{_pill(v)}<span>{_e(t)}</span></li>"
                                                           for v, t in r.findings) + "</ul>")
        parts += [_figure_html(f) for f in r.figures]                         # charts
        parts += [_table_html(t) for t in r.tables]                           # tables
        sections.append(f'<section class="exp" id="exp-{r.id}">{"".join(parts)}</section>')
    issues.sort()                                                             # FAIL first, then by experiment
    if issues:
        issues_html = "<ul class='issues'>" + "".join(
            f'<li>{_pill(v)} <a href="#exp-{i}">{_e(i)}</a> — {_e(t)}</li>' for _, i, v, t in issues) + "</ul>"
    else:
        issues_html = f"<p>{_pill(PASS)} Nothing to look at: no warnings or failures.</p>"
    meta_rows = "".join(f"<tr><th>{_e(k)}</th><td class='wrap'>{_e(v)}</td></tr>" for k, v in meta.items())
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clamshell validation report</title><style>{CSS}</style></head>
<body><main>
<h1>ADS1298 clamshell validation</h1>
<div class="meta">{_e(meta.get("Run", ""))} · {_e(meta.get("Source", ""))} · {_e(meta.get("Captures", ""))} captures
 · generated {datetime.now():%Y-%m-%d %H:%M}</div>
<div class="tiles">{"".join(tiles)}</div>
<section class="exp"><h2>Things to look at</h2>{issues_html}</section>
{"".join(sections)}
<section class="exp"><h2>Run details</h2><div class="tablewrap"><table>{meta_rows}</table></div></section>
</main></body></html>"""                                                      # f-string with the pieces inserted
    path.write_text(doc, encoding="utf-8")                                    # save


# ---------------------------------------------------------------------------
# Markdown, CSV, JSON
# ---------------------------------------------------------------------------
def write_markdown(path: Path, results: list, meta: dict):
    """summary.md: verdict table, findings per experiment, and the section-13 results log."""
    out = ["# ADS1298 clamshell validation — summary", "",
           f"Run: {meta.get('Run', '')} · {meta.get('Source', '')} · {meta.get('Captures', '')} captures", "",
           "| Exp | Experiment | Verdict | Headline |", "|---|---|---|---|"]          # lines of the file
    for r in results:                                                         # verdict table
        out.append(f"| {r.id} | {r.name} | {VERDICT_ICON.get(r.verdict, '')} {r.verdict} | {r.headline} |")
    for r in results:                                                         # findings per experiment
        out += ["", f"## {r.id} · {r.name} — {r.verdict}", "", r.goal, ""]
        out += [f"- **{v}** {t}" for v, t in r.findings]
    out += ["", "## Results log (clamshell_validation.md §13)", "",
            "| " + " | ".join(LOG_HEADERS) + " |", "|" + "---|" * len(LOG_HEADERS)]   # results-log header
    numeric = ("offset_uV", "rms_uV", "pp_uV", "pp_rms")                       # columns formatted as numbers
    for r in results:
        for row in r.log_rows:
            out.append("| " + " | ".join(_num(row.get(c)) if c in numeric else str(row.get(c, ""))
                                         for c in LOG_COLUMNS) + " |")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")                  # join lines and save


def write_csv(path: Path, results: list):
    """results_log.csv: one row per channel measurement (opens in Excel / Numbers / LibreOffice)."""
    with path.open("w", newline="", encoding="utf-8") as fh:                 # newline="" is required by csv
        w = csv.writer(fh)                                                    # handles quoting and commas
        w.writerow(LOG_HEADERS)                                               # header
        for r in results:
            for row in r.log_rows:
                w.writerow([row.get(c, "") for c in LOG_COLUMNS])             # one measurement


def write_json(path: Path, results: list, meta: dict):
    """results.json: everything except the figures' pixels, for your own scripts."""
    data = {"meta": meta, "experiments": [{
        "id": r.id, "name": r.name, "verdict": r.verdict, "headline": r.headline,
        "findings": [{"verdict": v, "text": t} for v, t in r.findings],
        "tables": [{"title": t.title, "columns": t.columns, "rows": t.rows} for t in r.tables],
        "figures": r.figures} for r in results]}                              # plain dicts and lists
    path.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")


def write_all(run_dir: Path, results: list, meta: dict) -> Path:
    """Write every report file; return the path of report.html."""
    write_html(run_dir / "report.html", results, meta)
    write_markdown(run_dir / "summary.md", results, meta)
    write_csv(run_dir / "results_log.csv", results)
    write_json(run_dir / "results.json", results, meta)
    return run_dir / "report.html"
