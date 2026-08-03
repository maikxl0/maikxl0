#!/usr/bin/env python3
"""
make_ascii_svg.py — convierte source-prepped.png en avi-ascii.svg.

La imagen se reduce a una rejilla de caracteres y el brillo de cada celda
elige un glifo de la rampa. Cada fila vive dentro de un clip horizontal que
se abre de izquierda a derecha, con un bloque-cursor montado en el borde,
escalonado de arriba a abajo. Se imprime una vez y se congela: sin bucle.

La animación es SMIL DENTRO del SVG, que es lo único que GitHub ejecuta en
un README (nada de <script>, nada de CSS externo).

    python scripts/make_ascii_svg.py
    STATIC=1 python scripts/make_ascii_svg.py   # fotograma congelado
"""

import os
import pathlib

import numpy as np
from PIL import Image

import config

SRC = pathlib.Path("source-prepped.png")
OUT = pathlib.Path("ascii-portrait.svg")

FONT_SIZE = 9.0
CHAR_W = FONT_SIZE * 0.60          # ancho de celda monoespaciada
LINE_H = FONT_SIZE * 1.00          # alto de celda
PAD = 10

ROW_DELAY = 0.055                  # separación entre filas
ROW_DUR = 0.50                     # cuánto tarda una fila en escribirse
START = 0.25

STATIC = os.environ.get("STATIC") == "1"


def to_char_grid(path: pathlib.Path, cols: int) -> list[str]:
    """Reduce la imagen a filas de caracteres."""
    img = Image.open(path).convert("L")
    # Los caracteres son más altos que anchos: corregimos la proporción.
    rows = max(1, round(img.height / img.width * cols * (CHAR_W / LINE_H)))
    small = img.resize((cols, rows), Image.LANCZOS)

    arr = np.array(small, dtype=np.float32) / 255.0
    ramp = config.RAMP
    # brillo 1.0 (blanco) -> índice 0 (espacio); 0.0 (negro) -> último glifo
    idx = np.clip(((1.0 - arr) * (len(ramp) - 1)).round().astype(int),
                  0, len(ramp) - 1)
    return ["".join(ramp[i] for i in row) for row in idx]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(grid: list[str]) -> str:
    cols = max(len(r) for r in grid)
    rows = len(grid)
    w = round(cols * CHAR_W + PAD * 2, 2)
    h = round(rows * LINE_H + PAD * 2, 2)
    row_w = round(cols * CHAR_W, 2)

    defs, body = [], []

    for i, line in enumerate(grid):
        y = round(PAD + (i + 0.82) * LINE_H, 2)
        begin = round(START + i * ROW_DELAY, 3)
        stripped = line.rstrip()

        if STATIC:
            defs.append(
                f'<clipPath id="w{i}"><rect x="{PAD}" y="0" '
                f'width="{row_w}" height="{h}"/></clipPath>')
        else:
            defs.append(
                f'<clipPath id="w{i}"><rect x="{PAD}" y="0" width="0" '
                f'height="{h}">'
                f'<animate attributeName="width" from="0" to="{row_w}" '
                f'begin="{begin}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'</rect></clipPath>')

        if stripped:
            tl = round(len(stripped) * CHAR_W, 2)
            body.append(
                f'<text class="a" x="{PAD}" y="{y}" clip-path="url(#w{i})" '
                f'textLength="{tl}" lengthAdjust="spacingAndGlyphs" '
                f'xml:space="preserve">{esc(stripped)}</text>')

        if not STATIC:
            cy = round(PAD + i * LINE_H + LINE_H * 0.12, 2)
            body.append(
                f'<rect class="cur" x="{PAD}" y="{cy}" width="{CHAR_W:.2f}" '
                f'height="{LINE_H * 0.86:.2f}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{begin}s"/>'
                f'<animate attributeName="x" from="{PAD}" '
                f'to="{round(PAD + row_w, 2)}" begin="{begin}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" '
                f'begin="{round(begin + ROW_DUR, 3)}s"/>'
                f'</rect>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"
     viewBox="0 0 {w} {h}" role="img"
     aria-label="Retrato en arte ASCII de {esc(config.USERNAME)}">
  <style>
    .a  {{ font-family:{config.MONO}; font-size:{FONT_SIZE}px;
          fill:{config.FG}; white-space:pre; }}
    .cur{{ fill:{config.ACCENT}; }}
  </style>
  <defs>
{chr(10).join('    ' + d for d in defs)}
  </defs>
  <rect width="100%" height="100%" fill="{config.BG}" rx="10"/>
{chr(10).join('  ' + b for b in body)}
</svg>
"""


def main() -> None:
    if not SRC.exists():
        raise SystemExit(
            f"falta {SRC} — ejecuta antes: python scripts/prep_photo.py foto.jpg")
    grid = to_char_grid(SRC, config.ASCII_COLS)
    OUT.write_text(build_svg(grid), encoding="utf-8")
    print(f"✓ {OUT}  ({config.ASCII_COLS}×{len(grid)} caracteres"
          f"{', estático' if STATIC else ''})")


if __name__ == "__main__":
    main()
