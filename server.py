import os, re, json, base64, threading, time, requests, asyncio
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

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
REPORT_CHANNEL = os.environ.get("REPORT_CHANNEL", "RadarMapRf")
STATUS_EXPIRY_HOURS = int(os.environ.get("STATUS_EXPIRY_HOURS", 12))

print("✅ Конфигурация загружена")
print(f"📡 Основной канал: {CHANNEL_USERNAME}")
print(f"📡 Канал ДНР/ЛНР: {DPR_CHANNEL}")
print(f"📢 Канал для сводок: @{REPORT_CHANNEL}")
print(f"⏰ Статусы устаревают через: {STATUS_EXPIRY_HOURS} часов")

# Приоритеты (меньше число = выше приоритет)
STATUS_PRIORITY = {
    "missile_alert": 0,
    "missile_danger": 1,
    "drone_attack": 2,
    "drone_danger": 3,
    "clear": 4,
}

REGION_SHORT_NAMES = {
    "Московская область": "Московская обл.",
    "Москва": "Москва",
    "Ленинградская область": "Ленинградская обл.",
    "Санкт-Петербург": "Санкт-Петербург",
    "Нижегородская область": "Нижегородская обл.",
    "Ставропольский край": "Ставропольский край",
    "Краснодарский край": "Краснодарский край",
    "Чеченская Республика": "Чеченская Респ.",
    "Республика Дагестан": "Респ. Дагестан",
    "Республика Ингушетия": "Респ. Ингушетия",
    "Республика Северная Осетия": "Респ. Сев. Осетия",
    "Карачаево-Черкесская Республика": "Карачаево-Черкесия",
    "Кабардино-Балкарская Республика": "Кабардино-Балкария",
    "Республика Адыгея": "Респ. Адыгея",
    "Республика Крым": "Респ. Крым",
    "Запорожская область": "Запорожская обл.",
    "Херсонская область": "Херсонская обл.",
    "Донецкая Народная Республика": "ДНР",
    "Луганская Народная Республика": "ЛНР",
    "Астраханская область": "Астраханская обл.",
    "Волгоградская область": "Волгоградская обл.",
    "Белгородская область": "Белгородская обл.",
    "Брянская область": "Брянская обл.",
    "Воронежская область": "Воронежская обл.",
    "Курская область": "Курская обл.",
    "Ростовская область": "Ростовская обл.",
    "Смоленская область": "Смоленская обл.",
    "Тульская область": "Тульская обл.",
    "Калужская область": "Калужская обл.",
    "Рязанская область": "Рязанская обл.",
    "Тверская область": "Тверская обл.",
    "Ярославская область": "Ярославская обл.",
    "Владимирская область": "Владимирская обл.",
    "Ивановская область": "Ивановская обл.",
    "Костромская область": "Костромская обл.",
    "Тамбовская область": "Тамбовская обл.",
    "Липецкая область": "Липецкая обл.",
    "Орловская область": "Орловская обл.",
    "Пензенская область": "Пензенская обл.",
    "Саратовская область": "Саратовская обл.",
    "Ульяновская область": "Ульяновская обл.",
    "Самарская область": "Самарская обл.",
    "Пермский край": "Пермский край",
    "Республика Башкортостан": "Респ. Башкортостан",
    "Республика Татарстан": "Респ. Татарстан",
    "Республика Удмуртия": "Респ. Удмуртия",
    "Республика Марий Эл": "Респ. Марий Эл",
    "Республика Мордовия": "Респ. Мордовия",
    "Чувашская Республика": "Чувашская Респ.",
    "Кировская область": "Кировская обл.",
    "Оренбургская область": "Оренбургская обл.",
    "Челябинская область": "Челябинская обл.",
    "Свердловская область": "Свердловская обл.",
    "Курганская область": "Курганская обл.",
    "Тюменская область": "Тюменская обл.",
    "Омская область": "Омская обл.",
    "Новосибирская область": "Новосибирская обл.",
    "Томская область": "Томская обл.",
    "Кемеровская область": "Кемеровская обл.",
    "Алтайский край": "Алтайский край",
    "Красноярский край": "Красноярский край",
    "Иркутская область": "Иркутская обл.",
    "Забайкальский край": "Забайкальский край",
    "Республика Бурятия": "Респ. Бурятия",
    "Приморский край": "Приморский край",
    "Хабаровский край": "Хабаровский край",
    "Амурская область": "Амурская обл.",
    "Сахалинская область": "Сахалинская обл.",
    "Камчатский край": "Камчатский край",
    "Магаданская область": "Магаданская обл.",
    "Республика Саха (Якутия)": "Респ. Саха (Якутия)",
    "Еврейская АО": "Еврейская АО",
    "Чукотский АО": "Чукотский АО",
    "ЯНАО": "ЯНАО",
    "Ханты-Мансийский АО": "ХМАО",
    "Ненецкий АО": "Ненецкий АО",
    "Республика Карелия": "Респ. Карелия",
    "Республика Коми": "Респ. Коми",
    "Архангельская область": "Архангельская обл.",
    "Мурманская область": "Мурманская обл.",
    "Вологодская область": "Вологодская обл.",
    "Новгородская область": "Новгородская обл.",
    "Псковская область": "Псковская обл.",
    "Калининградская область": "Калининградская обл.",
    "Республика Алтай": "Респ. Алтай",
    "Республика Хакасия": "Респ. Хакасия",
    "Республика Тыва": "Респ. Тыва",
    "Республика Калмыкия": "Респ. Калмыкия",
}

