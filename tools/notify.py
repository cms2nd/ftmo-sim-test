"""Envoie un message Telegram. Token lu dans la variable d'environnement TELEGRAM_KEY (secret GitHub).

L'identifiant de conversation est retrouvé via getUpdates (le dernier message envoyé au robot),
puis gardé dans .tg_chat (cache Actions, jamais commité). Usage : python tools/notify.py "texte" | -
"""
import json, os, sys, urllib.parse, urllib.request

TOKEN = os.environ.get("TELEGRAM_KEY", "").strip()
CACHE = ".tg_chat"


def api(method, **params):
    data = urllib.parse.urlencode(params).encode() if params else None
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data, timeout=30) as r:
        return json.load(r)


def chat_id():
    if os.path.exists(CACHE):
        return open(CACHE).read().strip()
    ups = api("getUpdates").get("result", [])
    ids = [u[k]["chat"]["id"] for u in ups for k in ("message", "my_chat_member") if k in u]
    if not ids:
        sys.exit("Aucun message reçu par le robot : envoie-lui un message dans Telegram puis relance.")
    open(CACHE, "w").write(str(ids[-1]))
    return str(ids[-1])


def main():
    if not TOKEN:
        sys.exit("TELEGRAM_KEY manquant")
    text = sys.stdin.read() if sys.argv[1:] == ["-"] else " ".join(sys.argv[1:])
    for i in range(0, len(text), 4000):
        api("sendMessage", chat_id=chat_id(), text=text[i:i + 4000], disable_web_page_preview="true")
    print("message envoyé")


if __name__ == "__main__":
    main()
