import os, re, json, base64, threading, time, requests, shutil
from datetime import datetime, timedelta
from flask import Flask, jsonify
from telethon import TelegramClient, events

app = Flask(__name__)

# ---------- КОПИРУЕМ СЕССИЮ ИЗ SECRET FILE ----------
SECRET_SESSION = "/etc/secrets/session.session"
LOCAL_SESSION = "session.session"

if os.path.exists(SECRET_SESSION):
    shutil.copy(SECRET_SESSION, LOCAL_SESSION)
    print("✅ Сессия скопирована из Secret File")
else:
    print("❌ Secret File не найден! Проверьте имя файла в настройках Render.")

# ---------- НАСТРОЙКИ ----------
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"])
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
CHANNEL_USERNAME = "radarrussiia"

STATUS_PRIORITY = {"missile_alert": 0, "missile_danger": 1, "drone_attack": 2, "drone_danger": 3, "clear": 4}

REGION_ALIASES = {
    "Московская область": "Московская область", "Московский регион": "Московская область", "Москва": "Москва",
    "Тульская область": "Тульская область", "Калужская область": "Калужская область",
    "Рязанская область": "Рязанская область", "Тверская область": "Тверская область",
    "Воронежская область": "Воронежская область", "Белгородская область": "Белгородская область",
    "Брянская область": "Брянская область", "Курская область": "Курская область",
    "Ростовская область": "Ростовская область", "Смоленская область": "Смоленская область",
    "Орловская область": "Орловская область", "Липецкая область": "Липецкая область",
    "Тамбовская область": "Тамбовская область", "Владимирская область": "Владимирская область",
    "Ивановская область": "Ивановская область", "Нижегородская область": "Нижегородская область",
    "Пензенская область": "Пензенская область", "Ульяновская область": "Ульяновская область",
    "Саратовская область": "Саратовская область", "Вологодская область": "Вологодская область",
    "Ставропольский край": "Ставропольский край", "Краснодарский край": "Краснодарский край",
    "Пермский край": "Пермский край", "Республика Крым": "Республика Крым",
    "Республика Адыгея": "Республика Адыгея", "Чеченская Республика": "Чеченская Республика",
    "Республика Дагестан": "Республика Дагестан", "Республика Ингушетия": "Республика Ингушетия",
    "Республика Северная Осетия": "Республика Северная Осетия",
    "Кабардино-Балкарская Республика": "Кабардино-Балкарская Республика",
    "Карачаево-Черкесская Республика": "Карачаево-Черкесская Республика",
}

region_statuses = {}
alert_history = []

def is_ad_message(text):
    return "❗️Радар по всей России" not in text

def is_superseded_by_later(text):
    return bool(re.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", text, re.IGNORECASE))

def extract_regions(text):
    found = set()
    for alias, norm in REGION_ALIASES.items():
        if alias in text:
            found.add(norm)
    return list(found)

def detect_status(text):
    t = text.lower()
    if "ракетная тревога" in t: return "missile_alert"
    if "ракетная опасность" in t or "ракетной опасности" in t: return "missile_danger"
    if any(w in t for w in ["работа пво", "сбитие", "фиксация бпла", "фиксации бпла",
                              "фиксация от", "фиксация групп", "в небе", "еще фиксации"]): return "drone_attack"
    if any(w in t for w in ["опасность по бпла", "тревога по бпла", "угроза атаки",
                              "приготовиться к очередной волне", "срочно принять меры"]): return "drone_danger"
    if "отбой опасности" in t or "отбой по бпла" in t:
        return "drone_danger" if "опасность сохраняется" in t else "clear"
    return None

client = TelegramClient(LOCAL_SESSION, API_ID, API_HASH)

@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def handler(event):
    text = event.message.text
    if not text or is_ad_message(text) or is_superseded_by_later(text):
        return
    regions = extract_regions(text)
    if not regions:
        return
    status = detect_status(text)
    if not status:
        return
    now = datetime.utcnow().isoformat() + "Z"
    for r in regions:
        cur = region_statuses.get(r, {}).get("status")
        if cur and STATUS_PRIORITY.get(status, 99) >= STATUS_PRIORITY.get(cur, 99):
            continue
        region_statuses[r] = {"status": status, "last_update": now, "message": text[:200]}
        alert_history.append({"region": r, "status": status, "timestamp": now})

@app.route("/api/statuses")
def get_statuses():
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = {"regions": {}, "last_updated": datetime.utcnow().isoformat() + "Z"}
    for r, d in region_statuses.items():
        count = sum(1 for a in alert_history if a["region"] == r and datetime.fromisoformat(a["timestamp"]) > hour_ago)
        result["regions"][r] = {**d, "alerts_last_hour": count}
    return jsonify(result)

@app.route("/")
def index():
    return "OK"

def push_to_github():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/data/statuses.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    export = {"regions": region_statuses, "last_updated": datetime.utcnow().isoformat() + "Z"}
    content = json.dumps(export, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(content.encode()).decode()
    try:
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha") if resp.status_code == 200 else None
    except:
        sha = None
    body = {"message": "update", "content": b64, "branch": "main"}
    if sha:
        body["sha"] = sha
    try:
        requests.put(url, headers=headers, json=body)
    except:
        pass

def periodic_push():
    while True:
        time.sleep(60)
        if region_statuses:
            push_to_github()

def keep_alive():
    port = int(os.environ.get("PORT", 5000))
    while True:
        time.sleep(300)
        try:
            requests.get(f"http://localhost:{port}/api/statuses", timeout=10)
        except:
            pass

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()
    
    async def start():
        await client.start()
        print("✅ Клиент запущен")
    
    client.loop.run_until_complete(start())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
