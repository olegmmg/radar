import os, re, json, base64, threading, time, requests, asyncio
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    return response

# ---------- НАСТРОЙКИ ----------
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "radarrussiia")

print("✅ Конфигурация загружена")

STATUS_PRIORITY = {
    "missile_alert": 0,
    "missile_danger": 1,
    "drone_attack": 2,
    "drone_danger": 3,
    "clear": 4
}

REGION_ALIASES = {
    "Московская область": "Московская область",
    "Московский регион": "Московская область",
    "Подмосковье": "Московская область",
    "Москва": "Московская область",
    "Тульская область": "Тульская область",
    "Тула": "Тульская область",
    "Калужская область": "Калужская область",
    "Калуга": "Калужская область",
    "Рязанская область": "Рязанская область",
    "Рязань": "Рязанская область",
    "Тверская область": "Тверская область",
    "Тверь": "Тверская область",
    "Воронежская область": "Воронежская область",
    "Воронеж": "Воронежская область",
    "Белгородская область": "Белгородская область",
    "Белгород": "Белгородская область",
    "Брянская область": "Брянская область",
    "Брянск": "Брянская область",
    "Курская область": "Курская область",
    "Курск": "Курская область",
    "Ростовская область": "Ростовская область",
    "Смоленская область": "Смоленская область",
    "Смоленск": "Смоленская область",
    "Орловская область": "Орловская область",
    "Орёл": "Орловская область",
    "Орел": "Орловская область",
    "Липецкая область": "Липецкая область",
    "Липецк": "Липецкая область",
    "Тамбовская область": "Тамбовская область",
    "Тамбов": "Тамбовская область",
    "Владимирская область": "Владимирская область",
    "Владимир": "Владимирская область",
    "Ивановская область": "Ивановская область",
    "Иваново": "Ивановская область",
    "Ярославская область": "Ярославская область",
    "Ярославль": "Ярославская область",
    "Костромская область": "Костромская область",
    "Кострома": "Костромская область",
    "Нижегородская область": "Нижегородская область",
    "Нижний Новгород": "Нижегородская область",
    "Кировская область": "Кировская область",
    "Киров": "Кировская область",
    "Пензенская область": "Пензенская область",
    "Пенза": "Пензенская область",
    "Ульяновская область": "Ульяновская область",
    "Ульяновск": "Ульяновская область",
    "Саратовская область": "Саратовская область",
    "Саратов": "Саратовская область",
    "Волгоградская область": "Волгоградская область",
    "Волгоград": "Волгоградская область",
    "Астраханская область": "Астраханская область",
    "Астрахань": "Астраханская область",
    "Вологодская область": "Вологодская область",
    "Вологда": "Вологодская область",
    "Новгородская область": "Новгородская область",
    "Псковская область": "Псковская область",
    "Псков": "Псковская область",
    "Ленинградская область": "Ленинградская область",
    "Челябинская область": "Челябинская область",
    "Челябинск": "Челябинская область",
    "Свердловская область": "Свердловская область",
    "Екатеринбург": "Свердловская область",
    "Ставропольский край": "Ставропольский край",
    "Ставрополь": "Ставропольский край",
    "Невинномысск": "Ставропольский край",
    "Краснодарский край": "Краснодарский край",
    "Краснодар": "Краснодарский край",
    "Сочи": "Краснодарский край",
    "Анапа": "Краснодарский край",
    "Новороссийск": "Краснодарский край",
    "Приморско-Ахтарск": "Краснодарский край",
    "Пермский край": "Пермский край",
    "Пермь": "Пермский край",
    "Республика Крым": "Республика Крым",
    "Симферополь": "Республика Крым",
    "Республика Адыгея": "Республика Адыгея",
    "Майкоп": "Республика Адыгея",
    "Чеченская Республика": "Чеченская Республика",
    "Грозный": "Чеченская Республика",
    "Республика Дагестан": "Республика Дагестан",
    "Дагестан": "Республика Дагестан",
    "Махачкала": "Республика Дагестан",
    "Каспийск": "Республика Дагестан",
    "Республика Ингушетия": "Республика Ингушетия",
    "Республика Северная Осетия": "Республика Северная Осетия",
    "Республика Северная Осетия - Алания": "Республика Северная Осетия",
    "Владикавказ": "Республика Северная Осетия",
    "Кабардино-Балкарская Республика": "Кабардино-Балкарская Республика",
    "Карачаево-Черкесская Республика": "Карачаево-Черкесская Республика",
    "Республика Удмуртия": "Республика Удмуртия",
    "Удмуртская Республика": "Республика Удмуртия",
    "Республика Мордовия": "Республика Мордовия",
}

region_statuses = {}
alert_history = []
last_msg_id = 0

