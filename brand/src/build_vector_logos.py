#!/usr/bin/env python3
"""Compose the soundadam mark, compact hat, and lockup from the traced wordmark.

Writes into web/, the directory every consumer takes the marks from
(see README.md). The
filled Mexican-hat / Ricker wavelet is the identity. The nine-cell grid
with a hat cutout is the large mark. The hat silhouette alone is the
compact mark used at small sizes and next to the wordmark.
"""

import math
from pathlib import Path
from xml.etree import ElementTree as ET

BRAND = Path(__file__).resolve().parents[1]
REPO = BRAND.parent
SRC = Path(__file__).resolve().parent
WEB = REPO / "web"
ARCHIVE = BRAND / "archive"
TRACE = SRC / "wordmark-trace.svg"

CANVAS_W = 1324
CANVAS_H = 280
GRID_MARGIN = 48
WORDMARK_GAP = 64
WORDMARK_FILL_LIGHT = "#050505"
# The wordmark on a dark page; the hat keeps its blue gradient.
WORDMARK_FILL_DARK = "#f1eef3"

GRADIENT_STOPS = [
    (0, "#006fe8"),
    (0.5, "#0f93ff"),
    (1, "#1386ff"),
]


def wordmark_paths() -> str:
    root = ET.parse(TRACE).getroot()
    chunks = []
    for element in root.iter():
        if element.tag.endswith("path") and element.get("d"):
            transform = element.get("transform")
            transform_attr = f' transform="{transform}"' if transform else ""
            chunks.append(f'<path d="{element.get("d")}"{transform_attr}/>')
    if not chunks:
        raise RuntimeError(f"No wordmark paths in {TRACE}")
    return "\n      ".join(chunks)


def gradient_def() -> str:
    stops = "\n      ".join(
        f'<stop offset="{offset}" stop-color="{color}"/>' for offset, color in GRADIENT_STOPS
    )
    return f'''<linearGradient id="soundadam-blue" x1="0%" y1="100%" x2="100%" y2="0%">
      {stops}
    </linearGradient>'''


def icon_cells(rx: int = 10) -> str:
    cells = []
    for y in (2, 78, 154):
        for x in (2, 78, 154):
            cells.append(f'<rect x="{x}" y="{y}" width="68" height="68" rx="{rx}"/>')
    return "\n        ".join(cells)


def polyline_path(points: list[tuple[float, float]]) -> str:
    """Dense sample polyline — faithful to the numpy Ricker, no spline fattening."""
    parts = [f"M{points[0][0]:.2f} {points[0][1]:.2f}"]
    parts.extend(f"L{x:.2f} {y:.2f}" for x, y in points[1:])
    return " ".join(parts)


def ricker(t: float) -> float:
    """Mexican-hat / Ricker wavelet: (1 - t²) exp(-t² / 2). Peak 1 at t=0.

    Zeros at t=±1, negative lobes at t=±√3 (value ≈ −0.446), returns to
    ~0 by |t|≈4. Same formula as numpy; scipy.signal.ricker is this
    shape at a discrete width.
    """
    return (1.0 - t * t) * math.exp(-0.5 * t * t)


# t ∈ [−4, 4]: edges ≈ 0 (flat brim). Previous [−2.4, 2.4] cut the
# return-to-zero and stretched the peak across the side columns.
RICKER_T_MAX = 4.0
RICKER_SAMPLES = 241
WAVEFORM_X0, WAVEFORM_X1 = 8.0, 216.0
WAVEFORM_Y_ZERO = 112.0
WAVEFORM_AMP_POS = 96.0
WAVEFORM_AMP_NEG = 184.0  # −0.446 * 184 ≈ 82px below zero → y≈194
WAVEFORM_STROKE = 10


def ricker_series(n: int = RICKER_SAMPLES, t_max: float = RICKER_T_MAX):
    """(t, ψ(t)) samples. numpy when present, identical math otherwise."""
    try:
        import numpy as np

        t = np.linspace(-t_max, t_max, n)
        psi = (1.0 - t * t) * np.exp(-0.5 * t * t)
        return list(zip(t.tolist(), psi.tolist()))
    except ImportError:
        return [
            (
                -t_max + 2 * t_max * i / (n - 1),
                ricker(-t_max + 2 * t_max * i / (n - 1)),
            )
            for i in range(n)
        ]


def waveform_points(*, brim_boost: bool = True) -> list[tuple[float, float]]:
    """Map a real Ricker onto the 224×224 nine-cell.

    Linear t→x. Positive lobe uses AMP_POS. If brim_boost, negative lobes
    use AMP_NEG so the hat brim cuts the bottom row; otherwise true 0.446
    ratio (brim sits in the mid/bottom gutter and vanishes at favicon size).
    """
    span = WAVEFORM_X1 - WAVEFORM_X0
    pts = []
    for t, psi in ricker_series():
        x = WAVEFORM_X0 + span * (t + RICKER_T_MAX) / (2 * RICKER_T_MAX)
        amp = WAVEFORM_AMP_POS if (psi >= 0 or not brim_boost) else WAVEFORM_AMP_NEG
        y = WAVEFORM_Y_ZERO - amp * psi
        pts.append((x, y))
    return pts


