"""Render data/contributions.json as an animated SVG contribution calendar.

Cells fade+drop in along a diagonal wave (delay tied to week + weekday), so the
graph appears to sweep in from the top-left. Pure CSS keyframes: GitHub serves
README images through <img>, which runs declarative animation but no script.
"""

import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD_L = 30
PAD_T = 34
WIDTH = 860
FOOT = 34

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(day):
    """Trust GitHub's own bucket, but promote the busiest days to the 6th color."""
    lvl = day["level"]
    return 5 if day["count"] >= 10 else lvl


def build():
    payload = json.loads(DATA.read_text())
    days = payload["days"]

    # Bucket into columns of 7, starting on the calendar's first Sunday column.
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    offset = (first.weekday() + 1) % 7  # Python: Mon=0; GitHub grid: Sun=0

    cells = []
    months = []
    seen_months = set()
    for i, day in enumerate(days):
        idx = i + offset
        week, wd = divmod(idx, 7)
        x = PAD_L + week * STEP
        y = PAD_T + wd * STEP
        d = datetime.strptime(day["date"], "%Y-%m-%d").date()

        if d.day <= 7 and d.month not in seen_months and week > 0:
            seen_months.add(d.month)
            months.append((PAD_L + week * STEP, MONTHS[d.month - 1]))

        delay = round((week + wd) * 0.022, 3)
        label = "No contributions" if day["count"] == 0 else (
            f"{day['count']} contribution{'s' if day['count'] != 1 else ''}")
        cells.append(
            f'<rect class="d" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{PALETTE[level_for(day)]}" '
            f'style="animation-delay:{delay}s">'
            f"<title>{label} on {day['date']}</title></rect>"
        )

    weeks = (len(days) + offset + 6) // 7
    height = PAD_T + 7 * STEP + FOOT

    wd_labels = "".join(
        f'<text class="lab" x="{PAD_L - 8}" y="{PAD_T + i * STEP + CELL - 2}" '
        f'text-anchor="end">{n}</text>'
        for i, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    mo_labels = "".join(
        f'<text class="lab" x="{x}" y="{PAD_T - 8}">{n}</text>' for x, n in months
    )

    # Right-align the legend against the last column so nothing clips the edge.
    right = PAD_L + weeks * STEP - GAP
    swatches_x = right - 34 - len(PALETTE) * STEP
    legend_y = height - 26
    legend = (f'<text class="lab" x="{swatches_x - 6}" y="{legend_y + 10}" '
              f'text-anchor="end">Less</text>')
    for i, color in enumerate(PALETTE):
        legend += (f'<rect x="{swatches_x + i * STEP}" y="{legend_y}" width="{CELL}" '
                   f'height="{CELL}" rx="2.5" fill="{color}"/>')
    legend += (f'<text class="lab" x="{swatches_x + len(PALETTE) * STEP + 6}" '
               f'y="{legend_y + 10}">More</text>')

    total = payload["total"]
    stamp = date.today().isoformat()
    summary = (f'<text class="sum" x="{PAD_L}" y="{height - 16}">'
               f'{total} contributions in the last year '
               f'<tspan class="lab">· updated {stamp}</tspan></text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"
     viewBox="0 0 {WIDTH} {height}" role="img"
     aria-label="{total} GitHub contributions in the last year">
  <style>
    /* Base state is the *finished* state and fill-mode is `both`, so a renderer
       that ignores CSS animation still shows a complete graph. */
    .d {{ opacity: 1; transform-box: fill-box; transform-origin: center;
          animation: pop .55s cubic-bezier(.2,.8,.3,1) both; }}
    @keyframes pop {{
      from {{ opacity: 0; transform: translateY(-9px) scale(.4); }}
      to   {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    .lab {{ font: 10px ui-monospace, SFMono-Regular, Menlo, monospace; fill: #7d8590; }}
    .sum {{ font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; fill: #c9d1d9; }}
    @media (prefers-reduced-motion: reduce) {{
      .d {{ animation: none; opacity: 1; }}
    }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117" rx="10"/>
  {mo_labels}{wd_labels}
  {"".join(cells)}
  {legend}{summary}
</svg>
'''


def main():
    OUT.write_text(build())
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