last_summary = {"missile_alert": [], "missile_danger": [], "drone_attack": [], "drone_danger": [], "timestamp": None}

REGION_ALIASES = {
    "Московская область": "Московская область",
    "Московский регион": "Московская область",
    "Подмосковье": "Московская область",
    "Москва": "Москва",
    "г. Москва": "Москва",
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
    "Кемеровская область": "Кемеровская область",
    "Республика Алтай": "Республика Алтай",
    "Республика Хакасия": "Республика Хакасия",
    "Республика Тыва": "Республика Тыва",
    "Красноярский край": "Красноярский край",
    "Республика Бурятия": "Республика Бурятия",
    "Иркутская область": "Иркутская область",
    "Забайкальский край": "Забайкальский край",
    "Амурская область": "Амурская область",
    "Республика Саха (Якутия)": "Республика Саха (Якутия)",
    "Еврейская АО": "Еврейская АО",
    "Приморский край": "Приморский край",
    "Хабаровский край": "Хабаровский край",
    "Сахалинская область": "Сахалинская область",
    "Магаданская область": "Магаданская область",
    "Камчатский край": "Камчатский край",
    "Чукотский АО": "Чукотский АО",
    "Донецкая Народная Республика": "Донецкая Народная Республика",
    "Луганская Народная Республика": "Луганская Народная Республика",
    "Запорожская область": "Запорожская область",
    "Херсонская область": "Херсонская область",
}

ALLOWED_DPR_REGIONS = [
    "Донецкая Народная Республика",
    "Луганская Народная Республика",
    "Запорожская область",
    "Херсонская область"
]

region_statuses = {}
alert_history = []
last_msg_id_main = 0
last_msg_id_dpr = 0

PERSIST_FILE = "/tmp/radar_state.json"

def expire_old_statuses():
    """Устанавливает статус clear для регионов, у которых последнее обновление старше STATUS_EXPIRY_HOURS часов"""
    global region_statuses
    now = datetime.now(timezone.utc)
    expiry_time = now - timedelta(hours=STATUS_EXPIRY_HOURS)
    expired_count = 0
    changed = False
    
    for region, data in list(region_statuses.items()):
        last_update_str = data.get("last_update")
        if not last_update_str:
            continue
        
        try:
            last_update = datetime.fromisoformat(last_update_str)
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
            
            if last_update < expiry_time and data.get("status") != "clear":
                region_statuses[region] = {
                    "status": "clear",
                    "last_update": now.isoformat(),
                    "message": f"Автоматический отбой (нет обновлений >{STATUS_EXPIRY_HOURS}ч)",
                    "source": data.get("source", "system")
                }
                expired_count += 1
                changed = True
                print(f"  ⏰ {region}: статус устарел → clear")
        except Exception as e:
            print(f"  ⚠️ Ошибка парсинга даты для {region}: {e}")
    
    if expired_count > 0:
        print(f"✅ Устарело {expired_count} регионов (автоматический отбой)")
        save_state()
    
    return changed

