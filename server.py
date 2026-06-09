import os as O, re as R, json as J, threading as T, time as I, requests as Q, asyncio as A
import hashlib as HL, secrets as SC, base64 as B
from functools import wraps as WR
from datetime import datetime as D, timedelta as TD, timezone as TZ
from flask import Flask as F, jsonify as Jf, request as QR, render_template_string as RTS
from telethon import TelegramClient as TC
from telethon.sessions import StringSession as SS
from telethon.errors import FloodWaitError as FWE
import sys as _sys

_ = F(__name__)

@_.after_request
def _1(_2):
    _2.headers["Access-Control-Allow-Origin"] = "*"
    _2.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    _2.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return _2

@_.route("/admin", methods=["OPTIONS"])
@_.route("/admin/<path:path>", methods=["OPTIONS"])
def _3(path=None):
    return "", 200

_4 = int(O.environ.get("API_ID", 0))
_5 = O.environ.get("API_HASH", "")
_6 = O.environ.get("SESSION_STRING", "")
_7 = O.environ.get("GITHUB_TOKEN", "")
_8 = O.environ.get("GITHUB_REPO", "")
_9 = O.environ.get("CHANNEL_USERNAME", "radarrussiia")
_10 = O.environ.get("DPR_CHANNEL", "DPR_channel")
_11 = O.environ.get("REPORT_CHANNEL", "RadarMapRf")
_12 = int(O.environ.get("STATUS_EXPIRY_HOURS", 12))

ADMIN_PASSWORD = O.environ.get("ADMIN_PASSWORD", "admin123")
ADMIN_TOKENS = {}
BLOCKED_IPS = {}
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 3
BLOCK_DURATION = TD(hours=24)
TOKEN_EXPIRY = TD(hours=12)
MANUAL_STATUS_SOURCE = "admin_panel"

ADMIN_CHANGES = []
SNAPSHOT_BEFORE_ADMIN = {}
_ADMIN_CHANGE_ID = 0

# API Key system
API_KEYS = {}
API_APPLICATIONS = []
_API_APP_ID = 0
API_KEY_EXPIRY_DAYS = 30

_13 = {"missile_alert":0, "missile_danger":1, "drone_attack":2, "drone_danger":3, "clear":4}

_14 = {"Московская область":"Московская обл.","Москва":"Москва","Ленинградская область":"Ленинградская обл.","Санкт-Петербург":"Санкт-Петербург","Нижегородская область":"Нижегородская обл.","Ставропольский край":"Ставропольский край","Краснодарский край":"Краснодарский край","Чеченская Республика":"Чеченская Респ.","Республика Дагестан":"Респ. Дагестан","Республика Ингушетия":"Респ. Ингушетия","Республика Северная Осетия":"Респ. Сев. Осетия","Карачаево-Черкесская Республика":"Карачаево-Черкесия","Кабардино-Балкарская Республика":"Кабардино-Балкария","Республика Адыгея":"Респ. Адыгея","Республика Крым":"Респ. Крым","Запорожская область":"Запорожская обл.","Херсонская область":"Херсонская обл.","Донецкая Народная Республика":"ДНР","Луганская Народная Республика":"ЛНР","Астраханская область":"Астраханская обл.","Волгоградская область":"Волгоградская обл.","Белгородская область":"Белгородская обл.","Брянская область":"Брянская обл.","Воронежская область":"Воронежская обл.","Курская область":"Курская обл.","Ростовская область":"Ростовская обл.","Смоленская область":"Смоленская обл.","Тульская область":"Тульская обл.","Калужская область":"Калужская обл.","Рязанская область":"Рязанская обл.","Тверская область":"Тверская обл.","Ярославская область":"Ярославская обл.","Владимирская область":"Владимирская обл.","Ивановская область":"Ивановская обл.","Костромская область":"Костромская обл.","Тамбовская область":"Тамбовская обл.","Липецкая область":"Липецкая обл.","Орловская область":"Орловская обл.","Пензенская область":"Пензенская обл.","Саратовская область":"Саратовская обл.","Ульяновская область":"Ульяновская обл.","Самарская область":"Самарская обл.","Пермский край":"Пермский край","Республика Башкортостан":"Респ. Башкортостан","Республика Татарстан":"Респ. Татарстан","Республика Удмуртия":"Респ. Удмуртия","Республика Марий Эл":"Респ. Марий Эл","Республика Мордовия":"Респ. Мордовия","Чувашская Республика":"Чувашская Респ.","Кировская область":"Кировская обл.","Оренбургская область":"Оренбургская обл.","Челябинская область":"Челябинская обл.","Свердловская область":"Свердловская обл.","Курганская область":"Курганская обл.","Тюменская область":"Тюменская обл.","Омская область":"Омская обл.","Новосибирская область":"Новосибирская обл.","Томская область":"Томская обл.","Кемеровская область":"Кемеровская обл.","Алтайский край":"Алтайский край","Красноярский край":"Красноярский край","Иркутская область":"Иркутская обл.","Забайкальский край":"Забайкальский край","Республика Бурятия":"Респ. Бурятия","Приморский край":"Приморский край","Хабаровский край":"Хабаровский край","Амурская область":"Амурская обл.","Сахалинская область":"Сахалинская обл.","Камчатский край":"Камчатский край","Магаданская область":"Магаданская обл.","Республика Саха (Якутия)":"Респ. Саха (Якутия)","Еврейская АО":"Еврейская АО","Чукотский АО":"Чукотский АО","ЯНАО":"ЯНАО","Ханты-Мансийский АО":"ХМАО","Ненецкий АО":"Ненецкий АО","Республика Карелия":"Респ. Карелия","Республика Коми":"Респ. Коми","Архангельская область":"Архангельская обл.","Мурманская область":"Мурманская обл.","Вологодская область":"Вологодская обл.","Новгородская область":"Новгородская обл.","Псковская область":"Псковская обл.","Калининградская область":"Калининградская обл.","Республика Алтай":"Респ. Алтай","Республика Хакасия":"Респ. Хакасия","Республика Тыва":"Респ. Тыва","Республика Калмыкия":"Респ. Калмыкия"}

_15 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
_16 = {}
_17 = []
_18 = 0
_19 = 0
_20 = "/tmp/radar_state.json"
_21 = None

_22 = {"костромской":"Костромская область","кировской":"Кировская область","московской":"Московская область","ленинградской":"Ленинградская область","нижегородской":"Нижегородская область","тульской":"Тульская область","калужской":"Калужская область","рязанской":"Рязанская область","тверской":"Тверская область","воронежской":"Воронежская область","белгородской":"Белгородская область","брянской":"Брянская область","курской":"Курская область","смоленской":"Смоленская область","орловской":"Орловская область","липецкой":"Липецкая область","тамбовской":"Тамбовская область","владимирской":"Владимирская область","ивановской":"Ивановская область","ярославской":"Ярославская область","вологодской":"Вологодская область","новгородской":"Новгородская область","псковской":"Псковская область","калининградской":"Калининградская область","пензенской":"Пензенская область","ульяновской":"Ульяновская область","саратовской":"Саратовская область","самарской":"Самарская область","оренбургской":"Оренбургская область","челябинской":"Челябинская область","свердловской":"Свердловская область","курганской":"Курганская область","тюменской":"Тюменская область","омской":"Омская область","томской":"Томская область","новосибирской":"Новосибирская область","кемеровской":"Кемеровская область","иркутской":"Иркутская область","амурской":"Амурская область","сахалинской":"Сахалинская область","магаданской":"Магаданская область","мурманской":"Мурманская область","архангельской":"Архангельская область","астраханской":"Астраханская область","волгоградской":"Волгоградская область","ростовской":"Ростовская область","запорожской":"Запорожская область","херсонской":"Херсонская область"}

