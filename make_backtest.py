"""Lance le backtest de validation complet et écrit docs/backtest_summary.json.

Période d'ajustement : début des données → TUNE_END ; validation : après TUNE_END.
"""
import json
import os

import backtest as B

TUNE_END = "2026-10-23"
VALID_START = "2026-10-24"


def slim(r):
    return {k: v for k, v in r.items() if k not in ("trades", "breakers")}


WEEKS = ["2026-09-14", "2026-09-21", "2026-09-28", "2026-10-05", "2026-10-12",
         "2026-10-19", "2026-10-26", "2026-11-02", "2026-11-09", "2026-11-16"]


def weekly_runs():
    """Un challenge neuf de 25 000 $ par semaine (lundi -> vendredi), mêmes règles."""
    from datetime import date, timedelta
    from collections import defaultdict
    out = []
    for w in WEEKS:
        end = (date.fromisoformat(w) + timedelta(days=4)).isoformat()
        r = B.run(start=w, end=end)
        a = r["attempts"][0]
        bal, low = 25000.0, 25000.0
        for t in r["trades"]:
            bal = t["balance"]; low = min(low, bal)
        daily = defaultdict(float)
        for t in r["trades"]:
            daily[t["exit_time"][:10]] += t["pnl"]
        out.append({"week": w, "end": end, "status": a["status"] if a["status"] != "INACHEVÉ" else "objectif non atteint",
                    "reason": a["reason"] if a["status"] != "INACHEVÉ" else "",
                    "balance": a["balance"], "pnl": round(a["balance"] - 25000, 2), "trades": len(r["trades"]),
                    "wins": sum(1 for t in r["trades"] if t["pnl"] > 0), "min_balance": round(low, 2),
                    "best_day": round(max(daily.values()), 2) if daily else 0.0,
                    "worst_day": round(min(daily.values()), 2) if daily else 0.0,
                    "breakers": len(r["breakers"]),
                    "detail": [[t["exit_time"][:16], t["sym"], t["side"], t["reason"], t["pnl"], t["balance"]] for t in r["trades"]]})
        print(w, out[-1]["status"], out[-1]["pnl"], out[-1]["trades"])
    return out


def main():
    full = B.run()
    tune = B.run(end=TUNE_END)
    valid = B.run(start=VALID_START)
    counts, n = B.rolling_windows()
    weekly = weekly_runs()
    out = {
        "intro": ("Backtest de `aggressive_v1` avec exactement le même moteur que le test en direct (règles FTMO, "
                  "spread, commission, glissement pessimiste doublé sur les stops, plus haut/plus bas des bougies, "
                  "coupe-circuits). Données : bougies 5 min Yahoo Finance (maximum gratuit ≈ 60 jours calendaires, "
                  "soit " + str(full["trading_days"]) + " jours de trading). Une nouvelle tentative de 25 000 $ démarre "
                  "le jour suivant chaque réussite, échec ou blocage.\n"),
        "full": slim(full), "tune": slim(tune), "valid": slim(valid),
        "rolling3": {"counts": counts, "n": n},
        "weekly": weekly,
        "tuning_note": open(os.path.join(os.path.dirname(__file__), "docs", "ajustement.md")).read()
        if os.path.exists(os.path.join(os.path.dirname(__file__), "docs", "ajustement.md")) else "",
    }
    with open(os.path.join(os.path.dirname(__file__), "docs", "backtest_summary.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, default=str)
    with open(os.path.join(os.path.dirname(__file__), "docs", "backtest_trades.json"), "w") as f:
        json.dump({"trades": full["trades"], "breakers": full["breakers"]}, f, ensure_ascii=False, default=str, indent=0)
    print(json.dumps({k: slim(v) if isinstance(v, dict) and "curve" in v else v for k, v in out.items() if k != "full"},
                     ensure_ascii=False, default=str)[:1500])


if __name__ == "__main__":
    main()
