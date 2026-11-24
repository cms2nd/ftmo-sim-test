# RAPPORT — Simulation FTMO Challenge 1-Step 25 000 $ (paper trading)

> **EN COURS** — solde 25 000.00 $ — perte du jour 0.00 $ / 750 $ — distance au plancher 2 500.00 $ — mis à jour 2026-11-24T21:46 UTC

⚠️ Simulation uniquement : aucun argent réel, aucun compte de courtage ni FTMO connecté.

## Sommaire
1. Verdict
2. Test en direct
3. Backtest de validation
3 bis. Recherche d'amélioration (walk-forward)
4. Audit du repo source
5. Fonctionnement du simulateur
6. Limites du test

## 1. Verdict

**Non. Avec `aggressive_v1` telle quelle, la probabilité réaliste de passer le challenge FTMO 1-Step 25k en 3 jours est quasi nulle, et elle reste faible même sans limite de temps.**

Pourquoi :
1. **Les chiffres ne collent pas.** Atteindre +2 500 $ en 3 jours avec un risque de 250 $ par trade demande ≈ +10 R nets en 3 jours. La stratégie prend ≈ 1,8 trade par jour (une seule cassure par instrument et par séance), soit ≈ 5–6 trades en 3 jours : même avec un taux de réussite de 100 % à 2 R on plafonne vers +2 500 / +2 800 $, et sur l'historique le taux de réussite est d'environ 38 %.
2. **Aucun avantage statistique démontré.** Sur 60 jours de trading et ≈ 100 trades, le profit factor est < 1 (P&L net négatif après frais). La seule période un peu positive est celle qui a servi à choisir les instruments ; la période de validation hors échantillon est nettement perdante. Toutes les fenêtres glissantes de 3 jours du backtest échouent à atteindre l'objectif.
3. **Les coupe-circuits demandés protègent du « challenge échoué », pas de l'échec économique.** Aucune règle FTMO n'a été violée en backtest (perte du jour plafonnée à 600 $, refus des trades trop risqués), mais la règle « pas de trade si distance au plancher < 3 × risque » **fige le compte** dès ≈ 1 750 $ de baisse depuis le plus haut : c'est la cause de toutes les tentatives terminées. Le compte n'est jamais « recalé » ; il devient inutilisable, ce qui coûte autant que les 199 €.
4. **Le Best Day Rule et l'arrêt à +1 250 $/jour** imposent de répartir le gain sur ≥ 2 bons jours : impossible à garantir avec 1–2 trades par jour.

Ce qu'il faudrait pour avoir une chance : une stratégie avec un avantage mesuré sur des centaines de trades (pas 100), testée sur plusieurs années de données (payantes ou données 1 h de Yahoo sur 2 ans), et un objectif sans contrainte de 3 jours (le 1-Step n'a pas de limite de temps : viser 2–6 semaines à 0,5 % de risque par trade est bien plus réaliste que « agressif en 3 jours »).

Le test en direct d'une semaine (5 jours de marché, section 2) ne changera pas ce verdict, quel que soit son résultat : 5 jours de trading restent statistiquement insignifiants. Sur le backtest, **aucune des 56 fenêtres glissantes de 5 jours n'atteint +2 500 $** (24 terminent en gain, 31 en perte, 1 compte bloqué par le coupe-circuit plancher).

**Mise à jour après la recherche (section 3 bis) :** 5 variantes testées en walk-forward sur 2 ans (≈ 3 000 trades hors échantillon). Aucune n'a d'espérance positive après frais. Le léger avantage brut de la cassure du range d'ouverture (≈ +0,035 R par trade) disparaît dans le spread et le glissement. Sans limite de temps, 1 à 2 challenges sur 10 sont réussis, mais par hasard (marche aléatoire), au bout de 30 à 50 jours. Ce n'est pas une méthode reproductible ni rentable.

## 2. Test en direct

- Stratégie active : `aggressive_v1` — premier lancement : 2026-11-24T13:14:13.465556+00:00 UTC — fin du test : **2026-12-01** (heure de Prague)
- Dernière exécution : 2026-11-24T21:46:02.202450+00:00 UTC
- Solde : **25 000.00 $** — equity : 25 000.00 $ — plancher perte max : 22 500.00 $ — plus haut solde de fin de journée : 25 000.00 $

