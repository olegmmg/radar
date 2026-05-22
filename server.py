import os as O, re as R, json as J, threading as T, time as I, requests as Q, asyncio as A
from datetime import datetime as D, timedelta as TD, timezone as TZ
from flask import Flask as F, jsonify as Jf
from telethon import TelegramClient as TC
from telethon.sessions import StringSession as SS
from telethon.errors import FloodWaitError as FWE

_ = F(__name__)

@_.after_request
def _1(_2):
    _2.headers["Access-Control-Allow-Origin"] = "*"
    _2.headers["Access-Control-Allow-Headers"] = "Content-Type"
    _2.headers["Access-Control-Allow-Methods"] = "GET"
    return _2

_3 = int(O.environ["API_ID"])
_4 = O.environ["API_HASH"]
_5 = O.environ["SESSION_STRING"]
_6 = O.environ.get("GITHUB_TOKEN", "")
_7 = O.environ.get("GITHUB_REPO", "")
_8 = O.environ.get("CHANNEL_USERNAME", "radarrussiia")
_9 = O.environ.get("DPR_CHANNEL", "DPR_channel")
_10 = O.environ.get("REPORT_CHANNEL", "RadarMapRf")
_11 = int(O.environ.get("STATUS_EXPIRY_HOURS", 12))

_12 = {"missile_alert":0,"missile_danger":1,"drone_attack":2,"drone_danger":3,"clear":4}
_13 = {"Московская область":"Московская обл.","Москва":"Москва","Ленинградская область":"Ленинградская обл.","Санкт-Петербург":"Санкт-Петербург"}
_14 = {"Донецкая Народная Республика","Луганская Народная Республика","Запорожская область","Херсонская область"}
_15 = {}
_16 = []
_17 = 0
_18 = 0
_19 = "/tmp/radar_state.json"
_20 = None
_21 = {"костромской":"Костромская область","московской":"Московская область","ленинградской":"Ленинградская область"}
_22 = {"Московская область":"Московская область","Москва":"Москва","Подмосковье":"Московская область","г. Москва":"Москва"}
_23 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}

def _24():
    global _15, _23
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
                _15[_29] = {"status":"clear","last_update":_25.isoformat(),"message":"Автоматический отбой","source":_30.get("source","system")}
                _27 += 1
                _28 = True
        except: pass
    if _27 > 0:
        _23 = {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None}
        _33()
    return _28

def _33():
    try:
        _34 = {"region_statuses":_15,"alert_history":_16[-2000:],"last_msg_id_main":_17,"last_msg_id_dpr":_18,"saved_at":D.now(TZ.utc).isoformat(),"last_summary":_23}
        with open(_19, "w", encoding="utf-8") as _35: J.dump(_34, _35, ensure_ascii=False)
    except: pass

def _36():
    global _15, _16, _17, _18, _23
    try:
        if not O.path.exists(_19): return
        with open(_19, "r", encoding="utf-8") as _37: _38 = J.load(_37)
        _15 = _38.get("region_statuses", {})
        _16 = _38.get("alert_history", [])
        _17 = _38.get("last_msg_id_main", 0)
        _18 = _38.get("last_msg_id_dpr", 0)
        _23 = _38.get("last_summary", {"drone_danger":[],"drone_attack":[],"missile_danger":[],"missile_alert":[],"timestamp":None})
    except: pass

@_.route("/api/statuses")
def _39():
    _40 = {"regions":{}, "last_updated":D.now(TZ.utc).isoformat()}
    for _41, _42 in _15.items():
        _43 = 0
        for _44 in reversed(_16[-5000:]):
            if _44["region"] == _41:
                try:
                    if D.fromisoformat(_44["timestamp"]) > D.now(TZ.utc) - TD(hours=24): _43 += 1
                except: pass
        _40["regions"][_41] = {"status":_42.get("status"),"last_update":_42.get("last_update"),"message":_42.get("message",""),"alerts_last_hour":_43,"source":_42.get("source","unknown")}
    return Jf(_40)

@_.route("/api/recent_alerts")
def _45():
    return Jf({"alerts":list(reversed(_16[-100:]))[:50], "total":len(_16), "last_updated":D.now(TZ.utc).isoformat()})

@_.route("/")
def _46():
    return Jf({"status":"ok","endpoints":["/api/statuses","/api/recent_alerts"],"regions_count":len(_15),"last_update":D.now(TZ.utc).isoformat()})

def _47():
    _48 = int(O.environ.get("PORT", 5000))
    while True:
        I.sleep(240)
        try: Q.get(f"http://localhost:{_48}/api/statuses", timeout=10)
        except: pass

def _49():
    _50 = int(O.environ.get("PORT", 5000))
    _.run(host="0.0.0.0", port=_50, debug=False, use_reloader=False)

def _51():
    while True:
        I.sleep(60)
        if _15: _33()

def _52(_53):
    if not _53: return ""
    _54 = str(_53)
    for _55 in [r'❗️Радар по всей России\s*-\s*@radarrussiia\s*\n?', r'@radarrussiia\s*\n?', r'https?://t\.me/Internet_Boost_bot\S*\s*\n?']:
        _54 = R.sub(_55, '', _54, flags=R.IGNORECASE|R.MULTILINE)
    return R.sub(r'\n\s*\n', '\n', _54).strip()