def hat_fill_d() -> str:
    pts = waveform_points(brim_boost=True)
    curve = polyline_path(pts)
    y0 = WAVEFORM_Y_ZERO
    return f"{curve} L{pts[-1][0]:.2f} {y0:.2f} L{pts[0][0]:.2f} {y0:.2f} Z"


def hat_stroke_d() -> str:
    return polyline_path(waveform_points(brim_boost=True))


def waveform_overlay(cutout: str, filled: bool = True) -> str:
    if filled:
        return f'<path d="{hat_fill_d()}" fill="{cutout}"/>'
    return (
        f'<path d="{hat_stroke_d()}" fill="none" stroke="{cutout}" '
        f'stroke-width="{WAVEFORM_STROKE}" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
    )


def grid_cutout_mark(overlay: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="224" height="224" viewBox="0 0 224 224">
  <defs>
    {gradient_def()}
    <mask id="mark-cutout" maskUnits="userSpaceOnUse" x="0" y="0" width="224" height="224">
      <g fill="#ffffff">
        {icon_cells()}
      </g>
      {overlay}
    </mask>
  </defs>
  <rect width="224" height="224" fill="url(#soundadam-blue)" mask="url(#mark-cutout)"/>
</svg>
'''


def mark_svg() -> str:
    """Nine-cell grid with filled-hat cutout. Hole stays transparent.

    Use as a standalone glyph (browser chrome, large display). The cutout
    maps whatever sits behind the SVG — do not composite onto white.
    Never pair with the wordmark.
    """
    return grid_cutout_mark(waveform_overlay("#000000", filled=True))


def compact_mark_svg() -> str:
    """Filled Mexican-hat as the glyph itself — no nine-cell grid."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="224" height="224" viewBox="0 0 224 224">
  <defs>
    {gradient_def()}
  </defs>
  <path d="{hat_fill_d()}" fill="url(#soundadam-blue)"/>
</svg>
'''


def compact_on_blue_svg() -> str:
    """Blue tile, white hat. Standalone icon only — never next to type."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="224" height="224" viewBox="0 0 224 224">
  <defs>
    {gradient_def()}
  </defs>
  <rect width="224" height="224" fill="url(#soundadam-blue)"/>
  <path d="{hat_fill_d()}" fill="#ffffff"/>
</svg>
'''


def lockup_svg(wordmark: str, fill: str = WORDMARK_FILL_LIGHT) -> str:
    """Compact hat + traced wordmark on a transparent canvas.

    Never the nine-cell next to type. Never compact-on-blue next to type.
    """
    wordmark_x = GRID_MARGIN + 224 + WORDMARK_GAP
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" aria-labelledby="title desc">
  <title id="title">soundadam O&amp;M + acoustics logo</title>
  <desc id="desc">soundadam wordmark with a compact Mexican-hat mark.</desc>
  <defs>
    {gradient_def()}
  </defs>
  <g transform="translate({GRID_MARGIN} 28)">
    <path d="{hat_fill_d()}" fill="url(#soundadam-blue)"/>
  </g>
  <g transform="translate({wordmark_x} 28)" fill="{fill}" fill-rule="evenodd">
      {wordmark}
  </g>
</svg>
'''


def archive_stroke_svg() -> str:
    """Nine-cell grid with stroked-hat cutout. Light backgrounds only."""
    return grid_cutout_mark(waveform_overlay("#000000", filled=False))


def archive_stroke_on_blue_svg() -> str:
    """Blue field, white Ricker stroke — inverse of the unused line mark."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="224" height="224" viewBox="0 0 224 224">
  <defs>
    {gradient_def()}
  </defs>
  <rect width="224" height="224" fill="url(#soundadam-blue)"/>
  <path d="{hat_stroke_d()}" fill="none" stroke="#ffffff" stroke-width="{WAVEFORM_STROKE}" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''


def main() -> None:
    wordmark = wordmark_paths()
    WEB.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    compact = compact_mark_svg()
    (WEB / "mark.svg").write_text(mark_svg(), encoding="utf-8")
    (WEB / "mark-compact.svg").write_text(compact, encoding="utf-8")
    (WEB / "waveform.svg").write_text(lockup_svg(wordmark), encoding="utf-8")
    (WEB / "waveform-dark.svg").write_text(
        lockup_svg(wordmark, WORDMARK_FILL_DARK), encoding="utf-8"
    )
    (WEB / "mark-compact-on-blue.svg").write_text(
        compact_on_blue_svg(), encoding="utf-8"
    )
    # Page favicon is the compact hat, never the lockup (the wordmark
    # vanishes at 16px). NewAPI Logo is this same file: rc.25 applies
    # Logo as the tab icon and sits it next to SystemName.
    (WEB / "favicon.svg").write_text(compact, encoding="utf-8")
    (ARCHIVE / "stroke.svg").write_text(archive_stroke_svg(), encoding="utf-8")
    (ARCHIVE / "stroke-on-blue.svg").write_text(
        archive_stroke_on_blue_svg(), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