![Courbe d'equity live](docs/equity_live.png)

### P&L par jour (trades clôturés, jour de Prague)

| Jour | P&L clôturé |
|---|---:|
| — | — |

### Règle du meilleur jour

Aucun jour positif pour l'instant.

### Positions ouvertes

Aucune.

### Journal des trades

| Instr. | Sens | Entrée (UTC) | Prix | Sortie (UTC) | Prix | Motif | P&L | Solde |
|---|---|---|---:|---|---:|---|---:|---:|
| — | | | | | | aucun trade pour l'instant | | |

### Coupe-circuits déclenchés

Aucun.

## 3. Backtest de validation

Backtest de `aggressive_v1` avec exactement le même moteur que le test en direct (règles FTMO, spread, commission, glissement pessimiste doublé sur les stops, plus haut/plus bas des bougies, coupe-circuits). Données : bougies 5 min Yahoo Finance (maximum gratuit ≈ 60 jours calendaires, soit 60 jours de trading). Une nouvelle tentative de 25 000 $ démarre le jour suivant chaque réussite, échec ou blocage.

| Période | Dates | Trades | % gagnants | Profit factor | P&L net | Tentatives terminées | Réussies | Échouées/bloquées |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Ajustement | 2026-09-02 → 2026-10-23 (38 j) | 63 | 41 % | 1.03 | 242.32 $ | 1 | 0 | 1 |
| Validation (hors échantillon) | 2026-10-26 → 2026-11-24 (22 j) | 45 | 33 % | 0.70 | -2 091.26 $ | 2 | 0 | 2 |
| Complet | 2026-09-02 → 2026-11-24 (60 j) | 108 | 38 % | 0.88 | -1 848.94 $ | 3 | 0 | 3 |

**Détail des tentatives (période complète)**

| # | Statut | Début | Fin | Jours | Solde final | Trades | Raison |
|---|---|---|---|---:|---:|---:|---|
| 1 | BLOQUÉ | 2026-09-02 | 2026-10-05 | 24 | 24 152.69 | 34 | bloqué: distance au plancher 599 $ < 3 × risque |
| 2 | BLOQUÉ | 2026-10-06 | 2026-11-05 | 23 | 24 469.73 | 46 | bloqué: distance au plancher 622 $ < 3 × risque |
| 3 | BLOQUÉ | 2026-11-06 | 2026-11-18 | 9 | 23 914.99 | 20 | bloqué: distance au plancher 334 $ < 3 × risque |
| 4 | INACHEVÉ | 2026-11-19 | 2026-11-24 | 4 | 25 613.60 | 8 | fin des données |

- **Taux de réussite** : 0/3 tentatives terminées (0 %) ; **en 3 jours ou moins** : 0 %.
- **Départ un jour quelconque, fenêtre de 3 jours** (58 fenêtres glissantes) : en perte : 37, en gain : 21. Aucune fenêtre n'atteint +2 500 $.
- **Durée moyenne** : réussite — j ; échec/blocage 18.7 j.
- **Cause d'échec la plus fréquente** : bloqué par coupe-circuit plancher (pas une violation FTMO, mais plus aucun trade possible) (3).
- **Coût** : 3 tentatives × 199 € (≈ 214.92 $) = **644.76 $** de frais, pour 0 compte(s) financé(s) ; gain potentiel attendu par tentative (90 % × 2 500 $ × taux de réussite) ≈ **0.00 $**. Espérance nette par tentative ≈ **-214.92 $**.

![Backtest](docs/equity_backtest.png)

### Backtest semaine par semaine (un challenge neuf de 25 000 $ chaque lundi, 5 jours de marché)

Même moteur, mêmes frais et coupe-circuits que le test en direct. Chaque semaine est indépendante. Semaine du 14/09 : US100 n'a de données qu'à partir du 16/09 et son ATR n'est disponible qu'en fin de semaine.

| Semaine | Issue | P&L | Solde final | Solde le plus bas (clôtures) | Trades (gagnants) | Meilleur jour | Pire jour |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-09-14 → 2026-09-18 | objectif non atteint | 781.39 $ | 25 781.39 $ | 25 000.00 $ | 7 (4) | 617.62 $ | -483.10 $ |
| 2026-09-21 → 2026-09-25 | objectif non atteint | -783.31 $ | 24 216.69 $ | 24 147.60 $ | 9 (3) | 260.93 $ | -485.92 $ |
| 2026-09-28 → 2026-10-02 | objectif non atteint | -352.89 $ | 24 647.11 $ | 24 647.11 $ | 11 (4) | 736.40 $ | -498.15 $ |
| 2026-10-05 → 2026-10-09 | objectif non atteint | -1 010.37 $ | 23 989.63 $ | 23 989.63 $ | 10 (2) | 122.91 $ | -486.10 $ |
| 2026-10-12 → 2026-10-16 | objectif non atteint | 514.59 $ | 25 514.59 $ | 25 000.00 $ | 10 (5) | 830.62 $ | -527.20 $ |
| 2026-10-19 → 2026-10-23 | objectif non atteint | 1 099.28 $ | 26 099.28 $ | 24 756.04 $ | 11 (6) | 586.89 $ | -271.90 $ |
| 2026-10-26 → 2026-10-30 | objectif non atteint | -511.13 $ | 24 488.87 $ | 24 488.87 $ | 9 (3) | 251.99 $ | -495.10 $ |
| 2026-11-02 → 2026-11-06 | objectif non atteint | -1 000.71 $ | 23 999.29 $ | 23 891.26 $ | 10 (2) | 226.92 $ | -494.26 $ |
| 2026-11-09 → 2026-11-13 | objectif non atteint | -119.60 $ | 24 880.40 $ | 24 880.40 $ | 12 (5) | 972.92 $ | -489.87 $ |
| 2026-11-16 → 2026-11-20 | objectif non atteint | -543.28 $ | 24 456.72 $ | 23 674.66 $ | 12 (4) | 566.85 $ | -488.66 $ |

**Bilan sur 10 semaines :** 0 réussite(s) du challenge, 3 semaine(s) en gain, 7 en perte ; P&L cumulé -1 926.03 $ (moyenne -192.60 $/semaine) ; meilleure semaine 2026-10-19 (1 099.28 $), pire semaine 2026-10-05 (-1 010.37 $). Objectif requis : +2 500 $ en une semaine.

<details><summary>Détail des trades — semaine du 16/11 (dernière semaine complète)</summary>

| Sortie (UTC) | Instr. | Sens | Motif | P&L | Solde |
|---|---|---|---|---:|---:|
| 2026-11-16T10:45 | GER40 | long | stop-loss | -246.97 | 24 753.03 |
| 2026-11-16T20:45 | US100 | short | clôture fin de journée | 146.93 | 24 899.96 |
| 2026-11-17T10:10 | EURUSD | long | stop-loss | -239.15 | 24 660.81 |
| 2026-11-17T10:40 | GER40 | short | stop-loss | -245.59 | 24 415.22 |
| 2026-11-18T09:10 | GER40 | long | stop-loss | -246.94 | 24 163.73 |
| 2026-11-18T10:10 | EURUSD | short | stop-loss | -241.72 | 23 926.56 |
| 2026-11-19T09:15 | GER40 | long | stop-loss | -245.92 | 23 674.66 |
| 2026-11-19T10:45 | EURUSD | long | objectif | 322.84 | 24 003.48 |
| 2026-11-19T20:05 | US100 | short | objectif | 489.93 | 24 493.41 |
| 2026-11-20T10:00 | GER40 | short | objectif | 456.41 | 24 946.57 |
| 2026-11-20T12:45 | EURUSD | short | stop-loss | -244.08 | 24 705.73 |
| 2026-11-20T15:20 | US100 | long | stop-loss | -249.01 | 24 456.72 |

</details>

**Ajustement (une seule fois, sur la période d'ajustement uniquement, avant le 23/10/2026) :**
1. Backtest instrument par instrument avec les paramètres par défaut (range 15 min, fenêtre d'entrée 2 h, RR 2, filtre ATR 0,08–0,60, filtre de tendance clôture de la veille). Profit factor sur la période d'ajustement : US100 1,07 ; GER40 1,02 ; EURUSD 1,31 ; GBPUSD 0,74 ; US30 0,41 ; XAUUSD 0,24.
2. **Seul changement retenu : sélection des instruments US100, GER40, EURUSD** (profit factor > 1 sur l'ajustement). Une variante RR 1,5 a été testée et **rejetée** (pire : PF 0,74 contre 0,83 sur le portefeuille). Aucun autre paramètre n'a été touché.
3. La période de validation (24/10 → 24/11/2026), jamais utilisée pour choisir, sert de test hors échantillon : elle est nettement **perdante** (PF ≈ 0,7), ce qui confirme que la sélection d'instruments relevait surtout du bruit sur un si petit échantillon.

Note : un 4ᵉ instrument n'a pas été ajouté car aucun autre n'était positif ; réduire à 2 aurait été de la sur-optimisation.


## 3 bis. Recherche d'amélioration (walk-forward sur 2 ans)

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


#### Résultats hors échantillon (trades de test uniquement, 2025-01 → 2026-11, bougies 1 h)

| Stratégie | Trades | Espérance (R/trade) | % gagnants | Profit factor | Total R | Challenges terminés | Réussis | Taux | Jours moyens pour réussir | Espérance nette / tentative |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `mr_v1` | 126 | -0.159 | 36 % | 0.70 | -20.0 | 3 | 0 | 0 % | — | -214.92 $ |
| `orb_ref` | 795 | -0.026 | 45 % | 0.92 | -21.0 | 11 | 2 | 18 % | 52.5 | 194.17 $ |
| `orb_v2_tight` | 790 | -0.058 | 41 % | 0.88 | -46.0 | 15 | 1 | 7 % | 30.0 | -64.92 $ |
| `orb_v3_retest` | 634 | -0.175 | 36 % | 0.68 | -110.9 | 20 | 0 | 0 % | — | -214.92 $ |
| `orb_v4_trend` | 535 | -0.029 | 43 % | 0.93 | -15.3 | 9 | 1 | 11 % | 38.0 | 35.08 $ |

<details><summary>Plis du walk-forward — <code>mr_v1</code></summary>

| Test | Paramètres choisis (sur les 6 mois précédents) | R ajustement | R test (trades) |
|---|---|---:|---:|
| 2025-01-01 → 2025-03-31 | {'EXT_ATR': 0.8, 'TARGET_FRAC': 1.0} | -7.5 | -0.0 (6) |
| 2025-04-01 → 2025-06-30 | {'EXT_ATR': 0.6, 'TARGET_FRAC': 0.6} | -8.9 | -0.8 (5) |
| 2025-07-01 → 2025-09-30 | {'EXT_ATR': 0.4, 'TARGET_FRAC': 0.6} | -5.8 | -4.6 (23) |
| 2025-10-01 → 2025-12-31 | {'EXT_ATR': 0.4, 'TARGET_FRAC': 0.6} | -5.5 | -2.9 (12) |
| 2026-01-01 → 2026-03-31 | {'EXT_ATR': 0.6, 'TARGET_FRAC': 1.0} | -2.3 | 0.8 (12) |
| 2026-04-01 → 2026-06-30 | {'EXT_ATR': 0.4, 'TARGET_FRAC': 0.6} | 1.7 | -1.0 (10) |
| 2026-07-01 → 2026-09-30 | {'EXT_ATR': 0.4, 'TARGET_FRAC': 1.0} | -3.3 | -2.1 (34) |
| 2026-10-01 → 2026-11-20 | {'EXT_ATR': 0.4, 'TARGET_FRAC': 1.0} | 1.6 | -9.4 (24) |

| # | Statut | Début | Fin | Jours | Solde final | Raison |
|---|---|---|---|---:|---:|---|
| 1 | BLOQUÉ | 2025-01-01 | 2025-09-18 | 187 | 23 429.85 | bloqué: distance au plancher 587 $ < 3 × risque |
| 2 | BLOQUÉ | 2025-09-19 | 2026-10-02 | 271 | 23 666.58 | bloqué: distance au plancher 674 $ < 3 × risque |
| 3 | BLOQUÉ | 2026-10-05 | 2026-11-03 | 22 | 23 129.68 | bloqué: distance au plancher 630 $ < 3 × risque |
| 4 | INACHEVÉ | 2026-11-04 | 2026-11-20 | 13 | 24 764.61 | fin des données |

</details>

<details><summary>Plis du walk-forward — <code>orb_ref</code></summary>

| Test | Paramètres choisis (sur les 6 mois précédents) | R ajustement | R test (trades) |
|---|---|---:|---:|
| 2025-01-01 → 2025-03-31 | {'RR': 2.0} | -5.2 | 1.7 (106) |
| 2025-04-01 → 2025-06-30 | {'RR': 2.0} | -15.5 | -4.6 (98) |
| 2025-07-01 → 2025-09-30 | {'RR': 2.0} | -2.9 | -3.4 (112) |
| 2025-10-01 → 2025-12-31 | {'RR': 2.0} | -8.0 | -5.6 (99) |
| 2026-01-01 → 2026-03-31 | {'RR': 2.0} | -8.9 | -9.6 (105) |
| 2026-04-01 → 2026-06-30 | {'RR': 2.0} | -15.2 | -7.7 (117) |
| 2026-07-01 → 2026-09-30 | {'RR': 2.0} | -17.3 | -1.6 (100) |
| 2026-10-01 → 2026-11-20 | {'RR': 2.0} | -9.4 | 9.7 (58) |

| # | Statut | Début | Fin | Jours | Solde final | Raison |
|---|---|---|---|---:|---:|---|
| 1 | RÉUSSI | 2025-01-01 | 2025-04-10 | 72 | 27 619.53 | Objectif atteint (solde 27619.53) et règle du meilleur jour respectée (1022.09 ≤ 50 % de 8232.06) |
| 2 | BLOQUÉ | 2025-04-11 | 2025-05-07 | 19 | 23 164.71 | bloqué: distance au plancher 665 $ < 3 × risque |
| 3 | BLOQUÉ | 2025-05-08 | 2025-06-23 | 33 | 23 876.78 | bloqué: distance au plancher 557 $ < 3 × risque |
| 4 | BLOQUÉ | 2025-06-24 | 2025-09-18 | 63 | 23 831.56 | bloqué: distance au plancher 497 $ < 3 × risque |
| 5 | BLOQUÉ | 2025-09-19 | 2025-11-07 | 36 | 24 038.03 | bloqué: distance au plancher 734 $ < 3 × risque |
| 6 | BLOQUÉ | 2025-11-10 | 2026-01-13 | 47 | 23 786.01 | bloqué: distance au plancher 674 $ < 3 × risque |
| 7 | BLOQUÉ | 2026-01-14 | 2026-02-18 | 26 | 23 102.56 | bloqué: distance au plancher 305 $ < 3 × risque |
| 8 | BLOQUÉ | 2026-02-19 | 2026-04-07 | 34 | 24 232.74 | bloqué: distance au plancher 628 $ < 3 × risque |
| 9 | BLOQUÉ | 2026-04-08 | 2026-05-13 | 26 | 24 502.01 | bloqué: distance au plancher 665 $ < 3 × risque |
| 10 | BLOQUÉ | 2026-05-14 | 2026-09-30 | 100 | 24 146.39 | bloqué: distance au plancher 730 $ < 3 × risque |
| 11 | RÉUSSI | 2026-10-01 | 2026-11-16 | 33 | 27 646.46 | Objectif atteint (solde 27646.46) et règle du meilleur jour respectée (552.77 ≤ 50 % de 4255.82) |
| 12 | INACHEVÉ | 2026-11-17 | 2026-11-20 | 4 | 24 770.93 | fin des données |

</details>

<details><summary>Plis du walk-forward — <code>orb_v2_tight</code></summary>

| Test | Paramètres choisis (sur les 6 mois précédents) | R ajustement | R test (trades) |
|---|---|---:|---:|
| 2025-01-01 → 2025-03-31 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.25, 'RR': 2.0} | -0.0 | 0.9 (107) |
| 2025-04-01 → 2025-06-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.25, 'RR': 1.5} | -11.8 | -8.4 (99) |
| 2025-07-01 → 2025-09-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.25, 'RR': 1.5} | -7.7 | -13.3 (112) |
| 2025-10-01 → 2025-12-31 | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 2.0} | -7.7 | -8.9 (98) |
| 2026-01-01 → 2026-03-31 | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 2.0} | -4.3 | -12.8 (105) |
| 2026-04-01 → 2026-06-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.25, 'RR': 2.0} | -6.2 | 5.2 (114) |
| 2026-07-01 → 2026-09-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.25, 'RR': 2.0} | -0.6 | -10.5 (97) |
| 2026-10-01 → 2026-11-20 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.25, 'RR': 1.5} | -0.6 | 1.9 (58) |

