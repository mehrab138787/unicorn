# -*- coding: utf-8 -*-
"""
🦄 UNICORN PET GAME — Royal Edition v13
💔 Divorce · 🥚 6h Hatch · 🐣 Babies · 💰 Passive income
⚔️ Strategic Battle (Light) · 🔫 Weapon Tiers · 👑 Iranian Heroes
🎁 UNICORN Code · 🛡️ Default Soldier · 🎉 Update Reward
✏️ Rename babies · 🎀 Baby answers when called!
🎀 NEW: Baby answers family questions (mom/dad/siblings) — only IDs, never names!
"""

import re, random, asyncio, logging, time, json
import requests
from telethon import events, Button
from telethon.errors import MessageNotModifiedError

logger = logging.getLogger("UnicornGame")

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
NEIGH_COOLDOWN_SEC = 300
FEED_COST = 500
FEED_HUNGER_BOOST = 25
HUNGER_DECAY_SEC = 300
PENDING_CAP_HOURS = 8
TICK_INTERVAL = 20
NEIGH_REWARD_MIN = 1
NEIGH_REWARD_MAX = 1000

EGG_HATCH_SEC = 6 * 3600
EGG_COST = 5000
BABY_GROW_COST_BASE = 10000
BABY_MAX_LEVEL = 5
BABY_INCOME_PER_LEVEL_PER_DAY = 500

# ✏️ Rename config
BABY_NAME_MIN_LEN = 1
BABY_NAME_MAX_LEN = 30
BABY_RENAME_COST = 0

# 🎀 NEW: Baby call feature
BABY_CALL_ENABLED = True
BABY_CALL_COOLDOWN_SEC = 90   # per baby, per chat
BABY_CALL_MIN_LEN = 1          # minimum length of word to consider
BABY_CALL_MAX_MSG_LEN = 400    # ignore long messages
BABY_CALL_AI_MODELS = [
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
]
# fallback responses (if AI fails)
BABY_FALLBACK_RESPONSES = [
    "دلام مامانی 🥺💕",
    "جانم مامان؟ 🍼✨",
    "چیه مامانی؟ 🦄💖",
    "بیا بغلم مامان 🥺💗",
    "مامان صدام زدی؟ 🌸✨",
    "جووونم 🍼💕",
    "بله مامان؟ 🦄✨",
    "چشم مامان 🥺💖",
    "هاااای مامان 🌸💫",
    "چیه؟ بخورمت مامان 🍼😘",
    "بله؟ اینجام مامانی 🦄💕",
    "جانم؟ دل من لرزید 🥺✨",
]

# 🎀 NEW: Family question fallbacks
BABY_FAMILY_ONLY_CHILD = [
    "من تنهام مامانی 🥺💕",
    "من فقط خودمم 🥺✨ خواهر برادر ندارم",
    "تنها تنهام مامانی 💔🌸",
    "خواهر و برادر ندارم، فقط شمام 🥺💖",
    "من تک‌فرزندم مامانی 🍼✨",
    "فقط منم مامانی، کسی رو ندارم 🥺💗",
]
BABY_FAMILY_HAS_SIBLINGS = [
    "ما {n} تاییم 🍼✨",
    "یه عالمه خواهر برادر دارم 🦄💖",
    "{n} تا همشیر دارم مامانی 🌸💫",
    "من {sib} تا خواهر و برادر دارم 🥺💕",
]
BABY_FAMILY_UNKNOWN = [
    "نمی‌دونم مامانی 🥺✨",
    "هیچ‌کس رو ندارم 💔🥺",
]

COMBO_WINDOW_SEC = 30
COMBO_BONUS_MULT = 2.0

LEVEL_THRESHOLDS = [0, 15, 30, 45, 60, 80, 100, 125, 155, 200]
LEVEL_POINT_COST = [0, 1000, 3000, 6000, 10000, 15000, 25000, 40000, 60000, 100000]
LEVEL_RATES      = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

LEVEL_NAMES = [
    "🍼 بـچه‌یـونـیـکـورن", "🐴 یـونـیـکـورن کـوچـولـو",
    "🦄 یـونـیـکـورن جـوان", "✨ یـونـیـکـورن درخـشـان",
    "💫 یـونـیـکـورن سـتـاره‌ای", "🌟 یـونـیـکـورن طـلایـی",
    "💎 یـونـیـکـورن الـمـاسـی", "👑 یـونـیـکـورن سـلـطـنـتـی",
    "🔥 یـونـیـکـورن افـسـانـه‌ای", "🌌 یـونـیـکـورن کـائـنـاتـی",
]
LEVEL_UNLOCKS = [
    "🦄 نیـه زدن پـایـه", "⚡ تـولیـد ۲ بـرابـر",
    "💸 انتـقـال یـونـیـکـورن", "🎁 نیـه‌ی پـاداشـی +",
    "🌟 بـرداشـت سـریـع‌تـر", "🍰 غـذاهـای ویـژه",
    "🔥 تـولیـد x1.5", "💎 پـاداش دو بـرابـر",
    "🛡 ضـد قـهـر ۳۰٪", "👑 نـشـان افـسـانـه‌ای",
]

DAILY_BASE_REWARD = 2000
DAILY_STREAK_BONUS = 500
DAILY_MAX_STREAK = 30
DAILY_COOLDOWN_SEC = 86400

SPIN_COOLDOWN_SEC = 86400
SPIN_REWARDS = [
    ("💎", "پوینت کمی", "points", 800, 32),
    ("💎", "پوینت متوسط", "points", 3000, 25),
    ("💰", "پوینت خوب", "points", 9000, 15),
    ("🌟", "پوینت عالی", "points", 25000, 6),
    ("⚡", "بونوس 2x (1h)", "boost2_3600", 0, 10),
    ("⚡", "بونوس 3x (30m)", "boost3_1800", 0, 5),
    ("🍰", "سیری کامل", "hunger", 100, 5),
    ("🥚", "تخم یونیکورن", "egg", 1, 1),
    ("👑", "جکپات بزرگ!!", "points", 150000, 1),
]

NEIGH_EVENTS = [
    ("bonus_pts", 500,  25, "🎁 یه کیسه‌ی طلا پیدا کردی!"),
    ("bonus_pts", 1500, 12, "💎 یه الماس درخشان!"),
    ("bonus_pts", 3000, 3,  "👑 گنج پنهان!"),
    ("hunger",    30,   20, "🍰 یه شیرینی خوشمزه خوردی!"),
    ("boost",     1800, 8,  "⚡ انرژی مضاعف! بونوس x2 (30 دقیقه)"),
    ("bomb",      -200, 5,  "💣 اوه نه! یه چاله افتادی!"),
    ("nothing",   0,    27, None),
]

SKINS = {
    "classic": ("🌸", "کلاسیک", 0),
    "blue": ("💙", "آبی", 5_000),
    "purple": ("💜", "بنفش", 15_000),
    "gold": ("💛", "طلایی", 50_000),
    "rose": ("🌹", "گلی", 120_000),
    "rainbow": ("🌈", "رنگین‌کمان", 350_000),
    "galaxy": ("🌌", "کهکشانی", 900_000),
    "royal": ("👑", "سلطنتی", 2_500_000),
}

BABY_NAMES = [
    "🌈 استار", "✨ لونا", "💫 نوا", "🌸 پیچ", "🦄 دریم",
    "⭐ گالاکس", "🌟 سلست", "💎 کریستال", "🔥 فینیکس", "🌙 سلن",
    "☀️ سول", "🎀 تافی", "🍭 شوگر", "🧁 کاپ‌کیک", "🌺 بلاسم",
    "🍀 لاکی", "💖 هارت", "🎵 ملی", "🌊 آبی", "🍯 هانی",
]

BABY_NAME_PRESETS = [
    "🌈 استار", "✨ لونا", "💫 نوا", "🌸 پیچ", "🦄 دریم",
    "⭐ گالاکس", "🌟 سلست", "💎 کریستال", "🔥 فینیکس", "🌙 سلن",
]

ACHIEVEMENTS = {
    "first_neigh": ("🎉", "اولین نیه", "برای اولین بار نیه زدی"),
    "neigh_50": ("👋", "۵۰ نیه", "۵۰ بار نیه زدی"),
    "neigh_200": ("🌟", "۲۰۰ نیه", "۲۰۰ بار نیه زدی"),
    "neigh_500": ("💫", "۵۰۰ نیه", "۵۰۰ بار نیه زدی"),
    "level_5": ("⚡", "لول ۵", "به لول ۵ رسیدی"),
    "level_10": ("👑", "لول ۱۰", "به بالاترین لول رسیدی"),
    "millionaire": ("💎", "میلیونر", "۱ میلیون پوینت جمع کردی"),
    "billionaire": ("💰", "میلیاردر", "۱ میلیارد پوینت جمع کردی"),
    "first_battle": ("🥊", "اولین نبرد", "اولین دوئل رو انجام دادی"),
    "warrior": ("⚔️", "جنگجو", "۱۰ بار بردی"),
    "married": ("💍", "متأهل", "ازدواج کردی"),
    "daily_7": ("🎁", "۷ روز پیوسته", "۷ روز پاداش گرفتی"),
    "daily_30": ("🏅", "۳۰ روز پیوسته", "۳۰ روز پیاپی"),
    "breeder": ("👶", "پدر/مادر", "اولین تخم رو ساختی"),
    "first_baby": ("🐣", "اولین بیبی", "اولین تخم هچ شد"),
    "baby_master": ("🏠", "خانواده", "۵ تا بیبی داری"),
}

BATTLE_ANIM = ["💥", "⚡", "🔥", "💫", "⚔️", "🗡️", "🏹", "☄️"]
BATTLE_WORDS = [
    "💥 بـوم! ضربه‌ی کاری!",
    "⚡ چـقـدر سـریـع!",
    "🔥 حـمـلـه‌ی آتـشـی!",
    "💫 چـرخـش مـهـیـب!",
    "⚔️ شـمـشـیـر نـور!",
    "🗡️ ضـربـه‌ی نـهـایـی!",
]

# ═══════════════════════════════════════════════════════════
# ⚔️ STRATEGIC BATTLE SYSTEM
# ═══════════════════════════════════════════════════════════
BATTLE_REWARD_MIN = 50_000
BATTLE_REWARD_MAX = 100_000
SOLDIER_COST_BASE = 100_000
SOLDIER_BASE_POWER = 10
BATTLE_VARIANCE = 0.05

DEFAULT_SOLDIER_COUNT = 1
UNICORN_CODE_REWARD = 150_000

UPDATE_VERSION = "v13_2025-11-08"
REWARD_USER_ID = 6691915596
REWARD_AMOUNT = 2_000_000

WEAPON_TIERS = {
    0: ("🪨", "سنگ و چوب"), 1: ("⚒️", "مفرغ"),
    2: ("🗡️", "آهن"), 3: ("⚔️", "فولاد"),
    4: ("💥", "باروت"), 5: ("🔫", "مدرن"),
    6: ("⚡", "پیشرفته"), 7: ("🌟", "آینده"),
    8: ("🌌", "فرا نوین"),
}

WEAPONS = {
    "club_stone":    ("چماق سنگی",       "🪨", 0, 10,        50_000),
    "spear_wood":    ("نیزه چوبی",       "🪵", 0, 25,        150_000),
    "axe_stone":     ("تبر سنگی",        "🪓", 0, 40,        400_000),
    "bow_wood":      ("کمان چوبی",       "🏹", 0, 60,        1_000_000),
    "sword_bronze":  ("شمشیر مفرغی",     "⚒️", 1, 120,       2_500_000),
    "shield_bronze": ("سپر مفرغی",       "🛡️", 1, 180,       5_000_000),
    "spear_bronze":  ("نیزه مفرغی",      "🔱", 1, 250,       10_000_000),
    "sword_iron":    ("شمشیر آهنی",      "🗡️", 2, 400,       25_000_000),
    "axe_iron":      ("تبر جنگی",        "🪓", 2, 600,       50_000_000),
    "bow_iron":      ("کمان آهنی",       "🏹", 2, 850,       100_000_000),
    "sword_steel":   ("شمشیر فولادی",    "⚔️", 3, 1_300,     250_000_000),
    "shield_steel":  ("سپر فولادی",      "🛡️", 3, 1_800,     500_000_000),
    "crossbow":      ("تیرکمان فولادی",  "🎯", 3, 2_500,     1_000_000_000),
    "musket":        ("تفنگ سرپر",       "💥", 4, 4_000,     2_500_000_000),
    "cannon":        ("توپ جنگی",        "💣", 4, 6_000,     5_000_000_000),
    "grenade":       ("نارنجک",          "🧨", 4, 9_000,     10_000_000_000),
    "rifle":         ("تفنگ جنگی",       "🔫", 5, 15_000,    25_000_000_000),
    "sniper":        ("اسنایپر",         "🎯", 5, 25_000,    50_000_000_000),
    "machinegun":    ("مسلسل سنگین",     "🔫", 5, 40_000,    100_000_000_000),
    "laser":         ("لیزر پلاسما",     "⚡", 6, 75_000,    250_000_000_000),
    "railgun":       ("ریلگان",          "🌟", 6, 120_000,   500_000_000_000),
    "drone":         ("پهپاد رزمی",      "🛸", 6, 200_000,   1_000_000_000_000),
    "plasma":        ("تفنگ پلاسما",     "💫", 7, 400_000,   2_500_000_000_000),
    "antimatter":    ("توپ ضد ماده",     "🌌", 7, 700_000,   5_000_000_000_000),
    "quantum":       ("سلاح کوانتومی",   "🌀", 7, 1_200_000, 10_000_000_000_000),
    "blackhole":     ("توپ سیاه‌چاله",   "🕳️", 8, 3_000_000, 25_000_000_000_000),
    "nova":          ("نواختر",          "💥", 8, 5_000_000, 50_000_000_000_000),
    "godslayer":     ("خداشکن",          "👁️", 8, 10_000_000,100_000_000_000_000),
}

HEROES = {
    "arash":       ("آرش کمانگیر",   "🏹", 5_000,    50_000_000),
    "kaveh":       ("کاوه آهنگر",    "⚒️", 8_000,    100_000_000),
    "babak":       ("بابک خرمدین",   "🔥", 12_000,   200_000_000),
    "ariobarzan":  ("آریوبرزن",      "🦅", 18_000,   400_000_000),
    "yaqub":       ("یعقوب لیث",     "⚔️", 25_000,   800_000_000),
    "cyrus":       ("کوروش بزرگ",    "👑", 40_000,   2_000_000_000),
    "darius":      ("داریوش بزرگ",   "🏛️", 55_000,   4_000_000_000),
    "esfandiar":   ("اسفندیار",      "🛡️", 75_000,   8_000_000_000),
    "sohrab":      ("سهراب",         "🦁", 100_000,  15_000_000_000),
    "siavash":     ("سیاوش",         "🕊️", 130_000,  25_000_000_000),
    "zal":         ("زال زر",        "🦅", 170_000,  40_000_000_000),
    "goudarz":     ("گودرز",         "🗡️", 200_000,  60_000_000_000),
    "bahram":      ("بهرام گور",     "🐗", 260_000,  90_000_000_000),
    "nader":       ("نادر شاه",      "👑", 350_000,  150_000_000_000),
    "rostam":      ("رستم دستان",    "🦸", 500_000,  250_000_000_000),
}

DIV = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
DIV2 = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"

PREM = {
    "sparkle": "5404654051945521778", "heart": "5443038326535759644",
    "star": "6337048821603763745", "crown": "5458603043203327669",
    "gem": "5404654051945521778", "fire": "5424972470023104089",
    "rocket": "5424972470023104089", "trophy": "5458603043203327669",
    "check": "5206607081334906820", "cross": "5210952531676504517",
    "party": "5456359790390093750", "wave": "5368324170671202286",
    "gift": "5456359790390093750", "warning": "5447644880824181073",
    "info": "5323442290708985472", "user": "5443038326535759644",
    "id": "5397782960512444700", "flag": "5447644880824181073",
    "target": "5424972470023104089", "bolt": "5424972470023104089",
    "alert": "5447644880824181073", "hourglass": "5458603043203327669",
    "message": "5443038326535759644", "diamond": "5404654051945521778",
    "chart": "5231200819986047254", "eye": "5397782960512444700",
    "brain": "5323442290708985472",
}

_TG_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="\d+">([^<]*)</tg-emoji>')

# regex for emoji chars (for stripping from baby name matching)
_EMOJI_STRIP_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # emoji
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F2FF"
    "\u2600-\u27bf"
    "\u2190-\u21ff"
    "\u2300-\u23ff"
    "\u2b00-\u2bff"
    "\u200d\u2640\u2642\ufe0f"
    "]+",
    flags=re.UNICODE,
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def PE(k, fb):
    eid = PREM.get(k)
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>' if eid else fb


def strip_premium(text):
    return _TG_EMOJI_RE.sub(r"\1", text)


def _emoji_err(ex):
    s = str(ex).lower()
    return ("document" in s) or ("invalid" in s and "inline" in s) or \
           ("custom emoji" in s) or ("emoji" in s and "invalid" in s)