_23 = {
    "Московская область":"Московская область","Московский регион":"Московская область","Подмосковье":"Московская область","Москва":"Москва","г. Москва":"Москва",
    "Тульская область":"Тульская область","Тула":"Тульская область","Калужская область":"Калужская область","Калуга":"Калужская область",
    "Рязанская область":"Рязанская область","Рязань":"Рязанская область","Тверская область":"Тверская область","Тверь":"Тверская область",
    "Воронежская область":"Воронежская область","Воронеж":"Воронежская область","Белгородская область":"Белгородская область","Белгород":"Белгородская область",
    "Брянская область":"Брянская область","Брянск":"Брянская область","Курская область":"Курская область","Курск":"Курская область",
    "Смоленская область":"Смоленская область","Смоленск":"Смоленская область","Орловская область":"Орловская область","Орёл":"Орловская область","Орел":"Орловская область",
    "Липецкая область":"Липецкая область","Липецк":"Липецкая область","Тамбовская область":"Тамбовская область","Тамбов":"Тамбовская область",
    "Владимирская область":"Владимирская область","Владимир":"Владимирская область","Ивановская область":"Ивановская область","Иваново":"Ивановская область",
    "Ярославская область":"Ярославская область","Ярославль":"Ярославская область","Костромская область":"Костромская область","Кострома":"Костромская область",
    "г. Санкт-Петербург":"Ленинградская область","Санкт-Петербург":"Ленинградская область","Ленинградская область":"Ленинградская область",
    "Республика Карелия":"Республика Карелия","Архангельская область":"Архангельская область","Республика Коми":"Республика Коми","Ненецкий АО":"Ненецкий АО",
    "Вологодская область":"Вологодская область","Вологда":"Вологодская область","Новгородская область":"Новгородская область","Псковская область":"Псковская область","Псков":"Псковская область",
    "Нижегородская область":"Нижегородская область","Нижний Новгород":"Нижегородская область","Кировская область":"Кировская область","Киров":"Кировская область",
    "Пензенская область":"Пензенская область","Пенза":"Пензенская область","Ульяновская область":"Ульяновская область","Ульяновск":"Ульяновская область",
    "Саратовская область":"Саратовская область","Саратов":"Саратовская область","Пермский край":"Пермский край","Пермь":"Пермский край","г.Пермь":"Пермский край","Пермский район":"Пермский край",
    "Республика Удмуртия":"Республика Удмуртия","Республика Башкортостан":"Республика Башкортостан","Башкортостан":"Республика Башкортостан",
    "Оренбургская область":"Оренбургская область","Самарская область":"Самарская область","Чувашская Республика":"Чувашская Республика","Чувашия":"Чувашская Республика",
    "Республика Татарстан":"Республика Татарстан","Татарстан":"Республика Татарстан","Республика Марий Эл":"Республика Марий Эл","Марий Эл":"Республика Марий Эл",
    "Республика Мордовия":"Республика Мордовия","Мордовия":"Республика Мордовия","Ставропольский край":"Ставропольский край","Ставрополь":"Ставропольский край","Невинномысск":"Ставропольский край",
    "Краснодарский край":"Краснодарский край","Краснодар":"Краснодарский край","Причерноморье":"Краснодарский край","Сочи":"Краснодарский край","Анапа":"Краснодарский край","Новороссийск":"Краснодарский край","Приморско-Ахтарск":"Краснодарский край",
    "Ростовская область":"Ростовская область","Волгоградская область":"Волгоградская область","Волгоград":"Волгоградская область","Астраханская область":"Астраханская область","Астрахань":"Астраханская область",
    "Республика Крым":"Республика Крым","Крым":"Республика Крым","Побережье Крыма":"Республика Крым","Крымский мост":"Республика Крым","Севастополь":"Республика Крым","Симферополь":"Республика Крым",
    "Республика Адыгея":"Республика Адыгея","Адыгея":"Республика Адыгея","Республика Калмыкия":"Республика Калмыкия",
    "Чеченская Республика":"Чеченская Республика","Грозный":"Чеченская Республика","Республика Дагестан":"Республика Дагестан","Дагестан":"Республика Дагестан","Махачкала":"Республика Дагестан","Каспийск":"Республика Дагестан",
    "Республика Ингушетия":"Республика Ингушетия","Республика Северная Осетия":"Республика Северная Осетия","Владикавказ":"Республика Северная Осетия",
    "Кабардино-Балкарская Республика":"Кабардино-Балкарская Республика","Карачаево-Черкесская Республика":"Карачаево-Черкесская Республика",
    "Челябинская область":"Челябинская область","Челябинск":"Челябинская область","Свердловская область":"Свердловская область","Екатеринбург":"Свердловская область",
    "Курганская область":"Курганская область","ЯНАО":"ЯНАО","Ямало-Ненецкий АО":"ЯНАО","Ханты-Мансийский АО - Югра":"Ханты-Мансийский АО",
    "Тюменская область":"Тюменская область","Омская область":"Омская область","Томская область":"Томская область","Новосибирская область":"Новосибирская область",
    "Алтайский край":"Алтайский край","Кемеровская область":"Кемеровская область","Республика Алтай":"Республика Алтай","Республика Хакасия":"Республика Хакасия",
    "Республика Тыва":"Республика Тыва","Красноярский край":"Красноярский край","Республика Бурятия":"Республика Бурятия","Иркутская область":"Иркутская область",
    "Забайкальский край":"Забайкальский край","Амурская область":"Амурская область","Республика Саха (Якутия)":"Республика Саха (Якутия)","Еврейская АО":"Еврейская АО",
    "Приморский край":"Приморский край","Хабаровский край":"Хабаровский край","Сахалинская область":"Сахалинская область","Магаданская область":"Магаданская область",
    "Камчатский край":"Камчатский край","Чукотский АО":"Чукотский АО","Донецкая Народная Республика":"Донецкая Народная Республика",
    "Луганская Народная Республика":"Луганская Народная Республика","Запорожская область":"Запорожская область","Херсонская область":"Херсонская область",
    "Губаха":"Пермский край"
}

_24 = {
    "Москва", "Тула", "Калуга", "Рязань", "Тверь", "Воронеж", "Белгород",
    "Брянск", "Курск", "Смоленск", "Орёл", "Орел", "Липецк", "Тамбов",
    "Владимир", "Иваново", "Ярославль", "Кострома", "Вологда", "Псков",
    "Киров", "Пенза", "Ульяновск", "Саратов", "Пермь", "Ставрополь",
    "Краснодар", "Волгоград", "Астрахань", "Севастополь", "Симферополь",
    "Грозный", "Махачкала", "Каспийск", "Владикавказ", "Челябинск",
    "Екатеринбург", "Крым", "Адыгея", "Татарстан", "Чувашия", "Мордовия",
    "Башкортостан", "Невинномысск", "Анапа", "Сочи", "Новороссийск",
    "Дагестан", "Марий Эл", "Иваново", "Тверь",
    "Московский регион", "Подмосковье", "Нижний Новгород", "Санкт-Петербург",
    "Причерноморье", "Побережье Крыма", "Крымский мост", "Приморско-Ахтарск",
    "г. Москва", "г. Санкт-Петербург", "г.Пермь",
}

_25 = ["Донецкая Народная Республика","Луганская Народная Республика","Запорожская область","Херсонская область"]

def _26(msg):
    print(f"[RADAR_DEBUG {D.now(TZ.utc).strftime('%H:%M:%S')}] {msg}", file=_sys.stderr, flush=True)

def _280(msg):
    if not msg: return msg
    if msg.rstrip().endswith("@olegmmg"): return msg
    return msg + " @olegmmg"

def get_effective_status(statuses):
    if not statuses: return "clear"
    for st in ["missile_alert", "missile_danger", "drone_attack", "drone_danger"]:
        if statuses.get(st): return st
    return "clear"

