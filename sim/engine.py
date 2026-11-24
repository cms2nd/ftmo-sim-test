"""Moteur commun: simulateur d'ordres + moteur de règles FTMO + coupe-circuits.

Le même moteur sert au backtest et au test en direct. Tout l'état est un dict
JSON-sérialisable (persisté dans state/state.json entre deux exécutions).

Conventions de prix: les bougies Yahoo sont des prix "milieu/dernier".
  achat  = prix + spread/2 + glissement
  vente  = prix - spread/2 - glissement
Stops et objectifs sont testés sur le plus haut / plus bas de chaque bougie.
Si stop ET objectif sont touchés dans la même bougie, on suppose le stop (pessimiste).
L'equity flottante utilisée pour les règles FTMO est calculée au pire prix de la
bougie (plus bas pour un achat, plus haut pour une vente), comme un suivi tick à tick.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import config as C
from .news import blackout


def prague_day(ts_utc: datetime) -> str:
    return ts_utc.astimezone(C.PRAGUE).date().isoformat()


def new_state(start_ts: datetime | None = None, attempt: int = 1) -> dict:
    return {
        "attempt": attempt,
        "status": "EN COURS",          # EN COURS / RÉUSSI / ÉCHOUÉ
        "status_reason": "",
        "status_time": "",
        "balance": C.INITIAL_BALANCE,
        "equity": C.INITIAL_BALANCE,
        "worst_equity_today": C.INITIAL_BALANCE,
        "day": prague_day(start_ts) if start_ts else None,
        "day_start_balance": C.INITIAL_BALANCE,
        "max_eod_balance": C.INITIAL_BALANCE,
        "floor": C.INITIAL_BALANCE - C.MAX_TRAILING_LOSS,
        "daily_closed_pnl": {},        # jour Prague -> P&L clôturé
        "halted_today": "",            # raison de l'arrêt pour la journée
        "positions": [],
        "trades": [],
        "breakers": [],                # déclenchements de coupe-circuits
        "last_prices": {},             # sym -> dernier close
        "last_bar": {},                # sym -> iso ts du dernier bar traité
        "strategy_mem": {},
        "equity_curve": [],            # [iso, equity, balance]
        "start_time": start_ts.isoformat() if start_ts else "",
    }


class Engine:
    def __init__(self, state: dict, strategy, live: bool = False, now: datetime | None = None,
                 log_breakers: bool = True):
        self.s = state
        self.strat = strategy
        self.live = live
        self.now = now
        self.log_breakers = log_breakers

    # ------------------------------------------------------------------ utils
    def _breaker(self, ts, kind, reason, sym=""):
        if not self.log_breakers:
            return
        key = (prague_day(ts), kind, sym)
        for b in self.s["breakers"][-50:]:
            if (b["day"], b["kind"], b.get("sym", "")) == key:
                return  # un seul enregistrement par jour/type/instrument
        self.s["breakers"].append({"time": ts.isoformat(), "day": key[0], "kind": kind,
                                   "sym": sym, "reason": reason})

    @staticmethod
    def _inst(sym):
        return C.INSTRUMENTS[sym]

    def _cost_exit(self, sym, price, units, stop=False):
        i = self._inst(sym)
        slip = i["slippage"] * (2 if stop else 1)
        return (i["spread"] / 2 + slip) * units * i["usd_per_point"] + abs(price) * units * i["usd_per_point"] * i["commission_rate"]

    def _pos_pnl(self, p, price):
        i = self._inst(p["sym"])
        d = 1 if p["side"] == "long" else -1
        return d * (price - p["entry"]) * p["units"] * i["usd_per_point"]

    def _floating(self, use_worst=False, bars=None):
        tot = 0.0
        for p in self.s["positions"]:
            px = self.s["last_prices"].get(p["sym"], p["entry"])
            if use_worst and bars and p["sym"] in bars:
                b = bars[p["sym"]]
                px = b["low"] if p["side"] == "long" else b["high"]
            i = self._inst(p["sym"])
            # valeur liquidative: prix bid/ask (demi-spread) inclus
            adj = -i["spread"] / 2 if p["side"] == "long" else i["spread"] / 2
            tot += self._pos_pnl(p, px + adj)
        return tot

    def open_risk(self):
        r = 0.0
        for p in self.s["positions"]:
            r += max(0.0, -self._pos_pnl(p, p["stop"])) + self._cost_exit(p["sym"], p["stop"], p["units"], True)
        return r

    def day_loss(self, equity):
        return max(0.0, self.s["day_start_balance"] - equity)

    def tradable(self):
        return self.s["status"] == "EN COURS"

    # ----------------------------------------------------------- day rollover
    def rollover(self, ts):
        day = prague_day(ts)
        if self.s["day"] is None:
            self.s["day"] = day
        if day == self.s["day"]:
            return
        # Fin de journée: solde de fin de journée -> plancher trailing (ne fait que monter)
        eod = self.s["balance"]
        if eod > self.s["max_eod_balance"]:
            self.s["max_eod_balance"] = eod
        self.s["floor"] = max(self.s["floor"], self.s["max_eod_balance"] - C.MAX_TRAILING_LOSS)
        self.s["day"] = day
        self.s["day_start_balance"] = self.s["balance"]
        self.s["worst_equity_today"] = self.s["balance"] + self._floating()
        self.s["halted_today"] = ""

    # ---------------------------------------------------------------- closing
    def close(self, p, price, ts, reason, stop=False):
        i = self._inst(p["sym"])
        slip = i["slippage"] * (2 if stop else 1)
        if p["side"] == "long":
            fill = price - i["spread"] / 2 - slip
        else:
            fill = price + i["spread"] / 2 + slip
        gross = self._pos_pnl(p, fill)
        comm = abs(fill) * p["units"] * i["usd_per_point"] * i["commission_rate"]
        pnl = gross - comm - p["entry_commission"]
        self.s["balance"] += gross - comm
        day = prague_day(ts)
        self.s["daily_closed_pnl"][day] = self.s["daily_closed_pnl"].get(day, 0.0) + pnl
        self.s["positions"].remove(p)
        self.s["trades"].append({
            "attempt": self.s["attempt"], "sym": p["sym"], "side": p["side"], "units": round(p["units"], 4),
            "entry_time": p["entry_time"], "entry": round(p["entry"], 5), "stop": round(p["stop"], 5),
            "target": round(p["target"], 5), "exit_time": ts.isoformat(), "exit": round(fill, 5),
            "reason": reason, "pnl": round(pnl, 2), "balance": round(self.s["balance"], 2),
        })
        if self.s["daily_closed_pnl"][day] >= C.DAILY_STOP_PROFIT and not self.s["halted_today"]:
            self.s["halted_today"] = "profit du jour ≥ %.0f $" % C.DAILY_STOP_PROFIT
            self._breaker(ts, "STOP_PROFIT_JOUR", "Profit clôturé du jour %.2f $ ≥ %.0f $ (protection règle du meilleur jour)"
                          % (self.s["daily_closed_pnl"][day], C.DAILY_STOP_PROFIT))
        return pnl

    def flatten(self, ts, reason):
        for p in list(self.s["positions"]):
            self.close(p, self.s["last_prices"].get(p["sym"], p["entry"]), ts, reason)

    # ------------------------------------------------------------ FTMO rules
    def best_day_ok(self):
        pos = [v for v in self.s["daily_closed_pnl"].values() if v > 0]
        if not pos:
            return False, 0.0, 0.0
        best, tot = max(pos), sum(pos)
        return best <= C.BEST_DAY_RATIO * tot + 1e-9, best, tot

    def fail(self, ts, reason):
        if self.s["status"] != "EN COURS":
            return
        self.s["status"] = "ÉCHOUÉ"
        self.s["status_reason"] = reason
        self.s["status_time"] = ts.isoformat()
        # en observation: on clôture tout (le compte serait désactivé chez FTMO)
        self.flatten(ts, "challenge échoué")

    def check_rules(self, ts, bars=None):
        worst_eq = self.s["balance"] + self._floating(use_worst=True, bars=bars)
        self.s["equity"] = self.s["balance"] + self._floating()
        self.s["worst_equity_today"] = min(self.s["worst_equity_today"], worst_eq)
        if self.s["status"] != "EN COURS":
            return
        if worst_eq < self.s["day_start_balance"] - C.MAX_DAILY_LOSS:
            self.fail(ts, "Perte journalière max dépassée: equity %.2f < %.2f (début de jour %.2f − 750)"
                      % (worst_eq, self.s["day_start_balance"] - C.MAX_DAILY_LOSS, self.s["day_start_balance"]))
            return
        if worst_eq < self.s["floor"]:
            self.fail(ts, "Perte max trailing dépassée: equity %.2f < plancher %.2f" % (worst_eq, self.s["floor"]))
            return
        # Coupe-circuit: perte du jour (equity comprise) ≥ 600 $
        if self.day_loss(worst_eq) >= C.DAILY_STOP_LOSS and self.s["halted_today"] != "perte":
            self.s["halted_today"] = "perte"
            self._breaker(ts, "STOP_PERTE_JOUR", "Perte du jour %.2f $ ≥ %.0f $: clôture et arrêt pour la journée"
                          % (self.day_loss(worst_eq), C.DAILY_STOP_LOSS))
            self.flatten(ts, "coupe-circuit perte du jour")
            self.s["equity"] = self.s["balance"]

    def check_pass(self, ts):
        if self.s["status"] != "EN COURS" or self.s["positions"]:
            return
        if self.s["balance"] >= C.INITIAL_BALANCE + C.PROFIT_TARGET:
            ok, best, tot = self.best_day_ok()
            if ok:
                self.s["status"] = "RÉUSSI"
                self.s["status_reason"] = "Objectif atteint (solde %.2f) et règle du meilleur jour respectée (%.2f ≤ 50 %% de %.2f)" % (self.s["balance"], best, tot)
                self.s["status_time"] = ts.isoformat()
            else:
                self._breaker(ts, "BEST_DAY_NON_RESPECTEE", "Objectif atteint mais meilleur jour %.2f > 50 %% de %.2f: on continue" % (best, tot))

    # ---------------------------------------------------------- pre-trade
    def pre_trade(self, ts, sym, side, entry, stop, risk_usd):
        s = self.s
        if not self.tradable():
            return "challenge terminé"
        if s["halted_today"]:
            return "arrêt du jour (%s)" % s["halted_today"]
        if len(s["positions"]) >= C.MAX_OPEN_POSITIONS:
            return "2 positions déjà ouvertes"
        if any(p["sym"] == sym for p in s["positions"]):
            return "position déjà ouverte sur %s" % sym
        g = self._inst(sym)["group"]
        for p in s["positions"]:
            pg = self._inst(p["sym"])["group"]
            if p["side"] == side and any(g in grp and pg in grp for grp in C.CORRELATED):
                return "corrélation: %s déjà %s" % (p["sym"], side)
        ev = blackout(ts, C.NEWS_BLACKOUT_MIN)
        if ev:
            return "annonce macro %s" % ev
        eq = s["balance"] + self._floating()
        if self.day_loss(eq) + self.open_risk() + risk_usd > C.DAILY_STOP_LOSS:
            return "risque ouvert + perte du jour + nouveau risque > %.0f $" % C.DAILY_STOP_LOSS
        if eq - s["floor"] < C.FLOOR_BUFFER_MULT * risk_usd:
            return "distance au plancher < 3 × risque"
        return None

    def open(self, ts, sym, side, ref_price, stop, target, tag=""):
        i = self._inst(sym)
        slip = i["slippage"]
        entry = ref_price + (i["spread"] / 2 + slip) * (1 if side == "long" else -1)
        dist = abs(entry - stop)
        if (side == "long" and stop >= entry) or (side == "short" and stop <= entry) or dist <= 0:
            return None
        # Risque fixe (jamais augmenté après une perte): 250 $ frais de sortie inclus
        exit_cost_per_unit = (i["spread"] / 2 + 2 * slip) * i["usd_per_point"] + abs(stop) * i["usd_per_point"] * i["commission_rate"]
        entry_comm_per_unit = abs(entry) * i["usd_per_point"] * i["commission_rate"]
        units = C.RISK_PER_TRADE / (dist * i["usd_per_point"] + exit_cost_per_unit + entry_comm_per_unit)
        eq = self.s["balance"] + self._floating()
        max_units = C.MAX_LEVERAGE * eq / (abs(entry) * i["usd_per_point"])
        notional_existing = sum(abs(p["entry"]) * p["units"] * self._inst(p["sym"])["usd_per_point"] for p in self.s["positions"])
        max_units = min(max_units, max(0.0, (C.MAX_LEVERAGE * eq - notional_existing)) / (abs(entry) * i["usd_per_point"]))
        units = min(units, max_units)
        if units <= 0:
            return None
        risk = units * (dist * i["usd_per_point"] + exit_cost_per_unit + entry_comm_per_unit)
        why = self.pre_trade(ts, sym, side, entry, stop, risk)
        if why:
            self._breaker(ts, "TRADE_REFUSE", why, sym)
            return None
        comm = entry_comm_per_unit * units
        self.s["balance"] -= comm
        p = {"sym": sym, "side": side, "units": units, "entry": entry, "stop": stop, "target": target,
             "entry_time": ts.isoformat(), "entry_commission": comm, "tag": tag}
        self.s["positions"].append(p)
        return p

    # ------------------------------------------------------------- bar step
    def manage_bar(self, sym, close_ts, bar):
        """Gère stops/objectifs d'une position sur une bougie (plus haut/plus bas)."""
        i = self._inst(sym)
        hs = i["spread"] / 2
        for p in [p for p in self.s["positions"] if p["sym"] == sym]:
            if p["side"] == "long":
                bid_lo, bid_hi, bid_open = bar["low"] - hs, bar["high"] - hs, bar["open"] - hs
                if bid_lo <= p["stop"]:
                    px = min(p["stop"], bid_open) + hs  # gap: rempli à l'ouverture
                    self.close(p, px, close_ts, "stop-loss", stop=True)
                elif bid_hi >= p["target"]:
                    self.close(p, p["target"] + hs, close_ts, "objectif")
            else:
                ask_hi, ask_lo, ask_open = bar["high"] + hs, bar["low"] + hs, bar["open"] + hs
                if ask_hi >= p["stop"]:
                    px = max(p["stop"], ask_open) - hs
                    self.close(p, px, close_ts, "stop-loss", stop=True)
                elif ask_lo <= p["target"]:
                    self.close(p, p["target"] - hs, close_ts, "objectif")

    def flatten_due(self, close_ts):
        lp = close_ts.astimezone(C.PRAGUE)
        hm = C.FRIDAY_FLATTEN_PRAGUE if lp.weekday() == 4 else C.FLATTEN_PRAGUE
        return (lp.hour, lp.minute) >= hm

    def step(self, close_ts: datetime, bars: dict, allow_entries: bool = True):
        """Traite toutes les bougies qui se clôturent à close_ts. bars: sym -> row(dict)."""
        self.rollover(close_ts)
        for sym, b in bars.items():
            self.manage_bar(sym, close_ts, b)
            self.s["last_prices"][sym] = b["close"]
        self.check_rules(close_ts, bars)
        # Sorties décidées par la stratégie (fin de session, etc.)
        for p in list(self.s["positions"]):
            if p["sym"] in bars and self.strat.exit_now(p["sym"], close_ts, p):
                self.close(p, bars[p["sym"]]["close"], close_ts, "fin de session")
        if self.flatten_due(close_ts) and self.s["positions"]:
            self.flatten(close_ts, "clôture fin de journée")
        self.check_pass(close_ts)
        if not allow_entries or not self.tradable() or self.flatten_due(close_ts):
            return
        for sym, b in bars.items():
            sig = self.strat.signal(sym, close_ts, b, self.s["strategy_mem"])
            if sig:
                self.open(close_ts, sym, sig["side"], b["close"], sig["stop"], sig["target"], sig.get("tag", ""))
        self.s["equity"] = self.s["balance"] + self._floating()
