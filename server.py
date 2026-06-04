import os as O, re as R, json as J, threading as T, time as I, requests as Q, asyncio as A
import hashlib as HL, secrets as SC
from functools import wraps as WR
from datetime import datetime as D, timedelta as TD, timezone as TZ
from flask import Flask as F, jsonify as Jf, request as QR
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
def _handle_options(path=None):
    return "", 200

_3 = int(O.environ["API_ID"])
_4 = O.environ["API_HASH"]
_5 = O.environ["SESSION_STRING"]
_6 = O.environ.get("GITHUB_TOKEN", "")
_7 = O.environ.get("GITHUB_REPO", "")
_8 = O.environ.get("CHANNEL_USERNAME", "radarrussiia")
_9 = O.environ.get("DPR_CHANNEL", "DPR_channel")
_10 = O.environ.get("REPORT_CHANNEL", "RadarMapRf")
_11 = int(O.environ.get("STATUS_EXPIRY_HOURS", 12))

# ============= АДМИН-ПАНЕЛЬ КОНФИГ =============
ADMIN_PASSWORD = O.environ.get("ADMIN_PASSWORD", "admin123")
ADMIN_TOKENS = {}
BLOCKED_IPS = {}
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 3
BLOCK_DURATION = TD(hours=24)
TOKEN_EXPIRY = TD(hours=12)
MANUAL_STATUS_SOURCE = "admin_panel"

# ============= ИСТОРИЯ ИЗМЕНЕНИЙ АДМИНА =============
ADMIN_CHANGES = []  # [{region, status, previous_status, timestamp, source}]
SNAPSHOT_BEFORE_ADMIN = {}  # Снимок состояния до изменений админа

def _save_admin_snapshot():
    """Сохранить текущее состояние перед изменениями админа"""
    global SNAPSHOT_BEFORE_ADMIN
    # Не перезаписываем, если уже есть снимок
    if SNAPSHOT_BEFORE_ADMIN:
        return
    SNAPSHOT_BEFORE_ADMIN = {}
    for region, info in _15.items():
        SNAPSHOT_BEFORE_ADMIN[region] = {
            "status": info.get("status", "clear"),
            "last_update": info.get("last_update"),
            "message": info.get("message", ""),
            "source": info.get("source", "unknown")
        }

def _record_admin_change(region, status, previous_status=None):
    """Записать изменение админа в историю"""
    global ADMIN_CHANGES
    ADMIN_CHANGES.append({
        "region": region,
        "status": status,
        "previous_status": previous_status,
        "timestamp": D.now(TZ.utc).isoformat(),
        "source": MANUAL_STATUS_SOURCE
    })
    if len(ADMIN_CHANGES) > 1000:
        ADMIN_CHANGES = ADMIN_CHANGES[-1000:]

_12 = {"missile_alert":0, "missile_danger":1, "drone_attack":2, "drone_danger":3, "clear":4}

_13 = {"Московская область":"Московская обл.","Москва":"Москва","Ленинградская область":"Ленинградская обл.","Санкт-Петербург":"Санкт-Петербург","Нижегородская область":"Нижегородская обл.","Ставропольский край":"Ставропольский край","Краснодарский край":"Краснодарский край","Чеченская Республика":"Чеченская Респ.","Республика Дагестан":"Респ. Дагестан","Республика Ингушетия":"Респ. Ингушетия","Республика Северная Осетия":"Респ. Сев. Осетия","Карачаево-Черкесская Республика":"Карачаево-Черкесия","Кабардино-Балкарская Республика":"Кабардино-Балкария","Республика Адыгея":"Респ. Адыгея","Республика Крым":"Респ. Крым","Запорожская область":"Запорожская обл.","Херсонская область":"Херсонская обл.","Донецкая Народная Республика":"ДНР","Луганская Народная Республика":"ЛНР","Астраханская область":"Астраханская обл.","Волгоградская область":"Волгоградская обл.","Белгородская область":"Белгородская обл.","Брянская область":"Брянская обл.","Воронежская область":"Воронежская обл.","Курская область":"Курская обл.","Ростовская область":"Ростовская обл.","Смоленская область":"Смоленская обл.","Тульская область":"Тульская обл.","Калужская область":"Калужская обл.","Рязанская область":"Рязанская обл.","Тверская область":"Тверская обл.","Ярославская область":"Ярославская обл.","Владимирская область":"Владимирская обл.","Ивановская область":"Ивановская обл.","Костромская область":"Костромская обл.","Тамбовская область":"Тамбовская обл.","Липецкая область":"Липецкая обл.","Орловская область":"Орловская обл.","Пензенская область":"Пензенская обл.","Саратовская область":"Саратовская обл.","Ульяновская область":"Ульяновская обл.","Самарская область":"Самарская обл.","Пермский край":"Пермский край","Республика Башкортостан":"Респ. Башкортостан","Республика Татарстан":"Респ. Татарстан","Республика Удмуртия":"Респ. Удмуртия","Республика Марий Эл":"Респ. Марий Эл","Республика Мордовия":"Респ. Мордовия","Чувашская Республика":"Чувашская Респ.","Кировская область":"Кировская обл.","Оренбургская область":"Оренбургская обл.","Челябинская область":"Челябинская обл.","Свердловская область":"Свердловская обл.","Курганская область":"Курганская обл.","Тюменская область":"Тюменская обл.","Омская область":"Омская обл.","Новосибирская область":"Новосибирская обл.","Томская область":"Томская обл.","Кемеровская область":"Кемеровская обл.","Алтайский край":"Алтайский край","Красноярский край":"Красноярский край","Иркутская область":"Иркутская обл.","Забайкальский край":"Забайкальский край","Республика Бурятия":"Респ. Бурятия","Приморский край":"Приморский край","Хабаровский край":"Хабаровский край","Амурская область":"Амурская обл.","Сахалинская область":"Сахалинская обл.","Камчатский край":"Камчатский край","Магаданская область":"Магаданская обл.","Республика Саха (Якутия)":"Респ. Саха (Якутия)","Еврейская АО":"Еврейская АО","Чукотский АО":"Чукотский АО","ЯНАО":"ЯНАО","Ханты-Мансийский АО":"ХМАО","Ненецкий АО":"Ненецкий АО","Республика Карелия":"Респ. Карелия","Республика Коми":"Респ. Коми","Архангельская область":"Архангельская обл.","Мурманская область":"Мурманская обл.","Вологодская область":"Вологодская обл.","Новгородская область":"Новгородская обл.","Псковская область":"Псковская обл.","Калининградская область":"Калининградская обл.","Республика Алтай":"Респ. Алтай","Республика Хакасия":"Респ. Хакасия","Республика Тыва":"Респ. Тыва","Республика Калмыкия":"Респ. Калмыкия"}