| # | Statut | Début | Fin | Jours | Solde final | Raison |
|---|---|---|---|---:|---:|---|
| 1 | BLOQUÉ | 2025-01-01 | 2025-01-17 | 13 | 23 753.39 | bloqué: distance au plancher 749 $ < 3 × risque |
| 2 | BLOQUÉ | 2025-01-20 | 2025-04-21 | 66 | 25 216.77 | bloqué: distance au plancher 712 $ < 3 × risque |
| 3 | BLOQUÉ | 2025-04-22 | 2025-06-20 | 44 | 24 243.00 | bloqué: distance au plancher 680 $ < 3 × risque |
| 4 | BLOQUÉ | 2025-06-23 | 2025-08-15 | 40 | 23 102.04 | bloqué: distance au plancher 602 $ < 3 × risque |
| 5 | BLOQUÉ | 2025-08-18 | 2025-09-17 | 23 | 23 805.65 | bloqué: distance au plancher 569 $ < 3 × risque |
| 6 | BLOQUÉ | 2025-09-18 | 2025-10-06 | 13 | 23 875.62 | bloqué: distance au plancher 740 $ < 3 × risque |
| 7 | BLOQUÉ | 2025-10-07 | 2025-11-04 | 21 | 24 984.08 | bloqué: distance au plancher 600 $ < 3 × risque |
| 8 | BLOQUÉ | 2025-11-05 | 2025-11-27 | 17 | 23 198.90 | bloqué: distance au plancher 650 $ < 3 × risque |
| 9 | BLOQUÉ | 2025-11-28 | 2026-01-15 | 35 | 24 102.95 | bloqué: distance au plancher 635 $ < 3 × risque |
| 10 | BLOQUÉ | 2026-01-16 | 2026-02-18 | 24 | 23 338.62 | bloqué: distance au plancher 623 $ < 3 × risque |
| 11 | BLOQUÉ | 2026-02-19 | 2026-04-07 | 34 | 23 734.23 | bloqué: distance au plancher 568 $ < 3 × risque |
| 12 | RÉUSSI | 2026-04-08 | 2026-05-19 | 30 | 27 744.30 | Objectif atteint (solde 27744.30) et règle du meilleur jour respectée (859.69 ≤ 50 % de 4813.23) |
| 13 | BLOQUÉ | 2026-05-20 | 2026-07-01 | 31 | 24 259.02 | bloqué: distance au plancher 541 $ < 3 × risque |
| 14 | BLOQUÉ | 2026-07-02 | 2026-08-21 | 37 | 23 986.62 | bloqué: distance au plancher 718 $ < 3 × risque |
| 15 | BLOQUÉ | 2026-08-24 | 2026-09-29 | 27 | 23 345.71 | bloqué: distance au plancher 623 $ < 3 × risque |
| 16 | INACHEVÉ | 2026-09-30 | 2026-11-20 | 38 | 25 315.21 | fin des données |

