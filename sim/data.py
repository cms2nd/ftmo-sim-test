"""Données intraday gratuites (Yahoo Finance via yfinance, sans clé API).

Les données sont mises en cache dans data/<SYM>_5m.csv et fusionnées à chaque
appel: le cache grossit au fil du temps et le backtest peut ainsi dépasser
la limite de 60 jours de Yahoo pour l'intervalle 5 minutes.
"""
from __future__ import annotations

import os
from datetime import timezone

import pandas as pd

from . import config as C

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _cache_path(sym, interval="5m"):
    return os.path.join(DATA_DIR, f"{sym}_{interval}.csv")


def load_cache(sym, interval="5m") -> pd.DataFrame:
    p = _cache_path(sym, interval)
    if not os.path.exists(p):
        return pd.DataFrame(columns=["open", "high", "low", "close"])
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    if interval == "60m":  # quelques barres Yahoo irrégulières (xx:30) : écartées
        df = df[df.index.minute == 0]
    return df


def fetch(sym, period="5d") -> pd.DataFrame:
    import yfinance as yf
    t = C.INSTRUMENTS[sym]["yahoo"]
    df = yf.download(t, period=period, interval="5m", progress=False, auto_adjust=False, threads=False)
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close"])
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    df = df[(df["high"] >= df["low"]) & (df["close"] > 0)]
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def update(sym, period="5d") -> pd.DataFrame:
    old = load_cache(sym)
    try:
        new = fetch(sym, period)
    except Exception as e:  # source indisponible: on garde le cache
        print(f"[data] {sym}: échec téléchargement ({e})")
        new = old.iloc[0:0]
    df = pd.concat([old, new])
    df = df[~df.index.duplicated(keep="last")].sort_index()
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(_cache_path(sym), float_format="%.6f")
    return df


def complete_bars(df: pd.DataFrame, now_utc) -> pd.DataFrame:
    """Supprime la bougie en cours de formation (début + 5 min > maintenant)."""
    return df[df.index + pd.Timedelta(minutes=5) <= pd.Timestamp(now_utc)]


def load_duka(sym) -> pd.DataFrame:
    """Bougies 5 min Dukascopy (prix milieu + spread moyen réel de la bougie)."""
    p = os.path.join(DATA_DIR, "duka", f"{sym}_5m.csv.gz")
    if not os.path.exists(p):
        return pd.DataFrame(columns=["open", "high", "low", "close", "spread"])
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[df["ticks"] >= 3]
    return df.rename(columns={"spread_avg": "spread"})[["open", "high", "low", "close", "spread"]]