_14 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
_15 = {}
_16 = []
_17 = 0
_18 = 0
_19 = "/tmp/radar_state.json"
_20 = None

_21 = {"костромской":"Костромская область","кировской":"Кировская область","московской":"Московская область","ленинградской":"Ленинградская область","нижегородской":"Нижегородская область","тульской":"Тульская область","калужской":"Калужская область","рязанской":"Рязанская область","тверской":"Тверская область","воронежской":"Воронежская область","белгородской":"Белгородская область","брянской":"Брянская область","курской":"Курская область","смоленской":"Смоленская область","орловской":"Орловская область","липецкой":"Липецкая область","тамбовской":"Тамбовская область","владимирской":"Владимирская область","ивановской":"Ивановская область","ярославской":"Ярославская область","вологодской":"Вологодская область","новгородской":"Новгородская область","псковской":"Псковская область","калининградской":"Калининградская область","пензенской":"Пензенская область","ульяновской":"Ульяновская область","саратовской":"Саратовская область","самарской":"Самарская область","оренбургской":"Оренбургская область","челябинской":"Челябинская область","свердловской":"Свердловская область","курганской":"Курганская область","тюменской":"Тюменская область","омской":"Омская область","томской":"Томская область","новосибирской":"Новосибирская область","кемеровской":"Кемеровская область","иркутской":"Иркутская область","амурской":"Амурская область","сахалинской":"Сахалинская область","магаданской":"Магаданская область","мурманской":"Мурманская область","архангельской":"Архангельская область","астраханской":"Астраханская область","волгоградской":"Волгоградская область","ростовской":"Ростовская область","запорожской":"Запорожская область","херсонской":"Херсонская область"}

