"""Téléchargeur de ticks Dukascopy (gratuit, sans clé) -> bougies 5 min bid/ask avec spread réel.

Flux : https://datafeed.dukascopy.com/datafeed/<SYM>/<AAAA>/<MM-1>/<JJ>/<HH>h_ticks.bi5
Chaque fichier = 1 heure de ticks, LZMA, enregistrements de 20 octets :
  uint32 ms depuis le début de l'heure, uint32 ask, uint32 bid, float ask_vol, float bid_vol
Sortie : data/duka/<SYM>_5m.csv.gz avec open/high/low/close (prix milieu), spread_avg, spread_max (en prix).

Usage : python tools/dukascopy.py --start 2026-09-01 --end 2026-11-20 [--symbols US100,EURUSD] [--probe]
"""
import argparse
import lzma
import os
import struct
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import pandas as pd

# symbole FTMO -> (symbole Dukascopy, diviseur de prix)
SYMS = {
    "US100": ("USATECHIDXUSD", 1e3), "US30": ("USA30IDXUSD", 1e3), "GER40": ("DEUIDXEUR", 1e3),
    "XAUUSD": ("XAUUSD", 1e3), "EURUSD": ("EURUSD", 1e5), "GBPUSD": ("GBPUSD", 1e5),
}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "duka")
MISSING = []
UA = {"User-Agent": "Mozilla/5.0 (research backtest)"}


def fetch_hour(dsym, div, dt):
    url = f"https://datafeed.dukascopy.com/datafeed/{dsym}/{dt.year}/{dt.month - 1:02d}/{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
    for attempt in range(8):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []
            time.sleep(min(60, 3 * 2 ** attempt))
        except Exception:
            time.sleep(min(60, 3 * 2 ** attempt))
    else:
        MISSING.append(url)
        return []
    if not raw:
        return []
    d = lzma.decompress(raw)
    base = dt.timestamp() * 1000
    return [(base + ms, a / div, b / div) for ms, a, b, _, _ in struct.iter_unpack(">IIIff", d)]


def hours(start, end):
    t = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    stop = datetime(end.year, end.month, end.day, 23, tzinfo=timezone.utc)
    while t <= stop:
        if t.weekday() < 5 and 5 <= t.hour <= 21:   # sessions Londres + New York
            yield t
        t += timedelta(hours=1)


def build(sym, start, end, workers=2):
    dsym, div = SYMS[sym]
    hs = list(hours(start, end))
    ticks = []
    with ThreadPoolExecutor(workers) as ex:
        for part in ex.map(lambda h: fetch_hour(dsym, div, h), hs):
            ticks += part
    if not ticks:
        return pd.DataFrame()
    df = pd.DataFrame(ticks, columns=["ms", "ask", "bid"])
    df.index = pd.to_datetime(df["ms"], unit="ms", utc=True)
    df["mid"] = (df["ask"] + df["bid"]) / 2
    df["spread"] = df["ask"] - df["bid"]
    g = df.resample("5min")
    bars = pd.DataFrame({"open": g["mid"].first(), "high": g["mid"].max(), "low": g["mid"].min(),
                         "close": g["mid"].last(), "spread_avg": g["spread"].mean(),
                         "spread_max": g["spread"].max(), "ticks": g["mid"].count()}).dropna()
    return bars


def fetch_day_candles(dsym, div, d, side):
    """Bougies 1 min d'une journée (BID ou ASK) : 1 fichier par jour au lieu de 24 fichiers de ticks."""
    url = f"https://datafeed.dukascopy.com/datafeed/{dsym}/{d.year}/{d.month - 1:02d}/{d.day:02d}/{side}_candles_min_1.bi5"
    for attempt in range(8):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return pd.DataFrame()
            time.sleep(min(60, 3 * 2 ** attempt))
        except Exception:
            time.sleep(min(60, 3 * 2 ** attempt))
    else:
        MISSING.append(url)
        return pd.DataFrame()
    if not raw:
        return pd.DataFrame()
    recs = list(struct.iter_unpack(">IIIIIf", lzma.decompress(raw)))
    base = datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()
    df = pd.DataFrame(recs, columns=["sec", "open", "close", "low", "high", "vol"])
    df.index = pd.to_datetime(base + df["sec"], unit="s", utc=True)
    for c in ("open", "close", "low", "high"):
        df[c] = df[c] / div
    return df[df["vol"] > 0][["open", "high", "low", "close"]]


def build_from_candles(sym, start, end, out_path):
    """Bougies 5 min (prix milieu) + spread moyen/max réel calculé sur les bougies 1 min ask-bid.
    Sauvegarde après chaque journée : une coupure ne fait rien perdre."""
    dsym, div = SYMS[sym]
    parts = []
    if os.path.exists(out_path):
        old = pd.read_csv(out_path, index_col=0)
        old.index = pd.to_datetime(old.index, utc=True)
        parts.append(old)
    done = {ts.date() for ts in parts[0].index} if parts else set()
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in done:
            b, a = fetch_day_candles(dsym, div, d, "BID"), fetch_day_candles(dsym, div, d, "ASK")
            if len(b) and len(a):
                j = b.join(a, lsuffix="_b", rsuffix="_a", how="inner")
                mid = pd.DataFrame({k: (j[k + "_b"] + j[k + "_a"]) / 2 for k in ("open", "high", "low", "close")})
                mid["spread"] = j["close_a"] - j["close_b"]
                g = mid.resample("5min")
                bars = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                                     "close": g["close"].last(), "spread_avg": g["spread"].mean(),
                                     "spread_max": g["spread"].max(), "ticks": g["close"].count()}).dropna()
                parts.append(bars)
                pd.concat(parts).sort_index().to_csv(out_path, float_format="%.6f")
                print(f"{sym} {d}: {len(bars)} bougies 5 min", flush=True)
        d += timedelta(days=1)
    return pd.concat(parts).sort_index() if parts else pd.DataFrame()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--symbols", default=",".join(SYMS))
    ap.add_argument("--probe", action="store_true", help="1 heure par instrument, juste pour tester l'accès")
    a = ap.parse_args()
    s, e = date.fromisoformat(a.start), date.fromisoformat(a.end)
    if a.probe:
        ok = True
        for sym in a.symbols.split(","):
            dsym, div = SYMS[sym]
            try:
                t = fetch_hour(dsym, div, datetime(e.year, e.month, e.day, 14, tzinfo=timezone.utc))
                sp = sorted(x[1] - x[2] for x in t)
                print(f"PROBE {sym}: {len(t)} ticks, prix {t[0][1]:.5f}/{t[0][2]:.5f}, spread médian {sp[len(sp)//2]:.5f}" if t else f"PROBE {sym}: 0 tick")
            except Exception as ex:
                ok = False
                print(f"PROBE {sym}: ERREUR {ex}")
        sys.exit(0 if ok else 1)
    os.makedirs(OUT, exist_ok=True)
    for sym in a.symbols.split(","):
        t0 = time.time()
        b = build_from_candles(sym, s, e, os.path.join(OUT, f"{sym}_5m.csv.gz"))
        print(f"{sym}: heures manquantes après nouvelles tentatives : {len(MISSING)}", flush=True)
        MISSING.clear()
        print(f"{sym}: {len(b)} bougies, spread moyen {b['spread_avg'].mean() if len(b) else float('nan'):.5f} ({time.time() - t0:.0f}s)", flush=True)