def save_state():
    try:
        state = {
            "region_statuses": region_statuses,
            "alert_history": alert_history[-2000:],
            "last_msg_id_main": last_msg_id_main,
            "last_msg_id_dpr": last_msg_id_dpr,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        with open(PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        print(f"❤️ State saved ({len(alert_history)} records)")
    except Exception as e:
        print(f"❌ Save error: {e}")

def load_state():
    global region_statuses, alert_history, last_msg_id_main, last_msg_id_dpr
    try:
        if not os.path.exists(PERSIST_FILE):
            print("ℹ️ No state file found")
            return
        with open(PERSIST_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        saved_at = state.get("saved_at", "")
        if saved_at:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(saved_at)
            if age.total_seconds() > 48 * 3600:
                print(f"ℹ️ State too old ({age}), skipping")
                return
        region_statuses = state.get("region_statuses", {})
        alert_history = state.get("alert_history", [])
        last_msg_id_main = state.get("last_msg_id_main", 0)
        last_msg_id_dpr = state.get("last_msg_id_dpr", 0)
        print(f"✅ State loaded: {len(region_statuses)} regions, {len(alert_history)} history records")
    except Exception as e:
        print(f"❌ Load error: {e}")

def get_short_name(region):
    return REGION_SHORT_NAMES.get(region, region)

def format_summary(regions):
    missile_alert = []     # 🟤 РАКЕТНАЯ ТРЕВОГА
    missile_danger = []    # 🔴 РАКЕТНАЯ ОПАСНОСТЬ
    drone_attack = []      # 🟠 ТРЕВОГА ПО БПЛА
    drone_danger = []      # 🟡 ОПАСНОСТЬ ПО БПЛА

    for region, data in regions.items():
        status = data.get("status")
        if not status or status == "clear":
            continue
        
        short_name = get_short_name(region)
        
        if status == "missile_alert":
            missile_alert.append(f"    • {short_name}")
        elif status == "missile_danger":
            missile_danger.append(f"    • {short_name}")
        elif status == "drone_attack":
            drone_attack.append(f"    • {short_name}")
        elif status == "drone_danger":
            drone_danger.append(f"    • {short_name}")

    missile_alert.sort()
    missile_danger.sort()
    drone_attack.sort()
    drone_danger.sort()

    global last_summary
    current = {
        "missile_alert": missile_alert,
        "missile_danger": missile_danger,
        "drone_attack": drone_attack,
        "drone_danger": drone_danger
    }
    
    if (last_summary.get("missile_alert") == missile_alert and
        last_summary.get("missile_danger") == missile_danger and
        last_summary.get("drone_attack") == drone_attack and
        last_summary.get("drone_danger") == drone_danger):
        return None

    last_summary = current
    last_summary["timestamp"] = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc) + timedelta(hours=3)
    time_str = now.strftime("%H:%M | %d/%m")

    message = f"✈️ *Воздушная тревога* 🚀\n`{time_str}`\n\n"
    
    message += "🟤 *РАКЕТНАЯ ТРЕВОГА*\n"
    message += ("\n".join(missile_alert) if missile_alert else "    • Отсутствуют") + "\n\n"
    
    message += "🔴 *РАКЕТНАЯ ОПАСНОСТЬ*\n"
    message += ("\n".join(missile_danger) if missile_danger else "    • Отсутствуют") + "\n\n"
    
    message += "🟠 *ТРЕВОГА ПО БПЛА*\n"
    message += ("\n".join(drone_attack) if drone_attack else "    • Отсутствуют") + "\n\n"
    
    message += "🟡 *ОПАСНОСТЬ ПО БПЛА*\n"
    message += ("\n".join(drone_danger) if drone_danger else "    • Отсутствуют") + "\n\n"
    
    message += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)"
    message += "\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"

    return message

async def send_report(client):
    if not region_statuses:
        return
    summary = format_summary(region_statuses)
    if summary is None:
        return
    try:
        entity = await client.get_entity(REPORT_CHANNEL)
        await client.send_message(entity, summary, link_preview=False)
        print(f"📢 Отправлена сводка в @{REPORT_CHANNEL}")
    except FloodWaitError as e:
        print(f"⏳ Flood wait {e.seconds} секунд")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"❌ Ошибка отправки сводки: {e}")

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
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

def is_pure_ad_message(text):
    if not text:
        return False
    if "Радар ДНР" in text:
        return False
    cleaned = clean_message_for_frontend(text)
    return not cleaned or len(cleaned) < 15

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

    if any(w in t for w in [
        "отбой", "отбой опасности", "отбой по бпла", "отбой ракетной опасности",
        "отбой авиационной", "отбой фиксации", "отбой по пкр", "отбой по бэк"
    ]):
        return "clear"

    if "ложная цель" in t:
        return None

    if any(w in t for w in [
        "ракетная тревога", "ракетной тревоги", "тревога по пкр", "тревога по бэк",
        "ракетно бомбовая опасность", "авиационная ракетная"
    ]):
        return "missile_alert"

    if any(w in t for w in [
        "ракетная опасность", "ракетной опасности", "опасность по пкр", "опасность по бэк"
    ]):
        return "missile_danger"

    if any(w in t for w in [
        "работа пво", "сбитие", "сбития", "фиксация бпла", "фиксации бпла",
        "группа бпла", "группы бпла", "тревога по бпла", "атака бпла", "атакуют",
        "много бпла", "волна бпла", "фиксация групп", "идут сбития"
    ]):
        return "drone_attack"

    if any(w in t for w in [
        "опасность по бпла", "угроза атаки", "внимание по бпла", "меры безопасности",
        "опасность сохраняется", "повторно"
    ]):
        return "drone_danger"

    return None

