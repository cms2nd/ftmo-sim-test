"""Briques communes aux stratégies de recherche (indépendantes de l'unité de temps).

Pour chaque instrument et chaque jour de séance (heure locale de la session) :
  or_hi / or_lo  : plus haut / plus bas du range d'ouverture
  s_open         : prix d'ouverture de la séance
  prev_close     : clôture de la veille
  atr            : ATR(14) journalier connu avant la séance
  sma            : moyenne des clôtures journalières sur SMA_DAYS jours (connue avant la séance)
Le range d'ouverture couvre les bougies qui commencent dans
[ouverture arrondie à la bougie, + max(or_minutes, durée d'une bougie)).
En 1 h, New York (ouverture 9:30) utilise donc la bougie 9:00–10:00 ET.
"""
import math

import pandas as pd

from sim import config as C
from strategies.base import BaseStrategy

SESSIONS = {
    "NY": dict(tz=C.NY, open=(9, 30), exit=(15, 50)),
    "LDN": dict(tz=C.LONDON, open=(8, 0), exit=(16, 0)),
}


class SessionStrategy(BaseStrategy):
    instruments = ["US100", "US30", "XAUUSD", "GER40", "EURUSD", "GBPUSD"]
    bar_minutes = 5
    OR_MINUTES = 15
    ENTRY_WINDOW_MIN = 120
    SMA_DAYS = 20
    GRID = []  # liste de dicts de paramètres testés en walk-forward

    def __init__(self, **params):
        for k, v in params.items():
            setattr(self, k, v)
        self.feat = {}

    # ---------------------------------------------------------------- utils
    def session(self, sym):
        return SESSIONS[C.INSTRUMENTS[sym]["session"]]

    def or_bounds(self, sym):
        sess = self.session(sym)
        o = sess["open"][0] * 60 + sess["open"][1]
        start = (o // self.bar_minutes) * self.bar_minutes
        end = start + max(self.OR_MINUTES, self.bar_minutes)
        return o, start, end

    def prepare(self, data):
        self.feat = {}
        for sym, df in data.items():
            if df.empty:
                continue
            sess = self.session(sym)
            loc = df.index.tz_convert(sess["tz"])
            d = df.copy()
            d["date"] = loc.date
            d["mins"] = loc.hour * 60 + loc.minute
            o, st, en = self.or_bounds(sym)
            daily = d.groupby("date").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
            pc = daily["close"].shift(1)
            tr = pd.concat([daily["high"] - daily["low"], (daily["high"] - pc).abs(), (daily["low"] - pc).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14, min_periods=5).mean().shift(1)
            sma = daily["close"].rolling(self.SMA_DAYS, min_periods=self.SMA_DAYS).mean().shift(1)
            orb = d[(d["mins"] >= st) & (d["mins"] < en)]
            g = orb.groupby("date").agg(or_hi=("high", "max"), or_lo=("low", "min"), s_open=("open", "first"))
            f = {}
            for date, r in g.iterrows():
                a, p, m = atr.get(date), pc.get(date), sma.get(date)
                if a is None or p is None or pd.isna(a) or pd.isna(p):
                    continue
                f[date] = dict(or_hi=r.or_hi, or_lo=r.or_lo, s_open=r.s_open, prev_close=p, atr=a,
                               sma=None if m is None or pd.isna(m) else m)
            self.feat[sym] = (sess, en, f)

    def ctx(self, sym, close_ts):
        """Renvoie (features du jour, minutes locales à la clôture, date) ou None hors fenêtre d'entrée."""
        if sym not in self.instruments or sym not in self.feat:
            return None
        sess, or_end, f = self.feat[sym]
        lt = close_ts.astimezone(sess["tz"])
        mins = lt.hour * 60 + lt.minute
        o = sess["open"][0] * 60 + sess["open"][1]
        if not (or_end < mins <= max(or_end + self.bar_minutes, o + self.ENTRY_WINDOW_MIN)):
            return None
        date = lt.date()
        if date not in f:
            return None
        return f[date], mins, date

    def exit_now(self, sym, close_ts, position):
        sess = self.session(sym)
        lt = close_ts.astimezone(sess["tz"])
        return (lt.hour, lt.minute) >= sess["exit"]
