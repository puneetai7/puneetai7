"""Render info-card.svg — a neofetch-style panel beside the ASCII portrait.

Prose lives in data/profile.json (edit it freely); the counts and language mix
are read live from the public GitHub API so the card cannot go stale.
Lines fade and slide in one after another.
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "data" / "profile.json"
OUT = ROOT / "info-card.svg"

WIDTH = 490
PAD = 22
LINE = 22
CHARW = 7.82   # advance width of the 13px monospace stack, measured
COLS = int((WIDTH - 2 * PAD) / CHARW)

FG = "#c9d1d9"
KEY = "#39d353"
DIM = "#7d8590"
ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}

SWATCHES = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]


def escape(s):
    return "".join(ESCAPES.get(c, c) for c in str(s))


def wrap(text, budget):
    """Greedy word wrap in character units; the font is monospace so this is exact."""
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) > budget and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def live_stats(handle):
    """Best-effort: the card still renders if GitHub is unreachable."""
    try:
        user = requests.get(f"https://api.github.com/users/{handle}",
                            timeout=20).json()
        repos = requests.get(
            f"https://api.github.com/users/{handle}/repos?per_page=100",
            timeout=20).json()
    except Exception:
        return []

    if not isinstance(repos, list) or not isinstance(user, dict):
        return []

    langs = Counter(r["language"] for r in repos if r.get("language"))
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    since = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ")

    rows = [{"k": "repos", "v": f"{user.get('public_repos', len(repos))} public"}]
    if langs:
        top = " · ".join(f"{n} ({c})" for n, c in langs.most_common(3))
        rows.append({"k": "languages", "v": top})
    if stars:
        rows.append({"k": "stars", "v": str(stars)})
    rows.append({"k": "since", "v": since.strftime("%b %Y")})
    return rows


def build(conf, rows):
    lines = []
    y = PAD + 34

    def add(markup, step):
        nonlocal y
        delay = round(0.25 + step * 0.09, 3)
        lines.append(f'<g class="ln" style="animation-delay:{delay}s">{markup}</g>')

    step = 0
    add(f'<text class="title" x="{PAD}" y="{y}">{escape(conf["title"])}</text>', step)
    y += 8
    step += 1
    add(f'<line class="rule" x1="{PAD}" y1="{y}" x2="{WIDTH - PAD}" y2="{y}"/>', step)
    y += LINE + 2

    # Keys and values are separate <text> runs on a fixed pixel column, so
    # wrapped continuation lines line up under the value rather than the key.
    key_w = max(len(r["k"]) for r in rows) + 2
    val_x = round(PAD + key_w * CHARW)
    val_budget = COLS - key_w

    for r in rows:
        step += 1
        parts = wrap(r["v"], val_budget)
        markup = (f'<text class="k" x="{PAD}" y="{y}">{escape(r["k"])}:</text>')
        for j, part in enumerate(parts):
            markup += (f'<text class="v" x="{val_x}" y="{y + j * LINE}">'
                       f'{escape(part)}</text>')
        add(markup, step)
        y += LINE * len(parts)

    y += 6
    step += 1
    tag_lines = wrap(conf["tagline"], COLS)
    markup = "".join(
        f'<text class="tag" x="{PAD}" y="{y + j * LINE}">{escape(t)}</text>'
        for j, t in enumerate(tag_lines))
    add(markup, step)
    y += LINE * len(tag_lines) + 4

    step += 1
    sw = ""
    for i, c in enumerate(SWATCHES):
        sw += (f'<rect x="{PAD + i * 26}" y="{y - 12}" width="22" height="12" '
               f'rx="2" fill="{c}"/>')
    add(sw, step)
    y += 16

    height = y + PAD

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"
     viewBox="0 0 {WIDTH} {height}" role="img"
     aria-label="Profile summary card for {escape(conf["handle"])}">
  <style>
    text {{ font: 13px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .title {{ font-size: 15px; fill: {KEY}; font-weight: 600; }}
    .k {{ fill: {KEY}; }}
    .v {{ fill: {FG}; }}
    .tag {{ fill: {DIM}; font-style: italic; }}
    .rule {{ stroke: #21262d; stroke-width: 1; }}
    /* Base state is the resting state; `both` holds the from-state during the
       delay, so a non-animating renderer still shows a complete card. */
    .ln {{ opacity: 1; animation: rise .45s ease-out both; }}
    @keyframes rise {{
      from {{ opacity: 0; transform: translateX(-10px); }}
      to   {{ opacity: 1; transform: translateX(0); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .ln {{ animation: none; }} }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117" rx="10"/>
  <circle cx="{PAD}" cy="{PAD}" r="5" fill="#ff5f56"/>
  <circle cx="{PAD + 18}" cy="{PAD}" r="5" fill="#ffbd2e"/>
  <circle cx="{PAD + 36}" cy="{PAD}" r="5" fill="#27c93f"/>
  {"".join(lines)}
</svg>
'''


def main():
    conf = json.loads(CONF.read_text())
    rows = list(conf["rows"]) + live_stats(conf["handle"])
    OUT.write_text(build(conf, rows))
    print(f"wrote {OUT.name} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
