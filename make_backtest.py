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


def main():
    full = B.run()
    tune = B.run(end=TUNE_END)
    valid = B.run(start=VALID_START)
    counts, n = B.rolling_windows()
    out = {
        "intro": ("Backtest de `aggressive_v1` avec exactement le même moteur que le test en direct (règles FTMO, "
                  "spread, commission, glissement pessimiste doublé sur les stops, plus haut/plus bas des bougies, "
                  "coupe-circuits). Données : bougies 5 min Yahoo Finance (maximum gratuit ≈ 60 jours calendaires, "
                  "soit " + str(full["trading_days"]) + " jours de trading). Une nouvelle tentative de 25 000 $ démarre "
                  "le jour suivant chaque réussite, échec ou blocage.\n"),
        "full": slim(full), "tune": slim(tune), "valid": slim(valid),
        "rolling3": {"counts": counts, "n": n},
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
