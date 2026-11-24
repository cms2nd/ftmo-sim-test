"""Backtest d'une stratégie avec le même moteur (règles FTMO, frais, glissement, coupe-circuits).

Découpe en challenges successifs: à chaque réussite/échec, une nouvelle tentative
de 25 000 $ démarre le jour de trading suivant (heure de Prague).

Usage:
  python backtest.py [--strategy aggressive_v1] [--instruments US100,XAUUSD] [--start 2026-09-01] [--end 2026-11-30]
                     [--param RR=2.0 ...] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime

import pandas as pd

from sim import config as C
from sim.data import load_cache
from sim.engine import Engine, new_state, prague_day
from strategies.base import load


def timeline(data, bar_minutes=5):
    rows = {}
    for sym, df in data.items():
        sp = df["spread"].values if "spread" in df.columns else [None] * len(df)
        for ts, o, h, l, c, z in zip(df.index, df["open"].values, df["high"].values, df["low"].values, df["close"].values, sp):
            ct = (ts + pd.Timedelta(minutes=bar_minutes)).to_pydatetime()
            b = {"open": float(o), "high": float(h), "low": float(l), "close": float(c)}
            if z is not None and z == z:
                b["spread"] = float(z)
            rows.setdefault(ct, {})[sym] = b
    return sorted(rows.items())


def trading_days(tl):
    return sorted({prague_day(t) for t, _ in tl if t.astimezone(C.PRAGUE).weekday() < 5})


INTERVAL_MIN = {"5m": 5, "15m": 15, "60m": 60}


def run(strategy_name="aggressive_v1", instruments=None, start=None, end=None, params=None, verbose=False,
        interval="5m", strategy=None, data=None):
    strat = strategy or load(strategy_name)
    for k, v in (params or {}).items():
        setattr(strat, k, v)
    if instruments:
        strat.instruments = instruments
    if data is None:
        data = {s: load_cache(s, interval) for s in strat.instruments}
    else:
        data = {s: data[s] for s in strat.instruments}
    if start or end:  # marge de 40 jours avant le début pour les indicateurs journaliers
        lo = pd.Timestamp(start, tz="UTC") - pd.Timedelta(days=40) if start else None
        hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=2) if end else None
        data = {s: d[(lo is None or d.index >= lo) & (hi is None or d.index <= hi)] for s, d in data.items()}
    strat.bar_minutes = INTERVAL_MIN[interval]
    strat.prepare(data)
    tl = timeline(data, INTERVAL_MIN[interval])
    if start:
        tl = [x for x in tl if prague_day(x[0]) >= start]
    if end:
        tl = [x for x in tl if prague_day(x[0]) <= end]
    tl = [x for x in tl if x[0].astimezone(C.PRAGUE).weekday() < 5]
    days = trading_days(tl)
    results, all_trades, breakers = [], [], []
    attempt = 1
    state = new_state(tl[0][0] if tl else None, attempt)
    eng = Engine(state, strat)
    skip_day = None
    equity_curve = []
    for t, bars in tl:
        d = prague_day(t)
        if skip_day and d == skip_day:
            continue
        if state["status"] != "EN COURS":
            continue
        eng.step(t, bars)
        equity_curve.append((t, attempt, state["equity"]))
        if (state["status"] == "EN COURS" and not state["positions"]
                and state["balance"] - state["floor"] < C.FLOOR_BUFFER_MULT * C.RISK_PER_TRADE):
            # Compte figé: le coupe-circuit "distance au plancher < 3 × risque" interdit
            # tout nouveau trade pour toujours (le plancher ne descend jamais).
            state["status"] = "BLOQUÉ"
            state["status_reason"] = "bloqué: distance au plancher %.0f $ < 3 × risque" % (state["balance"] - state["floor"])
        if state["status"] != "EN COURS":
            d0 = prague_day(datetime.fromisoformat(state["start_time"]))
            ndays = len([x for x in days if d0 <= x <= d])
            results.append({"attempt": attempt, "status": state["status"], "reason": state["status_reason"],
                            "start": d0, "end": d, "days": ndays, "balance": round(float(state["balance"]), 2),
                            "trades": len(state["trades"])})
            all_trades += state["trades"]
            breakers += state["breakers"]
            attempt += 1
            skip_day = d
            # nouvelle tentative au prochain jour
            nxt = [x for x in tl if prague_day(x[0]) > d]
            if not nxt:
                break
            state = new_state(nxt[0][0], attempt)
            eng = Engine(state, strat)
            state["status"] = "EN COURS"
    if state["status"] == "EN COURS" and state["start_time"]:
        d0 = prague_day(datetime.fromisoformat(state["start_time"]))
        if tl:
            eng.flatten(tl[-1][0], "fin des données")
        results.append({"attempt": attempt, "status": "INACHEVÉ", "reason": "fin des données",
                        "start": d0, "end": days[-1] if days else d0,
                        "days": len([x for x in days if x >= d0]), "balance": round(float(state["balance"]), 2),
                        "trades": len(state["trades"])})
        all_trades += state["trades"]
        breakers += state["breakers"]
    return summarize(results, all_trades, breakers, days, equity_curve)


def summarize(results, trades, breakers, days, curve):
    done = [r for r in results if r["status"] in ("RÉUSSI", "ÉCHOUÉ", "BLOQUÉ")]
    wins = [r for r in done if r["status"] == "RÉUSSI"]
    fails = [r for r in done if r["status"] != "RÉUSSI"]

    def cause(r):
        if r["status"] == "BLOQUÉ":
            return "bloqué par coupe-circuit plancher (pas une violation FTMO, mais plus aucun trade possible)"
        return "perte journalière" if "journalière" in r["reason"] else "perte max trailing"
    causes = Counter(cause(r) for r in fails)
    pnl = [t["pnl"] for t in trades]
    gp = sum(p for p in pnl if p > 0)
    gl = -sum(p for p in pnl if p < 0)
    n = len(done)
    fee_usd = C.CHALLENGE_FEE_EUR * 1.08
    # Espérance par tentative si le compte financé rapportait autant que le challenge (hypothèse optimiste):
    exp_payout = (len(wins) / n) * C.PROFIT_SPLIT * C.PROFIT_TARGET if n else 0.0
    return {
        "trading_days": len(days), "first_day": days[0] if days else None, "last_day": days[-1] if days else None,
        "attempts": results, "n_completed": n, "n_pass": len(wins), "n_fail": len(fails),
        "pass_rate": (len(wins) / n) if n else None,
        "pass_rate_3d": (len([r for r in wins if r["days"] <= 3]) / n) if n else None,
        "avg_days_pass": (sum(r["days"] for r in wins) / len(wins)) if wins else None,
        "avg_days_fail": (sum(r["days"] for r in fails) / len(fails)) if fails else None,
        "fail_causes": dict(causes),
        "n_trades": len(trades), "win_rate": (sum(1 for p in pnl if p > 0) / len(pnl)) if pnl else None,
        "profit_factor": (gp / gl) if gl else None, "net_pnl": round(sum(pnl), 2),
        "avg_trade": (sum(pnl) / len(pnl)) if pnl else None,
        "fees_usd": round(n * fee_usd, 2), "fee_per_attempt_usd": round(fee_usd, 2),
        "expected_payout_per_attempt_usd": round(exp_payout, 2),
        "trades": trades, "breakers": breakers,
        "curve": [(t.isoformat(), a, round(e, 2)) for t, a, e in curve[::6]],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default=C.ACTIVE_STRATEGY)
    ap.add_argument("--instruments")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--param", action="append", default=[])
    ap.add_argument("--json")
    a = ap.parse_args()
    params = {k: float(v) for k, v in (p.split("=") for p in a.param)}
    r = run(a.strategy, a.instruments.split(",") if a.instruments else None, a.start, a.end, params)
    show = {k: v for k, v in r.items() if k not in ("trades", "breakers", "curve", "attempts")}
    print(json.dumps(show, indent=1, ensure_ascii=False, default=str))
    for x in r["attempts"]:
        print(x)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(r, f, ensure_ascii=False, default=str)


def rolling_windows(strategy_name="aggressive_v1", horizon=3, start=None, end=None):
    """Lance un challenge neuf à chaque jour de trading et observe l'issue après `horizon` jours."""
    strat = load(strategy_name)
    data = {s: load_cache(s) for s in strat.instruments}
    days = trading_days(timeline(data))
    days = [d for d in days if (not start or d >= start) and (not end or d <= end)]
    out = Counter()
    for i in range(len(days) - horizon + 1):
        r = run(strategy_name, start=days[i], end=days[i + horizon - 1])
        a = r["attempts"][0]
        out[a["status"] if a["status"] != "INACHEVÉ" else ("en gain" if a["balance"] > C.INITIAL_BALANCE else "en perte")] += 1
    return dict(out), len(days) - horizon + 1
