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

last_summary = {"drone_danger": [], "drone_attack": [], "missile_danger": [], "missile_alert": [], "timestamp": None}

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
    "Башкортостан": "Республика Башкортостан",
    "Оренбургская область": "Оренбургская область",
    "Самарская область": "Самарская область",
    "Чувашская Республика": "Чувашская Республика",
    "Чувашия": "Чувашская Республика",
    "Республика Татарстан": "Республика Татарстан",
    "Татарстан": "Республика Татарстан",
    "Республика Марий Эл": "Республика Марий Эл",
    "Марий Эл": "Республика Марий Эл",
    "Республика Мордовия": "Республика Мордовия",
    "Мордовия": "Республика Мордовия",
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
telegram_client = None

GENITIVE_MAP = {
    "костромской": "Костромская область",
    "кировской": "Кировская область",
    "московской": "Московская область",
    "ленинградской": "Ленинградская область",
    "нижегородской": "Нижегородская область",
    "тульской": "Тульская область",
    "калужской": "Калужская область",
    "рязанской": "Рязанская область",
    "тверской": "Тверская область",
    "воронежской": "Воронежская область",
    "белгородской": "Белгородская область",
    "брянской": "Брянская область",
    "курской": "Курская область",
    "смоленской": "Смоленская область",
    "орловской": "Орловская область",
    "липецкой": "Липецкая область",
    "тамбовской": "Тамбовская область",
    "владимирской": "Владимирская область",
    "ивановской": "Ивановская область",
    "ярославской": "Ярославская область",
    "вологодской": "Вологодская область",
    "новгородской": "Новгородская область",
    "псковской": "Псковская область",
    "калининградской": "Калининградская область",
    "пензенской": "Пензенская область",
    "ульяновской": "Ульяновская область",
    "саратовской": "Саратовская область",
    "самарской": "Самарская область",
    "оренбургской": "Оренбургская область",
    "челябинской": "Челябинская область",
    "свердловской": "Свердловская область",
    "курганской": "Курганская область",
    "тюменской": "Тюменская область",
    "омской": "Омская область",
    "томской": "Томская область",
    "новосибирской": "Новосибирская область",
    "кемеровской": "Кемеровская область",
    "иркутской": "Иркутская область",
    "амурской": "Амурская область",
    "сахалинской": "Сахалинская область",
    "магаданской": "Магаданская область",
    "мурманской": "Мурманская область",
    "архангельской": "Архангельская область",
    "астраханской": "Астраханская область",
    "волгоградской": "Волгоградская область",
    "ростовской": "Ростовская область",
    "запорожской": "Запорожская область",
    "херсонской": "Херсонская область",
}

def expire_old_statuses():
    global region_statuses, last_summary
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
        last_summary = {"drone_danger": [], "drone_attack": [], "missile_danger": [], "missile_alert": [], "timestamp": None}
        save_state()
    
    return changed

def clear_status_by_type(status_type, source="system"):
    global region_statuses, last_summary
    now = datetime.now(timezone.utc).isoformat()
    cleared_count = 0
    
    status_names = {
        "drone_danger": "опасность БПЛА",
        "missile_danger": "ракетная опасность",
        "missile_alert": "ракетная тревога",
        "drone_attack": "атака БПЛА"
    }
    
    for region, data in list(region_statuses.items()):
        if data.get("status") == status_type:
            region_statuses[region] = {
                "status": "clear",
                "last_update": now,
                "message": f"Отбой {status_names.get(status_type, status_type)} по всем регионам",
                "source": source
            }
            cleared_count += 1
            print(f"  🚫 {region}: отбой {status_names.get(status_type, status_type)} → clear")
    
    if cleared_count > 0:
        print(f"✅ Отбой {status_names.get(status_type, status_type)}: сброшено {cleared_count} регионов")
        last_summary = {"drone_danger": [], "drone_attack": [], "missile_danger": [], "missile_alert": [], "timestamp": None}
        save_state()
    
    return cleared_count > 0

