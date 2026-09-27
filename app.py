# -*- coding: utf-8 -*-
"""
✨ UNICORN ANONY BOT — ROYAL EDITION ✨
"""

import os, re, csv, io, json, random, asyncio, logging, time
from datetime import datetime, timedelta, timezone

import socks, requests, psycopg2, psycopg2.extras
from aiohttp import web
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.errors import MessageNotModifiedError, FloodWaitError

load_dotenv()

API_ID = int(os.getenv("API_ID", "6") or 6)
API_HASH = os.getenv("API_HASH", "eb06d4abfb49dc3eeb1aeb98ae0f581e").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

_admins_str = os.getenv("ADMIN_IDS", "").strip()
EXTRA_ADMINS = [int(x) for x in _admins_str.split(",") if x.strip().isdigit()]
ALL_ADMINS = set([OWNER_ID] + EXTRA_ADMINS)
ALL_ADMINS.discard(0)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL and "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = DATABASE_URL + sep + "sslmode=require"

SESSION_NAME = os.getenv("SESSION_NAME", "anony_bot_session")
PROXY_HOST = os.getenv("PROXY_HOST", "").strip()
PROXY_PORT = int(os.getenv("PROXY_PORT", "0") or 0)
PORT = int(os.getenv("PORT", "10000"))
IRAN_TZ = timezone(timedelta(hours=3, minutes=30))
BOT_USERNAME = ""

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("UnicornBot")
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

PREMIUM = {
    "laugh": "5368324170671202286", "joy": "5780769611324455942",
    "heart": "5443038326535759644", "party": "5456359790390093750",
    "sparkle": "5404654051945521778", "star": "6337048821603763745",
    "check": "5206607081334906820", "cross": "5210952531676504517",
    "user": "5443038326535759644", "id": "5397782960512444700",
    "tag": "5436113877181941026", "crown": "5458603043203327669",
    "group": "5447410659077661506", "pin": "5397782960512444700",
    "time": "5458603043203327669", "info": "5323442290708985472",
    "warning": "5447644880824181073", "alert": "5447644880824181073",
    "shield": "5397782960512444700", "list": "5447410659077661506",
    "stats": "5231200819986047254", "message": "5443038326535759644",
    "link": "5271604874419647061", "rocket": "5424972470023104089",
    "fire": "5424972470023104089", "trophy": "5458603043203327669",
    "magic": "5404654051945521778", "diamond": "5404654051945521778",
    "lock": "5397782960512444700", "wave": "5368324170671202286",
    "point": "5436113877181941026", "hourglass": "5458603043203327669",
    "gift": "5456359790390093750", "chart": "5231200819986047254",
    "search": "5271604874419647061", "share": "5271604874419647061",
    "export": "5447410659077661506", "vote": "5206607081334906820",
    "flag": "5447644880824181073", "target": "5424972470023104089",
    "brain": "5404654051945521778", "gamepad": "5424972470023104089",
    "bolt": "5424972470023104089", "gem": "5404654051945521778",
    "book": "5447410659077661506", "ball": "5424972470023104089",
    "globe": "5271604874419647061", "movie": "5443038326535759644",
    "music": "5456359790390093750", "laptop": "5404654051945521778",
    "medal": "5458603043203327669", "skip": "5424972470023104089",
}


def E(key, fallback):
    eid = PREMIUM.get(key)
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback


DIV = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
DIV2 = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"

_TG_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="\d+">([^<]*)</tg-emoji>')


def strip_premium(text):
    return _TG_EMOJI_RE.sub(r"\1", text)


def _emoji_err(ex):
    s = str(ex).lower()
    return ("document" in s) or ("invalid" in s and "inline" in s)


async def safe_reply(event, text, **kw):
    try:
        return await event.reply(text, **kw)
    except Exception as ex:
        if _emoji_err(ex):
            return await event.reply(strip_premium(text), **kw)
        raise


async def safe_send(peer, text, **kw):
    try:
        return await client.send_message(peer, text, **kw)
    except Exception as ex:
        if _emoji_err(ex):
            return await client.send_message(peer, strip_premium(text), **kw)
        raise


async def safe_respond(event, text, **kw):
    try:
        return await event.respond(text, **kw)
    except Exception as ex:
        if _emoji_err(ex):
            return await event.respond(strip_premium(text), **kw)
        raise


async def safe_edit(event, text, **kw):
    try:
        return await event.edit(text, **kw)
    except MessageNotModifiedError:
        return None
    except Exception as ex:
        if _emoji_err(ex):
            try:
                return await event.edit(strip_premium(text), **kw)
            except MessageNotModifiedError:
                return None
        raise


async def safe_edit_msg(chat_id, msg_id, text, buttons=None, max_retry=3):
    for attempt in range(max_retry):
        try:
            await client.edit_message(chat_id, msg_id, text=text,
                                       buttons=buttons, parse_mode="html")
            return True
        except MessageNotModifiedError:
            return True
        except FloodWaitError as fwe:
            wait = fwe.seconds
            logger.warning(f"🚦 flood wait {wait}s (try {attempt+1})")
            if wait > 10:
                return False
            await asyncio.sleep(wait + 1)
        except Exception as e:
            logger.warning(f"edit try{attempt+1}/{max_retry}: {type(e).__name__}: {str(e)[:80]}")
            if "message to edit not found" in str(e).lower():
                return False
            await asyncio.sleep(0.5)
    return False


def h(t):
    if t is None:
        return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def now_str():
    return datetime.now(IRAN_TZ).strftime("%Y/%m/%d - %H:%M:%S")


def now_iso():
    return datetime.now(IRAN_TZ).isoformat()


def user_name(u):
    if not u:
        return "ناشناس"
    n = getattr(u, "first_name", "") or ""
    l = getattr(u, "last_name", "") or ""
    full = (n + " " + l).strip()
    return full or getattr(u, "username", None) or str(getattr(u, "id", "?"))


def is_admin(uid):
    return uid in ALL_ADMINS


def parse_duration(text):
    if not text:
        return None
    t = str(text).strip().lower()
    if t in ("", "0", "-", "نه", "ندارد", "بدون", "skip", "none", "خالی"):
        return None
    m = re.match(r"^(\d+)\s*(m|min|mins|د|دقیقه|h|hr|hrs|س|ساعت|d|day|days|روز)?$", t)
    if not m:
        return None
    n = int(m.group(1))
    unit = (m.group(2) or "m").strip()
    if unit in ("m", "min", "mins", "د", "دقیقه"):
        return timedelta(minutes=n)
    if unit in ("h", "hr", "hrs", "س", "ساعت"):
        return timedelta(hours=n)
    if unit in ("d", "day", "days", "روز"):
        return timedelta(days=n)
    return timedelta(minutes=n)


def time_bar_colored(remaining, total, width=18):
    if total <= 0:
        return "⬜" * width
    pct = max(0, min(100, int(100 * remaining / total)))
    filled = int(pct / 100 * width)
    empty = width - filled
    if pct > 60:
        return "🟩" * filled + "⬜" * empty
    elif pct > 30:
        return "🟨" * filled + "⬜" * empty
    else:
        return "🟥" * filled + "⬜" * empty


def time_badge(remaining, total):
    if total <= 0:
        return "⚪"
    pct = remaining / total * 100
    if pct > 60:
        return "🟢"
    elif pct > 30:
        return "🟡"
    else:
        return "🔴"


MAX_ANSWER_LEN = 1500

TEMPLATES = [
    ("💎 صادق‌ترین نظرت", "صادق‌ترین نظرت درباره من چیه؟"),
    ("💎 بدترین خصلت من", "بدترین خصلت من چیه که باید تغییرش بدم؟"),
    ("💎 بهترین خاطره", "بهترین خاطره‌ای که با من داری چیه؟"),
    ("💎 اولین برداشت", "اولین برداشتی که از من داشتی چی بود؟"),
    ("💎 اگه یه آرزو", "اگه یه آرزو داشتی، چی بود؟"),
    ("💎 راز نگفته", "چی رو همیشه می‌خواستی بهم بگی ولی نگفتی؟"),
]

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

AI_MODELS = [
    "openai/gpt-oss-120b", "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.1-8b-instant",
]

QUIZ_CATEGORIES = [
    ("book", "📖", "تاریخی"), ("ball", "⚽", "ورزشی"),
    ("star", "🌟", "دینی"), ("bolt", "⚡", "علمی"),
    ("globe", "🌍", "جغرافیایی"), ("movie", "🎬", "سینما"),
    ("music", "🎵", "موسیقی"), ("book", "📚", "ادبیات"),
    ("laptop", "💻", "فناوری"), ("brain", "🧠", "عمومی"),
]

QUIZ_TIME_OPTIONS = [15, 30, 45, 60]
QUIZ_Q_OPTIONS = [3, 5, 7, 10]
QUIZ_TARGET_OPTIONS = [0, 5, 10, 15, 20]

TD_CATEGORIES_ALL = [
    ("truth", "🎭", "حقیقت"), ("truth18", "🔥", "حقیقت +18"),
    ("dare", "⚡", "جرعت"), ("dare18", "💋", "جرعت +18"),
]
TD_TURNS_OPTIONS = [1, 2, 3, 5]
TD_TIMEOUT_OPTIONS = [30, 60, 120, 180]

TD_BANK = {
    "truth": [
        "آخرین باری که از ته دل گریه کردی کی بود و چرا؟",
        "اگه یه روز نامرئی می‌شدی، اولین کاری که می‌کردی چی بود؟",
        "کدوم آهنگ رو وقتی غمگینی همیشه گوش می‌دی؟",
        "یه راز که هیچ‌کس توی این گروه نمی‌دونه رو بگو.",
        "بدترین دروغی که تا حالا به مامانت گفتی چی بود؟",
        "آخرین باری که یه دوستت رو به خاطر یه چیز مسخره از دست دادی کی بود؟",
        "اگه فقط ۲۴ ساعت می‌تونستی توی بدن یکی دیگه باشی، کی رو انتخاب می‌کردی؟",
        "چیزی که همیشه می‌خواستی به یه نفر بگی ولی جراتش رو نداشتی چیه؟",
        "توی کل زندگیت، بیشترین پولی که یهو خرج یه چیز بی‌خودی کردی چقدر بود؟",
        "بدترین ویژگی که توی خودت داری و می‌دونی چیه؟",
        "اگه بخوای یکی از اعضای این گروه رو حذف کنی، کی رو انتخاب می‌کنی؟",
        "آخرین باری که یه کار خیلی احمقانه کردی و پشیمون شدی چی بود؟",
        "بدترین چیز درباره اولین روز مدرسه/دانشگاهت چی بود؟",
        "کدوم عادت بدت رو هیچ‌کس نمی‌دونه؟",
        "چیزی که داری ولی قدرش رو نمی‌دونی چیه؟",
        "اگه بخوای یه شخصیت کارتونی باشی، کی رو انتخاب می‌کنی؟",
        "بدترین خاطره‌ای که داری چیه؟",
        "چیزی که هیچ‌وقت به هیچ‌کس نگفتی چیه؟",
        "آخرین باری که به یه نفر حسادت کردی کی بود؟",
        "بزرگترین ترست چیه؟",
    ],
    "truth18": [
        "تا حالا عاشق کسی شدی که نباید می‌شد؟",
        "بدترین کراش زندگیت کی بود؟",
        "آخرین بار کی به یکی از اعضای این گروه فکر بد کردی؟",
        "اگه یه شب مخفیانه می‌تونستی با یه نفر باشی، کی رو انتخاب می‌کردی؟",
        "چیزی که هیچ‌وقت به هیچ‌کس نگفتی از رابطه‌هات چیه؟",
        "بدترین دیتی که توی زندگیت رفتی چطور بود؟",
        "اگه بخوای با یکی از اعضای این گروه قرار بذاری، کی رو انتخاب می‌کنی؟",
        "توی یه رابطه، چیزی که باعث می‌شه سریع ازش بزنی چیه؟",
        "آخرین بار کی به یه نفر خیانت کردی (عاطفی یا هر نوع)؟",
        "مخفیانه بیشتر از همه توی این گروه به کی اهمیت می‌دی؟",
        "اسم اولین کراشت و یه خاطره ازش بگو.",
        "بدترین پیامی که تو زندگیت فرستادی چی بود؟",
        "چند تا از اعضای این گروه رو تو خیالت تصور کردی؟",
        "بدترین قرار عاشقانه‌ای که رفتی چطور بود؟",
    ],
    "dare": [
        "یه ویس ۱۵ ثانیه‌ای بفرست که با آهنگ مورد علاقه‌ت می‌رقصی و آواز می‌خونی!",
        "پروفایلت رو برای ۱ ساعت بذار عکس خنده‌دار خودت!",
        "به یه نفر توی مخاطبینت که ۳ ماه باهاش حرف نزدی، بگو «دلم برات تنگ شده بود». نتیجه رو اسکرین بفرست!",
        "اسم یه چیز عجیب که همیشه توی جیبت داری رو بگو!",
        "اسم ۳ نفر از اعضای گروه رو به ترتیب اولویت از بد به خوب بگو!",
        "توی گروه ۱۰ تا استیکر رندوم پشت سر هم بفرست!",
        "یه جمله عاشقانه واسه اولین نفر توی مخاطبینت بفرست!",
        "با صدای بلند یه شعر یا جمله معروف رو با استایل خنده‌دار بخون و ویس بفرست!",
        "برای یه عضو دیگه‌ی گروه یه شعر بساز (۴ خط) و همونجا بفرست!",
        "اسم یه کار احمقانه که بچگی می‌کردی و الان یادت میاد رو بگو!",
        "پروفایل یه نفر از اعضای گروه رو یه بار کپی کن!",
        "۵ پیام آخرت توی یه چت رندوم رو کپی کن و توی گروه بفرست!",
    ],
    "dare18": [
        "به یه نفر توی مخاطبینت که ۶ ماه باهاش حرف نزدی، بگو «تو همیشه توی فکر منی». اسکرین بفرست!",
        "به یکی از اعضای گروه یه پیام با تیکه‌ی جسورانه بفرست!",
        "اسم اولین کراش زندگیت و یه خاطره ازش رو تعریف کن!",
        "به یه نفر که خوشت میاد (ولی بهش نگفتی) توی گروه یه تیکه بنداز که بفهمه!",
        "توی گروه بگو از بین اعضا کی رو بیشتر از همه دوست داری و چرا!",
        "اسم یه کاری که فقط توی خیالت انجام دادی و جراتش رو نداری بگو!",
        "توی گروه بگو بدترین دروغی که به یه دختر/پسر گفتی چی بود!",
        "به یکی از اعضای گروه که باهاش صمیمی‌تر از همه‌ای بگو «تو رو بیشتر از اونی که فکر می‌کنی دوست دارم»!",
        "اسم یه چیز که مخفیانه از یکی از اعضای گروه می‌خوای بگو!",
        "بگو اگه یکی از اعضای گروه قرار بود عاشقش بشی، کی بود!",
    ],
}

SETUP_GAMES = {}
ACTIVE_GAMES = {}
TD_SETUP_GAMES = {}
TD_ACTIVE_GAMES = {}


def _ai_call_sync(messages, temperature, model):
    payload = {"model": model, "messages": messages, "temperature": temperature,
               "response_format": {"type": "json_object"}}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=35)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.json()


async def ai_generate_question(category):
    sys_msg = (
        "Persian quiz maker. Respond ONLY with JSON:\n"
        '{"question": "متن", "options": ["1","2","3","4"], "correct": 0}\n'
        "Rules: Persian. correct=0-based. Exactly 4 options. Only one correct. Random position."
    )
    msgs = [{"role": "system", "content": sys_msg},
            {"role": "user", "content": f"سوال چهارگزینه‌ای جذاب از «{category}»"}]
    for model in AI_MODELS:
        for att in range(2):
            try:
                t = 0.9 if att == 0 else 1.1
                data = await asyncio.to_thread(_ai_call_sync, msgs, t, model)
                obj = json.loads(data["choices"][0]["message"]["content"])
                opts = obj.get("options")
                if not isinstance(opts, list) or len(opts) != 4:
                    raise ValueError("bad")
                if not isinstance(obj.get("correct"), int) or not (0 <= obj["correct"] <= 3):
                    raise ValueError("bad")
                if not obj.get("question"):
                    raise ValueError("bad")
                opts = [str(o).strip()[:80] for o in opts]
                if len(set(opts)) < 4:
                    raise ValueError("dup")
                ct = opts[obj["correct"]]
                random.shuffle(opts)
                return {"question": str(obj["question"]).strip()[:400],
                        "options": opts, "correct": opts.index(ct)}
            except Exception as e:
                logger.warning(f"quiz AI fail {model}: {e}")
                await asyncio.sleep(0.4)
    return None