def normalize_fa(text):
    if not text: return text
    return (text
        .replace("ي", "ی").replace("ك", "ک").replace("ة", "ه").replace("ۀ", "ه")
        .replace("ؤ", "و").replace("إ", "ا").replace("أ", "ا")
        .replace("\u200c", "").replace("\u200f", "").replace("\u200e", "")
        .replace("\u064b", "").replace("\u064c", "").replace("\u064d", "")
        .replace("\u064e", "").replace("\u064f", "").replace("\u0650", "")
        .replace("\u0651", "").replace("\u0652", "").replace("\u0670", ""))


def fmt_num(n):
    try: n = int(n)
    except Exception: return "0"
    if n >= 1_000_000_000_000: return f"{n/1_000_000_000_000:.1f}T"
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)


def fmt_full(n):
    try: return f"{int(n):,}"
    except Exception: return "0"


def parse_amount(s):
    if not s: return None
    s = s.strip().lower().replace(",", "").replace("،", "").replace(" ", "")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([kmb])?$", s)
    if not m: return None
    n = float(m.group(1)); u = m.group(2)
    if u == "k": n *= 1_000
    elif u == "m": n *= 1_000_000
    elif u == "b": n *= 1_000_000_000
    return int(n)


def now_ts(): return int(time.time())


def user_name(u):
    if not u: return "ناشناس"
    n = (getattr(u, "first_name", "") or "").strip()
    l = (getattr(u, "last_name", "") or "").strip()
    full = (n + " " + l).strip()
    return full or getattr(u, "username", None) or str(getattr(u, "id", "?"))


def h(t):
    if t is None: return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hunger_face(hunger, angry):
    if angry or hunger <= 0: return "😭"
    if hunger < 20: return "😫"
    if hunger < 50: return "😕"
    if hunger < 80: return "🙂"
    return "😍"


