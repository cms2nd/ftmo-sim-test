#### Données de qualité broker (Dukascopy) contre Yahoo — 21/09 → 20/11/2026, bougies 5 min

Dukascopy publie gratuitement le bid et l'ask minute par minute. Les bougies sont calculées au prix milieu, et le spread réel de chaque bougie remplace le spread fixe de la config (le glissement et les commissions restent identiques). Le troisième jeu de données (« Dukascopy, spread fixe ») isole l'effet de la qualité des prix, sans l'effet du coût.

**Ce qu'on apprend :**
- Les spreads réels sont **plus faibles** que ceux de la config pour les indices et le FX (EURUSD ≈ 0,3 pip contre 1 pip). Ils sont en revanche **plus élevés** pour l'or.
- Le plus gros écart ne vient pas du spread mais **des prix eux-mêmes** : avec le même spread fixe, `aggressive_v1` passe de −10 R (Yahoo) à −1 R (Dukascopy). Les bougies Yahoo des contrats à terme (NQ=F, YM=F) ne sont pas les CFD cotés par un broker : les plus hauts et plus bas diffèrent, et donc les stops touchés aussi.
- Avec les prix de broker, `aggressive_v1` et `orb_ref` sont **à l'équilibre** (+0,02 à +0,03 R par trade), pas gagnants. `orb_v4_trend` reste la seule variante nettement positive (+0,11 R/trade, 90 trades), mais elle était déjà négative sur 2 ans en walk-forward (bougies 1 h). Deux mois ne suffisent pas à conclure.
- Sur la période, il y a 0 ou 1 challenge réussi par variante et par jeu de données.
