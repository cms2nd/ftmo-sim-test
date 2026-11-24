"""Famille ORB paramétrable (base des variantes orb_v2/v3/v4 et de la référence orb_ref).

Paramètres :
  RR          ratio gain/risque de l'objectif (≥ 1,5)
  STOP_MODE   "or"  = autre côté du range (comme aggressive_v1)
              "mid" = milieu du range
              "atr" = STOP_ATR × ATR journalier depuis l'entrée
  TREND       "prev" = au-dessus/au-dessous de la clôture de la veille
              "sma"  = idem et du bon côté de la moyenne 20 jours
              "none"
  ENTRY       "close"  = à la clôture de la bougie de cassure
              "retest" = cassure confirmée, puis ordre limite au niveau cassé
  OR_ATR_MIN / OR_ATR_MAX : filtre de largeur du range en ATR
"""
from strategies._common import SessionStrategy


class OrbFamily(SessionStrategy):
    RR = 2.0
    STOP_MODE = "or"
    STOP_ATR = 0.25
    TREND = "prev"
    ENTRY = "close"
    OR_ATR_MIN = 0.08
    OR_ATR_MAX = 0.60

    def _trend_ok(self, x, price, side):
        if self.TREND == "none":
            return True
        up = price > x["prev_close"]
        if self.TREND == "sma":
            if x["sma"] is None:
                return False
            up_s = price > x["sma"]
            return (up and up_s) if side == "long" else (not up and not up_s)
        return up if side == "long" else not up

    def _stop(self, x, side, entry):
        if self.STOP_MODE == "mid":
            return (x["or_hi"] + x["or_lo"]) / 2
        if self.STOP_MODE == "atr":
            d = self.STOP_ATR * x["atr"]
            return entry - d if side == "long" else entry + d
        return x["or_lo"] if side == "long" else x["or_hi"]

    def signal(self, sym, close_ts, bar, mem):
        c = self.ctx(sym, close_ts)
        if not c:
            return None
        x, mins, date = c
        key = f"{sym}:{date}"
        st = mem.get(key)
        if st == "done":
            return None
        width = x["or_hi"] - x["or_lo"]
        if not (self.OR_ATR_MIN * x["atr"] <= width <= self.OR_ATR_MAX * x["atr"]):
            return None
        if self.ENTRY == "retest":
            if st in ("brk_long", "brk_short"):
                side = "long" if st == "brk_long" else "short"
                lvl = x["or_hi"] if side == "long" else x["or_lo"]
                touched = bar["low"] <= lvl if side == "long" else bar["high"] >= lvl
                if touched:
                    mem[key] = "done"
                    stop = self._stop(x, side, lvl)
                    r = abs(lvl - stop)
                    if r <= 0 or (side == "long" and stop >= lvl) or (side == "short" and stop <= lvl):
                        return None
                    tgt = lvl + self.RR * r if side == "long" else lvl - self.RR * r
                    return {"side": side, "entry": lvl, "stop": stop, "target": tgt, "tag": "ORB-retest"}
                return None
            if bar["close"] > x["or_hi"] and self._trend_ok(x, bar["close"], "long"):
                mem[key] = "brk_long"
            elif bar["close"] < x["or_lo"] and self._trend_ok(x, bar["close"], "short"):
                mem[key] = "brk_short"
            return None
        cl = bar["close"]
        for side, cond in (("long", cl > x["or_hi"]), ("short", cl < x["or_lo"])):
            if cond and self._trend_ok(x, cl, side):
                mem[key] = "done"
                stop = self._stop(x, side, cl)
                r = abs(cl - stop)
                if r <= 0 or (side == "long" and stop >= cl) or (side == "short" and stop <= cl):
                    return None
                tgt = cl + self.RR * r if side == "long" else cl - self.RR * r
                return {"side": side, "stop": stop, "target": tgt, "tag": "ORB"}
        return None
