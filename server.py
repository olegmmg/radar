import os
import re
import json
import base64
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify
from telethon import TelegramClient, events

app = Flask(__name__)

# ---------- БЕЗОПАСНЫЕ НАСТРОЙКИ (из переменных окружения) ----------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
PHONE = os.environ.get("PHONE")  # +79015054860
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Токен с правами на запись в репо
GITHUB_REPO = os.environ.get("GITHUB_REPO")    # olegmmg/olegmmg.github.io
CHANNEL_USERNAME = "radarrussiia"
DATA_PATH = "data/statuses.json"  # Путь в репозитории GitHub Pages

# ---------- ТИРЛИСТ СТАТУСОВ ----------
STATUS_PRIORITY = {
    "missile_alert": 0,
    "missile_danger": 1,
    "drone_attack": 2,
    "drone_danger": 3,
    "clear": 4
}

STATUS_COLORS = {
    "missile_alert": "#2D0000",
    "missile_danger": "#8B0000",
    "drone_attack": "#FF0000",
    "drone_danger": "#FFD700",
    "clear": "#00AA00"
}

STATUS_LABELS = {
    "missile_alert": "Ракетная тревога",
    "missile_danger": "Ракетная опасность",
    "drone_attack": "Атака БПЛА",
    "drone_danger": "Опасность по БПЛА",
    "clear": "Отбой"
}

# ---------- СПРАВОЧНИК РЕГИОНОВ ----------
REGION_ALIASES = {
    "Московская область": "Московская область",
    "Московский регион": "Московская область",
    "Москва": "Москва",
    "Тульская область": "Тульская область",
    "Калужская область": "Калужская область",
    "Рязанская область": "Рязанская область",
    "Тверская область": "Тверская область",
    "Воронежская область": "Воронежская область",
    "Белгородская область": "Белгородская область",
    "Брянская область": "Брянская область",
    "Курская область": "Курская область",
    "Ростовская область": "Ростовская область",
    "Смоленская область": "Смоленская область",
    "Орловская область": "Орловская область",
    "Липецкая область": "Липецкая область",
    "Тамбовская область": "Тамбовская область",
    "Владимирская область": "Владимирская область",
    "Ивановская область": "Ивановская область",
    "Нижегородская область": "Нижегородская область",
    "Пензенская область": "Пензенская область",
    "Ульяновская область": "Ульяновская область",
    "Саратовская область": "Саратовская область",
    "Вологодская область": "Вологодская область",
    "Ставропольский край": "Ставропольский край",
    "Краснодарский край": "Краснодарский край",
    "Пермский край": "Пермский край",
    "Республика Крым": "Республика Крым",
    "Республика Адыгея": "Республика Адыгея",
    "Чеченская Республика": "Чеченская Республика",
    "Республика Дагестан": "Республика Дагестан",
    "Республика Ингушетия": "Республика Ингушетия",
    "Республика Северная Осетия": "Республика Северная Осетия",
    "Кабардино-Балкарская Республика": "Кабардино-Балкарская Республика",
    "Карачаево-Черкесская Республика": "Карачаево-Черкесская Республика",
}

# ---------- ХРАНИЛИЩА ----------
region_statuses = {}
alert_history = []

# ---------- ФУНКЦИИ ПАРСИНГА ----------

def is_ad_message(text):
    return "❗️Радар по всей России" not in text

def is_superseded_by_later(text):
    if re.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", text, re.IGNORECASE):
        return True
    return False

def extract_regions(text):
    found_regions = set()
    for alias, normalized in REGION_ALIASES.items():
        if alias in text:
            found_regions.add(normalized)
    return list(found_regions)