# ═════════════════════════════════════════════
# 🎭 TRUTH OR DARE — SUPER FRIENDLY PROMPT
# ═════════════════════════════════════════════
async def ai_generate_td(kind, pname, used_texts=None):
    """Generate one truth/dare with a warm, casual, friendly tone"""
    if used_texts is None:
        used_texts = []

    # ═══════════════════════════════════════════
    # 🎯 Config per category — with friendly vibe
    # ═══════════════════════════════════════════
    config = {
        "truth": {
            "label": "حقیقت",
            "topic": "یک سوال صادقانه و صمیمی",
            "vibe": "خودمونی، گرم، مثل یه رفیق نزدیک که کنارت نشسته",
            "theme": random.choice([
                "خاطره‌ی خنده‌دار", "لحظه‌ی خجالت‌آور", "پشیمونی قدیمی",
                "راز کوچیک", "ترس پنهان", "آرزوی نگفته",
                "عادت عجیب", "دروغ بی‌ضرر", "روز بد",
                "احساس واقعی", "فکر نیمه‌شب", "خاطره‌ی بچگی",
            ]),
            "examples": [
                "علی جان، آخرین باری که از خنده روده‌بُر شدی و نتونستی خودت رو کنترل کنی کی بود؟",
                "علی، راستش رو بگو، کدوم آهنگ رو وقتی ناراحتی صد بار پشت سر هم گوش می‌دی؟",
                "بگو ببینم علی، بدترین دروغی که به مامانت گفتی چی بود و چطور لو رفت؟",
                "علی جان، اگه یه روز نامرئی می‌شدی، اولین جایی که می‌رفتی کجا بود؟",
                "بیا صادق باش علی، بدترین ویژگی خودت که هیچ‌وقت به کسی نگفتی چیه؟",
                "علی، اون روزی که از مدرسه در رفتی و به مامانت دروغ گفتی، کجا رفتی؟",
                "علی جان، چیزی که هنوزم از بچگیت خاطره‌ش اذیتت می‌کنه چیه؟",
            ],
        },
        "truth18": {
            "label": "حقیقت +18",
            "topic": "یک سوال جسورانه و شیطون‌کار",
            "vibe": "شیطون، خودمونی، بازیگوش — مثل رفیقی که یه کم شیطونیه",
            "theme": random.choice([
                "کراش قدیمی", "رابطه‌ی مخفی", "دروغ عاشقانه",
                "اعتراف جسورانه", "پیام پشیمونی", "خاطره‌ی شیطون",
                "کسی که مخفیانه دوستش داری", "لحظه‌ی خجالت عاشقانه",
                "دلخوری عاطفی", "اولین برخورد",
            ]),
            "examples": [
                "علی، بیا خودمونی، بدترین کراش زندگیت کی بود و چرا انقدر بد بود؟",
                "راستش رو بگو علی، آخرین بار کی مخفیانه چک کردی ببینی طرف آنلاینه یا نه؟",
                "علی جان، اگه مجبور بودی از این گروه یکی رو انتخاب کنی، کی رو انتخاب می‌کردی؟",
                "بگو ببینم علی، بدترین پیامی که تو حالت شیطونی فرستادی و پشیمون شدی چی بود؟",
                "علی، اسم کسی که هنوزم بهش فکر می‌کنی ولی به هیچ‌کس نگفتی؟",
                "خودمونی بگو علی، اولین بار کی فهمیدی عاشق شدی و همه‌چیز خراب شد؟",
                "علی جان، دروغی که به یکی از اعضای این گروه گفتی و هنوز ندونسته چیه؟",
            ],
        },
        "dare": {
            "label": "جرعت",
            "topic": "یک جرعت بامزه و قابل اجرا",
            "vibe": "خنده‌دار، خودمونی، مثل یه شیطنت دوستانه",
            "theme": random.choice([
                "ویس خنده‌دار", "استیکر عجیب", "پیام به مخاطب قدیمی",
                "شعر بداهه", "لهجه‌ی غلیظ", "لو دادن یه چیز کوچیک",
                "کپی پروفایل", "تقلید صدا", "رقص بدون موزیک",
            ]),
            "examples": [
                "علی جان، یه ویس ۱۵ ثانیه‌ای بفرست که با آهنگ مورد علاقه‌ت آواز می‌خونی!",
                "علی، اسم ۳ نفر از اعضای این گروه رو به ترتیب از بدترین تا بهترین بگو!",
                "بیا علی، به آخرین نفر توی مخاطبینت پیام بده «سلام داشتم بهت فکر می‌کردم»!",
                "علی جان، پروفایلت رو ۱ ساعت بذار عکس خنده‌دار خودت!",
                "با لهجه‌ی غلیظ اصفهانی یه ویس بفرست که خودت رو معرفی کنی علی!",
                "علی، ۱۰ تا استیکر رندوم پشت سر هم توی گروه بفرست!",
                "بیا علی، اسم یه چیز که همه می‌دونن ولی تو انکارش می‌کنی رو بگو!",
            ],
        },
        "dare18": {
            "label": "جرعت +18",
            "topic": "یک جرعت جسورانه و هیجان‌انگیز",
            "vibe": "جسورانه، شیطون، هیجان‌انگیز — بدون وقاحت",
            "theme": random.choice([
                "پیام به کراش قدیمی", "اعتراف مخفی", "تیکه به عضو گروه",
                "اعتراف احساسی", "لو دادن راز عاشقانه", "اعتراف خجالت‌آور",
            ]),
            "examples": [
                "علی، به کسی که ۶ ماه باهاش حرف نزدی پیام بده «تو هنوز توی فکر منی»!",
                "بیا علی، به یکی از اعضای این گروه بگو دقیقاً چی فکر می‌کنی راجع بهش!",
                "علی جان، اسم اولین کسی که دوستش داشتی و یه خاطره ازش تعریف کن!",
                "علی، به یکی از اعضای گروه بگو اگه بخوای یکی رو انتخاب کنی، کی رو انتخاب می‌کنی!",
                "بیا علی، بدترین پیام عاشقانه‌ای که فرستادی رو بخون!",
                "علی جان، بگو بین اعضای گروه کی رو بیشتر از همه دوست داری و چرا!",
            ],
        },
    }

    c = config[kind]
    label = c["label"]
    topic = c["topic"]
    vibe = c["vibe"]
    theme = c["theme"]
    examples = c["examples"]
    examples_txt = "\n".join([f"   {ex}" for ex in examples])

    avoid_txt = ""
    if used_texts:
        last = used_texts[-8:]
        lst = "\n".join([f"   ✗ {t[:90]}" for t in last])
        avoid_txt = f"\n\n⛔️ اینا رو قبلاً پرسیدیم — کاملاً متفاوت بساز:\n{lst}\n"

    # ═══════════════════════════════════════════
    # 🎯 SUPER FRIENDLY PROMPT
    # ═══════════════════════════════════════════
    system_prompt = (
        f"تو یه رفیق صمیمی و خودمونی هستی که داره بچه‌های گروه رو توی بازی «جرعت یا حقیقت» می‌چرخونه.\n"
        f"لحنت گرم، صمیمی، و مثل کسی که سال‌هاست با اینا رفیقه.\n\n"

        f"🎯 وظیفه‌ت:\n"
        f"یه {topic} برای «{pname}» بساز.\n\n"

        f"🔥 حس و حال:\n"
        f"   • {vibe}\n"
        f"   • طوری حرف بزن که انگار داری کنارش نشستی و لبخند می‌زنی\n"
        f"   • خودمونی، بدون تکلف، بدون رسمی‌بازی\n"
        f"   • بعضی وقتا با «بیا»، «راستش رو بگو»، «بگو ببینم» شروع کن\n\n"

        f"📌 موضوع این نوبت: {theme}\n\n"

        f"✅ قوانین:\n"
        f"   1. یک جمله کوتاه — حداکثر ۱۵۰ کاراکتر\n"
        f"   2. اسم «{pname}» توی جمله — می‌تونی با «{pname} جان» یا «{pname}» شروع کنی\n"
        f"   3. سوال/جرعت باید مستقیم، مشخص و قابل جواب باشه\n"
        f"   4. هیچ فحش یا محتوای مستهجن نباشه\n"
        f"   5. هیچ مقدمه، برچسب، یا گیومه نداشته باشه\n"
        f"   6. تو مجری هستی — جواب نمی‌دی، نظر نمی‌دی، تایید نمی‌کنی!\n"
        f"   7. عین رفیق رفتار کن، عین ربات خشک نه\n\n"

        f"💎 نمونه‌های درجه‌یک (سبکش رو بگیر، کپی نکن):\n"
        f"{examples_txt}\n"
        f"{avoid_txt}\n"

        f"📤 خروجی:\n"
        f"فقط یک خط متن. بدون JSON، بدون برچسب، بدون گیومه.\n"
        f"مثل این: «{pname}، آخرین باری که از خنده روده‌بُر شدی کی بود؟»"
    )

    user_prompt = (
        f"یه {label} گرم و خودمونی برای «{pname}» بساز. "
        f"موضوع: {theme}. کوتاه، بامزه، صمیمی."
    )

    msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for model in AI_MODELS[:3]:
        for attempt in range(3):
            try:
                temp = 1.1 if attempt == 0 else (1.3 if attempt == 1 else 1.5)
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "messages": msgs,
                    "temperature": temp,
                    "max_tokens": 200,
                }
                r = await asyncio.to_thread(
                    lambda: requests.post(GROQ_URL, headers=headers,
                                          json=payload, timeout=30)
                )
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}")
                data = r.json()
                txt = data["choices"][0]["message"]["content"].strip()

                # Cleanup
                txt = txt.strip('"').strip("'").strip("«").strip("»").strip()
                for p in [f"{label}:", f"{label}：", "سوال:", "جرعت:", "حقیقت:",
                          "پاسخ:", "جواب:", "❌", "✅", "-", "•", "*"]:
                    if txt.startswith(p):
                        txt = txt[len(p):].strip()
                txt = re.sub(r'^["\']+', "", txt)
                txt = re.sub(r'["\']+$', "", txt)
                txt = txt.split("\n")[0].strip()

                # Fix duplicate name
                parts = txt.split("،")
                if len(parts) >= 2 and parts[0].strip() == parts[1].strip():
                    txt = "،".join(parts[1:]).strip()

                # Validation
                if not txt or len(txt) < 15:
                    raise ValueError(f"too short: {len(txt)}")
                if len(txt) > 200:
                    txt = txt[:197] + "..."
                bad_starts = ["باشه", "بله", "خب ", "حتما", "چشم",
                              "سلام ", "در خدمتم", "من نمی", "بذار ", "الان "]
                for bs in bad_starts:
                    if txt.startswith(bs) and "؟" not in txt[:30]:
                        raise ValueError(f"chat-like: {txt[:40]}")
                if kind in ("truth", "truth18") and "؟" not in txt and "?" not in txt:
                    txt = txt.rstrip(".") + "؟"
                if any(txt.strip() == u.strip() for u in used_texts):
                    raise ValueError("duplicate")

                logger.info(f"✅ TD[{kind}] {model} t={temp}: {txt[:60]}")
                return txt

            except Exception as e:
                logger.warning(f"TD {model} t{attempt}: {e}")
                await asyncio.sleep(0.4)

    logger.warning(f"TD fallback bank: {kind}")
    bank = TD_BANK.get(kind, [])
    if bank:
        unused = [t for t in bank if t not in used_texts]
        pool = unused if unused else bank
        return random.choice(pool)
    return None


class DB:
    def __init__(self, dsn):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True
        self._create(); self._migrate()
        logger.info("✅ PostgreSQL connected")

    def _c(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _create(self):
        c = self._c()
        c.execute("""CREATE TABLE IF NOT EXISTS groups (group_id BIGINT PRIMARY KEY,
            title TEXT, username TEXT, last_seen TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS challenges (id BIGSERIAL PRIMARY KEY,
            admin_id BIGINT, group_id BIGINT, title TEXT, question TEXT,
            message_id BIGINT, created_at TEXT, is_active INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS answers (challenge_id BIGINT,
            user_id BIGINT, user_name TEXT, username TEXT, answer TEXT, answered_at TEXT,
            PRIMARY KEY (challenge_id, user_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY,
            user_name TEXT, username TEXT, first_seen TEXT, last_seen TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS scores (user_id BIGINT PRIMARY KEY,
            user_name TEXT, points INTEGER DEFAULT 0, challenges_joined INTEGER DEFAULT 0,
            ngl_received INTEGER DEFAULT 0, ngl_sent INTEGER DEFAULT 0, last_active TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS anon_messages (id BIGSERIAL PRIMARY KEY,
            target_id BIGINT, sender_id BIGINT, text TEXT, sent_at TEXT, is_read INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS poll_votes (challenge_id BIGINT,
            user_id BIGINT, user_name TEXT, option_index INTEGER, voted_at TEXT,
            PRIMARY KEY (challenge_id, user_id))""")

    def _migrate(self):
        c = self._c()
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='challenges'")
        cols = {r["column_name"] for r in c.fetchall()}
        for col, ddl in [
            ("ch_type", "ALTER TABLE challenges ADD COLUMN ch_type TEXT DEFAULT 'text'"),
            ("options", "ALTER TABLE challenges ADD COLUMN options TEXT"),
            ("deadline", "ALTER TABLE challenges ADD COLUMN deadline TEXT"),
            ("results_announced", "ALTER TABLE challenges ADD COLUMN results_announced INTEGER DEFAULT 0"),
        ]:
            if col not in cols:
                try: self._c().execute(ddl)
                except Exception: pass

    def save_group(self, gid, t, u=None):
        self._c().execute("""INSERT INTO groups (group_id,title,username,last_seen)
            VALUES (%s,%s,%s,%s) ON CONFLICT(group_id) DO UPDATE SET
            title=EXCLUDED.title,username=EXCLUDED.username,last_seen=EXCLUDED.last_seen""",
            (gid, t, u, now_iso()))
    def get_groups(self):
        c = self._c(); c.execute("SELECT * FROM groups ORDER BY last_seen DESC")
        return [dict(r) for r in c.fetchall()]
    def save_user(self, uid, un, uu=None):
        self._c().execute("""INSERT INTO users (user_id,user_name,username,first_seen,last_seen)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET
            user_name=EXCLUDED.user_name,username=EXCLUDED.username,last_seen=EXCLUDED.last_seen""",
            (uid, un, uu, now_iso(), now_iso()))
    def get_all_users(self):
        c = self._c(); c.execute("SELECT user_id FROM users")
        return [r["user_id"] for r in c.fetchall()]
    def count_users(self):
        c = self._c(); c.execute("SELECT COUNT(*) AS n FROM users")
        return c.fetchone()["n"]
    def create_challenge(self, aid, gid, title, q, ch_type="text", options=None, deadline=None):
        c = self._c()
        c.execute("""INSERT INTO challenges (admin_id,group_id,title,question,created_at,ch_type,options,deadline)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (aid, gid, title, q, now_iso(), ch_type,
             json.dumps(options, ensure_ascii=False) if options else None, deadline))
        return c.fetchone()["id"]
    def set_challenge_message(self, cid, mid):
        self._c().execute("UPDATE challenges SET message_id=%s WHERE id=%s", (mid, cid))
    def get_challenge(self, cid):
        c = self._c(); c.execute("SELECT * FROM challenges WHERE id=%s", (cid,))
        r = c.fetchone(); return dict(r) if r else None
    def get_challenges(self, aid=None):
        c = self._c()
        if aid: c.execute("SELECT * FROM challenges WHERE admin_id=%s ORDER BY id DESC", (aid,))
        else: c.execute("SELECT * FROM challenges ORDER BY id DESC")
        return [dict(r) for r in c.fetchall()]
    def search_challenges(self, aid, q):
        c = self._c(); p = f"%{q}%"
        c.execute("""SELECT * FROM challenges WHERE admin_id=%s AND
            (title ILIKE %s OR question ILIKE %s) ORDER BY id DESC""", (aid, p, p))
        return [dict(r) for r in c.fetchall()]
    def deactivate_challenge(self, cid):
        self._c().execute("UPDATE challenges SET is_active=0 WHERE id=%s", (cid,))
    def mark_results_announced(self, cid):
        self._c().execute("UPDATE challenges SET results_announced=1 WHERE id=%s", (cid,))
    def get_expired_challenges(self):
        c = self._c()
        c.execute("""SELECT * FROM challenges WHERE is_active=1 AND deadline IS NOT NULL
            AND deadline<=%s AND results_announced=0""", (now_iso(),))
        return [dict(r) for r in c.fetchall()]
    def count_active_challenges(self):
        c = self._c(); c.execute("SELECT COUNT(*) AS n FROM challenges WHERE is_active=1")
        return c.fetchone()["n"]
    def save_answer(self, cid, uid, un, uu, a):
        self._c().execute("""INSERT INTO answers (challenge_id,user_id,user_name,username,answer,answered_at)
            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(challenge_id,user_id) DO UPDATE SET
            answer=EXCLUDED.answer,answered_at=EXCLUDED.answered_at,
            user_name=EXCLUDED.user_name,username=EXCLUDED.username""",
            (cid, uid, un, uu, a, now_iso()))
    def get_answers(self, cid):
        c = self._c(); c.execute("SELECT * FROM answers WHERE challenge_id=%s ORDER BY answered_at DESC", (cid,))
        return [dict(r) for r in c.fetchall()]
    def has_answered(self, cid, uid):
        c = self._c(); c.execute("SELECT 1 FROM answers WHERE challenge_id=%s AND user_id=%s", (cid, uid))
        return c.fetchone() is not None
    def count_answers(self, cid):
        c = self._c(); c.execute("SELECT COUNT(*) AS n FROM answers WHERE challenge_id=%s", (cid,))
        return c.fetchone()["n"]
    def save_poll_vote(self, cid, uid, un, idx):
        self._c().execute("""INSERT INTO poll_votes (challenge_id,user_id,user_name,option_index,voted_at)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT(challenge_id,user_id) DO UPDATE SET
            option_index=EXCLUDED.option_index,voted_at=EXCLUDED.voted_at""",
            (cid, uid, un, idx, now_iso()))
    def has_voted(self, cid, uid):
        c = self._c(); c.execute("SELECT 1 FROM poll_votes WHERE challenge_id=%s AND user_id=%s", (cid, uid))
        return c.fetchone() is not None
    def get_poll_results(self, cid, n):
        c = self._c()
        c.execute("""SELECT option_index,COUNT(*) AS n FROM poll_votes
            WHERE challenge_id=%s GROUP BY option_index""", (cid,))
        cnt = {i: 0 for i in range(n)}
        for r in c.fetchall(): cnt[r["option_index"]] = r["n"]
        return cnt
    def count_poll_votes(self, cid):
        c = self._c(); c.execute("SELECT COUNT(*) AS n FROM poll_votes WHERE challenge_id=%s", (cid,))
        return c.fetchone()["n"]
    def add_points(self, uid, un, pts=10, joined=True, ngl=False, sent=False):
        c = self._c(); c.execute("SELECT user_id FROM scores WHERE user_id=%s", (uid,))
        if c.fetchone() is None:
            self._c().execute("""INSERT INTO scores (user_id,user_name,points,challenges_joined,
                ngl_received,ngl_sent,last_active) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (uid, un, pts, 1 if joined else 0, 1 if ngl else 0, 1 if sent else 0, now_iso()))
        else:
            self._c().execute("""UPDATE scores SET user_name=%s,points=points+%s,
                challenges_joined=challenges_joined+%s,ngl_received=ngl_received+%s,
                ngl_sent=ngl_sent+%s,last_active=%s WHERE user_id=%s""",
                (un, pts, 1 if joined else 0, 1 if ngl else 0, 1 if sent else 0, now_iso(), uid))
    def get_score(self, uid):
        c = self._c(); c.execute("SELECT * FROM scores WHERE user_id=%s", (uid,))
        r = c.fetchone(); return dict(r) if r else None
    def get_top(self, lim=10):
        c = self._c()
        c.execute("SELECT * FROM scores ORDER BY points DESC,challenges_joined DESC LIMIT %s", (lim,))
        return [dict(r) for r in c.fetchall()]
    def get_rank(self, uid):
        c = self._c(); c.execute("SELECT points FROM scores WHERE user_id=%s", (uid,))
        r = c.fetchone()
        if not r: return None
        c.execute("SELECT COUNT(*) AS n FROM scores WHERE points > %s", (r["points"],))
        return c.fetchone()["n"] + 1
    def save_anon(self, tid, sid, txt):
        self._c().execute("""INSERT INTO anon_messages (target_id,sender_id,text,sent_at)
            VALUES (%s,%s,%s,%s)""", (tid, sid, txt, now_iso()))
    def get_anon_inbox(self, tid, lim=10):
        c = self._c()
        c.execute("SELECT * FROM anon_messages WHERE target_id=%s ORDER BY id DESC LIMIT %s", (tid, lim))
        return [dict(r) for r in c.fetchall()]
    def count_anon_received(self, tid):
        c = self._c(); c.execute("SELECT COUNT(*) AS n FROM anon_messages WHERE target_id=%s", (tid,))
        return c.fetchone()["n"]
    def mark_anon_read(self, tid):
        self._c().execute("UPDATE anon_messages SET is_read=1 WHERE target_id=%s", (tid,))


db = DB(DATABASE_URL)

if PROXY_HOST and PROXY_PORT:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH,
                            proxy=(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, None, None))
else:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

_user_states = {}


def set_state(uid, state, **data):
    _user_states[uid] = {"state": state, "data": data}


def get_state(uid):
    return _user_states.get(uid)


def clear_state(uid):
    _user_states.pop(uid, None)


async def send_admin_menu(event, edit=False):
    text = (
        f"{E('crown', '👑')} <b>UNICORN · ADMIN PANEL</b> {E('crown', '👑')}\n"
        f"{DIV}\n\n"
        f"{E('sparkle', '✨')} <b>سلام ادمین عزیز!</b> {E('wave', '👋')}\n"
        f"{DIV2}\n\n"
        f"{E('brain', '🧠')} <b>دستورات گروهی:</b>\n"
        f"  {E('diamond', '💎')} <code>چالش</code> {E('point', '←')} کوییز هوشمند\n"
        f"  {E('magic', '🎭')} <code>جرعت</code> {E('point', '←')} جرعت یا حقیقت\n"
        f"  {E('chart', '📊')} <code>نظرسنجی: عنوان | گ1 | گ2</code>\n\n"
        f"{DIV2}\n"
        f"{E('star', '⭐')} <i>از دکمه‌های زیر استفاده کن</i> {E('point', '👇')}"
    )
    buttons = [
        [Button.inline("💎 چالش متنی", data=b"new_text"),
         Button.inline("📊 نظرسنجی", data=b"new_poll")],
        [Button.inline("🎁 قالب آماده", data=b"templates")],
        [Button.inline("📋 چالش‌های من", data=b"my_challenges")],
        [Button.inline("🏢 گروه‌ها", data=b"my_groups"),
         Button.inline("🏆 لیدربورد", data=b"top")],
        [Button.inline("💌 لینک NGL", data=b"mylink"),
         Button.inline("📊 آمار", data=b"stats")],
        [Button.inline("📥 صندوق ناشناس", data=b"anon_inbox"),
         Button.inline("📤 برادکست", data=b"broadcast")],
    ]
    if edit:
        await safe_edit(event, text, buttons=buttons, parse_mode="html")
    else:
        await safe_respond(event, text, buttons=buttons, parse_mode="html")


def build_challenge_text(cid, title, question, ch_type, options, deadline):
    if ch_type == "poll":
        opts = "\n".join([f"  {E('point', '👉')} <b>{i+1}.</b> {h(o)}"
                          for i, o in enumerate(options or [])])
        body = (f"{E('chart', '📊')} <b>نظرسنجی ناشناس</b>\n{DIV}\n\n"
                f"{E('tag', '🏷️')} <b>عنوان:</b> {h(title)}\n\n"
                f"{E('list', '📋')} <b>گزینه‌ها:</b>\n{opts}\n\n")
    else:
        body = (f"{E('diamond', '💎')} <b>چالش ناشناس</b>\n{DIV}\n\n"
                f"{E('tag', '🏷️')} <b>عنوان:</b> {h(title)}\n\n"
                f"{E('message', '💬')} <b>سوال:</b> {h(question)}\n\n")
    extra = (f"{E('shield', '🛡')} <i>پاسخ‌ها کاملاً ناشناس</i>\n"
             f"{E('lock', '🔒')} <i>هیچ‌کس نمی‌فهمه کی جواب داده</i>\n")
    if deadline:
        try:
            extra += f"{E('hourglass', '⏳')} <b>مهلت:</b> {datetime.fromisoformat(deadline).strftime('%Y/%m/%d - %H:%M')}\n"
        except Exception: pass
    extra += f"\n{E('rocket', '🚀')} <b>برای شرکت روی دکمه بزن:</b>"
    return body + extra


def create_setup_game(aid, gid):
    g = {"id": int(datetime.now(IRAN_TZ).timestamp() * 1000) % 100000000,
         "admin_id": aid, "group_id": gid, "categories": [],
         "questions_per_player": 5, "time_per_question": 30, "target_score": 0,
         "players": {}, "order": [], "state": "setup", "current_index": 0,
         "current_player": None, "current_state": None, "current_question": None,
         "join_msg_id": None, "turn_msg_id": None, "timeout_task": None}
    SETUP_GAMES[aid] = g
    return g


def _find_game_for_callback(event):
    try:
        mid = getattr(event, "message_id", None)
        if mid:
            for g in ACTIVE_GAMES.values():
                if g.get("join_msg_id") == mid or g.get("turn_msg_id") == mid:
                    return g
                cq = g.get("current_question")
                if cq and cq.get("msg_id") == mid: return g
    except Exception: pass
    try:
        cid = getattr(event, "chat_id", None)
        if cid and ACTIVE_GAMES.get(cid): return ACTIVE_GAMES.get(cid)
    except Exception: pass
    try:
        w = [g for g in ACTIVE_GAMES.values() if g.get("state") == "waiting"]
        if len(w) == 1: return w[0]
    except Exception: pass
    return None


def render_quiz_welcome(g):
    return (
        f"{E('brain', '🧠')} <b>کوییز هوشمند UNICORN</b> {E('brain', '🧠')}\n"
        f"{DIV}\n\n"
        f"{E('sparkle', '✨')} <b>سلام ادمین عزیز!</b> {E('wave', '👋')}\n\n"
        f"{E('info', 'ℹ️')} <b>جریان بازی:</b>\n"
        f"  {E('gamepad', '🎮')} بازیکنان توی گروه عضو می‌شن\n"
        f"  {E('target', '🎯')} نوبتی توی گروه دسته انتخاب می‌کنن\n"
        f"  {E('brain', '🧠')} هوش مصنوعی سوال می‌سازه\n"
        f"  {E('hourglass', '⏳')} تایمر زنده هر ثانیه\n"
        f"  {E('bolt', '⚡')} درست <b>+1</b> و غلط <b>-1</b>\n\n"
        f"{E('magic', '✨')} <i>آماده‌ای؟</i>",
        [[Button.inline("🚀 شروع تنظیمات", data=b"quiz_setup")],
         [Button.inline("❌ لغو", data=b"quiz_cancel")]]
    )


def render_categories_menu(g):
    sel = g["categories"]
    text = (f"{E('target', '🎯')} <b>مرحله ۱ از ۳ — دسته‌بندی</b>\n{DIV}\n\n"
            f"{E('info', 'ℹ️')} هر تعداد که می‌خوای انتخاب کن:\n\n"
            f"{E('list', '📋')} <b>انتخاب شده ({len(sel)}):</b>\n")
    if sel:
        for c in sel: text += f"  {E('check', '✅')} <b>{c}</b>\n"
    else:
        text += f"  {E('cross', '➖')} <i>هنوز چیزی انتخاب نکردی</i>\n"
    btns, row = [], []
    for i, (k, e, n) in enumerate(QUIZ_CATEGORIES):
        mark = "✅" if n in sel else "◽"
        row.append(Button.inline(f"{mark} {e} {n}", data=f"quiz_cat:{i}".encode()))
        if len(row) == 2:
            btns.append(row); row = []
    if row: btns.append(row)
    if sel: btns.append([Button.inline("➡️ ادامه", data=b"quiz_settings")])
    else: btns.append([Button.inline("⛔ حداقل یکی", data=b"quiz_noop")])
    btns.append([Button.inline("❌ لغو", data=b"quiz_cancel")])
    return text, btns


def render_settings_menu(g):
    q, t, s = g["questions_per_player"], g["time_per_question"], g["target_score"]
    qb = [Button.inline(("✅ " if n == q else "◽ ") + str(n), data=f"quiz_q:{n}".encode())
          for n in QUIZ_Q_OPTIONS]
    tb = [Button.inline(("✅ " if n == t else "◽ ") + f"{n}s", data=f"quiz_t:{n}".encode())
          for n in QUIZ_TIME_OPTIONS]
    sb = [Button.inline(("✅ " if n == s else "◽ ") + ("♾" if n == 0 else str(n)),
                        data=f"quiz_s:{n}".encode()) for n in QUIZ_TARGET_OPTIONS]
    text = (f"{E('gamepad', '🎮')} <b>مرحله ۲ از ۳ — تنظیمات</b>\n{DIV}\n\n"
            f"{E('chart', '📊')} <b>سوال هر نفر:</b> <code>{q}</code>\n"
            f"{E('hourglass', '⏳')} <b>زمان هر سوال:</b> <code>{t}</code> ثانیه\n"
            f"{E('trophy', '🏆')} <b>امتیاز هدف:</b> "
            f"{'<i>بدون هدف</i>' if s == 0 else f'<code>{s}</code>'}\n\n"
            f"{E('info', 'ℹ️')} <i>با دکمه‌ها تنظیم کن</i>")
    return text, [
        [Button.inline("— 📊 تعداد سوال —", data=b"quiz_noop")], qb,
        [Button.inline("— ⏳ زمان هر سوال —", data=b"quiz_noop")], tb,
        [Button.inline("— 🏆 امتیاز هدف —", data=b"quiz_noop")], sb,
        [Button.inline("⬅️ قبلی", data=b"quiz_backcat"),
         Button.inline("➡️ ادامه", data=b"quiz_summary")],
        [Button.inline("❌ لغو", data=b"quiz_cancel")],
    ]


def render_summary_menu(g):
    cats = "، ".join(g["categories"])
    tt = "بدون هدف" if g["target_score"] == 0 else f"{g['target_score']} امتیاز"
    text = (f"{E('check', '✅')} <b>مرحله ۳ از ۳ — خلاصه</b>\n{DIV}\n\n"
            f"{E('brain', '🧠')} <b>کوییز هوشمند UNICORN</b>\n\n"
            f"{E('list', '📋')} <b>دسته‌ها:</b> {h(cats)}\n"
            f"{E('chart', '📊')} <b>سوال هر نفر:</b> <code>{g['questions_per_player']}</code>\n"
            f"{E('hourglass', '⏳')} <b>زمان هر سوال:</b> <code>{g['time_per_question']}</code> ثانیه\n"
            f"{E('trophy', '🏆')} <b>امتیاز هدف:</b> <code>{tt}</code>\n\n"
            f"{E('info', 'ℹ️')} <i>بعد از تأیید، پیام شرکت توی گروه فرستاده می‌شه</i>")
    return text, [
        [Button.inline("🚀 ایجاد بازی در گروه", data=b"quiz_create")],
        [Button.inline("⬅️ قبلی", data=b"quiz_settings")],
        [Button.inline("❌ لغو", data=b"quiz_cancel")],
    ]


async def quiz_send_setup_menu(aid, screen="welcome", game=None):
    if game is None: game = SETUP_GAMES.get(aid)
    if not game: return
    if screen == "welcome": text, b = render_quiz_welcome(game)
    elif screen == "categories": text, b = render_categories_menu(game)
    elif screen == "settings": text, b = render_settings_menu(game)
    elif screen == "summary": text, b = render_summary_menu(game)
    else: return
    try: await safe_send(aid, text, buttons=b, parse_mode="html")
    except Exception as e: logger.exception(f"quiz_send_setup_menu: {e}")


def _render_join_text(g):
    pl = list(g["players"].values())
    c = len(pl)
    if c == 0:
        nb = f"     {E('cross', '➖')} <i>هنوز کسی شرکت نکرده</i>"
    else:
        re_ = ["🥇", "🥈", "🥉"]
        lines = []
        for i, p in enumerate(pl):
            r = re_[i] if i < 3 else f"<b>{i+1:02d}.</b>"
            u = f"  <i>@{p['username']}</i>" if p.get("username") else ""
            lines.append(f"  {r} {E('check', '✅')} <b>{h(p['name'])}</b>{u}")
        nb = "\n".join(lines)
    cats = "، ".join(g["categories"])
    tt = "بدون هدف" if g["target_score"] == 0 else f"{g['target_score']} امتیاز"
    text = (
        f"{E('brain', '🧠')} <b>UNICORN QUIZ · PRO</b> {E('brain', '🧠')}\n"
        f"{DIV}\n\n"
        f"{E('party', '🎉')} <b>یه کوییز حرفه‌ای با هوش مصنوعی!</b>\n"
        f"{DIV2}\n\n"
        f"{E('list', '📋')} <b>دسته‌ها:</b>  {h(cats)}\n"
        f"{E('chart', '📊')} <b>سوال هر نفر:</b>  <code>{g['questions_per_player']}</code>\n"
        f"{E('hourglass', '⏳')} <b>زمان هر سوال:</b>  <code>{g['time_per_question']}</code> ثانیه\n"
        f"{E('trophy', '🏆')} <b>هدف:</b>  <code>{tt}</code>\n"
        f"{E('bolt', '⚡')} درست <b>+1</b>  ·  غلط <b>-1</b>\n"
        f"{DIV}\n"
        f"{E('crown', '👑')} <b>شرکت‌کنندگان ({c}):</b>\n"
        f"{nb}\n"
        f"{DIV}\n\n"
        f"{E('target', '🎯')} <b>برای شرکت، روی دکمه بزن</b> {E('point', '👇')}"
    )
    jb = f"✋ شرکت می‌کنم  ·  ({c})" if c > 0 else "✋ شرکت می‌کنم"
    return text, [[Button.inline(jb, data=b"quiz_join")],
                  [Button.inline("▶️ شروع بازی (ادمین)", data=b"quiz_start")]]


async def quiz_broadcast_join(g):
    text, btns = _render_join_text(g)
    try:
        sent = await safe_send(g["group_id"], text, buttons=btns, parse_mode="html")
        if sent: g["join_msg_id"] = sent.id
    except Exception as e: logger.exception(f"quiz_broadcast_join: {e}")


