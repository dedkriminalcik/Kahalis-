"""
KAHALIS — один файл: Telegram-бот (aiogram) + API игры (aiohttp) + раздача игры (index.html).
Положи рядом index.html, requirements.txt и Procfile — больше ничего не нужно.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from urllib.parse import parse_qsl

from aiohttp import ClientSession, ClientTimeout, web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6188701923

logging.basicConfig(level=logging.INFO)

# Адрес игры: на Railway берётся автоматически из домена сервиса (игру раздаёт сам бот).
# Если домена ещё нет — запасной вариант (GitHub Pages).
_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
WEBAPP_URL = os.getenv("WEBAPP_URL") or (f"https://{_domain}/" if _domain else "https://dedkriminalcik.github.io/Kahalis-/")

# =====================================================================
# ===== API ИГРЫ (раньше лежало в game_api.py) =====
# =====================================================================

BOT_TOKEN = TOKEN or os.getenv("TOKEN") or ""
GAME_OWNER = str(os.getenv("OWNER_ID", "6188701923"))
PORT = int(os.getenv("PORT", "8080"))
DATA_FILE = os.getenv("DATA_FILE", "kahalis_data.json")
DEV = os.getenv("DEV") == "1"          # тест без Telegram: initData = "dev:ID:Имя"
UP_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UP_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

BOT = None
DB = {
    "users": {},
    "promos": {
        "BOBIK2026": {"c": 50000, "k": 500, "uses": 1000000, "used": {}},
        "KAHALIS": {"c": 50000, "k": 500, "uses": 1000000, "used": {}},
    },
    "event": None,
    "announce": "",
    "logs": [],
    "paid": {},
    "tr": {},
}
_dirty = False

# vip и premium — только значки и бонус к доходу, к консоли доступа не дают
LV = {"pilot": 0, "vip": 0, "premium": 0, "moderator": 1, "admin": 2, "owner": 3}
CAP = {"credits": 100000, "crystals": 1000, "parts": 50, "lvl": 5}
SKUS = {
    "coins25": {"title": "25 000 монет", "stars": 25, "give": [("credits", 25000)]},
    "coins100": {"title": "200 000 монет", "stars": 100, "give": [("credits", 200000)]},
    "cr25": {"title": "1 000 алмазов", "stars": 25, "give": [("crystals", 1000)]},
    "cr100": {"title": "8 000 алмазов", "stars": 100, "give": [("crystals", 8000)]},
    "pass": {"title": "Премиум баттлпасс", "stars": 500, "give": [("premium", 1)]},
}


def save():
    global _dirty
    _dirty = True


def log(who, text):
    DB["logs"].append({"t": int(time.time() * 1000), "u": who, "x": text})
    if len(DB["logs"]) > 400:
        DB["logs"].pop(0)
    save()


# ---------------------------------------------------------------- хранение
async def _upstash(cmd):
    async with ClientSession(timeout=ClientTimeout(total=15)) as s:
        async with s.post(
            UP_URL, json=cmd, headers={"Authorization": "Bearer " + UP_TOKEN}
        ) as r:
            return await r.json(content_type=None)


async def load_db():
    global DB
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            DB.update(json.load(f))
    except Exception:
        pass
    if UP_URL:
        try:
            j = await _upstash(["GET", "kahalis_db"])
            if j and j.get("result"):
                DB.update(json.loads(j["result"]))
                print("Kahalis: база загружена из Upstash")
        except Exception as e:
            print("Kahalis upstash load:", e)


async def flush():
    txt = json.dumps(DB, ensure_ascii=False)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(txt)
    except Exception:
        pass
    if UP_URL:
        try:
            await _upstash(["SET", "kahalis_db", txt])
        except Exception as e:
            print("Kahalis upstash save:", e)


async def _saver():
    global _dirty
    while True:
        await asyncio.sleep(5)
        if _dirty:
            _dirty = False
            await flush()


# ---------------------------------------------------------------- игроки
def get_user(uid, name=None):
    uid = str(uid)
    u = DB["users"].get(uid)
    if not u:
        u = DB["users"][uid] = {
            "id": uid, "name": name or "Пилот", "lvl": 1, "credits": 0,
            "role": "pilot", "banned": "", "warns": [], "refs": [], "refBy": "",
            "inbox": [], "created": int(time.time() * 1000), "seen": int(time.time() * 1000),
        }
        save()
    if uid == GAME_OWNER:
        u["role"] = "owner"
    return u


def role_lv(u):
    return 3 if u["id"] == GAME_OWNER else LV.get(u["role"], 0)


def give(uid, kind, amount, note=""):
    u = DB["users"].get(str(uid))
    if not u:
        return False
    u["inbox"].append({
        "id": secrets.token_hex(5), "kind": kind,
        "amount": int(float(amount or 0)), "note": note,
    })
    if len(u["inbox"]) > 200:
        u["inbox"].pop(0)
    save()
    return True


def verify(init):
    """Проверка подписи Telegram Mini App."""
    if not init:
        return None
    if DEV and str(init).startswith("dev:"):
        p = str(init).split(":")
        return {"id": p[1], "first_name": p[2] if len(p) > 2 else "Dev"}
    if not BOT_TOKEN:
        return None
    try:
        pairs = dict(parse_qsl(init, keep_blank_values=True))
        h = pairs.pop("hash", "")
        data = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, h):
            return None
        if time.time() - int(pairs.get("auth_date", "0")) > 86400 * 7:
            return None
        return json.loads(pairs["user"])
    except Exception:
        return None


# ---------------------------------------------------------------- обработчики
def h_sync(u, b):
    u["name"] = str(b.get("name") or u["name"])[:32]
    u["lvl"] = max(1, min(9999, int(b.get("lvl") or u["lvl"])))
    u["credits"] = max(0, min(10 ** 15, int(float(b.get("credits") or 0))))
    u["seen"] = int(time.time() * 1000)
    ref = str(b.get("ref") or "")
    if (
        ref and not u["refBy"] and ref != u["id"] and ref in DB["users"]
        and time.time() * 1000 - u["created"] < 3 * 86400000
    ):
        inv = DB["users"][ref]
        if inv["refBy"] != u["id"]:
            u["refBy"] = inv["id"]
            if u["id"] not in inv["refs"]:
                inv["refs"].append(u["id"])
            give(u["id"], "credits", 15000, "🎁 Бонус новичка: +15,000 🪙")
            give(u["id"], "crystals", 30)
            give(u["id"], "parts", 5)
            give(inv["id"], "msg", 0, f"👥 Новый друг: {u['name']}! Награды — в профиле")
            log(u["name"], f"пришёл по ссылке {inv['name']} ({inv['id']})")
    ev = DB.get("event")
    if ev and ev["until"] <= time.time() * 1000:
        DB["event"] = None
        save()
    return {
        "ok": True, "role": u["role"], "banned": u["banned"], "announce": DB["announce"],
        "event": DB["event"], "refs": u["refs"], "inbox": u["inbox"][:50],
        "serverTime": int(time.time() * 1000),
    }


def h_ack(u, b):
    ids = set(b.get("ids") or [])
    u["inbox"] = [i for i in u["inbox"] if i["id"] not in ids]
    save()
    return {"ok": True}


def h_top(u, b):
    lst = sorted(
        (x for x in DB["users"].values() if not x["banned"]),
        key=lambda x: (x["lvl"], x["credits"]), reverse=True,
    )[:20]
    return {"ok": True, "top": [{"name": x["name"], "lvl": x["lvl"], "credits": x["credits"]} for x in lst]}


def h_transfer(u, b):
    to = str(b.get("to") or "")
    try:
        a = int(float(b.get("amount")))
    except Exception:
        a = 0
    if not (to.isdigit() and 5 <= len(to) <= 15) or a <= 0 or a > 10 ** 7:
        return {"ok": False, "error": "Неверные данные"}
    if to == u["id"]:
        return {"ok": False, "error": "Нельзя себе"}
    r = DB["users"].get(to)
    if not r:
        return {"ok": False, "error": "Игрок ещё не заходил в игру"}
    if r["banned"]:
        return {"ok": False, "error": "Получатель заблокирован"}
    give(to, "credits", a, f"💸 Перевод от {u['name']}: +{a:,} 🪙".replace(",", " "))
    log(u["name"], f"перевод {a} → {r['name']} ({to})")
    return {"ok": True}


def h_promo(u, b):
    code = str(b.get("code") or "").strip().upper()
    p = DB["promos"].get(code)
    if not p:
        return {"ok": False, "error": "Неверный промокод"}
    if u["id"] in p["used"]:
        return {"ok": False, "error": "Ты уже использовал этот промокод"}
    if p["uses"] <= 0:
        return {"ok": False, "error": "Промокод закончился"}
    p["uses"] -= 1
    p["used"][u["id"]] = 1
    if p["c"]:
        give(u["id"], "credits", p["c"])
    if p["k"]:
        give(u["id"], "crystals", p["k"])
    save()
    return {"ok": True, "c": p["c"], "k": p["k"]}


async def h_invoice(u, b):
    s = SKUS.get(b.get("sku"))
    if not s:
        return {"ok": False, "error": "Нет такого товара"}
    if BOT is None:
        return {"ok": False, "error": "Бот не подключён к API"}
    from aiogram.types import LabeledPrice

    try:
        url = await BOT.create_invoice_link(
            title=s["title"],
            description=s["title"] + " для игры Kahalis",
            payload=json.dumps({"u": u["id"], "sku": b["sku"]}),
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=s["title"], amount=s["stars"])],
        )
        return {"ok": True, "url": url}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


async def game_payment(message) -> bool:
    """Вызывается из твоего successful_payment. Возвращает True, если платёж — за игру."""
    sp = message.successful_payment
    try:
        info = json.loads(sp.invoice_payload)
    except Exception:
        return False
    if not isinstance(info, dict) or info.get("sku") not in SKUS:
        return False
    cid = sp.telegram_payment_charge_id
    if cid in DB["paid"]:
        return True
    DB["paid"][cid] = 1
    s = SKUS[info["sku"]]
    uid = str(info.get("u") or message.from_user.id)
    get_user(uid, message.from_user.first_name)
    for kind, amount in s["give"]:
        give(uid, kind, amount, f"⭐ Покупка: {s['title']}")
    log("Stars", f"{uid} купил {info['sku']}")
    save()
    await message.answer("✅ Покупка зачислена! Открой игру — награда уже ждёт.")
    return True


def grant(uid, name, kind, amount, note=""):
    """Начислить игроку подарок в игру (для твоих старых покупок в боте)."""
    get_user(uid, name)
    give(uid, kind, amount, note)
    save()


def h_admin(u, b):
    lv = role_lv(u)
    act = str(b.get("action") or "")

    def fail(e):
        return {"ok": False, "error": e}

    def target():
        return DB["users"].get(str(b.get("to") or ""))

    if lv < 1:
        return fail("Нет прав")

    if act == "stats":
        allu = list(DB["users"].values())
        now = time.time() * 1000
        return {
            "ok": True, "players": len(allu),
            "online": sum(1 for x in allu if now - x["seen"] < 300000),
            "banned": sum(1 for x in allu if x["banned"]),
            "credits": sum(x["credits"] for x in allu),
            "event": DB["event"]["name"] if DB["event"] else None,
        }
    if act == "lookup":
        t = target()
        if not t:
            return fail("Игрок не найден")
        return {"ok": True, "user": {
            "id": t["id"], "name": t["name"], "lvl": t["lvl"], "credits": t["credits"],
            "role": t["role"], "banned": t["banned"], "warns": len(t["warns"]),
            "refs": len(t["refs"]), "refBy": t["refBy"], "seen": t["seen"], "created": t["created"],
        }}
    if act == "logs":
        return {"ok": True, "logs": list(reversed(DB["logs"][-60:]))}
    if act == "warn":
        t = target()
        if not t:
            return fail("Игрок не найден")
        if role_lv(t) >= lv:
            return fail("Нельзя: роль не ниже вашей")
        reason = str(b.get("reason") or "Нарушение правил")[:100]
        t["warns"].append({"r": reason, "by": u["name"], "t": int(time.time() * 1000)})
        give(t["id"], "msg", 0, f"⚠️ Предупреждение: {reason}")
        log(u["name"], f"предупреждение {t['name']} ({t['id']})")
        return {"ok": True}
    if act in ("ban", "unban"):
        if lv < 2:
            return fail("Нет прав")
        t = target()
        if not t:
            return fail("Игрок не найден")
        if role_lv(t) >= lv:
            return fail("Нельзя: роль не ниже вашей")
        t["banned"] = str(b.get("reason") or "Нарушение правил")[:100] if act == "ban" else ""
        log(u["name"], f"{act} {t['name']} ({t['id']}) {t['banned']}")
        save()
        return {"ok": True}
    if act == "give":
        if lv < 2:
            return fail("Нет прав")
        t = target()
        if not t:
            return fail("Игрок не найден")
        kind = str(b.get("kind"))
        try:
            a = int(float(b.get("amount")))
        except Exception:
            a = 0
        if a <= 0 and kind not in ("ship", "galaxy"):
            return fail("Укажи количество")
        if kind in CAP:
            if lv < 3 and a > CAP[kind]:
                return fail(f"Лимит админа: {CAP[kind]}")
            give(t["id"], kind, a, f"🎁 От администрации: +{a} ({kind})")
        elif kind in ("ship", "galaxy"):
            if lv < 3:
                return fail("Только владелец")
            give(t["id"], kind, a, "🎁 Подарок от администрации: " + ("корабль" if kind == "ship" else "галактика"))
        else:
            return fail("Неизвестный тип")
        log(u["name"], f"give {kind} {a} → {t['name']} ({t['id']})")
        return {"ok": True}
    if act == "take":
        if lv < 3:
            return fail("Только владелец")
        t = target()
        if not t:
            return fail("Игрок не найден")
        try:
            a = int(float(b.get("amount")))
        except Exception:
            a = 0
        if a <= 0:
            return fail("Укажи количество")
        give(t["id"], str(b.get("kind")), -a, f"⚠️ Списано администрацией: {a}")
        log(u["name"], f"take {b.get('kind')} {a} ← {t['name']} ({t['id']})")
        return {"ok": True}
    if act == "reset":
        if lv < 3:
            return fail("Только владелец")
        t = target()
        if not t:
            return fail("Игрок не найден")
        give(t["id"], "reset", 1, "♻️ Прогресс сброшен администрацией")
        log(u["name"], f"reset {t['name']} ({t['id']})")
        return {"ok": True}
    if act == "role":
        if lv < 2:
            return fail("Нет прав")
        t = target()
        if not t:
            return fail("Игрок не найден")
        r = str(b.get("role"))
        if r not in LV:
            return fail("Нет такой роли")
        if t["id"] == GAME_OWNER:
            return fail("Роль владельца менять нельзя")
        if lv < 3 and (r in ("admin", "owner") or role_lv(t) >= 2):
            return fail("Админ может назначать только VIP, премиум и модераторов")
        t["role"] = r
        log(u["name"], f"роль {r} → {t['name']} ({t['id']})")
        give(t["id"], "msg", 0, f"🛡 Тебе назначена роль: {r}")
        save()
        return {"ok": True}
    if act == "announce":
        if lv < 2:
            return fail("Нет прав")
        DB["announce"] = str(b.get("text") or "")[:200]
        log(u["name"], "объявление: " + DB["announce"])
        save()
        return {"ok": True}
    if act == "event_start":
        if lv < 2:
            return fail("Нет прав")
        try:
            m = max(1, min(100, float(b.get("m") or 1)))
            mins = max(1, min(1440, int(float(b.get("min") or 10))))
        except Exception:
            return fail("Неверные данные")
        if lv < 3 and (m > 2 or mins > 30):
            return fail("Лимит админа: до x2 и 30 минут")
        fx = b.get("fx") if b.get("fx") in ("none", "rain", "snow", "stars", "confetti", "fire") else "none"
        nick = b.get("nick") if b.get("nick") in ("none", "rainbow", "glow", "gold") else "none"
        DB["event"] = {
            "name": str(b.get("name") or "Ивент")[:40], "m": m, "fx": fx, "nick": nick,
            "track": str(b.get("track") or "")[:300], "txt": str(b.get("text") or "")[:200],
            "until": int(time.time() * 1000) + mins * 60000,
        }
        if DB["event"]["txt"]:
            DB["announce"] = DB["event"]["txt"]
        log(u["name"], f"ивент «{DB['event']['name']}» x{m} на {mins} мин")
        save()
        return {"ok": True}
    if act == "event_stop":
        if lv < 2:
            return fail("Нет прав")
        if DB["event"] and DB["announce"] == DB["event"].get("txt"):
            DB["announce"] = ""
        DB["event"] = None
        log(u["name"], "ивент остановлен")
        save()
        return {"ok": True}
    if act == "promo_add":
        if lv < 2:
            return fail("Нет прав")
        code = "".join(ch for ch in str(b.get("code") or "").upper() if ch.isalnum() or ch == "_")[:24]
        try:
            c = max(0, int(float(b.get("c") or 0)))
            k = max(0, int(float(b.get("k") or 0)))
            uses = max(1, min(10 ** 6, int(float(b.get("uses") or 1))))
        except Exception:
            return fail("Неверные данные")
        if not code or (not c and not k):
            return fail("Укажи код и награду")
        if lv < 3 and (c > 100000 or k > 1000):
            return fail("Лимит админа: 100,000 🪙 / 1,000 💎")
        DB["promos"][code] = {"c": c, "k": k, "uses": uses, "used": {}}
        log(u["name"], f"промокод {code}: {c}🪙 {k}💎 x{uses}")
        save()
        return {"ok": True}
    if act == "promo_del":
        if lv < 2:
            return fail("Нет прав")
        DB["promos"].pop(str(b.get("code") or "").upper(), None)
        save()
        return {"ok": True}
    if act == "promo_list":
        return {"ok": True, "promos": [
            {"code": c, "c": p["c"], "k": p["k"], "uses": p["uses"], "used": len(p["used"])}
            for c, p in DB["promos"].items()
        ]}
    if act == "giveall":
        if lv < 3:
            return fail("Только владелец")
        kind = str(b.get("kind"))
        try:
            a = int(float(b.get("amount")))
        except Exception:
            a = 0
        if kind not in ("credits", "crystals", "parts") or a <= 0 or a > 10 ** 7:
            return fail("Неверные данные")
        for x in DB["users"].values():
            give(x["id"], kind, a, f"🎁 Подарок всем игрокам: +{a} ({kind})")
        log(u["name"], f"giveall {kind} {a}")
        return {"ok": True}
    return fail("Неизвестное действие")


HANDLERS = {
    "sync": h_sync, "ack": h_ack, "top": h_top, "transfer": h_transfer,
    "promo": h_promo, "invoice": h_invoice, "admin": h_admin,
}


# ---------------------------------------------------------------- перевод интерфейса
async def h_i18n(b):
    lang = str(b.get("lang") or "en")[:10]
    texts = [str(t)[:300] for t in (b.get("texts") or [])[:60]]
    out = []
    async with ClientSession(timeout=ClientTimeout(total=12)) as s:
        for t in texts:
            key = lang + "|" + t
            if key not in DB["tr"]:
                try:
                    async with s.get(
                        "https://translate.googleapis.com/translate_a/single",
                        params={"client": "gtx", "sl": "ru", "tl": lang, "dt": "t", "q": t},
                    ) as r:
                        j = await r.json(content_type=None)
                    DB["tr"][key] = "".join(p[0] for p in j[0])
                    save()
                except Exception:
                    return {"ok": False}
            out.append(DB["tr"][key])
    return {"ok": True, "texts": out}


# ---------------------------------------------------------------- HTTP
@web.middleware
async def cors_mw(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        try:
            resp = await handler(request)
        except web.HTTPException as e:
            resp = e
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return resp


async def index(request):
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(f):
        return web.FileResponse(f)
    return web.json_response({"ok": True, "name": "kahalis-api"})


async def health(request):
    return web.json_response({"ok": True, "players": len(DB["users"])})


async def handle(request):
    name = request.match_info["name"]
    if request.method != "POST":
        return web.json_response({"ok": False, "error": "POST only"}, status=405)
    try:
        b = await request.json()
    except Exception:
        b = {}
    if name == "i18n":
        return web.json_response(await h_i18n(b))
    tu = verify(b.get("initData"))
    if not tu:
        return web.json_response({"ok": False, "error": "Вход не подтверждён"}, status=401)
    u = get_user(tu["id"], tu.get("first_name") or tu.get("username"))
    if u["banned"] and name != "sync":
        return web.json_response({"ok": False, "error": "Аккаунт заблокирован"}, status=403)
    fn = HANDLERS.get(name)
    if not fn:
        return web.json_response({"ok": False, "error": "Нет такого запроса"}, status=404)
    try:
        out = fn(u, b)
        if asyncio.iscoroutine(out):
            out = await out
        return web.json_response(out)
    except Exception as e:  # не роняем бота из-за ошибки в игре
        print("Kahalis API error:", repr(e))
        return web.json_response({"ok": False, "error": "Ошибка сервера"}, status=500)


async def start_api(bot):
    """Запускает API рядом с ботом (в том же процессе)."""
    global BOT
    BOT = bot
    await load_db()
    app = web.Application(middlewares=[cors_mw], client_max_size=2 * 1024 * 1024)
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_route("*", "/{name}", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    asyncio.create_task(_saver())
    print(f"Kahalis API запущен на порту {PORT}")


# =====================================================================
# ===== TELEGRAM-БОТ =====
# =====================================================================
async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        is_owner = (message.from_user.id == OWNER_ID)
        keyboard = [
            [InlineKeyboardButton(text="🚀 Запустить KAHALIS RPG", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="⭐ Купить кредиты за Telegram Stars", callback_data="buy_stars_menu")]
        ]
        if is_owner:
            keyboard.insert(0, [InlineKeyboardButton(text="⚙️ Консоль владельца", callback_data="owner_console")])

        await message.answer(
            "🌌 **Космический терминал KAHALIS:**\n\n"
            "Добро пожаловать в сектор! Выберите действие:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )

    @dp.callback_query(F.data == "owner_console")
    async def owner_console(call: CallbackQuery):
        # Консоль теперь находится прямо в игре: вкладка ⚙️ «Консоль» (видна владельцу, админам и модераторам)
        await call.message.answer(
            "⚙️ **Консоль владельца** — в игре, вкладка «Консоль».\n"
            "Там: роли по ID, выдача игрокам, баны, промокоды, ивенты, рейтинг и журнал.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Открыть игру", web_app=WebAppInfo(url=WEBAPP_URL))]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "buy_stars_menu")
    async def stars_menu(call: CallbackQuery):
        await call.message.edit_text(
            "⭐ **Магазин Telegram Stars:**\nВыберите пакет для покупки за звезды:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ 100 Stars (= 5,000 🪙)", callback_data="pay_star_100")],
                [InlineKeyboardButton(text="⭐ 500 Stars (= 30,000 🪙)", callback_data="pay_star_500")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "pay_star_100")
    async def pay_100(call: CallbackQuery):
        prices = [LabeledPrice(label="100 Telegram Stars", amount=100)]
        await call.message.answer_invoice(
            title="Пакет кредитов [100 Stars]",
            description="Дает 5,000 кредитов 🪙 на баланс в KAHALIS RPG.",
            prices=prices,
            provider_token="",
            payload="stars_100_pack",
            currency="XTR",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Оплатить 100 Stars", pay=True)],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="buy_stars_menu")]
            ])
        )
        await call.answer()

    @dp.callback_query(F.data == "pay_star_500")
    async def pay_500(call: CallbackQuery):
        prices = [LabeledPrice(label="500 Telegram Stars", amount=500)]
        await call.message.answer_invoice(
            title="Пакет кредитов [500 Stars]",
            description="Дает 30,000 кредитов 🪙 на баланс в KAHALIS RPG.",
            prices=prices,
            provider_token="",
            payload="stars_500_pack",
            currency="XTR",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Оплатить 500 Stars", pay=True)],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="buy_stars_menu")]
            ])
        )
        await call.answer()

    @dp.pre_checkout_query()
    async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @dp.message(F.successful_payment)
    async def successful_payment(message: Message):
        # 1) покупки, оформленные внутри игры (кнопка ⭐ в магазине игры)
        if await game_payment(message):
            return
        # 2) покупки через меню бота — теперь реально зачисляются в игру
        payment_info = message.successful_payment
        reward = 5000 if payment_info.invoice_payload == "stars_100_pack" else 30000
        grant(message.from_user.id, message.from_user.first_name, "credits", reward, f"⭐ Покупка: +{reward} 🪙")
        await message.answer(f"🎉 **Оплата прошла успешно!**\nВам начислено +{reward} 🪙. Зайдите в Mini App!", parse_mode="Markdown")

    @dp.callback_query(F.data == "menu_main")
    async def back_to_main(call: CallbackQuery):
        is_owner = (call.from_user.id == OWNER_ID)
        keyboard = [
            [InlineKeyboardButton(text="🚀 Запустить KAHALIS RPG", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="⭐ Купить кредиты за Telegram Stars", callback_data="buy_stars_menu")]
        ]
        if is_owner:
            keyboard.insert(0, [InlineKeyboardButton(text="⚙️ Консоль владельца", callback_data="owner_console")])
        await call.message.edit_text("🌌 **Космический терминал KAHALIS:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

    await start_api(bot)  # запускаем API игры рядом с ботом
    print("🚀 Бот запущен со звёздами!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
