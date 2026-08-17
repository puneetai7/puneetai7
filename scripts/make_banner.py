"""Render banner.svg — the animated header at the top of the README.

The wordmark is filled with a repeating gradient that is swept across it by a
SMIL animateTransform (SMIL, like CSS keyframes, runs inside an <img>), giving a
light that travels through the letters. The tagline types itself underneath.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "data" / "profile.json"
OUT = ROOT / "banner.svg"

WIDTH = 860
HEIGHT = 176
PAD = 30

TITLE_SIZE = 62
TRACK = 6           # letter-spacing
SWEEP = 420         # gradient tile width; the sweep translates exactly this far

ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def escape(s):
    return "".join(ESCAPES.get(c, c) for c in str(s))


def build(conf):
    handle = conf["handle"]
    tagline = conf["tagline"]

    title_y = PAD + TITLE_SIZE - 6
    rule_y = title_y + 20
    tag_y = rule_y + 30

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}" role="img"
     aria-label="{escape(handle)} — {escape(tagline)}">
  <defs>
    <linearGradient id="sweep" gradientUnits="userSpaceOnUse"
                    x1="0" y1="0" x2="{SWEEP}" y2="0" spreadMethod="repeat">
      <stop offset="0"    stop-color="#1f9e40"/>
      <stop offset="0.35" stop-color="#39d353"/>
      <stop offset="0.5"  stop-color="#d8ffe6"/>
      <stop offset="0.65" stop-color="#39d353"/>
      <stop offset="1"    stop-color="#1f9e40"/>
      <animateTransform attributeName="gradientTransform" type="translate"
                        from="0 0" to="{SWEEP} 0" dur="3.2s" repeatCount="indefinite"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .wordmark {{
      font: 700 {TITLE_SIZE}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      letter-spacing: {TRACK}px;
    }}
    .tag {{
      font: 15px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      fill: #8b949e;
      clip-path: inset(0 0 0 0);
      animation: type 1.6s steps(48, end) both;
      animation-delay: .45s;
    }}
    @keyframes type {{
      from {{ clip-path: inset(0 100% 0 0); }}
      to   {{ clip-path: inset(0 0 0 0); }}
    }}
    .rule {{
      stroke: #39d353; stroke-width: 2; stroke-linecap: round;
      stroke-dasharray: {WIDTH}; stroke-dashoffset: 0;
      animation: draw .9s cubic-bezier(.2,.8,.3,1) both;
    }}
    @keyframes draw {{
      from {{ stroke-dashoffset: {WIDTH}; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    .caret {{
      font: 15px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      fill: #39d353;
      animation: blink 1.05s steps(1, end) infinite both;
      animation-delay: 2.05s;
    }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 51%, 100% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .tag, .rule, .caret {{ animation: none; }}
    }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117" rx="12"/>
  <text class="wordmark" x="{PAD}" y="{title_y}" fill="url(#sweep)"
        filter="url(#soft)">{escape(handle)}</text>
  <line class="rule" x1="{PAD}" y1="{rule_y}" x2="{WIDTH - PAD}" y2="{rule_y}"/>
  <text class="tag" x="{PAD}" y="{tag_y}">{escape(tagline)}</text>
  <text class="caret" x="{PAD}" y="{tag_y + 22}">&#9611;</text>
</svg>
'''


def main():
    conf = json.loads(CONF.read_text())
    OUT.write_text(build(conf))
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
