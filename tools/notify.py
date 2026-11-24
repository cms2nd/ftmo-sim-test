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


def send_file(method, field, path, caption=""):
    import uuid
    b = uuid.uuid4().hex
    parts = []
    for k, v in (("chat_id", chat_id()), ("caption", caption[:1000])):
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{field}"; filename="{os.path.basename(path)}"\r\n'
                 f'Content-Type: application/octet-stream\r\n\r\n'.encode() + open(path, "rb").read() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=b"".join(parts),
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def report_html(out="RAPPORT.html"):
    """RAPPORT.md -> page HTML autonome (images intégrées), lisible sur téléphone."""
    import base64, re
    import markdown
    html = markdown.markdown(open("RAPPORT.md", encoding="utf-8").read(), extensions=["tables", "md_in_html"])
    def emb(m):
        p = m.group(1)
        return f'src="data:image/png;base64,{base64.b64encode(open(p, "rb").read()).decode()}"' if os.path.exists(p) else m.group(0)
    html = re.sub(r'src="([^"]+\.png)"', emb, html)
    css = ("body{font-family:system-ui,sans-serif;max-width:860px;margin:auto;padding:16px;line-height:1.5}"
           "table{border-collapse:collapse;display:block;overflow-x:auto;font-size:13px}td,th{border:1px solid #ccc;padding:4px 6px}"
           "img{max-width:100%}")
    open(out, "w", encoding="utf-8").write(f'<!doctype html><meta charset="utf-8"><meta name="viewport" '
                                           f'content="width=device-width,initial-scale=1"><title>Rapport FTMO</title><style>{css}</style>{html}')
    return out


def main():
    if not TOKEN:
        sys.exit("TELEGRAM_KEY manquant")
    a = sys.argv[1:]
    if a and a[0] in ("--photo", "--doc", "--report"):
        cap = " ".join(a[2:]) if a[0] != "--report" else " ".join(a[1:])
        if a[0] == "--photo":
            send_file("sendPhoto", "photo", a[1], cap)
        elif a[0] == "--doc":
            send_file("sendDocument", "document", a[1], cap)
        else:
            send_file("sendDocument", "document", report_html(), cap or "Rapport complet (ouvre-le dans ton navigateur)")
        print("fichier envoyé")
        return

    if not TOKEN:
        sys.exit("TELEGRAM_KEY manquant")
    text = sys.stdin.read() if sys.argv[1:] == ["-"] else " ".join(sys.argv[1:])
    for i in range(0, len(text), 4000):
        api("sendMessage", chat_id=chat_id(), text=text[i:i + 4000], disable_web_page_preview="true")
    print("message envoyé")


if __name__ == "__main__":
    main()
