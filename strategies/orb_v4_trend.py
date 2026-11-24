"""ORB filtré par la tendance de fond : prix du bon côté de la clôture de la veille ET de la moyenne 20 jours."""
from strategies._orb_family import OrbFamily


class Strategy(OrbFamily):
    name = "orb_v4_trend"
    TREND = "sma"
    GRID = [dict(STOP_MODE=m, STOP_ATR=k, RR=rr)
            for m, k in (("or", 0.0), ("mid", 0.0))
            for rr in (1.5, 2.0, 3.0)]
