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
DPR_CHANNEL = os.environ.get("DPR_CHANNEL", "DPR_channel")

print("✅ Конфигурация загружена")
print(f"📡 Основной канал: {CHANNEL_USERNAME}")
print(f"📡 Канал ДНР/ЛНР: {DPR_CHANNEL}")

# Приоритеты (меньше число = выше приоритет)
# Опасность имеет более высокий приоритет, чем отбой
STATUS_PRIORITY = {
    "missile_alert": 0,      # РАКЕТНАЯ ТРЕВОГА - наивысший
    "missile_danger": 1,     # РАКЕТНАЯ ОПАСНОСТЬ
    "drone_attack": 2,       # АТАКА БПЛА
    "drone_danger": 3,       # ОПАСНОСТЬ БПЛА
    "clear": 4,              # ОТБОЙ - наинизший (но clear имеет особое правило: всегда сбрасывает)
}

# Регионы, разрешённые для канала ДНР/ЛНР
ALLOWED_DPR_REGIONS = [
    "Донецкая Народная Республика",
    "Луганская Народная Республика",
    "Запорожская область",
    "Херсонская область"
]

REGION_ALIASES = {
    "Московская область": "Московская область",
    "Московский регион": "Московская область",
    "Подмосковье": "Московская область",
    "Москва": "Московская область",
    "г. Москва": "Московская область",
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
    "г. Санкт-Петербург": "Ленинградская область",
    "Санкт-Петербург": "Ленинградская область",
    "Ленинградская область": "Ленинградская область",
    "Республика Карелия": "Республика Карелия",
    "Архангельская область": "Архангельская область",
    "Республика Коми": "Республика Коми",
    "Ненецкий АО": "Ненецкий АО",
    "Вологодская область": "Вологодская область",
    "Вологда": "Вологодская область",
    "Новгородская область": "Новгородская область",
    "Псковская область": "Псковская область",
    "Псков": "Псковская область",
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
    "Пермский край": "Пермский край",
    "Пермь": "Пермский край",
    "Республика Удмуртия": "Республика Удмуртия",
    "Республика Башкортостан": "Республика Башкортостан",
    "Оренбургская область": "Оренбургская область",
    "Самарская область": "Самарская область",
    "Чувашская Республика": "Чувашская Республика",
    "Республика Татарстан": "Республика Татарстан",
    "Республика Марий Эл": "Республика Марий Эл",
    "Республика Мордовия": "Республика Мордовия",
    "Ставропольский край": "Ставропольский край",
    "Ставрополь": "Ставропольский край",
    "Невинномысск": "Ставропольский край",
    "Краснодарский край": "Краснодарский край",
    "Краснодар": "Краснодарский край",
    "Причерноморье": "Краснодарский край",
    "Причерноморье Краснодарского края": "Краснодарский край",
    "Сочи": "Краснодарский край",
    "Анапа": "Краснодарский край",
    "Новороссийск": "Краснодарский край",
    "Приморско-Ахтарск": "Краснодарский край",
    "Ростовская область": "Ростовская область",
    "Волгоградская область": "Волгоградская область",
    "Волгоград": "Волгоградская область",
    "Астраханская область": "Астраханская область",
    "Астрахань": "Астраханская область",
    "Республика Крым": "Республика Крым",
    "Крым": "Республика Крым",
    "Побережье Крыма": "Республика Крым",
    "Крымский мост": "Республика Крым",
    "Севастополь": "Республика Крым",
    "Симферополь": "Республика Крым",
    "Республика Адыгея": "Республика Адыгея",
    "Адыгея": "Республика Адыгея",
    "Республика Калмыкия": "Республика Калмыкия",
    "Чеченская Республика": "Чеченская Республика",
    "Грозный": "Чеченская Республика",
    "Республика Дагестан": "Республика Дагестан",
    "Дагестан": "Республика Дагестан",
    "Махачкала": "Республика Дагестан",
    "Каспийск": "Республика Дагестан",
    "Республика Ингушетия": "Республика Ингушетия",
    "Республика Северная Осетия": "Республика Северная Осетия",
    "Владикавказ": "Республика Северная Осетия",
    "Кабардино-Балкарская Республика": "Кабардино-Балкарская Республика",
    "Карачаево-Черкесская Республика": "Карачаево-Черкесская Республика",
    "Челябинская область": "Челябинская область",
    "Челябинск": "Челябинская область",
    "Свердловская область": "Свердловская область",
    "Екатеринбург": "Свердловская область",
    "Курганская область": "Курганская область",
    "ЯНАО": "ЯНАО",
    "Ямало-Ненецкий АО": "ЯНАО",
    "Ханты-Мансийский АО - Югра": "Ханты-Мансийский АО",
    "Тюменская область": "Тюменская область",
    "Омская область": "Омская область",
    "Томская область": "Томская область",
    "Новосибирская область": "Новосибирская область",
    "Алтайский край": "Алтайский край",
    "Кемеровская область": "Кемеровская обл.",
    "Республика Алтай": "Республика Алтай",
    "Республика Хакасия": "Республика Хакасия",
    "Республика Тыва": "Республика Тыва",
    "Красноярский край": "Красноярский край",
    "Республика Бурятия": "Республика Бурятия",
    "Иркутская область": "Иркутская обл.",
    "Забайкальский край": "Забайкальский край",
    "Амурская область": "Амурская обл.",
    "Республика Саха (Якутия)": "Республика Саха (Якутия)",
    "Еврейская АО": "Еврейская АО",
    "Приморский край": "Приморский край",
    "Хабаровский край": "Хабаровский край",
    "Сахалинская область": "Сахалинская обл.",
    "Магаданская область": "Магаданская обл.",
    "Камчатский край": "Камчатский край",
    "Чукотский АО": "Чукотский АО",
    "Донецкая Народная Республика": "Донецкая область",
    "Луганская Народная Республика": "Луганская область",
    "Запорожская область": "Запорожская область",
    "Херсонская область": "Херсонская область",
}