def process_message(text, msg_id=None, source="main", msg_date=None, is_history=False):
    global region_statuses, alert_history

    if not text:
        return False

    if source == "main" and is_pure_ad_message(text):
        return False

    if is_superseded_by_later(text):
        return False

    regions = extract_regions(text)
    if not regions:
        return False

    if source == "dpr":
        regions = [r for r in regions if r in ALLOWED_DPR_REGIONS]
        if not regions:
            return False

    status = detect_status(text)
    if not status:
        return False

    if msg_date is not None:
        if msg_date.tzinfo is None:
            msg_date = msg_date.replace(tzinfo=timezone.utc)
        timestamp = msg_date.isoformat()
    else:
        timestamp = datetime.now(timezone.utc).isoformat()

    clean_msg = clean_message_for_frontend(text)
    updated = False

    for r in regions:
        cur_data = region_statuses.get(r, {})
        cur_status = cur_data.get("status")

        # Для канала ДНР/ЛНР — всегда перезаписываем (игнорируем приоритеты)
        if source == "dpr":
            # Просто перезаписываем
            pass
        # Для основного канала — соблюдаем приоритеты
        elif not is_history and status != "clear":
            if cur_status is not None and STATUS_PRIORITY.get(status, 99) > STATUS_PRIORITY.get(cur_status, 99):
                if msg_id:
                    print(f"  ↳ {r}: {status} не приоритетнее {cur_status}")
                continue

        region_statuses[r] = {
            "status": status,
            "last_update": timestamp,
            "message": clean_msg[:500] if clean_msg else "",
            "source": source
        }

        alert_history.append({
            "region": r,
            "status": status,
            "timestamp": timestamp,
            "message": clean_msg[:500] if clean_msg else "",
            "source": source
        })

        updated = True

        if len(alert_history) > 5000:
            alert_history.pop(0)

        if msg_id:
            print(f"  ✅ {r} → {status} (источник: {source})")

    return updated