</details>

<details><summary>Plis du walk-forward — <code>orb_v3_retest</code></summary>

| Test | Paramètres choisis (sur les 6 mois précédents) | R ajustement | R test (trades) |
|---|---|---:|---:|
| 2025-01-01 → 2025-03-31 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 3.0} | -11.8 | -17.4 (82) |
| 2025-04-01 → 2025-06-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 3.0} | -21.8 | -21.0 (78) |
| 2025-07-01 → 2025-09-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 2.0} | -27.5 | -5.5 (78) |
| 2025-10-01 → 2025-12-31 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 2.0} | -17.9 | -23.5 (89) |
| 2026-01-01 → 2026-03-31 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 3.0} | -22.4 | -3.9 (77) |
| 2026-04-01 → 2026-06-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 3.0} | -23.2 | -14.6 (97) |
| 2026-07-01 → 2026-09-30 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 3.0} | -19.5 | -18.4 (86) |
| 2026-10-01 → 2026-11-20 | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 3.0} | -33.1 | -6.5 (47) |

| # | Statut | Début | Fin | Jours | Solde final | Raison |
|---|---|---|---|---:|---:|---|
| 1 | BLOQUÉ | 2025-01-01 | 2025-01-13 | 9 | 23 817.29 | bloqué: distance au plancher 516 $ < 3 × risque |
| 2 | BLOQUÉ | 2025-01-14 | 2025-02-28 | 34 | 23 681.61 | bloqué: distance au plancher 612 $ < 3 × risque |
| 3 | BLOQUÉ | 2025-03-03 | 2025-03-21 | 15 | 23 248.84 | bloqué: distance au plancher 749 $ < 3 × risque |
| 4 | BLOQUÉ | 2025-03-24 | 2025-04-09 | 13 | 23 758.48 | bloqué: distance au plancher 623 $ < 3 × risque |
| 5 | BLOQUÉ | 2025-04-10 | 2025-05-07 | 20 | 24 403.64 | bloqué: distance au plancher 688 $ < 3 × risque |
| 6 | BLOQUÉ | 2025-05-08 | 2025-06-17 | 29 | 23 450.44 | bloqué: distance au plancher 679 $ < 3 × risque |
| 7 | BLOQUÉ | 2025-06-18 | 2025-06-30 | 9 | 23 046.36 | bloqué: distance au plancher 546 $ < 3 × risque |
| 8 | BLOQUÉ | 2025-07-01 | 2025-09-09 | 51 | 25 166.67 | bloqué: distance au plancher 648 $ < 3 × risque |
| 9 | BLOQUÉ | 2025-09-10 | 2025-10-01 | 16 | 23 201.53 | bloqué: distance au plancher 590 $ < 3 × risque |
| 10 | BLOQUÉ | 2025-10-02 | 2025-11-18 | 34 | 23 145.76 | bloqué: distance au plancher 590 $ < 3 × risque |
| 11 | BLOQUÉ | 2025-11-19 | 2025-12-04 | 12 | 23 082.97 | bloqué: distance au plancher 583 $ < 3 × risque |
| 12 | BLOQUÉ | 2025-12-05 | 2025-12-29 | 17 | 23 368.15 | bloqué: distance au plancher 521 $ < 3 × risque |
| 13 | BLOQUÉ | 2025-12-30 | 2026-01-26 | 20 | 24 029.51 | bloqué: distance au plancher 705 $ < 3 × risque |
| 14 | BLOQUÉ | 2026-01-27 | 2026-04-29 | 67 | 23 893.19 | bloqué: distance au plancher 709 $ < 3 × risque |
| 15 | BLOQUÉ | 2026-04-30 | 2026-05-26 | 19 | 24 149.81 | bloqué: distance au plancher 663 $ < 3 × risque |
| 16 | BLOQUÉ | 2026-05-27 | 2026-06-30 | 25 | 23 246.54 | bloqué: distance au plancher 747 $ < 3 × risque |
| 17 | BLOQUÉ | 2026-07-01 | 2026-09-02 | 46 | 23 238.88 | bloqué: distance au plancher 739 $ < 3 × risque |
| 18 | BLOQUÉ | 2026-09-03 | 2026-09-28 | 18 | 23 036.61 | bloqué: distance au plancher 513 $ < 3 × risque |
| 19 | BLOQUÉ | 2026-09-29 | 2026-10-28 | 22 | 23 321.58 | bloqué: distance au plancher 653 $ < 3 × risque |
| 20 | BLOQUÉ | 2026-10-29 | 2026-11-20 | 17 | 24 160.64 | bloqué: distance au plancher 709 $ < 3 × risque |