region_statuses = {}
alert_history = []
last_msg_id_main = 0
last_msg_id_dpr = 0

def clean_message_for_frontend(msg):
    if not msg:
        return ''
    
    ad_phrases = [
        r'❗️Радар по всей России\s*-\s*@radarrussiia\s*\n?',
        r'🌐 Обход белых списков\s*-\s*@Internet_Boost_bot\s*\([^)]+\)\s*\n?',
        r'@radarrussiia\s*\n?',
        r'@Internet_Boost_bot\s*\n?',
        r'https?://t\.me/Internet_Boost_bot\S*\s*\n?',
        r'Радар по всей России.*?\n',
        r'Обход белых списков.*?\n',
        r'🔴 Радар ДНР.*?\n?',
        r'📢 Оповещения Радар ДНР:\s*',
    ]
    
    cleaned = msg
    for pattern in ad_phrases:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def is_pure_ad_message(text):
    if not text:
        return False
    
    if "Радар ДНР" in text:
        return False
    
    cleaned = clean_message_for_frontend(text)
    if not cleaned or len(cleaned) < 15:
        return True
    
    return False

def is_superseded_by_later(text):
    return bool(re.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", text, re.IGNORECASE))

def extract_regions(text):
    normalized = ' '.join(text.split())
    found = set()
    
    for alias, norm in REGION_ALIASES.items():
        if alias.lower() in normalized.lower():
            found.add(norm)
    
    text_lower = normalized.lower()
    
    if re.search(r'\b(днр|dnr|донецк|горловка|макеевка|енакиево)\b', text_lower):
        found.add("Донецкая Народная Республика")
    if re.search(r'\b(лнр|lnr|луганск|алчевск|брянка)\b', text_lower):
        found.add("Луганская Народная Республика")
    if re.search(r'\b(лднр|ldnr)\b', text_lower):
        found.add("Донецкая Народная Республика")
        found.add("Луганская Народная Республика")
    if re.search(r'запорожск|zaporizh', text_lower):
        found.add("Запорожская область")
    if re.search(r'херсон|kherson', text_lower):
        found.add("Херсонская область")
    
    return list(found)

def detect_status(text):
    t = text.lower()
    
    # Отбой - проверяется первым
    if any(w in t for w in [
        "отбой", "отбой опасности", "отбой по бпла", "отбой ракетной опасности",
        "отбой авиационной", "отбой фиксации", "отбой по пкр", "отбой по бэк"
    ]):
        return "clear"
    
    if "ложная цель" in t:
        return None
    
    # Ракетная тревога
    if any(w in t for w in [
        "ракетная тревога", "ракетной тревоги", "тревога по пкр", "тревога по бэк",
        "ракетно бомбовая опасность", "авиационная ракетная"
    ]):
        return "missile_alert"
    
    # Ракетная опасность
    if any(w in t for w in [
        "ракетная опасность", "ракетной опасности", "опасность по пкр", "опасность по бэк"
    ]):
        return "missile_danger"
    
    # Атака БПЛА
    if any(w in t for w in [
        "работа пво", "сбитие", "сбития", "фиксация бпла", "фиксации бпла",
        "группа бпла", "группы бпла", "тревога по бпла", "атака бпла", "атакуют",
        "много бпла", "волна бпла", "фиксация групп", "идут сбития"
    ]):
        return "drone_attack"
    
    # Опасность БПЛА
    if any(w in t for w in [
        "опасность по бпла", "угроза атаки", "внимание по бпла", "меры безопасности",
        "опасность сохраняется", "повторно"
    ]):
        return "drone_danger"
    
    return None

def process_message(text, msg_id=None, source="main"):
    if not text:
        return
    
    if source == "main" and is_pure_ad_message(text):
        if msg_id:
            print(f"  ↳ Реклама (пропущено)")
        return
    
    if is_superseded_by_later(text):
        if msg_id:
            print(f"  ↳ Сводка (пропущено)")
        return
    
    regions = extract_regions(text)
    if not regions:
        if msg_id:
            print(f"  ↳ Регионы не найдены")
        return
    
    if source == "dpr":
        regions = [r for r in regions if r in ALLOWED_DPR_REGIONS]
        if not regions:
            if msg_id:
                print(f"  ↳ Регион не из списка (пропущено)")
            return
    
    status = detect_status(text)
    if not status:
        if msg_id:
            print(f"  ↳ Статус не определён: {text[:50]}")
        return
    
    now = datetime.now(timezone.utc).isoformat()
    clean_msg = clean_message_for_frontend(text)
    
    for r in regions:
        cur = region_statuses.get(r, {}).get("status")
        
        # clear ВСЕГДА перезаписывает (сбрасывает любой статус)
        if status == "clear":
            # clear применяется всегда
            pass
        # Для остальных статусов: проверяем приоритет
        elif cur is not None and STATUS_PRIORITY.get(status, 99) > STATUS_PRIORITY.get(cur, 99):
            if msg_id:
                print(f"  ↳ {r}: {status} (приор.{STATUS_PRIORITY.get(status,99)}) не приоритетнее {cur} (приор.{STATUS_PRIORITY.get(cur,99)})")
            continue
        
        region_statuses[r] = {
            "status": status, 
            "last_update": now, 
            "message": clean_msg[:500] if clean_msg else "",
            "source": source
        }
        
        alert_history.append({
            "region": r, 
            "status": status, 
            "timestamp": now,
            "message": clean_msg[:500] if clean_msg else "",
            "source": source
        })
        
        if len(alert_history) > 1000:
            alert_history.pop(0)
        
        if msg_id:
            print(f"  ✅ {r} → {status} (источник: {source})")

# ---------- FLASK ----------
@app.route("/api/statuses")
def get_statuses():
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    result = {"regions": {}, "last_updated": now.isoformat()}
    
    for r, d in region_statuses.items():
        count = 0
        for a in reversed(alert_history[-200:]):
            if a["region"] == r:
                at = datetime.fromisoformat(a["timestamp"])
                if at > hour_ago:
                    count += 1
        
        result["regions"][r] = {
            "status": d["status"], 
            "last_update": d["last_update"], 
            "message": d.get("message", ""),
            "alerts_last_hour": count,
            "source": d.get("source", "unknown")
        }
    
    return jsonify(result)

@app.route("/api/recent_alerts")
def get_recent_alerts():
    filtered = []
    for alert in reversed(alert_history[-100:]):
        filtered.append(alert)
        if len(filtered) >= 50:
            break
    
    return jsonify({
        "alerts": filtered,
        "total": len(filtered),
        "last_updated": datetime.now(timezone.utc).isoformat()
    })

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "endpoints": ["/api/statuses", "/api/recent_alerts"],
        "regions_count": len(region_statuses),
        "last_update": datetime.now(timezone.utc).isoformat()
    })

