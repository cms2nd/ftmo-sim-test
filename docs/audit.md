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