</details>

<details><summary>Plis du walk-forward — <code>orb_v4_trend</code></summary>

| Test | Paramètres choisis (sur les 6 mois précédents) | R ajustement | R test (trades) |
|---|---|---:|---:|
| 2025-01-01 → 2025-03-31 | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 1.5} | -0.4 | -2.2 (74) |
| 2025-04-01 → 2025-06-30 | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 1.5} | -8.3 | -4.5 (64) |
| 2025-07-01 → 2025-09-30 | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 2.0} | -5.6 | -2.7 (75) |
| 2025-10-01 → 2025-12-31 | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 3.0} | 1.1 | 1.3 (73) |
| 2026-01-01 → 2026-03-31 | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 3.0} | -0.1 | -3.2 (70) |
| 2026-04-01 → 2026-06-30 | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 3.0} | -1.8 | -3.4 (76) |
| 2026-07-01 → 2026-09-30 | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 3.0} | -5.5 | -10.7 (66) |
| 2026-10-01 → 2026-11-20 | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 1.5} | -6.3 | 9.9 (37) |

| # | Statut | Début | Fin | Jours | Solde final | Raison |
|---|---|---|---|---:|---:|---|
| 1 | BLOQUÉ | 2025-01-01 | 2025-06-09 | 114 | 24 413.66 | bloqué: distance au plancher 669 $ < 3 × risque |
| 2 | BLOQUÉ | 2025-06-10 | 2025-08-13 | 47 | 23 384.67 | bloqué: distance au plancher 735 $ < 3 × risque |
| 3 | BLOQUÉ | 2025-08-14 | 2025-11-04 | 59 | 24 178.43 | bloqué: distance au plancher 632 $ < 3 × risque |
| 4 | BLOQUÉ | 2025-11-05 | 2026-01-21 | 56 | 24 605.42 | bloqué: distance au plancher 555 $ < 3 × risque |
| 5 | BLOQUÉ | 2026-01-22 | 2026-04-07 | 54 | 24 354.37 | bloqué: distance au plancher 660 $ < 3 × risque |
| 6 | BLOQUÉ | 2026-04-08 | 2026-06-08 | 44 | 25 503.82 | bloqué: distance au plancher 596 $ < 3 × risque |
| 7 | BLOQUÉ | 2026-06-09 | 2026-08-28 | 59 | 23 816.45 | bloqué: distance au plancher 701 $ < 3 × risque |
| 8 | BLOQUÉ | 2026-08-31 | 2026-09-29 | 22 | 23 616.56 | bloqué: distance au plancher 731 $ < 3 × risque |
| 9 | RÉUSSI | 2026-09-30 | 2026-11-20 | 38 | 27 539.86 | Objectif atteint (solde 27539.86) et règle du meilleur jour respectée (474.45 ≤ 50 % de 3674.46) |

