"""Convert data/prepped-photo.png into an animated ASCII-art SVG.

Each row of characters wipes in left-to-right, staggered top-to-bottom, so the
portrait looks like it is being typed into a terminal.

Font metrics are forced with textLength/lengthAdjust so the art keeps its
proportions no matter which monospace face the viewer's machine resolves.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "prepped-photo.png"
MASK = ROOT / "data" / "prepped-alpha.png"
OUT = ROOT / "avi-ascii.svg"

# Density ramp, brightest -> darkest.
RAMP = " .`:-=+*cs#%@"

COLS = 84
CW = 7          # character advance width
CH = 12         # line height
PAD = 14
GAMMA = 0.85    # <1 darkens midtones so the face keeps its modelling

ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def escape(s):
    return "".join(ESCAPES.get(c, c) for c in s)


def to_rows():
    img = ImageOps.grayscale(Image.open(SRC))
    w, h = img.size
    rows = max(1, round(h / w * COLS * CW / CH))

    lum = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32)
    if MASK.exists():
        alpha = np.asarray(
            ImageOps.grayscale(Image.open(MASK)).resize((COLS, rows), Image.LANCZOS),
            dtype=np.float32,
        ) / 255.0
    else:
        alpha = (lum < 200).astype(np.float32)

    subject = alpha > 0.45
    if not subject.any():
        subject = np.ones_like(alpha, dtype=bool)

    # Stretch the subject's own tonal range across the ramp. Without this the
    # skin occupies only the top few levels and the face reads as an empty oval.
    lo, hi = np.percentile(lum[subject], (2, 98))
    if hi - lo < 1e-3:
        hi = lo + 1.0
    norm = np.clip((lum - lo) / (hi - lo), 0.0, 1.0) ** GAMMA

    # The art is bright glyphs on a dark panel, so ink reads as *light*: map
    # bright pixels to the dense end of the ramp, or the portrait comes out
    # tonally inverted (glowing suit, shadowed face).
    # Index 0 (space) is reserved for the background so the silhouette stays clean.
    idx = np.rint(norm * (len(RAMP) - 2)).astype(int) + 1
    idx[~subject] = 0

    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def build(rows):
    width = COLS * CW + PAD * 2
    height = len(rows) * CH + PAD * 2 + CH  # extra line for the caret

    body = []
    for i, line in enumerate(rows):
        if not line:
            continue
        y = PAD + (i + 1) * CH
        delay = round(i * 0.045, 3)
        body.append(
            f'<text class="r" x="{PAD}" y="{y}" textLength="{len(line) * CW}" '
            f'lengthAdjust="spacing" xml:space="preserve" '
            f'style="animation-delay:{delay}s">{escape(line)}</text>'
        )

    caret_y = PAD + (len(rows) + 1) * CH
    caret_delay = round(len(rows) * 0.045 + 0.3, 3)
    caret = (f'<text class="caret" x="{PAD}" y="{caret_y}" '
             f'style="animation-delay:{caret_delay}s">&#9611;</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img"
     aria-label="ASCII-art portrait rendered from a photograph">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#9ef7b4"/>
      <stop offset="0.55" stop-color="#39d353"/>
      <stop offset="1" stop-color="#1f9e40"/>
    </linearGradient>
    <!-- Phosphor bloom: a blurred copy under the crisp glyphs. -->
    <filter id="crt" x="-8%" y="-8%" width="116%" height="116%">
      <feGaussianBlur stdDeviation="1.1" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    /* Base state is fully revealed; `both` makes the delay hold the hidden
       from-state, so renderers that ignore animation still show the art. */
    .r {{
      font: {CH - 1}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      fill: url(#g);
      white-space: pre;
      clip-path: inset(0 0 0 0);
      animation: type .5s steps(24, end) both;
    }}
    @keyframes type {{
      from {{ clip-path: inset(0 100% 0 0); }}
      to   {{ clip-path: inset(0 0 0 0); }}
    }}
    .caret {{
      font: {CH - 1}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      fill: #39d353;
      animation: blink 1.05s steps(1, end) infinite both;
    }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 51%, 100% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .r {{ animation: none; }}
      .caret {{ animation: none; }}
    }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117" rx="10"/>
  <g filter="url(#crt)">{"".join(body)}</g>
  {caret}
</svg>
'''


def main():
    rows = to_rows()
    OUT.write_text(build(rows))
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} chars)")


if __name__ == "__main__":
    main()
