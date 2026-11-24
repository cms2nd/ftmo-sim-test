"""Interface commune des stratégies.

Pour tester une nouvelle stratégie: créer strategies/<nom>.py exposant une
classe `Strategy(BaseStrategy)`, puis changer ACTIVE_STRATEGY dans sim/config.py
(ou passer --strategy <nom> à run.py / backtest.py).
"""
import importlib


class BaseStrategy:
    name = "base"
    instruments: list = []

    def prepare(self, data: dict):
        """data: sym -> DataFrame 5m (index UTC = début de bougie). Pré-calcule les indicateurs."""

    def signal(self, sym, close_ts, bar: dict, mem: dict):
        """Renvoie None ou {"side": "long"/"short", "stop": float, "target": float}."""
        return None

    def exit_now(self, sym, close_ts, position) -> bool:
        return False


def load(name):
    return importlib.import_module(f"strategies.{name}").Strategy()
