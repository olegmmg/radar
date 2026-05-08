import os, re, json, base64, threading, time, requests
from datetime import datetime, timedelta
from flask import Flask, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession

app = Flask(__name__)

# ---------- НАСТРОЙКИ ----------
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
CHANNEL_USERNAME = "radarrussiia"

print("✅ Конфигурация загружена")

STATUS_PRIORITY = {"missile_alert": 0, "missile_danger": 1, "drone_attack": 2, "drone_danger": 3, "clear": 4}

REGION_ALIASES = {
    "Московская область": "Московская область", "Московский регион": "Московская область",
    "Москва": "Москва", "Подмосковье": "Московская область",
    "Тульская область": "Тульская область", "Тула": "Тульская область",
    "Калужская область": "Калужская область", "Калуга": "Калужская область",
    "Рязанская область": "Рязанская область", "Рязань": "Рязанская область",
    "Тверская область": "Тверская область", "Тверь": "Тверская область",
    "Воронежская область": "Воронежская область", "Воронеж": "Воронежская область",
    "Белгородская область": "Белгородская область", "Белгород": "Белгородская область",
    "Брянская область": "Брянская область", "Брянск": "Брянская область",
    "Курская область": "Курская область", "Курск": "Курская область",
    "Ростовская область": "Ростовская область", "Ростов": "Ростовская область",
    "Смоленская область": "Смоленская область", "Смоленск": "Смоленская область",
    "Орловская область": "Орловская область", "Орёл": "Орловская область", "Орел": "Орловская область",
    "Липецкая область": "Липецкая область", "Липецк": "Липецкая область",
    "Тамбовская область": "Тамбовская область", "Тамбов": "Тамбовская область",
    "Владимирская область": "Владимирская область", "Владимир": "Владимирская область",
    "Ивановская область": "Ивановская область", "Иваново": "Ивановская область",
    "Нижегородская область": "Нижегородская область", "Нижний Новгород": "Нижегородская область",
    "Пензенская область": "Пензенская область", "Пенза": "Пензенская область",
    "Ульяновская область": "Ульяновская область", "Ульяновск": "Ульяновская область",
    "Саратовская область": "Саратовская область", "Саратов": "Саратовская область",
    "Вологодская область": "Вологодская область", "Вологда": "Вологодская область",
    "Ставропольский край": "Ставропольский край", "Ставрополь": "Ставропольский край",
    "Краснодарский край": "Краснодарский край", "Краснодар": "Краснодарский край",
    "Пермский край": "Пермский край", "Пермь": "Пермский край",
    "Республика Крым": "Республика Крым", "Симферополь": "Республика Крым",
    "Республика Адыгея": "Республика Адыгея", "Майкоп": "Республика Адыгея",
    "Чеченская Республика": "Чеченская Республика", "Грозный": "Чеченская Республика",
    "Республика Дагестан": "Республика Дагестан", "Махачкала": "Республика Дагестан",
    "Каспийск": "Республика Дагестан", "дагестанский": "Республика Дагестан",
    "Республика Ингушетия": "Республика Ингушетия",
    "Республика Северная Осетия": "Республика Северная Осетия",
    "Кабардино-Балкарская Республика": "Кабардино-Балкарская Республика",
    "Карачаево-Черкесская Республика": "Карачаево-Черкесская Республика",
}

region_statuses = {}
alert_history = []

# ID последнего обработанного сообщения
last_msg_id = 0

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
    if any(w in t for w in [
        "работа пво", "сбитие", "сбития", "фиксация бпла", "фиксации бпла",
        "фиксация от", "фиксация групп", "фиксация группы", "в небе",
        "приготовиться к сбитию", "продолжается работа пво", "еще фиксации",
        "идут сбития", "много бпла", "очередная волна бпла",
        "тревога по бпла", "атакуют", "атака бпла", "бпла атакуют",
        "на москву", "летят бпла"
    ]): return "drone_attack"
    if any(w in t for w in [
        "опасность по бпла", "угроза атаки", "приготовиться к очередной волне",
        "срочно принять меры безопасности", "внимание", "меры безопасности"
    ]): return "drone_danger"
    if "сохраняется" in t: return "drone_danger"
    if "отбой опасности" in t or "отбой по бпла" in t:
        return "drone_danger" if "опасность сохраняется" in t else "clear"
    return None

# ---------- КЛИЕНТ ----------
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def poll_messages():
    """Каждые 30 секунд проверяет новые сообщения"""
    global last_msg_id
    
    while True:
        time.sleep(30)
        try:
            # Получаем последние 5 сообщений
            messages = client.loop.run_until_complete(
                client.get_messages(CHANNEL_USERNAME, limit=15)
            )
            
            if not messages:
                continue
            
            for msg in reversed(messages):
                if msg.id <= last_msg_id:
                    continue
                
                last_msg_id = max(last_msg_id, msg.id)
                text = msg.message
                if not text:
                    continue
                
                preview = text[:80].replace('\n', ' ')
                print(f"📩 ID:{msg.id} | {preview}...")
                
                if is_ad_message(text):
                    print(f"  ↳ Реклама")
                    continue
                if is_superseded_by_later(text):
                    print(f"  ↳ Сводка")
                    continue
                
                regions = extract_regions(text)
                if not regions:
                    print(f"  ↳ Регионы не найдены")
                    continue
                
                status = detect_status(text)
                if not status:
                    print(f"  ↳ Статус не определён (регионы: {regions})")
                    continue
                
                now = datetime.utcnow().isoformat() + "Z"
                for r in regions:
                    cur = region_statuses.get(r, {}).get("status")
                    if cur and STATUS_PRIORITY.get(status, 99) >= STATUS_PRIORITY.get(cur, 99):
                        print(f"  ↳ {r}: {status} не приоритетнее {cur}")
                        continue
                    region_statuses[r] = {"status": status, "last_update": now, "message": text[:200]}
                    alert_history.append({"region": r, "status": status, "timestamp": now})
                    print(f"  ✅ {r} → {status}")
                    
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")

# ---------- FLASK ----------
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
    # Запускаем клиент
    async def start():
        await client.start()
        print("✅ Клиент запущен")
        # Получаем ID последнего сообщения, чтобы не обрабатывать старые
        global last_msg_id
        messages = await client.get_messages(CHANNEL_USERNAME, limit=1)
        if messages:
            last_msg_id = messages[0].id
            print(f"📌 Последнее сообщение ID: {last_msg_id}")
    
    client.loop.run_until_complete(start())
    
    # Запускаем polling в отдельном потоке
    threading.Thread(target=poll_messages, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()
    
    print("🔄 Polling запущен (каждые 30 секунд)")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
