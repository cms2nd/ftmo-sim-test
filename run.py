"""Exécution live (paper trading) appelée toutes les 5 minutes par GitHub Actions.

1. charge l'état (state/state.json)          4. applique le moteur FTMO + coupe-circuits
2. récupère les bougies 5 min (Yahoo)         5. sauvegarde l'état + RAPPORT.md
3. rejoue les bougies clôturées non traitées (plus hauts/bas => stops/objectifs)

Les entrées ne sont autorisées que sur une bougie clôturée depuis moins de
STALE_MIN minutes (le cron GitHub peut avoir du retard): les bougies plus
anciennes ne servent qu'à gérer stops, objectifs et règles.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone, date

import pandas as pd

from sim import config as C
from sim import data as D
from sim.engine import Engine, new_state, prague_day
from strategies.base import load

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, "state", "state.json")
STALE_MIN = 15


def load_state():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return None


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    s["equity_curve"] = s["equity_curve"][-5000:]
    with open(STATE, "w") as f:
        json.dump(s, f, ensure_ascii=False, indent=1, default=float)


def compute_end(first_day: date) -> str:
    if first_day.isoformat() <= C.LIVE_START_DATE:
        return C.LIVE_END_DATE
    d, n = first_day, 0
    while True:
        if d.weekday() < 5:
            n += 1
            if n == 5:
                break
        d += timedelta(days=1)
    return min(d.isoformat(), C.HARD_STOP_DATE)


def main(now=None, strategy=None):
    now = now or datetime.now(timezone.utc)
    today = prague_day(now)
    s = load_state()
    if s is None:
        s = new_state(now)
        s["strategy"] = strategy or C.ACTIVE_STRATEGY
        s["live_end_date"] = compute_end(now.astimezone(C.PRAGUE).date())
        s["first_run"] = now.isoformat()
        s["run_log"] = []
        print(f"[run] nouvel état, fin du test: {s['live_end_date']} (Prague)")
    strat = load(s.get("strategy", C.ACTIVE_STRATEGY))
    finished = today > s["live_end_date"] or today > C.HARD_STOP_DATE
    if finished:
        s["test_finished"] = True

    data = {}
    for sym in strat.instruments:
        df = D.update(sym, period="5d") if not (finished or os.environ.get("SIM_OFFLINE")) else D.load_cache(sym)
        data[sym] = D.complete_bars(df, now)
    strat.prepare(data)
    eng = Engine(s, strat, live=True, now=now)

    # Premier lancement: ne pas rejouer l'historique
    for sym, df in data.items():
        if sym not in s["last_bar"]:
            s["last_bar"][sym] = (now - timedelta(minutes=STALE_MIN)).isoformat()

    rows = {}
    for sym, df in data.items():
        last = pd.Timestamp(s["last_bar"][sym])
        for ts, r in df.iterrows():
            ct = ts + pd.Timedelta(minutes=5)
            if ct <= last:
                continue
            rows.setdefault(ct.to_pydatetime(), {})[sym] = {k: float(r[k]) for k in ("open", "high", "low", "close")}
    n_bars = 0
    for ct, bars in sorted(rows.items()):
        if ct.astimezone(C.PRAGUE).date().isoformat() > s["live_end_date"]:
            break
        fresh = (now - ct) <= timedelta(minutes=STALE_MIN)
        started = prague_day(ct) >= C.LIVE_START_DATE
        eng.step(ct, bars, allow_entries=fresh and not finished and started)
        for sym in bars:
            s["last_bar"][sym] = ct.isoformat()
        n_bars += 1
    eng.rollover(now)
    if eng.flatten_due(now) and s["positions"]:
        eng.flatten(now, "clôture fin de journée")
    if finished and s["positions"]:
        eng.flatten(now, "fin du test")
    s["equity"] = s["balance"] + eng._floating()
    s["equity_curve"].append([now.isoformat(), round(s["equity"], 2), round(s["balance"], 2)])
    s["last_run"] = now.isoformat()
    s.setdefault("run_log", []).append({"t": now.isoformat(), "bars": n_bars,
                                        "data": {k: (str(v.index[-1]) if len(v) else None) for k, v in data.items()}})
    s["run_log"] = s["run_log"][-300:]
    save_state(s)
    print(f"[run] {now:%Y-%m-%d %H:%M} UTC | bougies traitées: {n_bars} | statut {s['status']} | "
          f"solde {s['balance']:.2f} | equity {s['equity']:.2f} | positions {len(s['positions'])}")
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", help="horodatage UTC ISO (tests)")
    a = ap.parse_args()
    main(datetime.fromisoformat(a.now) if a.now else None)
    from report import write_report
    write_report()