# ---------- ФОНОВАЯ ЗАДАЧА ДЛЯ УСТАРЕВАНИЯ СТАТУСОВ ----------
def periodic_expire():
    """Запускает проверку устаревших статусов каждые 10 минут и отправляет сводку если были изменения"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        time.sleep(600)  # 10 минут
        try:
            print("🔍 Проверка устаревших статусов...")
            changed = expire_old_statuses()
            if changed:
                print("📢 Отправляем обновлённую сводку после устаревания...")
                loop.run_until_complete(send_report(client))
        except Exception as e:
            print(f"❌ Ошибка при устаревании статусов: {e}")

# ---------- FLASK ----------
@app.route("/api/statuses")
def get_statuses():
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    result = {"regions": {}, "last_updated": now.isoformat()}

    for r, d in region_statuses.items():
        count = 0
        for a in reversed(alert_history[-5000:]):
            if a["region"] == r:
                try:
                    at = datetime.fromisoformat(a["timestamp"])
                    if at > day_ago:
                        count += 1
                except Exception:
                    pass

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
    filtered = list(reversed(alert_history[-100:]))[:50]
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
    except Exception:
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
            save_state()

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
            messages = await client.get_messages(CHANNEL_USERNAME, limit=50)
            if messages:
                updated = False
                for msg in reversed(messages):
                    if msg.id <= last_msg_id_main:
                        continue
                    last_msg_id_main = msg.id
                    if msg.message:
                        preview = msg.message[:80].replace('\n', ' ')
                        print(f"📩 [main] ID:{msg.id} | {preview}...")
                        if process_message(msg.message, msg.id, source="main", msg_date=msg.date):
                            updated = True
                if updated:
                    await send_report(client)
        except Exception as e:
            print(f"❌ Ошибка основного канала: {e}")

        # Канал ДНР/ЛНР
        try:
            dpr_messages = await client.get_messages(DPR_CHANNEL, limit=50)
            if dpr_messages:
                updated = False
                for msg in reversed(dpr_messages):
                    if msg.id <= last_msg_id_dpr:
                        continue
                    last_msg_id_dpr = msg.id
                    if msg.message:
                        preview = msg.message[:80].replace('\n', ' ')
                        print(f"📩 [DPR] ID:{msg.id} | {preview}...")
                        if process_message(msg.message, msg.id, source="dpr", msg_date=msg.date):
                            updated = True
                if updated:
                    await send_report(client)
        except Exception as e:
            print(f"❌ Ошибка канала ДНР/ЛНР: {e}")

async def main():
    await client.start()
    print("✅ Telegram клиент запущен")

    global last_msg_id_main, last_msg_id_dpr, region_statuses

    load_state()

    # Применяем устаревание к загруженному состоянию
    expire_old_statuses()

    last_msg_id_main_loaded = last_msg_id_main
    last_msg_id_dpr_loaded = last_msg_id_dpr

    print("📥 Загружаем историю (по одному сообщению, от старых к новым)...")

    # ========== ОСНОВНОЙ КАНАЛ ==========
    try:
        all_messages = await client.get_messages(CHANNEL_USERNAME, limit=200)
        if all_messages:
            sorted_messages = sorted(all_messages, key=lambda x: x.id)
            
            last_msg_id_main = sorted_messages[-1].id
            
            new_count = 0
            for msg in sorted_messages:
                if msg.id <= last_msg_id_main_loaded:
                    continue
                if msg.message:
                    preview = msg.message[:80].replace('\n', ' ')
                    print(f"📥 [main] ID:{msg.id} | {preview}...")
                    process_message(msg.message, msg.id, source="main", msg_date=msg.date, is_history=True)
                    new_count += 1
                    await asyncio.sleep(0.05)
            
            print(f"✅ Обработано {len(sorted_messages)} сообщений из основного канала (новых: {new_count})")
    except Exception as e:
        print(f"❌ Ошибка основного канала: {e}")

    # ========== КАНАЛ ДНР/ЛНР ==========
    try:
        all_messages = await client.get_messages(DPR_CHANNEL, limit=200)
        if all_messages:
            sorted_messages = sorted(all_messages, key=lambda x: x.id)
            
            last_msg_id_dpr = sorted_messages[-1].id
            
            new_count = 0
            for msg in sorted_messages:
                if msg.id <= last_msg_id_dpr_loaded:
                    continue
                if msg.message:
                    preview = msg.message[:80].replace('\n', ' ')
                    print(f"📥 [DPR] ID:{msg.id} | {preview}...")
                    process_message(msg.message, msg.id, source="dpr", msg_date=msg.date, is_history=True)
                    new_count += 1
                    await asyncio.sleep(0.05)
            
            print(f"✅ Обработано {len(sorted_messages)} сообщений из канала ДНР/ЛНР (новых: {new_count})")
    except Exception as e:
        print(f"❌ Ошибка канала ДНР/ЛНР: {e}")

    # Ещё раз применяем устаревание после загрузки истории
    expire_old_statuses()

    print(f"📊 Статусов регионов: {len(region_statuses)}")
    print(f"📋 Записей в истории: {len(alert_history)}")

    await send_report(client)

    asyncio.create_task(poll_messages())
    print("🔄 Polling запущен (каждые 30 секунд)")

    # Запускаем фоновую задачу устаревания статусов
    threading.Thread(target=periodic_expire, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()

    print(f"""
    ╔═══════════════════════════════════════════════════╗
    ║              ✅ СЕРВЕР ЗАПУЩЕН                    ║
    ╠═══════════════════════════════════════════════════╣
    ║   📡 Основной канал: {CHANNEL_USERNAME}
    ║   📡 Канал ДНР/ЛНР: {DPR_CHANNEL}
    ║   📢 Канал для сводок: @{REPORT_CHANNEL}
    ║   📊 Статусов активно: {len(region_statuses)}
    ║   📋 Записей в истории: {len(alert_history)}
    ║   🔄 Обновление: 30 сек
    ║   ⏰ Устаревание статусов: {STATUS_EXPIRY_HOURS} часов
    ║   📥 История: последовательная обработка
    ║   🎨 Цвета: 🟤 ракетная тревога | 🔴 ракетная опасность | 🟠 тревога БПЛА | 🟡 опасность БПЛА
    ║   🎯 Для канала ДНР/ЛНР: любой статус перезаписывает предыдущий
    ╚═══════════════════════════════════════════════════╝
    """)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