async def quiz_refresh_join(g):
    mid = g.get("join_msg_id")
    if not mid: return
    text, btns = _render_join_text(g)
    try:
        await client.edit_message(g["group_id"], mid, text=text, buttons=btns, parse_mode="html")
        return
    except MessageNotModifiedError: return
    except Exception as e: logger.warning(f"refresh m1: {e}")
    try:
        msg = await client.get_messages(g["group_id"], ids=mid)
        if msg:
            await msg.edit(text=text, buttons=btns, parse_mode="html")
            return
    except Exception as e: logger.warning(f"refresh m2: {e}")
    try:
        new = await safe_send(g["group_id"], text, buttons=btns, parse_mode="html")
        if new:
            g["join_msg_id"] = new.id
            try: await client.delete_messages(g["group_id"], mid)
            except Exception: pass
    except Exception as e: logger.exception(f"refresh m3: {e}")


async def quiz_start_game(g):
    g["state"] = "playing"
    g["order"] = list(g["players"].keys())
    g["current_index"] = 0
    pl = "\n".join([f"  {E('point', '👉')} <b>{h(p['name'])}</b>" for p in g["players"].values()])
    await safe_send(g["group_id"],
                    f"{E('party', '🎉')} <b>بازی شروع شد!</b> {E('party', '🎉')}\n{DIV}\n\n"
                    f"{E('user', '👤')} <b>بازیکنان ({len(g['order'])}):</b>\n{pl}\n\n"
                    f"{E('rocket', '🚀')} <b>آماده باشید...</b>", parse_mode="html")
    await asyncio.sleep(2)
    await quiz_next_turn(g)


async def quiz_next_turn(g):
    if g["state"] != "playing": return
    if not g["order"]:
        await quiz_finish(g); return
    n = len(g["order"])
    if all(g["players"][uid]["asked"] >= g["questions_per_player"] for uid in g["order"]):
        await quiz_finish(g); return
    tries = 0
    while tries < n:
        idx = g["current_index"] % n
        uid = g["order"][idx]
        if g["players"][uid]["asked"] < g["questions_per_player"]:
            break
        g["current_index"] += 1; tries += 1
    else:
        await quiz_finish(g); return
    uid = g["order"][g["current_index"] % n]
    p = g["players"][uid]
    g["current_player"] = uid
    g["current_state"] = "picking_category"
    g["current_question"] = None
    if g.get("turn_msg_id"):
        try: await client.delete_messages(g["group_id"], g["turn_msg_id"])
        except Exception: pass
    cb = quiz_category_buttons(g)
    cb.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"quiz_skip_turn")])
    text = (f"{E('target', '🎯')} <b>نوبت {h(p['name'])}</b>\n{DIV}\n\n"
            f"{E('chart', '📊')} سوال <code>{p['asked']+1}/{g['questions_per_player']}</code>\n"
            f"{E('star', '⭐')} امتیاز: <code>{p['score']}</code>\n\n"
            f"{E('brain', '🧠')} <b>{h(p['name'])}</b> یه دسته انتخاب کن:\n"
            f"{E('info', 'ℹ️')} <i>فقط خودت می‌تونی کلیک کنی</i>")
    sent = await safe_send(g["group_id"], text, buttons=cb, parse_mode="html")
    if sent: g["turn_msg_id"] = sent.id


def quiz_category_buttons(g):
    btns, row = [], []
    for i, (k, e, n) in enumerate(QUIZ_CATEGORIES):
        if n not in g["categories"]: continue
        row.append(Button.inline(f"{e} {n}", data=f"quiz_pick:{i}".encode()))
        if len(row) == 2:
            btns.append(row); row = []
    if row: btns.append(row)
    return btns


async def quiz_ask_question(g, uid, ci):
    k, e, cn = QUIZ_CATEGORIES[ci]
    gid = g["group_id"]
    if g.get("turn_msg_id"):
        try:
            await client.delete_messages(gid, g["turn_msg_id"]); g["turn_msg_id"] = None
        except Exception: pass
    wm = await safe_send(gid,
                         f"{E('brain', '🧠')} <b>AI در حال ساخت سوال...</b>\n"
                         f"{DIV}\n\n"
                         f"{e} دسته: <b>{h(cn)}</b>\n"
                         f"{E('bolt', '⚡')} <i>چند لحظه صبر کن...</i>",
                         parse_mode="html")
    q = await ai_generate_question(cn)
    if not q:
        try: await wm.delete()
        except Exception: pass
        await safe_send(gid, f"{E('cross', '❌')} <b>خطا در ساخت سوال</b>\n"
                             f"{E('info', 'ℹ️')} نوبت می‌چرخه...", parse_mode="html")
        await asyncio.sleep(2)
        g["current_index"] += 1
        await quiz_next_turn(g); return
    p = g["players"][uid]
    g["current_question"] = {
        "player": uid, "question": q["question"], "options": q["options"],
        "correct": q["correct"], "category": cn, "category_emoji": e,
        "answered": False, "msg_id": None, "total_time": g["time_per_question"],
    }
    g["current_state"] = "answering"
    p["asked"] += 1
    labels = ["۱", "۲", "۳", "۴"]
    btns = [[Button.inline(f"{labels[i]}. {opt[:60]}", data=f"quiz_ans:{i}".encode())]
            for i, opt in enumerate(q["options"])]
    btns.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"quiz_skip_turn")])
    total = g["time_per_question"]
    bar = time_bar_colored(total, total)
    tb = time_badge(total, total)
    text = (
        f"{e} <b>سوال {h(cn)}</b> — نوبت <b>{h(p['name'])}</b>\n"
        f"{DIV}\n\n"
        f"{E('brain', '🧠')} <b>{h(q['question'])}</b>\n\n"
        f"{DIV2}\n"
        f"{tb} <b>زمان:</b> <code>{total}</code> ثانیه\n"
        f"{bar}  <b>100%</b>\n"
        f"{E('bolt', '⚡')} درست <b>+1</b> | غلط <b>-1</b>\n"
        f"{E('star', '⭐')} امتیاز فعلی: <code>{p['score']}</code>\n"
        f"{DIV}\n\n"
        f"{E('target', '🎯')} <b>{h(p['name'])}</b> یکی رو انتخاب کن:"
    )
    try: await wm.delete()
    except Exception: pass
    sent = await safe_send(gid, text, buttons=btns, parse_mode="html")
    if sent: g["current_question"]["msg_id"] = sent.id
    if g.get("timeout_task"):
        try: g["timeout_task"].cancel()
        except Exception: pass
    g["timeout_task"] = asyncio.create_task(quiz_live_countdown(g, uid, total))


async def quiz_live_countdown(g, uid, total):
    logger.info(f"⏱ countdown {total}s uid={uid}")
    try:
        gid = g["group_id"]
        last_shown = None
        for remaining in range(total, -1, -1):
            cq = g.get("current_question")
            if not cq or cq.get("answered") or cq.get("player") != uid: return
            p = g["players"].get(uid)
            if not p: return
            if cq.get("msg_id") is None:
                await asyncio.sleep(0.5); continue
            bar = time_bar_colored(remaining, total)
            tb = time_badge(remaining, total)
            pct = int(100 * remaining / total) if total > 0 else 0
            if remaining <= 3 and remaining > 0:
                tw = f"{E('alert', '🚨')} <b><i>زود باش! فقط {remaining} ثانیه!</i></b>"
            elif remaining == 0:
                tw = f"{E('hourglass', '⏰')} <b>وقت تموم شد!</b>"
            else:
                tw = f"{tb} <b>زمان:</b> <code>{remaining}</code> ثانیه"
            labels = ["۱", "۲", "۳", "۴"]
            btns = [[Button.inline(f"{labels[i]}. {opt[:60]}", data=f"quiz_ans:{i}".encode())]
                    for i, opt in enumerate(cq["options"])]
            btns.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"quiz_skip_turn")])
            text = (
                f"{cq['category_emoji']} <b>سوال {h(cq['category'])}</b> — نوبت <b>{h(p['name'])}</b>\n"
                f"{DIV}\n\n"
                f"{E('brain', '🧠')} <b>{h(cq['question'])}</b>\n\n"
                f"{DIV2}\n{tw}\n{bar}  <b>{pct}%</b>\n"
                f"{E('bolt', '⚡')} درست <b>+1</b> | غلط <b>-1</b>\n"
                f"{E('star', '⭐')} امتیاز فعلی: <code>{p['score']}</code>\n"
                f"{DIV}\n\n"
                f"{E('target', '🎯')} <b>{h(p['name'])}</b> یکی رو انتخاب کن:"
            )
            if text != last_shown:
                ok = await safe_edit_msg(gid, cq["msg_id"], text, buttons=btns)
                if ok: last_shown = text
            if remaining == 0: break
            await asyncio.sleep(1)
        cq = g.get("current_question")
        if cq and not cq.get("answered") and cq.get("player") == uid:
            await quiz_handle_timeout(g, uid)
    except asyncio.CancelledError: return
    except Exception as e: logger.exception(f"cd err: {e}")


async def quiz_handle_timeout(g, uid):
    cq = g.get("current_question")
    if not cq or cq.get("answered"): return
    cq["answered"] = True
    p = g["players"].get(uid)
    if not p: return
    p["score"] -= 1
    ct = cq["options"][cq["correct"]]
    labels = ["۱", "۲", "۳", "۴"]
    btns = []
    for i, opt in enumerate(cq["options"]):
        if i == cq["correct"]:
            btns.append([Button.inline(f"✅ {labels[i]}. {opt[:58]}", data=b"quiz_noop")])
        else:
            btns.append([Button.inline(f"❌ {labels[i]}. {opt[:58]}", data=b"quiz_noop")])
    if cq.get("msg_id"):
        await safe_edit_msg(g["group_id"], cq["msg_id"],
            text=(f"{E('hourglass', '⏰')} <b>وقت تموم شد!</b>\n{DIV}\n\n"
                  f"{E('user', '👤')} <b>{h(p['name'])}</b> نتونست جواب بده\n\n"
                  f"{E('check', '✅')} <b>جواب درست:</b>\n     <b>{h(ct)}</b>\n\n"
                  f"{E('bolt', '⚡')} امتیاز: <code>-1</code>\n"
                  f"{E('star', '⭐')} امتیاز فعلی: <code>{p['score']}</code>"),
            buttons=btns)
    await asyncio.sleep(2.5)
    if await quiz_check_target(g): return
    g["current_index"] += 1
    await quiz_next_turn(g)


def _bb(options, correct, pick=None):
    labels = ["۱", "۲", "۳", "۴"]
    return [[Button.inline(f"{'✅' if i == correct else '❌'} {labels[i]}. {opt[:58]}",
                            data=b"quiz_noop")] for i, opt in enumerate(options)]


async def quiz_check_target(g):
    t = g["target_score"]
    if t <= 0: return False
    for uid, p in g["players"].items():
        if p["score"] >= t:
            await quiz_finish(g, winner_uid=uid); return True
    return False


async def quiz_answer(g, uid, ai):
    cq = g.get("current_question")
    if not cq or cq.get("answered") or cq["player"] != uid: return
    cq["answered"] = True
    if g.get("timeout_task"):
        try: g["timeout_task"].cancel()
        except Exception: pass
    p = g["players"][uid]
    correct = cq["correct"]
    ok = (ai == correct)
    ct = cq["options"][correct]
    ch = cq["options"][ai]
    btns = _bb(cq["options"], correct, pick=ai)
    if ok:
        p["score"] += 1
        text = (
            f"{E('party', '🎉')}🎊 <b>H O O R A ! ! !</b> 🎊{E('party', '🎉')}\n"
            f"{DIV}\n\n"
            f"{E('sparkle', '✨')} <b>{h(p['name'])} عزیز، درست زدی!</b> {E('sparkle', '✨')}\n"
            f"{DIV2}\n\n"
            f"{E('check', '✅')} <b>انتخاب تو:</b>  <code>{h(ch)}</code>\n"
            f"{E('check', '✅')} <b>جواب صحیح:</b>  <code>{h(ct)}</code>\n\n"
            f"{E('fire', '🔥')} <b>آفرین! فوق‌العاده بود!</b>\n"
            f"{E('bolt', '⚡')} امتیاز:  <code>+1</code>\n"
            f"{E('star', '⭐')} امتیاز کل:  <code>{p['score']}</code>\n"
            f"{DIV}\n"
            f"{E('rocket', '🚀')} <i>همینطوری ادامه بده قهرمان!</i>"
        )
    else:
        p["score"] -= 1
        text = (
            f"{E('warning', '😢')} <b>O O P S ! ! !</b> {E('warning', '😢')}\n"
            f"{DIV}\n\n"
            f"{E('alert', '⚠️')} <b>{h(p['name'])} جان، اشتباه بود</b>\n"
            f"{DIV2}\n\n"
            f"{E('cross', '❌')} <b>انتخاب تو:</b>  <code>{h(ch)}</code>\n"
            f"{E('check', '✅')} <b>جواب درست:</b>  <code>{h(ct)}</code>\n\n"
            f"{E('bolt', '⚡')} امتیاز:  <code>-1</code>\n"
            f"{E('star', '⭐')} امتیاز کل:  <code>{p['score']}</code>\n"
            f"{DIV}\n"
            f"{E('magic', '✨')} <i>اشکال نداره، نوبت بعدی جبران می‌کنی!</i>"
        )
    if cq.get("msg_id"):
        await safe_edit_msg(g["group_id"], cq["msg_id"], text, buttons=btns)
    await asyncio.sleep(2.5)
    if await quiz_check_target(g): return
    g["current_index"] += 1
    await quiz_next_turn(g)


async def quiz_skip_turn(g):
    if g["state"] != "playing": return
    cur = g.get("current_player")
    if not cur: return
    if g.get("timeout_task"):
        try: g["timeout_task"].cancel()
        except Exception: pass
    p = g["players"].get(cur)
    pn = p["name"] if p else "?"
    if g.get("turn_msg_id"):
        try:
            await client.delete_messages(g["group_id"], g["turn_msg_id"]); g["turn_msg_id"] = None
        except Exception: pass
    cq = g.get("current_question")
    if cq:
        cq["answered"] = True
        if cq.get("msg_id"):
            nb = _bb(cq["options"], cq["correct"])
            await safe_edit_msg(g["group_id"], cq["msg_id"],
                text=(f"{E('skip', '⏭')} <b>نوبت رد شد</b>\n{DIV}\n\n"
                      f"{E('user', '👤')} <b>{h(pn)}</b>\n"
                      f"{E('info', 'ℹ️')} ادمین این نوبت رو رد کرد"),
                buttons=nb)
        if p: p["asked"] += 1
    await safe_send(g["group_id"],
                    f"{E('skip', '⏭')} <b>نوبت {h(pn)} رد شد</b>\n"
                    f"{E('info', 'ℹ️')} <i>در حال رفتن به نوبت بعدی...</i>",
                    parse_mode="html")
    await asyncio.sleep(1.5)
    if await quiz_check_target(g): return
    g["current_index"] += 1
    await quiz_next_turn(g)


async def quiz_finish(g, winner_uid=None):
    g["state"] = "finished"
    try:
        if g.get("timeout_task"): g["timeout_task"].cancel()
    except Exception: pass
    ps = g["players"]
    sp = sorted(ps.items(), key=lambda x: x[1]["score"], reverse=True)
    if winner_uid and winner_uid in ps:
        w = ps[winner_uid]
        hd = (f"{E('trophy', '🏆')} <b>برنده کوییز!</b> {E('trophy', '🏆')}\n{DIV}\n\n"
              f"{E('crown', '👑')} <b>{h(w['name'])}</b>\n"
              f"{E('star', '⭐')} امتیاز: <code>{w['score']}</code>\n"
              f"{E('target', '🎯')} به امتیاز هدف رسید!")
    elif sp:
        w = sp[0][1]
        hd = (f"{E('flag', '🏁')} <b>کوییز تموم شد!</b>\n{DIV}\n\n"
              f"{E('trophy', '🏆')} <b>برنده:</b> {h(w['name'])}\n"
              f"{E('star', '⭐')} امتیاز: <code>{w['score']}</code>")
    else:
        hd = f"{E('flag', '🏁')} <b>کوییز تموم شد!</b>"
    medals = ["🥇", "🥈", "🥉"]
    lines = [hd, "", f"{E('stats', '📊')} <b>جدول نهایی:</b>"]
    for i, (uid, p) in enumerate(sp):
        m = medals[i] if i < 3 else "▫️"
        lines.append(f"{m} <b>{h(p['name'])}</b> — <code>{p['score']}</code> امتیاز")
    await safe_send(g["group_id"], "\n".join(lines), parse_mode="html")
    for uid, p in ps.items():
        if p["score"] > 0:
            try: db.add_points(uid, p["name"], p["score"] * 2, joined=True)
            except Exception: pass
    ACTIVE_GAMES.pop(g["group_id"], None)


