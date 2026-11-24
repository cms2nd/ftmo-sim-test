"""Historique Dukascopy par morceaux mensuels (téléchargement parallèle sur GitHub Actions).

  plan   : liste JSON des morceaux (sym, mois) pas encore terminés -> matrice du workflow
  merge  : fusionne data/duka/parts/*.csv.gz + data/duka/{sym}_5m.csv.gz -> data/duka/{sym}_5m.csv.gz
Un morceau est terminé quand son fichier .done existe (écrit par le workflow après un téléchargement complet).
"""
import glob, json, os, sys
from datetime import date
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "data", "duka", "parts")
SYMS = ["US100", "US30", "GER40", "XAUUSD", "EURUSD", "GBPUSD"]
FIRST, LAST = (2024, 11), (2026, 8)   # sept.→nov. 2026 déjà présents


def months():
    y, m = FIRST
    while (y, m) <= LAST:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def plan(limit=256):
    out = []
    for y, m in months():
        end = (date(y + (m == 12), m % 12 + 1, 1) - pd.Timedelta(days=1).to_pytimedelta())
        for sym in SYMS:
            tag = f"{sym}_{y}-{m:02d}"
            if not os.path.exists(os.path.join(PARTS, tag + ".done")):
                out.append(dict(sym=sym, tag=tag, start=f"{y}-{m:02d}-01", end=end.isoformat()))
    return out[:limit]


def merge():
    for sym in SYMS:
        files = sorted(glob.glob(os.path.join(PARTS, f"{sym}_*.csv.gz")))
        main = os.path.join(ROOT, "data", "duka", f"{sym}_5m.csv.gz")
        dfs = [pd.read_csv(f, index_col=0) for f in files + ([main] if os.path.exists(main) else [])]
        if not dfs:
            continue
        df = pd.concat(dfs)
        df.index = pd.to_datetime(df.index, utc=True)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        df.to_csv(main, float_format="%.6f")
        print(sym, len(df), df.index.min(), df.index.max())


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        print(json.dumps(plan()))
    else:
        merge()