def _27():
    global _16, _15
    _28 = D.now(TZ.utc)
    _29 = _28 - TD(hours=_12)
    _30 = 0
    _31 = False
    for _32, _33 in list(_16.items()):
        _34 = _33.get("last_update")
        if not _34: continue
        try:
            _35 = D.fromisoformat(_34)
            if _35.tzinfo is None: _35 = _35.replace(tzinfo=TZ.utc)
            if _35 < _29 and get_effective_status(_33.get("statuses", {})) != "clear":
                for s in _16[_32].get("statuses", {}): _16[_32]["statuses"][s] = False
                _16[_32]["last_update"] = _28.isoformat()
                _16[_32]["message"] = _280(f"Автоматический отбой (нет обновлений >{_12}ч)")
                _16[_32]["source"] = _33.get("source","system")
                _30 += 1
                _31 = True
        except: pass
    if _30 > 0:
        _15 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _36()
    return _31

def _48():
    """Синхронизация ключей API с GitHub (регионы остаются локальными)"""
    global API_KEYS, API_APPLICATIONS, _API_APP_ID
    if not _7 or not _8: return
    try:
        _291 = "data/api_state.json"
        _293 = f"https://api.github.com/repos/{_8}/contents/{_291}"
        _294 = {"Authorization": f"token {_7}"}
        _295 = Q.get(_293, headers=_294)
        if _295.status_code == 200:
            _296 = _295.json()
            _297 = B.b64decode(_296["content"]).decode()
            _298 = J.loads(_297)
            API_KEYS = _298.get("api_keys", API_KEYS)
            API_APPLICATIONS = _298.get("api_applications", API_APPLICATIONS)
            _API_APP_ID = _298.get("api_app_id", _API_APP_ID)
            _26("✅ Ключи API синхронизированы с GitHub")
    except Exception as e:
        _26(f"GitHub key sync error: {e}")

def _37(_38, _39="system"):
    global _16, _15
    _40 = D.now(TZ.utc).isoformat()
    _41 = 0
    _42 = {"drone_danger":"опасность БПЛА","missile_danger":"ракетная опасность","missile_alert":"ракетная тревога","drone_attack":"атака БПЛА"}
    for _43, _44 in list(_16.items()):
        if _44.get("statuses", {}).get(_38):
            _16[_43]["statuses"][_38] = False
            _16[_43]["last_update"] = _40
            _16[_43]["message"] = _280(f"Отбой {_42.get(_38, _38)} по всем регионам")
            _16[_43]["source"] = _39
            _41 += 1
    if _41 > 0:
        _15 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _36()
    return _41 > 0
    
def _290():
    if not _7 or not _8:
        _26(f"GitHub API sync skipped: token={'yes' if _7 else 'no'}, repo={'yes' if _8 else 'no'}")
        return
    try:
        _291 = "data/api_state.json"
        _292 = J.dumps({
            "api_keys": API_KEYS,
            "api_applications": API_APPLICATIONS[-200:],
            "api_app_id": _API_APP_ID
        }, ensure_ascii=False, default=str)
        _293 = f"https://api.github.com/repos/{_8}/contents/{_291}"
        _294 = {"Authorization": f"token {_7}"}
        _295 = Q.get(_293, headers=_294)
        _26(f"GitHub Keys GET: {_295.status_code}")
        _296 = None
        if _295.status_code == 200:
            _296 = _295.json().get("sha")
        _297 = {
            "message": f"Auto save API keys {D.now(TZ.utc).isoformat()}",
            "content": B.b64encode(_292.encode()).decode(),
            "branch": "main"
        }
        if _296: _297["sha"] = _296
        _298 = Q.put(_293, headers=_294, json=_297)
        _26(f"GitHub Keys PUT: {_298.status_code} - {_298.text[:200]}")
    except Exception as e:
        import traceback
        _26(f"GitHub key save error: {traceback.format_exc()}")

def _36():
    try:
        _45 = {
            "saved_at": D.now(TZ.utc).isoformat(),
            "region_statuses": _16,
            "alert_history": _17[-5000:],
            "last_msg_id_main": _18,
            "last_msg_id_dpr": _19,
            "last_summary": _15,
            "admin_changes": ADMIN_CHANGES[-200:],
            "snapshot_before_admin": SNAPSHOT_BEFORE_ADMIN,
            "admin_change_id": _ADMIN_CHANGE_ID,
            "api_keys": API_KEYS,
            "api_applications": API_APPLICATIONS[-200:],
            "api_app_id": _API_APP_ID
        }
        with open(_20, "w", encoding="utf-8") as _46:
            J.dump(_45, _46, ensure_ascii=False, default=str)
        _290()
    except Exception as e:
        _26(f"Local save error: {e}")

