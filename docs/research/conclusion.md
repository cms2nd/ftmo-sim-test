#### Contrôles complémentaires

| Contrôle | Résultat |
|---|---|
| `orb_ref` **sans aucun frais** (2025-01 → 2026-11, 1 h) | +0,038 R/trade, profit factor 1,11 (799 trades) |
| `orb_ref` **avec frais** | −0,027 R/trade, profit factor 0,92 |
| `orb_v4_trend` sans frais / avec frais | +0,034 R → −0,022 R/trade |
| `orb_ref` en 15 min (60 derniers jours) | +0,06 R/trade, 120 trades |
| `orb_v4_trend` en 15 min (60 derniers jours) | +0,095 R/trade, 64 trades |
| `orb_ref` en 5 min (60 derniers jours) | −0,07 R/trade, 114 trades |
| `orb_v4_trend` en 5 min (60 derniers jours) | **+0,17 R/trade**, 69 trades, 1 challenge réussi sur 2 |

#### Conclusion de la recherche

1. **Aucune variante n'a d'avantage hors échantillon sur 2 ans.** Les 5 variantes sont négatives sur les ≈ 23 mois de test (de −0,03 à −0,18 R par trade). Même sur les périodes d'ajustement, la meilleure combinaison est presque toujours négative : ce n'est pas un problème de réglage, il n'y a rien à régler.
2. **La cassure du range d'ouverture a un très léger avantage brut (≈ +0,035 R/trade avant frais), entièrement mangé par le spread et le glissement (≈ 0,06 R/trade).** Plus le stop est serré, plus les frais pèsent lourd en R : c'est pourquoi `orb_v2_tight` et `orb_v3_retest` font pire que la référence.
3. **Le retour à la moyenne (`mr_v1`) ne fonctionne pas non plus** et trouve peu d'occasions en 1 h.
4. **La moins mauvaise variante est `orb_v4_trend`** (filtre de tendance 20 jours). Sur 2 ans : −0,03 R par trade, soit à peu près à l'équilibre. Sur les 2 derniers mois en 5 min, elle est positive (+0,17 R), mais sur 69 trades, l'écart-type de la moyenne est d'environ ±0,15 R : **ce n'est pas statistiquement différent de zéro**. C'est exactement le piège qui avait fait choisir US100/GER40/EURUSD pour aggressive_v1.
5. **Challenges sans limite de temps** : 1 à 2 réussites sur 9 à 15 tentatives selon la variante, après 30 à 50 jours de trading. **Ces réussites viennent du hasard, pas d'un avantage.** Avec une stratégie proche de zéro, le solde fait une marche aléatoire entre l'objectif (+2 500 $) et le blocage du coupe-circuit plancher (≈ −1 750 $). Une partie des tentatives touche l'objectif par chance. Toutes les autres finissent bloquées par le coupe-circuit plancher. Aucune règle FTMO n'a été violée.
6. **L'« espérance nette par tentative » du tableau est trompeuse et ne doit pas être lue comme un gain.** Réussir le challenge ne rapporte pas 2 500 $ : on obtient un compte financé, sur lequel il faut ensuite gagner. Or avec une espérance négative par trade, ce compte perdrait en moyenne.

**Verdict de la recherche : je n'ai trouvé aucune stratégie avec un avantage démontré. Pousser l'optimisation plus loin sur ces données produirait seulement de belles courbes sur-ajustées.** Pour aller plus loin, il faudrait des données tick ou 1 min de qualité broker (spreads réels FTMO) et une idée de stratégie avec une raison économique d'exister, pas un balayage de paramètres.