def create_td_setup(aid, gid):
    g = {"id": int(datetime.now(IRAN_TZ).timestamp() * 1000) % 100000000,
         "admin_id": aid, "group_id": gid,
         "categories": ["truth", "truth18", "dare", "dare18"],
         "turns_per_player": 1, "timeout_sec": 60,
         "players": {}, "order": [], "state": "setup",
         "current_index": 0, "current_player": None, "current_state": None,
         "join_msg_id": None, "turn_msg_id": None, "timeout_task": None,
         "used_texts": []}
    TD_SETUP_GAMES[aid] = g
    return g


def _find_td_game(event):
    try:
        mid = getattr(event, "message_id", None)
        if mid:
            for g in TD_ACTIVE_GAMES.values():
                if g.get("join_msg_id") == mid or g.get("turn_msg_id") == mid:
                    return g
    except Exception: pass
    try:
        cid = getattr(event, "chat_id", None)
        if cid and TD_ACTIVE_GAMES.get(cid): return TD_ACTIVE_GAMES.get(cid)
    except Exception: pass
    try:
        w = [g for g in TD_ACTIVE_GAMES.values() if g.get("state") == "waiting"]
        if len(w) == 1: return w[0]
    except Exception: pass
    return None


def render_td_welcome(g):
    return (
        f"{E('magic', '🎭')} <b>جرعت یا حقیقت — UNICORN</b> {E('magic', '🎭')}\n"
        f"{DIV}\n\n"
        f"{E('sparkle', '✨')} <b>سلام ادمین عزیز!</b> {E('wave', '👋')}\n\n"
        f"{E('info', 'ℹ️')} <b>جریان بازی:</b>\n"
        f"  {E('user', '👤')} بازیکنان توی گروه عضو می‌شن\n"
        f"  🎲 نوبت‌ها به صورت تصادفی\n"
        f"  {E('hourglass', '⏳')} تایمر زنده هر ثانیه\n"
        f"  🎯 بین ۴ گزینه انتخاب می‌کنن\n"
        f"     🎭 حقیقت | 🔥 حقیقت+18 | ⚡ جرعت | 💋 جرعت+18\n\n"
        f"{E('magic', '✨')} <i>آماده‌ای؟</i>",
        [[Button.inline("🚀 شروع تنظیمات", data=b"td_setup")],
         [Button.inline("❌ لغو", data=b"td_cancel")]]
    )


def render_td_categories(g):
    sel = g["categories"]
    text = (f"{E('target', '🎯')} <b>مرحله ۱ از ۳ — دسته‌ها</b>\n{DIV}\n\n"
            f"{E('info', 'ℹ️')} کدوم‌ها فعال باشن؟\n"
            f"{E('alert', '⚠️')} <i>برای 18+ باید همه بزرگسال باشن</i>\n\n"
            f"{E('list', '📋')} <b>انتخاب شده ({len(sel)}):</b>\n")
    if sel:
        for c in sel:
            name = next((n for k, e, n in TD_CATEGORIES_ALL if k == c), c)
            text += f"  {E('check', '✅')} <b>{name}</b>\n"
    else:
        text += f"  {E('cross', '➖')} <i>هیچی</i>\n"
    btns = []
    for k, e, n in TD_CATEGORIES_ALL:
        mark = "✅" if k in sel else "◽"
        btns.append([Button.inline(f"{mark} {e} {n}", data=f"td_cat:{k}".encode())])
    if sel: btns.append([Button.inline("➡️ ادامه", data=b"td_settings")])
    else: btns.append([Button.inline("⛔ حداقل یکی", data=b"td_noop")])
    btns.append([Button.inline("❌ لغو", data=b"td_cancel")])
    return text, btns


def render_td_settings(g):
    t = g["turns_per_player"]; tm = g["timeout_sec"]
    tb = [Button.inline(("✅ " if n == t else "◽ ") + str(n), data=f"td_turns:{n}".encode())
          for n in TD_TURNS_OPTIONS]
    tmb = [Button.inline(("✅ " if n == tm else "◽ ") + f"{n}s", data=f"td_time:{n}".encode())
           for n in TD_TIMEOUT_OPTIONS]
    text = (f"{E('gamepad', '🎮')} <b>مرحله ۲ از ۳ — تنظیمات</b>\n{DIV}\n\n"
            f"{E('chart', '📊')} <b>نوبت هر نفر:</b> <code>{t}</code>\n"
            f"{E('hourglass', '⏳')} <b>زمان هر نوبت:</b> <code>{tm}</code> ثانیه\n\n"
            f"{E('info', 'ℹ️')} <i>با دکمه‌ها تنظیم کن</i>")
    return text, [
        [Button.inline("— 📊 تعداد نوبت —", data=b"td_noop")], tb,
        [Button.inline("— ⏳ زمان —", data=b"td_noop")], tmb,
        [Button.inline("⬅️ قبلی", data=b"td_backcat"),
         Button.inline("➡️ ادامه", data=b"td_summary")],
        [Button.inline("❌ لغو", data=b"td_cancel")],
    ]


def render_td_summary(g):
    cats = "، ".join([next((n for k, e, n in TD_CATEGORIES_ALL if k == c), c)
                      for c in g["categories"]])
    text = (f"{E('check', '✅')} <b>مرحله ۳ از ۳ — خلاصه</b>\n{DIV}\n\n"
            f"{E('magic', '🎭')} <b>جرعت یا حقیقت</b>\n\n"
            f"{E('list', '📋')} <b>دسته‌ها:</b> {h(cats)}\n"
            f"{E('chart', '📊')} <b>نوبت هر نفر:</b> <code>{g['turns_per_player']}</code>\n"
            f"{E('hourglass', '⏳')} <b>زمان هر نوبت:</b> <code>{g['timeout_sec']}</code> ثانیه\n\n"
            f"{E('info', 'ℹ️')} <i>بعد از تأیید، پیام شرکت توی گروه فرستاده می‌شه</i>")
    return text, [
        [Button.inline("🚀 ایجاد بازی در گروه", data=b"td_create")],
        [Button.inline("⬅️ قبلی", data=b"td_settings")],
        [Button.inline("❌ لغو", data=b"td_cancel")],
    ]


async def td_send_setup_menu(aid, screen="welcome", game=None):
    if game is None: game = TD_SETUP_GAMES.get(aid)
    if not game: return
    if screen == "welcome": text, b = render_td_welcome(game)
    elif screen == "categories": text, b = render_td_categories(game)
    elif screen == "settings": text, b = render_td_settings(game)
    elif screen == "summary": text, b = render_td_summary(game)
    else: return
    try: await safe_send(aid, text, buttons=b, parse_mode="html")
    except Exception as e: logger.exception(f"td_send_setup_menu: {e}")


def _render_td_join_text(g):
    pl = list(g["players"].values())
    c = len(pl)
    if c == 0:
        nb = f"     {E('cross', '➖')} <i>هنوز کسی نیست</i>"
    else:
        re_ = ["🥇", "🥈", "🥉"]
        lines = []
        for i, p in enumerate(pl):
            r = re_[i] if i < 3 else f"<b>{i+1:02d}.</b>"
            u = f"  <i>@{p['username']}</i>" if p.get("username") else ""
            lines.append(f"  {r} {E('check', '✅')} <b>{h(p['name'])}</b>{u}")
        nb = "\n".join(lines)
    cats = "، ".join([next((n for k, e, n in TD_CATEGORIES_ALL if k == x), x)
                      for x in g["categories"]])
    text = (
        f"{E('magic', '🎭')} <b>UNICORN · TRUTH or DARE</b> {E('magic', '🎭')}\n"
        f"{DIV}\n\n"
        f"{E('party', '🎉')} <b>یه بازی هیجان‌انگیز شروع می‌شه!</b>\n"
        f"{DIV2}\n\n"
        f"{E('list', '📋')} <b>دسته‌ها:</b>  {h(cats)}\n"
        f"{E('chart', '📊')} <b>نوبت هر نفر:</b>  <code>{g['turns_per_player']}</code>\n"
        f"{E('hourglass', '⏳')} <b>زمان هر نوبت:</b>  <code>{g['timeout_sec']}</code> ثانیه\n\n"
        f"🎲 <b>ترتیب بازیکنان تصادفی</b>\n\n"
        f"{DIV}\n"
        f"{E('crown', '👑')} <b>شرکت‌کنندگان ({c}):</b>\n"
        f"{nb}\n"
        f"{DIV}\n\n"
        f"{E('target', '🎯')} <b>برای شرکت، روی دکمه بزن</b> {E('point', '👇')}"
    )
    jb = f"✋ شرکت می‌کنم  ·  ({c})" if c > 0 else "✋ شرکت می‌کنم"
    return text, [[Button.inline(jb, data=b"td_join")],
                  [Button.inline("▶️ شروع بازی (ادمین)", data=b"td_start")]]


async def td_broadcast_join(g):
    text, btns = _render_td_join_text(g)
    try:
        sent = await safe_send(g["group_id"], text, buttons=btns, parse_mode="html")
        if sent: g["join_msg_id"] = sent.id
    except Exception as e: logger.exception(f"td_broadcast_join: {e}")


async def td_refresh_join(g):
    mid = g.get("join_msg_id")
    if not mid: return
    text, btns = _render_td_join_text(g)
    try:
        await client.edit_message(g["group_id"], mid, text=text, buttons=btns, parse_mode="html")
        return
    except MessageNotModifiedError: return
    except Exception as e: logger.warning(f"td refresh m1: {e}")
    try:
        msg = await client.get_messages(g["group_id"], ids=mid)
        if msg:
            await msg.edit(text=text, buttons=btns, parse_mode="html"); return
    except Exception as e: logger.warning(f"td refresh m2: {e}")
    try:
        new = await safe_send(g["group_id"], text, buttons=btns, parse_mode="html")
        if new:
            g["join_msg_id"] = new.id
            try: await client.delete_messages(g["group_id"], mid)
            except Exception: pass
    except Exception as e: logger.exception(f"td refresh m3: {e}")


async def td_start_game(g):
    g["state"] = "playing"
    order = list(g["players"].keys())
    random.shuffle(order)
    g["order"] = order; g["current_index"] = 0
    pl = "\n".join([f"  {E('point', '👉')} <b>{h(g['players'][uid]['name'])}</b>" for uid in order])
    await safe_send(g["group_id"],
                    f"{E('party', '🎉')} <b>بازی شروع شد!</b> {E('party', '🎉')}\n{DIV}\n\n"
                    f"🎲 <b>ترتیب تصادفی بازیکنان:</b>\n{pl}\n\n"
                    f"{E('rocket', '🚀')} <b>آماده باشید...</b>", parse_mode="html")
    await asyncio.sleep(2)
    await td_next_turn(g)


async def td_next_turn(g):
    if g["state"] != "playing": return
    if not g["order"]:
        await td_finish(g); return
    n = len(g["order"])
    if all(g["players"][uid]["turns_done"] >= g["turns_per_player"] for uid in g["order"]):
        await td_finish(g); return
    tries = 0
    while tries < n:
        idx = g["current_index"] % n
        uid = g["order"][idx]
        if g["players"][uid]["turns_done"] < g["turns_per_player"]: break
        g["current_index"] += 1; tries += 1
    else:
        await td_finish(g); return
    uid = g["order"][g["current_index"] % n]
    p = g["players"][uid]
    g["current_player"] = uid
    g["current_state"] = "picking_choice"
    if g.get("turn_msg_id"):
        try: await client.delete_messages(g["group_id"], g["turn_msg_id"])
        except Exception: pass
    btns = []
    for k, e, n in TD_CATEGORIES_ALL:
        if k not in g["categories"]: continue
        btns.append(Button.inline(f"{e} {n}", data=f"td_pick:{k}".encode()))
    rows = []
    for i in range(0, len(btns), 2):
        rows.append(btns[i:i+2])
    rows.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"td_skip_turn")])
    total = g["timeout_sec"]
    bar = time_bar_colored(total, total)
    tb = time_badge(total, total)
    text = (
        f"{E('magic', '🎭')} <b>TRUTH or DARE</b> {E('magic', '🎭')}\n"
        f"{DIV}\n\n"
        f"{E('target', '🎯')} <b>نوبت {h(p['name'])}</b>\n"
        f"{E('chart', '📊')} نوبت <code>{p['turns_done']+1}/{g['turns_per_player']}</code>\n"
        f"{DIV2}\n"
        f"{tb} <b>زمان:</b> <code>{total}</code> ثانیه\n"
        f"{bar}  <b>100%</b>\n"
        f"{DIV2}\n\n"
        f"{E('sparkle', '✨')} <b>{h(p['name'])}</b> یکی رو انتخاب کن:\n\n"
        f"  🎭 <b>حقیقت</b>  <i>— سوال صادقانه</i>\n"
        f"  🔥 <b>حقیقت +18</b>  <i>— سوال جسورانه</i>\n"
        f"  ⚡ <b>جرعت</b>  <i>— چالش بامزه</i>\n"
        f"  💋 <b>جرعت +18</b>  <i>— چالش جسورانه</i>\n\n"
        f"{E('info', 'ℹ️')} <i>فقط خودت کلیک کن</i>"
    )
    sent = await safe_send(g["group_id"], text, buttons=rows, parse_mode="html")
    if sent: g["turn_msg_id"] = sent.id
    if g.get("timeout_task"):
        try: g["timeout_task"].cancel()
        except Exception: pass
    g["timeout_task"] = asyncio.create_task(td_live_countdown(g, uid, total))


async def td_live_countdown(g, uid, total):
    logger.info(f"⏱ TD countdown {total}s")
    try:
        gid = g["group_id"]
        last_shown = None
        for remaining in range(total, -1, -1):
            if g.get("current_player") != uid or g.get("current_state") != "picking_choice":
                return
            p = g["players"].get(uid)
            if not p or g.get("turn_msg_id") is None:
                await asyncio.sleep(0.5); continue
            bar = time_bar_colored(remaining, total)
            tb = time_badge(remaining, total)
            pct = int(100 * remaining / total) if total > 0 else 0
            btns = []
            for k, e, n in TD_CATEGORIES_ALL:
                if k not in g["categories"]: continue
                btns.append(Button.inline(f"{e} {n}", data=f"td_pick:{k}".encode()))
            rows = []
            for i in range(0, len(btns), 2):
                rows.append(btns[i:i+2])
            rows.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"td_skip_turn")])
            if remaining <= 3 and remaining > 0:
                tw = f"{E('alert', '🚨')} <b><i>زود باش! فقط {remaining} ثانیه!</i></b>"
            elif remaining == 0:
                tw = f"{E('hourglass', '⏰')} <b>وقت تموم شد!</b>"
            else:
                tw = f"{tb} <b>زمان:</b> <code>{remaining}</code> ثانیه"
            text = (
                f"{E('magic', '🎭')} <b>TRUTH or DARE</b> {E('magic', '🎭')}\n"
                f"{DIV}\n\n"
                f"{E('target', '🎯')} <b>نوبت {h(p['name'])}</b>\n"
                f"{E('chart', '📊')} نوبت <code>{p['turns_done']+1}/{g['turns_per_player']}</code>\n"
                f"{DIV2}\n{tw}\n{bar}  <b>{pct}%</b>\n"
                f"{DIV2}\n\n"
                f"{E('sparkle', '✨')} <b>{h(p['name'])}</b> یکی رو انتخاب کن:\n\n"
                f"  🎭 <b>حقیقت</b>  <i>— سوال صادقانه</i>\n"
                f"  🔥 <b>حقیقت +18</b>  <i>— سوال جسورانه</i>\n"
                f"  ⚡ <b>جرعت</b>  <i>— چالش بامزه</i>\n"
                f"  💋 <b>جرعت +18</b>  <i>— چالش جسورانه</i>\n\n"
                f"{E('info', 'ℹ️')} <i>فقط خودت کلیک کن</i>"
            )
            if text != last_shown:
                ok = await safe_edit_msg(gid, g["turn_msg_id"], text, buttons=rows)
                if ok: last_shown = text
            if remaining == 0: break
            await asyncio.sleep(1)
        if g.get("current_player") == uid and g.get("current_state") == "picking_choice":
            p = g["players"].get(uid)
            if p:
                await safe_send(g["group_id"],
                                f"{E('hourglass', '⏰')} <b>وقت {h(p['name'])} تموم شد!</b>\n"
                                f"{E('info', 'ℹ️')} نوبت بعدی می‌ره...", parse_mode="html")
                p["turns_done"] += 1
                await asyncio.sleep(1.5)
                g["current_index"] += 1
                await td_next_turn(g)
    except asyncio.CancelledError: return
    except Exception as e: logger.exception(f"td cd err: {e}")


