Objectif : chercher honnêtement s'il existe une variante avec un **avantage réel**, sans sur-optimiser (les 4 points proposés).

1. **Plus de données** : 2 ans de bougies **1 heure** Yahoo (juillet 2024 → novembre 2026) sur les 6 instruments, soit ≈ 10 fois plus de trades que les 60 jours en 5 min. Les données 15 min (60 jours) et 5 min servent de contrôle final. En 1 h, le range d'ouverture correspond à la première bougie de séance (Londres 08:00–09:00 ; New York **09:00–10:00 ET**, car Yahoo aligne les bougies sur l'heure pile, ce qui inclut 30 min de pré-ouverture). C'est une approximation de l'ORB 15 min.
2. **Quelques variantes connues, chacune dans son propre fichier** (6 combinaisons de paramètres au plus par variante) :
   - `orb_ref` : les règles d'aggressive_v1 telles quelles, mais sur les 6 instruments (référence) ;
   - `orb_v2_tight` : stop plus serré (milieu du range, ou 0,15 / 0,25 ATR), objectif 1,5 ou 2 R ;
   - `orb_v3_retest` : cassure confirmée, puis entrée par ordre limite sur le retest du niveau cassé ;
   - `orb_v4_trend` : filtre de tendance de fond (clôture de la veille **et** moyenne 20 jours) ;
   - `mr_v1` : autre famille, retour vers l'ouverture après un excès de début de séance (≥ 0,4–0,8 ATR) suivi d'une bougie de retournement.
3. **Validation glissante (walk-forward)** : 8 plis trimestriels. Les paramètres sont choisis sur les 6 mois précédents, puis appliqués tels quels aux 3 mois suivants, jamais vus. Seuls les trades de test comptent dans les résultats. Les 6 instruments sont toujours utilisés (pas de choix d'instruments a posteriori).
4. **Même objectif FTMO, sans limite de temps** : simulation continue sur toute la période de test (≈ 23 mois), avec le moteur, les frais, le glissement et les coupe-circuits du test en direct. On enchaîne les challenges de 25 000 $ (nouvelle tentative après réussite, échec ou blocage) et on mesure le taux de réussite, la durée et l'espérance nette par tentative (90 % × 2 500 $ × taux de réussite − 199 €).