def _56(_57):
    _58 = str(_57).lower()
    if "радар днр" in _58: return False
    for _59 in ["❗️ВНИМАНИЕ","враг планирует","Подписывайтесь"]:
        if _59.upper() in _58.upper(): return True
    _60 = _52(_57)
    return not _60 or len(_60) < 15

def _61(_62):
    return bool(R.search(r"с \d{1,2}:\d{2} до \d{1,2}:\d{2}.*уничтожено", str(_62), R.IGNORECASE))

def _63(_64):
    _65 = str(_64).lower()
    _66 = set()
    for _67, _68 in _22.items():
        if _67.lower() in _65: _66.add(_68)
    if any(x in _65 for x in ["днр","dnr","донецк"]): _66.add("Донецкая Народная Республика")
    if any(x in _65 for x in ["лнр","lnr","луганск"]): _66.add("Луганская Народная Республика")
    if "запорожск" in _65: _66.add("Запорожская область")
    if "херсон" in _65: _66.add("Херсонская область")
    return list(_66)

def _69(_70):
    _71 = str(_70).lower()
    if "отбой опасности бпла по всем" in _71: return "mass_clear_drone_danger"
    if "отбой ракетной опасности по всем" in _71: return "mass_clear_missile_danger"
    if "отбой ракетной тревоги по всем" in _71: return "mass_clear_missile_alert"
    if any(w in _71 for w in ["отбой","все спокойно","тихо"]): return "clear"
    if any(w in _71 for w in ["ракетная тревога","ракетно бомбовая"]): return "missile_alert"
    if "ракетная опасность" in _71: return "missile_danger"
    if any(w in _71 for w in ["работа пво","сбитие","атака бпла"]): return "drone_attack"
    if any(w in _71 for w in ["опасность по бпла","внимание"]): return "drone_danger"
    return None

def _72(_73, _74=None, _75="main", _76=None, _77=False):
    global _15, _16, _23
    if not _73: return False
    if _75 == "main" and _56(_73): return False
    if _61(_73): return False
    _78 = _69(_73)
    if _78 and _78.startswith("mass_clear_"):
        _79 = False
        if _78 == "mass_clear_drone_danger":
            for _80, _81 in list(_15.items()):
                if _81.get("status") == "drone_danger":
                    _15[_80] = {"status":"clear","last_update":D.now(TZ.utc).isoformat(),"message":"Отбой","source":_75}
                    _79 = True
        elif _78 == "mass_clear_missile_danger":
            for _80, _81 in list(_15.items()):
                if _81.get("status") == "missile_danger":
                    _15[_80] = {"status":"clear","last_update":D.now(TZ.utc).isoformat(),"message":"Отбой","source":_75}
                    _79 = True
        elif _78 == "mass_clear_missile_alert":
            for _80, _81 in list(_15.items()):
                if _81.get("status") == "missile_alert":
                    _15[_80] = {"status":"clear","last_update":D.now(TZ.utc).isoformat(),"message":"Отбой","source":_75}
                    _79 = True
        if _79 and not _77:
            _16.append({"region":"ВСЕ РЕГИОНЫ","status":"mass_clear","timestamp":D.now(TZ.utc).isoformat(),"message":_73[:500],"source":_75})
        return _79
    _82 = _63(_73)
    if not _82: return False
    if _75 == "dpr": _82 = [r for r in _82 if r in _14]
    if not _82: return False
    if not _78: return False
    _83 = _76.isoformat() if _76 and _76.tzinfo else D.now(TZ.utc).isoformat()
    _84 = _52(_73)
    _85 = False
    for _86 in _82:
        _15[_86] = {"status":_78,"last_update":_83,"message":_84[:500],"source":_75}
        _16.append({"region":_86,"status":_78,"timestamp":_83,"message":_84[:500],"source":_75})
        if len(_16) > 5000: _16.pop(0)
        _85 = True
    return _85

async def _87():
    global _20, _17, _18, _15
    _20 = TC(SS(_5), _3, _4)
    await _20.start()
    _36()
    _24()
    try:
        _88 = await _20.get_messages(_8, limit=200)
        if _88:
            _89 = sorted(_88, key=lambda x: x.id)
            _17 = _89[-1].id
            for _90 in _89:
                if _90.message and _90.id > _17 - 200:
                    _72(_90.message, _90.id, "main", _90.date, True)
                    await A.sleep(0.05)
    except: pass
    try:
        _91 = await _20.get_messages(_9, limit=200)
        if _91:
            _92 = sorted(_91, key=lambda x: x.id)
            _18 = _92[-1].id
            for _93 in _92:
                if _93.message and _93.id > _18 - 200:
                    _72(_93.message, _93.id, "dpr", _93.date, True)
                    await A.sleep(0.05)
    except: pass
    T.Thread(target=_47, daemon=True).start()
    T.Thread(target=_49, daemon=True).start()
    T.Thread(target=_51, daemon=True).start()
    while True:
        await A.sleep(30)
        try:
            _94 = await _20.get_messages(_8, limit=50)
            if _94:
                for _95 in reversed(_94):
                    if _95.id <= _17: continue
                    _17 = _95.id
                    if _95.message and _72(_95.message, _95.id, "main", _95.date):
                        pass
        except: pass
        try:
            _96 = await _20.get_messages(_9, limit=50)
            if _96:
                for _97 in reversed(_96):
                    if _97.id <= _18: continue
                    _18 = _97.id
                    if _97.message and _72(_97.message, _97.id, "dpr", _97.date):
                        pass
        except: pass

if __name__ == "__main__":
    A.run(_87())