async def td_play(g, uid, kind):
    gid = g["group_id"]
    p = g["players"].get(uid)
    if not p: return
    if g.get("turn_msg_id"):
        try: await client.delete_messages(gid, g["turn_msg_id"]); g["turn_msg_id"] = None
        except Exception: pass
    if g.get("timeout_task"):
        try: g["timeout_task"].cancel()
        except Exception: pass
    label = next((n for k, e, n in TD_CATEGORIES_ALL if k == kind), kind)
    em_map = {"truth": "🎭", "truth18": "🔥", "dare": "⚡", "dare18": "💋"}
    em = em_map.get(kind, "🎭")
    wm = await safe_send(gid,
                         f"{em} <b>{h(p['name'])}</b> انتخاب کرد: <b>{label}</b>\n\n"
                         f"{E('brain', '🧠')} <i>هوش مصنوعی در حال ساخت...</i>",
                         parse_mode="html")
    txt = None
    for _ in range(3):
        candidate = await ai_generate_td(kind, p["name"], g.get("used_texts", []))
        if candidate and candidate not in g["used_texts"]:
            txt = candidate; break
        await asyncio.sleep(0.5)
    if not txt:
        try: await wm.delete()
        except Exception: pass
        await safe_send(gid, f"{E('cross', '❌')} <b>خطا در ساخت محتوا</b>", parse_mode="html")
        p["turns_done"] += 1
        await asyncio.sleep(2)
        g["current_index"] += 1
        await td_next_turn(g); return
    g["used_texts"].append(txt)
    if len(g["used_texts"]) > 60: g["used_texts"] = g["used_texts"][-60:]
    header = {
        "truth": f"{E('magic', '🎭')} <b>حقیقت</b> {E('magic', '🎭')}",
        "truth18": f"{E('fire', '🔥')} <b>حقیقت +18</b> {E('fire', '🔥')}",
        "dare": f"{E('bolt', '⚡')} <b>جرعت</b> {E('bolt', '⚡')}",
        "dare18": f"{E('heart', '💋')} <b>جرعت +18</b> {E('heart', '💋')}",
    }.get(kind, "🎭")
    result = (f"{header}\n{DIV}\n\n"
              f"{E('user', '👤')} <b>{h(p['name'])}</b>\n"
              f"{DIV2}\n\n"
              f"{E('message', '💬')} <b>متن:</b>\n"
              f"<blockquote>{h(txt)}</blockquote>\n\n"
              f"{DIV2}\n"
              f"{E('sparkle', '✨')} <i>انجامش بده و بگو توی گروه!</i>")
    try: await wm.delete()
    except Exception: pass
    btns = [[Button.inline("▶️ نوبت بعدی (ادمین)", data=b"td_next_now")]]
    await safe_send(gid, result, buttons=btns, parse_mode="html")
    p["turns_done"] += 1
    asyncio.create_task(td_auto_next(g, uid))


async def td_auto_next(g, uid):
    try:
        await asyncio.sleep(25)
    except asyncio.CancelledError: return
    if g.get("current_player") != uid: return
    if g.get("current_state") == "moving_on": return
    g["current_state"] = "moving_on"
    g["current_index"] += 1
    await td_next_turn(g)


async def td_skip_turn(g):
    if g["state"] != "playing": return
    cur = g.get("current_player")
    if not cur: return
    if g.get("timeout_task"):
        try: g["timeout_task"].cancel()
        except Exception: pass
    p = g["players"].get(cur)
    pn = p["name"] if p else "?"
    if g.get("turn_msg_id"):
        try: await client.delete_messages(g["group_id"], g["turn_msg_id"]); g["turn_msg_id"] = None
        except Exception: pass
    await safe_send(g["group_id"],
                    f"{E('skip', '⏭')} <b>نوبت {h(pn)} رد شد</b>\n"
                    f"{E('info', 'ℹ️')} <i>در حال رفتن به نوبت بعدی...</i>",
                    parse_mode="html")
    if p: p["turns_done"] += 1
    await asyncio.sleep(1.5)
    g["current_index"] += 1
    await td_next_turn(g)


async def td_finish(g):
    g["state"] = "finished"
    try:
        if g.get("timeout_task"): g["timeout_task"].cancel()
    except Exception: pass
    ps = g["players"]
    lines = [f"{E('flag', '🏁')} <b>بازی جرعت یا حقیقت تموم شد!</b>\n{DIV}\n\n",
             f"{E('stats', '📊')} <b>خلاصه بازیکنان:</b>"]
    for uid, p in ps.items():
        lines.append(f"  {E('point', '👉')} <b>{h(p['name'])}</b> — "
                     f"<code>{p['turns_done']}</code> نوبت")
    lines.append(f"\n{E('party', '🎉')} <b>ممنون که بازی کردید!</b>")
    await safe_send(g["group_id"], "\n".join(lines), parse_mode="html")
    for uid, p in ps.items():
        if p["turns_done"] > 0:
            try: db.add_points(uid, p["name"], p["turns_done"] * 3, joined=True)
            except Exception: pass
    TD_ACTIVE_GAMES.pop(g["group_id"], None)


@client.on(events.NewMessage())
async def on_group_message(event):
    try:
        if event.is_private: return
        me = await client.get_me()
        if event.sender_id == me.id: return
        chat = await event.get_chat()
        if hasattr(chat, "title"):
            try: db.save_group(event.chat_id, chat.title, getattr(chat, "username", None))
            except Exception: pass
        raw = (event.raw_text or "").strip()
        if "خلوته" in raw:
            await safe_reply(event, f"{E('laugh', '😂')} <b>شیک بزن شلوغ بشه</b> {E('laugh', '😂')}",
                             parse_mode="html")
            return
        if not is_admin(event.sender_id): return
        if raw in ("جرعت", "حقیقت", "جرعت حقیقت", "جرعت یا حقیقت"):
            uid = event.sender_id
            game = create_td_setup(uid, event.chat_id)
            await safe_reply(event,
                             f"{E('check', '✅')} <b>منوی جرعت یا حقیقت به پیوی شما فرستاده شد</b>\n"
                             f"{DIV}\n\n{E('magic', '🎭')} تنظیمات رو توی پیوی انجام بده.",
                             parse_mode="html")
            try: await td_send_setup_menu(uid, "welcome", game)
            except Exception as e: logger.exception(f"td setup: {e}")
            return
        if raw in ("چالش", "چالش جدید", "کوییز", "کوییز جدید"):
            uid = event.sender_id
            game = create_setup_game(uid, event.chat_id)
            await safe_reply(event,
                             f"{E('check', '✅')} <b>منوی کوییز به پیوی شما فرستاده شد</b>\n"
                             f"{DIV}\n\n{E('brain', '🧠')} تنظیمات رو توی پیوی انجام بده.",
                             parse_mode="html")
            try: await quiz_send_setup_menu(uid, "welcome", game)
            except Exception as e: logger.exception(f"quiz setup: {e}")
            return
        if raw.startswith("نظرسنجی"):
            content = raw[len("نظرسنجی"):].strip().lstrip(":").lstrip("：").strip()
            parts = [p.strip() for p in content.split("|") if p.strip()]
            if len(parts) < 3:
                await safe_reply(event, f"{E('warning', '⚠️')} <code>نظرسنجی: عنوان | گ1 | گ2</code>",
                                 parse_mode="html")
                return
            title = parts[0]; options = parts[1:]; deadline = None
            last = parts[-1]
            if len(parts) > 3 and re.match(r"^\d+\s*(m|min|h|hr|d|day|د|دقیقه|س|ساعت|روز)?$", last):
                maybe = parse_duration(last)
                if maybe:
                    deadline = (datetime.now(IRAN_TZ) + maybe).isoformat()
                    options = parts[1:-1]
            if len(options) < 2:
                await safe_reply(event, f"{E('cross', '❌')} حداقل ۲ گزینه!", parse_mode="html")
                return
            cid = db.create_challenge(event.sender_id, event.chat_id, title, "",
                                       ch_type="poll", options=options, deadline=deadline)
            link = f"https://t.me/{BOT_USERNAME}?start=ch_{cid}"
            txt = build_challenge_text(cid, title, "", "poll", options, deadline)
            sent = await safe_respond(event, txt, parse_mode="html",
                                      buttons=[[Button.url("🎯 شرکت می‌کنم", link)]])
            if sent: db.set_challenge_message(cid, sent.id)
            return
        if raw.startswith("چالش"):
            content = raw[len("چالش"):].strip().lstrip(":").lstrip("：").strip()
            parts = [p.strip() for p in content.split("|") if p.strip()]
            if len(parts) < 2:
                await safe_reply(event, f"{E('warning', '⚠️')} <code>چالش: عنوان | سوال</code>",
                                 parse_mode="html")
                return
            title = parts[0]; question = parts[1]; deadline = None
            if len(parts) >= 3:
                maybe = parse_duration(parts[2])
                if maybe: deadline = (datetime.now(IRAN_TZ) + maybe).isoformat()
            cid = db.create_challenge(event.sender_id, event.chat_id, title, question,
                                       ch_type="text", deadline=deadline)
            link = f"https://t.me/{BOT_USERNAME}?start=ch_{cid}"
            txt = build_challenge_text(cid, title, question, "text", None, deadline)
            sent = await safe_respond(event, txt, parse_mode="html",
                                      buttons=[[Button.url("🎯 شرکت می‌کنم", link)]])
            if sent: db.set_challenge_message(cid, sent.id)
            return
    except Exception as ex: logger.exception(f"group handler: {ex}")


