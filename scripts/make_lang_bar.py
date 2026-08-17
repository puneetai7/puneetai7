"""Render lang-bar.svg — a stacked bar of language mix across the public repos.

Shares are computed from real bytes-per-language (the repo list's single
`language` field only names the top one), so the bar reflects what is actually
written rather than how repos happen to be counted.
"""

import json
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "data" / "profile.json"
OUT = ROOT / "lang-bar.svg"

WIDTH = 860
PAD = 24
BAR_H = 16
LINE = 22

# GitHub's own language colors; anything unlisted falls back to grey.
COLORS = {
    "Python": "#3572A5", "HTML": "#e34c26", "JavaScript": "#f1e05a",
    "CSS": "#563d7c", "TypeScript": "#3178c6", "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051", "Java": "#b07219", "C++": "#f34b7d", "Go": "#00ADD8",
    "Ruby": "#701516", "PHP": "#4F5D95", "Dockerfile": "#384d54",
    "Makefile": "#427819", "SCSS": "#c6538c", "Vue": "#41b883",
}
FALLBACK = "#8b949e"

MAX_SHOWN = 6
ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def escape(s):
    return "".join(ESCAPES.get(c, c) for c in str(s))


def fetch_bytes(handle):
    repos = requests.get(
        f"https://api.github.com/users/{handle}/repos?per_page=100", timeout=30).json()
    if not isinstance(repos, list):
        return Counter()

    totals = Counter()
    for r in repos:
        if r.get("fork"):
            continue
        try:
            langs = requests.get(r["languages_url"], timeout=20).json()
        except Exception:
            continue
        if isinstance(langs, dict):
            totals.update({k: int(v) for k, v in langs.items()})
    return totals


def build(totals):
    total = sum(totals.values())
    if not total:
        return None

    top = totals.most_common(MAX_SHOWN)
    other = total - sum(v for _, v in top)
    segments = [(n, v) for n, v in top]
    if other > 0:
        segments.append(("Other", other))

    inner = WIDTH - PAD * 2
    bar_y = PAD + 20
    x = PAD
    bars, legend = [], []

    # Legend wraps onto rows of three so long language names cannot collide.
    per_row = 3
    col_w = inner // per_row

    for i, (name, val) in enumerate(segments):
        share = val / total
        w = max(3, round(inner * share))
        if i == len(segments) - 1:          # absorb rounding into the last piece
            w = max(3, PAD + inner - x)
        color = COLORS.get(name, FALLBACK)

        # Each segment grows from zero width, one after the next.
        bars.append(
            f'<rect class="seg" x="{x}" y="{bar_y}" width="{w}" height="{BAR_H}" '
            f'fill="{color}" style="animation-delay:{round(i * 0.11, 3)}s">'
            f'<title>{escape(name)} — {share * 100:.1f}%</title></rect>'
        )

        row, col = divmod(i, per_row)
        lx = PAD + col * col_w
        ly = bar_y + BAR_H + 26 + row * LINE
        legend.append(
            f'<g class="lg" style="animation-delay:{round(0.5 + i * 0.07, 3)}s">'
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text class="lab" x="{lx + 17}" y="{ly}">{escape(name)} '
            f'<tspan class="pct">{share * 100:.1f}%</tspan></text></g>'
        )
        x += w

    rows = (len(segments) + per_row - 1) // per_row
    height = bar_y + BAR_H + 26 + rows * LINE + PAD - 10

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"
     viewBox="0 0 {WIDTH} {height}" role="img"
     aria-label="Language mix across public repositories">
  <style>
    text {{ font: 12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .hdr {{ font-size: 13px; fill: #39d353; }}
    .lab {{ fill: #c9d1d9; }}
    .pct {{ fill: #7d8590; }}
    /* Base state is the finished state; `both` holds the collapsed from-state
       during the delay, so non-animating renderers still show a full bar. */
    .seg {{ transform-box: fill-box; transform-origin: left center;
            animation: grow .7s cubic-bezier(.2,.8,.3,1) both; }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    .lg {{ animation: fade .4s ease-out both; }}
    @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .seg, .lg {{ animation: none; }}
    }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117" rx="10"/>
  <text class="hdr" x="{PAD}" y="{PAD + 8}">language mix · by bytes across public repos</text>
  <g>{"".join(bars)}</g>
  {"".join(legend)}
</svg>
'''


def main():
    handle = json.loads(CONF.read_text())["handle"]
    svg = build(fetch_bytes(handle))
    if not svg:
        print("no language data; leaving lang-bar.svg untouched")
        return
    OUT.write_text(svg)
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
