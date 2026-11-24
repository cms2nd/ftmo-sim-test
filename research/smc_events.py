"""Étude d'événements : que fait l'or après le franchissement d'un niveau de liquidité ?

Événement = première fois du jour où le prix dépasse un niveau évident (plus haut/bas asiatique,
plus haut/bas de la veille) pendant une killzone (Londres 07-10h, New York 08:30-11h).
Deux issues, mesurées sur les SWEEP_BARS bougies suivantes (sans regarder plus loin) :
  - balayage : une clôture revient de l'autre côté du niveau (thèse SMC : retournement attendu)
  - cassure  : le prix reste au-delà (thèse d'Osler : cascade de stops, prolongement attendu)
Puis on mesure le rendement à 30 min, 1 h, 2 h et à la clôture de New York (15:50), à partir
de la clôture qui confirme l'issue, en unités d'ATR journalier, dans le sens « retournement »
pour les balayages et « prolongement » pour les cassures.
Comparaison avec un hasard : mêmes heures, jours tirés au hasard, direction aléatoire.
Écart-type, t de Student et intervalle de confiance bootstrap 95 %.

Usage : python -m research.smc_events [début] [fin]
"""
import json, os, sys
import numpy as np
import pandas as pd

from sim import config as C
from sim.data import load_duka

SWEEP_BARS = 3
HORIZONS = {"30 min": 6, "1 h": 12, "2 h": 24}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research")


def features(df):
    d = df[["open", "high", "low", "close"]].copy()
    ldn, ny = d.index.tz_convert(C.LONDON), d.index.tz_convert(C.NY)
    d["ldate"] = ldn.date
    lm, nm = ldn.hour * 60 + ldn.minute, ny.hour * 60 + ny.minute
    d["kz"] = np.where((lm >= 420) & (lm < 600), "Londres", np.where((nm >= 510) & (nm < 660), "New York", ""))
    d["ny_end"] = (nm >= 950) & (lm >= 720)   # 15:50 New York, le même après-midi (pas la veille au soir)
    asia = d[lm < 420].groupby("ldate").agg(a_hi=("high", "max"), a_lo=("low", "min"))
    daily = d.groupby("ldate").agg(hi=("high", "max"), lo=("low", "min"), cl=("close", "last"))
    pc = daily["cl"].shift(1)
    tr = pd.concat([daily["hi"] - daily["lo"], (daily["hi"] - pc).abs(), (daily["lo"] - pc).abs()], axis=1).max(axis=1)
    lv = pd.DataFrame({"pdh": daily["hi"].shift(1), "pdl": daily["lo"].shift(1),
                       "atr": tr.rolling(14, min_periods=5).mean().shift(1)}).join(asia)
    return d.join(lv, on="ldate")


def events(d):
    out = []
    for day, g in d.groupby("ldate"):
        g = g.reset_index()
        if g["atr"].isna().all():
            continue
        atr = g["atr"].iloc[0]
        levels = [("Asie haut", "hi", g["a_hi"].iloc[0]), ("Asie bas", "lo", g["a_lo"].iloc[0]),
                  ("Veille haut", "hi", g["pdh"].iloc[0]), ("Veille bas", "lo", g["pdl"].iloc[0])]
        H, L, Cl = g["high"].values, g["low"].values, g["close"].values
        run_hi, run_lo = np.maximum.accumulate(H), np.minimum.accumulate(L)
        ny_end = np.where(g["ny_end"].values)[0]
        end_i = ny_end[0] if len(ny_end) else len(g) - 1
        for name, side, lvl in levels:
            if pd.isna(lvl):
                continue
            for i in range(1, len(g)):
                prev_ext = run_hi[i - 1] if side == "hi" else run_lo[i - 1]
                if (side == "hi" and prev_ext > lvl) or (side == "lo" and prev_ext < lvl):
                    break   # déjà franchi plus tôt dans la journée : plus « frais »
                crossed = H[i] > lvl if side == "hi" else L[i] < lvl
                if not crossed:
                    continue
                if not g["kz"].iloc[i]:
                    break
                j_back = None
                for j in range(i, min(i + SWEEP_BARS, len(g))):
                    if (side == "hi" and Cl[j] < lvl) or (side == "lo" and Cl[j] > lvl):
                        j_back = j
                        break
                kind = "balayage" if j_back is not None else "cassure"
                j0 = j_back if j_back is not None else min(i + SWEEP_BARS - 1, len(g) - 1)
                # sens attendu : retournement pour un balayage, prolongement pour une cassure
                sgn = (-1 if side == "hi" else 1) * (1 if kind == "balayage" else -1)
                ev = dict(day=str(day), ts=str(g.iloc[i, 0]), level=name, side=side, kind=kind, kz=g["kz"].iloc[i],
                          depth_atr=float(((H[i] - lvl) if side == "hi" else (lvl - L[i])) / atr))
                for h, n in HORIZONS.items():
                    k = j0 + n
                    ev[h] = float(sgn * (Cl[k] - Cl[j0]) / atr) if k < len(g) and k <= end_i + n else None
                ev["NY clôture"] = float(sgn * (Cl[end_i] - Cl[j0]) / atr) if end_i > j0 else None
                out.append(ev)
                break
    return pd.DataFrame(out)