</details>

#### Données de qualité broker (Dukascopy) contre Yahoo — 21/09 → 20/11/2026, bougies 5 min

Dukascopy publie gratuitement le bid et l'ask minute par minute. Les bougies sont calculées au prix milieu, et le spread réel de chaque bougie remplace le spread fixe de la config (le glissement et les commissions restent identiques). Le troisième jeu de données (« Dukascopy, spread fixe ») isole l'effet de la qualité des prix, sans l'effet du coût.

**Ce qu'on apprend :**
- Les spreads réels sont **plus faibles** que ceux de la config pour les indices et le FX (EURUSD ≈ 0,3 pip contre 1 pip). Ils sont en revanche **plus élevés** pour l'or.
- Le plus gros écart ne vient pas du spread mais **des prix eux-mêmes** : avec le même spread fixe, `aggressive_v1` passe de −10 R (Yahoo) à −1 R (Dukascopy). Les bougies Yahoo des contrats à terme (NQ=F, YM=F) ne sont pas les CFD cotés par un broker : les plus hauts et plus bas diffèrent, et donc les stops touchés aussi.
- Avec les prix de broker, `aggressive_v1` et `orb_ref` sont **à l'équilibre** (+0,02 à +0,03 R par trade), pas gagnants. `orb_v4_trend` reste la seule variante nettement positive (+0,11 R/trade, 90 trades), mais elle était déjà négative sur 2 ans en walk-forward (bougies 1 h). Deux mois ne suffisent pas à conclure.
- Sur la période, il y a 0 ou 1 challenge réussi par variante et par jeu de données.


| Instrument | Spread médian réel | Spread médian à l'ouverture | Spread config |
|---|---:|---:|---:|
| US100 | 1.4528 | 0.9685 | 2 |
| US30 | 1.9788 | 1.4932 | 3 |
| XAUUSD | 0.566 | 0.542 | 0.35 |
| GER40 | 1.6416 | 1.1438 | 2 |
| EURUSD | 2.8e-05 | 2.8e-05 | 0.0001 |
| GBPUSD | 5.8e-05 | 5.6e-05 | 0.00012 |

| Stratégie | Données | Trades | R/trade | Profit factor | P&L net | Challenges réussis / terminés |
|---|---|---:|---:|---:|---:|---:|
| `aggressive_v1` | Yahoo, spread fixe pessimiste | 93 | -0.110 | 0.81 | -2 547.17 $ | 0 / 3 |
| `aggressive_v1` | Dukascopy, spread réel | 96 | 0.022 | 1.04 | 537.47 $ | 1 / 2 |
| `aggressive_v1` | Dukascopy, spread fixe pessimiste | 96 | -0.011 | 0.98 | -261.47 $ | 1 / 3 |
| `orb_ref` | Yahoo, spread fixe pessimiste | 114 | -0.070 | 0.87 | -1 998.27 $ | 0 / 2 |
| `orb_ref` | Dukascopy, spread réel | 128 | 0.029 | 1.06 | 936.72 $ | 0 / 1 |
| `orb_ref` | Dukascopy, spread fixe pessimiste | 127 | 0.019 | 1.04 | 591.68 $ | 0 / 1 |
| `orb_v4_trend` | Yahoo, spread fixe pessimiste | 69 | 0.172 | 1.35 | 2 964.05 $ | 1 / 2 |
| `orb_v4_trend` | Dukascopy, spread réel | 90 | 0.114 | 1.25 | 2 564.96 $ | 1 / 2 |
| `orb_v4_trend` | Dukascopy, spread fixe pessimiste | 92 | 0.136 | 1.32 | 3 120.17 $ | 1 / 2 |
| `orb_v2_tight` | Yahoo, spread fixe pessimiste | 137 | -0.145 | 0.75 | -4 978.44 $ | 0 / 3 |
| `orb_v2_tight` | Dukascopy, spread réel | 137 | -0.066 | 0.88 | -2 254.07 $ | 1 / 4 |
| `orb_v2_tight` | Dukascopy, spread fixe pessimiste | 137 | -0.067 | 0.87 | -2 277.66 $ | 1 / 4 |

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


**Sélection libre entre les 6 familles** : 330 trades, -0.082 R/trade, profit factor 0.84, challenges réussis 0 / 6, P&L net -6 309.34 $

| Test | Stratégie | Paramètres | Instruments | R ajustement | R test (trades) |
|---|---|---|---|---:|---:|
| 2026-03-01 → 2026-04-30 | `orb_v5_grid` | {'OR_MINUTES': 30, 'TREND': 'prev', 'RR': 3.0, 'STOP_MODE': 'or'} | XAUUSD, GER40, US30 | 20.5 | 2.5 (75) |
| 2026-05-01 → 2026-06-30 | `orb_v3_retest` | {'STOP_MODE': 'atr', 'STOP_ATR': 0.2, 'RR': 2.0} | GBPUSD, US30, US100, XAUUSD | 20.6 | -14.1 (94) |
| 2026-07-01 → 2026-08-31 | `orb_v4_trend` | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 2.0} | EURUSD, US100, US30, XAUUSD | 30.8 | -5.4 (67) |
| 2026-09-01 → 2026-10-31 | `orb_v4_trend` | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 2.0} | EURUSD, US100, XAUUSD, US30 | 15.7 | -3.5 (77) |
| 2026-11-01 → 2026-11-20 | `mr_v1` | {'EXT_ATR': 0.4, 'TARGET_FRAC': 1.0} | US30, US100 | 21.3 | -6.4 (17) |