# ---------- GITHUB ----------
def push_to_github():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/data/statuses.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    export_data = {
        "regions": {},
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    for r, d in region_statuses.items():
        export_data["regions"][r] = {
            "status": d["status"],
            "last_update": d["last_update"],
            "message": d.get("message", "")
        }
    
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
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
        print("📤 Данные отправлены в GitHub")
    except Exception as e:
        print(f"❌ Ошибка отправки в GitHub: {e}")

# ---------- ФОНОВЫЕ ЗАДАЧИ ----------
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ---------- TELEGRAM ----------
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def poll_messages():
    global last_msg_id_main, last_msg_id_dpr
    
    try:
        main_channel = await client.get_entity(CHANNEL_USERNAME)
        dpr_channel = await client.get_entity(DPR_CHANNEL)
        print(f"✅ Основной канал: {main_channel.title}")
        print(f"✅ Канал ДНР/ЛНР: {dpr_channel.title}")
    except Exception as e:
        print(f"❌ Ошибка получения каналов: {e}")
        return
    
    while True:
        await asyncio.sleep(30)
        
        # Основной канал
        try:
            messages = await client.get_messages(CHANNEL_USERNAME, limit=30)
            if messages:
                for msg in reversed(messages):
                    if msg.id <= last_msg_id_main:
                        continue
                    last_msg_id_main = msg.id
                    if msg.message:
                        preview = msg.message[:80].replace('\n', ' ')
                        print(f"📩 [main] ID:{msg.id} | {preview}...")
                        process_message(msg.message, msg.id, source="main")
        except Exception as e:
            print(f"❌ Ошибка основного канала: {e}")
        
        # Канал ДНР/ЛНР
        try:
            dpr_messages = await client.get_messages(DPR_CHANNEL, limit=30)
            if dpr_messages:
                for msg in reversed(dpr_messages):
                    if msg.id <= last_msg_id_dpr:
                        continue
                    last_msg_id_dpr = msg.id
                    if msg.message:
                        preview = msg.message[:80].replace('\n', ' ')
                        print(f"📩 [DPR] ID:{msg.id} | {preview}...")
                        process_message(msg.message, msg.id, source="dpr")
        except Exception as e:
            print(f"❌ Ошибка канала ДНР/ЛНР: {e}")

async def main():
    await client.start()
    print("✅ Telegram клиент запущен")
    
    global last_msg_id_main, last_msg_id_dpr
    
    print("📥 Загружаем историю...")
    
    try:
        history_main = await client.get_messages(CHANNEL_USERNAME, limit=100)
        if history_main:
            last_msg_id_main = history_main[0].id
            for msg in reversed(history_main):
                if msg.message:
                    process_message(msg.message, msg.id, source="main")
            print(f"✅ Обработано {len(history_main)} сообщений из основного канала")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    try:
        history_dpr = await client.get_messages(DPR_CHANNEL, limit=100)
        if history_dpr:
            last_msg_id_dpr = history_dpr[0].id
            for msg in reversed(history_dpr):
                if msg.message:
                    process_message(msg.message, msg.id, source="dpr")
            print(f"✅ Обработано {len(history_dpr)} сообщений из канала ДНР/ЛНР")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print(f"📊 Статусов регионов: {len(region_statuses)}")
    
    asyncio.create_task(poll_messages())
    print("🔄 Polling запущен (каждые 30 секунд)")
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()
    
    print(f"""
    ╔═══════════════════════════════════════════════════╗
    ║              ✅ СЕРВЕР ЗАПУЩЕН                    ║
    ╠═══════════════════════════════════════════════════╣
    ║   📡 Основной канал: {CHANNEL_USERNAME}
    ║   📡 Канал ДНР/ЛНР: {DPR_CHANNEL}
    ║   📊 Статусов активно: {len(region_statuses)}
    ║   🔄 Обновление: 30 сек
    ║   🎯 clear ВСЕГДА сбрасывает любой статус!
    ║   🎯 Ракетная тревога имеет наивысший приоритет
    ╚═══════════════════════════════════════════════════╝
    """)
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
