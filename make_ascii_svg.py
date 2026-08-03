#!/usr/bin/env python3
"""
fetch_contributions.py — baja tu calendario real de contribuciones.

Sin token, sin GraphQL, sin servicios de terceros: GitHub publica el
calendario como HTML en https://github.com/users/<usuario>/contributions,
el mismo fragmento que usa tu página de perfil.

Guarda data/contributions.json con los días crudos más estadísticas
derivadas: racha actual, racha más larga, mejor día y totales por mes.

    python scripts/fetch_contributions.py
"""

import datetime as dt
import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

import config

USERNAME = os.environ.get("GH_USERNAME") or config.USERNAME
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = pathlib.Path("data/contributions.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art script)",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html",
}


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


def main() -> None:
    print(f"· leyendo {URL}")
    days = parse_days(fetch_html())
    add_neon_level(days)

    payload = {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc)
                          .isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "stats": build_stats(days),
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    s = payload["stats"]
    print(f"✓ {OUT}  {s['total']:,} contribuciones · racha {s['current_streak']}d "
          f"· récord {s['longest_streak']}d · mejor día {s['busiest_day']['count']}")


if __name__ == "__main__":
    main()