def is_ad_message(text):
    t = text.lower()
    ad_patterns = [
        "платим от", "отзыв на ozon", "взять подработку",
        "заработок", "вакансия", "работа в интернете"
    ]
    for pattern in ad_patterns:
        if pattern in t:
            return True
    return False

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
    
    # 1. ОТБОЙ (проверяется первым)
    if any(w in t for w in [
        "отбой опасности по бпла", "отбой по бпла",
        "отбой ракетной опасности", "отбой ракетной тревоги",
        "отбой фиксации"
    ]):
        if "опасность сохраняется" in t:
            return "drone_danger"
        return "clear"
    
    # 2. ЛОЖНАЯ ЦЕЛЬ (игнорируем)
    if "ложная цель" in t:
        return None
    
    # 3. РАКЕТНАЯ ОПАСНОСТЬ
    if "ракетная тревога" in t:
        return "missile_alert"
    if "ракетная опасность" in t or "ракетной опасности" in t:
        return "missile_danger"
    
    # 4. АТАКА БПЛА (активные действия)
    if any(w in t for w in [
        "работа пво", "сбитие", "сбития",
        "фиксация бпла", "фиксации бпла",
        "фиксация групп", "фиксация группы", "фиксации групп",
        "фиксация от", "фиксация реактивного бпла",
        "приготовиться к сбитию", "приготовится к сбитиям",
        "продолжается работа пво",
        "еще фиксации", "идут сбития",
        "много бпла", "очередная волна бпла",
        "тревога по бпла", "атакуют", "атака бпла", "бпла атакуют",
    ]):
        return "drone_attack"
    
    # 5. ОПАСНОСТЬ БПЛА (предупреждения)
    if any(w in t for w in [
        "опасность по бпла", "угроза атаки",
        "приготовиться к очередной волне",
        "срочно принять меры безопасности",
        "внимание по возможным бпла", "внимание по бпла",
        "меры безопасности"
    ]):
        return "drone_danger"
    
    # 6. СОХРАНЯЕТСЯ / ПОВТОРНО
    if "опасность по бпла сохраняется" in t:
        return "drone_danger"
    if "опасность по бпла" in t and "повторно" in t:
        return "drone_danger"
    
    # 7. Формат "г. Город - опасность по БПЛА"
    if re.search(r"г\.\s*\S+.*опасность по бпла", t):
        return "drone_danger"
    
    return None

def process_message(text, msg_id=None):
    """Обрабатывает одно сообщение и обновляет статусы регионов"""
    if not text:
        return
    
    if is_ad_message(text):
        if msg_id:
            print(f"  ↳ Реклама")
        return
    
    if is_superseded_by_later(text):
        if msg_id:
            print(f"  ↳ Сводка")
        return
    
    regions = extract_regions(text)
    if not regions:
        if msg_id:
            print(f"  ↳ Регионы не найдены")
        return
    
    status = detect_status(text)
    if not status:
        if msg_id:
            print(f"  ↳ Статус не определён (регионы: {regions})")
        return
    
    now = datetime.now(timezone.utc).isoformat()
    for r in regions:
        cur = region_statuses.get(r, {}).get("status")
        if cur and STATUS_PRIORITY.get(status, 99) >= STATUS_PRIORITY.get(cur, 99):
            if msg_id:
                print(f"  ↳ {r}: {status} не приоритетнее {cur}")
            continue
        region_statuses[r] = {"status": status, "last_update": now, "message": text[:200]}
        alert_history.append({"region": r, "status": status, "timestamp": now})
        if msg_id:
            print(f"  ✅ {r} → {status}")

# ---------- КЛИЕНТ ----------
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def poll_messages():
    global last_msg_id
    
    try:
        channel = await client.get_entity(CHANNEL_USERNAME)
        print(f"✅ Канал: {channel.title} (ID: {channel.id})")
    except Exception as e:
        print(f"❌ Ошибка канала: {e}")
    
    while True:
        await asyncio.sleep(30)
        try:
            messages = await client.get_messages(CHANNEL_USERNAME, limit=15)
            if not messages:
                continue
            for msg in reversed(messages):
                if msg.id <= last_msg_id:
                    continue
                last_msg_id = msg.id
                text = msg.message
                preview = text[:80].replace('\n', ' ') if text else ''
                print(f"📩 ID:{msg.id} | {preview}...")
                process_message(text, msg.id)
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")

# ---------- FLASK ----------
@app.route("/api/statuses")
def get_statuses():
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    result = {"regions": {}, "last_updated": now.isoformat()}
    for r, d in region_statuses.items():
        count = 0
        for a in alert_history:
            if a["region"] == r:
                at = datetime.fromisoformat(a["timestamp"])
                if at > hour_ago:
                    count += 1
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
    export = {"regions": region_statuses, "last_updated": datetime.now(timezone.utc).isoformat()}
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
        time.sleep(240)
        try:
            requests.get(f"http://localhost:{port}/api/statuses", timeout=10)
            print("💓 Self-ping OK")
        except Exception as e:
            print(f"💔 Self-ping failed: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

async def main():
    await client.start()
    print("✅ Клиент запущен")
    
    global last_msg_id
    
    # Загружаем последние 100 сообщений для восстановления состояния
    print("📥 Загружаем последние 100 сообщений...")
    try:
        history = await client.get_messages(CHANNEL_USERNAME, limit=100)
        if history:
            last_msg_id = history[0].id
            print(f"📌 Последнее сообщение ID: {last_msg_id}")
            
            # Обрабатываем от старых к новым
            for msg in reversed(history):
                text = msg.message
                if text:
                    preview = text[:80].replace('\n', ' ')
                    print(f"📥 ID:{msg.id} | {preview}...")
                    process_message(text, msg.id)
            
            print(f"✅ Загружено и обработано {len(history)} сообщений")
            print(f"📊 Текущие статусы регионов: {len(region_statuses)}")
    except Exception as e:
        print(f"❌ Ошибка загрузки истории: {e}")
    
    asyncio.create_task(poll_messages())
    print("🔄 Polling запущен (каждые 30 секунд)")
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
