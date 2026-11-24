"""Configuration globale du simulateur FTMO (paper trading uniquement)."""
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")
NY = ZoneInfo("America/New_York")
LONDON = ZoneInfo("Europe/London")

ACTIVE_STRATEGY = "aggressive_v1"

# --- Date de fin codée en dur (3 jours de marché à partir du 25/11/2026) ---
# Mer 25/11, Jeu 26/11 (Thanksgiving: marchés US fermés, Europe ouverte), Ven 27/11.
LIVE_START_DATE = "2026-11-25"
LIVE_END_DATE = "2026-11-27"      # inclus, heure de Prague
# Garde-fou: si le premier lancement a lieu plus tard, run.py fixe une fin
# à 3 jours de marché après le premier lancement (stockée dans state.json),
# sans jamais dépasser HARD_STOP_DATE.
HARD_STOP_DATE = "2026-12-31"

# --- Règles FTMO 1-Step 25k ---
INITIAL_BALANCE = 25_000.0
PROFIT_TARGET = 2_500.0
MAX_DAILY_LOSS = 750.0          # 3 % du capital initial
MAX_TRAILING_LOSS = 2_500.0     # 10 % sous le plus haut solde de fin de journée
BEST_DAY_RATIO = 0.50
MAX_LEVERAGE = 100.0
CHALLENGE_FEE_EUR = 199.0
PROFIT_SPLIT = 0.90

# --- Instruments (proxys de données gratuites Yahoo) ---
# value_per_point_usd: valeur en $ d'un mouvement de 1.0 du prix pour 1 unité.
# spread: écart bid/ask complet (en points de prix), typique FTMO ou pire.
# slippage: glissement pessimiste par ordre (points); doublé sur les stops.
# commission_rate: par côté, en fraction du notionnel ($5/lot A/R en FX ≈ 0.0025 % par côté).
INSTRUMENTS = {
    "US100":  dict(yahoo="NQ=F",     usd_per_point=1.0,  spread=2.0,     slippage=1.5,     commission_rate=0.0,       group="US_IDX",  session="NY"),
    "US30":   dict(yahoo="YM=F",     usd_per_point=1.0,  spread=3.0,     slippage=3.0,     commission_rate=0.0,       group="US_IDX",  session="NY"),
    "XAUUSD": dict(yahoo="GC=F",     usd_per_point=1.0,  spread=0.35,    slippage=0.25,    commission_rate=0.000035,  group="GOLD",    session="NY"),
    "GER40":  dict(yahoo="^GDAXI",   usd_per_point=1.08, spread=2.0,     slippage=1.5,     commission_rate=0.0,       group="EU_IDX",  session="LDN"),
    "EURUSD": dict(yahoo="EURUSD=X", usd_per_point=1.0,  spread=0.00010, slippage=0.00005, commission_rate=0.000025,  group="USD_FX",  session="LDN"),
    "GBPUSD": dict(yahoo="GBPUSD=X", usd_per_point=1.0,  spread=0.00012, slippage=0.00006, commission_rate=0.000025,  group="USD_FX",  session="LDN"),
}
# Groupes corrélés: interdiction de 2 positions de même sens dans un même ensemble.
CORRELATED = [{"US_IDX", "EU_IDX"}, {"USD_FX"}]

# --- Coupe-circuits aggressive_v1 ---
RISK_PER_TRADE = 250.0
DAILY_STOP_LOSS = 600.0
DAILY_STOP_PROFIT = 1_250.0
MAX_OPEN_POSITIONS = 2
NEWS_BLACKOUT_MIN = 5
FLOOR_BUFFER_MULT = 3.0
# Heure de Prague après laquelle tout est clôturé (day trading)
FLATTEN_PRAGUE = (21, 45)
FRIDAY_FLATTEN_PRAGUE = (21, 30)