def _47():
    global _16, _17, _18, _19, _15, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN, _ADMIN_CHANGE_ID, API_KEYS, API_APPLICATIONS, _API_APP_ID
    try:
        if O.path.exists(_20):
            with open(_20, "r", encoding="utf-8") as _f: _49 = J.load(_f)
            _16 = _49.get("region_statuses", {})
            for r, data in _16.items():
                if "statuses" not in data:
                    old_status = data.get("status", "clear")
                    data["statuses"] = {"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False}
                    if old_status in data["statuses"]:
                        data["statuses"][old_status] = True
            _17 = _49.get("alert_history", [])
            _18 = _49.get("last_msg_id_main", 0)
            _19 = _49.get("last_msg_id_dpr", 0)
            _15 = _49.get("last_summary", {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None})
            ADMIN_CHANGES = _49.get("admin_changes", [])
            SNAPSHOT_BEFORE_ADMIN = _49.get("snapshot_before_admin", {})
            _ADMIN_CHANGE_ID = _49.get("admin_change_id", 0)
            API_KEYS = _49.get("api_keys", {})
            API_APPLICATIONS = _49.get("api_applications", [])
            _API_APP_ID = _49.get("api_app_id", 0)
            _26("✅ Локальное состояние загружено")
        
        # Загружаем ключи с GitHub в любом случае
        _48()
    except Exception as e:
        _26(f"Load error: {e}")

def _50(_51): return _14.get(_51, _51)

def _52(_53):
    _54, _55, _56, _57 = [], [], [], []
    for _58, _59 in _53.items():
        eff = get_effective_status(_59.get("statuses", {}))
        if eff == "clear": continue
        _61 = _50(_58)
        if eff == "drone_danger": _54.append(f"    • {_61}")
        elif eff == "drone_attack": _55.append(f"    • {_61}")
        elif eff == "missile_danger": _56.append(f"    • {_61}")
        elif eff == "missile_alert": _57.append(f"    • {_61}")
    _54.sort(); _55.sort(); _56.sort(); _57.sort()
    global _15
    _62 = {"drone_danger":_54,"drone_attack":_55,"missile_danger":_56,"missile_alert":_57}
    if _15.get("drone_danger") == _54 and _15.get("drone_attack") == _55 and _15.get("missile_danger") == _56 and _15.get("missile_alert") == _57: return None
    _15 = _62
    _15["timestamp"] = D.now(TZ.utc)
    _63 = D.now(TZ.utc) + TD(hours=3)
    _64 = _63.strftime("%H:%M | %d/%m")
    _65 = f"✈️ *Воздушная тревога* 🚀\n`{_64}`\n\n"
    _66 = []
    _66.extend(_57); _66.extend(_56); _66.extend(_55)
    _65 += "🔴 *АКТИВНАЯ ТРЕВОГА*\n"
    _65 += "\n".join(_66) + "\n\n" if _66 else "    • Отсутствует\n\n"
    _65 += "🟡 *ПОТЕНЦИАЛЬНАЯ ОПАСНОСТЬ*\n"
    _65 += "\n".join(_54) + "\n\n" if _54 else "    • Отсутствует\n\n"
    _65 += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"
    return _65

async def _67(_68, _69=False):
    if not _16: return
    _70 = _52(_16)
    if _70 is None and not _69: return
    if _70 is None and _69:
        if _15 and _15.get("timestamp"):
            _71 = D.now(TZ.utc) + TD(hours=3)
            _72 = _71.strftime("%H:%M | %d/%m")
            _70 = f"✈️ *Воздушная тревога* 🚀\n`{_72}`\n\n"
            _73 = []
            _73.extend(_15.get("missile_alert", [])); _73.extend(_15.get("missile_danger", [])); _73.extend(_15.get("drone_attack", []))
            _70 += "🔴 *АКТИВНАЯ ТРЕВОГА*\n"
            _70 += "\n".join(_73) + "\n\n" if _73 else "    • Отсутствует\n\n"
            _70 += "🟡 *ПОТЕНЦИАЛЬНАЯ ОПАСНОСТЬ*\n"
            _70 += "\n".join(_15.get("drone_danger", [])) + "\n\n" if _15.get("drone_danger", []) else "    • Отсутствует\n\n"
            _70 += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"
        else: return
    try:
        _74 = await _68.get_entity(_11)
        await _68.send_message(_74, _70, link_preview=False)
    except FWE as _75: await A.sleep(_75.seconds)
    except: pass

def _76(_77):
    if not _77: return ''
    _78 = [_77]
    for _79 in [r'❗️Радар по всей России\s*-\s*@radarrussiia\s*\n?', r'🌐 Обход белых списков\s*-\s*@Internet_Boost_bot\s*\([^)]+\)\s*\n?', r'@radarrussiia\s*\n?', r'@Internet_Boost_bot\s*\n?', r'https?://t\.me/Internet_Boost_bot\S*\s*\n?', r'Радар по всей России.*?\n?', r'Обход белых списков.*?\n?', r'🔴 Радар ДНР.*?\n?', r'📢 Оповещения Радар ДНР:\s*']:
        _78 = [R.sub(_79, '', _80, flags=R.IGNORECASE|R.MULTILINE) for _80 in _78]
    return R.sub(r'\n\s*\n', '\n', _78[0]).strip()

def _81(_82):
    if not _82: return False
    if "Радар ДНР" in _82: return False
    _83 = ["❗️ВНИМАНИЕ","Враг планирует", "БЕЗ МОБИЛЬНОЙ", "за прошедшую", "Впервые регионы РФ подверглись массовым РАКЕТНЫМ атакам","создать телеграм каналы для оповещения граждан","Ищите свой регион и подписывайтесь","НЕ БУДУТ БЛОКИРОВАТЬ","Нет вашего региона","вакансия без опыта","Пятёрочка ищет людей","платят от","АВАНС","Удалять негативные отзывы","Ставить лайки под роликами","Сравнивать цены","24/7 (https://t.me/","Москва 24/7","Питер 24/7","Подписывайтесь","будет автоматически выдан АВАНС"]
    for _84 in _83:
        if _84.upper() in _82.upper(): return True
    if len(R.findall(r'https?://t\.me/', _82)) > 3: return True
    _85 = _76(_82)
    return not _85 or len(_85) < 15

def _86(_87): return bool(R.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", _87, R.IGNORECASE))

def _88(_89, _90):
    _91 = _89.lower()
    _92 = _90.lower()
    try:
        pattern = r'\b' + R.escape(_91) + r'\b'
        return bool(R.search(pattern, _92))
    except:
        return _91 in _92

def _93(_94):
    _95 = _94.lower()
    _96 = set()
    _97 = set()
    for _98, _99 in _23.items():
        if _88(_98, _94):
            if _99 not in _97:
                _96.add(_99)
                _97.add(_99)
    _100 = R.findall(r'(?:г\.|город|города)\s*([А-Яа-яёЁ-]+)', _95)
    for _101 in _100:
        for _102, _103 in _23.items():
            if _101.lower() == _102.lower():
                if _103 not in _97:
                    _96.add(_103)
                    _97.add(_103)
                    break
    _104 = R.findall(r'([А-Яа-яёЁ-]+)\s+район', _95)
    for _105 in _104:
        _106 = _105.lower()
        for _107, _108 in _23.items():
            if _107.lower().startswith(_106) and "район" in _107.lower():
                if _108 not in _97:
                    _96.add(_108)
                    _97.add(_108)
                    break
    _109 = R.findall(r'([А-Яа-яёЁ]+(?:ской|ской))\s+области', _95)
    for _110 in _109:
        _111 = _110.lower()
        if _111 in _22:
            _112 = _22[_111]
            if _112 not in _97:
                _96.add(_112)
                _97.add(_112)
    _113 = R.findall(r'([А-Яа-яёЁ]+(?:ская|ская))\s+область', _95)
    for _114 in _113:
        for _98, _99 in _23.items():
            if R.search(r'\b' + R.escape(_114.lower()) + r'\b', _98.lower()) and _99 not in _97:
                _96.add(_99)
                _97.add(_99)
                break
    _115 = R.findall(r'([А-Яа-яёЁ]+(?:ский|ский))\s+край', _95)
    for _116 in _115:
        for _98, _99 in _23.items():
            if R.search(r'\b' + R.escape(_116.lower()) + r'\b', _98.lower()) and _99 not in _97:
                _96.add(_99)
                _97.add(_99)
                break
    _117 = R.findall(r'(?:республика|республики)\s+([А-Яа-яёЁ][а-яёЁ]+(?:ская|ская)?)', _95)
    for _118 in _117:
        for _98, _99 in _23.items():
            if _118 in _98.lower() or _118 in _99.lower():
                if _99 not in _97:
                    _96.add(_99)
                    _97.add(_99)
                    break
    for _119 in ["башкортостан","чувашия","татарстан","удмуртия","марий эл","мордовия","карелия","коми","адыгея","калмыкия","алтай","хакасия","тыва","бурятия","саха"]:
        if R.search(r'\b' + R.escape(_119) + r'\b', _95):
            for _98, _99 in _23.items():
                if _119 in _98.lower() or _119 in _99.lower():
                    if _99 not in _97:
                        _96.add(_99)
                        _97.add(_99)
                        break
    if "Донецкая Народная Республика" not in _97 and R.search(r'\b(днр|dnr|донецк|горловка|макеевка|енакиево)\b', _95):
        _96.add("Донецкая Народная Республика")
    if "Луганская Народная Республика" not in _97 and R.search(r'\b(лнр|lnr|луганск|алчевск|брянка)\b', _95):
        _96.add("Луганская Народная Республика")
    if "Запорожская область" not in _97 and R.search(r'запорожск|zaporizh', _95):
        _96.add("Запорожская область")
    if "Херсонская область" not in _97 and R.search(r'херсон|kherson', _95):
        _96.add("Херсонская область")
    return list(_96)

def _120(_121):
    _122 = _121.lower()
    if "отбой опасности бпла по всем ранее объявленным регионам" in _122: return "mass_clear_drone_danger"
    if "отбой ракетной опасности по всем ранее объявленным регионам" in _122: return "mass_clear_missile_danger"
    if "отбой ракетной тревоги по всем ранее объявленным регионам" in _122: return "mass_clear_missile_alert"
    if any(w in _122 for w in ["отбой","отбой опасности","отбой по бпла","отбой ракетной опасности","отбой авиационной","отбой фиксации","отбой по пкр","отбой по бэк","все спокойно","тихо","обстановка спокойная","угрозу атаки снимаем"]):
        return "clear"
    if "ложная цель" in _122: return None
    if any(w in _122 for w in ["ракетная тревога","ракетной тревоги","тревога по пкр","тревога по бэк","ракетно бомбовая опасность","авиационная ракетная","авиационная ракетная бомбовая опасность"]):
        return "missile_alert"
    if any(w in _122 for w in ["ракетная опасность","ракетной опасности","опасность по пкр","опасность по бэк"]):
        return "missile_danger"
    if any(w in _122 for w in ["работа пво","сбитие","сбития","фиксация бпла","фиксации бпла","группа бпла","меры безопасности","группы бпла","тревога по бпла","атака бпла","атакуют","много бпла","волна бпла","фиксация групп","идут сбития","массовый запуск","угроза атаки БПЛА","угроза атаки","угроза бпла"]):
        return "drone_attack"
    if any(w in _122 for w in ["опасность по бпла", "опасность сохраняем", "угроза атаки","внимание по бпла","опасность сохраняется","повторно","fpv","fpv-дронам","единичных бпла","внимание","опасность сохраняем"]):
        return "drone_danger"
    return None

def _123(_124, _125=None, _126="main", _127=None, _128=False):
    global _16, _17
    if not _124: return False
    if _126 == "main" and _81(_124): return False
    if _86(_124): return False
    _129 = _120(_124)
    if _129 and _129.startswith("mass_clear_"):
        _130 = False
        if _129 == "mass_clear_drone_danger": _130 = _37("drone_danger", _126)
        elif _129 == "mass_clear_missile_danger": _130 = _37("missile_danger", _126)
        elif _129 == "mass_clear_missile_alert": _130 = _37("missile_alert", _126)
        if _130 and not _128: _17.append({"region":"ВСЕ РЕГИОНЫ","status":"mass_clear","timestamp":D.now(TZ.utc).isoformat(),"message":_280(_124[:500]),"source":_126})
        return _130
    _131 = _93(_124)
    if not _131: return False
    if _126 == "dpr": _131 = [r for r in _131 if r in _25]
    if not _131: return False
    if not _129: return False
    _132 = _127.isoformat() if _127 and _127.tzinfo else D.now(TZ.utc).isoformat()
    _133 = _76(_124)
    _133 = _280(_133) if _133 else ""
    _134 = False
    for _135 in _131:
        if _135 not in _16 or "statuses" not in _16[_135]:
            _16[_135] = {"statuses": {"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False}, "last_update": _132, "message": "", "source": _126}
        
        if _129 == "clear":
            for s in _16[_135]["statuses"]: _16[_135]["statuses"][s] = False
        else:
            _16[_135]["statuses"][_129] = True
            
        _16[_135]["last_update"] = _132
        _16[_135]["message"] = _133
        _16[_135]["source"] = _126
        
        _17.append({"region":_135,"status":_129,"timestamp":_132,"message":_133,"source":_126})
        if len(_17) > 5000: _17.pop(0)
        _134 = True
        _137(_135, _129, _133, _126)
    return _134

def _138():
    global SNAPSHOT_BEFORE_ADMIN
    if SNAPSHOT_BEFORE_ADMIN: return
    SNAPSHOT_BEFORE_ADMIN = {}
    for _139, _140 in _16.items():
        SNAPSHOT_BEFORE_ADMIN[_139] = {
            "statuses": _140.get("statuses", {"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False}).copy(),
            "last_update": _140.get("last_update"),
            "message": _140.get("message", ""),
            "source": _140.get("source", "unknown")
        }

def _137(_141, _142, _143, _144):
    global SNAPSHOT_BEFORE_ADMIN, ADMIN_CHANGES
    if not SNAPSHOT_BEFORE_ADMIN: return
    _145 = set()
    for _146 in ADMIN_CHANGES:
        if _146["region"] != "ВСЕ РЕГИОНЫ": _145.add(_146["region"])
    if _141 not in _145:
        SNAPSHOT_BEFORE_ADMIN[_141] = {
            "statuses": {"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False},
            "last_update": D.now(TZ.utc).isoformat(),
            "message": _143 or "",
            "source": _144
        }
        if _141 in _16 and "statuses" in _16[_141]:
            SNAPSHOT_BEFORE_ADMIN[_141]["statuses"] = _16[_141]["statuses"].copy()

def _147(_148, _149, _150=None, _reason=None):
    global ADMIN_CHANGES, _ADMIN_CHANGE_ID
    _ADMIN_CHANGE_ID += 1
    ADMIN_CHANGES.append({
        "id": _ADMIN_CHANGE_ID,
        "region": _148,
        "status": _149,
        "previous_statuses": _150,
        "reason": _reason,
        "timestamp": D.now(TZ.utc).isoformat(),
        "source": MANUAL_STATUS_SOURCE,
        "rolled_back": False
    })
    if len(ADMIN_CHANGES) > 1000: ADMIN_CHANGES = ADMIN_CHANGES[-1000:]

def _151():
    global _21
    while True:
        I.sleep(600)
        try:
            _152 = _27()
            if _152 and _21:
                _153 = A.new_event_loop()
                A.set_event_loop(_153)
                _153.run_until_complete(_67(_21, True))
                _153.close()
        except: pass

def _154():
    ip = QR.remote_addr
    if ip in BLOCKED_IPS:
        if BLOCKED_IPS[ip] > D.now(TZ.utc): return True
        else:
            del BLOCKED_IPS[ip]
            if ip in LOGIN_ATTEMPTS: del LOGIN_ATTEMPTS[ip]
    return False

def _155(f):
    @WR(f)
    def _156(*args, **kwargs):
        _157 = QR.headers.get('Authorization', '')
        _158 = _157.replace('Bearer ', '')
        if not _158 or _158 not in ADMIN_TOKENS: return Jf({"error":"Unauthorized","message":"Требуется авторизация"}), 401
        if ADMIN_TOKENS[_158] < D.now(TZ.utc):
            del ADMIN_TOKENS[_158]
            return Jf({"error":"Token expired","message":"Токен истёк"}), 401
        ADMIN_TOKENS[_158] = D.now(TZ.utc) + TOKEN_EXPIRY
        return f(*args, **kwargs)
    return _156

def _159():
    _160 = D.now(TZ.utc)
    _161 = [t for t, exp in ADMIN_TOKENS.items() if exp < _160]
    for t in _161: del ADMIN_TOKENS[t]

@_.route("/admin/login", methods=["POST"])
def _162():
    ip = QR.remote_addr
    if _154():
        _163 = BLOCKED_IPS.get(ip)
        return Jf({"success":False,"error":"IP blocked","message":f"IP заблокирован до {_163.strftime('%H:%M %d.%m.%Y') if _163 else 'неизвестно'}","blocked_until":_163.isoformat() if _163 else None}), 403
    _164 = QR.get_json()
    _165 = _164.get("password","") if _164 else ""
    if not _165: return Jf({"success":False,"error":"No password"}), 400
    if _165 == ADMIN_PASSWORD:
        if ip in LOGIN_ATTEMPTS: del LOGIN_ATTEMPTS[ip]
        _166 = SC.token_hex(32)
        ADMIN_TOKENS[_166] = D.now(TZ.utc) + TOKEN_EXPIRY
        _159()
        return Jf({"success":True,"token":_166,"expires_at":(D.now(TZ.utc)+TOKEN_EXPIRY).isoformat()})
    else:
        LOGIN_ATTEMPTS[ip] = LOGIN_ATTEMPTS.get(ip,0) + 1
        if LOGIN_ATTEMPTS[ip] >= MAX_LOGIN_ATTEMPTS:
            BLOCKED_IPS[ip] = D.now(TZ.utc) + BLOCK_DURATION
            return Jf({"success":False,"error":"Too many attempts","message":"IP заблокирован на 24 часа","blocked_until":BLOCKED_IPS[ip].isoformat()}), 403
        return Jf({"success":False,"error":"Wrong password","attempts_left":MAX_LOGIN_ATTEMPTS-LOGIN_ATTEMPTS[ip]}), 401

@_.route("/admin/regions", methods=["GET"])
@_155
def _167():
    _168 = {}
    _169 = D.now(TZ.utc)
    _170 = _169 - TD(hours=24)
    for _171, _172 in _16.items():
        _173 = 0
        for _174 in reversed(_17[-5000:]):
            if _174["region"] == _171:
                try:
                    if D.fromisoformat(_174["timestamp"]) > _170: _173 += 1
                except: pass
        _168[_171] = {"status":get_effective_status(_172.get("statuses", {})),"statuses":_172.get("statuses", {}),"last_update":_172.get("last_update"),"message":_172.get("message",""),"alerts_last_hour":_173,"source":_172.get("source","unknown")}
    for _175 in _23.values():
        if _175 not in _168:
            _168[_175] = {"status":"clear","statuses":{"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False},"last_update":None,"message":"","alerts_last_hour":0,"source":"system"}
    _176 = {}
    for _177, _178 in _168.items():
        if _177 not in _176: _176[_177] = _178
    return Jf({"regions":_176,"last_updated":_169.isoformat(),"total_count":len(_176)})

@_.route("/admin/set_status", methods=["POST"])
@_155
def _179():
    global _16, _17, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    _180 = QR.get_json()
    if not _180: return Jf({"success":False,"error":"No data"}), 400
    _181 = _180.get("region","").strip()
    _182 = _180.get("status","").strip()
    _reason = _180.get("reason","")
    if not _181 or not _182: return Jf({"success":False,"error":"Region and status required"}), 400
    _183 = ["missile_alert","missile_danger","drone_attack","drone_danger","clear"]
    if _182 not in _183: return Jf({"success":False,"error":f"Invalid status"}), 400
    if not SNAPSHOT_BEFORE_ADMIN: _138()
    _184 = None
    for _185 in _16.keys():
        if _185.lower() == _181.lower():
            _184 = _185
            break
    if not _184:
        for _186, _187 in _23.items():
            if _187.lower() == _181.lower() or _186.lower() == _181.lower():
                _184 = _187
                break
    if not _184: _184 = _181
    if _184 not in _16 or "statuses" not in _16[_184]:
        _16[_184] = {"statuses": {"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False}, "last_update": D.now(TZ.utc).isoformat(), "message": "", "source": MANUAL_STATUS_SOURCE}
    
    _prev_statuses = _16[_184]["statuses"].copy()
    _188 = get_effective_status(_prev_statuses)
    _189 = D.now(TZ.utc)
    _default_msg = _280(_reason if _reason else "Статус изменён администратором")
    
    if _182 == "clear":
        for s in _16[_184]["statuses"]: _16[_184]["statuses"][s] = False
    else:
        _16[_184]["statuses"][_182] = True
        
    _16[_184]["last_update"] = _189.isoformat()
    _16[_184]["message"] = _default_msg
    _16[_184]["source"] = MANUAL_STATUS_SOURCE
    _17.append({"region":_184,"status":_182,"timestamp":_189.isoformat(),"message":_default_msg,"source":MANUAL_STATUS_SOURCE})
    if len(_17) > 5000: _17.pop(0)
    _147(_184, _182, _prev_statuses, _reason)
    _36()
    return Jf({"success":True,"region":_184,"status":_182,"previous_status":_188,"timestamp":_189.isoformat()})

@_.route("/admin/mass_clear", methods=["POST"])
@_155
def _191():
    global _16, _17, _15, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    _192 = QR.get_json()
    if not _192: return Jf({"success":False,"error":"No data"}), 400
    _193 = _192.get("status_type","").strip()
    _reason = _192.get("reason","")
    _194 = {"drone_danger":"опасность БПЛА","missile_danger":"ракетная опасность","missile_alert":"ракетная тревога"}
    if _193 not in _194: return Jf({"success":False,"error":"Invalid status_type"}), 400
    if not SNAPSHOT_BEFORE_ADMIN: _138()
    _195 = D.now(TZ.utc).isoformat()
    _196 = []
    for _197, _198 in list(_16.items()):
        if _198.get("statuses", {}).get(_193):
            _msg = _reason if _reason else f"Массовый отбой {_194[_193]} (админ)"
            _16[_197]["statuses"][_193] = False
            _16[_197]["last_update"] = _195
            _16[_197]["message"] = _280(_msg)
            _16[_197]["source"] = MANUAL_STATUS_SOURCE
            _196.append(_197)
    if _196:
        _msg_total = _reason if _reason else f"Массовый отбой {_194[_193]} (админ)"
        _17.append({"region":"ВСЕ РЕГИОНЫ","status":f"mass_clear_{_193}","timestamp":_195,"message":_280(_msg_total),"source":MANUAL_STATUS_SOURCE})
        _147("ВСЕ РЕГИОНЫ", f"mass_clear_{_193}", None, _reason)
        _15 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _36()
    return Jf({"success":True,"status_type":_193,"cleared_count":len(_196),"cleared_regions":_196,"timestamp":_195})

@_.route("/admin/mass_clear_all", methods=["POST"])
@_155
def _199():
    global _16, _17, _15, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    _200 = D.now(TZ.utc).isoformat()
    _reason = QR.get_json().get("reason","") if QR.get_json() else ""
    if not SNAPSHOT_BEFORE_ADMIN: _138()
    _201 = []
    for _202, _203 in list(_16.items()):
        if get_effective_status(_203.get("statuses", {})) != "clear":
            _msg = _reason if _reason else "Полный отбой всех тревог (админ)"
            for s in _16[_202]["statuses"]: _16[_202]["statuses"][s] = False
            _16[_202]["last_update"] = _200
            _16[_202]["message"] = _280(_msg)
            _16[_202]["source"] = MANUAL_STATUS_SOURCE
            _201.append(_202)
    if _201:
        _msg_total = _reason if _reason else "Полный отбой всех тревог (админ)"
        _17.append({"region":"ВСЕ РЕГИОНЫ","status":"mass_clear_all","timestamp":_200,"message":_280(_msg_total),"source":MANUAL_STATUS_SOURCE})
        _147("ВСЕ РЕГИОНЫ", "mass_clear_all", None, _reason)
        _15 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _36()
    return Jf({"success":True,"cleared_count":len(_201),"cleared_regions":_201,"timestamp":_200})

@_.route("/admin/changes", methods=["GET"])
@_155
def _204():
    return Jf({"changes":list(reversed(ADMIN_CHANGES[-200:])),"count":len(ADMIN_CHANGES),"last_updated":D.now(TZ.utc).isoformat()})

@_.route("/admin/rollback", methods=["POST"])
@_155
def _205():
    global _16, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN, _15
    if not SNAPSHOT_BEFORE_ADMIN and not ADMIN_CHANGES: return Jf({"success":False,"error":"No changes","message":"Нет изменений для отката"}), 400
    _206 = 0
    _207 = {}
    if SNAPSHOT_BEFORE_ADMIN:
        for _208, _209 in SNAPSHOT_BEFORE_ADMIN.items():
            _16[_208] = {"statuses":_209["statuses"].copy(),"last_update":_209["last_update"] or D.now(TZ.utc).isoformat(),"message":_209["message"],"source":_209["source"]}
            _207[_208] = {"status":get_effective_status(_209["statuses"]),"last_update":_209["last_update"],"message":_209["message"],"source":_209["source"]}
            _206 += 1
        SNAPSHOT_BEFORE_ADMIN = {}
    else:
        for _210, _211 in list(_16.items()):
            if _211.get("source") == MANUAL_STATUS_SOURCE:
                for s in _16[_210]["statuses"]: _16[_210]["statuses"][s] = False
                _16[_210]["last_update"] = D.now(TZ.utc).isoformat()
                _16[_210]["message"] = _280("Откат изменений админа")
                _16[_210]["source"] = "system"
                _207[_210] = {"status":"clear","last_update":D.now(TZ.utc).isoformat(),"message":_280("Откат изменений админа"),"source":"system"}
                _206 += 1
    ADMIN_CHANGES = []
    _15 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
    _36()
    return Jf({"success":True,"restored_count":_206,"restored_regions":_207,"timestamp":D.now(TZ.utc).isoformat()})

@_.route("/admin/parse_message", methods=["POST"])
@_155
def _256():
    global _16, _17
    _257 = QR.get_json()
    if not _257: return Jf({"success":False,"error":"No data"}), 400
    _258 = _257.get("message","").strip()
    if not _258: return Jf({"success":False,"error":"Empty message"}), 400
    _259 = _120(_258)
    if not _259: return Jf({"success":False,"error":"Не удалось определить тип тревоги в сообщении"}), 400
    _260 = _93(_258)
    if not _260: return Jf({"success":False,"error":"Не удалось определить регионы в сообщении"}), 400
    _261 = D.now(TZ.utc)
    _262 = {}
    _cred_msg = _280(_258[:500])
    for _263 in _260:
        if _263 not in _16 or "statuses" not in _16[_263]:
            _16[_263] = {"statuses": {"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False}, "last_update": _261.isoformat(), "message": "", "source": "simulated"}
        if _259 == "clear":
            for s in _16[_263]["statuses"]: _16[_263]["statuses"][s] = False
        elif not _259.startswith("mass_clear_"):
            _16[_263]["statuses"][_259] = True
        _16[_263]["last_update"] = _261.isoformat()
        _16[_263]["message"] = _cred_msg
        _16[_263]["source"] = "simulated"
        
        _17.append({"region":_263,"status":_259,"timestamp":_261.isoformat(),"message":_cred_msg,"source":"simulated"})
        if len(_17) > 5000: _17.pop(0)
        _262[_263] = _259
    _36()
    return Jf({"success":True,"parsed_status":_259,"regions":_260,"updated":_262,"timestamp":_261.isoformat()})

@_.route("/admin/log", methods=["GET"])
@_155
def _264():
    page = QR.args.get("page", 1, type=int)
    limit = QR.args.get("limit", 50, type=int)
    region_filter = QR.args.get("region", "").strip()
    status_filter = QR.args.get("status", "").strip()
    source_filter = QR.args.get("source", "").strip()
    entries = []
    for ch in ADMIN_CHANGES:
        if ch.get("rolled_back"): continue
        prev = get_effective_status(ch.get("previous_statuses", {})) if "previous_statuses" in ch else ch.get("previous_status")
        entries.append({
            "id": ch.get("id"),
            "region": ch["region"],
            "status": ch["status"],
            "previous_status": prev,
            "reason": ch.get("reason",""),
            "timestamp": ch["timestamp"],
            "source": ch.get("source", MANUAL_STATUS_SOURCE),
            "type": "admin"
        })
    for idx, alert in enumerate(reversed(_17)):
        entries.append({
            "id": f"alert_{len(_17)-idx}",
            "region": alert["region"],
            "status": alert["status"],
            "previous_status": None,
            "reason": alert.get("message",""),
            "timestamp": alert["timestamp"],
            "source": alert.get("source","unknown"),
            "type": "alert"
        })
    if region_filter:
        entries = [e for e in entries if region_filter.lower() in e["region"].lower()]
    if status_filter:
        entries = [e for e in entries if status_filter.lower() in e["status"].lower()]
    if source_filter:
        entries = [e for e in entries if source_filter.lower() in e["source"].lower()]
    total = len(entries)
    start = (page-1)*limit
    end = start + limit
    page_entries = entries[start:end]
    return Jf({"entries": page_entries, "page": page, "limit": limit, "total": total, "last_updated": D.now(TZ.utc).isoformat()})

@_.route("/admin/log/<int:change_id>/rollback", methods=["POST"])
@_155
def _265(change_id):
    global _16, ADMIN_CHANGES
    target = None
    for ch in ADMIN_CHANGES:
        if ch.get("id") == change_id and not ch.get("rolled_back"):
            target = ch
            break
    if not target: return Jf({"success":False,"error":"Change not found or already rolled back"}), 404
    region = target["region"]
    prev_statuses = target.get("previous_statuses")
    if not prev_statuses or region == "ВСЕ РЕГИОНЫ":
        return Jf({"success":False,"error":"Cannot rollback this change"}), 400
    
    _16[region] = {"statuses": prev_statuses.copy(), "last_update": D.now(TZ.utc).isoformat(), "message": _280(f"Откат изменения #{change_id}"), "source": "system"}
    target["rolled_back"] = True
    _36()
    return Jf({"success":True,"region":region,"restored_status":get_effective_status(prev_statuses)})

@_.route("/admin/region_details/<path:region>", methods=["GET"])
@_155
def _266(region):
    _267 = None
    for _268 in _16.keys():
        if _268.lower() == region.lower():
            _267 = _268
            break
    if not _267:
        for _269, _270 in _23.items():
            if _270.lower() == region.lower() or _269.lower() == region.lower():
                _267 = _270
                break
    if not _267:
        return Jf({"error":"Region not found"}), 404
    info = _16.get(_267, {"statuses":{"missile_alert":False,"missile_danger":False,"drone_attack":False,"drone_danger":False},"last_update":None,"message":"","source":"system"})
    recent = []
    for alert in reversed(_17):
        if alert["region"] == _267:
            recent.append(alert)
            if len(recent) >= 10: break
    return Jf({
        "region": _267,
        "status": get_effective_status(info.get("statuses", {})),
        "statuses": info.get("statuses", {}),
        "last_update": info.get("last_update"),
        "message": info.get("message",""),
        "source": info.get("source","unknown"),
        "recent_alerts": recent
    })

@_.route("/admin/stats", methods=["GET"])
@_155
def _271():
    days = QR.args.get("days", 7, type=int)
    end_date = D.now(TZ.utc).date()
    start_date = end_date - TD(days=days-1)
    date_list = [(start_date + TD(days=i)).isoformat() for i in range(days)]
    stats = {d: {"missile_alert":0,"missile_danger":0,"drone_attack":0,"drone_danger":0,"clear":0} for d in date_list}
    for alert in _17:
        try:
            ts = D.fromisoformat(alert["timestamp"])
            if ts.tzinfo: ts = ts.astimezone(TZ.utc).replace(tzinfo=None)
        except: continue
        day = ts.date().isoformat()
        if day in stats:
            status = alert["status"]
            if status in stats[day]:
                stats[day][status] += 1
    return Jf({"days": days, "stats": stats, "last_updated": D.now(TZ.utc).isoformat()})

@_.route("/api/request_key", methods=["GET","POST"])
def _300():
    if QR.method == "GET":
        return RTS('''
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Заявка на API ключ</title>
                <style>
                    body { font-family: sans-serif; background: #0a0a0a; color: #ddd; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
                    .form-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; padding: 30px; width: 100%; max-width: 420px; text-align: center; }
                    h2 { color: #fff; }
                    input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; background: rgba(255,255,255,0.05); color: white; font-size: 14px; outline: none; }
                    button { width: 100%; padding: 12px; border: none; border-radius: 10px; background: #4488ff; color: white; font-size: 16px; cursor: pointer; }
                    button:hover { background: #3366cc; }
                    .success { color: #44bb44; }
                    .error { color: #ff4444; }
                </style>
            </head>
            <body>
                <div class="form-box">
                    <h2>🔑 Заявка на API ключ</h2>
                    <p>Для доступа к данным радара</p>
                    <form method="POST">
                        <input type="email" name="email" placeholder="Ваш email" required>
                        <input type="text" name="telegram" placeholder="Telegram (например, @username)" required>
                        <textarea name="reason" placeholder="Зачем вам API?" rows="3" required></textarea>
                        <button type="submit">Отправить заявку</button>
                    </form>
                    {% if msg %}<p class="{{msg_type}}">{{ msg }}</p>{% endif %}
                </div>
            </body>
            </html>
        ''', msg=None, msg_type="")
    email = QR.form.get("email","").strip()
    telegram = QR.form.get("telegram","").strip()
    reason = QR.form.get("reason","").strip()
    if not email or not telegram or not reason:
        return RTS('''
            <!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>Заявка на API ключ</title>
            <style>body { font-family: sans-serif; background: #0a0a0a; color: #ddd; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
            .form-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; padding: 30px; width: 100%; max-width: 420px; text-align: center; }
            h2 { color: #fff; } .error { color: #ff4444; } a { color: #4488ff; }</style></head>
            <body><div class="form-box"><h2>🔑 Заявка на API ключ</h2><p class="error">Пожалуйста, заполните все поля.</p><a href="/api/request_key">← Назад</a></div></body></html>
        ''', msg="Пожалуйста, заполните все поля.", msg_type="error"), 400
    global API_APPLICATIONS, _API_APP_ID
    _API_APP_ID += 1
    API_APPLICATIONS.append({
        "id": _API_APP_ID,
        "email": email,
        "telegram": telegram,
        "reason": reason,
        "status": "pending",
        "timestamp": D.now(TZ.utc).isoformat()
    })
    _36()
    return RTS('''
        <!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>Заявка принята</title>
        <style>body { font-family: sans-serif; background: #0a0a0a; color: #ddd; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .form-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; padding: 30px; width: 100%; max-width: 420px; text-align: center; }
        h2 { color: #fff; } .success { color: #44bb44; } a { color: #4488ff; }</style></head>
        <body><div class="form-box"><h2>✅ Заявка принята!</h2><p class="success">Спасибо! Для ускорения рассмотрения свяжитесь с @olegmmg в Telegram.</p></div></body></html>
    ''')

@_.route("/admin/api_applications", methods=["GET"])
@_155
def _301():
    status_filter = QR.args.get("status", "").strip()
    if status_filter:
        filtered = [a for a in API_APPLICATIONS if a["status"] == status_filter]
    else:
        filtered = API_APPLICATIONS
    return Jf({"applications": list(reversed(filtered[-200:])), "count": len(filtered)})

@_.route("/admin/api_applications/<int:app_id>/approve", methods=["POST"])
@_155
def _302(app_id):
    global API_KEYS, API_APPLICATIONS
    app = None
    for a in API_APPLICATIONS:
        if a["id"] == app_id:
            app = a
            break
    if not app: return Jf({"success":False,"error":"Application not found"}), 404
    if app["status"] != "pending": return Jf({"success":False,"error":"Application already processed"}), 400
    key = SC.token_hex(32)
    now = D.now(TZ.utc)
    expires = now + TD(days=API_KEY_EXPIRY_DAYS)
    API_KEYS[key] = {
        "email": app["email"],
        "telegram": app["telegram"],
        "reason": app["reason"],
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "active": True
    }
    app["status"] = "approved"
    _36()
    return Jf({"success":True,"api_key":key,"expires_at":expires.isoformat()})

@_.route("/admin/api_applications/<int:app_id>/reject", methods=["POST"])
@_155
def _303(app_id):
    global API_APPLICATIONS
    app = None
    for a in API_APPLICATIONS:
        if a["id"] == app_id:
            app = a
            break
    if not app: return Jf({"success":False,"error":"Application not found"}), 404
    if app["status"] != "pending": return Jf({"success":False,"error":"Application already processed"}), 400
    app["status"] = "rejected"
    _36()
    return Jf({"success":True})

@_.route("/admin/api_keys", methods=["GET"])
@_155
def _304():
    keys_list = []
    for k, v in API_KEYS.items():
        keys_list.append({
            "key": k,
            "email": v["email"],
            "telegram": v["telegram"],
            "reason": v["reason"],
            "created_at": v["created_at"],
            "expires_at": v["expires_at"],
            "active": v["active"]
        })
    return Jf({"keys": keys_list, "count": len(keys_list)})

@_.route("/admin/api_keys/revoke", methods=["POST"])
@_155
def _305():
    key = QR.get_json().get("key","").strip() if QR.get_json() else ""
    if not key or key not in API_KEYS:
        return Jf({"success":False,"error":"Key not found"}), 404
    API_KEYS[key]["active"] = False
    _36()
    return Jf({"success":True})

@_.route("/api/statuses")
def _212():
    api_key = QR.args.get("api_key", "")
    if not api_key or api_key not in API_KEYS:
        return Jf({"error":"Valid API key required"}), 403
    key_info = API_KEYS[api_key]
    if not key_info.get("active", False):
        return Jf({"error":"API key is revoked"}), 403
    try:
        expires = D.fromisoformat(key_info["expires_at"])
        if D.now(TZ.utc) > expires:
            return Jf({"error":"API key expired"}), 403
    except:
        return Jf({"error":"Invalid expiration date in key"}), 403

    _213 = D.now(TZ.utc)
    _214 = _213 - TD(hours=24)
    _215 = {"regions":{},"last_updated":_213.isoformat()}
    for _216, _217 in _16.items():
        _218 = 0
        for _219 in reversed(_17[-5000:]):
            if _219["region"] == _216:
                try:
                    if D.fromisoformat(_219["timestamp"]) > _214: _218 += 1
                except: pass
        _215["regions"][_216] = {"status":get_effective_status(_217.get("statuses", {})),"statuses":_217.get("statuses", {}),"last_update":_217["last_update"],"message":_217.get("message",""),"alerts_last_hour":_218,"source":_217.get("source","unknown")}
    return Jf(_215)

@_.route("/api/recent_alerts")
def _220():
    api_key = QR.args.get("api_key", "")
    if not api_key or api_key not in API_KEYS:
        return Jf({"error":"Valid API key required"}), 403
    key_info = API_KEYS[api_key]
    if not key_info.get("active", False):
        return Jf({"error":"API key is revoked"}), 403
    try:
        expires = D.fromisoformat(key_info["expires_at"])
        if D.now(TZ.utc) > expires:
            return Jf({"error":"API key expired"}), 403
    except:
        return Jf({"error":"Invalid expiration date in key"}), 403

    return Jf({"alerts":list(reversed(_17[-100:]))[:50],"total":len(_17),"last_updated":D.now(TZ.utc).isoformat()})

@_.route("/")
def _221():
    return Jf({
        "status": "ok",
        "endpoints": [
            "/api/statuses",
            "/api/recent_alerts",
            "/api/request_key"
        ],
        "docs": "/docs",
        "regions_count": len(_16),
        "last_updated": D.now(TZ.utc).isoformat()
    })
    
def _222():
    while True:
        I.sleep(60)
        try:
            _48() 
        except Exception as e:
            _26(f"Auto-sync error: {e}")

def _223():
    _224 = int(O.environ.get("PORT", 5000))
    while True:
        I.sleep(240)
        try: Q.get(f"http://localhost:{_224}/api/statuses", timeout=10)
        except: pass

def _225():
    _226 = int(O.environ.get("PORT", 5000))
    _.run(host="0.0.0.0", port=_226, debug=False, use_reloader=False)

async def _227():
    global _18, _19, _21
    try:
        _228 = await _21.get_entity(_9)
        _229 = await _21.get_entity(_10)
    except: return
    while True:
        await A.sleep(30)
        try:
            _230 = await _21.get_messages(_9, limit=50)
            if _230:
                _231 = False
                for _232 in reversed(_230):
                    if _232.id <= _18: continue
                    _18 = _232.id
                    if _232.message and _123(_232.message, _232.id, "main", _232.date): _231 = True
                if _231: await _67(_21)
        except: pass
        try:
            _233 = await _21.get_messages(_10, limit=50)
            if _233:
                _234 = False
                for _235 in reversed(_233):
                    if _235.id <= _19: continue
                    _19 = _235.id
                    if _235.message and _123(_235.message, _235.id, "dpr", _235.date): _234 = True
                if _234: await _67(_21)
        except: pass

async def _236():
    global _21, _18, _19, _16
    _21 = TC(SS(_6), _4, _5)
    await _21.start()
    _47()
    _27()
    _237, _238 = _18, _19
    try:
        _239 = await _21.get_messages(_9, limit=500)
        if _239:
            _240 = sorted(_239, key=lambda x: x.id)
            _18 = _240[-1].id
            for _241 in _240:
                if _241.id <= _237: continue
                if _241.message: _123(_241.message, _241.id, "main", _241.date, True)
                await A.sleep(0.05)
    except: pass
    try:
        _242 = await _21.get_messages(_10, limit=200)
        if _242:
            _243 = sorted(_242, key=lambda x: x.id)
            _19 = _243[-1].id
            for _244 in _243:
                if _244.id <= _238: continue
                if _244.message: _123(_244.message, _244.id, "dpr", _244.date, True)
                await A.sleep(0.05)
    except: pass
    _27()
    await _67(_21)
    A.create_task(_227())
    T.Thread(target=_151, daemon=True).start()
    T.Thread(target=_225, daemon=True).start()
    T.Thread(target=_223, daemon=True).start()
    T.Thread(target=_222, daemon=True).start()
    while True: await A.sleep(1)

if __name__ == "__main__":
    A.run(_236())
