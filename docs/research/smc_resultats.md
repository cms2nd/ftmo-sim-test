#### Or (XAUUSD) : Smart Money Concept éprouvé scientifiquement

**Ce que dit la littérature.**
- **Aucune étude scientifique ne valide le SMC ou l'ICT** (order blocks, FVG, MSS). On ne trouve que des blogs et des backtests de vendeurs, souvent contradictoires. Le seul travail de type académique trouvé est un preprint arXiv sur le modèle AMD d'ICT appliqué au Nasdaq : il ne trouve pas d'avantage, hormis la tendance journalière.
- **Le fondement solide le plus proche** : les travaux d'Osler (Fed de New York) montrent que les ordres stop s'accumulent au-delà des niveaux évidents, et que leur déclenchement **accélère** le mouvement au lieu de le retourner.

**Méthode.**
- Deux années de prix broker sur l'or (Dukascopy, bougies 5 min, spread réel) :
  - une année de développement (novembre 2025 → novembre 2026) pour construire ;
  - une année de validation (novembre 2024 → octobre 2025) jamais regardée.
- Les hypothèses, les règles et les paramètres ont été **figés et commités avant** d'ouvrir la validation (`docs/research/smc_preregistration.md`, commit 49838b4).

| | Hypothèse / stratégie | Développement | **Validation (jamais vue)** | Verdict |
|---|---|---|---|---|
| H1 | Après un balayage de liquidité, le prix se retourne (thèse SMC), à 1 h | +0,001 ATR, t = 0,1 | **−0,010 ATR, t = −0,8** | ❌ rejetée deux fois |
| H2 | Après le 1er franchissement du range asiatique à Londres, prolongement jusqu'à la clôture NY | +0,10 ATR, t = 2,3 | **+0,026 ATR, t = 0,7** | ❌ non confirmée |
| S1 | `smc_gold` : balayage → cassure de structure → entrée | −0,14 R/trade (41 trades) | **−0,13 R/trade (51 trades)** | ❌ perdante deux fois |
| S2 | `gold_asia_break` (issue de H2) | +0,19 R/trade, t = 2,4, 3 challenges / 4 | **−0,01 R/trade, t = −0,2, 1 challenge / 4** | ❌ l'avantage disparaît |

**Robustesse de S2 sur la validation** :
- entrée retardée de 5 min : −0,03 R ;
- coûts doublés : −0,06 R ;
- autres réglages : −0,05 et −0,01 R.

**Monte Carlo des challenges** (journées tirées au hasard, règles FTMO, 60 jours de trading au maximum) :
- **40 % de réussite** sur l'année de développement ;
- **8 % sur la validation**, soit une espérance d'environ −37 $ par tentative après frais.

**Conclusion.**
- La version mécanique du Smart Money Concept **ne fonctionne pas sur l'or**, ni sur l'année de développement, ni sur l'année de validation.
- Le seul effet trouvé en développement (+0,19 R/trade, t = 2,4) était **un faux positif**, classique quand on fait une quarantaine de comparaisons. Sans la validation pré-enregistrée, on l'aurait pris pour une stratégie gagnante.
