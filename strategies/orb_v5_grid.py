"""ORB élargi pour la recherche sur données broker : durée du range, filtre de tendance et RR testés en walk-forward."""
from strategies._orb_family import OrbFamily


class Strategy(OrbFamily):
    name = "orb_v5_grid"
    GRID = [dict(OR_MINUTES=om, TREND=tr, RR=rr, STOP_MODE=sm)
            for om in (15, 30)
            for tr in ("prev", "sma")
            for rr in (1.5, 2.0, 3.0)
            for sm in ("or", "mid")]
