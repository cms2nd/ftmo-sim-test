"""Infographies (PNG) envoyées sur Telegram : carte du jour, carte de recherche."""
import json, os, sys
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["text.parse_math"] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import config as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "cards")
BG, FG, MUTED, GREEN, RED, BLUE, AMBER = "#0f172a", "#f8fafc", "#94a3b8", "#22c55e", "#ef4444", "#60a5fa", "#f59e0b"


def _money(x, sign=True):
    s = f"{abs(x):,.0f}".replace(",", " ")
    return (("+" if x >= 0 else "−") if sign else ("" if x >= 0 else "−")) + s + " $"


def _fig(h=10.5):
    fig = plt.figure(figsize=(7.2, h), dpi=150, facecolor=BG)
    return fig


def _tile(fig, x, y, w, h, label, value, color=FG):
    ax = fig.add_axes([x, y, w, h]); ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color="#1e293b", transform=ax.transAxes))
    ax.text(0.07, 0.68, label, color=MUTED, fontsize=10, transform=ax.transAxes)
    ax.text(0.07, 0.22, value, color=color, fontsize=19, weight="bold", transform=ax.transAxes)


def daily_card(state_path=os.path.join(ROOT, "state", "state.json"), day=None):
    s = json.load(open(state_path))
    day = day or s["day"]
    pnl_day = s["daily_closed_pnl"].get(day, 0.0)
    bal = s["balance"]; prog = bal - C.INITIAL_BALANCE
    trades = [t for t in s["trades"] if t["exit_time"] and
              datetime.fromisoformat(t["exit_time"]).astimezone(C.PRAGUE).date().isoformat() == day]
    fig = _fig()
    fig.text(0.06, 0.955, "FTMO 25k · paper trading", color=MUTED, fontsize=11)
    fig.text(0.06, 0.915, f"Bilan du {datetime.fromisoformat(day):%d/%m/%Y}", color=FG, fontsize=22, weight="bold")
    st = s["status"]; stc = GREEN if "RÉUSSI" in st else RED if "ÉCHOU" in st else BLUE
    fig.text(0.06, 0.88, f"Statut : {st}" + (f" — {s['status_reason']}" if s.get("status_reason") else ""), color=stc, fontsize=11)
    _tile(fig, 0.06, 0.76, 0.42, 0.095, "P&L du jour", _money(pnl_day), GREEN if pnl_day >= 0 else RED)
    _tile(fig, 0.52, 0.76, 0.42, 0.095, "Solde", _money(bal, False))
    _tile(fig, 0.06, 0.65, 0.42, 0.095, "Trades du jour", f"{len(trades)}  ({sum(t['pnl'] > 0 for t in trades)} gagnants)")
    _tile(fig, 0.52, 0.65, 0.42, 0.095, "Marge au plancher", _money(bal - s["floor"], False), AMBER)
    # progression vers l'objectif
    ax = fig.add_axes([0.06, 0.585, 0.88, 0.03]); ax.set_axis_off()
    ax.set_xlim(-C.MAX_TOTAL_LOSS if hasattr(C, "MAX_TOTAL_LOSS") else -2500, C.PROFIT_TARGET)
    lo = ax.get_xlim()[0]
    ax.barh(0, C.PROFIT_TARGET - lo, left=lo, color="#1e293b", height=1)
    ax.barh(0, prog, left=0, color=GREEN if prog >= 0 else RED, height=1)
    ax.axvline(0, color=MUTED, lw=1)
    fig.text(0.06, 0.625, f"Objectif +2 500 $ : {_money(prog)} ({prog / C.PROFIT_TARGET * 100:.0f} %)", color=FG, fontsize=11)
    # courbe d'equity
    ax = fig.add_axes([0.1, 0.30, 0.84, 0.24], facecolor=BG)
    pts = s.get("equity_curve", [])
    if pts:
        t = [datetime.fromisoformat(p[0]) for p in pts]
        ax.plot(t, [p[1] for p in pts], color=BLUE, lw=1.8)
    ax.axhline(C.INITIAL_BALANCE + C.PROFIT_TARGET, color=GREEN, lw=1, ls="--")
    ax.axhline(s["floor"], color=RED, lw=1, ls="--")
    ax.set_title("Equity depuis le début du test", color=MUTED, fontsize=10, loc="left")
    for sp in ax.spines.values(): sp.set_color("#334155")
    ax.tick_params(colors=MUTED, labelsize=7)
    fig.autofmt_xdate()
    # liste des trades
    y = 0.215
    fig.text(0.06, y, "Trades du jour", color=MUTED, fontsize=10); y -= 0.03
    for t in trades[:7]:
        h = datetime.fromisoformat(t["entry_time"]).astimezone(C.PRAGUE).strftime("%H:%M")
        fig.text(0.06, y, f"{h}  {t['sym']:<7} {t['side']:<5} {t['reason']:<10}", color=FG, fontsize=10, family="monospace")
        fig.text(0.94, y, _money(t["pnl"]), color=GREEN if t["pnl"] >= 0 else RED, fontsize=10, ha="right", family="monospace")
        y -= 0.025
    if not trades:
        fig.text(0.06, y, "Aucun trade (pas de signal ou coupe-circuit).", color=FG, fontsize=10)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"jour_{day}.png"); fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