def detect_status(text):
    text_lower = text.lower()
    
    # Ракетная тревога (высший приоритет)
    if "ракетная тревога" in text_lower:
        return "missile_alert"
    
    # Ракетная опасность
    if "ракетная опасность" in text_lower or "ракетной опасности" in text_lower:
        return "missile_danger"
    
    # Атака БПЛА (фиксации/сбития/работа ПВО)
    if any(word in text_lower for word in [
        "работа пво", "сбитие", "сбития", "фиксация бпла",
        "фиксации бпла", "фиксация от", "фиксация групп",
        "в небе", "приготовиться к сбитию",
        "продолжается работа пво", "еще фиксации",
        "фиксации групп бпла"
    ]):
        return "drone_attack"
    
    # Опасность по БПЛА / внимание
    if any(word in text_lower for word in [
        "опасность по бпла", "тревога по бпла", "угроза атаки",
        "приготовиться к очередной волне", "сохраняется",
        "срочно принять меры безопасности", "внимание",
        "опасность по бпла и ракетной опасности"
    ]):
        return "drone_danger"
    
    # Отбой
    if "отбой опасности" in text_lower or "отбой по бпла" in text_lower:
        if "опасность сохраняется" in text_lower:
            return "drone_danger"
        return "clear"
    
    return None

def clean_old_history():
    global alert_history
    cutoff = datetime.utcnow() - timedelta(hours=24)
    alert_history = [a for a in alert_history if datetime.fromisoformat(a["timestamp"]) > cutoff]

# ---------- ОБРАБОТЧИК СООБЩЕНИЙ ----------
async def process_message(event):
    text = event.message.text
    if not text or is_ad_message(text) or is_superseded_by_later(text):
        return
    
    regions = extract_regions(text)
    if not regions:
        return
    
    status = detect_status(text)
    if status is None:
        return
    
    now = datetime.utcnow()
    now_iso = now.isoformat() + "Z"
    
    for region in regions:
        current = region_statuses.get(region, {}).get("status")
        if current is not None and STATUS_PRIORITY.get(status, 99) >= STATUS_PRIORITY.get(current, 99):
            continue
        
        region_statuses[region] = {
            "status": status,
            "last_update": now_iso,
            "message": text[:200] + ("..." if len(text) > 200 else "")
        }
        
        alert_history.append({
            "region": region,
            "status": status,
            "timestamp": now_iso
        })
        
        print(f"[{now_iso}] {region} -> {status}")
    
    clean_old_history()

# ---------- КЛИЕНТ TELEGRAM ----------
client = TelegramClient("session", API_ID, API_HASH)

@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def handler(event):
    await process_message(event)

# ---------- API ----------
@app.route("/api/statuses")
def get_statuses():
    """Отдаёт текущие статусы + историю за час для каждого региона"""
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = {"regions": {}, "last_updated": datetime.utcnow().isoformat() + "Z"}
    
    for region, data in region_statuses.items():
        count = sum(1 for a in alert_history 
                    if a["region"] == region 
                    and datetime.fromisoformat(a["timestamp"]) > hour_ago)
        result["regions"][region] = {
            **data,
            "alerts_last_hour": count
        }
    
    return jsonify(result)

@app.route("/")
def index():
    return "Парсер запущен. Данные: /api/statuses"

# ---------- ПУШ В GITHUB ----------
def push_to_github():
    """Обновляет data/statuses.json в репозитории GitHub Pages"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Собираем данные для сохранения
    export_data = {
        "regions": region_statuses,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "history": alert_history[-1000:]  # Последние 1000 записей
    }
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    content_bytes = content.encode("utf-8")
    content_b64 = base64.b64encode(content_bytes).decode("utf-8")
    
    # Пробуем получить текущий SHA файла
    try:
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha") if resp.status_code == 200 else None
    except:
        sha = None
    
    # Пушим файл
    data = {
        "message": f"Update statuses {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content_b64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
    
    try:
        resp = requests.put(url, headers=headers, json=data)
        if resp.status_code in [200, 201]:
            print("✅ Статусы обновлены в GitHub Pages")
        else:
            print(f"❌ Ошибка обновления GitHub: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def periodic_push():
    """Пушит данные каждые 30 секунд"""
    while True:
        time.sleep(30)
        if region_statuses:  # Только если есть данные
            push_to_github()

# ---------- KEEP-ALIVE ----------
def keep_alive():
    port = 5000
    url = f"http://localhost:{port}/api/statuses"
    while True:
        time.sleep(300)
        try:
            resp = requests.get(url, timeout=10)
            print(f"Keep-alive: {resp.status_code}")
        except Exception as e:
            print(f"Keep-alive failed: {e}")

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=periodic_push, daemon=True).start()
    
    with client:
        print("Telegram клиент запущен, слушаю канал @radarrussiia...")
        app.run(host="0.0.0.0", port=5000)
