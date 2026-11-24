"""SMC mécanique sur l'or (XAUUSD) : balayage de liquidité -> cassure de structure -> retour dans le FVG.

Fondement : les ordres stop s'accumulent juste au-delà des niveaux évidents (Osler, Fed de New York,
2002-2005). Quand le prix les déclenche puis revient aussitôt à l'intérieur, le mouvement est
souvent un « balayage » plutôt qu'une vraie cassure. Les notions SMC (order block, FVG, MSS) n'ont
aucune validation académique : elles sont ici définies de façon strictement mécanique pour être testées.

Définitions (toutes calculées sans regarder le futur) :
  niveaux de liquidité  plus haut / plus bas de la séance asiatique (00:00-07:00 Londres) du jour,
                        plus haut / plus bas de la veille (PDH / PDL)
  fenêtres (killzones)  Londres 07:00-10:00 (heure de Londres), New York 08:30-11:00 (heure de NY)
  balayage              une bougie dépasse le niveau, puis une clôture revient de l'autre côté
                        dans les SWEEP_BARS bougies ; l'extrême atteint est mémorisé
  cassure (MSS)         clôture au-delà du dernier creux (ou sommet) de swing (fractale à 2 bougies)
                        dans les MSS_BARS bougies suivant le balayage
  FVG                   trou entre la bougie i-2 et la bougie i dans la jambe de cassure
  entrée                ENTRY="fvg"  : ordre limite au bord du FVG le plus proche, valable ENTRY_EXPIRY bougies
                        ENTRY="mss"  : à la clôture de la bougie de cassure
  stop                  extrême du balayage + STOP_BUF × ATR journalier
  objectif              TARGET="rr"  : RR × risque
                        TARGET="liq" : niveau de liquidité opposé (autre bord du range asiatique), si RR ≥ MIN_RR
  biais                 BIAS="none" | "trend" (ventes sous la moyenne 20 jours et la clôture de la veille, achats au-dessus)
Une seule position par jour (MAX_PER_DAY). Sortie forcée à 15:50 New York au plus tard.
"""
import pandas as pd

from sim import config as C
from strategies.base import BaseStrategy


