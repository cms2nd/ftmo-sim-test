"""orb_v4_trend figée pour le test en direct parallèle.

Paramètres et instruments = dernier pli du walk-forward 1 an sur prix broker (research/wf_duka.py,
ajustement juillet → octobre 2026) : stop à l'autre bord du range, objectif 3 R, filtre de tendance
(clôture de la veille ET moyenne 20 jours), instruments EURUSD, GER40, XAUUSD.
"""
from strategies.orb_v4_trend import Strategy as _Base


class Strategy(_Base):
    name = "orb_v4_live"
    STOP_MODE = "or"
    RR = 3.0
    instruments = ["EURUSD", "GER40", "XAUUSD"]
