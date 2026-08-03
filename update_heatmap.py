#!/usr/bin/env python3
"""
update_heatmap.py — todo el heatmap en un solo archivo, sin dependencias.

Baja tu calendario público de contribuciones (sin token, sin GraphQL) y lo
dibuja como SVG animado. Es lo único que necesita correr cada día.

    pip install requests beautifulsoup4
    python update_heatmap.py

Genera: data/contributions.json  y  contrib-heatmap.svg
"""

import datetime as dt
import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------------ ajustes
USERNAME = "maikxl0"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
BG, FG, DIM = "#0d1117", "#c9d1d9", "#8b949e"
MONO = ("ui-monospace,'SFMono-Regular','JetBrains Mono','Fira Code',"
        "Menlo,Consolas,monospace")

JSON_OUT = pathlib.Path("data/contributions.json")
SVG_OUT = pathlib.Path("contrib-heatmap.svg")

URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {"User-Agent": "Mozilla/5.0 (profile-art script)",
           "X-Requested-With": "XMLHttpRequest", "Accept": "text/html"}

CELL, GAP = 12, 3
PITCH = CELL + GAP
LEFT, TOP, RIGHT, W = 36, 34, 32, 860
DIAG, DUR = 0.016, 0.45
STATIC = os.environ.get("STATIC") == "1"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fetch_html() -> str:
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse_days(html: str) -> list[dict]:
    """Cada celda <td class="ContributionCalendar-day"> es un día."""
    soup = BeautifulSoup(html, "html.parser")

    # El número exacto vive en el <tool-tip for="id-de-la-celda">.
    tips = {t.get("for"): t.get_text(" ", strip=True)
            for t in soup.find_all("tool-tip") if t.get("for")}

    days = []
    for cell in soup.select(".ContributionCalendar-day"):
        date = cell.get("data-date")
        if not date:
            continue

        count = cell.get("data-count")           # por si GitHub lo reactiva
        if count is None:
            text = tips.get(cell.get("id"), "")
            m = re.search(r"([\d,]+)\s+contribution", text)
            count = m.group(1).replace(",", "") if m else "0"

        days.append({
            "date": date,
            "count": int(count),
            "level": int(cell.get("data-level") or 0),
        })

    if not days:
        sys.exit("No pude leer ninguna celda. ¿El usuario existe y es público?")

    days.sort(key=lambda d: d["date"])
    return days


def add_neon_level(days: list[dict]) -> None:
    """
    GitHub solo da niveles 0–4. Nuestro nivel 5 es un extremo propio: los
    días de nivel 4 que además están en tu 15 % superior.
    """
    tops = sorted((d["count"] for d in days if d["level"] == 4), reverse=True)
    if not tops:
        return
    cutoff = tops[max(0, int(len(tops) * 0.15) - 1)]
    for d in days:
        if d["level"] == 4 and d["count"] >= cutoff:
            d["level"] = 5


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # La racha actual se cuenta hacia atrás. El último día se ignora si aún
    # está en cero: puede que simplemente no hayas empujado nada hoy.
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    current = 0
    for d in tail:
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def build_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)

    monthly: dict[str, int] = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    active = sum(1 for d in days if d["count"] > 0)
    return {
        "total": total,
        "days_tracked": len(days),
        "active_days": active,
        "busiest_day": {"date": best["date"], "count": best["count"]},
        "current_streak": current,
        "longest_streak": longest,
        "daily_average": round(total / max(1, len(days)), 2),
        "monthly": monthly,
    }


def render(data: dict) -> None:
    days, stats = data["days"], data["stats"]

    cells, month_labels = [], []
    col = 0
    seen_months: set[str] = set()

    for d in days:
        date = dt.date.fromisoformat(d["date"])
        row = (date.weekday() + 1) % 7          # domingo = 0, como GitHub
        if row == 0 and d is not days[0]:
            col += 1

        x = LEFT + col * PITCH
        y = TOP + row * PITCH
        fill = PALETTE[min(d["level"], len(PALETTE) - 1)]
        delay = f'{(col + row) * DIAG:.2f}s'

        style = "" if STATIC else f' style="animation-delay:{delay}"'
        label = (f'{d["count"]} contributions on {d["date"]}'
                 if d["count"] else f'no contributions on {d["date"]}')
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{fill}"{style}><title>{esc(label)}</title></rect>')

        # etiqueta de mes sobre la primera columna de cada mes nuevo
        key = d["date"][:7]
        if key not in seen_months and date.day <= 7:
            seen_months.add(key)
            month_labels.append(
                f'<text class="lbl" x="{x}" y="{TOP - 12}">'
                f'{MONTHS[date.month - 1]}</text>')

    grid_bottom = TOP + 7 * PITCH
    legend_y = grid_bottom + 22
    H = grid_bottom + 62

    weekdays = "".join(
        f'<text class="lbl" x="{LEFT - 8}" y="{TOP + r * PITCH + 9.5}" '
        f'text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))

    lx = W - RIGHT - (len(PALETTE) * PITCH) - 78
    legend = f'<text class="lbl" x="{lx}" y="{legend_y + 9.5}">Less</text>'
    for i, c in enumerate(PALETTE):
        legend += (f'<rect x="{lx + 40 + i * PITCH}" y="{legend_y}" '
                   f'width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    legend += (f'<text class="lbl" x="{lx + 46 + len(PALETTE) * PITCH}" '
               f'y="{legend_y + 9.5}">More</text>')

    foot = f'{stats["total"]:,} contributions in the last year'
    sub = (f'current streak {stats["current_streak"]}d  ·  '
           f'longest {stats["longest_streak"]}d  ·  '
           f'best day {stats["busiest_day"]["count"]}  ·  '
           f'{stats["active_days"]}/{stats["days_tracked"]} active days')

    anim = "" if STATIC else f"""
    .c {{ opacity:0; transform-box:fill-box; transform-origin:center;
         animation: pop {DUR}s cubic-bezier(.2,.8,.3,1) forwards; }}
    @keyframes pop {{ from {{ opacity:0; transform:translateY(-7px) scale(.55); }}
                     to   {{ opacity:1; transform:none; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .c {{ opacity:1; animation:none; }} }}"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="Contribution calendar for {esc(data['username'])}">
  <style>
    text  {{ font-family:{MONO}; }}
    .lbl  {{ font-size:11px; fill:{DIM}; }}
    .tot  {{ font-size:13px; fill:{FG}; font-weight:700; }}
    .sub  {{ font-size:11px; fill:{DIM}; }}{anim}
  </style>
  <rect width="100%" height="100%" fill="{BG}" rx="10"/>
{chr(10).join('  ' + m for m in month_labels)}
  {weekdays}
{chr(10).join('  ' + c for c in cells)}
  {legend}
  <text class="tot" x="{LEFT}" y="{legend_y + 10}">{foot}</text>
  <text class="sub" x="{LEFT}" y="{legend_y + 30}">{sub}</text>
</svg>
"""
    SVG_OUT.write_text(svg, encoding="utf-8")
    print(f"✓ {SVG_OUT}  ({W}×{H}, {len(cells)} días"
          f"{', estático' if STATIC else ''})")

def main() -> None:
    print(f"· leyendo {URL}")
    days = parse_days(fetch_html())
    add_neon_level(days)

    data = {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc)
                          .isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "stats": build_stats(days),
        "days": days,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    s = data["stats"]
    print(f"✓ {JSON_OUT}  {s['total']:,} contribuciones · "
          f"racha {s['current_streak']}d · récord {s['longest_streak']}d")

    render(data)


if __name__ == "__main__":
    main()