def random_baseline(d, ev, n_rep=20, seed=1):
    """Mêmes heures de la journée que les événements, jours au hasard, direction au hasard."""
    rng = np.random.default_rng(seed)
    days = list(d.groupby("ldate"))
    idx = {day: g.reset_index() for day, g in days}
    keys = list(idx)
    res = {h: [] for h in list(HORIZONS) + ["NY clôture"]}
    for _ in range(n_rep):
        for _, e in ev.iterrows():
            g = idx[keys[rng.integers(len(keys))]]
            tod = pd.Timestamp(e["ts"]).tz_convert(C.LONDON).time()
            pos = np.where(g.iloc[:, 0].dt.tz_convert(C.LONDON).dt.time >= tod)[0]
            if not len(pos) or g["atr"].isna().all():
                continue
            j0, atr, Cl, sgn = pos[0], g["atr"].iloc[0], g["close"].values, rng.choice([-1, 1])
            nye = np.where(g["ny_end"].values)[0]
            end_i = nye[0] if len(nye) else len(g) - 1
            for h, n in HORIZONS.items():
                if j0 + n < len(g):
                    res[h].append(sgn * (Cl[j0 + n] - Cl[j0]) / atr)
            if end_i > j0:
                res["NY clôture"].append(sgn * (Cl[end_i] - Cl[j0]) / atr)
    return res


def summarize(x, seed=0):
    x = np.array([v for v in x if v is not None and v == v], dtype=float)
    if len(x) < 5:
        return dict(n=len(x))
    rng = np.random.default_rng(seed)
    boots = [rng.choice(x, len(x)).mean() for _ in range(2000)]
    return dict(n=int(len(x)), mean=round(float(x.mean()), 4), t=round(float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))), 2),
                hit=round(float((x > 0).mean()), 3), ci95=[round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)])


def main(start="2025-11-01", end="2026-11-20", tag="dev"):
    df = load_duka("XAUUSD")
    df = df[(df.index >= pd.Timestamp(start, tz="UTC") - pd.Timedelta(days=40)) & (df.index <= pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))]
    d = features(df)
    ev = events(d)
    ev = ev[(ev["day"] >= start) & (ev["day"] <= end)]
    H = list(HORIZONS) + ["NY clôture"]
    res = {"period": [start, end], "n_days": int(d[(d.index >= pd.Timestamp(start, tz="UTC"))]["ldate"].nunique()), "groups": {}}
    for kind in ("balayage", "cassure"):
        sub = ev[ev["kind"] == kind]
        res["groups"][kind] = {h: summarize(sub[h]) for h in H}
        for kz in ("Londres", "New York"):
            s2 = sub[sub["kz"] == kz]
            res["groups"][f"{kind} · {kz}"] = {h: summarize(s2[h]) for h in H}
        for lv in ("Asie", "Veille"):
            s2 = sub[sub["level"].str.startswith(lv)]
            res["groups"][f"{kind} · niveau {lv}"] = {h: summarize(s2[h]) for h in H}
    rb = random_baseline(d, ev)
    res["groups"]["hasard (même heure, direction aléatoire)"] = {h: summarize(rb[h]) for h in H}
    res["share_sweep"] = round(float((ev["kind"] == "balayage").mean()), 3)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"smc_events_{tag}.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    ev.to_csv(os.path.join(OUT, f"smc_events_{tag}.csv"), index=False)
    for g, v in res["groups"].items():
        print(f"{g:45s}", " | ".join(f"{h}: n={v[h].get('n')} m={v[h].get('mean')} t={v[h].get('t')}" for h in H))
    print("part de balayages :", res["share_sweep"])
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    main(*a) if a else main()
