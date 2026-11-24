"""aggressive_v1 — Cassure du range d'ouverture (Opening Range Breakout).

Inspirée du setup `orb` du skill day-trader-skill (trader-scanner / trader-entry:
range = premières minutes de séance en bougies 5 min, entrée à la clôture d'une
bougie au-delà du range), transposée aux CFD FTMO et aux sessions de Londres/NY.

Règles:
  * Range d'ouverture: OR_MINUTES minutes après l'ouverture de la session
    (Londres 08:00 heure de Londres; New York 09:30 heure de New York).
  * Entrée: clôture d'une bougie 5 min au-dessus du plus haut (achat) ou sous
    le plus bas (vente) du range, au plus tard ENTRY_WINDOW_MIN après l'ouverture.
    Une seule tentative par instrument et par jour.
  * Filtre de tendance: achat seulement si le prix est au-dessus de la clôture
    de la veille, vente seulement s'il est en dessous.
  * Filtre de volatilité: largeur du range comprise entre OR_ATR_MIN et
    OR_ATR_MAX fois l'ATR(14) journalier.
  * Stop: de l'autre côté du range (placé dès l'ouverture). Objectif: RR × risque.
  * Sortie forcée en fin de session (et à 21:45 heure de Prague par le moteur).
"""
from datetime import timedelta

import pandas as pd

from sim import config as C
from strategies.base import BaseStrategy

SESSIONS = {
    "NY": dict(tz=C.NY, open=(9, 30), exit=(15, 50)),
    "LDN": dict(tz=C.LONDON, open=(8, 0), exit=(16, 0)),
}


class Strategy(BaseStrategy):
    name = "aggressive_v1"
    # Choix après backtest (voir RAPPORT.md)
    instruments = ["US100", "GER40", "EURUSD"]

    OR_MINUTES = 15
    ENTRY_WINDOW_MIN = 120
    RR = 2.0
    OR_ATR_MIN = 0.08
    OR_ATR_MAX = 0.60

    def __init__(self, **params):
        for k, v in params.items():
            setattr(self, k, v)
        self.feat = {}

    def prepare(self, data):
        self.feat = {}
        for sym, df in data.items():
            if sym not in C.INSTRUMENTS or df.empty:
                continue
            sess = SESSIONS[C.INSTRUMENTS[sym]["session"]]
            loc = df.index.tz_convert(sess["tz"])
            d = df.copy()
            d["date"] = loc.date
            d["mins"] = loc.hour * 60 + loc.minute
            o = sess["open"][0] * 60 + sess["open"][1]
            daily = d.groupby("date").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
            prev_close = daily["close"].shift(1)
            tr = pd.concat([daily["high"] - daily["low"], (daily["high"] - prev_close).abs(),
                            (daily["low"] - prev_close).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14, min_periods=5).mean().shift(1)  # ATR connue avant la séance
            in_or = d[(d["mins"] >= o) & (d["mins"] < o + self.OR_MINUTES)]
            orr = in_or.groupby("date").agg(or_hi=("high", "max"), or_lo=("low", "min"), n=("high", "size"))
            orr = orr[orr["n"] >= max(1, self.OR_MINUTES // 5 - 1)]
            f = {}
            for date, row in orr.iterrows():
                f[date] = dict(or_hi=row.or_hi, or_lo=row.or_lo, prev_close=prev_close.get(date),
                               atr=atr.get(date))
            self.feat[sym] = (sess, o, f)

    def signal(self, sym, close_ts, bar, mem):
        if sym not in self.instruments or sym not in self.feat:
            return None
        sess, o, f = self.feat[sym]
        lt = close_ts.astimezone(sess["tz"])
        mins = lt.hour * 60 + lt.minute
        if not (o + self.OR_MINUTES < mins <= o + self.ENTRY_WINDOW_MIN):
            return None
        date = lt.date()
        key = f"{sym}:{date}"
        if mem.get(key) or date not in f:
            return None
        x = f[date]
        if x["prev_close"] is None or x["atr"] is None or pd.isna(x["atr"]) or pd.isna(x["prev_close"]):
            return None
        width = x["or_hi"] - x["or_lo"]
        if not (self.OR_ATR_MIN * x["atr"] <= width <= self.OR_ATR_MAX * x["atr"]):
            return None
        c = bar["close"]
        if c > x["or_hi"] and c > x["prev_close"]:
            stop = x["or_lo"]
            risk = c - stop
            mem[key] = "long"
            return {"side": "long", "stop": stop, "target": c + self.RR * risk, "tag": "ORB"}
        if c < x["or_lo"] and c < x["prev_close"]:
            stop = x["or_hi"]
            risk = stop - c
            mem[key] = "short"
            return {"side": "short", "stop": stop, "target": c - self.RR * risk, "tag": "ORB"}
        return None

    def exit_now(self, sym, close_ts, position):
        sess = SESSIONS[C.INSTRUMENTS[sym]["session"]]
        lt = close_ts.astimezone(sess["tz"])
        return (lt.hour, lt.minute) >= sess["exit"]
