# ftmo-sim-test

Simulateur **paper trading** du FTMO Challenge 1-Step 25 000 $ (aucun argent réel, aucun compte connecté).
Résultats et verdict : **[RAPPORT.md](RAPPORT.md)** (mis à jour automatiquement toutes les 5 minutes pendant le test).

```
sim/config.py        règles FTMO, instruments, coûts, coupe-circuits, dates du test
sim/engine.py        simulateur d'ordres + moteur de règles FTMO (commun backtest/live)
sim/data.py          données 5 min gratuites (Yahoo Finance, sans clé) + cache data/
sim/news.py          calendrier NFP / CPI / Fed / BCE
strategies/          une stratégie = un fichier (aggressive_v1.py = ORB Londres/NY)
backtest.py          backtest en challenges successifs ; make_backtest.py = rapport complet
run.py               une exécution live (appelée par .github/workflows/simulate.yml)
report.py            génère RAPPORT.md et les graphiques
state/state.json     état persistant (solde, positions, journal)
```

Nouvelle stratégie : copier `strategies/aggressive_v1.py`, l'adapter, `python backtest.py --strategy <nom>`.
