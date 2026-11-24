"""Retour à la moyenne après un excès en début de séance (autre famille que l'ORB).

Si, dans la fenêtre d'entrée, une bougie clôture à plus de EXT_ATR × ATR de l'ouverture
de séance puis se retourne (clôture opposée à son ouverture), on joue le retour vers
l'ouverture de séance. Stop : extrême de la bougie + STOP_PAD × ATR. Objectif : un
retour de TARGET_FRAC de l'excès, pris seulement si gain/risque ≥ 1,5.
"""
from strategies._common import SessionStrategy


class Strategy(SessionStrategy):
    name = "mr_v1"
    ENTRY_WINDOW_MIN = 240
    EXT_ATR = 0.6
    STOP_PAD = 0.1
    TARGET_FRAC = 1.0
    MIN_RR = 1.5
    GRID = [dict(EXT_ATR=e, TARGET_FRAC=t) for e in (0.4, 0.6, 0.8) for t in (0.6, 1.0)]

    def signal(self, sym, close_ts, bar, mem):
        c = self.ctx(sym, close_ts)
        if not c:
            return None
        x, mins, date = c
        key = f"{sym}:{date}"
        if mem.get(key):
            return None
        a, o, cl = x["atr"], x["s_open"], bar["close"]
        ext = cl - o
        if ext >= self.EXT_ATR * a and cl < bar["open"]:
            side, stop = "short", bar["high"] + self.STOP_PAD * a
            tgt = cl - self.TARGET_FRAC * ext
        elif -ext >= self.EXT_ATR * a and cl > bar["open"]:
            side, stop = "long", bar["low"] - self.STOP_PAD * a
            tgt = cl - self.TARGET_FRAC * ext
        else:
            return None
        risk, gain = abs(cl - stop), abs(tgt - cl)
        if risk <= 0 or gain / risk < self.MIN_RR:
            return None
        mem[key] = side
        return {"side": side, "stop": stop, "target": tgt, "tag": "MR"}