| # | Statut | Début | Fin | Jours | Solde final |
|---|---|---|---|---:|---:|
| 1 | BLOQUÉ | 2026-03-02 | 2026-05-12 | 52 | 25 615.53 |
| 2 | BLOQUÉ | 2026-05-13 | 2026-06-11 | 22 | 24 235.50 |
| 3 | BLOQUÉ | 2026-06-12 | 2026-06-30 | 13 | 22 958.54 |
| 4 | BLOQUÉ | 2026-07-01 | 2026-08-03 | 24 | 23 490.12 |
| 5 | BLOQUÉ | 2026-08-04 | 2026-09-09 | 27 | 24 305.63 |
| 6 | BLOQUÉ | 2026-09-10 | 2026-11-09 | 43 | 23 454.37 |
| 7 | INACHEVÉ | 2026-11-10 | 2026-11-20 | 9 | 24 631.02 |

**`orb_v4_trend` seule** : 275 trades, 0.069 R/trade, profit factor 1.14, challenges réussis 3 / 7, P&L net 4 268.85 $

| Test | Stratégie | Paramètres | Instruments | R ajustement | R test (trades) |
|---|---|---|---|---:|---:|
| 2026-03-01 → 2026-04-30 | `orb_v4_trend` | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 3.0} | US100, US30, GER40, GBPUSD | 11.8 | 5.5 (61) |
| 2026-05-01 → 2026-06-30 | `orb_v4_trend` | {'STOP_MODE': 'mid', 'STOP_ATR': 0.0, 'RR': 3.0} | GER40, US100 | 18.3 | 7.8 (46) |
| 2026-07-01 → 2026-08-31 | `orb_v4_trend` | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 2.0} | EURUSD, US100, US30, XAUUSD | 30.8 | -5.4 (67) |
| 2026-09-01 → 2026-10-31 | `orb_v4_trend` | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 2.0} | EURUSD, US100, XAUUSD, US30 | 15.7 | -3.5 (77) |
| 2026-11-01 → 2026-11-20 | `orb_v4_trend` | {'STOP_MODE': 'or', 'STOP_ATR': 0.0, 'RR': 3.0} | EURUSD, GER40, XAUUSD | 13.0 | 14.6 (24) |

| # | Statut | Début | Fin | Jours | Solde final |
|---|---|---|---|---:|---:|
| 1 | BLOQUÉ | 2026-03-02 | 2026-03-17 | 12 | 23 631.69 |
| 2 | RÉUSSI | 2026-03-18 | 2026-04-30 | 32 | 27 738.70 |
| 3 | RÉUSSI | 2026-05-01 | 2026-05-26 | 18 | 27 775.33 |
| 4 | BLOQUÉ | 2026-05-27 | 2026-06-18 | 17 | 23 326.79 |
| 5 | BLOQUÉ | 2026-06-19 | 2026-08-03 | 32 | 24 343.06 |
| 6 | BLOQUÉ | 2026-08-04 | 2026-09-09 | 27 | 24 305.63 |
| 7 | RÉUSSI | 2026-09-10 | 2026-11-11 | 45 | 27 554.43 |
| 8 | INACHEVÉ | 2026-11-12 | 2026-11-20 | 7 | 25 593.20 |

| Famille (meilleurs paramètres de chaque tranche) | Trades | R/trade | Profit factor | Total R |
|---|---:|---:|---:|---:|
| `orb_ref` | 290 | -0.062 | 0.87 | -18.1 |
| `orb_v2_tight` | 263 | -0.100 | 0.84 | -26.4 |
| `orb_v3_retest` | 266 | -0.110 | 0.82 | -29.4 |
| `orb_v4_trend` | 275 | 0.069 | 1.14 | 19.0 |
| `orb_v5_grid` | 311 | 0.015 | 1.03 | 4.7 |
| `mr_v1` | 130 | -0.014 | 0.98 | -1.8 |

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


## 4. Audit du repo source

Repo audité : <https://github.com/Jakeschincariol/day-trader-skill> (licence MIT), lu intégralement avant toute exécution (11 skills, ~8 500 lignes Python + tests).

**Sécurité — rien de suspect trouvé :**
- Python 3 bibliothèque standard uniquement, aucune dépendance à installer, aucun `eval`/`exec`, aucun code obfusqué ni base64.
- Seuls appels réseau : endpoints publics gratuits et sans clé — Yahoo Finance (`query1/query2.finance.yahoo.com`, flux RSS), Stooq, Nasdaq Trader (listes de symboles), SEC EDGAR, House Clerk (déclarations du Congrès). Aucun envoi de données personnelles (seul un User-Agent avec nom/email est demandé par la SEC, à fournir par l'utilisateur).
- Un seul `subprocess` : `pdftotext` local pour lire les PDF du Congrès (`trader-pelosi`).
- `trader-broker` ne passe **aucun** ordre : il fabrique un ticket que Claude envoie à un serveur MCP courtier (Alpaca par défaut, paper par défaut) uniquement après un « oui » explicite. Aucun service payant appelé.

**Ce que fait le skill :** un pack de 11 skills orientés **actions US** (pas CFD, pas forex, pas FTMO) :
| Skill | Rôle |
|---|---|
| trader-scanner | Scan de milliers d'actions US : cassures du range d'ouverture (ORB, bougies 5 min, range des 15 premières minutes), bull flags, RSI survendu / rebond |
| trader-entry | Surveille un setup bougie par bougie (ORB, cassure de niveau) et signale l'entrée à la clôture d'une bougie au-delà du range |
| trader-exit | Place stop (autre côté du range / ATR) et objectif (multiple de R) avant l'entrée |
| trader-timemachine | Monte-Carlo (10 000 sessions rééchantillonnées) + historique des fois où le setup a fonctionné |
| trader-risk / trader-budget | Limites de perte, taille de position selon le risque max par trade |
| trader-broker | Tickets d'ordres (Alpaca, paper par défaut), jamais sans confirmation |
| trader-alerts, trader-news, trader-analyst, trader-pelosi | Alertes de prix, news, analyse de résultats (SEC), déclarations de trades du Congrès |

Unités de temps : bougies 5 min (intraday), 1 jour (scanner quotidien). Signaux : ORB, cassures de niveau, flags, RSI. Gestion du risque : risque fixe par trade, stop obligatoire, R-multiples.

**Conclusion de l'audit :** le skill ne contient pas de « stratégie gagnante » backtestée : c'est une boîte à outils pour actions US. Son seul setup intraday mécanique est l'**ORB 15 minutes en 5 min**, c'est donc lui qui sert de base à `aggressive_v1`, transposé aux sessions de Londres et New York sur les CFD FTMO. Le code du skill n'est pas copié tel quel (il cible des actions et l'API Yahoo brute) ; le simulateur réimplémente la logique ORB dans un module séparé.