def research_card():
    d = json.load(open(os.path.join(ROOT, "docs", "research", "duka_compare.json")))
    fig = _fig(8.5)
    fig.text(0.06, 0.94, "Recherche · 21/09 → 20/11/2026", color=MUTED, fontsize=11)
    fig.text(0.06, 0.895, "Prix Yahoo vs prix broker", color=FG, fontsize=22, weight="bold")
    ax = fig.add_axes([0.24, 0.30, 0.70, 0.52], facecolor=BG)
    strats = list(dict.fromkeys(r["strategy"] for r in d["runs"]))
    labels = ["Yahoo", "Dukascopy, spread réel"]
    cols = [MUTED, BLUE]
    for j, lab in enumerate(labels):
        vals = [next(r["pnl"] for r in d["runs"] if r["strategy"] == s and r["data"].startswith(lab.split(",")[0]) and
                     (("réel" in r["data"]) == ("réel" in lab) or lab == "Yahoo")) for s in strats]
        ax.barh([i + (0.2 if j == 0 else -0.2) for i in range(len(strats))], vals, height=0.38, color=cols[j], label=lab)
    ax.set_yticks(range(len(strats))); ax.set_yticklabels(strats, color=FG, fontsize=10)
    ax.invert_yaxis(); ax.axvline(0, color=MUTED, lw=1)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8)
    for sp in ax.spines.values(): sp.set_color("#334155")
    ax.set_title("P&L net sur 2 mois (USD)", color=MUTED, fontsize=10, loc="left")
    ax.legend(frameon=False, labelcolor=FG, fontsize=9, loc="lower right")
    txt = ("• Spreads réels ≈ 2× plus faibles (sauf or).\n"
           "• Les prix broker changent plus le résultat que le spread.\n"
           "• aggressive_v1 ≈ équilibre ; seule orb_v4_trend gagne,\n   mais elle perdait sur 2 ans.\n"
           "• Verdict : pas d'avantage fiable pour réussir FTMO.")
    fig.text(0.06, 0.05, txt, color=FG, fontsize=11, linespacing=1.6)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "recherche_dukascopy.png"); fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


def wf_card():
    R = os.path.join(ROOT, "docs", "research")
    allw, v4 = json.load(open(os.path.join(R, "wf_duka.json"))), json.load(open(os.path.join(R, "wf_duka_v4.json")))
    fig = _fig(11)
    fig.text(0.06, 0.955, "Backtest 1 an · prix broker · hors échantillon", color=MUTED, fontsize=11)
    fig.text(0.06, 0.915, "Mars → novembre 2026", color=FG, fontsize=22, weight="bold")
    c1, c2 = allw["challenge"], v4["challenge"]
    _tile(fig, 0.06, 0.79, 0.42, 0.095, "Meilleure strat. à chaque tranche", f"{allw['oos']['exp_R']:+.2f} R/trade", RED)
    _tile(fig, 0.52, 0.79, 0.42, 0.095, "Challenges réussis", f"{c1['n_pass']} / {c1['n_completed']}", RED)
    _tile(fig, 0.06, 0.68, 0.42, 0.095, "orb_v4_trend seule", f"{v4['oos']['exp_R']:+.2f} R/trade", GREEN)
    _tile(fig, 0.52, 0.68, 0.42, 0.095, "Challenges réussis", f"{c2['n_pass']} / {c2['n_completed']}", GREEN)
    ax = fig.add_axes([0.1, 0.36, 0.84, 0.27], facecolor=BG)
    for w, col, lab in ((allw, RED, "Sélection libre"), (v4, GREEN, "orb_v4_trend")):
        pts = w.get("curve", [])
        if pts:
            ax.plot([datetime.fromisoformat(str(p[0])) for p in pts], [p[2] for p in pts], color=col, lw=1.6, label=lab)
    ax.set_title("Solde du challenge en cours (chaque chute = nouvelle tentative)", color=MUTED, fontsize=9, loc="left")
    ax.legend(frameon=False, labelcolor=FG, fontsize=9)
    for sp in ax.spines.values(): sp.set_color("#334155")
    ax.tick_params(colors=MUTED, labelsize=7); fig.autofmt_xdate()
    txt = ("• Choisir la meilleure stratégie du passé = sur-ajustement :\n   gagnante en ajustement, perdante en test 4 fois sur 5.\n"
           f"• orb_v4_trend : {_money(c2['net_pnl'])} net, mais non significatif (t ≈ 0,9),\n   gains concentrés sur novembre, négative sur 2 ans en 1 h.\n"
           "• Verdict : aucun avantage démontré. Piste à suivre :\n   orb_v4_trend en test en direct prolongé, pas d'argent réel.")
    fig.text(0.06, 0.05, txt, color=FG, fontsize=11, linespacing=1.6)
    p = os.path.join(OUT, "backtest_1an.png"); os.makedirs(OUT, exist_ok=True); fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


if __name__ == "__main__":
    a = sys.argv[1:]
    print(research_card() if a == ["research"] else wf_card() if a == ["wf"] else daily_card())
