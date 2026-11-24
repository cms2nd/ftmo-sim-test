"""Référence : mêmes règles qu'aggressive_v1 (stop de l'autre côté du range, RR 2,
filtre clôture de la veille), mais sur les 6 instruments et toute unité de temps."""
from strategies._orb_family import OrbFamily


class Strategy(OrbFamily):
    name = "orb_ref"
    GRID = [dict(RR=2.0)]
