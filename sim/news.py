"""Calendrier des annonces macro majeures (NFP, CPI, Fed, BCE), heures en UTC.

Liste codée à la main: NFP = 1er vendredi du mois 13:30 UTC (12:30 en été US) généré
automatiquement; CPI / FOMC / BCE listés explicitement. Les dates explicites sont
à vérifier (calendrier officiel) : c'est une limite documentée du test.
"""
from datetime import datetime, timedelta, timezone, date
from .config import NY

EXPLICIT_UTC = [
    # FOMC (décision 14:00 New York)
    ("2026-09-16 14:00", "NY", "FOMC"), ("2026-10-28 14:00", "NY", "FOMC"), ("2026-12-09 14:00", "NY", "FOMC"),
    # BCE (décision 14:15 Francfort)
    ("2026-09-10 14:15", "FRA", "BCE"), ("2026-10-29 14:15", "FRA", "BCE"), ("2026-12-17 14:15", "FRA", "BCE"),
    # CPI US (08:30 New York)
    ("2026-09-11 08:30", "NY", "CPI"), ("2026-10-14 08:30", "NY", "CPI"), ("2026-11-12 08:30", "NY", "CPI"),
    ("2026-12-10 08:30", "NY", "CPI"),
]


def _events():
    from zoneinfo import ZoneInfo
    out = []
    for s, tz, name in EXPLICIT_UTC:
        z = NY if tz == "NY" else ZoneInfo("Europe/Berlin")
        out.append((datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=z).astimezone(timezone.utc), name))
    for y in (2026, 2027):
        for m in range(1, 13):
            d = date(y, m, 1)
            while d.weekday() != 4:
                d += timedelta(days=1)
            out.append((datetime(d.year, d.month, d.day, 8, 30, tzinfo=NY).astimezone(timezone.utc), "NFP"))
    return sorted(out)


EVENTS = _events()


def blackout(ts_utc, minutes):
    """Renvoie le nom de l'annonce si ts est à moins de `minutes` d'une annonce."""
    for t, name in EVENTS:
        if abs((ts_utc - t).total_seconds()) <= minutes * 60:
            return name
    return None
