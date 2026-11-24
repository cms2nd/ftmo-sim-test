**Ajustement (une seule fois, sur la période d'ajustement uniquement, avant le 23/10/2026) :**
1. Backtest instrument par instrument avec les paramètres par défaut (range 15 min, fenêtre d'entrée 2 h, RR 2, filtre ATR 0,08–0,60, filtre de tendance clôture de la veille). Profit factor sur la période d'ajustement : US100 1,07 ; GER40 1,02 ; EURUSD 1,31 ; GBPUSD 0,74 ; US30 0,41 ; XAUUSD 0,24.
2. **Seul changement retenu : sélection des instruments US100, GER40, EURUSD** (profit factor > 1 sur l'ajustement). Une variante RR 1,5 a été testée et **rejetée** (pire : PF 0,74 contre 0,83 sur le portefeuille). Aucun autre paramètre n'a été touché.
3. La période de validation (24/10 → 24/11/2026), jamais utilisée pour choisir, sert de test hors échantillon : elle est nettement **perdante** (PF ≈ 0,7), ce qui confirme que la sélection d'instruments relevait surtout du bruit sur un si petit échantillon.

Note : un 4ᵉ instrument n'a pas été ajouté car aucun autre n'était positif ; réduire à 2 aurait été de la sur-optimisation.