def hunger_bar(hv):
    hv = max(0, min(100, int(hv)))
    return "🍰" * (hv // 10) + "🖤" * (10 - hv // 10)


def progress_bar(cur, total, width=8):
    if total <= 0: return "▰" * width
    p = max(0, min(100, int(100 * cur / total)))
    filled = int(p / 100 * width)
    return "▰" * filled + "▱" * (width - filled)


def fmt_time(sec):
    sec = max(0, int(sec))
    if sec < 60: return f"{sec}s"
    m, s = divmod(sec, 60)
    if m < 60: return f"{m}:{s:02d}"
    hr, m = divmod(m, 60)
    return f"{hr}:{m:02d}:{s:02d}"


def roll_neigh_event():
    total = sum(e[2] for e in NEIGH_EVENTS)
    pick = random.randint(1, total)
    acc = 0
    for kind, val, w, msg in NEIGH_EVENTS:
        acc += w
        if pick <= acc:
            if kind == "nothing": return None
            return kind, val, msg
    return None


def _clean_baby_name(raw):
    """Sanitize a new baby name from user input."""
    if not raw:
        return None
    n = raw.strip()
    if not n:
        return None
    n = n.replace("\n", " ").replace("\r", " ").strip()
    n = re.sub(r"\s+", " ", n)
    if len(n) < BABY_NAME_MIN_LEN or len(n) > BABY_NAME_MAX_LEN:
        return None
    return n


def _strip_emoji(s):
    """Remove emojis from a string (for name matching)."""
    if not s:
        return ""
    s = _EMOJI_STRIP_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ═══════════════════════════════════════════════════════════
# GAME
# ═══════════════════════════════════════════════════════════
class UnicornGame:
    def __init__(self, client, db, groq_key="", ai_models=None):
        self.client = client
        self.db = db
        self.conn = db.conn
        self._running = False
        self._combo = {}
        self._last_breed_cache = {}
        self._pending_renames = {}
        # 🎀 NEW: baby call cooldown & AI
        self._baby_call_cd = {}       # {(baby_id, chat_id): ts}
        # 🎀 NEW: map sent messages -> baby_id so we can reply to family questions
        self._baby_reply_msgs = {}    # {(chat_id, msg_id): baby_id}
        self.groq_key = (groq_key or "").strip()
        self.ai_models = ai_models or BABY_CALL_AI_MODELS

    def _c(self):
        import psycopg2, psycopg2.extras
        try:
            if self.conn is None or self.conn.closed:
                raise psycopg2.InterfaceError("closed")
            return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        except (psycopg2.InterfaceError, psycopg2.OperationalError, AttributeError) as e:
            logger.warning(f"🔄 DB reconnect — {e}")
            try:
                self.db.reconnect()
                self.conn = self.db.conn
            except Exception as e2:
                logger.error(f"❌ reconnect fail: {e2}")
                raise
            return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _ensure_alive(self):
        try:
            c = self._c(); c.execute("SELECT 1"); c.fetchone()
            return True
        except Exception:
            try:
                self.db.reconnect(); self.conn = self.db.conn; return True
            except Exception as e:
                logger.error(f"❌ health: {e}"); return False

    async def _safe_send(self, chat_id, text, **kw):
        try: return await self.client.send_message(chat_id, text, **kw)
        except MessageNotModifiedError: return None
        except Exception as ex:
            if _emoji_err(ex):
                try: return await self.client.send_message(chat_id, strip_premium(text), **kw)
                except Exception as ex2:
                    logger.error(f"🦄 fallback: {ex2}"); return None
            raise

    async def _safe_edit_msg(self, chat_id, msg_id, text, buttons=None, **kw):
        try:
            await self.client.edit_message(chat_id, msg_id, text=text,
                                            buttons=buttons, parse_mode="html")
            return True
        except MessageNotModifiedError: return True
        except Exception as ex:
            if _emoji_err(ex):
                try:
                    await self.client.edit_message(chat_id, msg_id,
                                                    text=strip_premium(text),
                                                    buttons=buttons, parse_mode="html")
                    return True
                except MessageNotModifiedError: return True
                except Exception: return False
            return False

    async def _safe_answer(self, event, text=None, alert=False):
        try: await event.answer(text, alert=alert)
        except Exception: pass

    # ═══════════ SETUP ═══════════
    def setup(self):
        c = self._c()
        c.execute("""CREATE TABLE IF NOT EXISTS unicorns (
            user_id BIGINT PRIMARY KEY, name TEXT,
            level INTEGER DEFAULT 1, neigh_count INTEGER DEFAULT 0,
            points BIGINT DEFAULT 0, pending REAL DEFAULT 0,
            hunger INTEGER DEFAULT 100, angry INTEGER DEFAULT 0,
            last_neigh BIGINT DEFAULT 0, last_feed BIGINT DEFAULT 0,
            last_produce BIGINT DEFAULT 0, last_hunger_tick BIGINT DEFAULT 0,
            created_at BIGINT DEFAULT 0, total_earned BIGINT DEFAULT 0,
            total_fed INTEGER DEFAULT 0, color TEXT DEFAULT 'classic',
            daily_streak INTEGER DEFAULT 0, daily_best INTEGER DEFAULT 0,
            last_daily BIGINT DEFAULT 0, last_spin BIGINT DEFAULT 0,
            spin_count INTEGER DEFAULT 0, battles_won INTEGER DEFAULT 0,
            battles_lost INTEGER DEFAULT 0, married_to BIGINT DEFAULT 0,
            married_at BIGINT DEFAULT 0, eggs INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]', boost_mult REAL DEFAULT 1.0,
            boost_until BIGINT DEFAULT 0, last_profile_msg BIGINT DEFAULT 0,
            last_profile_chat BIGINT DEFAULT 0, total_neigh_ever INTEGER DEFAULT 0,
            unicorn_code_used BIGINT DEFAULT 0
        )""")
        try:
            c.execute("ALTER TABLE unicorns ADD COLUMN IF NOT EXISTS unicorn_code_used BIGINT DEFAULT 0")
        except Exception as e:
            logger.warning(f"alter unicorns: {e}")
        c.execute("""CREATE TABLE IF NOT EXISTS unicorn_transfers (
            id BIGSERIAL PRIMARY KEY, from_id BIGINT, to_id BIGINT,
            amount BIGINT, at BIGINT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS unicorn_battles (
            id BIGSERIAL PRIMARY KEY, winner_id BIGINT, loser_id BIGINT,
            amount BIGINT, at BIGINT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS unicorn_eggs (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            partner_id BIGINT NOT NULL,
            laid_at BIGINT NOT NULL,
            hatched_at BIGINT,
            baby_id BIGINT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS unicorn_babies (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            partner_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            born_at BIGINT NOT NULL,
            last_income BIGINT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS uni_weapons (
            user_id BIGINT NOT NULL,
            weapon_key TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, weapon_key)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS uni_heroes (
            user_id BIGINT NOT NULL,
            hero_key TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, hero_key)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS uni_army (
            user_id BIGINT PRIMARY KEY,
            soldier_count INTEGER DEFAULT 1,
            active_weapon TEXT DEFAULT 'club_stone',
            updated_at BIGINT DEFAULT 0
        )""")
        try:
            c.execute("UPDATE uni_army SET soldier_count = 1 WHERE soldier_count IS NULL OR soldier_count < 1")
            c.execute("ALTER TABLE uni_army ALTER COLUMN soldier_count SET DEFAULT 1")
        except Exception as e:
            logger.warning(f"army default: {e}")
        c.execute("""CREATE TABLE IF NOT EXISTS bot_meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at BIGINT DEFAULT 0
        )""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_uni_points ON unicorns(points DESC)""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_eggs_lookup ON unicorn_eggs(user_id, partner_id, hatched_at)""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_babies_lookup ON unicorn_babies(user_id, partner_id)""")
        logger.info("🦄 Unicorn tables ready (v13 — baby call + family reply)")
        try:
            self._check_update_reward()
        except Exception as e:
            logger.exception(f"reward check: {e}")

    def _check_update_reward(self):
        try:
            c = self._c()
            c.execute("SELECT value FROM bot_meta WHERE key='unicorn_version'")
            row = c.fetchone()
            old_version = row["value"] if row else None
            if old_version == UPDATE_VERSION:
                logger.info(f"🦄 version {UPDATE_VERSION} already applied")
                return
            logger.info(f"🎉 New update detected: {old_version} → {UPDATE_VERSION}")

            u = self.get_unicorn(REWARD_USER_ID)
            if not u:
                self.get_or_create(REWARD_USER_ID, "Owner")
                u = self.get_unicorn(REWARD_USER_ID)
            if u:
                new_pts = (u.get("points") or 0) + REWARD_AMOUNT
                new_total = (u.get("total_earned") or 0) + REWARD_AMOUNT
                self.update(REWARD_USER_ID, points=new_pts, total_earned=new_total)
                logger.info(f"🎁 Gave {REWARD_AMOUNT:,} points to {REWARD_USER_ID}")

            c.execute("""INSERT INTO bot_meta (key, value, updated_at)
                         VALUES ('unicorn_version', %s, %s)
                         ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at""",
                      (UPDATE_VERSION, now_ts()))
        except Exception as e:
            logger.exception(f"_check_update_reward: {e}")

    def register_handlers(self):
        self.client.add_event_handler(self.on_message, events.NewMessage())
        self.client.add_event_handler(self.on_callback, events.CallbackQuery())
        self._running = True

    def start_ticker(self):
        asyncio.create_task(self._ticker())

    # ═══════════ DB ═══════════
    def get_unicorn(self, uid):
        c = self._c()
        c.execute("SELECT * FROM unicorns WHERE user_id=%s", (uid,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_or_create(self, uid, name):
        u = self.get_unicorn(uid)
        if u: return u
        ts = now_ts()
        c = self._c()
        c.execute("""INSERT INTO unicorns
            (user_id, name, created_at, last_neigh, last_feed,
             last_produce, last_hunger_tick, achievements)
            VALUES (%s, %s, %s, 0, %s, %s, %s, '[]')
            ON CONFLICT (user_id) DO NOTHING""",
            (uid, name, ts, ts, ts, ts))
        return self.get_unicorn(uid)

    def update(self, uid, **fields):
        if not fields: return
        keys = list(fields.keys()); vals = [fields[k] for k in keys]
        sets = ", ".join([f"{k}=%s" for k in keys]); vals.append(uid)
        c = self._c()
        c.execute(f"UPDATE unicorns SET {sets} WHERE user_id=%s", vals)

    def add_achievement(self, uid, key):
        u = self.get_unicorn(uid)
        if not u: return False
        try: ach = json.loads(u.get("achievements") or "[]")
        except Exception: ach = []
        if key in ach: return False
        ach.append(key)
        self.update(uid, achievements=json.dumps(ach))
        return True

    def check_achievements(self, uid):
        u = self.get_unicorn(uid)
        if not u: return []
        new_ones = []
        def try_unlock(key, cond):
            if cond and self.add_achievement(uid, key):
                new_ones.append(key)
        nc = u.get("neigh_count") or 0
        lvl = u.get("level") or 1
        tot = u.get("total_earned") or 0
        bw = u.get("battles_won") or 0
        btotal = (u.get("battles_won") or 0) + (u.get("battles_lost") or 0)
        try_unlock("first_neigh", nc >= 1)
        try_unlock("neigh_50", nc >= 50)
        try_unlock("neigh_200", nc >= 200)
        try_unlock("neigh_500", nc >= 500)
        try_unlock("level_5", lvl >= 5)
        try_unlock("level_10", lvl >= 10)
        try_unlock("millionaire", tot >= 1_000_000)
        try_unlock("billionaire", tot >= 1_000_000_000)
        try_unlock("first_battle", btotal >= 1)
        try_unlock("warrior", bw >= 10)
        try_unlock("married", (u.get("married_to") or 0) > 0)
        try_unlock("daily_7", (u.get("daily_streak") or 0) >= 7)
        try_unlock("daily_30", (u.get("daily_streak") or 0) >= 30)
        return new_ones

    # ═══════════ STRATEGIC BATTLE HELPERS ═══════════
    def get_army(self, uid):
        c = self._c()
        c.execute("SELECT * FROM uni_army WHERE user_id=%s", (uid,))
        r = c.fetchone()
        if r:
            army = dict(r)
            if (army.get("soldier_count") or 0) < DEFAULT_SOLDIER_COUNT:
                c.execute("UPDATE uni_army SET soldier_count=%s WHERE user_id=%s",
                          (DEFAULT_SOLDIER_COUNT, uid))
                army["soldier_count"] = DEFAULT_SOLDIER_COUNT
            return army
        c.execute("""INSERT INTO uni_army (user_id, soldier_count, active_weapon, updated_at)
                     VALUES (%s, %s, 'club_stone', %s) ON CONFLICT (user_id) DO NOTHING""",
                  (uid, DEFAULT_SOLDIER_COUNT, now_ts()))
        c.execute("SELECT * FROM uni_army WHERE user_id=%s", (uid,))
        return dict(c.fetchone())

    def get_weapons(self, uid):
        c = self._c()
        c.execute("SELECT * FROM uni_weapons WHERE user_id=%s", (uid,))
        return {r["weapon_key"]: dict(r) for r in c.fetchall()}

    def get_heroes(self, uid):
        c = self._c()
        c.execute("SELECT * FROM uni_heroes WHERE user_id=%s", (uid,))
        return {r["hero_key"]: dict(r) for r in c.fetchall()}

    def has_weapon(self, uid, key):
        c = self._c()
        c.execute("SELECT 1 FROM uni_weapons WHERE user_id=%s AND weapon_key=%s",
                  (uid, key))
        return c.fetchone() is not None

    def has_hero(self, uid, key):
        c = self._c()
        c.execute("SELECT 1 FROM uni_heroes WHERE user_id=%s AND hero_key=%s",
                  (uid, key))
        return c.fetchone() is not None

    def buy_weapon(self, uid, key):
        if key not in WEAPONS: return False, "نامعتبر"
        if self.has_weapon(uid, key): return False, "قبلاً داری"
        w = WEAPONS[key]
        u = self.get_unicorn(uid)
        if (u.get("points") or 0) < w[4]: return False, "پوینت کافی نداری"
        self.update(uid, points=(u.get("points") or 0) - w[4])
        c = self._c()
        c.execute("INSERT INTO uni_weapons (user_id, weapon_key, count) VALUES (%s,%s,1)",
                  (uid, key))
        return True, "خرید موفق"

    def equip_weapon(self, uid, key):
        if key not in WEAPONS: return False
        if not self.has_weapon(uid, key): return False
        self.get_army(uid)
        c = self._c()
        c.execute("UPDATE uni_army SET active_weapon=%s, updated_at=%s WHERE user_id=%s",
                  (key, now_ts(), uid))
        return True

    def buy_hero(self, uid, key):
        if key not in HEROES: return False, "نامعتبر"
        if self.has_hero(uid, key): return False, "قبلاً داری"
        hd = HEROES[key]
        u = self.get_unicorn(uid)
        if (u.get("points") or 0) < hd[3]: return False, "پوینت کافی نداری"
        self.update(uid, points=(u.get("points") or 0) - hd[3])
        c = self._c()
        c.execute("INSERT INTO uni_heroes (user_id, hero_key, count) VALUES (%s,%s,1)",
                  (uid, key))
        return True, "خرید موفق"

    def train_soldiers(self, uid, count):
        if count < 1 or count > 100: return False, "تعداد نامعتبر (1-100)"
        cost = SOLDIER_COST_BASE * count
        u = self.get_unicorn(uid)
        if (u.get("points") or 0) < cost: return False, f"{fmt_num(cost)} پوینت لازمه"
        self.update(uid, points=(u.get("points") or 0) - cost)
        self.get_army(uid)
        c = self._c()
        c.execute("UPDATE uni_army SET soldier_count=soldier_count+%s, updated_at=%s WHERE user_id=%s",
                  (count, now_ts(), uid))
        return True, f"{count} سرباز آموزش دید"

    def compute_power(self, uid):
        army = self.get_army(uid)
        weapons = self.get_weapons(uid)
        heroes = self.get_heroes(uid)

        active_key = army.get("active_weapon") or "club_stone"
        if active_key not in weapons:
            if "club_stone" in WEAPONS:
                active_key = "club_stone"
        w = WEAPONS.get(active_key)
        w_power = w[3] if w else 0

        soldier_count = army.get("soldier_count") or 0
        soldier_power = soldier_count * (w_power + SOLDIER_BASE_POWER)

        hero_power = 0
        for hk in heroes:
            if hk in HEROES:
                hero_power += HEROES[hk][2]

        total = soldier_power + hero_power
        return {
            "soldier_power": soldier_power,
            "hero_power": hero_power,
            "total": total,
            "weapon_key": active_key,
            "weapon_power": w_power,
            "soldier_count": soldier_count,
            "heroes_count": len(heroes),
        }

    # ═══════════ EGGS & BABIES ═══════════
    def get_eggs(self, uid):
        u = self.get_unicorn(uid)
        if not u: return []
        partner = u.get("married_to") or 0
        c = self._c()
        if partner:
            c.execute("""SELECT * FROM unicorn_eggs
                WHERE ((user_id=%s AND partner_id=%s)
                    OR (user_id=%s AND partner_id=%s))
                AND hatched_at IS NULL
                ORDER BY laid_at DESC""",
                (uid, partner, partner, uid))
        else:
            c.execute("""SELECT * FROM unicorn_eggs
                WHERE user_id=%s AND hatched_at IS NULL
                ORDER BY laid_at DESC""", (uid,))
        return [dict(r) for r in c.fetchall()]

    def count_eggs(self, uid):
        return len(self.get_eggs(uid))

    def get_babies(self, uid):
        u = self.get_unicorn(uid)
        if not u: return []
        partner = u.get("married_to") or 0
        c = self._c()
        if partner:
            c.execute("""SELECT * FROM unicorn_babies
                WHERE (user_id=%s AND partner_id=%s)
                   OR (user_id=%s AND partner_id=%s)
                ORDER BY born_at DESC""",
                (uid, partner, partner, uid))
        else:
            c.execute("""SELECT * FROM unicorn_babies
                WHERE user_id=%s ORDER BY born_at DESC""", (uid,))
        return [dict(r) for r in c.fetchall()]

    def count_babies(self, uid):
        return len(self.get_babies(uid))

    def babies_income_per_day(self, uid):
        babies = self.get_babies(uid)
        return sum(b.get("level", 1) * BABY_INCOME_PER_LEVEL_PER_DAY for b in babies)

    def delete_couple_eggs_and_babies(self, uid1, uid2):
        c = self._c()
        c.execute("""DELETE FROM unicorn_eggs
            WHERE (user_id=%s AND partner_id=%s)
               OR (user_id=%s AND partner_id=%s)""",
            (uid1, uid2, uid2, uid1))
        c.execute("""DELETE FROM unicorn_babies
            WHERE (user_id=%s AND partner_id=%s)
               OR (user_id=%s AND partner_id=%s)""",
            (uid1, uid2, uid2, uid1))

    def rename_baby(self, uid, baby_id, new_name):
        c = self._c()
        c.execute("SELECT * FROM unicorn_babies WHERE id=%s", (baby_id,))
        r = c.fetchone()
        if not r:
            return False, "بیبی پیدا نشد"
        baby = dict(r)
        u = self.get_unicorn(uid)
        if not u:
            return False, "یونیکورن نداری"
        partner = u.get("married_to") or 0
        owns = (baby["user_id"] == uid or baby["partner_id"] == uid or
                (partner and (baby["user_id"] == partner or baby["partner_id"] == partner)))
        if not owns:
            return False, "مال تو نیست"
        clean = _clean_baby_name(new_name)
        if not clean:
            return False, f"اسم باید بین {BABY_NAME_MIN_LEN} تا {BABY_NAME_MAX_LEN} حرف باشه"
        if BABY_RENAME_COST > 0:
            if (u.get("points") or 0) < BABY_RENAME_COST:
                return False, f"{fmt_num(BABY_RENAME_COST)} پوینت لازمه"
            self.update(uid, points=(u.get("points") or 0) - BABY_RENAME_COST)
        c2 = self._c()
        c2.execute("UPDATE unicorn_babies SET name=%s WHERE id=%s", (clean, baby_id))
        return True, clean

    # ═══════════ 🎀 BABY CALL HELPERS ═══════════
    def _fetch_all_babies_light(self, limit=500):
        """Return list of {id, name, user_id, partner_id}."""
        try:
            c = self._c()
            c.execute("""SELECT id, name, user_id, partner_id FROM unicorn_babies
                         ORDER BY born_at DESC LIMIT %s""", (limit,))
            return [dict(r) for r in c.fetchall()]
        except Exception as e:
            logger.warning(f"fetch babies: {e}")
            return []

    def _find_babies_in_text(self, raw_text):
        """Return list of baby dicts whose clean name matches a word in text."""
        if not raw_text or len(raw_text) > BABY_CALL_MAX_MSG_LEN:
            return []
        # clean the incoming text
        text_clean = _strip_emoji(raw_text)
        if not text_clean:
            return []
        text_lower = text_clean.lower()
        # words set (split on whitespace and punctuation)
        words = re.findall(r"[\w\u0600-\u06FF]+", text_lower, flags=re.UNICODE)
        word_set = set(w for w in words if len(w) >= BABY_CALL_MIN_LEN)
        if not word_set and " " not in text_lower:
            return []

        babies = self._fetch_all_babies_light()
        if not babies:
            return []

        matches = []
        seen_ids = set()
        for b in babies:
            bid = b["id"]
            if bid in seen_ids:
                continue
            clean = _strip_emoji(b.get("name") or "").lower()
            if not clean:
                continue
            if " " in clean:
                # multi-word baby name — match exact phrase in text
                if clean in text_lower:
                    matches.append(b)
                    seen_ids.add(bid)
            else:
                if clean in word_set:
                    matches.append(b)
                    seen_ids.add(bid)
        return matches

    def _check_baby_call_cooldown(self, baby_id, chat_id):
        key = (baby_id, chat_id)
        last = self._baby_call_cd.get(key, 0)
        now = now_ts()
        if now - last < BABY_CALL_COOLDOWN_SEC:
            return False
        self._baby_call_cd[key] = now
        # light cleanup of old entries
        if len(self._baby_call_cd) > 500:
            cutoff = now - BABY_CALL_COOLDOWN_SEC * 4
            self._baby_call_cd = {k: v for k, v in self._baby_call_cd.items() if v > cutoff}
        return True

    # ═══════════ 🎀 FAMILY REPLY HELPERS (NEW) ═══════════
    def _register_baby_reply(self, chat_id, msg_id, baby_id):
        """Remember which baby sent this message, so we can reply later."""
        if not msg_id: return
        self._baby_reply_msgs[(chat_id, msg_id)] = baby_id
        # light cleanup
        if len(self._baby_reply_msgs) > 400:
            items = list(self._baby_reply_msgs.items())
            self._baby_reply_msgs = dict(items[-250:])

    def _find_baby_id_by_reply(self, chat_id, msg_id):
        return self._baby_reply_msgs.get((chat_id, msg_id))

    def _get_baby_full(self, baby_id):
        try:
            c = self._c()
            c.execute("SELECT * FROM unicorn_babies WHERE id=%s", (baby_id,))
            r = c.fetchone()
            return dict(r) if r else None
        except Exception as e:
            logger.warning(f"get_baby_full: {e}")
            return None

    def _count_siblings(self, baby):
        """How many siblings does this baby have (excluding itself)."""
        try:
            c = self._c()
            c.execute("""SELECT COUNT(*) AS n FROM unicorn_babies
                WHERE id != %s AND (
                    (user_id=%s AND partner_id=%s) OR
                    (user_id=%s AND partner_id=%s)
                )""",
                (baby["id"], baby["user_id"], baby["partner_id"],
                 baby["partner_id"], baby["user_id"]))
            return int(c.fetchone()["n"] or 0)
        except Exception:
            return 0

    def _classify_family_question(self, norm_text):
        """Detect question type: 'mom' | 'dad' | 'sibling' | None."""
        has_sib = any(k in norm_text for k in
                      ("خواهر", "برادر", "داداش", "ابجی", "آبجی", "همشیر", "هم شیر"))
        has_mom = any(k in norm_text for k in
                      ("مامان", "مادر", "مامانی", "ماما", "مامی"))
        has_dad = any(k in norm_text for k in
                      ("بابا", "پدر", "بابایی", "بابای", "بابام"))

        if not (has_sib or has_mom or has_dad):
            return None
        # it must look like a question
        is_q = ("کی" in norm_text or "کیه" in norm_text or
                "کدوم" in norm_text or "؟" in norm_text or "?" in norm_text or
                "کیه؟" in norm_text)
        if not is_q:
            return None
        # priority: siblings first (more specific), then mom, then dad
        if has_sib: return "sibling"
        if has_mom: return "mom"
        if has_dad: return "dad"
        return None

    def _ai_call_sync(self, messages, temperature, model, max_tokens=200, timeout=20):
        if not self.groq_key:
            raise RuntimeError("no groq key")
        payload = {"model": model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        headers = {"Authorization": f"Bearer {self.groq_key}",
                   "Content-Type": "application/json"}
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}")
        return r.json()

    async def _ai_baby_reply(self, baby_name, caller_name):
        """Generate a cute short baby reply using AI (with fallback)."""
        # fallback path when no key
        if not self.groq_key:
            return random.choice(BABY_FALLBACK_RESPONSES)

        sys_prompt = (
            "تو یه بیبی یونیکورن فوق‌العاده کیوت، بچگونه، مظلوم و گوگولی هستی 🦄💕\n"
            "مامان یا بابات صدات می‌زنن و تو باید با لحن بچگونه و لوس جواب بدی.\n\n"
            "🎀 قوانین خیلی مهم:\n"
            "1. خروجی فقط یه جمله‌ی کوتاه فارسی (بین ۲ تا ۸ کلمه)\n"
            "2. لحن: بچگونه، مظلوم، لوس، عاشق، ناز\n"
            "3. آخر جمله ۱ تا ۳ ایموجی کیوت بذار (🥺 💕 🍼 ✨ 🦄 💖 😘 🌸 👶 🍭)\n"
            "4. هیچ توضیح اضافه‌ای نده، فقط همون جمله\n"
            "5. از «مامانی»، «مامان»، «جووونم»، «دلام»، «بابایی» آزادانه استفاده کن\n"
            "6. هر بار جمله‌ی متفاوت بساز\n"
            "7. 🚫 تحت هیچ شرایطی اسم کسی رو نگو — فقط خودت جواب بده\n\n"
            "مثال‌های خوب:\n"
            "دلام مامانی 🥺💕\n"
            "جانم مامان؟ 🍼✨\n"
            "چیه مامانی؟ 🦄💖\n"
            "بیا بغلم مامان 🥺💗\n"
            "مامان صدام زدی؟ 🌸✨\n"
            "جووونم 🍼💕\n"
            "چشم مامان 🥺💖\n"
            "هاااای مامان 🌸💫\n"
            "مامانی اینجام 🦄🥺💕\n"
            "بغلم کن مامان 🍼✨\n"
        )
        user_prompt = (
            f"بیبی اسمش «{baby_name}» هست و الان "
            f"«{caller_name}» صداش زده.\n"
            f"یه جواب خیلی کیوت بچگونه بده."
        )
        msgs = [{"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}]

        models = self.ai_models or BABY_CALL_AI_MODELS
        for model in models:
            for attempt in range(2):
                try:
                    temp = 0.9 if attempt == 0 else 1.15
                    data = await asyncio.to_thread(
                        self._ai_call_sync, msgs, temp, model, 80
                    )
                    content = data["choices"][0]["message"]["content"].strip()
                    # clean up
                    content = re.sub(r"^[\"'\-\*\s]+", "", content)
                    content = re.sub(r"[\"'\s]+$", "", content)
                    content = content.replace("\n", " ").strip()
                    if not content:
                        raise ValueError("empty")
                    if len(content) > 80:
                        content = content[:80]
                    return content
                except Exception as e:
                    logger.warning(f"baby AI fail {model}: {str(e)[:60]}")
                    await asyncio.sleep(0.3)
        return random.choice(BABY_FALLBACK_RESPONSES)

    async def _handle_baby_call(self, event, raw_text):
        """Check if message calls any baby; if so, reply cutely."""
        if not BABY_CALL_ENABLED:
            return False
        try:
            if not raw_text or not raw_text.strip():
                return False
            # skip if message is a bot command or too long
            if len(raw_text) > BABY_CALL_MAX_MSG_LEN:
                return False
            # skip commands like نیه
            low = normalize_fa(raw_text.lower().strip())
            if low in ("نیه", "نیییه", "نههه", "neigh", "برداشت",
                       "غذا", "پاداش", "گردونه", "راهنما", "یونیکورن",
                       "تخم", "طلاق", "ازدواج", "دوئل", "دویل", "بجنگ",
                       "بیبی هام", "بچه هام", "بچه‌هام", "بچه ها"):
                return False

            matches = self._find_babies_in_text(raw_text)
            if not matches:
                return False

            # pick the first match (most recent by born_at desc)
            baby = matches[0]
            bid = baby["id"]
            chat_id = event.chat_id

            if not self._check_baby_call_cooldown(bid, chat_id):
                return True  # considered "handled" to block other handlers

            # find caller name
            try:
                s = await event.get_sender()
                caller_name = user_name(s)
            except Exception:
                caller_name = "مامان"

            # display clean baby name
            baby_display = _strip_emoji(baby.get("name") or "") or (baby.get("name") or "🐣")
            baby_display = h(baby_display)

            # generate reply
            reply_text = await self._ai_baby_reply(baby_display, caller_name)

            # send
            sent = None
            try:
                sent = await self._safe_send(chat_id, reply_text, reply_to=event.id)
            except Exception:
                try:
                    sent = await self._safe_send(chat_id, reply_text)
                except Exception:
                    pass
            if sent:
                try:
                    self._register_baby_reply(chat_id, sent.id, bid)
                except Exception:
                    pass
            return True
        except Exception as e:
            logger.exception(f"baby_call: {e}")
            return False

    # ═══════════ 🎀 FAMILY QUESTION HANDLER (NEW) ═══════════
    async def _handle_baby_family_reply(self, event, raw_text):
        """If user replies to a baby's message and asks about family — answer cutely."""
        try:
            if not event.reply_to_msg_id: return False
            if not raw_text or len(raw_text) > BABY_CALL_MAX_MSG_LEN: return False

            baby_id = self._find_baby_id_by_reply(event.chat_id, event.reply_to_msg_id)
            if not baby_id: return False
            baby = self._get_baby_full(baby_id)
            if not baby: return False

            norm = normalize_fa(raw_text.lower().strip())
            qtype = self._classify_family_question(norm)
            if not qtype: return False

            baby_disp = _strip_emoji(baby.get("name") or "") or "🐣"
            baby_disp = h(baby_disp)

            # ── sibling question ──
            if qtype == "sibling":
                siblings = self._count_siblings(baby)
                if siblings <= 0:
                    reply = random.choice(BABY_FAMILY_ONLY_CHILD)
                    reply = f"{baby_disp}: {reply}"
                else:
                    tmpl = random.choice(BABY_FAMILY_HAS_SIBLINGS)
                    reply = tmpl.format(n=siblings + 1, sib=siblings)
                    reply = f"{baby_disp}: {reply}"
            else:
                # ── mom or dad question ──
                user_id = baby.get("user_id") or 0
                partner_id = baby.get("partner_id") or 0

                if qtype == "mom":
                    target = user_id or partner_id
                    label = "مامانی"
                    emo = "💖👶"
                else:  # dad
                    target = partner_id or user_id
                    label = "بابایی"
                    emo = "💙👶"

                if not target:
                    reply = random.choice(BABY_FAMILY_UNKNOWN)
                    reply = f"{baby_disp}: {reply}"
                else:
                    templates = [
                        f"{baby_disp}:\n{label} اینه 👇\n<a href=\"tg://user?id={target}\">👉 اینجا 👈</a> {emo}",
                        f"{baby_disp}:\n{label} اینه 🥺\n<a href=\"tg://user?id={target}\">کلیک کن</a> {emo}",
                        f"{baby_disp}:\nبیا {label}:\n<a href=\"tg://user?id={target}\">این 👶</a> {emo}",
                        f"{baby_disp}:\n{baby_disp} میگه {label} اینه 💕\n<a href=\"tg://user?id={target}\">👉 {label} 👈</a> {emo}",
                    ]
                    reply = random.choice(templates)

            try:
                sent = await self._safe_send(
                    event.chat_id, reply,
                    parse_mode="html", reply_to=event.id,
                )
                if sent:
                    self._register_baby_reply(event.chat_id, sent.id, baby_id)
            except Exception:
                pass
            return True
        except Exception as e:
            logger.exception(f"baby family reply: {e}")
            return False

    # ═══════════ TICKER ═══════════
    async def _ticker(self):
        await asyncio.sleep(8)
        while self._running:
            try:
                self._ensure_alive()
                self._tick_all()
                self._hatch_eggs()
                self._babies_income()
            except Exception as e:
                logger.exception(f"tick: {e}")
            await asyncio.sleep(TICK_INTERVAL)

    def _hatch_eggs(self):
        ts = now_ts()
        c = self._c()
        c.execute("""SELECT * FROM unicorn_eggs
            WHERE hatched_at IS NULL
            AND laid_at <= %s""", (ts - EGG_HATCH_SEC,))
        ready = c.fetchall()
        for egg in ready:
            try:
                self._hatch_one(dict(egg), ts)
            except Exception as e:
                logger.warning(f"hatch: {e}")

    def _hatch_one(self, egg, ts):
        egg_id = egg["id"]
        user_id = egg["user_id"]
        partner_id = egg["partner_id"]
        name = random.choice(BABY_NAMES)
        c = self._c()
        c.execute("""INSERT INTO unicorn_babies
            (user_id, partner_id, name, level, born_at, last_income)
            VALUES (%s, %s, %s, 1, %s, %s) RETURNING id""",
            (user_id, partner_id, name, ts, ts))
        baby_id = c.fetchone()["id"]
        c.execute("""UPDATE unicorn_eggs SET hatched_at=%s, baby_id=%s WHERE id=%s""",
                  (ts, baby_id, egg_id))
        for u in (user_id, partner_id):
            if u and u != 0:
                self.add_achievement(u, "first_baby")
                if self.count_babies(u) >= 5:
                    self.add_achievement(u, "baby_master")

    def _babies_income(self):
        ts = now_ts()
        c = self._c()
        c.execute("""SELECT * FROM unicorn_babies WHERE last_income IS NOT NULL""")
        for b in c.fetchall():
            baby = dict(b)
            last = baby.get("last_income") or baby.get("born_at") or ts
            elapsed = ts - last
            if elapsed < 60:
                continue
            rate_per_sec = (baby.get("level", 1) * BABY_INCOME_PER_LEVEL_PER_DAY) / 86400
            income = elapsed * rate_per_sec
            for uid in (baby["user_id"], baby["partner_id"]):
                if not uid or uid == 0: continue
                u = self.get_unicorn(uid)
                if not u: continue
                if u.get("angry"): continue
                new_pending = float(u.get("pending") or 0) + income
                self.update(uid, pending=new_pending)
            c2 = self._c()
            c2.execute("""UPDATE unicorn_babies SET last_income=%s WHERE id=%s""",
                       (ts, baby["id"]))

    def _tick_all(self):
        ts = now_ts()
        c = self._c()
        c.execute("SELECT * FROM unicorns")
        for row in c.fetchall():
            try: self._tick_one(dict(row), ts)
            except Exception as e: logger.warning(f"tick: {e}")

    def _tick_one(self, row, ts):
        uid = row["user_id"]
        level = max(1, min(10, row.get("level") or 1))
        rate = LEVEL_RATES[level - 1]
        boost_mult = 1.0
        if row.get("boost_until", 0) > ts:
            boost_mult = row.get("boost_mult") or 1.0
        last_h = row.get("last_hunger_tick") or ts
        dec = (ts - last_h) // HUNGER_DECAY_SEC
        hunger = row.get("hunger", 100)
        new_last_h = last_h
        if dec > 0:
            hunger = max(0, hunger - dec)
            new_last_h = last_h + dec * HUNGER_DECAY_SEC
        angry = 1 if hunger <= 0 else 0
        pending = float(row.get("pending") or 0)
        last_p = row.get("last_produce") or ts
        elapsed = ts - last_p
        if not angry and elapsed > 0:
            max_p = rate * boost_mult * 3600 * PENDING_CAP_HOURS
            if pending < max_p:
                pending = min(max_p, pending + elapsed * rate * boost_mult)
        c = self._c()
        c.execute("""UPDATE unicorns SET hunger=%s, angry=%s, pending=%s,
            last_hunger_tick=%s, last_produce=%s WHERE user_id=%s""",
            (hunger, angry, pending, new_last_h, ts, uid))

    # ═══════════ MESSAGE HANDLER ═══════════
    async def on_message(self, event):
        try:
            if event.is_private: return
            me = await self.client.get_me()
            if event.sender_id == me.id: return
            raw = (event.raw_text or "").strip()
            if not raw: return
            uid = event.sender_id
            low = normalize_fa(raw.lower().strip())
            norm_raw = normalize_fa(raw)

            # 🎀 NEW: baby call / family question (BEFORE all other handlers)
            if BABY_CALL_ENABLED:
                # ۱) if reply to a baby message + family question
                try:
                    handled = await self._handle_baby_family_reply(event, raw)
                    if handled: return
                except Exception as e:
                    logger.warning(f"baby family outer: {e}")
                # ۲) if a baby name is called
                try:
                    handled = await self._handle_baby_call(event, raw)
                    if handled: return
                except Exception as e:
                    logger.warning(f"baby_call outer: {e}")

            # ✏️ Rename pending — catch the next message
            if uid in self._pending_renames:
                pending = self._pending_renames.get(uid)
                if low in ("لغو", "کنسل", "cancel", "بیخیال", "❌", "بازگشت", "back"):
                    self._pending_renames.pop(uid, None)
                    await self._safe_send(event.chat_id,
                        f"{PE('cross','❌')} <b>تغییر اسم لغو شد.</b>",
                        parse_mode="html", reply_to=event.id)
                    return
                baby_id = pending.get("baby_id")
                ok, result = self.rename_baby(uid, baby_id, raw)
                self._pending_renames.pop(uid, None)
                if ok:
                    new_name = result
                    await self._safe_send(event.chat_id,
                        f"        ✏️ {PE('sparkle','✨')} ✏️\n"
                        f"    {PE('party','🎉')} <b>اسم عوض شد!</b> {PE('party','🎉')}\n"
                        f"{DIV}\n"
                        f"📛 اسم جدید: <b>{h(new_name)}</b>\n"
                        f"{PE('heart','💖')} <i>حالا این اسمشه!</i>",
                        parse_mode="html", reply_to=event.id)
                    fake = type("E", (), {"chat_id": event.chat_id,
                                          "id": pending.get("msg_id"),
                                          "message_id": pending.get("msg_id"),
                                          "reply_to_msg_id": None})()
                    try:
                        await self._show_babies(fake, uid, edit_msg=pending.get("msg_id"))
                    except Exception: pass
                else:
                    await self._safe_send(event.chat_id,
                        f"{PE('warning','⚠️')} <b>نشد!</b>\n"
                        f"{PE('info','ℹ️')} {result}",
                        parse_mode="html", reply_to=event.id)
                return

            try:
                s = await event.get_sender()
                name = user_name(s)
            except Exception:
                name = str(uid)
            self.get_or_create(uid, name)

            # 🦄 کد UNICORN
            if raw.strip() == "UNICORN":
                await self._handle_unicorn_code(event, uid); return

            # انتقال
            if event.reply_to_msg_id and "انتقال" in norm_raw and "یونیکورن" in norm_raw:
                await self._handle_transfer(event, uid, norm_raw); return

            # طلاق
            if low in ("طلاق", "جدا", "جدا شو", "divorce"):
                if not event.reply_to_msg_id:
                    await self._divorce_hint(event); return
                await self._handle_divorce(event, uid); return

            # دوئل
            if low in ("دویل", "دوئل", "نبرد", "مبارزه", "جنگ", "بجنگ", "دوعل"):
                if not event.reply_to_msg_id:
                    await self._show_battle_panel(event.chat_id, uid, reply_to=event.id); return
                await self._handle_battle(event, uid); return

            # پنل
            if low in ("تنظیمات دوئل", "تنظیمات دوعل", "تنظیمات نبرد",
                       "زرادخانه", "ارتش", "قهرمانان", "سلاح", "armory"):
                await self._show_battle_panel(event.chat_id, uid, reply_to=event.id); return

            # ازدواج
            if low in ("ازدواج", "ازدواج کن", "بگیر"):
                if not event.reply_to_msg_id:
                    await self._marry_hint(event); return
                await self._handle_marry(event, uid); return

            # تخم
            if low in ("تخم", "پرورش", "جوجه"):
                await self._handle_breed(event, uid); return

            # بیبی ها
            if low in ("بیبی هام", "بچه هام", "بچه‌هام", "بیبی", "بیبی‌ها",
                       "فرزندام", "فرزندهام", "بچه ها"):
                await self._show_babies(event, uid); return

            # نیه
            if low in ("نیه", "نیییه", "نههه", "neigh"):
                await self._handle_neigh(event, uid); return

            # برداشت
            if low in ("برداشت", "برداشت کن", "جمع", "جمع کن", "collect"):
                await self._do_withdraw(uid, event.chat_id, reply_to=event.id); return

            # غذا
            if low in ("غذا", "غذا بده", "feed", "خوراک"):
                await self._do_feed(uid, event.chat_id, reply_to=event.id); return

            # پاداش
            if low in ("پاداش", "پاداش روزانه", "daily"):
                await self._do_daily(uid, event.chat_id, reply_to=event.id); return

            # گردونه
            if low in ("گردونه", "شانس", "spin"):
                await self._do_spin(uid, event.chat_id, reply_to=event.id); return

            # راهنما
            if low in ("راهنما", "کمک", "help", "اموزش", "آموزش"):
                await self._show_help(event.chat_id, reply_to=event.id); return

            # لیدربورد
            if low in ("لیدربورد", "برترین", "بهترین", "top", "رتبه"):
                await self._show_leaderboard(event.chat_id, reply_to=event.id); return

            # آمار
            if low in ("یونیکورن هام", "یونیکورنهام", "یونیکورن های من",
                       "امار یونیکورن", "آمار یونیکورن", "یونیکورن هام کامل"):
                await self._show_full_stats(event.chat_id, uid, reply_to=event.id); return

            if (event.reply_to_msg_id and low in ("یونیکورن هاش", "یونیکورن های اون",
                                                  "یونیکورن هاش کامل")):
                rm = await event.get_reply_message()
                target = rm.sender_id if rm else None
                if target:
                    self.get_or_create(target, "—")
                    await self._show_full_stats(event.chat_id, target, reply_to=event.id); return

            # پروفایل
            if low in ("یونیکورن", "تک شاخ", "یونیکورنم", "شونیکورن", "پروفایل"):
                await self._show_profile(uid, event.chat_id, reply_to=event.id, force_new=True); return
        except Exception as e:
            logger.exception(f"uni msg: {e}")

    # ═══════════ 🦄 UNICORN CODE ═══════════
    async def _handle_unicorn_code(self, event, uid):
        try:
            u = self.get_unicorn(uid)
            if not u:
                await self._safe_send(event.chat_id,
                    f"{PE('warning','⚠️')} اول یونیکورت رو بساز! <code>نیه</code> بزن.",
                    parse_mode="html", reply_to=event.id)
                return
            if (u.get("unicorn_code_used") or 0) > 0:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} <b>قبلاً استفاده کردی!</b>\n"
                    f"{PE('info','ℹ️')} <i>این کد یک‌بار مصرفه.</i>",
                    parse_mode="html", reply_to=event.id)
                return

            reward = UNICORN_CODE_REWARD
            self.update(uid,
                        unicorn_code_used=now_ts(),
                        points=(u.get("points") or 0) + reward,
                        total_earned=(u.get("total_earned") or 0) + reward)
            new_ach = self.check_achievements(uid)

            lines = [
                f"        🦄 {PE('sparkle','✨')} 🦄",
                f"    {PE('party','🎉')} <b>کد یونیکورن فعال شد!</b> {PE('party','🎉')}",
                f"{DIV}",
                f"{PE('gem','💎')} پاداش: <code>+{fmt_full(reward)}</code> پوینت",
                f"{PE('gift','🎁')} موجودی: <code>{fmt_full((u.get('points') or 0) + reward)}</code>",
                f"{DIV2}",
                f"{PE('info','ℹ️')} <i>این کد یک‌بار مصرفه!</i>",
                f"{PE('heart','💖')} <i>مرسی که با ما هستی</i>",
            ]
            if new_ach:
                names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}"
                                    for k in new_ach[:2]])
                lines.append(f"\n{PE('trophy','🏆')} {names}")

            await self._safe_send(event.chat_id, "\n".join(lines),
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"unicorn code: {e}")

    # ═══════════ PROFILE ═══════════
    async def _show_profile(self, uid, chat_id, reply_to=None, flash=None, force_new=False):
        u = self.get_unicorn(uid)
        if not u:
            try:
                await self._safe_send(chat_id,
                    f"{PE('cross','❌')} <b>یونیکورت پیدا نشد!</b>\n"
                    f"اول <code>نیه</code> بزن.",
                    parse_mode="html", reply_to=reply_to)
            except Exception: pass
            return
        try:
            self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
        except Exception: pass
        try:
            text = self._render_profile(u, flash=flash)
        except Exception as e:
            logger.exception(f"render: {e}")
            text = f"{PE('cross','❌')} خطا"

        btns = self._profile_buttons(uid)
        msg_id = u.get("last_profile_msg") or 0
        stored_chat = u.get("last_profile_chat") or 0

        if not force_new and msg_id and stored_chat == chat_id:
            ok = await self._safe_edit_msg(chat_id, msg_id, text, buttons=btns)
            if ok: return

        attempts = [
            ("with-btn",  text,                {"parse_mode": "html", "buttons": btns, "reply_to": reply_to}),
            ("with-btn2", text,                {"parse_mode": "html", "buttons": btns}),
            ("plain",     strip_premium(text), {"parse_mode": "html", "buttons": btns}),
            ("plain2",    strip_premium(text), {"parse_mode": "html"}),
        ]
        for label, send_text, kwargs in attempts:
            try:
                kw = {k: v for k, v in kwargs.items() if v is not None}
                sent = await self.client.send_message(chat_id, send_text, **kw)
                if sent:
                    self.update(uid, last_profile_msg=sent.id, last_profile_chat=chat_id)
                    return
            except Exception as e:
                logger.warning(f"profile '{label}': {type(e).__name__}: {str(e)[:80]}")
                if "reply" in str(e).lower(): reply_to = None
                await asyncio.sleep(0.3)
                continue

    def _render_profile(self, u, flash=None):
        level = max(1, min(10, u.get("level") or 1))
        rate = LEVEL_RATES[level - 1]
        boost_mult = u.get("boost_mult") if u.get("boost_until", 0) > now_ts() else 1.0
        per_hour = rate * (boost_mult or 1.0) * 3600
        hunger = u.get("hunger", 100)
        angry = u.get("angry", 0)
        points = u.get("points", 0)
        pending = int(u.get("pending") or 0)
        neigh = u.get("neigh_count", 0)
        skin_key = u.get("color") or "classic"
        skin_emoji, skin_name, _ = SKINS.get(skin_key, SKINS["classic"])
        face = hunger_face(hunger, angry)
        name = h(u.get("name") or "—")
        uid = u["user_id"]

        line1 = f"{face} <b>{skin_emoji} {name}</b>"
        line2 = f"{PE('crown','👑')} <b>{LEVEL_NAMES[level-1]}</b>  ·  Lv<code>{level}</code>"

        status_parts = [f"{PE('diamond','💎')} {skin_name}"]
        if u.get("married_to"):
            status_parts.append(f"{PE('heart','💖')} متأهل")
        if angry:
            status_parts.append(f"{PE('cross','❌')} قهر")
        elif hunger < 30:
            status_parts.append(f"{PE('warning','⚠️')} گشنه")
        if boost_mult > 1.0:
            status_parts.append(f"{PE('bolt','⚡')}x{boost_mult:g}")
        line3 = "  ·  ".join(status_parts)

        line4 = (f"{PE('gem','💎')} <b>{fmt_num(points)}</b>"
                 f"  ·  {PE('gift','🎁')} <b>{fmt_num(pending)}</b>"
                 f"  ·  {PE('bolt','⚡')} {per_hour:.0f}/س")
        line5 = f"🍰 {hunger_bar(hunger)} <code>{hunger}%</code>"
        line6 = f"{PE('wave','👋')} نیه: <b>{neigh}</b>"

        try:
            p = self.compute_power(uid)
            if p['total'] > 0:
                battle_line = f"\n⚔️ {fmt_full(p['total'])}  ·  🛡️{p['soldier_count']}  ·  👑{p['heroes_count']}"
            else:
                battle_line = ""
        except Exception:
            battle_line = ""

        eggs = self.count_eggs(uid)
        babies = self.count_babies(uid)
        baby_income = self.babies_income_per_day(uid)
        family_parts = []
        if eggs > 0: family_parts.append(f"🥚 {eggs}")
        if babies > 0: family_parts.append(f"🐣 {babies}")
        family_line = ""
        if family_parts:
            family_line = "  ·  " + "  ·  ".join(family_parts)
            if baby_income > 0:
                family_line += f"  ·  💰 {fmt_num(baby_income)}/روز"

        header = f"{PE('sparkle','✨')} <b>پروفایل یونیکورن</b> {PE('sparkle','✨')}"

        if level < 10:
            nxt = level + 1
            need_n = LEVEL_THRESHOLDS[nxt - 1]
            need_p = LEVEL_POINT_COST[nxt - 1]
            bar_n = progress_bar(neigh, need_n)
            bar_p = progress_bar(points, need_p)
            lvl_block = (
                f"{PE('star','⭐')} <b>تا لول {nxt}:</b>\n"
                f"👋 {bar_n} <code>{neigh}/{need_n}</code>\n"
                f"{PE('gem','💎')} {bar_p} <code>{fmt_num(points)}/{fmt_num(need_p)}</code>"
            )
        else:
            lvl_block = f"{PE('crown','👑')} <b>آخرین لول!</b>"

        parts = []
        if flash:
            parts.append(flash); parts.append(DIV2)
        parts.append(header)
        parts.append(DIV)
        parts.append(line1)
        parts.append(line2)
        parts.append(line3)
        parts.append("")
        parts.append(line4)
        parts.append(line5)
        parts.append(line6 + family_line + battle_line)
        parts.append(DIV2)
        parts.append(lvl_block)
        return "\n".join(parts)

    def _profile_buttons(self, uid):
        return [
            [Button.inline("🍰 غذا", data=f"uni:feed:{uid}".encode()),
             Button.inline("💰 برداشت", data=f"uni:withdraw:{uid}".encode())],
            [Button.inline("🎁 روزانه", data=f"uni:daily:{uid}".encode()),
             Button.inline("🎰 گردونه", data=f"uni:spin:{uid}".encode())],
            [Button.inline("⚔️ دوئل", data=f"uni:armory:{uid}".encode()),
             Button.inline("🎨 رنگ‌ها", data=f"uni:skins:{uid}".encode())],
            [Button.inline("🥚 تخم", data=f"uni:breed:{uid}".encode()),
             Button.inline("🐣 بیبی‌ها", data=f"uni:babies:{uid}".encode())],
            [Button.inline("💍 ازدواج", data=f"uni:marry:{uid}".encode()),
             Button.inline("💔 طلاق", data=f"uni:divorce:{uid}".encode())],
            [Button.inline("🏆 دستاورد", data=f"uni:ach:{uid}".encode()),
             Button.inline("💸 انتقال", data=f"uni:transfer:{uid}".encode())],
            [Button.inline("🏠 خانه", data=f"uni:home:{uid}".encode()),
             Button.inline("🏅 لیدر", data=f"uni:top:{uid}".encode())],
            [Button.inline("📊 آمار", data=f"uni:stats:{uid}".encode()),
             Button.inline("🆘 راهنما", data=f"uni:help:{uid}".encode())],
            [Button.inline("🔄 بروزرسانی", data=f"uni:refresh:{uid}".encode())],
        ]

    # ═══════════ NEIGH ═══════════
    async def _handle_neigh(self, event, uid):
        try:
            u = self.get_or_create(uid, "—")
            ts = now_ts()
            p_name = h(u.get("name") or "—")

            if u.get("angry"):
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} <b>{p_name} قهره!</b> اول غذا بده {PE('heart','💔')}",
                    parse_mode="html", reply_to=event.id)
                return

            last = u.get("last_neigh") or 0
            if last and ts - last < NEIGH_COOLDOWN_SEC:
                rem = NEIGH_COOLDOWN_SEC - (ts - last)
                await self._safe_send(event.chat_id,
                    f"{PE('hourglass','⏰')} <b>{p_name} تازه نیه کشید!</b>\n"
                    f"تا <code>{fmt_time(rem)}</code> صبر کن 💤",
                    parse_mode="html", reply_to=event.id)
                return

            reward = random.randint(NEIGH_REWARD_MIN, NEIGH_REWARD_MAX)
            level = max(1, min(10, u.get("level") or 1))
            if level >= 8: reward *= 2
            elif level >= 5: reward = int(reward * 1.5)

            combo_bonus = 0
            combo_text = ""
            prev = self._combo.get(event.chat_id)
            if prev and prev[0] != uid and ts - prev[1] <= COMBO_WINDOW_SEC:
                combo_bonus = int(reward * (COMBO_BONUS_MULT - 1))
                reward += combo_bonus
                combo_text = f"\n{PE('fire','🔥')} <b>کمبو!</b> <code>+{fmt_num(combo_bonus)}</code>"
            self._combo[event.chat_id] = (uid, ts)

            event_res = roll_neigh_event()
            event_text = ""
            upd_extra = {}
            if event_res:
                kind, val, msg = event_res
                if kind == "bonus_pts":
                    reward += val
                    event_text = f"\n{msg}\n{PE('gem','💎')} <code>+{fmt_num(val)}</code>"
                elif kind == "hunger":
                    new_h = min(100, (u.get("hunger") or 100) + val)
                    upd_extra["hunger"] = new_h
                    event_text = f"\n{msg}"
                elif kind == "boost":
                    upd_extra["boost_mult"] = 2.0
                    upd_extra["boost_until"] = ts + val
                    event_text = f"\n{msg}"
                elif kind == "bomb":
                    reward = max(0, reward + val)
                    event_text = f"\n{msg}\n{PE('warning','⚠️')} <code>{fmt_num(val)}</code>"

            new_neigh = (u.get("neigh_count") or 0) + 1
            new_points = (u.get("points") or 0) + reward
            new_total = (u.get("total_earned") or 0) + reward
            new_total_neigh = (u.get("total_neigh_ever") or 0) + 1

            final_upd = dict(last_neigh=ts, neigh_count=new_neigh,
                             points=new_points, total_earned=new_total,
                             total_neigh_ever=new_total_neigh)
            final_upd.update(upd_extra)
            self.update(uid, **final_upd)

            u2 = self.get_unicorn(uid)
            leveled = self._check_levelup(uid, u2)
            new_ach = self.check_achievements(uid)

            v = random.choice(["🦄💖", "🌈✨", "💫🌟", "🎀💝", "🌙⭐", "🦄💫", "🌸🦄"])
            lines = [
                f"{v} {PE('sparkle','✨')} <b>{p_name} نیـه زد!</b>",
                f"{PE('gift','🎁')} پاداش: <code>+{fmt_num(reward)}</code>",
                f"{PE('gem','💎')} مجموع: <code>{fmt_num(new_points)}</code>",
            ]
            if combo_text: lines.append(combo_text)
            if event_text: lines.append(event_text)
            if leveled:
                nxt = leveled["new_level"]
                lines.append(f"\n🎊 {PE('party','🎉')} <b>لـول آپ → {nxt}</b> {PE('party','🎉')}")
                lines.append(f"🔓 {LEVEL_UNLOCKS[nxt-1]}")
            if new_ach:
                names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}"
                                    for k in new_ach[:2]])
                lines.append(f"\n{PE('trophy','🏆')} {names}")
            await self._safe_send(event.chat_id, "\n".join(lines),
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"neigh: {e}")

    def _check_levelup(self, uid, u):
        if not u: return None
        level = max(1, min(10, u.get("level") or 1))
        if level >= 10: return None
        neigh = u.get("neigh_count") or 0
        points = u.get("points") or 0
        nxt = level + 1
        if neigh >= LEVEL_THRESHOLDS[nxt - 1] and points >= LEVEL_POINT_COST[nxt - 1]:
            self.update(uid, level=nxt, points=points - LEVEL_POINT_COST[nxt - 1])
            return {"new_level": nxt}
        return None

    # ═══════════ FEED ═══════════
    async def _do_feed(self, uid, chat_id, reply_to=None):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            hunger = u.get("hunger", 100)
            points = u.get("points") or 0
            if hunger >= 100:
                await self._show_profile(uid, chat_id, reply_to=reply_to,
                    flash=f"{PE('check','✅')} <b>سیر کامله!</b> 🌸")
                return
            if points < FEED_COST:
                await self._show_profile(uid, chat_id, reply_to=reply_to,
                    flash=f"{PE('cross','❌')} <b>پوینت کمه!</b> نیاز <code>{fmt_num(FEED_COST)}</code>")
                return
            new_h = min(100, hunger + FEED_HUNGER_BOOST)
            self.update(uid, hunger=new_h, points=points - FEED_COST, angry=0,
                        last_feed=now_ts(),
                        total_fed=(u.get("total_fed") or 0) + 1,
                        last_hunger_tick=now_ts())
            v = random.choice(["🍰🍬", "🧁🍭", "🍪🍩", "🎂🌸", "🍯💖"])
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{v} <b>نوم‌نوم!</b> سیری <code>{new_h}%</code> {PE('heart','💖')}")
        except Exception as e:
            logger.exception(f"feed: {e}")

    # ═══════════ WITHDRAW ═══════════
    async def _do_withdraw(self, uid, chat_id, reply_to=None):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            try:
                self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
            except Exception: pass
            pending = int(u.get("pending") or 0)
            if pending < 1:
                await self._show_profile(uid, chat_id, reply_to=reply_to,
                    flash=f"{PE('info','ℹ️')} چیزی برای برداشت نیست! 🦄")
                return
            if u.get("angry"):
                await self._show_profile(uid, chat_id, reply_to=reply_to,
                    flash=f"{PE('cross','❌')} قهره! اول غذا بده {PE('heart','💔')}")
                return
            self.update(uid, points=(u.get("points") or 0) + pending,
                        pending=0, total_earned=(u.get("total_earned") or 0) + pending,
                        last_produce=now_ts())
            new_ach = self.check_achievements(uid)
            flash = f"{PE('gift','🎁')} <b>برداشت!</b> <code>+{fmt_num(pending)}</code>"
            if new_ach:
                names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}"
                                    for k in new_ach[:2]])
                flash += f"\n\n{PE('trophy','🏆')} {names}"
            await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)
        except Exception as e:
            logger.exception(f"withdraw: {e}")

    # ═══════════ DAILY ═══════════
    async def _do_daily(self, uid, chat_id, reply_to=None, edit_msg=None):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            ts = now_ts()
            last = u.get("last_daily") or 0
            if last and ts - last < DAILY_COOLDOWN_SEC:
                rem = DAILY_COOLDOWN_SEC - (ts - last)
                msg = f"{PE('hourglass','⏰')} پاداش بعدی: <code>{fmt_time(rem)}</code>"
                if edit_msg:
                    await self._safe_edit_msg(chat_id, edit_msg, msg, buttons=self._profile_buttons(uid))
                elif reply_to:
                    await self._show_profile(uid, chat_id, reply_to=reply_to, flash=msg)
                return

            streak = u.get("daily_streak") or 0
            if last and ts - last < DAILY_COOLDOWN_SEC * 2:
                streak += 1
            else:
                streak = 1
            best = max(streak, u.get("daily_best") or 0)
            reward = min(DAILY_BASE_REWARD + (streak - 1) * DAILY_STREAK_BONUS,
                         DAILY_BASE_REWARD + DAILY_MAX_STREAK * DAILY_STREAK_BONUS)
            self.update(uid, last_daily=ts, daily_streak=streak, daily_best=best,
                        points=(u.get("points") or 0) + reward,
                        total_earned=(u.get("total_earned") or 0) + reward)
            new_ach = self.check_achievements(uid)
            flash = (f"{PE('gift','🎁')} <b>پاداش روزانه!</b>\n"
                     f"{PE('fire','🔥')} استریک <code>{streak}</code>  ·  "
                     f"{PE('gem','💎')} <code>+{fmt_num(reward)}</code>")
            if new_ach:
                names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}"
                                    for k in new_ach[:2]])
                flash += f"\n\n{PE('trophy','🏆')} {names}"
            if edit_msg:
                try:
                    u2 = self.get_unicorn(uid)
                    text = self._render_profile(u2, flash=flash)
                    await self._safe_edit_msg(chat_id, edit_msg, text,
                        buttons=self._profile_buttons(uid))
                except Exception: pass
            else:
                await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)
        except Exception as e:
            logger.exception(f"daily: {e}")

    # ═══════════ SPIN ═══════════
    async def _do_spin(self, uid, chat_id, reply_to=None, edit_msg=None):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            ts = now_ts()
            last = u.get("last_spin") or 0
            if last and ts - last < SPIN_COOLDOWN_SEC:
                rem = SPIN_COOLDOWN_SEC - (ts - last)
                msg = f"🎰 گردونه آماده نیست! <code>{fmt_time(rem)}</code>"
                if edit_msg:
                    await self._safe_edit_msg(chat_id, edit_msg, msg, buttons=self._profile_buttons(uid))
                elif reply_to:
                    await self._show_profile(uid, chat_id, reply_to=reply_to, flash=msg)
                return

            total_w = sum(r[4] for r in SPIN_REWARDS)
            pick = random.randint(1, total_w); acc = 0
            chosen = SPIN_REWARDS[0]
            for r in SPIN_REWARDS:
                acc += r[4]
                if pick <= acc: chosen = r; break
            emoji, label, kind, val, _ = chosen
            flash = f"🎰 {PE('party','🎉')} <b>گردونه!</b>\n{emoji} {label}"
            upd = {"last_spin": ts, "spin_count": (u.get("spin_count") or 0) + 1}
            if kind == "points":
                upd["points"] = (u.get("points") or 0) + val
                upd["total_earned"] = (u.get("total_earned") or 0) + val
                flash += f"\n{PE('gem','💎')} <code>+{fmt_num(val)}</code>"
            elif kind.startswith("boost"):
                parts = kind.split("_")
                mult = int(parts[0].replace("boost", ""))
                dur = int(parts[1])
                upd["boost_mult"] = float(mult); upd["boost_until"] = ts + dur
                flash += f"\n{PE('bolt','⚡')} x{mult} ({dur//60} دقیقه)"
            elif kind == "hunger":
                upd["hunger"] = 100; upd["angry"] = 0; upd["last_hunger_tick"] = ts
                flash += "\n🍰 سیری فول!"
            elif kind == "egg":
                partner = u.get("married_to") or 0
                if partner:
                    c = self._c()
                    c.execute("""INSERT INTO unicorn_eggs
                        (user_id, partner_id, laid_at) VALUES (%s, %s, %s)""",
                        (uid, partner, ts))
                    flash += "\n🥚 یه تخم جدید از گردونه!"
                else:
                    upd["eggs"] = (u.get("eggs") or 0) + 1
                    flash += "\n🥚 یه تخم (فقط بعد ازدواج هچ میشه)"
            self.update(uid, **upd)
            new_ach = self.check_achievements(uid)
            if new_ach:
                names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}"
                                    for k in new_ach[:2]])
                flash += f"\n\n{PE('trophy','🏆')} {names}"
            if edit_msg:
                try:
                    u2 = self.get_unicorn(uid)
                    text = self._render_profile(u2, flash=flash)
                    await self._safe_edit_msg(chat_id, edit_msg, text,
                        buttons=self._profile_buttons(uid))
                except Exception: pass
            else:
                await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)
        except Exception as e:
            logger.exception(f"spin: {e}")

    # ═══════════ HINTS ═══════════
    async def _marry_hint(self, event):
        await self._safe_send(event.chat_id,
            f"💍 {PE('heart','💖')} <b>ازدواج</b>\n"
            f"{DIV}\n"
            f"روی پیام طرف <b>ریپلای</b> کن و بنویس <code>ازدواج</code>",
            parse_mode="html", reply_to=event.id)

    async def _divorce_hint(self, event):
        await self._safe_send(event.chat_id,
            f"💔 {PE('cross','❌')} <b>طلاق</b>\n"
            f"{DIV}\n"
            f"روی پیام همسرت <b>ریپلای</b> کن و بنویس <code>طلاق</code>\n\n"
            f"{PE('warning','⚠️')} <i>هشدار: تخم‌ها و بیبی‌ها از بین می‌رن!</i>",
            parse_mode="html", reply_to=event.id)

    # ═══════════ TRANSFER ═══════════
    async def _handle_transfer(self, event, uid, raw):
        try:
            m = re.search(r"(\d+(?:[.,]\d+)?\s*[kmbKMB]?)",
                          raw.replace("انتقال", "").replace("یونیکورن", ""))
            if not m:
                await self._safe_send(event.chat_id,
                    f"{PE('warning','⚠️')} فرمت: ریپلای + <code>انتقال یونیکورن 100k</code>",
                    parse_mode="html", reply_to=event.id); return
            amount = parse_amount(m.group(1))
            if not amount or amount < 1:
                await self._safe_send(event.chat_id, f"{PE('cross','❌')} مقدار نامعتبر!",
                    parse_mode="html", reply_to=event.id); return
            rm = await event.get_reply_message()
            if not rm: return
            to_uid = rm.sender_id
            if to_uid == uid:
                await self._safe_send(event.chat_id, f"{PE('cross','❌')} به خودت!",
                    parse_mode="html", reply_to=event.id); return
            su = self.get_unicorn(uid) or self.get_or_create(uid, "—")
            if (su.get("points") or 0) < amount:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} پوینت کمه! داری <code>{fmt_num(su.get('points', 0))}</code>",
                    parse_mode="html", reply_to=event.id); return
            try:
                s = await self.client.get_entity(to_uid); to_name = user_name(s)
            except Exception: to_name = str(to_uid)
            self.get_or_create(to_uid, to_name)
            tu = self.get_unicorn(to_uid)
            self.update(uid, points=(su.get("points") or 0) - amount)
            self.update(to_uid, points=(tu.get("points") or 0) + amount)
            c = self._c()
            c.execute("INSERT INTO unicorn_transfers (from_id,to_id,amount,at) VALUES (%s,%s,%s,%s)",
                      (uid, to_uid, amount, now_ts()))
            self.check_achievements(uid); self.check_achievements(to_uid)
            try:
                so = await event.get_sender(); fname = user_name(so)
            except Exception: fname = str(uid)
            await self._safe_send(event.chat_id,
                f"{PE('rocket','🚀')} <b>انتقال موفق!</b>\n"
                f"{DIV}\n"
                f"{PE('user','👤')} <a href=\"tg://user?id={uid}\">{h(fname)}</a>\n"
                f"   ⬇️ <code>{fmt_num(amount)}</code>\n"
                f"{PE('target','🎯')} <a href=\"tg://user?id={to_uid}\">{h(to_name)}</a>",
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"transfer: {e}")

    # ═══════════ BATTLE PANEL ═══════════
    async def _show_battle_panel(self, chat_id, uid, reply_to=None, edit_msg=None):
        try:
            u = self.get_unicorn(uid)
            if not u:
                await self._safe_send(chat_id,
                    f"{PE('cross','❌')} اول <code>نیه</code> بزن.", parse_mode="html")
                return
            p = self.compute_power(uid)
            w = WEAPONS.get(p["weapon_key"], ("—", "❓", 0, 0, 0))
            pts = u.get("points", 0)

            text = (
                f"⚔️ <b>دوئل استراتژیک</b>\n"
                f"{DIV}\n"
                f"💪 قدرت: <code>{fmt_full(p['total'])}</code>\n"
                f"{w[1]} {w[0]}\n"
                f"🛡️ {p['soldier_count']}  ·  👑 {p['heroes_count']}\n"
                f"💎 <code>{fmt_full(pts)}</code>\n"
                f"{DIV2}\n"
                f"🥊 جایزه هر برد: <code>50K-100K</code>\n"
                f"⚔️ برای دوئل: ریپلای + <code>دوئل</code>"
            )
            btns = [
                [Button.inline("🔫 سلاح", data=f"uni:wep:0:{uid}".encode()),
                 Button.inline("👑 قهرمان", data=f"uni:hero:0:{uid}".encode())],
                [Button.inline("🛡️ ارتش", data=f"uni:army:{uid}".encode()),
                 Button.inline("📊 آمار", data=f"uni:bstats:{uid}".encode())],
                [Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())],
            ]
            if edit_msg:
                await self._safe_edit_msg(chat_id, edit_msg, text, buttons=btns)
            else:
                kwargs = {"parse_mode": "html", "buttons": btns}
                if reply_to: kwargs["reply_to"] = reply_to
                await self._safe_send(chat_id, text, **kwargs)
        except Exception as e:
            logger.exception(f"battle panel: {e}")

    async def _show_armory_weapons(self, event, uid, tier=0):
        try:
            tier = max(0, min(8, tier))
            u = self.get_unicorn(uid)
            pts = u.get("points", 0) if u else 0
            owned = self.get_weapons(uid)
            army = self.get_army(uid)
            active = army.get("active_weapon") or "club_stone"

            te, tn = WEAPON_TIERS[tier]
            tier_weapons = [(k, w) for k, w in WEAPONS.items() if w[2] == tier]

            lines = [
                f"🔫 <b>زرادخانه</b>",
                f"{DIV}",
                f"{te} <b>{tn}</b>",
                f"💎 <code>{fmt_full(pts)}</code>",
                f"{DIV2}",
            ]
            btns = []
            for key, (name, emoji, t, power, cost) in tier_weapons:
                if key == active:
                    lines.append(f"🎯 {emoji} <b>{name}</b> · 💥{fmt_full(power)}")
                    btns.append([Button.inline(f"🎯 {emoji} {name}",
                        data=b"uni:noop")])
                elif key in owned:
                    lines.append(f"✅ {emoji} <b>{name}</b> · 💥{fmt_full(power)}")
                    btns.append([Button.inline(f"⚙️ {emoji} {name}",
                        data=f"uni:wclick:{key}".encode())])
                else:
                    can = pts >= cost
                    mark = "🟢" if can else "🔴"
                    lines.append(f"🔒 {emoji} {name} · 💥{fmt_full(power)} · 💎{fmt_num(cost)}")
                    btns.append([Button.inline(f"{mark} {emoji} {name} · {fmt_num(cost)}",
                        data=f"uni:wclick:{key}".encode())])

            nav = []
            if tier > 0:
                nav.append(Button.inline("⬅️", data=f"uni:wep:{tier-1}:{uid}".encode()))
            nav.append(Button.inline(f"{tier}/8", data=b"uni:noop"))
            if tier < 8:
                nav.append(Button.inline("➡️", data=f"uni:wep:{tier+1}:{uid}".encode()))
            btns.append(nav)
            btns.append([Button.inline("🔙 بازگشت", data=f"uni:armory:{uid}".encode())])

            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"armory weap: {e}")

    async def _show_armory_heroes(self, event, uid, page=0):
        try:
            u = self.get_unicorn(uid)
            pts = u.get("points", 0) if u else 0
            owned = self.get_heroes(uid)

            hero_list = list(HEROES.items())
            per_page = 4
            total_pages = (len(hero_list) + per_page - 1) // per_page
            page = max(0, min(total_pages - 1, page))
            start = page * per_page
            page_heroes = hero_list[start:start + per_page]

            lines = [
                f"👑 <b>قهرمانان</b>",
                f"{DIV}",
                f"💎 <code>{fmt_full(pts)}</code>  ·  👥 {len(owned)}",
                f"{DIV2}",
            ]
            btns = []
            for key, (name, emoji, power, cost) in page_heroes:
                if key in owned:
                    lines.append(f"✅ {emoji} <b>{name}</b> · 💪{fmt_full(power)}")
                    btns.append([Button.inline(f"✅ {emoji} {name}",
                        data=b"uni:noop")])
                else:
                    can = pts >= cost
                    mark = "🟢" if can else "🔴"
                    lines.append(f"🔒 {emoji} {name} · 💪{fmt_full(power)} · 💎{fmt_num(cost)}")
                    btns.append([Button.inline(f"{mark} {emoji} {name} · {fmt_num(cost)}",
                        data=f"uni:hclick:{key}".encode())])

            nav = []
            if page > 0:
                nav.append(Button.inline("⬅️", data=f"uni:hero:{page-1}:{uid}".encode()))
            nav.append(Button.inline(f"{page+1}/{total_pages}", data=b"uni:noop"))
            if page < total_pages - 1:
                nav.append(Button.inline("➡️", data=f"uni:hero:{page+1}:{uid}".encode()))
            btns.append(nav)
            btns.append([Button.inline("🔙 بازگشت", data=f"uni:armory:{uid}".encode())])

            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"armory hero: {e}")

    async def _show_armory_army(self, event, uid):
        try:
            army = self.get_army(uid)
            p = self.compute_power(uid)
            u = self.get_unicorn(uid)
            pts = u.get("points", 0) if u else 0
            w = WEAPONS.get(army.get("active_weapon"), ("?", "?", 0, 0, 0))

            text = (
                f"🛡️ <b>ارتش</b>\n"
                f"{DIV}\n"
                f"👥 سرباز: <code>{p['soldier_count']}</code>\n"
                f"{w[1]} {w[0]}\n"
                f"💥 قدرت هر سرباز: <code>{fmt_full(p['weapon_power'] + SOLDIER_BASE_POWER)}</code>\n"
                f"⚡ قدرت ارتش: <code>{fmt_full(p['soldier_power'])}</code>\n"
                f"{DIV2}\n"
                f"💎 <code>{fmt_full(pts)}</code>\n"
                f"💵 هر سرباز: <code>{fmt_full(SOLDIER_COST_BASE)}</code>"
            )
            btns = [
                [Button.inline("+1", data=b"uni:train:1"),
                 Button.inline("+10", data=b"uni:train:10"),
                 Button.inline("+100", data=b"uni:train:100")],
                [Button.inline("🔙 بازگشت", data=f"uni:armory:{uid}".encode())],
            ]
            await self._safe_edit_msg(event.chat_id, event.message_id, text, buttons=btns)
        except Exception as e:
            logger.exception(f"armory army: {e}")

    async def _show_armory_stats(self, event, uid):
        try:
            p = self.compute_power(uid)
            w = WEAPONS.get(p["weapon_key"], ("?", "?", 0, 0, 0))
            heroes = self.get_heroes(uid)
            weapons = self.get_weapons(uid)

            hero_lines = []
            for hk in heroes:
                if hk in HEROES:
                    name, emoji, power, cost = HEROES[hk]
                    hero_lines.append(f"   {emoji} {name} · {fmt_full(power)}")
            if not hero_lines:
                hero_lines.append("   <i>قهرمانی نداری</i>")

            text = (
                f"📊 <b>آمار رزمی</b>\n"
                f"{DIV}\n"
                f"⚔️ قدرت کل: <code>{fmt_full(p['total'])}</code>\n"
                f"{DIV2}\n"
                f"🔫 {w[1]} {w[0]}\n"
                f"   💥 {fmt_full(p['weapon_power'] + SOLDIER_BASE_POWER)} هر سرباز\n"
                f"{DIV2}\n"
                f"🛡️ سرباز: <code>{p['soldier_count']}</code> · قدرت: <code>{fmt_full(p['soldier_power'])}</code>\n"
                f"👑 قهرمان: <code>{len(heroes)}</code> · قدرت: <code>{fmt_full(p['hero_power'])}</code>\n"
                f"{DIV2}\n"
                f"👑 <b>قهرمانان:</b>\n" + "\n".join(hero_lines) + "\n"
                f"{DIV2}\n"
                f"🎒 سلاح‌ها: <code>{len(weapons)}/{len(WEAPONS)}</code>"
            )
            btns = [[Button.inline("🔙 بازگشت", data=f"uni:armory:{uid}".encode())]]
            await self._safe_edit_msg(event.chat_id, event.message_id, text, buttons=btns)
        except Exception as e:
            logger.exception(f"armory stats: {e}")

    async def _weapon_click(self, event, uid, key):
        try:
            if key not in WEAPONS:
                await self._safe_answer(event, "نامعتبر", alert=True); return
            w = WEAPONS[key]
            if self.has_weapon(uid, key):
                self.equip_weapon(uid, key)
                await self._safe_answer(event, f"✅ {w[1]} {w[0]} فعال شد")
            else:
                ok, msg = self.buy_weapon(uid, key)
                if ok:
                    self.equip_weapon(uid, key)
                    await self._safe_answer(event, f"🎉 {w[1]} {w[0]}")
                else:
                    await self._safe_answer(event, f"❌ {msg}", alert=True)
                    return
            army = self.get_army(uid)
            active = army.get("active_weapon") or "club_stone"
            tier = WEAPONS.get(active, (None, None, 0))[2]
            await self._show_armory_weapons(event, uid, tier)
        except Exception as e:
            logger.exception(f"weapon click: {e}")

    async def _hero_click(self, event, uid, key):
        try:
            if key not in HEROES:
                await self._safe_answer(event, "نامعتبر", alert=True); return
            hd = HEROES[key]
            ok, msg = self.buy_hero(uid, key)
            if ok:
                await self._safe_answer(event, f"🎉 {hd[1]} {hd[0]}")
            else:
                await self._safe_answer(event, f"❌ {msg}", alert=True)
                return
            hero_keys = list(HEROES.keys())
            idx = hero_keys.index(key)
            page = idx // 4
            await self._show_armory_heroes(event, uid, page)
        except Exception as e:
            logger.exception(f"hero click: {e}")

    # ═══════════ BATTLE ═══════════
    async def _handle_battle(self, event, uid):
        try:
            rm = await event.get_reply_message()
            if not rm:
                await self._show_battle_panel(event.chat_id, uid, reply_to=event.id)
                return
            target = rm.sender_id
            if target == uid:
                await self._safe_send(event.chat_id, f"{PE('cross','❌')} با خودت!",
                    parse_mode="html", reply_to=event.id); return
            try:
                ent = await self.client.get_entity(target); tname = user_name(ent)
            except Exception: tname = str(target)
            self.get_or_create(target, tname)
            a = self.get_unicorn(uid); b = self.get_unicorn(target)
            if a.get("angry") or b.get("angry"):
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} یه یونیکورن قهره! اول غذا بدین.",
                    parse_mode="html", reply_to=event.id); return

            pa = self.compute_power(uid)
            pb = self.compute_power(target)

            if pa["total"] == 0 and pb["total"] == 0:
                await self._safe_send(event.chat_id,
                    f"{PE('warning','⚠️')} هیچکدوم ارتشی ندارید!",
                    parse_mode="html", reply_to=event.id); return
            if pa["total"] == 0:
                await self._safe_send(event.chat_id,
                    f"{PE('warning','⚠️')} تو ارتشی نداری!",
                    parse_mode="html", reply_to=event.id); return
            if pb["total"] == 0:
                await self._safe_send(event.chat_id,
                    f"{PE('warning','⚠️')} حریف ارتشی نداره!",
                    parse_mode="html", reply_to=event.id); return

            va = 1 + random.uniform(-BATTLE_VARIANCE, BATTLE_VARIANCE)
            vb = 1 + random.uniform(-BATTLE_VARIANCE, BATTLE_VARIANCE)
            pow_a = pa["total"] * va
            pow_b = pb["total"] * vb

            a_name = h(a.get("name") or "—"); b_name = h(b.get("name") or "—")

            if pow_a >= pow_b:
                winner, loser = a, b
                winner_uid, loser_uid = uid, target
            else:
                winner, loser = b, a
                winner_uid, loser_uid = target, uid

            reward = random.randint(BATTLE_REWARD_MIN, BATTLE_REWARD_MAX)
            self.update(winner_uid,
                        points=(winner.get("points") or 0) + reward,
                        total_earned=(winner.get("total_earned") or 0) + reward,
                        battles_won=(winner.get("battles_won") or 0) + 1)
            self.update(loser_uid, battles_lost=(loser.get("battles_lost") or 0) + 1)
            c = self._c()
            c.execute("INSERT INTO unicorn_battles (winner_id,loser_id,amount,at) VALUES (%s,%s,%s,%s)",
                      (winner_uid, loser_uid, reward, now_ts()))
            self.check_achievements(winner_uid); self.check_achievements(loser_uid)

            anim = " ".join(random.sample(BATTLE_ANIM, 3))
            cry = random.choice(BATTLE_WORDS)

            wa = WEAPONS.get(pa["weapon_key"], ("?", "❓", 0, 0, 0))
            wb = WEAPONS.get(pb["weapon_key"], ("?", "❓", 0, 0, 0))

            await self._safe_send(event.chat_id,
                f"        {anim}\n"
                f"    🥊 {PE('fire','🔥')} <b>نَـبـرد!</b> {PE('fire','🔥')} 🥊\n"
                f"        {anim}\n"
                f"{DIV}\n"
                f"🦄 <a href=\"tg://user?id={uid}\">{a_name}</a>  ⚔️  "
                f"<a href=\"tg://user?id={target}\">{b_name}</a>\n"
                f"{DIV2}\n"
                f"⚡ {a_name}: <code>{fmt_full(int(pow_a))}</code>\n"
                f"   {wa[1]} {wa[0]} · 🛡️{pa['soldier_count']} · 👑{pa['heroes_count']}\n"
                f"{DIV2}\n"
                f"⚡ {b_name}: <code>{fmt_full(int(pow_b))}</code>\n"
                f"   {wb[1]} {wb[0]} · 🛡️{pb['soldier_count']} · 👑{pb['heroes_count']}\n"
                f"{DIV2}\n"
                f"<i>{cry}</i>\n"
                f"{PE('crown','👑')} <b>{h(winner.get('name') or '—')}</b>\n"
                f"{PE('gift','🎁')} <code>+{fmt_full(reward)}</code>",
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"battle: {e}")

    # ═══════════ MARRY ═══════════
    async def _handle_marry(self, event, uid):
        try:
            rm = await event.get_reply_message()
            if not rm: return
            target = rm.sender_id
            if target == uid:
                await self._safe_send(event.chat_id, f"{PE('cross','❌')} با خودت!",
                    parse_mode="html", reply_to=event.id); return
            try:
                ent = await self.client.get_entity(target); tname = user_name(ent)
            except Exception: tname = str(target)
            self.get_or_create(target, tname)
            a = self.get_unicorn(uid); b = self.get_unicorn(target)

            if a.get("married_to") and a.get("married_to") != 0:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} <b>تو خودت متأهلی!</b>\n"
                    f"اول <code>طلاق</code> بده.",
                    parse_mode="html", reply_to=event.id); return

            if b.get("married_to") and b.get("married_to") != 0:
                spouse_id = b.get("married_to")
                try:
                    sp = await self.client.get_entity(spouse_id)
                    sp_name = user_name(sp)
                except Exception:
                    sp_name = "—"
                await self._safe_send(event.chat_id,
                    f"💔 {PE('warning','⚠️')} <b>این یونیکورن متأهله!</b>\n"
                    f"{DIV}\n"
                    f"{PE('user','👤')} <b>{tname}</b>\n"
                    f"{PE('heart','💖')} <b>همسر:</b> "
                    f"<a href=\"tg://user?id={spouse_id}\">{h(sp_name)}</a>\n\n"
                    f"{PE('info','ℹ️')} <i>نمی‌تونی بهش پیشنهاد بدی!</i>",
                    parse_mode="html", reply_to=event.id); return

            self.update(uid, married_to=target, married_at=now_ts())
            self.update(target, married_to=uid, married_at=now_ts())
            self.check_achievements(uid); self.check_achievements(target)

            await self._safe_send(event.chat_id,
                f"        💐 {PE('sparkle','✨')} 💐\n"
                f"    💍 {PE('party','🎉')} <b>ازدواج!</b> {PE('party','🎉')} 💍\n"
                f"        💐 {PE('sparkle','✨')} 💐\n"
                f"{DIV}\n"
                f"        🌸 <a href=\"tg://user?id={uid}\">{h(a.get('name') or '—')}</a>\n"
                f"              {PE('heart','💖')} {PE('heart','💖')} {PE('heart','💖')}\n"
                f"        🌸 <a href=\"tg://user?id={target}\">{h(b.get('name') or '—')}</a>\n"
                f"{DIV2}\n"
                f"🎉 با <code>تخم</code> بچه بسازید!",
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"marry: {e}")

    # ═══════════ DIVORCE ═══════════
    async def _handle_divorce(self, event, uid):
        try:
            rm = await event.get_reply_message()
            if not rm: return
            target = rm.sender_id
            if target == uid:
                await self._safe_send(event.chat_id, f"{PE('cross','❌')} با خودت!",
                    parse_mode="html", reply_to=event.id); return

            u = self.get_unicorn(uid)
            if not u: return
            spouse = u.get("married_to") or 0
            if not spouse:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} <b>تو متأهل نیستی!</b>",
                    parse_mode="html", reply_to=event.id); return
            if spouse != target:
                await self._safe_send(event.chat_id,
                    f"{PE('warning','⚠️')} <b>این شخص همسرت نیست!</b>",
                    parse_mode="html", reply_to=event.id); return

            try:
                sp = await self.client.get_entity(spouse)
                sp_name = user_name(sp)
            except Exception:
                sp_name = "—"

            eggs = self.count_eggs(uid)
            babies = self.count_babies(uid)

            text = (
                f"        💔 {PE('cross','❌')} 💔\n"
                f"    😭 {PE('warning','⚠️')} <b>مـطـمـئـنـی؟</b>\n"
                f"{DIV}\n"
                f"می‌خوای از <b>{h(sp_name)}</b> جدا بشی؟\n\n"
                f"   🥚 تخم‌ها: <code>{eggs}</code>\n"
                f"   🐣 بیبی‌ها: <code>{babies}</code>\n\n"
                f"{PE('alert','⚠️')} <b>برگشت‌ناپذیره!</b>"
            )
            btns = [
                [Button.inline("💔 آره", data=f"uni:divorce_yes:{uid}:{spouse}".encode()),
                 Button.inline("❤️ نه", data=f"uni:divorce_no:{uid}".encode())],
            ]
            await self._safe_send(event.chat_id, text, buttons=btns,
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"divorce: {e}")

    # ═══════════ BREED ═══════════
    async def _handle_breed(self, event, uid):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            marr = u.get("married_to") or 0
            if not marr:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} <b>اول ازدواج کن!</b>\n"
                    f"ریپلای کن و بنویس <code>ازدواج</code> 💍",
                    parse_mode="html", reply_to=event.id); return

            ts = now_ts()
            mu = self.get_unicorn(marr)
            my_last = self._last_breed_cache.get(uid, 0)
            sp_last = self._last_breed_cache.get(marr, 0)
            last_breed_at = max(my_last, sp_last)
            if ts - last_breed_at < 6 * 3600:
                rem = 6 * 3600 - (ts - last_breed_at)
                cur_eggs = self.count_eggs(uid)
                await self._safe_send(event.chat_id,
                    f"🥚 <b>هنوز آماده نیست!</b>\n"
                    f"{PE('hourglass','⏰')} <code>{fmt_time(rem)}</code>\n"
                    f"{PE('info','ℹ️')} تخم‌های فعلی: <code>{cur_eggs}</code>",
                    parse_mode="html", reply_to=event.id); return

            my_pts = u.get("points") or 0
            sp_pts = (mu.get("points") or 0) if mu else 0
            if my_pts + sp_pts < EGG_COST:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} پول مشترک کمه!\n"
                    f"{PE('gem','💎')} دارید: <code>{fmt_num(my_pts + sp_pts)}</code>\n"
                    f"نیاز: <code>{fmt_num(EGG_COST)}</code>",
                    parse_mode="html", reply_to=event.id); return

            if my_pts >= sp_pts:
                self.update(uid, points=my_pts - EGG_COST)
            else:
                self.update(marr, points=sp_pts - EGG_COST)

            c = self._c()
            c.execute("""INSERT INTO unicorn_eggs
                (user_id, partner_id, laid_at) VALUES (%s, %s, %s)""",
                (uid, marr, ts))
            self._last_breed_cache[uid] = ts
            self._last_breed_cache[marr] = ts
            self.add_achievement(uid, "breeder")
            self.add_achievement(marr, "breeder")

            total_eggs = self.count_eggs(uid)
            await self._safe_send(event.chat_id,
                f"        🥚 {PE('sparkle','✨')} 🥚\n"
                f"    👶 {PE('party','🎉')} <b>تـخـم جـدیـد!</b> {PE('party','🎉')}\n"
                f"{DIV}\n"
                f"🥚 تخم‌های در انتظار: <code>{total_eggs}</code>\n"
                f"{PE('hourglass','⏰')} بعد <b>۶ ساعت</b> هچ می‌شه!",
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"breed: {e}")

    # ═══════════ BABIES UI ═══════════
    async def _show_babies(self, event, uid, edit_msg=None):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            eggs = self.get_eggs(uid)
            babies = self.get_babies(uid)

            lines = [
                f"🏠 {PE('sparkle','✨')} <b>خانواده</b>",
                f"{DIV}", ""
            ]
            if not eggs and not babies:
                lines.append(f"{PE('info','ℹ️')} هنوز بچه‌ای نداری!")
                lines.append(f"با <code>تخم</code> شروع کن.")
            else:
                if eggs:
                    lines.append(f"🥚 <b>در حال هچ ({len(eggs)}):</b>")
                    ts = now_ts()
                    for e in eggs[:5]:
                        laid = e["laid_at"]
                        remain = max(0, EGG_HATCH_SEC - (ts - laid))
                        bar = progress_bar(ts - laid, EGG_HATCH_SEC, 8)
                        if remain <= 0:
                            lines.append(f"   ✨ آماده هچ!")
                        else:
                            lines.append(f"   {bar} <code>{fmt_time(remain)}</code>")
                    lines.append("")
                if babies:
                    income = self.babies_income_per_day(uid)
                    lines.append(f"🐣 <b>بیبی‌ها ({len(babies)}):</b>")
                    lines.append(f"💎 درآمد: <code>{fmt_num(income)}/روز</code>")
                    lines.append(f"{PE('info','ℹ️')} <i>برای تغییر اسم، روی دکمه ✏️ بزن</i>")
                    lines.append(f"🎀 <i>وقتی اسمشون رو صدا بزنی، جواب می‌دن!</i>")
                    lines.append(f"🎀 <i>روی پیامشون ریپلای کن و بپرس مامان/بابات کیه!</i>")
                    lines.append("")
                    for b in babies[:8]:
                        lvl = b.get("level", 1)
                        stars = "⭐" * lvl
                        lines.append(f"   📛 <b>{h(b['name'])}</b>  {stars}  Lv{lvl}")

            btns = []
            if babies:
                for b in babies[:8]:
                    btns.append([Button.inline(
                        f"✏️ تغییر اسم: {b['name'][:18]}",
                        data=f"uni:rename:{b['id']}".encode())])
            if babies:
                btns.append([Button.inline("🐣 رشد", data=f"uni:grow_menu:{uid}".encode())])
            btns.append([Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())])

            text = "\n".join(lines)
            if edit_msg:
                await self._safe_edit_msg(event.chat_id, edit_msg, text, buttons=btns)
            else:
                kwargs = {"parse_mode": "html", "buttons": btns, "reply_to": event.id}
                await self._safe_send(event.chat_id, text, **kwargs)
        except Exception as e:
            logger.exception(f"babies: {e}")

    async def _start_rename(self, event, uid, baby_id):
        try:
            c = self._c()
            c.execute("SELECT * FROM unicorn_babies WHERE id=%s", (baby_id,))
            r = c.fetchone()
            if not r:
                await self._safe_answer(event, "بیبی پیدا نشد!", alert=True); return
            baby = dict(r)
            u = self.get_unicorn(uid)
            if not u:
                await self._safe_answer(event, "یونیکورت پیدا نشد!", alert=True); return
            partner = u.get("married_to") or 0
            owns = (baby["user_id"] == uid or baby["partner_id"] == uid or
                    (partner and (baby["user_id"] == partner or baby["partner_id"] == partner)))
            if not owns:
                await self._safe_answer(event, "⛔ مال تو نیست!", alert=True); return

            self._pending_renames[uid] = {
                "baby_id": baby_id,
                "chat_id": event.chat_id,
                "msg_id": event.message_id,
            }
            await self._safe_answer(event, "✏️ اسم جدید رو بفرست")

            old_name = h(baby.get("name") or "—")
            rows = []
            for i in range(0, len(BABY_NAME_PRESETS), 2):
                pair = BABY_NAME_PRESETS[i:i+2]
                rows.append([Button.inline(p, data=f"uni:setname:{baby_id}:{i+j}".encode())
                             for j, p in enumerate(pair)])
            rows.append([Button.inline("❌ لغو", data=f"uni:cancelrename:{baby_id}".encode())])

            text = (
                f"✏️ {PE('sparkle','✨')} <b>تغییر اسم بیبی</b> {PE('sparkle','✨')}\n"
                f"{DIV}\n\n"
                f"📛 اسم فعلی: <b>{old_name}</b>\n\n"
                f"{PE('info','ℹ️')} یه اسم جدید (بین {BABY_NAME_MIN_LEN} تا {BABY_NAME_MAX_LEN} حرف) بفرست.\n"
                f"{PE('heart','💖')} <i>یا از پیشنهاد‌های زیر انتخاب کن:</i>"
            )
            try:
                await self._safe_send(event.chat_id, text, buttons=rows,
                                      parse_mode="html", reply_to=event.message_id)
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"start rename: {e}")
            await self._safe_answer(event, "خطا!", alert=True)

    async def _apply_rename_from_preset(self, event, uid, baby_id, preset_name):
        try:
            ok, result = self.rename_baby(uid, baby_id, preset_name)
            if ok:
                await self._safe_answer(event, f"✅ اسم شد: {result}")
            else:
                await self._safe_answer(event, f"❌ {result}", alert=True); return
            self._pending_renames.pop(uid, None)
            fake = type("E", (), {"chat_id": event.chat_id,
                                  "id": event.message_id,
                                  "message_id": event.message_id,
                                  "reply_to_msg_id": None})()
            await self._show_babies(fake, uid, edit_msg=event.message_id)
        except Exception as e:
            logger.exception(f"apply preset rename: {e}")
            await self._safe_answer(event, "خطا!", alert=True)

    async def _show_grow_menu(self, event, uid):
        try:
            babies = self.get_babies(uid)
            if not babies:
                await self._safe_answer(event, "بیبی نداری!", alert=True); return

            u = self.get_unicorn(uid)
            pts = u.get("points") or 0
            lines = [
                f"🐣 {PE('star','⭐')} <b>کدوم بیبی؟</b>",
                f"{DIV}",
                f"💎 <code>{fmt_num(pts)}</code>",
                "",
            ]
            btns = []
            for b in babies[:8]:
                lvl = b.get("level", 1)
                if lvl >= BABY_MAX_LEVEL:
                    continue
                cost = BABY_GROW_COST_BASE * lvl
                mark = "🟢" if pts >= cost else "🔴"
                btns.append([Button.inline(
                    f"{mark} {b['name']} Lv{lvl}→{lvl+1} · {fmt_num(cost)}",
                    data=f"uni:grow:{b['id']}".encode())])
            if not btns:
                lines.append(f"{PE('check','✅')} همه مکس لول!")
            btns.append([Button.inline("🔙 بازگشت", data=f"uni:babies:{uid}".encode())])

            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"grow menu: {e}")

    async def _grow_baby(self, event, uid, baby_id):
        try:
            c = self._c()
            c.execute("SELECT * FROM unicorn_babies WHERE id=%s", (baby_id,))
            r = c.fetchone()
            if not r:
                await self._safe_answer(event, "بیبی پیدا نشد!", alert=True); return
            baby = dict(r)
            u = self.get_unicorn(uid)
            if not u: return
            partner = u.get("married_to") or 0
            if baby["user_id"] != uid and baby["user_id"] != partner:
                if baby["partner_id"] != uid and baby["partner_id"] != partner:
                    await self._safe_answer(event, "⛔ مال تو نیست!", alert=True); return

            lvl = baby.get("level", 1)
            if lvl >= BABY_MAX_LEVEL:
                await self._safe_answer(event, "مکس لوله!", alert=True); return
            cost = BABY_GROW_COST_BASE * lvl
            if (u.get("points") or 0) < cost:
                await self._safe_answer(event, f"❌ {fmt_num(cost)} لازمه!",
                                        alert=True); return
            self.update(uid, points=(u.get("points") or 0) - cost)
            c2 = self._c()
            c2.execute("UPDATE unicorn_babies SET level=level+1 WHERE id=%s", (baby_id,))
            await self._safe_answer(event, f"🎉 {baby['name']} Lv{lvl+1}!")
            await self._show_babies(event, uid, edit_msg=event.message_id)
        except Exception as e:
            logger.exception(f"grow: {e}")

    # ═══════════ FULL STATS ═══════════
    async def _show_full_stats(self, chat_id, uid, reply_to=None):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            try:
                self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
            except Exception: pass
            level = max(1, min(10, u.get("level") or 1))
            rate = LEVEL_RATES[level - 1]
            per_hour = rate * 3600
            skin_e, skin_n, _ = SKINS.get(u.get("color") or "classic", SKINS["classic"])
            face = hunger_face(u.get("hunger", 100), u.get("angry", 0))
            try: ach = json.loads(u.get("achievements") or "[]")
            except Exception: ach = []
            eggs = self.count_eggs(uid)
            babies = self.count_babies(uid)
            baby_income = self.babies_income_per_day(uid)

            try:
                p = self.compute_power(uid)
                w_act = WEAPONS.get(p["weapon_key"], ("?",))[0]
                battle_stats = (
                    f"{DIV2}\n"
                    f"⚔️ قدرت کل: <code>{fmt_full(p['total'])}</code>\n"
                    f"🔫 {w_act} · 🛡️{p['soldier_count']} · 👑{p['heroes_count']}\n"
                )
            except Exception:
                battle_stats = ""

            ach_lines = []
            for k, (emoji, name, desc) in ACHIEVEMENTS.items():
                mark = "✅" if k in ach else "🔒"
                ach_lines.append(f"  {mark} {emoji} {name}")

            marry = u.get("married_to") or 0
            if marry:
                try:
                    sp = await self.client.get_entity(marry)
                    sp_n = user_name(sp)
                except Exception:
                    sp_n = "—"
                marry_val = f"<a href=\"tg://user?id={marry}\">{h(sp_n)}</a>"
            else:
                marry_val = "<i>مجرد</i>"

            text = (
                f"📊 <b>آمـار کـامـل</b>\n"
                f"{DIV}\n"
                f"{face} <b>{skin_e} <a href=\"tg://user?id={uid}\">{h(u.get('name') or '—')}</a></b>\n"
                f"{PE('crown','👑')} {LEVEL_NAMES[level-1]}  ·  Lv{level}/10\n"
                f"💎 {skin_n}\n"
                f"{DIV2}\n"
                f"💎 موجودی: <code>{fmt_num(u.get('points', 0))}</code>\n"
                f"🏆 کل درآمد: <code>{fmt_num(u.get('total_earned', 0))}</code>\n"
                f"🎁 در تولید: <code>{fmt_num(int(u.get('pending') or 0))}</code>\n"
                f"⚡ سرعت: <code>{per_hour:.0f}/س</code>\n"
                f"👋 نیه: <code>{u.get('total_neigh_ever', 0)}</code>\n"
                f"🍰 سیری: <code>{u.get('hunger', 100)}%</code>\n"
                f"{DIV2}\n"
                f"🎁 استریک: <code>{u.get('daily_streak', 0)}</code> (رکورد {u.get('daily_best', 0)})\n"
                f"🎰 گردونه: <code>{u.get('spin_count', 0)}</code>\n"
                f"🥊 برد/باخت: <code>{u.get('battles_won', 0)}/{u.get('battles_lost', 0)}</code>\n"
                f"💍 همسر: {marry_val}\n"
                f"🥚 تخم: <code>{eggs}</code>  ·  🐣 بیبی: <code>{babies}</code>\n"
                f"💰 درآمد بیبی: <code>{fmt_num(baby_income)}/روز</code>\n"
                + battle_stats +
                f"{DIV2}\n"
                f"🏆 دستاورد: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>\n"
                + "\n".join(ach_lines)
            )

            if len(text) > 4000:
                chunks = [text[i:i+3500] for i in range(0, len(text), 3500)]
                first = True
                for c in chunks:
                    kwargs = {"parse_mode": "html"}
                    if first and reply_to: kwargs["reply_to"] = reply_to
                    try:
                        await self._safe_send(chat_id, c, **kwargs)
                        await asyncio.sleep(0.4)
                        first = False
                    except Exception: pass
            else:
                kwargs = {"parse_mode": "html"}
                if reply_to: kwargs["reply_to"] = reply_to
                await self._safe_send(chat_id, text, **kwargs)
        except Exception as e:
            logger.exception(f"stats: {e}")

    # ═══════════ HELP ═══════════
    async def _show_help(self, chat_id, reply_to=None, edit_msg=None):
        text = (
            f"🆘 {PE('sparkle','✨')} <b>راهنما</b>\n"
            f"{DIV}\n"
            f"👋 <code>نیه</code> — پاداش (هر ۵ دقیقه)\n"
            f"⭐ <code>یونیکورن</code> — پروفایل\n"
            f"🎁 <code>برداشت</code> · 🍰 <code>غذا</code>\n"
            f"🎉 <code>پاداش</code> · 🎰 <code>گردونه</code>\n"
            f"{DIV2}\n"
            f"⚔️ <code>تنظیمات دوئل</code> — پنل رزمی\n"
            f"🥊 <code>دوئل</code> (ریپلای) — نبرد · 🏆 50K-100K\n"
            f"🛡️ همه ۱ سرباز پیش‌فرض دارن\n"
            f"{DIV2}\n"
            f"💍 <code>ازدواج</code> · 🥚 <code>تخم</code>\n"
            f"🐣 <code>بیبی هام</code> · 💔 <code>طلاق</code>\n"
            f"✏️ <b>تغییر اسم بیبی:</b> از پنل بیبی‌ها، دکمه ✏️\n"
            f"🎀 <b>جواب دادن بیبی:</b> اسمش رو توی گروه بنویس!\n"
            f"🎀 <b>سوال خانوادگی:</b> روی پیام بیبی ریپلای کن و بپرس مامان/بابات کیه! 👶\n"
            f"{DIV2}\n"
            f"🦄 کد <code>UNICORN</code> — ۱۵۰K (یک‌بار!)\n"
            f"{DIV2}\n"
            f"🚀 <code>انتقال یونیکورن 100k</code>\n"
            f"🎨 <code>رنگ</code> · 🏆 <code>دستاورد</code> · 🏅 <code>لیدربورد</code>"
        )
        if edit_msg:
            await self._safe_edit_msg(chat_id, edit_msg, text,
                buttons=[[Button.inline("🔙 بازگشت", data=b"uni:back:0")]])
        else:
            kwargs = {"parse_mode": "html"}
            if reply_to: kwargs["reply_to"] = reply_to
            await self._safe_send(chat_id, text, **kwargs)

    # ═══════════ LEADERBOARD ═══════════
    async def _show_leaderboard(self, chat_id, reply_to=None, edit_msg=None):
        try:
            c = self._c()
            c.execute("""SELECT user_id, name, points, level FROM unicorns
                ORDER BY points DESC LIMIT 10""")
            top = c.fetchall()
        except Exception as e:
            logger.exception(f"top: {e}"); return
        if not top:
            msg = f"{PE('info','ℹ️')} هنوز کسی بازی نکرده!"
            if edit_msg:
                await self._safe_edit_msg(chat_id, edit_msg, msg,
                    buttons=[[Button.inline("🔙", data=b"uni:back:0")]])
            else:
                kwargs = {"parse_mode": "html"}
                if reply_to: kwargs["reply_to"] = reply_to
                await self._safe_send(chat_id, msg, **kwargs)
            return
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = [f"🏅 <b>لیدربورد</b>", DIV, ""]
        for i, r in enumerate(top):
            m = medals[i] if i < len(medals) else "•"
            lines.append(f"{m} <a href=\"tg://user?id={r['user_id']}\">"
                         f"{h(r.get('name') or '—')}</a> — Lv{r.get('level',1)} · "
                         f"<code>{fmt_num(r.get('points', 0))}</code>")
        text = "\n".join(lines)
        if edit_msg:
            await self._safe_edit_msg(chat_id, edit_msg, text,
                buttons=[[Button.inline("🔙 بازگشت", data=b"uni:back:0")]])
        else:
            kwargs = {"parse_mode": "html"}
            if reply_to: kwargs["reply_to"] = reply_to
            await self._safe_send(chat_id, text, **kwargs)

    # ═══════════ CALLBACK ═══════════
    async def on_callback(self, event):
        try:
            data = event.data.decode("utf-8", "ignore")
            if not data.startswith("uni:"): return
            uid = event.sender_id
            parts = data.split(":")
            action = parts[1]

            if action == "noop":
                await self._safe_answer(event); return

            if action == "rename":
                try: baby_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                await self._start_rename(event, uid, baby_id); return

            if action == "setname":
                try:
                    baby_id = int(parts[2])
                    preset_idx = int(parts[3])
                    preset = BABY_NAME_PRESETS[preset_idx]
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                await self._apply_rename_from_preset(event, uid, baby_id, preset); return

            if action == "cancelrename":
                self._pending_renames.pop(uid, None)
                await self._safe_answer(event, "❌ لغو شد")
                try:
                    await event.edit("❌ <b>تغییر اسم لغو شد.</b>",
                                     parse_mode="html", buttons=None)
                except Exception: pass
                return

            if action == "divorce_yes":
                try:
                    target_uid = int(parts[2])
                    spouse_uid = int(parts[3])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                if target_uid != uid:
                    await self._safe_answer(event, "⛔ فقط خودت!", alert=True); return
                await self._do_divorce(event, uid, spouse_uid); return

            if action == "divorce_no":
                await self._safe_answer(event, "❤️ پشیمون شدی، خوبه!")
                try:
                    await event.edit(
                        f"❤️ {PE('heart','💖')} <b>پشیمون شدی!</b>\n"
                        f"{DIV}\n"
                        f"ازدواجتون ادامه داره 💕",
                        parse_mode="html", buttons=None)
                except Exception: pass
                return

            if action == "grow":
                try: bid = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                await self._grow_baby(event, uid, bid); return

            if action == "grow_menu":
                await self._safe_answer(event)
                await self._show_grow_menu(event, uid); return

            if action == "babies":
                await self._safe_answer(event)
                await self._show_babies(event, uid, edit_msg=event.message_id); return

            if action == "armory":
                await self._safe_answer(event)
                await self._show_battle_panel(event.chat_id, uid, edit_msg=event.message_id)
                return
            if action == "wep":
                try: tier = int(parts[2])
                except Exception: tier = 0
                await self._safe_answer(event)
                await self._show_armory_weapons(event, uid, tier); return
            if action == "hero":
                try: page = int(parts[2])
                except Exception: page = 0
                await self._safe_answer(event)
                await self._show_armory_heroes(event, uid, page); return
            if action == "army":
                await self._safe_answer(event)
                await self._show_armory_army(event, uid); return
            if action == "bstats":
                await self._safe_answer(event)
                await self._show_armory_stats(event, uid); return

            if action == "wclick":
                key = parts[2] if len(parts) > 2 else ""
                await self._safe_answer(event)
                await self._weapon_click(event, uid, key); return

            if action == "hclick":
                key = parts[2] if len(parts) > 2 else ""
                await self._safe_answer(event)
                await self._hero_click(event, uid, key); return

            if action == "train":
                try: cnt = int(parts[2])
                except Exception: cnt = 1
                ok, msg = self.train_soldiers(uid, cnt)
                if ok:
                    await self._safe_answer(event, f"✅ {msg}")
                else:
                    await self._safe_answer(event, f"❌ {msg}", alert=True)
                await self._show_armory_army(event, uid)
                return

            if action in ("feed", "withdraw", "daily", "spin", "skins", "ach",
                          "home", "stats", "refresh", "battle", "marry",
                          "breed", "transfer", "help", "top", "divorce"):
                target = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else uid
                if target != uid and target != 0:
                    await self._safe_answer(event, "⛔ مال تو نیست!", alert=True); return

            if action == "refresh":
                await self._safe_answer(event, "🔄")
                u = self.get_unicorn(uid)
                if u:
                    try: self._tick_one(u, now_ts())
                    except Exception: pass
                await self._show_profile(uid, event.chat_id, force_new=False); return

            if action == "feed":
                await self._safe_answer(event, "🍰")
                await self._do_feed(uid, event.chat_id); return

            if action == "withdraw":
                await self._safe_answer(event, "💰")
                await self._do_withdraw(uid, event.chat_id); return

            if action == "daily":
                await self._safe_answer(event, "🎁")
                await self._do_daily(uid, event.chat_id, edit_msg=event.message_id); return

            if action == "spin":
                await self._safe_answer(event, "🎰")
                await self._do_spin(uid, event.chat_id, edit_msg=event.message_id); return

            if action == "skins":
                await self._safe_answer(event)
                await self._show_skins(event, uid); return

            if action == "ach":
                await self._safe_answer(event)
                await self._show_achievements(event, uid); return

            if action == "home":
                await self._safe_answer(event)
                await self._show_home(event, uid); return

            if action == "stats":
                await self._safe_answer(event)
                await self._show_full_stats(event.chat_id, uid, reply_to=event.message_id); return

            if action == "buyskin":
                await self._safe_answer(event)
                await self._buy_skin(event, uid, parts[2]); return

            if action == "back":
                await self._safe_answer(event)
                await self._show_profile(uid, event.chat_id, force_new=False); return

            if action == "battle":
                await self._safe_answer(event, "⚔️")
                await self._show_battle_panel(event.chat_id, uid, edit_msg=event.message_id)
                return

            if action == "marry":
                await self._safe_answer(event, "💍")
                await self._safe_send(event.chat_id,
                    f"💍 <b>ازدواج</b>\n"
                    f"ریپلای + <code>ازدواج</code>",
                    parse_mode="html"); return

            if action == "divorce":
                await self._safe_answer(event, "💔")
                await self._safe_send(event.chat_id,
                    f"💔 <b>طلاق</b>\n"
                    f"ریپلای + <code>طلاق</code>\n"
                    f"{PE('warning','⚠️')} <i>تخم و بیبی‌ها نابود می‌شن!</i>",
                    parse_mode="html"); return

            if action == "breed":
                await self._safe_answer(event, "🥚")
                fake = type("E", (), {"chat_id": event.chat_id, "id": event.message_id,
                                       "reply_to_msg_id": None})()
                await self._handle_breed(fake, uid); return

            if action == "transfer":
                await self._safe_answer(event, "💸")
                await self._safe_send(event.chat_id,
                    f"💸 <b>انتقال</b>\n"
                    f"ریپلای + <code>انتقال یونیکورن 100k</code>",
                    parse_mode="html"); return

            if action == "help":
                await self._safe_answer(event)
                await self._show_help(event.chat_id, edit_msg=event.message_id); return

            if action == "top":
                await self._safe_answer(event)
                await self._show_leaderboard(event.chat_id, edit_msg=event.message_id); return

        except Exception as e:
            logger.exception(f"cb: {e}")
            await self._safe_answer(event, "خطا!", alert=True)

    async def _do_divorce(self, event, uid, spouse_uid):
        try:
            u = self.get_unicorn(uid)
            sp = self.get_unicorn(spouse_uid)
            if not u or not sp:
                await self._safe_answer(event, "خطا", alert=True); return
            if u.get("married_to") != spouse_uid or sp.get("married_to") != uid:
                await self._safe_answer(event, "شما دیگه زوج نیستید!", alert=True); return

            eggs = self.count_eggs(uid)
            babies = self.count_babies(uid)

            self.update(uid, married_to=0, married_at=0)
            self.update(spouse_uid, married_to=0, married_at=0)
            self.delete_couple_eggs_and_babies(uid, spouse_uid)

            try:
                sp_name = sp.get("name") or "—"
            except Exception:
                sp_name = "—"

            text = (
                f"        💔 {PE('cross','❌')} 💔\n"
                f"    😢 <b>جـدا شـدیـد...</b>\n"
                f"{DIV}\n"
                f"<a href=\"tg://user?id={uid}\">شما</a> و "
                f"<a href=\"tg://user?id={spouse_uid}\">{h(sp_name)}</a>\n"
                f"از هم جدا شدید.\n\n"
                f"   🥚 تخم‌ها: <code>{eggs}</code>\n"
                f"   🐣 بیبی‌ها: <code>{babies}</code>"
            )
            try:
                await event.edit(text, parse_mode="html", buttons=None)
            except Exception:
                await self._safe_send(event.chat_id, text, parse_mode="html")
            await self._safe_answer(event, "💔 جدا شدید")
        except Exception as e:
            logger.exception(f"do divorce: {e}")

    # ═══════════ SKINS UI ═══════════
    async def _show_skins(self, event, uid):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            cur = u.get("color") or "classic"
            pts = u.get("points") or 0
            lines = [
                f"💎 <b>رنگ‌ها</b>",
                f"{DIV}",
                f"💎 <code>{fmt_num(pts)}</code>  ·  🎨 {SKINS.get(cur, SKINS['classic'])[1]}",
                f"{DIV2}",
            ]
            for k, (em, name, cost) in SKINS.items():
                if k == cur:
                    lines.append(f"  ✅ {em} <b>{name}</b>")
                elif cost == 0:
                    lines.append(f"  🎨 {em} {name}")
                else:
                    mark = "🟢" if pts >= cost else "🔴"
                    lines.append(f"  {mark} {em} {name} — <code>{fmt_num(cost)}</code>")
            btns, row = [], []
            for k, (em, name, cost) in SKINS.items():
                if k == cur: continue
                row.append(Button.inline(f"{em} {name}", data=f"uni:buyskin:{k}".encode()))
                if len(row) == 2: btns.append(row); row = []
            if row: btns.append(row)
            btns.append([Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())])
            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"skins: {e}")

    async def _buy_skin(self, event, uid, key):
        try:
            if key not in SKINS: return
            u = self.get_unicorn(uid)
            if not u: return
            em, name, cost = SKINS[key]
            if (u.get("points") or 0) < cost:
                await self._safe_answer(event, f"❌ کمه! ({fmt_num(cost)})", alert=True); return
            self.update(uid, points=(u.get("points") or 0) - cost, color=key)
            await self._safe_answer(event, f"✅ {name}!")
            u2 = self.get_unicorn(uid)
            text = self._render_profile(u2, flash=f"✅ {name} {em}")
            await self._safe_edit_msg(event.chat_id, event.message_id, text,
                buttons=self._profile_buttons(uid))
        except Exception as e:
            logger.exception(f"buyskin: {e}")

    async def _show_achievements(self, event, uid):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            try: ach = json.loads(u.get("achievements") or "[]")
            except Exception: ach = []
            lines = [
                f"🏆 <b>دستاوردها</b>",
                f"{DIV}",
                f"✅ <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>",
                f"{DIV2}",
            ]
            for k, (em, name, desc) in ACHIEVEMENTS.items():
                if k in ach: lines.append(f"  ✅ {em} <b>{name}</b>")
                else: lines.append(f"  🔒 {em} <s>{name}</s>")
            btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"ach: {e}")

    async def _show_home(self, event, uid):
        try:
            u = self.get_unicorn(uid)
            if not u: return
            try:
                self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
            except Exception: pass
            level = max(1, min(10, u.get("level") or 1))
            skin_e, skin_n, _ = SKINS.get(u.get("color") or "classic", SKINS["classic"])
            face = hunger_face(u.get("hunger", 100), u.get("angry", 0))
            marr = u.get("married_to") or 0
            eggs = self.count_eggs(uid)
            babies = self.count_babies(uid)
            try: ach = json.loads(u.get("achievements") or "[]")
            except Exception: ach = []
            decorations = "🌷🌻🌷" if level < 3 else "🌹🌸🌺" if level < 6 else "🌌✨🌟"
            lines = [
                f"🏠 {PE('sparkle','✨')} <b>خانه</b>",
                f"{DIV}",
                f"     {decorations}",
                f"     {skin_e} {face}",
                f"     {decorations}",
                f"{DIV2}",
                f"{PE('crown','👑')} {LEVEL_NAMES[level-1]}",
                f"💎 {skin_n}  ·  🍰 {u.get('hunger', 100)}%",
                f"👋 نیه: <b>{u.get('neigh_count', 0)}</b>",
            ]
            if marr:
                try:
                    sp = await self.client.get_entity(marr)
                    sp_n = user_name(sp)
                except Exception: sp_n = "—"
                lines.append(f"💖 همسر: <a href=\"tg://user?id={marr}\">{h(sp_n)}</a>")
            else:
                lines.append(f"💖 مجرد")
            lines.append(f"🥚 {eggs}  ·  🐣 {babies}  ·  🏆 {len(ach)}/{len(ACHIEVEMENTS)}")
            btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"home: {e}")


# ═══════════════════════════════════════════════════════════
_game = None


def init_unicorn(client, db, groq_key="", ai_models=None):
    global _game
    _game = UnicornGame(client, db, groq_key=groq_key, ai_models=ai_models)
    _game.setup()
    _game.register_handlers()
    _game.start_ticker()
    logger.info("🦄 Unicorn module initialized (v13 — baby call + family reply)!")
    return _game