_22 = {
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

_22_word_boundary = {
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

_23 = ["Донецкая Народная Республика","Луганская Народная Республика","Запорожская область","Херсонская область"]

def _dbg(msg):
    """Вывод отладочного сообщения в stderr с меткой времени."""
    print(f"[RADAR_DEBUG {D.now(TZ.utc).strftime('%H:%M:%S')}] {msg}", file=_sys.stderr, flush=True)

def _24():
    global _15, _14
    _25 = D.now(TZ.utc)
    _26 = _25 - TD(hours=_11)
    _27 = 0
    _28 = False
    for _29, _30 in list(_15.items()):
        _31 = _30.get("last_update")
        if not _31: continue
        try:
            _32 = D.fromisoformat(_31)
            if _32.tzinfo is None: _32 = _32.replace(tzinfo=TZ.utc)
            if _32 < _26 and _30.get("status") != "clear":
                _15[_29] = {"status":"clear","last_update":_25.isoformat(),"message":f"Автоматический отбой (нет обновлений >{_11}ч)","source":_30.get("source","system")}
                _27 += 1
                _28 = True
        except: pass
    if _27 > 0:
        _14 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _33()
    return _28

def _34(_35, _36="system"):
    global _15, _14
    _37 = D.now(TZ.utc).isoformat()
    _38 = 0
    _39 = {"drone_danger":"опасность БПЛА","missile_danger":"ракетная опасность","missile_alert":"ракетная тревога","drone_attack":"атака БПЛА"}
    for _40, _41 in list(_15.items()):
        if _41.get("status") == _35:
            _15[_40] = {"status":"clear","last_update":_37,"message":f"Отбой {_39.get(_35, _35)} по всем регионам","source":_36}
            _38 += 1
    if _38 > 0:
        _14 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _33()
    return _38 > 0

def _33():
    try:
        _42 = {"region_statuses":_15,"alert_history":_16[-2000:],"last_msg_id_main":_17,"last_msg_id_dpr":_18,"saved_at":D.now(TZ.utc).isoformat(),"last_summary":_14,"admin_changes":ADMIN_CHANGES[-200:],"snapshot_before_admin":SNAPSHOT_BEFORE_ADMIN}
        with open(_19, "w", encoding="utf-8") as _43: J.dump(_42, _43, ensure_ascii=False)
    except: pass

def _44():
    global _15, _16, _17, _18, _14, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    try:
        if not O.path.exists(_19): return
        with open(_19, "r", encoding="utf-8") as _45: _46 = J.load(_45)
        _15 = _46.get("region_statuses", {})
        _16 = _46.get("alert_history", [])
        _17 = _46.get("last_msg_id_main", 0)
        _18 = _46.get("last_msg_id_dpr", 0)
        _14 = _46.get("last_summary", {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None})
        ADMIN_CHANGES = _46.get("admin_changes", [])
        SNAPSHOT_BEFORE_ADMIN = _46.get("snapshot_before_admin", {})
    except: pass

def _47(_48): return _13.get(_48, _48)

def _49(_50):
    _51, _52, _53, _54 = [], [], [], []
    for _55, _56 in _50.items():
        _57 = _56.get("status")
        if not _57 or _57 == "clear": continue
        _58 = _47(_55)
        if _57 == "drone_danger": _51.append(f"    • {_58}")
        elif _57 == "drone_attack": _52.append(f"    • {_58}")
        elif _57 == "missile_danger": _53.append(f"    • {_58}")
        elif _57 == "missile_alert": _54.append(f"    • {_58}")
    _51.sort(); _52.sort(); _53.sort(); _54.sort()
    global _14
    _59 = {"drone_danger":_51,"drone_attack":_52,"missile_danger":_53,"missile_alert":_54}
    if _14.get("drone_danger") == _51 and _14.get("drone_attack") == _52 and _14.get("missile_danger") == _53 and _14.get("missile_alert") == _54: return None
    _14 = _59
    _14["timestamp"] = D.now(TZ.utc)
    _60 = D.now(TZ.utc) + TD(hours=3)
    _61 = _60.strftime("%H:%M | %d/%m")
    _62 = f"✈️ *Воздушная тревога* 🚀\n`{_61}`\n\n"
    _63 = []
    _63.extend(_54); _63.extend(_53); _63.extend(_52)
    _62 += "🔴 *АКТИВНАЯ ТРЕВОГА*\n"
    _62 += "\n".join(_63) + "\n\n" if _63 else "    • Отсутствует\n\n"
    _62 += "🟡 *ПОТЕНЦИАЛЬНАЯ ОПАСНОСТЬ*\n"
    _62 += "\n".join(_51) + "\n\n" if _51 else "    • Отсутствует\n\n"
    _62 += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"
    return _62

async def _64(_65, _66=False):
    if not _15: return
    _67 = _49(_15)
    if _67 is None and not _66: return
    if _67 is None and _66:
        if _14 and _14.get("timestamp"):
            _68 = D.now(TZ.utc) + TD(hours=3)
            _69 = _68.strftime("%H:%M | %d/%m")
            _67 = f"✈️ *Воздушная тревога* 🚀\n`{_69}`\n\n"
            _70 = []
            _70.extend(_14.get("missile_alert", [])); _70.extend(_14.get("missile_danger", [])); _70.extend(_14.get("drone_attack", []))
            _67 += "🔴 *АКТИВНАЯ ТРЕВОГА*\n"
            _67 += "\n".join(_70) + "\n\n" if _70 else "    • Отсутствует\n\n"
            _67 += "🟡 *ПОТЕНЦИАЛЬНАЯ ОПАСНОСТЬ*\n"
            _67 += "\n".join(_14.get("drone_danger", [])) + "\n\n" if _14.get("drone_danger", []) else "    • Отсутствует\n\n"
            _67 += "---\n📍 [Карта тревог](https://olegmmg.github.io/Radar/)\n📍 [TG Радар Россия](https://t.me/RadarMapRf)"
        else: return
    try:
        _71 = await _65.get_entity(_10)
        await _65.send_message(_71, _67, link_preview=False)
    except FWE as _72: await A.sleep(_72.seconds)
    except: pass

def _73(_74):
    if not _74: return ''
    _75 = [_74]
    for _76 in [r'❗️Радар по всей России\s*-\s*@radarrussiia\s*\n?', r'🌐 Обход белых списков\s*-\s*@Internet_Boost_bot\s*\([^)]+\)\s*\n?', r'@radarrussiia\s*\n?', r'@Internet_Boost_bot\s*\n?', r'https?://t\.me/Internet_Boost_bot\S*\s*\n?', r'Радар по всей России.*?\n?', r'Обход белых списков.*?\n?', r'🔴 Радар ДНР.*?\n?', r'📢 Оповещения Радар ДНР:\s*']:
        _75 = [R.sub(_76, '', _77, flags=R.IGNORECASE|R.MULTILINE) for _77 in _75]
    return R.sub(r'\n\s*\n', '\n', _75[0]).strip()

def _78(_79):
    if not _79: return False
    if "Радар ДНР" in _79: return False
    _80 = ["❗️ВНИМАНИЕ","Враг планирует", "БЕЗ МОБИЛЬНОЙ", "за прошедшую", "Впервые регионы РФ подверглись массовым РАКЕТНЫМ атакам","создать телеграм каналы для оповещения граждан","Ищите свой регион и подписывайтесь","НЕ БУДУТ БЛОКИРОВАТЬ","Нет вашего региона","вакансия без опыта","Пятёрочка ищет людей","платят от","АВАНС","Удалять негативные отзывы","Ставить лайки под роликами","Сравнивать цены","24/7 (https://t.me/","Москва 24/7","Питер 24/7","Подписывайтесь","будет автоматически выдан АВАНС"]
    for _81 in _80:
        if _81.upper() in _79.upper(): return True
    if len(R.findall(r'https?://t\.me/', _79)) > 3: return True
    _82 = _73(_79)
    return not _82 or len(_82) < 15

def _83(_84): return bool(R.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", _84, R.IGNORECASE))


def _region_match(_key, _text):
    _key_lower = _key.lower()
    _text_lower = _text.lower()
    if _key in _22_word_boundary:
        try:
            pattern = r'\b' + R.escape(_key_lower) + r'\b'
            result = bool(R.search(pattern, _text_lower))
            return result
        except:
            return _key_lower in _text_lower
    else:
        return _key_lower in _text_lower


def _85(_86):
    _87 = _86.lower()
    _88 = set()
    _89 = set()
    _dbg(f"=== _85() START | текст: {repr(_86[:120])} ===")
    for _90, _91 in _22.items():
        if _region_match(_90, _86):
            if _91 not in _89:
                _dbg(f"  [ШАГ 1] СОВПАДЕНИЕ: ключ='{_90}' → регион='{_91}' | word_boundary={'да' if _90 in _22_word_boundary else 'нет'}")
                _88.add(_91)
                _89.add(_91)
            else:
                _dbg(f"  [ШАГ 1] ДУБЛЬ (уже есть): ключ='{_90}' → регион='{_91}'")
    _city_pattern = r'(?:г\.|город|города)\s*([А-Яа-яёЁ-]+)'
    _cities = R.findall(_city_pattern, _87)
    if _cities:
        _dbg(f"  [ШАГ 2] найдены города с префиксом: {_cities}")
    for city in _cities:
        for full_name, region in _22.items():
            if city.lower() == full_name.lower():
                if region not in _89:
                    _dbg(f"  [ШАГ 2] СОВПАДЕНИЕ: город='{city}' → регион='{region}'")
                    _88.add(region)
                    _89.add(region)
                    break
    _district_pattern = r'([А-Яа-яёЁ-]+)\s+район'
    _districts = R.findall(_district_pattern, _87)
    if _districts:
        _dbg(f"  [ШАГ 3] найдены районы: {_districts}")
    for district in _districts:
        district_lower = district.lower()
        for full_name, region in _22.items():
            full_lower = full_name.lower()
            if full_lower.startswith(district_lower) and "район" in full_lower:
                if region not in _89:
                    _dbg(f"  [ШАГ 3] СОВПАДЕНИЕ: район='{district}' → регион='{region}'")
                    _88.add(region)
                    _89.add(region)
                    break
    _94 = R.findall(r'([А-Яа-яёЁ]+(?:ской|ской))\s+области', _87)
    if _94:
        _dbg(f"  [ШАГ 4] найдены склонения: {_94}")
    for _95 in _94:
        _96 = _95.lower()
        if _96 in _21:
            _97 = _21[_96]
            if _97 not in _89:
                _dbg(f"  [ШАГ 4] СОВПАДЕНИЕ: склонение='{_95}' → регион='{_97}'")
                _88.add(_97)
                _89.add(_97)
    _98 = R.findall(r'([А-Яа-яёЁ]+(?:ская|ская))\s+область', _87)
    if _98:
        _dbg(f"  [ШАГ 5] найдены прилагательные+область: {_98}")
    for _99 in _98:
        for _90, _91 in _22.items():
            if _99 in _90.lower() and _91 not in _89:
                _dbg(f"  [ШАГ 5] СОВПАДЕНИЕ: прилагательное='{_99}' входит в ключ='{_90}' → регион='{_91}'")
                _88.add(_91)
                _89.add(_91)
                break
    _100 = R.findall(r'([А-Яа-яёЁ]+(?:ский|ский))\s+край', _87)
    if _100:
        _dbg(f"  [ШАГ 6] найдены края: {_100}")
    for _101 in _100:
        for _90, _91 in _22.items():
            if _101 in _90.lower() and _91 not in _89:
                _dbg(f"  [ШАГ 6] СОВПАДЕНИЕ: '{_101}' → регион='{_91}'")
                _88.add(_91)
                _89.add(_91)
                break
    _102 = R.findall(r'(?:республика|республики)\s+([А-Яа-яёЁ][а-яёЁ]+(?:ская|ская)?)', _87)
    if _102:
        _dbg(f"  [ШАГ 7] найдены республики: {_102}")
    for _103 in _102:
        for _90, _91 in _22.items():
            if _103 in _90.lower() or _103 in _91.lower():
                if _91 not in _89:
                    _dbg(f"  [ШАГ 7] СОВПАДЕНИЕ: '{_103}' → регион='{_91}'")
                    _88.add(_91)
                    _89.add(_91)
                    break
    for _104 in ["башкортостан","чувашия","татарстан","удмуртия","марий эл","мордовия","карелия","коми","адыгея","калмыкия","алтай","хакасия","тыва","бурятия","саха"]:
        if R.search(r'\b' + R.escape(_104) + r'\b', _87):
            for _90, _91 in _22.items():
                if _104 in _90.lower() or _104 in _91.lower():
                    if _91 not in _89:
                        _dbg(f"  [ШАГ 8] СОВПАДЕНИЕ: '{_104}' → регион='{_91}'")
                        _88.add(_91)
                        _89.add(_91)
                        break
    if "Донецкая Народная Республика" not in _89 and R.search(r'\b(днр|dnr|донецк|горловка|макеевка|енакиево)\b', _87):
        _dbg(f"  [ШАГ 9] СОВПАДЕНИЕ ДНР")
        _88.add("Донецкая Народная Республика")
    if "Луганская Народная Республика" not in _89 and R.search(r'\b(лнр|lnr|луганск|алчевск|брянка)\b', _87):
        _dbg(f"  [ШАГ 9] СОВПАДЕНИЕ ЛНР")
        _88.add("Луганская Народная Республика")
    if "Запорожская область" not in _89 and R.search(r'запорожск|zaporizh', _87):
        _dbg(f"  [ШАГ 9] СОВПАДЕНИЕ Запорожская")
        _88.add("Запорожская область")
    if "Херсонская область" not in _89 and R.search(r'херсон|kherson', _87):
        _dbg(f"  [ШАГ 9] СОВПАДЕНИЕ Херсонская")
        _88.add("Херсонская область")
    result = list(_88)
    _dbg(f"=== _85() ИТОГ: {result} ===")
    return result

def _105(_106):
    _107 = _106.lower()
    if "отбой опасности бпла по всем ранее объявленным регионам" in _107: return "mass_clear_drone_danger"
    if "отбой ракетной опасности по всем ранее объявленным регионам" in _107: return "mass_clear_missile_danger"
    if "отбой ракетной тревоги по всем ранее объявленным регионам" in _107: return "mass_clear_missile_alert"
    if any(w in _107 for w in ["отбой","отбой опасности","отбой по бпла","отбой ракетной опасности","отбой авиационной","отбой фиксации","отбой по пкр","отбой по бэк","все спокойно","тихо","обстановка спокойная","угрозу атаки снимаем"]):
        return "clear"
    if "ложная цель" in _107: return None
    if any(w in _107 for w in ["ракетная тревога","ракетной тревоги","тревога по пкр","тревога по бэк","ракетно бомбовая опасность","авиационная ракетная","авиационная ракетная бомбовая опасность"]):
        return "missile_alert"
    if any(w in _107 for w in ["ракетная опасность","ракетной опасности","опасность по пкр","опасность по бэк"]):
        return "missile_danger"
    if any(w in _107 for w in ["работа пво","сбитие","сбития","фиксация бпла","фиксации бпла","группа бпла","группы бпла","тревога по бпла","атака бпла","атакуют","много бпла","волна бпла","фиксация групп","идут сбития","массовый запуск","угроза атаки БПЛА","угроза атаки","угроза бпла"]):
        return "drone_attack"
    if any(w in _107 for w in ["опасность по бпла", "опасность сохраняем", "угроза атаки","внимание по бпла","меры безопасности","опасность сохраняется","повторно","fpv","fpv-дронам","единичных бпла","внимание","опасность сохраняем"]):
        return "drone_danger"
    return None

def _108(_109, _110=None, _111="main", _112=None, _113=False):
    global _15, _16
    if not _109: return False
    _dbg(f"--- _108() SOURCE={_111} ID={_110} ---")
    _dbg(f"  [ORIG_TEXT] {repr(_109[:600])}")
    if _111 == "main" and _78(_109):
        _dbg(f"  [_108] ОТФИЛЬТРОВАНО: _78() → спам/нерелевантно")
        return False
    if _83(_109):
        _dbg(f"  [_108] ОТФИЛЬТРОВАНО: _83() → сводка уничтожения")
        return False
    _114 = _105(_109)
    _dbg(f"  [_108] статус из _105(): {_114!r}")
    if _114 and _114.startswith("mass_clear_"):
        _115 = False
        if _114 == "mass_clear_drone_danger": _115 = _34("drone_danger", _111)
        elif _114 == "mass_clear_missile_danger": _115 = _34("missile_danger", _111)
        elif _114 == "mass_clear_missile_alert": _115 = _34("missile_alert", _111)
        if _115 and not _113: _16.append({"region":"ВСЕ РЕГИОНЫ","status":"mass_clear","timestamp":D.now(TZ.utc).isoformat(),"message":_109[:500],"source":_111})
        return _115
    _116 = _85(_109)
    _dbg(f"  [_108] регионы из _85(): {_116}")
    if not _116:
        _dbg(f"  [_108] ПРОПУСК: регионы не найдены")
        return False
    if _111 == "dpr": _116 = [r for r in _116 if r in _23]
    if not _116:
        _dbg(f"  [_108] ПРОПУСК: после фильтра DPR регионы пусты")
        return False
    if not _114:
        _dbg(f"  [_108] ПРОПУСК: статус не определён (_105 вернул None)")
        return False
    _117 = _112.isoformat() if _112 and _112.tzinfo else D.now(TZ.utc).isoformat()
    _118 = _73(_109)
    _119 = False
    for _120 in _116:
        _121 = _15.get(_120, {}).get("status")
        _dbg(f"  [_108] регион='{_120}' текущий_статус={_121!r} новый_статус={_114!r}")
        if _111 != "dpr" and not _113:
            if _121 is not None:
                if _114 == "clear":
                    pass
                elif _12.get(_114, 99) > _12.get(_121, 99):
                    _dbg(f"  [_108] ПРОПУСК ОБНОВЛЕНИЯ: приоритет нового ({_114}={_12.get(_114,99)}) < текущего ({_121}={_12.get(_121,99)})")
                    continue
        _15[_120] = {"status":_114,"last_update":_117,"message":_118[:500] if _118 else "","source":_111}
        _16.append({"region":_120,"status":_114,"timestamp":_117,"message":_118[:500] if _118 else "","source":_111})
        if len(_16) > 5000: _16.pop(0)
        _119 = True
        _dbg(f"  [_108] ОБНОВЛЕНО: регион='{_120}' → {_114}")
    if not _119:
        _dbg(f"  [_108] НИ ОДИН регион не обновлён (все заблокированы приоритетом)")
    return _119

def _122():
    global _20
    while True:
        I.sleep(600)
        try:
            _123 = _24()
            if _123 and _20:
                _124 = A.new_event_loop()
                A.set_event_loop(_124)
                _124.run_until_complete(_64(_20, True))
                _124.close()
        except: pass

# ============= АДМИН-ПАНЕЛЬ API =============

def _check_ip_blocked():
    ip = QR.remote_addr
    if ip in BLOCKED_IPS:
        if BLOCKED_IPS[ip] > D.now(TZ.utc):
            return True
        else:
            del BLOCKED_IPS[ip]
            if ip in LOGIN_ATTEMPTS:
                del LOGIN_ATTEMPTS[ip]
    return False

def _admin_required(f):
    @WR(f)
    def decorated(*args, **kwargs):
        auth_header = QR.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        if not token or token not in ADMIN_TOKENS:
            return Jf({"error": "Unauthorized", "message": "Требуется авторизация"}), 401
        if ADMIN_TOKENS[token] < D.now(TZ.utc):
            del ADMIN_TOKENS[token]
            return Jf({"error": "Token expired", "message": "Токен истёк"}), 401
        ADMIN_TOKENS[token] = D.now(TZ.utc) + TOKEN_EXPIRY
        return f(*args, **kwargs)
    return decorated

def _cleanup_tokens():
    now = D.now(TZ.utc)
    expired = [t for t, exp in ADMIN_TOKENS.items() if exp < now]
    for t in expired:
        del ADMIN_TOKENS[t]

@_.route("/admin/login", methods=["POST"])
def _admin_login():
    ip = QR.remote_addr
    if _check_ip_blocked():
        blocked_until = BLOCKED_IPS.get(ip)
        return Jf({
            "success": False,
            "error": "IP blocked",
            "message": f"IP заблокирован до {blocked_until.strftime('%H:%M %d.%m.%Y') if blocked_until else 'неизвестно'}",
            "blocked_until": blocked_until.isoformat() if blocked_until else None
        }), 403
    data = QR.get_json()
    password = data.get("password", "") if data else ""
    if not password:
        return Jf({"success": False, "error": "No password"}), 400
    if password == ADMIN_PASSWORD:
        if ip in LOGIN_ATTEMPTS:
            del LOGIN_ATTEMPTS[ip]
        token = SC.token_hex(32)
        ADMIN_TOKENS[token] = D.now(TZ.utc) + TOKEN_EXPIRY
        _cleanup_tokens()
        return Jf({
            "success": True,
            "token": token,
            "expires_at": (D.now(TZ.utc) + TOKEN_EXPIRY).isoformat()
        })
    else:
        LOGIN_ATTEMPTS[ip] = LOGIN_ATTEMPTS.get(ip, 0) + 1
        if LOGIN_ATTEMPTS[ip] >= MAX_LOGIN_ATTEMPTS:
            BLOCKED_IPS[ip] = D.now(TZ.utc) + BLOCK_DURATION
            return Jf({
                "success": False,
                "error": "Too many attempts",
                "message": "IP заблокирован на 24 часа после 3 неверных попыток",
                "blocked_until": BLOCKED_IPS[ip].isoformat()
            }), 403
        return Jf({
            "success": False,
            "error": "Wrong password",
            "attempts_left": MAX_LOGIN_ATTEMPTS - LOGIN_ATTEMPTS[ip]
        }), 401

@_.route("/admin/regions", methods=["GET"])
@_admin_required
def _admin_get_regions():
    regions_data = {}
    now = D.now(TZ.utc)
    cutoff = now - TD(hours=24)
    for region_name, region_info in _15.items():
        alerts_count = 0
        for alert in reversed(_16[-5000:]):
            if alert["region"] == region_name:
                try:
                    if D.fromisoformat(alert["timestamp"]) > cutoff:
                        alerts_count += 1
                except:
                    pass
        regions_data[region_name] = {
            "status": region_info["status"],
            "last_update": region_info["last_update"],
            "message": region_info.get("message", ""),
            "alerts_last_hour": alerts_count,
            "source": region_info.get("source", "unknown")
        }
    for region_name in _22.values():
        if region_name not in regions_data:
            regions_data[region_name] = {
                "status": "clear",
                "last_update": None,
                "message": "",
                "alerts_last_hour": 0,
                "source": "system"
            }
    unique_regions = {}
    for name, data in regions_data.items():
        if name not in unique_regions:
            unique_regions[name] = data
    return Jf({
        "regions": unique_regions,
        "last_updated": now.isoformat(),
        "total_count": len(unique_regions)
    })

@_.route("/admin/set_status", methods=["POST"])
@_admin_required
def _admin_set_status():
    global _15, _16, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    data = QR.get_json()
    if not data:
        return Jf({"success": False, "error": "No data"}), 400
    region = data.get("region", "").strip()
    status = data.get("status", "").strip()
    if not region or not status:
        return Jf({"success": False, "error": "Region and status required"}), 400
    valid_statuses = ["missile_alert", "missile_danger", "drone_attack", "drone_danger", "clear"]
    if status not in valid_statuses:
        return Jf({"success": False, "error": f"Invalid status. Valid: {valid_statuses}"}), 400
    
    # Сохранить снимок перед первым изменением
    if not SNAPSHOT_BEFORE_ADMIN:
        _save_admin_snapshot()
    
    found_region = None
    for r_name in _15.keys():
        if r_name.lower() == region.lower():
            found_region = r_name
            break
    if not found_region:
        for key, val in _22.items():
            if val.lower() == region.lower() or key.lower() == region.lower():
                found_region = val
                break
    if not found_region:
        found_region = region
    
    previous_status = _15.get(found_region, {}).get("status", "clear")
    now = D.now(TZ.utc)
    status_labels = {
        "missile_alert": "Ракетная тревога (админ)",
        "missile_danger": "Ракетная опасность (админ)",
        "drone_attack": "Атака БПЛА (админ)",
        "drone_danger": "Опасность БПЛА (админ)",
        "clear": "Отбой (админ)"
    }
    _15[found_region] = {
        "status": status,
        "last_update": now.isoformat(),
        "message": status_labels.get(status, f"Статус изменён на {status}"),
        "source": MANUAL_STATUS_SOURCE
    }
    _16.append({
        "region": found_region,
        "status": status,
        "timestamp": now.isoformat(),
        "message": status_labels.get(status, f"Статус изменён на {status}"),
        "source": MANUAL_STATUS_SOURCE
    })
    if len(_16) > 5000:
        _16.pop(0)
    
    # Записать изменение админа
    _record_admin_change(found_region, status, previous_status)
    _33()
    return Jf({
        "success": True,
        "region": found_region,
        "status": status,
        "previous_status": previous_status,
        "timestamp": now.isoformat()
    })

@_.route("/admin/mass_clear", methods=["POST"])
@_admin_required
def _admin_mass_clear():
    global _15, _16, _14, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    data = QR.get_json()
    if not data:
        return Jf({"success": False, "error": "No data"}), 400
    status_type = data.get("status_type", "").strip()
    valid_types = {
        "drone_danger": "опасность БПЛА",
        "missile_danger": "ракетная опасность",
        "missile_alert": "ракетная тревога"
    }
    if status_type not in valid_types:
        return Jf({"success": False, "error": f"Invalid status_type. Valid: {list(valid_types.keys())}"}), 400
    
    # Сохранить снимок
    if not SNAPSHOT_BEFORE_ADMIN:
        _save_admin_snapshot()
    
    now = D.now(TZ.utc).isoformat()
    cleared = []
    for region_name, region_info in list(_15.items()):
        if region_info.get("status") == status_type:
            _15[region_name] = {
                "status": "clear",
                "last_update": now,
                "message": f"Массовый отбой {valid_types[status_type]} (админ)",
                "source": MANUAL_STATUS_SOURCE
            }
            cleared.append(region_name)
    if cleared:
        _16.append({
            "region": "ВСЕ РЕГИОНЫ",
            "status": f"mass_clear_{status_type}",
            "timestamp": now,
            "message": f"Массовый отбой {valid_types[status_type]} по всем регионам (админ)",
            "source": MANUAL_STATUS_SOURCE
        })
        _record_admin_change("ВСЕ РЕГИОНЫ", f"mass_clear_{status_type}", status_type)
        _14 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _33()
    return Jf({
        "success": True,
        "status_type": status_type,
        "cleared_count": len(cleared),
        "cleared_regions": cleared,
        "timestamp": now
    })

@_.route("/admin/mass_clear_all", methods=["POST"])
@_admin_required
def _admin_mass_clear_all():
    global _15, _16, _14, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN
    
    # Сохранить снимок
    if not SNAPSHOT_BEFORE_ADMIN:
        _save_admin_snapshot()
    
    now = D.now(TZ.utc).isoformat()
    cleared = []
    for region_name, region_info in list(_15.items()):
        if region_info.get("status") != "clear":
            _15[region_name] = {
                "status": "clear",
                "last_update": now,
                "message": "Полный отбой всех тревог (админ)",
                "source": MANUAL_STATUS_SOURCE
            }
            cleared.append(region_name)
    if cleared:
        _16.append({
            "region": "ВСЕ РЕГИОНЫ",
            "status": "mass_clear_all",
            "timestamp": now,
            "message": "Полный отбой всех тревог по всем регионам (админ)",
            "source": MANUAL_STATUS_SOURCE
        })
        _record_admin_change("ВСЕ РЕГИОНЫ", "mass_clear_all", None)
        _14 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _33()
    return Jf({
        "success": True,
        "cleared_count": len(cleared),
        "cleared_regions": cleared,
        "timestamp": now
    })

@_.route("/admin/changes", methods=["GET"])
@_admin_required
def _admin_get_changes():
    """Получить список изменений, сделанных через админ-панель"""
    return Jf({
        "changes": list(reversed(ADMIN_CHANGES[-200:])),
        "count": len(ADMIN_CHANGES),
        "last_updated": D.now(TZ.utc).isoformat()
    })

@_.route("/admin/rollback", methods=["POST"])
@_admin_required
def _admin_rollback():
    """Откатить все изменения админа, восстановить состояние из Telegram"""
    global _15, ADMIN_CHANGES, SNAPSHOT_BEFORE_ADMIN, _14
    
    if not SNAPSHOT_BEFORE_ADMIN and not ADMIN_CHANGES:
        return Jf({
            "success": False,
            "error": "No changes to rollback",
            "message": "Нет изменений для отката"
        }), 400
    
    restored_count = 0
    restored_regions = {}
    
    if SNAPSHOT_BEFORE_ADMIN:
        for region, info in SNAPSHOT_BEFORE_ADMIN.items():
            _15[region] = {
                "status": info["status"],
                "last_update": info["last_update"] or D.now(TZ.utc).isoformat(),
                "message": info["message"],
                "source": info["source"]
            }
            restored_regions[region] = {
                "status": info["status"],
                "last_update": info["last_update"],
                "message": info["message"],
                "source": info["source"]
            }
            restored_count += 1
        SNAPSHOT_BEFORE_ADMIN = {}
    else:
        for region, info in list(_15.items()):
            if info.get("source") == MANUAL_STATUS_SOURCE:
                _15[region] = {
                    "status": "clear",
                    "last_update": D.now(TZ.utc).isoformat(),
                    "message": "Откат изменений админа",
                    "source": "system"
                }
                restored_regions[region] = {
                    "status": "clear",
                    "last_update": D.now(TZ.utc).isoformat(),
                    "message": "Откат изменений админа",
                    "source": "system"
                }
                restored_count += 1
    
    ADMIN_CHANGES = []
    _14 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
    _33()
    
    return Jf({
        "success": True,
        "restored_count": restored_count,
        "restored_regions": restored_regions,
        "timestamp": D.now(TZ.utc).isoformat()
    })

# ============= ОСНОВНЫЕ API-ЭНДПОИНТЫ =============

@_.route("/api/statuses")
def _125():
    _126 = D.now(TZ.utc)
    _127 = _126 - TD(hours=24)
    _128 = {"regions":{}, "last_updated":_126.isoformat()}
    for _129, _130 in _15.items():
        _131 = 0
        for _132 in reversed(_16[-5000:]):
            if _132["region"] == _129:
                try:
                    if D.fromisoformat(_132["timestamp"]) > _127: _131 += 1
                except: pass
        _128["regions"][_129] = {"status":_130["status"],"last_update":_130["last_update"],"message":_130.get("message",""),"alerts_last_hour":_131,"source":_130.get("source","unknown")}
    return Jf(_128)

@_.route("/api/recent_alerts")
def _133():
    return Jf({"alerts":list(reversed(_16[-100:]))[:50], "total":len(_16), "last_updated":D.now(TZ.utc).isoformat()})

@_.route("/")
def _134():
    return Jf({"status":"ok","endpoints":["/api/statuses","/api/recent_alerts","/admin/login","/admin/regions","/admin/set_status","/admin/mass_clear","/admin/mass_clear_all","/admin/changes","/admin/rollback"],"regions_count":len(_15),"last_updated":D.now(TZ.utc).isoformat()})

def _135():
    while True:
        I.sleep(60)
        if _15: _33()

def _136():
    _137 = int(O.environ.get("PORT", 5000))
    while True:
        I.sleep(240)
        try: Q.get(f"http://localhost:{_137}/api/statuses", timeout=10)
        except: pass

def _138():
    _139 = int(O.environ.get("PORT", 5000))
    _.run(host="0.0.0.0", port=_139, debug=False, use_reloader=False)

async def _140():
    global _17, _18, _20
    try:
        _141 = await _20.get_entity(_8)
        _142 = await _20.get_entity(_9)
    except: return
    while True:
        await A.sleep(30)
        try:
            _143 = await _20.get_messages(_8, limit=50)
            if _143:
                _144 = False
                for _145 in reversed(_143):
                    if _145.id <= _17: continue
                    _17 = _145.id
                    if _145.message and _108(_145.message, _145.id, "main", _145.date): _144 = True
                if _144: await _64(_20)
        except: pass
        try:
            _146 = await _20.get_messages(_9, limit=50)
            if _146:
                _147 = False
                for _148 in reversed(_146):
                    if _148.id <= _18: continue
                    _18 = _148.id
                    if _148.message and _108(_148.message, _148.id, "dpr", _148.date): _147 = True
                if _147: await _64(_20)
        except: pass

async def _149():
    global _20, _17, _18, _15
    _20 = TC(SS(_5), _3, _4)
    await _20.start()
    _44()
    _24()
    _150, _151 = _17, _18
    try:
        _152 = await _20.get_messages(_8, limit=200)
        if _152:
            _153 = sorted(_152, key=lambda x: x.id)
            _17 = _153[-1].id
            for _154 in _153:
                if _154.id <= _150: continue
                if _154.message: _108(_154.message, _154.id, "main", _154.date, True)
                await A.sleep(0.05)
    except: pass
    try:
        _155 = await _20.get_messages(_9, limit=200)
        if _155:
            _156 = sorted(_155, key=lambda x: x.id)
            _18 = _156[-1].id
            for _157 in _156:
                if _157.id <= _151: continue
                if _157.message: _108(_157.message, _157.id, "dpr", _157.date, True)
                await A.sleep(0.05)
    except: pass
    _24()
    await _64(_20)
    A.create_task(_140())
    T.Thread(target=_122, daemon=True).start()
    T.Thread(target=_138, daemon=True).start()
    T.Thread(target=_136, daemon=True).start()
    T.Thread(target=_135, daemon=True).start()
    while True: await A.sleep(1)

if __name__ == "__main__":
    A.run(_149())
