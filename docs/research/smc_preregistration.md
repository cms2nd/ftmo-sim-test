# Pré-enregistrement — test de validation sur l'or (XAUUSD)

Écrit et commité **avant** d'ouvrir l'année de validation (2024-11-01 → 2025-10-31, jamais utilisée).
Rien ci-dessous ne sera modifié après coup ; les résultats seront publiés quels qu'ils soient.

## Littérature
- Aucune étude scientifique ne valide les concepts SMC/ICT (order blocks, FVG, MSS) : seulement des blogs,
  des backtests de vendeurs, souvent contradictoires. Un preprint arXiv (2610.35887) sur le modèle AMD d'ICT
  (Nasdaq E-mini) ne trouve pas d'avantage, hormis le régime de tendance journalier.
- Base solide la plus proche : Osler (Fed de New York, staff reports 125 et 150) — les ordres stop
  s'accumulent au-delà des niveaux évidents ; leur déclenchement **accélère** le mouvement (cascades).
- Or : volatilité intrajournalière en U autour des ouvertures de Londres et New York (RIETI DP 17-E-120).

## Année de développement (2025-11 → 2026-11) : constats
- 71 % des premiers franchissements de niveau en killzone reviennent dans les 15 min (« balayages »),
  mais **aucun retournement** ensuite (30 min, 1 h, 2 h : t ≈ 0). La thèse SMC n'est pas confirmée.
- Premier franchissement du range asiatique pendant Londres : **prolongement** jusqu'à la clôture de NY,
  +0,10 ATR, t = 2,28, 163 cas (≈ 40 comparaisons faites : risque de faux positif réel).

## Hypothèses testées sur l'année de validation (une seule fois)
| | Hypothèse | Test | Critère de succès |
|---|---|---|---|
| H1 | Après un balayage, le prix se retourne (SMC) | étude d'événements, retour à 1 h | moyenne > 0 et t ≥ 2 |
| H2 | Après le 1er franchissement du range asiatique à Londres, prolongement jusqu'à la clôture NY | étude d'événements | moyenne > 0 et t ≥ 2 |
| S1 | `smc_gold` (ENTRY=mss, TARGET=rr, RR=2, BIAS=none — paramètres par défaut) | backtest moteur FTMO | R/trade > 0 |
| S2 | `gold_asia_break` (STOP_ATR=0,5, RR=4) | backtest moteur FTMO | R/trade > 0 et t ≥ 2 ; challenges réussis |

Même moteur, mêmes frais (spread réel Dukascopy, glissement, commissions), mêmes règles FTMO et coupe-circuits.
Tests complémentaires prévus : coûts × 2, entrée décalée d'une bougie, Monte Carlo des challenges.
