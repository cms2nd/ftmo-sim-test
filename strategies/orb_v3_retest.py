"""ORB avec entrée sur retest : cassure confirmée en clôture, puis ordre limite au niveau cassé."""
from strategies._orb_family import OrbFamily


class Strategy(OrbFamily):
    name = "orb_v3_retest"
    ENTRY = "retest"
    ENTRY_WINDOW_MIN = 240  # laisser le temps au retest (en 1 h, 120 min = 1 seule bougie)
    STOP_MODE = "mid"
    RR = 2.0
    GRID = [dict(STOP_MODE=m, STOP_ATR=k, RR=rr)
            for m, k in (("mid", 0.0), ("atr", 0.2))
            for rr in (1.5, 2.0, 3.0)]
