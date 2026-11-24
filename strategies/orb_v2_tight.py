"""ORB avec stop plus serré (milieu du range ou fraction d'ATR) et objectif 1,5–2 R."""
from strategies._orb_family import OrbFamily


class Strategy(OrbFamily):
    name = "orb_v2_tight"
    STOP_MODE = "mid"
    RR = 1.5
    GRID = [dict(STOP_MODE=m, STOP_ATR=k, RR=rr)
            for m, k in (("mid", 0.0), ("atr", 0.15), ("atr", 0.25))
            for rr in (1.5, 2.0)]