def save_state():
    try:
        state = {
            "region_statuses": region_statuses,
            "alert_history": alert_history[-2000:],
            "last_msg_id_main": last_msg_id_main,
            "last_msg_id_dpr": last_msg_id_dpr,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "last_summary": last_summary
        }
        with open(PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        print(f"❤️ State saved ({len(alert_history)} records)")
    except Exception as e:
        print(f"❌ Save error: {e}")

def load_state():
    global region_statuses, alert_history, last_msg_id_main, last_msg_id_dpr, last_summary
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
        saved_summary = state.get("last_summary")
        if saved_summary:
            last_summary = saved_summary
        print(f"✅ State loaded: {len(region_statuses)} regions, {len(alert_history)} history records")
    except Exception as e:
        print(f"❌ Load error: {e}")

def get_short_name(region):
    return REGION_SHORT_NAMES.get(region, region)

def format_summary(regions):
    drone_danger = []
    drone_attack = []
    missile_danger = []
    missile_alert = []

    for region, data in regions.items():
        status = data.get("status")
        if not status or status == "clear":
            continue
        
        short_name = get_short_name(region)
        
        if status == "drone_danger":
            drone_danger.append(f"    • {short_name}")
        elif status == "drone_attack":
            drone_attack.append(f"    • {short_name}")
        elif status == "missile_danger":
            missile_danger.append(f"    • {short_name}")
        elif status == "missile_alert":
            missile_alert.append(f"    • {short_name}")

    drone_danger.sort()
    drone_attack.sort()
    missile_danger.sort()
    missile_alert.sort()

    global last_summary
    current = {
        "drone_danger": drone_danger,
        "drone_attack": drone_attack,
        "missile_danger": missile_danger,
        "missile_alert": missile_alert
    }
    
    if (last_summary.get("drone_danger") == drone_danger and
        last_summary.get("drone_attack") == drone_attack and
        last_summary.get("missile_danger") == missile_danger and
        last_summary.get("missile_alert") == missile_alert):
        return None

    last_summary = current
    last_summary["timestamp"] = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc) + timedelta(hours=3)
    time_str = now.strftime("%H:%M | %d/%m")

    message = f"✈️ *Воздушная тревога* 🚀\n`{time_str}`\n\n"
    
    active_alerts = []
    active_alerts.extend(missile_alert)
    active_alerts.extend(missile_danger)
    active_alerts.extend(drone_attack)
    
    message += "🔴 *АКТИВНАЯ ТРЕВОГА*\n"
    if active_alerts:
        message += "\n".join(active_alerts) + "\n\n"
    else:
        message += "    • Отсутствует\n\n"
    
    message += "🟡 *ПОТЕНЦИАЛЬНАЯ ОПАСНОСТЬ*\n"
    if drone_danger:
        message += "\n".join(drone_danger) + "\n\n"
    else:
        message += "    • Отсутствует\n\n"
    
    message += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)"
    message += "\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"

    return message

async def send_report(client, force=False):
    if not region_statuses:
        print("⚠️ Нет данных о регионах, сводка не отправлена")
        return
    
    summary = format_summary(region_statuses)
    if summary is None and not force:
        print("ℹ️ Сводка не изменилась, пропускаем")
        return
    
    if summary is None and force:
        if last_summary and last_summary.get("timestamp"):
            now = datetime.now(timezone.utc) + timedelta(hours=3)
            time_str = now.strftime("%H:%M | %d/%m")
            summary = f"✈️ *Воздушная тревога* 🚀\n`{time_str}`\n\n"
            
            active_alerts = []
            active_alerts.extend(last_summary.get("missile_alert", []))
            active_alerts.extend(last_summary.get("missile_danger", []))
            active_alerts.extend(last_summary.get("drone_attack", []))
            
            summary += "🔴 *АКТИВНАЯ ТРЕВОГА*\n"
            if active_alerts:
                summary += "\n".join(active_alerts) + "\n\n"
            else:
                summary += "    • Отсутствует\n\n"
            
            summary += "🟡 *ПОТЕНЦИАЛЬНАЯ ОПАСНОСТЬ*\n"
            if last_summary.get("drone_danger", []):
                summary += "\n".join(last_summary.get("drone_danger", [])) + "\n\n"
            else:
                summary += "    • Отсутствует\n\n"
            
            summary += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)"
            summary += "\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"
        else:
            print("ℹ️ Нет данных для форсированной отправки")
            return
    
    try:
        entity = await client.get_entity(REPORT_CHANNEL)
        await client.send_message(entity, summary, link_preview=False)
        print(f"📢 Отправлена сводка в @{REPORT_CHANNEL}" + (" (форсированно)" if force else ""))
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
    
    ad_indicators = [
        "❗️ВНИМАНИЕ",
        "Враг планирует",
        "Впервые регионы РФ подверглись массовым РАКЕТНЫМ атакам",
        "создать телеграм каналы для оповещения граждан",
        "Ищите свой регион и подписывайтесь",
        "НЕ БУДУТ БЛОКИРОВАТЬ",
        "Нет вашего региона",
        "вакансия без опыта",
        "Пятёрочка ищет людей",
        "платят от",
        "АВАНС",
        "Удалять негативные отзывы",
        "Ставить лайки под роликами",
        "Сравнивать цены",
        "24/7 (https://t.me/",
        "Москва 24/7",
        "Питер 24/7",
        "Подписывайтесь",
        "будет автоматически выдан АВАНС"
    ]
    
    text_upper = text.upper()
    for indicator in ad_indicators:
        if indicator.upper() in text_upper:
            return True
    
    link_count = len(re.findall(r'https?://t\.me/', text))
    if link_count > 3:
        return True
    
    cleaned = clean_message_for_frontend(text)
    return not cleaned or len(cleaned) < 15

