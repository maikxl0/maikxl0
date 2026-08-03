#!/usr/bin/env python3
"""
make_info_card.py — escribe info-card.svg a mano.

Imita la salida del comando `neofetch`: barra de título, líneas clave/valor
y la fila de bloques de color del final. Cada línea entra con un pequeño
retardo escalonado, así el panel parece imprimirse junto al retrato.

El contenido sale de scripts/config.py (CARD_ROWS). Mantén aquí lo que los
números no cuentan: el heatmap ya cubre tus estadísticas de GitHub.

    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py   # fotograma congelado
"""

import os
import pathlib

import config

OUT = pathlib.Path("info-card.svg")

W = 640
PAD = 26
FONT = 14.0
CH = FONT * 0.60                   # ancho de carácter monoespaciado
LINE = 25                          # alto de línea
KEY_COL = 11                       # ancho de la columna de etiquetas, en chars

STATIC = os.environ.get("STATIC") == "1"
STEP = 0.10                        # retardo entre líneas
START = 0.20

DOTS = ["#ff5f57", "#febc2e", "#28c840"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    body: list[str] = []
    n = 0                          # contador global de líneas, para el stagger

    def delay() -> str:
        """Retardo de animación de la siguiente línea (y avanza el contador)."""
        nonlocal n
        d = "" if STATIC else f' style="animation-delay:{START + n * STEP:.2f}s"'
        n += 1
        return d

    y = PAD + 44                   # bajo la barra de título

    # cabecera: usuario@host subrayado, como neofetch
    title = esc(config.CARD_TITLE)
    body.append(f'<text class="ln k" x="{PAD}" y="{y}"{delay()}>{title}</text>')
    y += LINE - 6
    body.append(f'<text class="ln dim" x="{PAD}" y="{y}"{delay()}>'
                f'{"─" * len(config.CARD_TITLE)}</text>')
    y += LINE

    if config.CARD_TAGLINE:
        body.append(f'<text class="ln dim" x="{PAD}" y="{y}"{delay()}>'
                    f'{esc(config.CARD_TAGLINE)}</text>')
        y += LINE + 6

    val_x = round(PAD + KEY_COL * CH, 1)

    for key, value in config.CARD_ROWS:
        values = value if isinstance(value, list) else [value]
        for j, v in enumerate(values):
            d = delay()
            parts = [f'<text class="ln val" x="{val_x}" y="{y}"{d}>'
                     f'{esc(v)}</text>']
            if j == 0:              # la etiqueta solo en la primera línea
                parts.insert(0, f'<text class="ln k" x="{PAD}" y="{y}"{d}>'
                                f'{esc(key)}</text>')
            body.extend(parts)
            y += LINE
        y += 4

    # bloques de color, el guiño final de neofetch
    y += 6
    sw = 22
    for i, c in enumerate(config.PALETTE):
        body.append(f'<rect class="ln" x="{PAD + i * (sw + 6)}" y="{y}"{delay()} '
                    f'width="{sw}" height="12" rx="2" fill="{c}"/>')
    y += 12 + PAD

    h = round(y)

    dots = "".join(
        f'<circle cx="{PAD + 6 + i * 18}" cy="{PAD - 4}" r="5.5" fill="{c}"/>'
        for i, c in enumerate(DOTS))

    anim = "" if STATIC else """
    .ln { opacity:0; animation: in .45s cubic-bezier(.2,.7,.3,1) forwards; }
    @keyframes in { from { opacity:0; transform:translateX(-10px); }
                    to   { opacity:1; transform:none; } }
    @media (prefers-reduced-motion: reduce) {
      .ln { opacity:1; animation:none; } }"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}"
     viewBox="0 0 {W} {h}" role="img" aria-label="Ficha estilo neofetch">
  <style>
    text {{ font-family:{config.MONO}; font-size:{FONT}px; }}
    .k   {{ fill:{config.ACCENT}; font-weight:700; }}
    .val {{ fill:{config.FG}; }}
    .dim {{ fill:{config.DIM}; }}{anim}
  </style>
  <rect width="100%" height="100%" fill="{config.BG}" rx="10"/>
  <rect x="0" y="0" width="{W}" height="{PAD + 6}" fill="#161b22"
        rx="10"/>
  <rect x="0" y="{PAD - 4}" width="{W}" height="10" fill="#161b22"/>
  {dots}
{chr(10).join('  ' + b for b in body)}
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"✓ {OUT}  ({W}×{h}{', estático' if STATIC else ''})")


if __name__ == "__main__":
    main()