class Strategy(BaseStrategy):
    name = "smc_gold"
    instruments = ["XAUUSD"]
    bar_minutes = 5
    SWEEP_BARS = 3
    MSS_BARS = 12
    ENTRY = "fvg"
    ENTRY_EXPIRY = 12
    STOP_BUF = 0.02
    TARGET = "rr"
    RR = 2.0
    MIN_RR = 1.5
    BIAS = "none"
    LEVELS = "asia+pd"     # "asia", "pd", "asia+pd"
    KILLZONES = "ldn+ny"   # "ldn", "ny", "ldn+ny"
    MAX_PER_DAY = 1
    MIN_RISK_ATR = 0.03    # évite les stops minuscules (bruit / spread)
    GRID = [dict(ENTRY=e, TARGET=t, RR=rr, BIAS=b)
            for e in ("fvg", "mss") for t, rr in (("rr", 2.0), ("rr", 3.0), ("liq", 2.0)) for b in ("none", "trend")]

    def __init__(self, **params):
        for k, v in params.items():
            setattr(self, k, v)
        self.f = {}

    # ------------------------------------------------------------ features
    def prepare(self, data):
        self.f = {}
        for sym, df in data.items():
            if sym not in self.instruments or df.empty:
                continue
            d = df[["open", "high", "low", "close"]].copy()
            ldn = d.index.tz_convert(C.LONDON)
            ny = d.index.tz_convert(C.NY)
            d["ldate"] = ldn.date
            lm = ldn.hour * 60 + ldn.minute
            nm = ny.hour * 60 + ny.minute
            d["kz_ldn"] = (lm >= 7 * 60) & (lm < 10 * 60)
            d["kz_ny"] = (nm >= 8 * 60 + 30) & (nm < 11 * 60)
            asia = d[lm < 7 * 60].groupby("ldate").agg(a_hi=("high", "max"), a_lo=("low", "min"))
            daily = d.groupby("ldate").agg(hi=("high", "max"), lo=("low", "min"), cl=("close", "last"))
            pc = daily["cl"].shift(1)
            tr = pd.concat([daily["hi"] - daily["lo"], (daily["hi"] - pc).abs(), (daily["lo"] - pc).abs()], axis=1).max(axis=1)
            lv = pd.DataFrame({"pdh": daily["hi"].shift(1), "pdl": daily["lo"].shift(1), "pc": pc,
                               "atr": tr.rolling(14, min_periods=5).mean().shift(1),
                               "sma": daily["cl"].rolling(20, min_periods=20).mean().shift(1)}).join(asia)
            d = d.join(lv, on="ldate")
            # fractales confirmées : swing haut à i-2 connu à la clôture de i
            h, l = d["high"], d["low"]
            sh = (h.shift(2) > h.shift(3)) & (h.shift(2) > h.shift(4)) & (h.shift(2) > h.shift(1)) & (h.shift(2) > h)
            sl = (l.shift(2) < l.shift(3)) & (l.shift(2) < l.shift(4)) & (l.shift(2) < l.shift(1)) & (l.shift(2) < l)
            d["swing_hi"] = h.shift(2).where(sh).ffill()
            d["swing_lo"] = l.shift(2).where(sl).ffill()
            d["fvg_bear"] = l.shift(2) > h          # trou baissier : bas de i-2 au-dessus du haut de i
            d["fvg_bull"] = h.shift(2) < l
            d["h2"], d["l2"] = h.shift(2), l.shift(2)
            self.f[sym] = d

    def _row(self, sym, close_ts):
        d = self.f.get(sym)
        if d is None:
            return None
        ts = pd.Timestamp(close_ts) - pd.Timedelta(minutes=self.bar_minutes)
        try:
            return d.loc[ts]
        except KeyError:
            return None

    # ------------------------------------------------------------ logique
    def _in_kz(self, r):
        return (("ldn" in self.KILLZONES and r["kz_ldn"]) or ("ny" in self.KILLZONES and r["kz_ny"]))

    def _levels(self, r):
        hi, lo = [], []
        if "asia" in self.LEVELS and pd.notna(r["a_hi"]):
            hi.append(r["a_hi"]); lo.append(r["a_lo"])
        if "pd" in self.LEVELS and pd.notna(r["pdh"]):
            hi.append(r["pdh"]); lo.append(r["pdl"])
        return hi, lo

    def _bias_ok(self, r, side):
        if self.BIAS == "none":
            return True
        if pd.isna(r["sma"]) or pd.isna(r["pc"]):
            return False
        up = r["close"] > r["sma"] and r["close"] > r["pc"]
        dn = r["close"] < r["sma"] and r["close"] < r["pc"]
        return up if side == "long" else dn

    def signal(self, sym, close_ts, bar, mem):
        r = self._row(sym, close_ts)
        if r is None or pd.isna(r["atr"]):
            return None
        day = str(r["ldate"])
        key = f"smc:{sym}"
        st = mem.get(key)
        if not st or st.get("day") != day:
            st = {"day": day, "n": 0, "phase": "idle", "probe": None}
        mem[key] = st
        atr = float(r["atr"])
        hi, lo = float(r["high"]), float(r["low"])
        cl = float(r["close"])
        prev_hi, prev_lo = st.get("run_hi"), st.get("run_lo")   # extrêmes du jour AVANT cette bougie
        st["run_hi"] = hi if prev_hi is None else max(prev_hi, hi)
        st["run_lo"] = lo if prev_lo is None else min(prev_lo, lo)
        if st["n"] >= self.MAX_PER_DAY:
            return None

        # 1) ordre limite en attente dans un FVG
        if st["phase"] == "pending":
            st["age"] += 1
            side, lvl, stop, tgt = st["side"], st["entry"], st["stop"], st["target"]
            hit_stop = hi >= stop if side == "short" else lo <= stop
            hit_tgt = lo <= tgt if side == "short" else hi >= tgt
            touched = hi >= lvl if side == "short" else lo <= lvl
            if touched and not hit_tgt:
                st["phase"], st["n"] = "idle", st["n"] + 1
                return {"side": side, "entry": lvl, "stop": stop, "target": tgt, "tag": "SMC-FVG"}
            if hit_stop or hit_tgt or st["age"] >= self.ENTRY_EXPIRY:
                st["phase"] = "idle"
            return None

        # 2) balayage en cours : attente de la cassure de structure
        if st["phase"] in ("sweep_hi", "sweep_lo"):
            st["age"] += 1
            short = st["phase"] == "sweep_hi"
            st["ext"] = max(st["ext"], hi) if short else min(st["ext"], lo)
            if short and r["fvg_bear"]:
                st["fvg"] = [float(r["high"]), float(r["l2"])]   # bord proche (bas du trou... côté prix actuel), bord éloigné
            if not short and r["fvg_bull"]:
                st["fvg"] = [float(r["low"]), float(r["h2"])]
            mss = (short and pd.notna(r["swing_lo"]) and cl < st["ref_swing"]) or \
                  (not short and pd.notna(r["swing_hi"]) and cl > st["ref_swing"])
            if mss:
                side = "short" if short else "long"
                st["phase"] = "idle"
                if not self._bias_ok(r, side):
                    return None
                stop = st["ext"] + self.STOP_BUF * atr if short else st["ext"] - self.STOP_BUF * atr
                if self.ENTRY == "fvg":
                    if not st.get("fvg"):
                        return None
                    entry = st["fvg"][0]
                else:
                    entry = cl
                risk = abs(entry - stop)
                if risk < self.MIN_RISK_ATR * atr or (short and stop <= entry) or (not short and stop >= entry):
                    return None
                if self.TARGET == "liq":
                    tgt = st["opp"]
                    if (short and tgt >= entry) or (not short and tgt <= entry) or abs(entry - tgt) < self.MIN_RR * risk:
                        return None
                else:
                    tgt = entry - self.RR * risk if short else entry + self.RR * risk
                if self.ENTRY == "fvg":
                    st.update(phase="pending", side=side, entry=entry, stop=stop, target=tgt, age=0)
                    return None
                st["n"] += 1
                return {"side": side, "stop": stop, "target": tgt, "tag": "SMC-MSS"}
            if st["age"] > self.MSS_BARS:
                st["phase"] = "idle"
            return None

        # 3) détection d'un balayage (niveau franchi pour la première fois du jour, en killzone)
        his, los = self._levels(r)
        pr = st.get("probe")
        if pr is None and self._in_kz(r) and prev_hi is not None:
            fresh_hi = [v for v in his if prev_hi <= v < hi]
            fresh_lo = [v for v in los if prev_lo >= v > lo]
            if fresh_hi:
                pr = {"dir": "hi", "lvl": float(max(fresh_hi)), "ext": hi, "age": -1}
            elif fresh_lo:
                pr = {"dir": "lo", "lvl": float(min(fresh_lo)), "ext": lo, "age": -1}
        if pr is None:
            return None
        pr["age"] += 1
        short = pr["dir"] == "hi"
        pr["ext"] = max(pr["ext"], hi) if short else min(pr["ext"], lo)
        back = cl < pr["lvl"] if short else cl > pr["lvl"]
        st["probe"] = pr
        if back:
            st["probe"] = None
            ref = r["swing_lo"] if short else r["swing_hi"]
            if pd.notna(ref):
                opp = (min(los) if los else pr["lvl"] - 2 * atr) if short else (max(his) if his else pr["lvl"] + 2 * atr)
                st.update(phase="sweep_hi" if short else "sweep_lo", ext=float(pr["ext"]), ref_swing=float(ref),
                          age=0, fvg=None, opp=float(opp))
        elif pr["age"] >= self.SWEEP_BARS:
            st["probe"] = None   # pas de retour : vraie cassure, pas un balayage
        return None

    def exit_now(self, sym, close_ts, position):
        lt = close_ts.astimezone(C.NY)
        return (lt.hour, lt.minute) >= (15, 50)