def is_superseded_by_later(text):
    return bool(re.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", text, re.IGNORECASE))

def extract_regions(text):
    """
    Извлекает регионы из текста сообщения.
    ИСПРАВЛЕНО: Использует строгое сопоставление по GENITIVE_MAP для родительного падежа,
    чтобы "костромской" не матчился с "омской".
    """
    text_lower = text.lower()
    found = set()
    
    region_blacklist = set()

    for alias, norm in REGION_ALIASES.items():
        alias_lower = alias.lower()
        if re.search(rf'{re.escape(alias_lower)}(?:ский|ская|ское|ской|ского|скому|ским|ском)?\s+район', text_lower):
            region_blacklist.add(norm)
            print(f"  ⚠️ Игнорируем {norm} (обнаружено 'район' рядом с названием)")
        short_name = norm.replace(" область", "").replace(" край", "").replace(" Республика", "").replace(" республика", "")
        short_name_lower = short_name.lower()
        if len(short_name_lower) > 3:
            if re.search(rf'{re.escape(short_name_lower)}(?:ский|ская|ское|ской|ского|скому|ским|ском)?\s+район', text_lower):
                region_blacklist.add(norm)
                print(f"  ⚠️ Игнорируем {norm} (обнаружено '{short_name}ский район')")
    

    genitive_matches = re.findall(r'([А-Яа-яёЁ]+(?:ской|ской))\s+области', text_lower)
    for region_name in genitive_matches:
        region_lower = region_name.lower()
        if region_lower in GENITIVE_MAP:
            norm = GENITIVE_MAP[region_lower]
            if norm not in region_blacklist:
                found.add(norm)
                print(f"  🔍 Найден регион (род. падеж, точное совпадение): {region_name} -> {norm}")
        else:
            for alias, norm in REGION_ALIASES.items():
                alias_lower = alias.lower()
                if alias_lower.startswith(region_lower) or region_lower in alias_lower:
                    if norm not in region_blacklist:
                        found.add(norm)
                        print(f"  🔍 Найден регион (род. падеж, alias): {region_name} -> {norm}")
                    break
    
    nominative_matches = re.findall(r'([А-Яа-яёЁ]+(?:ская|ская))\s+область', text_lower)
    for region_name in nominative_matches:
        for alias, norm in REGION_ALIASES.items():
            if region_name in alias.lower():
                if norm not in region_blacklist:
                    found.add(norm)
                    print(f"  🔍 Найден регион (им. падеж): {region_name} -> {norm}")
                break
    
    krai_matches = re.findall(r'([А-Яа-яёЁ]+(?:ский|ский))\s+край', text_lower)
    for region_name in krai_matches:
        for alias, norm in REGION_ALIASES.items():
            if region_name in alias.lower():
                if norm not in region_blacklist:
                    found.add(norm)
                    print(f"  🔍 Найден край: {region_name} -> {norm}")
                break
    
    republic_matches = re.findall(r'(?:республика|республики)\s+([А-Яа-яёЁ][а-яёЁ]+(?:ская|ская)?)', text_lower)
    for region_name in republic_matches:
        for alias, norm in REGION_ALIASES.items():
            if region_name in alias.lower() or region_name in norm.lower():
                if norm not in region_blacklist:
                    found.add(norm)
                    print(f"  🔍 Найдена республика: {region_name} -> {norm}")
                break
    
    direct_republics = [
        "башкортостан", "чувашия", "татарстан", "удмуртия", 
        "марий эл", "мордовия", "карелия", "коми", "адыгея",
        "калмыкия", "алтай", "хакасия", "тыва", "бурятия", "саха"
    ]
    for rep in direct_republics:
        if rep in text_lower:
            for alias, norm in REGION_ALIASES.items():
                if rep in alias.lower() or rep in norm.lower():
                    if norm not in region_blacklist:
                        found.add(norm)
                        print(f"  🔍 Найдена республика по прямому названию: {rep} -> {norm}")
                    break
    
    for alias, norm in REGION_ALIASES.items():
        if alias.lower() in text_lower:
            if norm not in region_blacklist:
                found.add(norm)
    
    if "Донецкая Народная Республика" not in region_blacklist:
        if re.search(r'\b(днр|dnr|донецк|горловка|макеевка|енакиево)\b', text_lower):
            found.add("Донецкая Народная Республика")
    if "Луганская Народная Республика" not in region_blacklist:
        if re.search(r'\b(лнр|lnr|луганск|алчевск|брянка)\b', text_lower):
            found.add("Луганская Народная Республика")
    if "Запорожская область" not in region_blacklist:
        if re.search(r'запорожск|zaporizh', text_lower):
            found.add("Запорожская область")
    if "Херсонская область" not in region_blacklist:
        if re.search(r'херсон|kherson', text_lower):
            found.add("Херсонская область")
    
    return list(found)

def detect_status(text):
    t = text.lower()

    if "отбой опасности бпла по всем ранее объявленным регионам" in t:
        return "mass_clear_drone_danger"
    
    if "отбой ракетной опасности по всем ранее объявленным регионам" in t:
        return "mass_clear_missile_danger"
    
    if "отбой ракетной тревоги по всем ранее объявленным регионам" in t:
        return "mass_clear_missile_alert"

    if any(w in t for w in [
        "отбой", "отбой опасности", "отбой по бпла", "отбой ракетной опасности",
        "отбой авиационной", "отбой фиксации", "отбой по пкр", "отбой по бэк",
        "все спокойно", "тихо", "обстановка спокойная"
    ]):
        return "clear"

    if "ложная цель" in t:
        return None

    if any(w in t for w in [
        "ракетная тревога", "ракетной тревоги", "тревога по пкр", "тревога по бэк",
        "ракетно бомбовая опасность", "авиационная ракетная", "авиационная ракетная бомбовая опасность"
    ]):
        return "missile_alert"

    if any(w in t for w in [
        "ракетная опасность", "ракетной опасности", "опасность по пкр", "опасность по бэк"
    ]):
        return "missile_danger"

    if any(w in t for w in [
        "работа пво", "сбитие", "сбития", "фиксация бпла", "фиксации бпла",
        "группа бпла", "группы бпла", "тревога по бпла", "атака бпла", "атакуют",
        "много бпла", "волна бпла", "фиксация групп", "идут сбития", "массовый запуск"
    ]):
        return "drone_attack"

    if any(w in t for w in [
        "опасность по бпла", "угроза атаки", "внимание по бпла", "меры безопасности",
        "опасность сохраняется", "повторно", "fpv", "fpv-дронам",
        "единичных бпла", "внимание"
    ]):
        return "drone_danger"

    return None

def process_message(text, msg_id=None, source="main", msg_date=None, is_history=False):
    global region_statuses, alert_history

    if not text:
        return False

    if source == "main" and is_pure_ad_message(text):
        print(f"  🚫 Рекламное сообщение пропущено: {text[:50]}...")
        return False

    if is_superseded_by_later(text):
        return False

    status = detect_status(text)
    
    if status and status.startswith("mass_clear_"):
        if status == "mass_clear_drone_danger":
            updated = clear_status_by_type("drone_danger", source)
        elif status == "mass_clear_missile_danger":
            updated = clear_status_by_type("missile_danger", source)
        elif status == "mass_clear_missile_alert":
            updated = clear_status_by_type("missile_alert", source)
        
        if updated and not is_history:
            alert_history.append({
                "region": "ВСЕ РЕГИОНЫ",
                "status": "mass_clear",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": text[:500],
                "source": source
            })
        return updated

    regions = extract_regions(text)
    if not regions:
        return False

    if source == "dpr":
        regions = [r for r in regions if r in ALLOWED_DPR_REGIONS]
        if not regions:
            return False

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

        if source == "dpr":
            pass
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

def periodic_expire():
    global telegram_client
    
    while True:
        time.sleep(600)
        try:
            print("🔍 Проверка устаревших статусов...")
            changed = expire_old_statuses()
            if changed and telegram_client:
                print("📢 Отправляем обновлённую сводку после устаревания...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_report(telegram_client, force=True))
                loop.close()
        except Exception as e:
            print(f"❌ Ошибка при устаревании статусов: {e}")

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
        "total": len(alert_history),
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

def push_to_github():
    pass

def periodic_push():
    while True:
        time.sleep(60)
        if region_statuses:
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

async def poll_messages():
    global last_msg_id_main, last_msg_id_dpr, telegram_client

    try:
        main_channel = await telegram_client.get_entity(CHANNEL_USERNAME)
        dpr_channel = await telegram_client.get_entity(DPR_CHANNEL)
        print(f"✅ Основной канал: {main_channel.title}")
        print(f"✅ Канал ДНР/ЛНР: {dpr_channel.title}")
    except Exception as e:
        print(f"❌ Ошибка получения каналов: {e}")
        return

    while True:
        await asyncio.sleep(30)

        try:
            messages = await telegram_client.get_messages(CHANNEL_USERNAME, limit=50)
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
                    await send_report(telegram_client)
        except Exception as e:
            print(f"❌ Ошибка основного канала: {e}")

        try:
            dpr_messages = await telegram_client.get_messages(DPR_CHANNEL, limit=50)
            if dpr_messages:
                updated = False
                for msg in reversed(dpr_messages):
                    if msg.id <= last_msg_id_dpr:
                        continue
                    last_msg_id_dpr = msg.id
                    if msg.message:
                        preview = msg.message[:80].replace('\n', ' ')
                        print(f"📩 [DPR/Новороссия] ID:{msg.id} | {preview}...")
                        if process_message(msg.message, msg.id, source="dpr", msg_date=msg.date):
                            updated = True
                if updated:
                    await send_report(telegram_client)
        except Exception as e:
            print(f"❌ Ошибка канала ДНР/ЛНР: {e}")

async def main():
    global telegram_client, last_msg_id_main, last_msg_id_dpr, region_statuses
    
    telegram_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await telegram_client.start()
    print("✅ Telegram клиент запущен")

    load_state()
    expire_old_statuses()

    last_msg_id_main_loaded = last_msg_id_main
    last_msg_id_dpr_loaded = last_msg_id_dpr

    print("📥 Загружаем историю...")

    try:
        all_messages = await telegram_client.get_messages(CHANNEL_USERNAME, limit=200)
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

    try:
        all_messages = await telegram_client.get_messages(DPR_CHANNEL, limit=200)
        if all_messages:
            sorted_messages = sorted(all_messages, key=lambda x: x.id)
            last_msg_id_dpr = sorted_messages[-1].id
            new_count = 0
            for msg in sorted_messages:
                if msg.id <= last_msg_id_dpr_loaded:
                    continue
                if msg.message:
                    preview = msg.message[:80].replace('\n', ' ')
                    print(f"📥 [DPR/Новороссия] ID:{msg.id} | {preview}...")
                    process_message(msg.message, msg.id, source="dpr", msg_date=msg.date, is_history=True)
                    new_count += 1
                    await asyncio.sleep(0.05)
            print(f"✅ Обработано {len(sorted_messages)} сообщений из канала ДНР/ЛНР (новых: {new_count})")
    except Exception as e:
        print(f"❌ Ошибка канала ДНР/ЛНР: {e}")

    expire_old_statuses()

    print(f"📊 Статусов регионов: {len(region_statuses)}")
    print(f"📋 Записей в истории: {len(alert_history)}")

    await send_report(telegram_client)

    asyncio.create_task(poll_messages())
    print("🔄 Polling запущен (каждые 30 секунд)")

    threading.Thread(target=periodic_expire, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()

    print(f"""
    ╔═══════════════════════════════════════════════════╗
    ║              ✅ СЕРВЕР ЗАПУЩЕН                    ║
    ╠═══════════════════════════════════════════════════╣
    ║   📡 Основной канал: {CHANNEL_USERNAME}
    ║   📡 Канал Новороссии: {DPR_CHANNEL}
    ║   📢 Канал для сводок: @{REPORT_CHANNEL}
    ║   📊 Статусов активно: {len(region_statuses)}
    ║   📋 Записей в истории: {len(alert_history)}
    ║   ⏰ Устаревание статусов: {STATUS_EXPIRY_HOURS} часов
    ╚═══════════════════════════════════════════════════╝
    """)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
