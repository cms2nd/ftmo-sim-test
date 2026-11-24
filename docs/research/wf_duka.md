#### Backtest sur 1 an de prix broker (Dukascopy, bougies 5 min, spread réel) — walk-forward

**Méthode.** Pour chaque tranche de test de 2 mois (de mars à novembre 2026), on regarde uniquement les 4 mois précédents. On y choisit la stratégie parmi 6 familles (49 combinaisons de paramètres), ses paramètres et les instruments à trader (ceux qui gagnaient en ajustement). Le choix est ensuite appliqué aux 2 mois suivants, jamais vus. Des challenges FTMO s'enchaînent sur toute la période de test, avec les mêmes règles, frais et coupe-circuits que le test en direct.

**Résultat 1 : choisir à chaque tranche la « meilleure » stratégie ne marche pas.** En ajustement, la stratégie retenue gagne entre +16 et +31 R. En test, elle perd 4 fois sur 5 : −0,08 R par trade sur 330 trades, et 0 challenge réussi sur 6. C'est le signe d'un sur-ajustement : la meilleure combinaison du passé est surtout celle qui a eu de la chance.

**Résultat 2 : une seule famille tient, `orb_v4_trend`.** Elle prend la cassure du range d'ouverture seulement dans le sens de la tendance (au-dessus de la clôture de la veille et de la moyenne sur 20 jours). Ses paramètres et instruments sont ré-ajustés à chaque tranche. En test, sur 275 trades, elle fait +0,07 R par trade (profit factor 1,14). Elle réussit 3 challenges sur 7 terminés, pour un P&L net de +4 269 $ après frais.

**Pourquoi il ne faut pas encore y croire :**
- l'avantage n'est **pas statistiquement significatif** (t ≈ 0,9 ; il faudrait environ t ≥ 2) ;
- il vient de 3 tranches sur 5 ; novembre (3 semaines, +14,6 R) pèse à lui seul les trois quarts du total ;
- j'ai mis cette famille en avant **après** l'avoir vue gagner sur septembre-novembre : ce choix est lui-même une sélection ;
- sur 2 ans de bougies 1 h (Yahoo), la même famille était **négative** hors échantillon (−0,03 R/trade).

**Conclusion.** Avec de vraies données de broker, aucune stratégie testée n'a d'avantage démontré. `orb_v4_trend` est la seule piste qui mérite un test en direct plus long, et pas encore de l'argent réel.
