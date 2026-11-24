"""Walk-forward sur 1 an de bougies 5 min Dukascopy (prix broker, spread réel).

Pour chaque pli (test de 2 mois, ajustement sur les 4 mois précédents) :
  1. pour chaque stratégie candidate et chaque jeu de paramètres de sa GRID, backtest sur l'ajustement ;
  2. sélection des instruments : on ne garde que ceux dont le R d'ajustement est > 0 (≥ 8 trades) ;
  3. on retient la combinaison (stratégie, paramètres, instruments) au meilleur R total (≥ 20 trades),
     après un second backtest d'ajustement limité aux instruments retenus.
Puis simulation FTMO continue sur toute la période de test, avec ce qui a été choisi à chaque pli
(challenges successifs, mêmes frais, règles et coupe-circuits). Rien du test n'est vu à l'ajustement.

Usage : python -m research.wf_duka [strat1,strat2,...]
"""
import json, os, sys, time
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

import backtest as B
from research.walkforward import stats
from sim import config as C
from sim.data import load_duka
from strategies.base import load

CANDIDATES = ["orb_ref", "orb_v2_tight", "orb_v3_retest", "orb_v4_trend", "orb_v5_grid", "mr_v1"]
TEST_STARTS = ["2026-03-01", "2026-05-01", "2026-07-01", "2026-09-01", "2026-11-01"]
DATA_END = "2026-11-20"
TRAIN_MONTHS = 4
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research")


def folds():
    out = []
    for i, ts in enumerate(TEST_STARTS):
        d = date.fromisoformat(ts)
        tr_s = (pd.Timestamp(d) - pd.DateOffset(months=TRAIN_MONTHS)).date().isoformat()
        te_e = ((date.fromisoformat(TEST_STARTS[i + 1]) - timedelta(days=1)).isoformat()
                if i + 1 < len(TEST_STARTS) else DATA_END)
        out.append((tr_s, (d - timedelta(days=1)).isoformat(), ts, te_e))
    return out


def per_sym(trades):
    r = defaultdict(list)
    for t in trades:
        r[t["sym"]].append(t["pnl"] / C.RISK_PER_TRADE)
    return {s: (len(v), sum(v)) for s, v in r.items()}


def make(name, params, instruments):
    inst = load(name)
    for k, v in params.items():
        setattr(inst, k, v)
    inst.instruments = list(instruments)
    return inst


class Plan:
    """Stratégie composite : délègue à l'instance choisie pour le pli courant."""
    name = "wf_duka"

    def __init__(self, plan):
        self.plan = plan  # [(start, end, instance)]
        self.instruments = sorted({s for _, _, i in plan for s in i.instruments})

    def _pick(self, ts):
        d = ts.astimezone(C.PRAGUE).date().isoformat()
        for s, e, inst in self.plan:
            if s <= d <= e:
                return inst
        return None

    def prepare(self, data):
        for _, _, inst in self.plan:
            inst.bar_minutes = self.bar_minutes
            inst.prepare(data)

    def signal(self, sym, ts, bar, mem):
        i = self._pick(ts)
        return i.signal(sym, ts, bar, mem) if i and sym in i.instruments else None

    def exit_now(self, sym, ts, pos):
        i = self._pick(ts) or self.plan[-1][2]
        return i.exit_now(sym, ts, pos)


def run_strat(strategy, s, e, data):
    return B.run(strategy=strategy, start=s, end=e, interval="5m", data=data)


def main(names):
    os.makedirs(OUT, exist_ok=True)
    data = {s: load_duka(s) for s in C.INSTRUMENTS}
    folds_out, plan, oos_trades, per_strat_oos = [], [], [], defaultdict(list)
    for tr_s, tr_e, te_s, te_e in folds():
        t0 = time.time()
        cands = []
        for name in names:
            for p in (load(name).GRID or [{}]):
                r = run_strat(make(name, p, C.INSTRUMENTS), tr_s, tr_e, data)
                ps = per_sym(r["trades"])
                keep = [s for s, (n, R) in ps.items() if n >= 8 and R > 0]
                if not keep:
                    continue
                r2 = run_strat(make(name, p, keep), tr_s, tr_e, data)
                st = stats(r2["trades"])
                if st["n"] >= 20:
                    cands.append((st["tot_R"], name, p, keep, st))
        cands.sort(key=lambda x: -x[0])
        if not cands:
            folds_out.append(dict(train=f"{tr_s} → {tr_e}", test=f"{te_s} → {te_e}", choice=None))
            print(f"{te_s}: aucun candidat positif -> pas de trading", flush=True)
            continue
        R, name, p, keep, st = cands[0]
        rt = run_strat(make(name, p, keep), te_s, te_e, data)
        ste = stats(rt["trades"])
        oos_trades += rt["trades"]
        plan.append((te_s, te_e, make(name, p, keep)))
        # pour comparaison : chaque stratégie avec ses meilleurs paramètres du pli (sans tri entre stratégies)
        for n2 in names:
            best = next((c for c in cands if c[1] == n2), None)
            if best:
                per_strat_oos[n2] += run_strat(make(n2, best[2], best[3]), te_s, te_e, data)["trades"]
        folds_out.append(dict(train=f"{tr_s} → {tr_e}", test=f"{te_s} → {te_e}", strategy=name, params=p,
                              instruments=keep, train_stats=st, test_stats=ste,
                              top5=[dict(strategy=c[1], params=c[2], instruments=c[3], R=c[0]) for c in cands[:5]]))
        print(f"{te_s}: {name} {p} {keep} | ajust. R={R} n={st['n']} | test R={ste['tot_R']} n={ste['n']} ({time.time()-t0:.0f}s)", flush=True)
    res = dict(folds=folds_out, oos=stats(oos_trades),
               per_strategy_oos={k: stats(v) for k, v in per_strat_oos.items()})
    if plan:
        ch = B.run(strategy=Plan(plan), start=TEST_STARTS[0], end=DATA_END, interval="5m", data=data)
        res["challenge"] = {k: ch[k] for k in ("n_completed", "n_pass", "n_fail", "pass_rate", "avg_days_pass",
                                               "fail_causes", "fees_usd", "fee_per_attempt_usd",
                                               "expected_payout_per_attempt_usd", "net_pnl")}
        res["attempts"], res["curve"] = ch["attempts"], ch["curve"]
    print(json.dumps({k: res[k] for k in ("oos", "per_strategy_oos")}, ensure_ascii=False), res.get("challenge"), flush=True)
    with open(os.path.join(OUT, "wf_duka.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, default=str)
    return res


if __name__ == "__main__":
    main(sys.argv[1].split(",") if len(sys.argv) > 1 else CANDIDATES)
