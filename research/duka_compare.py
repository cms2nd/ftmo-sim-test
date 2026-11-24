"""Compare les backtests sur données Yahoo (spread fixe) et Dukascopy (ticks bid/ask, spread réel).

Écrit docs/research/duka_compare.json et docs/research/duka.md (inclus dans RAPPORT.md).
Usage : python -m research.duka_compare
"""
import copy
import json
import os

import pandas as pd

import backtest as B
from research.walkforward import stats
from sim import config as C
from sim.data import load_cache, load_duka

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRATS = ["aggressive_v1", "orb_ref", "orb_v4_trend", "orb_v2_tight"]
START, END = "2026-09-21", "2026-11-20"


def spread_table(duka):
    rows = []
    for sym, df in duka.items():
        if df.empty:
            continue
        sess = C.INSTRUMENTS[sym]["session"]
        tz = C.NY if sess == "NY" else C.LONDON
        loc = df.index.tz_convert(tz)
        m = loc.hour * 60 + loc.minute
        o = 9 * 60 + 30 if sess == "NY" else 8 * 60
        open_win = df[(m >= o) & (m < o + 120)]["spread"]
        rows.append(dict(sym=sym, median=float(df["spread"].median()), p90=float(df["spread"].quantile(0.9)),
                         open_median=float(open_win.median()) if len(open_win) else None,
                         config=C.INSTRUMENTS[sym]["spread"]))
    return rows


def main():
    duka = {s: load_duka(s) for s in C.INSTRUMENTS}
    yahoo = {s: load_cache(s, "5m") for s in C.INSTRUMENTS}
    res = {"spreads": spread_table(duka), "runs": []}
    for name in STRATS:
        for label, data, strip in (("Yahoo, spread fixe pessimiste", yahoo, False),
                                   ("Dukascopy, spread réel", duka, False),
                                   ("Dukascopy, spread fixe pessimiste", duka, True)):
            d = {s: (df.drop(columns=["spread"]) if strip and "spread" in df else df) for s, df in data.items()}
            r = B.run(name, start=START, end=END, interval="5m", data=d)
            st = stats(r["trades"])
            res["runs"].append(dict(strategy=name, data=label, **st, pnl=r["net_pnl"],
                                    n_pass=r["n_pass"], n_completed=r["n_completed"]))
            print(name, label, st, r["net_pnl"], flush=True)
    with open(os.path.join(ROOT, "docs", "research", "duka_compare.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    main()