## 5. Fonctionnement du simulateur

- **Workflow** `.github/workflows/simulate.yml` : cron toutes les 5 min du lundi au vendredi, 06:00–21:55 UTC (sessions de Londres et New York), plus lancement manuel. Chaque exécution : `python run.py` → récupère les bougies 5 min (Yahoo Finance via `yfinance`, gratuit, sans clé), rejoue les bougies clôturées pas encore traitées, applique la stratégie, le simulateur et le moteur de règles FTMO, met à jour `state/state.json`, `data/`, `RAPPORT.md`, `docs/equity_live.png`, puis commite et pousse.
- **Arrêt automatique** : la date de fin est codée en dur (`LIVE_END_DATE = 2026-12-01`, soit 1 semaine = 5 jours de marché du 25/11 au 01/12 dans `sim/config.py`) et vérifiée à chaque exécution ; si le premier lancement est postérieur au 25/11, la fin est fixée à 5 jours de marché après ce lancement (stockée dans l'état). Après la fin, le workflow se désactive lui-même.
- **Retard du cron** : aucune entrée n'est prise sur une bougie clôturée depuis plus de 15 min ; les bougies manquées servent seulement à gérer stops et objectifs via leurs plus hauts / plus bas. Pas de scalping : 1 entrée max par instrument et par jour.
- **Exécution simulée** : achat au prix + demi-spread + glissement, vente au prix − demi-spread − glissement ; glissement doublé sur les stops ; ouverture en gap au-delà du stop remplie au prix d'ouverture ; si stop et objectif sont dans la même bougie, le stop est retenu. Spreads (US100 2 pts, GER40 2 pts, US30 3 pts, or 0,35 $, EURUSD 1 pip, GBPUSD 1,2 pip) et commissions (≈ 5 $/lot A/R en FX, 0 sur indices) volontairement au-dessus des valeurs typiques FTMO.
- **Moteur de règles FTMO** (`sim/engine.py`) : perte journalière 750 $ (référence = solde à 00:00 Prague, equity flottante au pire prix de la bougie), plancher trailing = plus haut solde de fin de journée − 2 500 $ (ne descend jamais), objectif 27 500 $ + règle du meilleur jour (≤ 50 %), levier 1:100, clôture de tout à 21:45 Prague (21:30 le vendredi). Violation → « CHALLENGE ÉCHOUÉ » + raison + heure, puis observation sans trading.
- **Coupe-circuits** : perte du jour ≥ 600 $ → clôture et arrêt ; refus si perte du jour + risque ouvert + nouveau risque > 600 $ ; arrêt dès 1 250 $ de profit clôturé dans la journée ; 2 positions max, jamais 2 positions corrélées de même sens (US100/US30/GER40 ; EURUSD/GBPUSD) ; pas d'entrée à ± 5 min de NFP / CPI / Fed / BCE ; refus si distance au plancher < 3 × risque ; risque fixe 250 $ (jamais augmenté après une perte, ni martingale ni grid).
- **Ajouter une stratégie** : créer `strategies/ma_strategie.py` avec une classe `Strategy(BaseStrategy)` (méthodes `prepare`, `signal`, `exit_now`), puis `python backtest.py --strategy ma_strategie` ; pour le direct, changer `ACTIVE_STRATEGY` dans `sim/config.py` et supprimer `state/state.json`.


## 6. Limites du test

- **Données gratuites ≠ prix FTMO** : Yahoo fournit des contrats à terme (NQ=F pour US100, YM=F pour US30, GC=F pour l'or), l'indice DAX au comptant (^GDAXI, heures d'ouverture Xetra uniquement) et un flux FX agrégé. Les CFD FTMO (MT5/cTrader) ont leurs propres prix, spreads variables (plus larges à l'ouverture et pendant les annonces) et un financement overnight (sans objet ici, tout est clôturé chaque jour). Les données Yahoo des futures peuvent avoir ~10 min de retard et des bougies manquantes.
- **Bougies 5 min** : l'ordre réel des prix à l'intérieur d'une bougie est inconnu ; l'hypothèse « stop d'abord » est pessimiste mais pas exacte. FTMO mesure l'equity tick à tick ; ici le pire prix de chaque bougie est utilisé, ce qui s'en approche.
- **Cron GitHub Actions** : retards fréquents de 5 à 20 min, voire exécutions sautées aux heures chargées ; les entrées peuvent donc être manquées (jamais prises en retard au-delà de 15 min).
- **Échantillon minuscule** : ~60 jours de trading et ~100 trades en backtest ; 5 jours en direct. Aucune conclusion statistique solide n'est possible sur 3 jours.
- **Fenêtre de test en direct** : 25 novembre – 1er décembre 2026, dont la semaine de Thanksgiving (marchés US fermés le jeudi 26, séance courte le vendredi 27) : volumes et volatilité atypiques, moins d'opportunités sur US100.
- **Calendrier macro** codé à la main (NFP calculé, CPI/Fed/BCE listés) : dates à vérifier, annonces secondaires ignorées.
- **Conversion EUR/USD** du GER40 fixée à 1,08 ; levier 1:100 appliqué uniformément (FTMO applique des leviers plus faibles sur certains instruments).
- Le simulateur n'est pas validé contre un compte FTMO réel ; il reproduit les règles telles que décrites dans la mission.

