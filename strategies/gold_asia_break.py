"""Or : prolongement après le premier franchissement du range asiatique pendant la séance de Londres.

Issue de l'étude d'événements research/smc_events.py (année de développement 2025-11 → 2026-11) :
contrairement à la thèse SMC (« balayage de liquidité puis retournement »), un premier franchissement
du plus haut / plus bas asiatique entre 07:00 et 10:00 (Londres) est suivi, en moyenne, d'un
prolongement dans le même sens jusqu'à la clôture de New York (+0,10 ATR, t ≈ 2,3, 163 cas),
cohérent avec les cascades d'ordres stop décrites par Osler (Fed de New York).

Règles :
  - range asiatique = plus haut / plus bas 00:00-07:00 (heure de Londres) ;
  - premier franchissement d'un des deux bords entre 07:00 et 10:00 (si le range a déjà été
    franchi plus tôt, pas de trade ce jour-là) ;
  - entrée dans le sens du franchissement à la clôture de la 3e bougie (15 min), que le prix soit
    revenu dans le range ou non ;
  - stop : STOP_ATR × ATR journalier ; objectif : RR × risque (RR élevé = laisser courir) ;
  - sortie à 15:50 New York au plus tard ; 1 trade par jour maximum.
"""
import pandas as pd

from sim import config as C
from strategies.base import BaseStrategy


class Strategy(BaseStrategy):
    name = "gold_asia_break"
    instruments = ["XAUUSD"]
    bar_minutes = 5
    CONFIRM_BARS = 3
    STOP_ATR = 0.5
    RR = 4.0
    GRID = [dict(STOP_ATR=s, RR=r) for s in (0.3, 0.5, 0.8) for r in (2.0, 4.0)]

    def __init__(self, **params):
        for k, v in params.items():
            setattr(self, k, v)
        self.f = {}

    def prepare(self, data):
        self.f = {}
        df = data.get("XAUUSD")
        if df is None or df.empty:
            return
        d = df[["high", "low", "close"]].copy()
        ldn = d.index.tz_convert(C.LONDON)
        d["ldate"] = ldn.date
        d["lm"] = ldn.hour * 60 + ldn.minute
        asia = d[d["lm"] < 420].groupby("ldate").agg(a_hi=("high", "max"), a_lo=("low", "min"))
        daily = d.groupby("ldate").agg(hi=("high", "max"), lo=("low", "min"), cl=("close", "last"))
        pc = daily["cl"].shift(1)
        tr = pd.concat([daily["hi"] - daily["lo"], (daily["hi"] - pc).abs(), (daily["lo"] - pc).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14, min_periods=5).mean().shift(1).rename("atr")
        self.f = d.join(asia, on="ldate").join(atr, on="ldate")

    def signal(self, sym, close_ts, bar, mem):
        if sym != "XAUUSD" or self.f is None or len(self.f) == 0:
            return None
        ts = pd.Timestamp(close_ts) - pd.Timedelta(minutes=self.bar_minutes)
        try:
            r = self.f.loc[ts]
        except KeyError:
            return None
        if pd.isna(r["a_hi"]) or pd.isna(r["atr"]) or r["lm"] < 420:
            return None
        day = str(r["ldate"])
        st = mem.get("gab")
        if not st or st.get("day") != day:
            st = {"day": day, "state": "watch"}
            mem["gab"] = st
        if st["state"] == "done":
            return None
        if st["state"] == "watch":
            up, dn = r["high"] > r["a_hi"], r["low"] < r["a_lo"]
            if not (up or dn):
                return None
            if r["lm"] >= 600 or (up and dn):
                st["state"] = "done"      # franchi hors fenêtre ou des deux côtés : pas de trade
                return None
            st.update(state="armed", side="long" if up else "short", age=1)
            return None
        st["age"] += 1
        if st["age"] < self.CONFIRM_BARS:
            return None
        st["state"] = "done"
        side, cl, atr = st["side"], float(r["close"]), float(r["atr"])
        risk = self.STOP_ATR * atr
        stop = cl - risk if side == "long" else cl + risk
        tgt = cl + self.RR * risk if side == "long" else cl - self.RR * risk
        return {"side": side, "stop": stop, "target": tgt, "tag": "ASIA-BRK"}

    def exit_now(self, sym, close_ts, position):
        lt = close_ts.astimezone(C.NY)
        return (lt.hour, lt.minute) >= (15, 50)
