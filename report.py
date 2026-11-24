"""Génère RAPPORT.md (et les graphiques PNG) à partir de l'état live et du backtest."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim import config as C

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")


def _read(p, default=""):
    p = os.path.join(ROOT, p)
    return open(p).read() if os.path.exists(p) else default


def _fmt(x, nd=2):
    return "—" if x is None else (f"{x:,.{nd}f}".replace(",", " "))


def _style(ax, title):
    ax.set_title(title, loc="left", fontsize=11, color="#222")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.tick_params(colors="#555", labelsize=8)


def plot_live(s):
    pts = s.get("equity_curve", [])
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=110)
    if pts:
        t = [datetime.fromisoformat(p[0]) for p in pts]
        ax.plot(t, [p[1] for p in pts], color="#2a6fdb", lw=1.6, label="Equity")
        ax.plot(t, [p[2] for p in pts], color="#888", lw=1, ls="--", label="Solde")
    ax.axhline(C.INITIAL_BALANCE + C.PROFIT_TARGET, color="#1a9e5a", lw=1, label="Objectif 27 500 $")
    ax.axhline(s["floor"], color="#d64545", lw=1, label="Plancher perte max")
    ax.axhline(s["day_start_balance"] - C.MAX_DAILY_LOSS, color="#e8a33d", lw=1, ls=":", label="Limite perte du jour")
    _style(ax, "Test en direct — equity (USD)")
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "equity_live.png"))
    plt.close(fig)


def plot_backtest(bt):
    curve = bt.get("curve", [])
    if not curve:
        return
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=110)
    attempts = sorted({c[1] for c in curve})
    for a in attempts:
        pts = [c for c in curve if c[1] == a]
        ax.plot([datetime.fromisoformat(p[0]) for p in pts], [p[2] for p in pts], lw=1.4, label=f"Tentative {a}")
    ax.axhline(C.INITIAL_BALANCE + C.PROFIT_TARGET, color="#1a9e5a", lw=1)
    ax.axhline(C.INITIAL_BALANCE, color="#999", lw=0.8, ls=":")
    _style(ax, "Backtest aggressive_v1 — equity par tentative (USD)")
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "equity_backtest.png"))
    plt.close(fig)


def best_day(s):
    pos = {d: v for d, v in s["daily_closed_pnl"].items() if v > 0}
    if not pos:
        return None, 0.0, 0.0
    d = max(pos, key=pos.get)
    return d, pos[d], sum(pos.values())


def live_section(s):
    L = []
    eq = s.get("equity", s["balance"])
    L.append(f"- Stratégie active : `{s.get('strategy')}` — premier lancement : {s.get('first_run', '—')} UTC — "
             f"fin du test : **{s.get('live_end_date')}** (heure de Prague){' — **TEST TERMINÉ**' if s.get('test_finished') else ''}")
    L.append(f"- Dernière exécution : {s.get('last_run', '—')} UTC")
    L.append(f"- Solde : **{_fmt(s['balance'])} $** — equity : {_fmt(eq)} $ — plancher perte max : {_fmt(s['floor'])} $ "
             f"— plus haut solde de fin de journée : {_fmt(s['max_eod_balance'])} $")
    if s["status"] != "EN COURS":
        L.append(f"- **{s['status']}** le {s['status_time']} : {s['status_reason']}")
    L.append("\n![Courbe d'equity live](docs/equity_live.png)\n")
    L.append("### P&L par jour (trades clôturés, jour de Prague)\n")
    L.append("| Jour | P&L clôturé |\n|---|---:|")
    for d, v in sorted(s["daily_closed_pnl"].items()):
        L.append(f"| {d} | {_fmt(v)} $ |")
    if not s["daily_closed_pnl"]:
        L.append("| — | — |")
    d, b, tot = best_day(s)
    ok = d is not None and b <= C.BEST_DAY_RATIO * tot
    L.append("\n### Règle du meilleur jour\n")
    if d is None:
        L.append("Aucun jour positif pour l'instant.")
    else:
        L.append(f"Meilleur jour : {d} = {_fmt(b)} $ ; somme des jours positifs = {_fmt(tot)} $ ; "
                 f"ratio = {b / tot:.0%} → **{'respectée' if ok else 'NON respectée (doit être ≤ 50 %)'}**")
    L.append("\n### Positions ouvertes\n")
    if s["positions"]:
        L.append("| Instr. | Sens | Unités | Entrée | Stop | Objectif | Heure |\n|---|---|---:|---:|---:|---:|---|")
        for p in s["positions"]:
            L.append(f"| {p['sym']} | {p['side']} | {p['units']:.3f} | {p['entry']:.5g} | {p['stop']:.5g} | {p['target']:.5g} | {p['entry_time']} |")
    else:
        L.append("Aucune.")
    L.append("\n### Journal des trades\n")
    L.append("| Instr. | Sens | Entrée (UTC) | Prix | Sortie (UTC) | Prix | Motif | P&L | Solde |\n|---|---|---|---:|---|---:|---|---:|---:|")
    for t in s["trades"]:
        L.append(f"| {t['sym']} | {t['side']} | {t['entry_time'][:16]} | {t['entry']:.5g} | {t['exit_time'][:16]} | "
                 f"{t['exit']:.5g} | {t['reason']} | {_fmt(t['pnl'])} | {_fmt(t['balance'])} |")
    if not s["trades"]:
        L.append("| — | | | | | | aucun trade pour l'instant | | |")
    L.append("\n### Coupe-circuits déclenchés\n")
    if s["breakers"]:
        L.append("| Heure (UTC) | Type | Instr. | Raison |\n|---|---|---|---|")
        for b in s["breakers"][-200:]:
            L.append(f"| {b['time'][:16]} | {b['kind']} | {b.get('sym', '')} | {b['reason']} |")
    else:
        L.append("Aucun.")
    return "\n".join(L)


def backtest_section(bt):
    if not bt:
        return "_Backtest non disponible._"
    full, tune, valid, roll = bt["full"], bt["tune"], bt["valid"], bt["rolling3"]

    def row(name, r):
        return (f"| {name} | {r['first_day']} → {r['last_day']} ({r['trading_days']} j) | {r['n_trades']} | "
                f"{_fmt((r['win_rate'] or 0) * 100, 0)} % | {_fmt(r['profit_factor'])} | {_fmt(r['net_pnl'])} $ | "
                f"{r['n_completed']} | {r['n_pass']} | {r['n_fail']} |")
    L = [bt.get("intro", ""),
         "| Période | Dates | Trades | % gagnants | Profit factor | P&L net | Tentatives terminées | Réussies | Échouées/bloquées |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|",
         row("Ajustement", tune), row("Validation (hors échantillon)", valid), row("Complet", full), ""]
    L.append("**Détail des tentatives (période complète)**\n")
    L.append("| # | Statut | Début | Fin | Jours | Solde final | Trades | Raison |\n|---|---|---|---|---:|---:|---:|---|")
    for a in full["attempts"]:
        L.append(f"| {a['attempt']} | {a['status']} | {a['start']} | {a['end']} | {a['days']} | {_fmt(a['balance'])} | {a['trades']} | {a['reason']} |")
    n = full["n_completed"]
    L.append("")
    L.append(f"- **Taux de réussite** : {full['n_pass']}/{n} tentatives terminées "
             f"({_fmt((full['pass_rate'] or 0) * 100, 0)} %) ; **en 3 jours ou moins** : {_fmt((full['pass_rate_3d'] or 0) * 100, 0)} %.")
    L.append(f"- **Départ un jour quelconque, fenêtre de 3 jours** ({roll['n']} fenêtres glissantes) : "
             + ", ".join(f"{k} : {v}" for k, v in roll["counts"].items()) + ". Aucune fenêtre n'atteint +2 500 $.")
    L.append(f"- **Durée moyenne** : réussite {_fmt(full['avg_days_pass'], 1)} j ; échec/blocage {_fmt(full['avg_days_fail'], 1)} j.")
    L.append(f"- **Cause d'échec la plus fréquente** : " + ", ".join(f"{k} ({v})" for k, v in full["fail_causes"].items()) + ".")
    L.append(f"- **Coût** : {n} tentatives × 199 € (≈ {_fmt(full['fee_per_attempt_usd'])} $) = **{_fmt(full['fees_usd'])} $** de frais, "
             f"pour {full['n_pass']} compte(s) financé(s) ; gain potentiel attendu par tentative (90 % × 2 500 $ × taux de réussite) "
             f"≈ **{_fmt(full['expected_payout_per_attempt_usd'])} $**. Espérance nette par tentative ≈ "
             f"**{_fmt(full['expected_payout_per_attempt_usd'] - full['fee_per_attempt_usd'])} $**.")
    L.append("\n![Backtest](docs/equity_backtest.png)\n")
    L.append(weekly_section(bt.get("weekly")))
    L.append(bt.get("tuning_note", ""))
    return "\n".join(L)


def weekly_section(wk):
    if not wk:
        return ""
    L = ["### Backtest semaine par semaine (un challenge neuf de 25 000 $ chaque lundi, 5 jours de marché)\n",
         "Même moteur, mêmes frais et coupe-circuits que le test en direct. Chaque semaine est indépendante. "
         "Semaine du 14/09 : US100 n'a de données qu'à partir du 16/09 et son ATR n'est disponible qu'en fin de semaine.\n",
         "| Semaine | Issue | P&L | Solde final | Solde le plus bas (clôtures) | Trades (gagnants) | Meilleur jour | Pire jour |",
         "|---|---|---:|---:|---:|---:|---:|---:|"]
    for w in wk:
        L.append(f"| {w['week']} → {w['end']} | {w['status']} | {_fmt(w['pnl'])} $ | {_fmt(w['balance'])} $ | "
                 f"{_fmt(w['min_balance'])} $ | {w['trades']} ({w['wins']}) | {_fmt(w['best_day'])} $ | {_fmt(w['worst_day'])} $ |")
    n = len(wk)
    pos = sum(1 for w in wk if w["pnl"] > 0)
    passed = sum(1 for w in wk if w["status"] == "RÉUSSI")
    tot = sum(w["pnl"] for w in wk)
    best = max(wk, key=lambda w: w["pnl"])
    worst = min(wk, key=lambda w: w["pnl"])
    L.append("")
    L.append(f"**Bilan sur {n} semaines :** {passed} réussite(s) du challenge, {pos} semaine(s) en gain, {n - pos} en perte ; "
             f"P&L cumulé {_fmt(tot)} $ (moyenne {_fmt(tot / n)} $/semaine) ; meilleure semaine {best['week']} "
             f"({_fmt(best['pnl'])} $), pire semaine {worst['week']} ({_fmt(worst['pnl'])} $). "
             f"Objectif requis : +2 500 $ en une semaine.\n")
    for w in wk:
        if w["week"] == "2026-11-16":
            L.append("<details><summary>Détail des trades — semaine du 16/11 (dernière semaine complète)</summary>\n")
            L.append("| Sortie (UTC) | Instr. | Sens | Motif | P&L | Solde |\n|---|---|---|---|---:|---:|")
            for d in w["detail"]:
                L.append(f"| {d[0]} | {d[1]} | {d[2]} | {d[3]} | {_fmt(d[4])} | {_fmt(d[5])} |")
            L.append("\n</details>\n")
    return "\n".join(L)


def research_section():
    import glob
    files = sorted(glob.glob(os.path.join(DOCS, "research", "wf_*.json")))
    if not files:
        return ""
    L = [_read("docs/research/methode.md"),
         "\n#### Résultats hors échantillon (trades de test uniquement, 2025-01 → 2026-11, bougies 1 h)\n",
         "| Stratégie | Trades | Espérance (R/trade) | % gagnants | Profit factor | Total R | Challenges terminés | Réussis | Taux | Jours moyens pour réussir | Espérance nette / tentative |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for f in files:
        w = json.load(open(f))
        name = os.path.basename(f)[3:-5]
        o, c = w["oos"], w["challenge"]
        net = (c["expected_payout_per_attempt_usd"] or 0) - (c["fee_per_attempt_usd"] or 0)
        L.append(f"| `{name}` | {o['n']} | {_fmt(o['exp_R'], 3)} | {_fmt((o['win'] or 0) * 100, 0)} % | {_fmt(o['pf'])} | "
                 f"{_fmt(o['tot_R'], 1)} | {c['n_completed']} | {c['n_pass']} | {_fmt((c['pass_rate'] or 0) * 100, 0)} % | "
                 f"{_fmt(c['avg_days_pass'], 1)} | {_fmt(net)} $ |")
    for f in files:
        w = json.load(open(f))
        name = os.path.basename(f)[3:-5]
        L.append(f"\n<details><summary>Plis du walk-forward — <code>{name}</code></summary>\n")
        L.append("| Test | Paramètres choisis (sur les 6 mois précédents) | R ajustement | R test (trades) |\n|---|---|---:|---:|")
        for r in w["folds"]:
            L.append(f"| {r['test']} | {r['params']} | {r['train_R']} | {r['test_R']} ({r['test_n']}) |")
        L.append("\n| # | Statut | Début | Fin | Jours | Solde final | Raison |\n|---|---|---|---|---:|---:|---|")
        for a in w["attempts"]:
            L.append(f"| {a['attempt']} | {a['status']} | {a['start']} | {a['end']} | {a['days']} | {_fmt(a['balance'])} | {a['reason']} |")
        L.append("\n</details>")
    L.append("\n" + _read("docs/research/conclusion.md"))
    return "\n".join(L)


def write_report():
    from run import load_state
    os.makedirs(DOCS, exist_ok=True)
    s = load_state()
    bt = json.load(open(os.path.join(DOCS, "backtest_summary.json"))) if os.path.exists(os.path.join(DOCS, "backtest_summary.json")) else None
    if bt:
        plot_backtest(bt["full"])
    out = ["# RAPPORT — Simulation FTMO Challenge 1-Step 25 000 $ (paper trading)\n"]
    if s:
        plot_live(s)
        eq = s.get("equity", s["balance"])
        dl = max(0.0, s["day_start_balance"] - eq)
        out.append(f"> **{s['status']}** — solde {_fmt(s['balance'])} $ — perte du jour {_fmt(dl)} $ / 750 $ — "
                   f"distance au plancher {_fmt(eq - s['floor'])} $ — mis à jour {s.get('last_run', '')[:16]} UTC\n")
    else:
        out.append("> **EN ATTENTE** — le test en direct n'a pas encore démarré.\n")
    out.append("⚠️ Simulation uniquement : aucun argent réel, aucun compte de courtage ni FTMO connecté.\n")
    out.append("## Sommaire\n1. Verdict\n2. Test en direct\n3. Backtest de validation\n3 bis. Recherche d'amélioration (walk-forward)\n4. Audit du repo source\n5. Fonctionnement du simulateur\n6. Limites du test\n")
    out.append("## 1. Verdict\n\n" + _read("docs/verdict.md", "_à venir_"))
    out.append("## 2. Test en direct\n\n" + (live_section(s) if s else "_Pas encore démarré._"))
    out.append("\n## 3. Backtest de validation\n\n" + backtest_section(bt))
    rs = research_section()
    if rs:
        out.append("\n## 3 bis. Recherche d'amélioration (walk-forward sur 2 ans)\n\n" + rs)
    out.append("\n## 4. Audit du repo source\n\n" + _read("docs/audit.md"))
    out.append("\n## 5. Fonctionnement du simulateur\n\n" + _read("docs/fonctionnement.md"))
    out.append("\n## 6. Limites du test\n\n" + _read("docs/limites.md"))
    with open(os.path.join(ROOT, "RAPPORT.md"), "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    write_report()
