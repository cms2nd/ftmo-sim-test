"""Validation pré-enregistrée (docs/research/smc_preregistration.md) sur l'année jamais utilisée.

Usage : python -m research.smc_validate
Écrit docs/research/smc_validation.json
"""
import copy, json, os
import numpy as np
import pandas as pd

import backtest as B
from research import smc_events as E
from research.walkforward import stats
from sim import config as C
from sim.data import load_duka

DEV = ("2025-11-01", "2026-11-20")
VAL = ("2024-11-01", "2025-10-31")
S1 = ("smc_gold", dict(ENTRY="mss", TARGET="rr", RR=2.0, BIAS="none"))
S2 = ("gold_asia_break", dict(STOP_ATR=0.5, RR=4.0))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research")


def tstat(trades):
    r = np.array([t["pnl"] / C.RISK_PER_TRADE for t in trades])
    return round(float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))), 2) if len(r) > 2 else None


def bt(name, params, period, data):
    r = B.run(name, start=period[0], end=period[1], interval="5m", data=data, params=params)
    st = stats(r["trades"])
    return dict(**st, t=tstat(r["trades"]), n_pass=r["n_pass"], n_completed=r["n_completed"],
                net_pnl=round(float(r["net_pnl"]), 2), attempts=r["attempts"]), r


def monte_carlo(trades, n_sims=5000, seed=0, max_days=60):
    """Tire au hasard des journées réelles (P&L de chaque jour de trading, jours sans trade compris)
    et applique les règles FTMO : +2 500 $ => réussi (Best Day ≤ 50 %), perte journalière 750 $,
    plancher = plus haut solde de fin de journée − 2 500 $, coupe-circuit de 3 × risque au plancher."""
    by_day = {}
    for t in trades:
        d = pd.Timestamp(t["exit_time"]).tz_convert(C.PRAGUE).date()
        by_day[d] = by_day.get(d, 0.0) + t["pnl"]
    days = pd.bdate_range(min(by_day), max(by_day)).date
    pnl = np.array([by_day.get(d, 0.0) for d in days])
    rng = np.random.default_rng(seed)
    res = {"pass": 0, "fail": 0, "timeout": 0, "days_pass": []}
    for _ in range(n_sims):
        bal, peak, best, tot = 25000.0, 25000.0, 0.0, 0.0
        out = "timeout"
        for k in range(max_days):
            p = pnl[rng.integers(len(pnl))]
            if p <= -C.MAX_DAILY_LOSS:
                out = "fail"; break
            bal += p; tot += p; best = max(best, p)
            peak = max(peak, bal)
            if bal <= peak - 2500:
                out = "fail"; break
            if bal - (peak - 2500) < 3 * C.RISK_PER_TRADE:
                out = "fail"; break   # bloqué par le coupe-circuit plancher
            if tot >= 2500 and best <= 0.5 * tot:
                out = "pass"; res["days_pass"].append(k + 1); break
        res[out] += 1
    return dict(pass_rate=round(res["pass"] / n_sims, 3), fail_rate=round(res["fail"] / n_sims, 3),
                timeout_rate=round(res["timeout"] / n_sims, 3),
                median_days_pass=float(np.median(res["days_pass"])) if res["days_pass"] else None,
                ev_per_attempt_usd=round((res["pass"] / n_sims) * 2250 - 215, 0))   # 90 % de 2 500 $ si réussi, moins les frais


def main():
    xau = load_duka("XAUUSD")
    data = {"XAUUSD": xau}
    out = {"prereg": "docs/research/smc_preregistration.md", "periods": {"dev": DEV, "val": VAL}}
    # H1 / H2 : étude d'événements sur l'année de validation
    ev = E.main(VAL[0], VAL[1], tag="val")
    e = pd.read_csv(os.path.join(OUT, "smc_events_val.csv"))
    h2 = e[(e.kz == "Londres") & e.level.str.startswith("Asie")].copy()
    sgn = np.where(h2.kind == "balayage", -1, 1)
    out["H1_sweep_reversal_1h"] = ev["groups"]["balayage"]["1 h"]
    out["H2_asia_london_continuation_nyclose"] = E.summarize(list(h2["NY clôture"] * sgn))
    # S1 / S2 sur les deux années
    full = {}
    for key, (name, p) in (("S1", S1), ("S2", S2)):
        for per_name, per in (("dev", DEV), ("val", VAL)):
            s, r = bt(name, p, per, data)
            out[f"{key}_{per_name}"] = s
            full[(key, per_name)] = r
            print(key, per_name, {k: s[k] for k in ("n", "exp_R", "pf", "t", "n_pass", "n_completed", "net_pnl")}, flush=True)
    # Robustesse S2 sur la validation
    name, p = S2
    rob = {}
    p2 = dict(p, CONFIRM_BARS=4)
    rob["entrée retardée de 5 min"] = bt(name, p2, VAL, data)[0]
    saved = copy.deepcopy(C.INSTRUMENTS["XAUUSD"])
    try:
        C.INSTRUMENTS["XAUUSD"]["slippage"] *= 2
        C.INSTRUMENTS["XAUUSD"]["commission_rate"] *= 2
        x2 = xau.copy(); x2["spread"] = x2["spread"] * 2
        rob["coûts × 2"] = bt(name, p, VAL, {"XAUUSD": x2})[0]
    finally:
        C.INSTRUMENTS["XAUUSD"] = saved
    for sa, rr in ((0.3, 2.0), (0.8, 4.0)):
        rob[f"STOP_ATR={sa}, RR={rr}"] = bt(name, dict(STOP_ATR=sa, RR=rr), VAL, data)[0]
    out["S2_robustness_val"] = {k: {kk: v[kk] for kk in ("n", "exp_R", "pf", "t", "n_pass", "n_completed", "net_pnl")} for k, v in rob.items()}
    for k, v in out["S2_robustness_val"].items():
        print("robustesse", k, v, flush=True)
    # Monte Carlo des challenges à partir des journées de validation
    out["S2_montecarlo_val"] = monte_carlo(full[("S2", "val")]["trades"])
    out["S2_montecarlo_dev"] = monte_carlo(full[("S2", "dev")]["trades"])
    print("Monte Carlo val", out["S2_montecarlo_val"], "dev", out["S2_montecarlo_dev"], flush=True)
    # courbes pour l'infographie
    out["S2_curve_val"] = full[("S2", "val")]["curve"]
    out["S2_curve_dev"] = full[("S2", "dev")]["curve"]
    out["S2_trades_val"] = [dict(t=x["exit_time"], R=round(x["pnl"] / C.RISK_PER_TRADE, 3)) for x in full[("S2", "val")]["trades"]]
    out["S2_trades_dev"] = [dict(t=x["exit_time"], R=round(x["pnl"] / C.RISK_PER_TRADE, 3)) for x in full[("S2", "dev")]["trades"]]
    with open(os.path.join(OUT, "smc_validation.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, default=str)
    print("H1", out["H1_sweep_reversal_1h"], "H2", out["H2_asia_london_continuation_nyclose"])
    return out


if __name__ == "__main__":
    main()
