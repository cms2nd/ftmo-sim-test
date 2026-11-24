"""Walk-forward sur 2 ans de bougies 1 h (Yahoo, gratuit).

Pour chaque stratégie de recherche :
  * 8 plis trimestriels : ajustement sur les 6 mois précédents (choix de la meilleure
    combinaison de GRID par R total, ≥ 20 trades), test sur les 3 mois suivants.
  * Les trades hors échantillon (test) sont concaténés -> espérance réelle.
  * Une simulation FTMO continue sur toute la période hors échantillon, en changeant de
    paramètres à chaque pli, sans limite de temps : challenges successifs (nouvelle
    tentative après réussite, échec ou blocage). Mêmes règles, frais et coupe-circuits.

Usage : python -m research.walkforward [strat1,strat2,...]
"""
import json
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd

import backtest as B
from sim import config as C
from sim.data import load_cache
from strategies.base import load

STRATS = ["orb_ref", "orb_v2_tight", "orb_v3_retest", "orb_v4_trend", "mr_v1"]
TEST_STARTS = ["2025-01-01", "2025-04-01", "2025-07-01", "2025-10-01",
               "2026-01-01", "2026-04-01", "2026-07-01", "2026-10-01"]
DATA_END = "2026-11-20"
INTERVAL = "60m"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research")


def folds():
    out = []
    for i, ts in enumerate(TEST_STARTS):
        d = date.fromisoformat(ts)
        tr_start = (pd.Timestamp(d) - pd.DateOffset(months=6)).date().isoformat()
        tr_end = (d - timedelta(days=1)).isoformat()
        te_end = ((date.fromisoformat(TEST_STARTS[i + 1]) - timedelta(days=1)).isoformat()
                  if i + 1 < len(TEST_STARTS) else DATA_END)
        out.append((tr_start, tr_end, ts, te_end))
    return out


def stats(trades):
    r = [t["pnl"] / C.RISK_PER_TRADE for t in trades]
    if not r:
        return dict(n=0, exp_R=None, win=None, pf=None, tot_R=0)
    gp, gl = sum(x for x in r if x > 0), -sum(x for x in r if x < 0)
    return dict(n=len(r), exp_R=round(float(sum(r) / len(r)), 3), win=round(sum(1 for x in r if x > 0) / len(r), 3),
                pf=round(float(gp / gl), 2) if gl else None, tot_R=round(float(sum(r)), 1))


class Switching:
    """Change de paramètres à chaque pli (paramètres choisis sur le passé uniquement)."""

    def __init__(self, name, plan):
        self.plan = []  # (start_iso, end_iso, instance)
        for (s, e, p) in plan:
            inst = load(name)
            for k, v in p.items():
                setattr(inst, k, v)
            self.plan.append((s, e, inst))
        self.instruments = self.plan[0][2].instruments
        self.name = name + "_wf"

    def _pick(self, ts):
        d = ts.astimezone(C.PRAGUE).date().isoformat()
        for s, e, inst in self.plan:
            if s <= d <= e:
                return inst
        return self.plan[-1][2]

    def prepare(self, data):
        for _, _, inst in self.plan:
            inst.bar_minutes = self.bar_minutes
            inst.prepare(data)

    def signal(self, sym, ts, bar, mem):
        return self._pick(ts).signal(sym, ts, bar, mem)

    def exit_now(self, sym, ts, pos):
        return self._pick(ts).exit_now(sym, ts, pos)


def main(names):
    os.makedirs(OUT, exist_ok=True)
    data = {s: load_cache(s, INTERVAL) for s in C.INSTRUMENTS}
    summary = {}
    for name in names:
        t0 = time.time()
        grid = load(name).GRID or [{}]
        plan, oos_trades, fold_rows = [], [], []
        for tr_s, tr_e, te_s, te_e in folds():
            best, best_score = None, None
            for p in grid:
                r = B.run(name, start=tr_s, end=tr_e, params=p, interval=INTERVAL, data=data)
                st = stats(r["trades"])
                score = st["tot_R"] if st["n"] >= 20 else -1e9
                if best_score is None or score > best_score:
                    best, best_score, best_st = p, score, st
            rt = B.run(name, start=te_s, end=te_e, params=best, interval=INTERVAL, data=data)
            st_te = stats(rt["trades"])
            oos_trades += rt["trades"]
            plan.append((te_s, te_e, best))
            fold_rows.append(dict(train=f"{tr_s} → {tr_e}", test=f"{te_s} → {te_e}", params=best,
                                  train_R=best_st["tot_R"], train_n=best_st["n"],
                                  test_R=st_te["tot_R"], test_n=st_te["n"], test_exp=st_te["exp_R"]))
            print(f"  {name} {te_s}: params={best} train R={best_st['tot_R']} | test R={st_te['tot_R']} (n={st_te['n']})", flush=True)
        # Simulation FTMO continue hors échantillon, paramètres changeant à chaque pli
        sw = Switching(name, plan)
        ch = B.run(strategy=sw, start=TEST_STARTS[0], end=DATA_END, interval=INTERVAL, data=data)
        summary[name] = dict(oos=stats(oos_trades), folds=fold_rows,
                             challenge={k: ch[k] for k in ("n_completed", "n_pass", "n_fail", "pass_rate", "pass_rate_3d",
                                                           "avg_days_pass", "avg_days_fail", "fail_causes", "fees_usd",
                                                           "fee_per_attempt_usd", "expected_payout_per_attempt_usd",
                                                           "trading_days", "first_day", "last_day")},
                             attempts=ch["attempts"], curve=ch["curve"])
        print(f"== {name}: OOS {summary[name]['oos']} | challenges {ch['n_pass']}/{ch['n_completed']} "
              f"({time.time() - t0:.0f}s)", flush=True)
        with open(os.path.join(OUT, f"wf_{name}.json"), "w") as f:
            json.dump(summary[name], f, ensure_ascii=False, default=str)
    return summary


if __name__ == "__main__":
    main(sys.argv[1].split(",") if len(sys.argv) > 1 else STRATS)