@client.on(events.NewMessage(func=lambda e: e.is_private))
async def on_private(event):
    try:
        me = await client.get_me()
        if event.sender_id == me.id: return
        uid = event.sender_id
        raw = (event.raw_text or "").strip()
        try: sender = await event.get_sender()
        except Exception: sender = None
        uname = user_name(sender)
        username = getattr(sender, "username", None) if sender else None
        db.save_user(uid, uname, username)

        if raw.startswith("/start"):
            parts = raw.split(None, 1)
            payload = parts[1].strip() if len(parts) > 1 else ""
            if payload.startswith("anon_"):
                try: target = int(payload[5:])
                except ValueError: target = 0
                if target == uid or target == 0:
                    await safe_respond(event, f"{E('cross', '❌')} لینک نامعتبره", parse_mode="html"); return
                set_state(uid, "awaiting_anon", target=target)
                await safe_respond(event,
                                   f"{E('heart', '💌')} <b>پیام ناشناس</b>\n{DIV}\n\nپیامت رو بنویس:",
                                   parse_mode="html",
                                   buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
                return
            if payload.startswith("ch_"):
                try: cid = int(payload[3:])
                except ValueError: cid = 0
                ch = db.get_challenge(cid)
                if not ch or not ch.get("is_active"):
                    await safe_respond(event, f"{E('cross', '❌')} چالش یافت نشد یا بسته شده",
                                       parse_mode="html")
                    return
                ct = ch.get("ch_type") or "text"
                if ct == "poll":
                    if db.has_voted(cid, uid):
                        await safe_respond(event, f"{E('info', 'ℹ️')} قبلاً رأی دادی", parse_mode="html"); return
                    opts = json.loads(ch["options"]) if ch.get("options") else []
                    ol = "\n".join([f"  {E('point', '👉')} <b>{i+1}.</b> {h(o)}"
                                    for i, o in enumerate(opts)])
                    txt = (f"{E('chart', '📊')} <b>نظرسنجی ناشناس</b>\n{DIV}\n\n"
                           f"{E('tag', '🏷️')} <b>عنوان:</b> {h(ch['title'])}\n\n"
                           f"{E('list', '📋')} <b>گزینه‌ها:</b>\n{ol}\n\n"
                           f"{E('rocket', '🚀')} یک گزینه انتخاب کن:")
                    btns = [[Button.inline(f"◽ {o[:30]}", data=f"vote:{cid}:{i}".encode())]
                            for i, o in enumerate(opts)]
                    btns.append([Button.inline("❌ لغو", data=b"cancel")])
                    await safe_respond(event, txt, buttons=btns, parse_mode="html")
                    return
                if db.has_answered(cid, uid):
                    await safe_respond(event, f"{E('info', 'ℹ️')} قبلاً شرکت کردی", parse_mode="html"); return
                txt = (f"{E('diamond', '💎')} <b>چالش ناشناس</b>\n{DIV}\n\n"
                       f"{E('tag', '🏷️')} <b>عنوان:</b> {h(ch['title'])}\n\n"
                       f"{E('message', '💬')} <b>سوال:</b> {h(ch['question'])}\n\n"
                       f"{E('alert', '⚠️')} شرکت می‌کنی؟")
                btns = [[Button.inline("✅ بله", data=f"join:{cid}".encode()),
                         Button.inline("❌ لغو", data=b"cancel")]]
                await safe_respond(event, txt, buttons=btns, parse_mode="html")
                return
            if is_admin(uid): await send_admin_menu(event)
            else:
                await safe_respond(event,
                                   f"{E('crown', '👑')} <b>UNICORN ANONY BOT</b>\n{DIV}\n\n"
                                   f"{E('wave', '👋')} سلام!\n\n"
                                   f"{E('brain', '🧠')} کوییز هوشمند + {E('magic', '🎭')} جرعت حقیقت\n"
                                   f"{E('diamond', '💎')} چالش ناشناس\n"
                                   f"{E('heart', '💌')} پیام ناشناس\n\n"
                                   f"{E('info', 'ℹ️')} /help",
                                   parse_mode="html")
            return

        if raw == "/help":
            await safe_respond(event, f"{E('info', 'ℹ️')} /me /top /mylink /help", parse_mode="html"); return
        if raw == "/me":
            sc = db.get_score(uid) or {}
            rank = db.get_rank(uid); nr = db.count_anon_received(uid)
            await safe_respond(event,
                               f"{E('user', '👤')} <b>پروفایل</b>\n{DIV}\n\n"
                               f"{E('tag', '🏷️')} {h(uname)}\n"
                               f"{E('id', '🆔')} <code>{uid}</code>\n\n"
                               f"{E('star', '⭐')} امتیاز: <code>{sc.get('points', 0)}</code>\n"
                               f"{E('diamond', '💎')} چالش‌ها: <code>{sc.get('challenges_joined', 0)}</code>\n"
                               f"{E('heart', '💌')} پیام ناشناس: <code>{nr}</code>\n"
                               f"{E('trophy', '🏆')} رتبه: {('#' + str(rank)) if rank else '—'}",
                               parse_mode="html")
            return
        if raw == "/top":
            top = db.get_top(10)
            if not top:
                await safe_respond(event, f"{E('info', 'ℹ️')} خالیه", parse_mode="html"); return
            medals = ["🥇", "🥈", "🥉"] + ["🎖"] * 7
            lines = [f"{E('trophy', '🏆')} <b>لیدربورد</b>\n{DIV}\n"]
            for i, u in enumerate(top):
                m = medals[i] if i < len(medals) else "•"
                lines.append(f"{m} <b>{h(u['user_name'] or 'ناشناس')}</b> — <code>{u['points']}</code>")
            await safe_respond(event, "\n".join(lines), parse_mode="html")
            return
        if raw == "/mylink":
            link = f"https://t.me/{BOT_USERNAME}?start=anon_{uid}"
            n = db.count_anon_received(uid)
            await safe_respond(event,
                               f"{E('heart', '💌')} <b>لینک NGL</b>\n{DIV}\n\n<code>{link}</code>\n\n"
                               f"{E('stats', '📊')} دریافتی: <code>{n}</code>",
                               parse_mode="html",
                               buttons=[
                                   [Button.url("📤 اشتراک", f"https://t.me/share/url?url={link}")],
                                   [Button.inline("📥 صندوق", data=b"anon_inbox")],
                               ])
            return
        if raw == "/stats" and is_admin(uid):
            al = "، ".join([f"<code>{x}</code>" for x in sorted(ALL_ADMINS)])
            await safe_respond(event,
                               f"{E('stats', '📊')} <b>آمار</b>\n{DIV}\n\n"
                               f"{E('group', '🏢')} گروه‌ها: <code>{len(db.get_groups())}</code>\n"
                               f"{E('user', '👤')} کاربران: <code>{db.count_users()}</code>\n"
                               f"{E('diamond', '💎')} چالش‌ها: <code>{len(db.get_challenges())}</code>\n"
                               f"{E('fire', '🔥')} فعال: <code>{db.count_active_challenges()}</code>\n\n"
                               f"{E('crown', '👑')} <b>ادمین‌ها:</b>\n{al}",
                               parse_mode="html")
            return
        if raw == "/broadcast" and is_admin(uid):
            set_state(uid, "awaiting_broadcast")
            await safe_respond(event, f"{E('message', '💬')} پیام برادکست رو بفرست:",
                               parse_mode="html",
                               buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
            return
        if raw.startswith("/search") and is_admin(uid):
            parts = raw.split(None, 1)
            if len(parts) < 2:
                await safe_respond(event, f"{E('search', '🔍')} <code>/search کلمه</code>", parse_mode="html"); return
            res = db.search_challenges(uid, parts[1].strip())
            if not res:
                await safe_respond(event, f"{E('info', 'ℹ️')} نتیجه‌ای نیس", parse_mode="html"); return
            lines = [f"{E('search', '🔍')} نتایج:\n"]
            for c_ in res[:10]:
                lines.append(f"{E('diamond', '💎')} <b>#{c_['id']}</b> {h(c_['title'])}")
            await safe_respond(event, "\n".join(lines), parse_mode="html")
            return

        st = get_state(uid)
        if st:
            state = st.get("state"); data = st.get("data", {})
            if state == "awaiting_anon":
                if not raw or len(raw) > MAX_ANSWER_LEN:
                    await safe_respond(event, f"{E('warning', '⚠️')} پیام نامعتبره", parse_mode="html"); return
                target = data.get("target")
                if not target: clear_state(uid); return
                db.save_anon(target, uid, raw)
                db.add_points(target, "", 5, ngl=True)
                db.add_points(uid, uname, 2, sent=True)
                clear_state(uid)
                await safe_respond(event,
                                   f"{E('check', '✅')} ارسال شد!\n{E('shield', '🛡')} هویتت مخفی موند",
                                   parse_mode="html")
                try:
                    n = db.count_anon_received(target)
                    await safe_send(target,
                                    f"{E('heart', '💌')} <b>پیام ناشناس جدید!</b>\n{DIV}\n\n"
                                    f"<blockquote>{h(raw)}</blockquote>\n\n"
                                    f"{E('stats', '📊')} کل: <code>{n}</code>\n"
                                    f"{E('time', '⏱')} {now_str()}",
                                    parse_mode="html",
                                    buttons=[[Button.inline("📥 صندوق", data=b"anon_inbox")]])
                except Exception: pass
                return
            if state == "awaiting_broadcast":
                clear_state(uid)
                uids = db.get_all_users()
                await safe_respond(event, f"{E('rocket', '🚀')} ارسال به {len(uids)} کاربر...",
                                   parse_mode="html")
                sent, failed = 0, 0
                for i, u in enumerate(uids):
                    try:
                        await safe_send(u, raw, parse_mode="html"); sent += 1
                    except FloodWaitError as fwe:
                        await asyncio.sleep(fwe.seconds + 1)
                        try:
                            await safe_send(u, raw, parse_mode="html"); sent += 1
                        except Exception: failed += 1
                    except Exception: failed += 1
                    if i % 25 == 24: await asyncio.sleep(1.2)
                await safe_respond(event,
                                   f"{E('check', '✅')} تمام شد\n"
                                   f"ارسال: <code>{sent}</code> | ناموفق: <code>{failed}</code>",
                                   parse_mode="html")
                return
            if state == "awaiting_title":
                if not raw: return
                data["title"] = raw[:200]
                ct = data.get("type", "text")
                set_state(uid, "awaiting_question" if ct == "text" else "awaiting_options", **data)
                if ct == "text":
                    await safe_respond(event, f"{E('message', '💬')} سوال رو بفرست:",
                                       parse_mode="html",
                                       buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
                else:
                    await safe_respond(event, f"{E('list', '📋')} گزینه‌ها با <code>|</code>:",
                                       parse_mode="html",
                                       buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
                return
            if state == "awaiting_question":
                if not raw: return
                data["question"] = raw[:800]
                set_state(uid, "awaiting_deadline", **data)
                await _ask_deadline(event); return
            if state == "awaiting_options":
                opts = [p.strip() for p in raw.split("|") if p.strip()]
                if len(opts) < 2:
                    await safe_respond(event, f"{E('warning', '⚠️')} حداقل ۲ گزینه!", parse_mode="html"); return
                data["options"] = opts[:10]
                set_state(uid, "awaiting_deadline", **data)
                await _ask_deadline(event); return
            if state == "awaiting_deadline":
                td = parse_duration(raw)
                if td is None and raw not in ("", "-", "ندارد", "بدون", "skip"):
                    await safe_respond(event, f"{E('warning', '⚠️')} فرمت اشتباه", parse_mode="html"); return
                dl = (datetime.now(IRAN_TZ) + td).isoformat() if td else None
                data["deadline"] = dl
                set_state(uid, "awaiting_group", **data)
                await _ask_group(event, data); return
            if state == "awaiting_answer":
                cid = data.get("challenge_id")
                ch = db.get_challenge(cid) if cid else None
                if not ch:
                    clear_state(uid)
                    await safe_respond(event, f"{E('cross', '❌')} چالش یافت نشد", parse_mode="html"); return
                if not raw or len(raw) > MAX_ANSWER_LEN:
                    await safe_respond(event, f"{E('warning', '⚠️')} پاسخ نامعتبره", parse_mode="html"); return
                db.save_answer(cid, uid, uname, username, raw)
                db.add_points(uid, uname, 10, joined=True)
                clear_state(uid)
                await safe_respond(event,
                                   f"{E('check', '✅')} ثبت شد!\n{E('star', '⭐')} +۱۰ امتیاز",
                                   parse_mode="html")
                try:
                    await safe_send(ch["admin_id"],
                                    f"{E('alert', '🚨')} <b>پاسخ جدید!</b>\n{DIV}\n\n"
                                    f"{E('diamond', '💎')} {h(ch['title'])}\n"
                                    f"{E('user', '👤')} {h(uname)}\n"
                                    f"{E('id', '🆔')} <a href=\"tg://user?id={uid}\">{uid}</a>\n\n"
                                    f"<blockquote>{h(raw)}</blockquote>",
                                    parse_mode="html")
                except Exception: pass
                return

        if is_admin(uid): await send_admin_menu(event)
        else:
            await safe_respond(event,
                               f"{E('info', 'ℹ️')} برای شرکت در بازی‌ها از دکمه‌های گروه استفاده کن.\n"
                               f"{E('rocket', '🚀')} /help",
                               parse_mode="html")
    except Exception as ex: logger.exception(f"pm handler: {ex}")


async def _ask_deadline(event):
    await safe_respond(event,
                       f"{E('hourglass', '⏳')} <b>مهلت</b>\n{DIV}\n\n"
                       f"مثال: <code>30</code>, <code>2h</code>, <code>1d</code>",
                       parse_mode="html",
                       buttons=[
                           [Button.inline("⏰ ۳۰ دقیقه", data=b"dl:30"),
                            Button.inline("⏰ ۱ ساعت", data=b"dl:60")],
                           [Button.inline("⏰ ۶ ساعت", data=b"dl:360"),
                            Button.inline("⏰ ۱ روز", data=b"dl:1440")],
                           [Button.inline("🚫 بدون", data=b"dl:none"),
                            Button.inline("❌ لغو", data=b"cancel")],
                       ])


async def _ask_group(event, data):
    groups = db.get_groups()
    if not groups:
        await safe_respond(event, f"{E('cross', '❌')} گروهی یافت نشد", parse_mode="html")
        clear_state(event.sender_id); return
    btns = [[Button.inline(f"🏢 {(g.get('title') or '—')[:40]}",
                           data=f"chgrp:{g['group_id']}".encode())] for g in groups[:20]]
    btns.append([Button.inline("❌ لغو", data=b"cancel")])
    await safe_respond(event, f"{E('group', '🏢')} کدوم گروه؟", buttons=btns, parse_mode="html")


@client.on(events.CallbackQuery())
async def on_cb(event):
    try:
        uid = event.sender_id
        data = event.data.decode("utf-8", "ignore")

        if data == "quiz_join":
            g = _find_game_for_callback(event)
            if not g: await event.answer("❌ بازی پیدا نشد!", alert=True); return
            if g.get("state") != "waiting":
                await event.answer("⏳ بازی شروع شده!", alert=True); return
            if uid in g["players"]:
                await event.answer("⚠️ قبلاً شرکت کردی!", alert=True); return
            try:
                s = await event.get_sender()
                name = user_name(s); uu = getattr(s, "username", None)
            except Exception:
                name = str(uid); uu = None
            g["players"][uid] = {"name": name, "username": uu, "score": 0, "asked": 0,
                                  "joined_at": now_iso()}
            await event.answer(f"✅ {name} عزیز، ثبت شد!")
            try: await quiz_refresh_join(g)
            except Exception as e: logger.exception(f"quiz refresh: {e}")
            return

        if data == "quiz_start":
            g = _find_game_for_callback(event)
            if not g or g.get("state") != "waiting":
                await event.answer("❌ بازی فعال نیست!", alert=True); return
            if not is_admin(uid):
                await event.answer("⛔ فقط ادمین!", alert=True); return
            if len(g["players"]) < 1:
                await event.answer("⚠️ حداقل ۱ بازیکن!", alert=True); return
            await event.answer("🚀 شروع!")
            try:
                if g.get("join_msg_id"):
                    await client.edit_message(g["group_id"], g["join_msg_id"],
                        text=(f"{E('check', '✅')} <b>بازی شروع شد!</b>\n"
                              f"{E('user', '👤')} <b>{len(g['players'])}</b> بازیکن"),
                        parse_mode="html", buttons=None)
            except Exception: pass
            asyncio.create_task(quiz_start_game(g)); return

        if data.startswith("quiz_pick:"):
            try: idx = int(data.split(":", 1)[1])
            except Exception: await event.answer("خطا", alert=True); return
            g = _find_game_for_callback(event)
            if not g or g.get("state") != "playing":
                await event.answer("❌", alert=True); return
            if g.get("current_player") != uid:
                await event.answer("⛔ نوبت تو نیست!", alert=True); return
            if g.get("current_state") != "picking_category":
                await event.answer("الان نمیشه", alert=True); return
            await event.answer(f"🎯 {QUIZ_CATEGORIES[idx][2]}")
            asyncio.create_task(quiz_ask_question(g, uid, idx)); return

        if data.startswith("quiz_ans:"):
            try: idx = int(data.split(":", 1)[1])
            except Exception: await event.answer("خطا", alert=True); return
            g = _find_game_for_callback(event)
            if not g or g.get("state") != "playing":
                await event.answer("❌", alert=True); return
            cq = g.get("current_question")
            if not cq or cq.get("answered"):
                await event.answer("سوال بسته شده", alert=True); return
            if cq.get("player") != uid:
                await event.answer("⛔ مال تو نیست!", alert=True); return
            await event.answer("✅")
            asyncio.create_task(quiz_answer(g, uid, idx)); return

        if data == "quiz_skip_turn":
            g = _find_game_for_callback(event)
            if not g or g.get("state") != "playing":
                await event.answer("❌", alert=True); return
            if not is_admin(uid):
                await event.answer("⛔ فقط ادمین!", alert=True); return
            await event.answer("⏭ رد شد")
            asyncio.create_task(quiz_skip_turn(g)); return

        if data == "quiz_cancel":
            SETUP_GAMES.pop(uid, None)
            await event.answer("❌ لغو شد")
            try: await safe_edit(event, f"{E('cross', '❌')} کوییز لغو شد",
                                  parse_mode="html", buttons=None)
            except Exception: pass
            return

        if data == "quiz_setup":
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer()
            text, btns = render_categories_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "quiz_noop":
            await event.answer(); return

        if data.startswith("quiz_cat:"):
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            try:
                idx = int(data.split(":", 1)[1]); _, _, name = QUIZ_CATEGORIES[idx]
            except Exception: await event.answer("خطا", alert=True); return
            if name in g["categories"]:
                g["categories"].remove(name); await event.answer(f"➖ {name}")
            else:
                g["categories"].append(name); await event.answer(f"✅ {name}")
            text, btns = render_categories_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "quiz_backcat":
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer()
            text, btns = render_categories_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "quiz_settings":
            g = SETUP_GAMES.get(uid)
            if not g or not g["categories"]:
                await event.answer("اول دسته انتخاب کن", alert=True); return
            await event.answer()
            text, btns = render_settings_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data.startswith("quiz_q:"):
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            g["questions_per_player"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {g['questions_per_player']}")
            text, btns = render_settings_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data.startswith("quiz_t:"):
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            g["time_per_question"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {g['time_per_question']} ثانیه")
            text, btns = render_settings_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data.startswith("quiz_s:"):
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            g["target_score"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {'بدون' if g['target_score'] == 0 else g['target_score']}")
            text, btns = render_settings_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "quiz_summary":
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer()
            text, btns = render_summary_menu(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "quiz_create":
            g = SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer("✅")
            try:
                await safe_edit(event,
                                f"{E('check', '✅')} <b>بازی ساخته شد!</b>\n{DIV}\n\n"
                                f"{E('info', 'ℹ️')} پیام شرکت توی گروه فرستاده شد.",
                                parse_mode="html", buttons=None)
            except Exception: pass
            g["state"] = "waiting"
            ACTIVE_GAMES[g["group_id"]] = g
            SETUP_GAMES.pop(uid, None)
            await quiz_broadcast_join(g); return

        if data == "td_join":
            g = _find_td_game(event)
            if not g: await event.answer("❌", alert=True); return
            if g.get("state") != "waiting":
                await event.answer("⏳ شروع شده!", alert=True); return
            if uid in g["players"]:
                await event.answer("⚠️ قبلاً شرکت کردی!", alert=True); return
            try:
                s = await event.get_sender()
                name = user_name(s); uu = getattr(s, "username", None)
            except Exception:
                name = str(uid); uu = None
            g["players"][uid] = {"name": name, "username": uu, "turns_done": 0,
                                  "joined_at": now_iso()}
            await event.answer(f"✅ {name} ثبت شد!")
            try: await td_refresh_join(g)
            except Exception as e: logger.exception(f"td refresh: {e}")
            return

        if data == "td_start":
            g = _find_td_game(event)
            if not g or g.get("state") != "waiting":
                await event.answer("❌", alert=True); return
            if not is_admin(uid):
                await event.answer("⛔ فقط ادمین!", alert=True); return
            if len(g["players"]) < 2:
                await event.answer("⚠️ حداقل ۲ بازیکن!", alert=True); return
            await event.answer("🚀")
            try:
                if g.get("join_msg_id"):
                    await client.edit_message(g["group_id"], g["join_msg_id"],
                        text=(f"{E('check', '✅')} <b>بازی شروع شد!</b>\n"
                              f"{E('user', '👤')} <b>{len(g['players'])}</b> بازیکن"),
                        parse_mode="html", buttons=None)
            except Exception: pass
            asyncio.create_task(td_start_game(g)); return

        if data.startswith("td_pick:"):
            try: kind = data.split(":", 1)[1]
            except Exception: await event.answer("خطا", alert=True); return
            g = _find_td_game(event)
            if not g or g.get("state") != "playing":
                await event.answer("❌", alert=True); return
            if g.get("current_player") != uid:
                await event.answer("⛔ نوبت تو نیست!", alert=True); return
            if g.get("current_state") != "picking_choice":
                await event.answer("الان نمیشه", alert=True); return
            await event.answer("✅")
            asyncio.create_task(td_play(g, uid, kind)); return

        if data == "td_skip_turn":
            g = _find_td_game(event)
            if not g or g.get("state") != "playing":
                await event.answer("❌", alert=True); return
            if not is_admin(uid):
                await event.answer("⛔", alert=True); return
            await event.answer("⏭")
            asyncio.create_task(td_skip_turn(g)); return

        if data == "td_next_now":
            g = _find_td_game(event)
            if not g or g.get("state") != "playing":
                await event.answer("❌", alert=True); return
            if not is_admin(uid):
                await event.answer("⛔", alert=True); return
            await event.answer("▶️")
            if g.get("current_state") == "moving_on": return
            g["current_state"] = "moving_on"
            g["current_index"] += 1
            asyncio.create_task(td_next_turn(g)); return

        if data == "td_setup":
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer()
            text, btns = render_td_categories(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "td_noop":
            await event.answer(); return

        if data.startswith("td_cat:"):
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            kind = data.split(":", 1)[1]
            if kind in g["categories"]:
                g["categories"].remove(kind); await event.answer("➖")
            else:
                g["categories"].append(kind); await event.answer("✅")
            text, btns = render_td_categories(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "td_backcat":
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer()
            text, btns = render_td_categories(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "td_settings":
            g = TD_SETUP_GAMES.get(uid)
            if not g or not g["categories"]:
                await event.answer("اول دسته", alert=True); return
            await event.answer()
            text, btns = render_td_settings(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data.startswith("td_turns:"):
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            g["turns_per_player"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {g['turns_per_player']}")
            text, btns = render_td_settings(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data.startswith("td_time:"):
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            g["timeout_sec"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {g['timeout_sec']} ثانیه")
            text, btns = render_td_settings(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "td_summary":
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer()
            text, btns = render_td_summary(g)
            await safe_edit(event, text, buttons=btns, parse_mode="html"); return

        if data == "td_create":
            g = TD_SETUP_GAMES.get(uid)
            if not g: await event.answer("منقضی", alert=True); return
            await event.answer("✅")
            try:
                await safe_edit(event,
                                f"{E('check', '✅')} <b>بازی ساخته شد!</b>\n{DIV}\n\n"
                                f"{E('info', 'ℹ️')} پیام شرکت توی گروه فرستاده شد.",
                                parse_mode="html", buttons=None)
            except Exception: pass
            g["state"] = "waiting"
            TD_ACTIVE_GAMES[g["group_id"]] = g
            TD_SETUP_GAMES.pop(uid, None)
            await td_broadcast_join(g); return

        if data == "td_cancel":
            TD_SETUP_GAMES.pop(uid, None)
            await event.answer("❌")
            try: await safe_edit(event, f"{E('cross', '❌')} لغو شد",
                                  parse_mode="html", buttons=None)
            except Exception: pass
            return

        if data == "cancel":
            clear_state(uid)
            await event.answer("❌ لغو شد")
            try: await safe_edit(event, f"{E('cross', '❌')} لغو شد",
                                  parse_mode="html", buttons=None)
            except Exception: pass
            return
        if data.startswith("dl:"):
            st = get_state(uid)
            if not st or st.get("state") != "awaiting_deadline":
                await event.answer("⚠️", alert=True); return
            val = data.split(":", 1)[1]
            td = None if val == "none" else parse_duration(val)
            dl = (datetime.now(IRAN_TZ) + td).isoformat() if td else None
            nd = dict(st["data"]); nd["deadline"] = dl
            set_state(uid, "awaiting_group", **nd)
            await event.answer("✅")
            await _ask_group(event, nd); return
        if data.startswith("join:"):
            try: cid = int(data.split(":", 1)[1])
            except ValueError: await event.answer("خطا", alert=True); return
            ch = db.get_challenge(cid)
            if not ch or not ch.get("is_active"):
                await event.answer("چالش یافت نشد", alert=True); return
            if db.has_answered(cid, uid):
                await event.answer("قبلاً شرکت کردی!", alert=True); return
            set_state(uid, "awaiting_answer", challenge_id=cid)
            await event.answer("✅")
            await safe_edit(event,
                            f"{E('check', '✅')} <b>تایید شد!</b>\n\n"
                            f"{E('message', '💬')} <b>جوابت رو بفرست:</b>",
                            parse_mode="html", buttons=None)
            return
        if data.startswith("vote:"):
            try:
                _, c_s, i_s = data.split(":"); cid, idx = int(c_s), int(i_s)
            except Exception: await event.answer("خطا", alert=True); return
            ch = db.get_challenge(cid)
            if not ch or not ch.get("is_active"):
                await event.answer("بسته شده", alert=True); return
            if db.has_voted(cid, uid):
                await event.answer("قبلاً رأی دادی", alert=True); return
            try:
                s = await event.get_sender(); un = user_name(s)
            except Exception: un = str(uid)
            db.save_poll_vote(cid, uid, un, idx)
            db.add_points(uid, un, 5, joined=True)
            await event.answer("✅")
            opts = json.loads(ch["options"]) if ch.get("options") else []
            ch_t = opts[idx] if 0 <= idx < len(opts) else "?"
            try:
                await safe_edit(event,
                                f"{E('check', '✅')} <b>رأی ثبت شد!</b>\n\n"
                                f"{E('vote', '🗳')} {h(ch_t)}\n"
                                f"{E('star', '⭐')} +۵ امتیاز",
                                parse_mode="html", buttons=None)
            except Exception: pass
            return

        if not is_admin(uid):
            await event.answer("⛔", alert=True); return

        if data == "new_text":
            set_state(uid, "awaiting_title", type="text")
            await event.answer()
            await safe_edit(event, f"{E('diamond', '💎')} <b>چالش متنی</b>\n{DIV}\n\nعنوان:",
                            parse_mode="html",
                            buttons=[[Button.inline("❌ لغو", data=b"cancel")]]); return
        if data == "new_poll":
            set_state(uid, "awaiting_title", type="poll")
            await event.answer()
            await safe_edit(event, f"{E('chart', '📊')} <b>نظرسنجی</b>\n{DIV}\n\nعنوان:",
                            parse_mode="html",
                            buttons=[[Button.inline("❌ لغو", data=b"cancel")]]); return
        if data == "templates":
            btns = [[Button.inline(t, data=f"tpl:{i}".encode())] for i, (t, _) in enumerate(TEMPLATES)]
            btns.append([Button.inline("🔙 بازگشت", data=b"menu")])
            await event.answer()
            await safe_edit(event, f"{E('gift', '🎁')} <b>قالب‌ها</b>",
                            parse_mode="html", buttons=btns); return
        if data.startswith("tpl:"):
            try:
                idx = int(data.split(":", 1)[1]); t, q = TEMPLATES[idx]
            except Exception: await event.answer("خطا", alert=True); return
            set_state(uid, "awaiting_deadline", type="text",
                      title=t.replace("💎 ", ""), question=q)
            await event.answer("✅")
            await _ask_deadline(event); return
        if data == "my_challenges":
            chs = db.get_challenges(admin_id=uid)
            if not chs: await event.answer("خالی", alert=True); return
            await event.answer()
            await _render_challenges_page(event, chs, page=0); return
        if data.startswith("chpage:"):
            page = int(data.split(":", 1)[1])
            chs = db.get_challenges(admin_id=uid)
            await event.answer()
            await _render_challenges_page(event, chs, page=page); return
        if data == "my_groups":
            groups = db.get_groups()
            if not groups: await event.answer("خالی", alert=True); return
            await event.answer()
            lines = [f"{E('group', '🏢')} <b>گروه‌ها</b>\n{DIV}\n"]
            for i, g in enumerate(groups[:20], 1):
                lines.append(f"{E('fire', '🔥')} <b>#{i}</b> {h(g.get('title') or '—')}\n"
                             f"{E('id', '🆔')} <code>{g['group_id']}</code>")
            await safe_edit(event, "\n".join(lines),
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]],
                            parse_mode="html"); return
        if data == "menu":
            await event.answer()
            await send_admin_menu(event, edit=True); return
        if data == "top":
            top = db.get_top(10)
            if not top: await event.answer("خالی", alert=True); return
            await event.answer()
            medals = ["🥇", "🥈", "🥉"] + ["🎖"] * 7
            lines = [f"{E('trophy', '🏆')} <b>لیدربورد</b>\n{DIV}\n"]
            for i, u in enumerate(top):
                m = medals[i] if i < len(medals) else "•"
                lines.append(f"{m} <b>{h(u['user_name'] or 'ناشناس')}</b> — <code>{u['points']}</code>")
            await safe_edit(event, "\n".join(lines),
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]],
                            parse_mode="html"); return
        if data == "mylink":
            link = f"https://t.me/{BOT_USERNAME}?start=anon_{uid}"
            n = db.count_anon_received(uid)
            await event.answer()
            await safe_edit(event,
                            f"{E('heart', '💌')} <b>لینک NGL</b>\n{DIV}\n\n"
                            f"<code>{link}</code>\n\n{E('stats', '📊')} <code>{n}</code>",
                            parse_mode="html",
                            buttons=[
                                [Button.url("📤 اشتراک", f"https://t.me/share/url?url={link}")],
                                [Button.inline("📥 صندوق", data=b"anon_inbox")],
                                [Button.inline("🔙 بازگشت", data=b"menu")],
                            ]); return
        if data == "anon_inbox":
            items = db.get_anon_inbox(uid, limit=10)
            if not items: await event.answer("خالی", alert=True); return
            await event.answer()
            lines = [f"{E('heart', '💌')} <b>صندوق ناشناس</b>\n{DIV}\n"]
            for i, m in enumerate(items, 1):
                lines.append(f"\n{E('message', '💬')} <b>#{i}</b>\n"
                             f"<blockquote>{h(m['text'])}</blockquote>\n"
                             f"{E('time', '⏱')} {h((m['sent_at'] or '')[:19])}")
            db.mark_anon_read(uid)
            await safe_edit(event, "\n".join(lines),
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]],
                            parse_mode="html"); return
        if data == "stats":
            al = "، ".join([f"<code>{x}</code>" for x in sorted(ALL_ADMINS)])
            await event.answer()
            await safe_edit(event,
                            f"{E('stats', '📊')} <b>آمار</b>\n{DIV}\n\n"
                            f"{E('group', '🏢')} گروه‌ها: <code>{len(db.get_groups())}</code>\n"
                            f"{E('user', '👤')} کاربران: <code>{db.count_users()}</code>\n"
                            f"{E('diamond', '💎')} چالش‌ها: <code>{len(db.get_challenges())}</code>\n"
                            f"{E('fire', '🔥')} فعال: <code>{db.count_active_challenges()}</code>\n\n"
                            f"{E('crown', '👑')} <b>ادمین‌ها:</b>\n{al}",
                            parse_mode="html",
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]]); return
        if data == "broadcast":
            set_state(uid, "awaiting_broadcast")
            await event.answer()
            await safe_edit(event, f"{E('message', '💬')} پیام رو بفرست:",
                            parse_mode="html",
                            buttons=[[Button.inline("❌ لغو", data=b"cancel")]]); return
        if data.startswith("viewans:"):
            try: cid = int(data.split(":", 1)[1])
            except ValueError: await event.answer("خطا", alert=True); return
            ch = db.get_challenge(cid)
            if not ch: await event.answer("یافت نشد", alert=True); return
            await event.answer()
            await _show_challenge_answers(event, ch); return
        if data.startswith("chgrp:"):
            try: gid_c = int(data.split(":", 1)[1])
            except ValueError: await event.answer("خطا", alert=True); return
            st = get_state(uid)
            if not st or st.get("state") != "awaiting_group":
                await event.answer("⚠️", alert=True); return
            d = st["data"]
            cid = db.create_challenge(uid, gid_c, d.get("title", ""), d.get("question", ""),
                                       ch_type=d.get("type", "text"),
                                       options=d.get("options"),
                                       deadline=d.get("deadline"))
            clear_state(uid)
            link = f"https://t.me/{BOT_USERNAME}?start=ch_{cid}"
            txt = build_challenge_text(cid, d.get("title", ""), d.get("question", ""),
                                        d.get("type", "text"), d.get("options"), d.get("deadline"))
            try:
                sent = await safe_send(gid_c, txt, parse_mode="html",
                                       buttons=[[Button.url("🎯 شرکت می‌کنم", link)]])
                if sent: db.set_challenge_message(cid, sent.id)
                await event.answer("✅")
                await safe_edit(event,
                                f"{E('check', '✅')} <b>ساخته شد!</b>\n\n"
                                f"{E('diamond', '💎')} <b>#{cid}</b> {h(d.get('title', ''))}",
                                parse_mode="html",
                                buttons=[[Button.inline("🔙 منو", data=b"menu")]])
            except Exception as e:
                logger.exception(f"send challenge: {e}")
                await event.answer("خطا", alert=True)
            return
    except Exception as ex:
        logger.exception(f"cb: {ex}")
        try: await event.answer("خطا!", alert=True)
        except Exception: pass


async def _render_challenges_page(event, chs, page=0, per_page=5):
    total = len(chs)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, pages - 1))
    items = chs[page * per_page:page * per_page + per_page]
    lines = [f"{E('list', '📋')} <b>چالش‌های شما</b> <i>({page+1}/{pages})</i>\n{DIV}\n"]
    btns = []
    for ch in items:
        ct = ch.get("ch_type") or "text"
        cnt = db.count_poll_votes(ch["id"]) if ct == "poll" else db.count_answers(ch["id"])
        kd = f"{E('chart', '📊')}" if ct == "poll" else f"{E('diamond', '💎')}"
        st = "🟢" if ch.get("is_active") else "🔴"
        lines.append(f"\n{kd} <b>#{ch['id']}</b> {st} {h(ch['title'])}\n"
                     f"{E('user', '👤')} <code>{cnt}</code>\n"
                     f"{E('time', '⏱')} {h((ch.get('created_at') or '')[:19])}")
        btns.append([Button.inline(f"📊 #{ch['id']} - {ch['title'][:25]}",
                                    data=f"viewans:{ch['id']}".encode())])
    nav = []
    if page > 0: nav.append(Button.inline("⬅️ قبلی", data=f"chpage:{page-1}".encode()))
    if page < pages - 1: nav.append(Button.inline("بعدی ➡️", data=f"chpage:{page+1}".encode()))
    if nav: btns.append(nav)
    btns.append([Button.inline("🔙 بازگشت", data=b"menu")])
    await safe_edit(event, "\n".join(lines), buttons=btns, parse_mode="html")


async def _show_challenge_answers(event, ch):
    cid = ch["id"]; ct = ch.get("ch_type") or "text"
    if ct == "poll":
        opts = json.loads(ch["options"]) if ch.get("options") else []
        res = db.get_poll_results(cid, len(opts))
        total = sum(res.values()) or 1
        lines = [f"{E('chart', '📊')} <b>نتایج نظرسنجی</b>\n{DIV}\n\n"
                 f"{E('diamond', '💎')} {h(ch['title'])}\n"
                 f"{E('user', '👤')} <code>{sum(res.values())}</code>\n"]
        for i, o in enumerate(opts):
            n = res.get(i, 0); pct = int(100 * n / total)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            lines.append(f"\n{E('vote', '🗳')} <b>{h(o)}</b>\n<code>{bar}</code> {pct}% (<code>{n}</code>)")
        await safe_edit(event, "\n".join(lines),
                        buttons=[[Button.inline("🔙 بازگشت", data=b"my_challenges")]],
                        parse_mode="html")
        return
    ans = db.get_answers(cid)
    lines = [f"{E('message', '💬')} <b>پاسخ‌ها</b>\n{DIV}\n\n"
             f"{E('diamond', '💎')} {h(ch['title'])}\n"
             f"{E('user', '👤')} <code>{len(ans)}</code>\n"]
    if not ans:
        lines.append(f"\n{E('info', 'ℹ️')} هنوز کسی شرکت نکرده.")
    else:
        for i, a in enumerate(ans[:15], 1):
            u_l = f'<a href="tg://user?id={a["user_id"]}">{a["user_id"]}</a>'
            un = f'@{a["username"]}' if a.get("username") else "—"
            lines.append(f"\n{E('fire', '🔥')} <b>#{i}</b>\n"
                         f"├ {E('user', '👤')} {h(a.get('user_name') or '—')}\n"
                         f"├ {E('id', '🆔')} {u_l}\n"
                         f"├ {E('link', '🔗')} {h(un)}\n"
                         f"└ <blockquote>{h(a['answer'])}</blockquote>")
    await safe_edit(event, "\n".join(lines),
                    buttons=[[Button.inline("🔙 بازگشت", data=b"my_challenges")]],
                    parse_mode="html")


async def _announce_results(ch):
    cid = ch["id"]; ct = ch.get("ch_type") or "text"; gid = ch["group_id"]
    try:
        if ct == "poll":
            opts = json.loads(ch["options"]) if ch.get("options") else []
            res = db.get_poll_results(cid, len(opts))
            total = sum(res.values()) or 1
            lines = [f"{E('flag', '🏁')} <b>نظرسنجی بسته شد!</b>\n{DIV}\n\n"
                     f"{E('diamond', '💎')} {h(ch['title'])}\n"
                     f"{E('user', '👤')} <code>{sum(res.values())}</code>\n"]
            for i, o in enumerate(opts):
                n = res.get(i, 0); pct = int(100 * n / total)
                bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                lines.append(f"{E('vote', '🗳')} <b>{h(o)}</b>\n<code>{bar}</code> {pct}%")
        else:
            ans = db.get_answers(cid)
            lines = [f"{E('flag', '🏁')} <b>چالش بسته شد!</b>\n{DIV}\n\n"
                     f"{E('diamond', '💎')} {h(ch['title'])}\n"
                     f"{E('user', '👤')} <code>{len(ans)}</code>\n"]
            for i, a in enumerate(ans[:10], 1):
                lines.append(f"\n{E('fire', '🔥')} <b>#{i}</b>\n<blockquote>{h(a['answer'])}</blockquote>")
        await safe_send(gid, "\n".join(lines), parse_mode="html")
    except Exception as e: logger.exception(f"announce: {e}")


async def deadline_watcher():
    await asyncio.sleep(5)
    while True:
        try:
            for ch in db.get_expired_challenges():
                try: await _announce_results(ch)
                except Exception: pass
                db.deactivate_challenge(ch["id"])
                db.mark_results_announced(ch["id"])
        except Exception as e: logger.exception(f"watcher: {e}")
        await asyncio.sleep(60)


async def start_web_server():
    app = web.Application()
    async def health(request):
        return web.Response(text="OK — Unicorn Bot is running ✨")
    async def root(request):
        return web.Response(text=(
            f"🦄 UNICORN ANONY BOT — ROYAL EDITION\n"
            f"Status: Running\nAdmins: {len(ALL_ADMINS)}\nTime: {now_str()}"
        ), content_type="text/plain")
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/healthz", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server on 0.0.0.0:{PORT}")


async def main():
    global BOT_USERNAME
    logger.info("👑 UNICORN ROYAL starting...")
    if not BOT_TOKEN: raise ValueError("❌ BOT_TOKEN لازمه")
    if not OWNER_ID: raise ValueError("❌ OWNER_ID لازمه")
    if not DATABASE_URL: raise ValueError("❌ DATABASE_URL لازمه")
    if not GROQ_API_KEY: raise ValueError("❌ GROQ_API_KEY لازمه")
    logger.info(f"👥 Admins ({len(ALL_ADMINS)}): {sorted(ALL_ADMINS)}")
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    BOT_USERNAME = me.username
    logger.info(f"✅ Bot: @{BOT_USERNAME} (ID: {me.id})")
    try:
        await safe_send(OWNER_ID,
                        f"{E('check', '✅')} <b>ربات روشن شد</b>\n{DIV}\n\n"
                        f"{E('crown', '👑')} <b>UNICORN ROYAL EDITION</b> {E('crown', '👑')}\n\n"
                        f"{E('rocket', '🚀')} @{BOT_USERNAME}\n"
                        f"{E('id', '🆔')} <code>{me.id}</code>\n"
                        f"{E('crown', '👑')} ادمین‌ها: <code>{len(ALL_ADMINS)}</code>\n"
                        f"{E('time', '⏱')} {now_str()}",
                        parse_mode="html")
    except Exception as e: logger.warning(f"notify owner: {e}")
    asyncio.create_task(deadline_watcher())
    logger.info("✅ Ready!")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("⛔ Stopped")
    except Exception as ex: logger.exception(f"❌ {ex}")