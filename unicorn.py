# -*- coding: utf-8 -*-
"""
🦄 UNICORN PET GAME — Royal Edition v8
💔 Divorce · 🥚 6h Hatch · 🐣 Babies · 💰 Passive income
"""

import re, random, asyncio, logging, time, json
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
}

_TG_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="\d+">([^<]*)</tg-emoji>')


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
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)


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


# ═══════════════════════════════════════════════════════════
# GAME
# ═══════════════════════════════════════════════════════════
class UnicornGame:
    def __init__(self, client, db):
        self.client = client
        self.db = db
        self.conn = db.conn
        self._running = False
        self._combo = {}
        self._last_breed_cache = {}

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
            last_profile_chat BIGINT DEFAULT 0, total_neigh_ever INTEGER DEFAULT 0
        )""")
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
        c.execute("""CREATE INDEX IF NOT EXISTS idx_uni_points ON unicorns(points DESC)""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_eggs_lookup ON unicorn_eggs(user_id, partner_id, hatched_at)""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_babies_lookup ON unicorn_babies(user_id, partner_id)""")
        logger.info("🦄 Unicorn tables ready")

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
        """🥚 تخم‌های آماده رو به بیبی تبدیل کن"""
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
        # اسم کیوت رندوم
        name = random.choice(BABY_NAMES)
        c = self._c()
        c.execute("""INSERT INTO unicorn_babies
            (user_id, partner_id, name, level, born_at, last_income)
            VALUES (%s, %s, %s, 1, %s, %s) RETURNING id""",
            (user_id, partner_id, name, ts, ts))
        baby_id = c.fetchone()["id"]
        c.execute("""UPDATE unicorn_eggs SET hatched_at=%s, baby_id=%s WHERE id=%s""",
                  (ts, baby_id, egg_id))
        # دستاورد
        for u in (user_id, partner_id):
            if u and u != 0:
                self.add_achievement(u, "first_baby")
                if self.count_babies(u) >= 5:
                    self.add_achievement(u, "baby_master")

    def _babies_income(self):
        """💰 بیبی‌ها پوینت پسیو تولید می‌کنن"""
        ts = now_ts()
        c = self._c()
        c.execute("""SELECT * FROM unicorn_babies WHERE last_income IS NOT NULL""")
        for b in c.fetchall():
            baby = dict(b)
            last = baby.get("last_income") or baby.get("born_at") or ts
            elapsed = ts - last
            if elapsed < 60:
                continue  # هر ۶۰ ثانیه یه بار
            rate_per_sec = (baby.get("level", 1) * BABY_INCOME_PER_LEVEL_PER_DAY) / 86400
            income = elapsed * rate_per_sec
            # اضافه به پوینت هر دو طرف اگه نی‌قهر نباشن
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

            try:
                s = await event.get_sender()
                name = user_name(s)
            except Exception:
                name = str(uid)
            self.get_or_create(uid, name)

            # ─── انتقال ───
            if event.reply_to_msg_id and "انتقال" in norm_raw and "یونیکورن" in norm_raw:
                await self._handle_transfer(event, uid, norm_raw); return

            # ─── طلاق ───
            if low in ("طلاق", "جدا", "جدا شو", "divorce"):
                if not event.reply_to_msg_id:
                    await self._divorce_hint(event); return
                await self._handle_divorce(event, uid); return

            # ─── دوئل ───
            if low in ("دویل", "دوئل", "نبرد", "مبارزه", "جنگ", "بجنگ"):
                if not event.reply_to_msg_id:
                    await self._battle_hint(event); return
                await self._handle_battle(event, uid); return

            # ─── ازدواج ───
            if low in ("ازدواج", "ازدواج کن", "بگیر"):
                if not event.reply_to_msg_id:
                    await self._marry_hint(event); return
                await self._handle_marry(event, uid); return

            # ─── تخم ───
            if low in ("تخم", "پرورش", "جوجه"):
                await self._handle_breed(event, uid); return

            # ─── بیبی ها ───
            if low in ("بیبی هام", "بچه هام", "بچه‌هام", "بیبی", "بیبی‌ها",
                       "فرزندام", "فرزندهام", "بچه ها"):
                await self._show_babies(event, uid); return

            # ─── نیه ───
            if low in ("نیه", "نیییه", "نههه", "neigh"):
                await self._handle_neigh(event, uid); return

            # ─── برداشت ───
            if low in ("برداشت", "برداشت کن", "جمع", "جمع کن", "collect"):
                await self._do_withdraw(uid, event.chat_id, reply_to=event.id); return

            # ─── غذا ───
            if low in ("غذا", "غذا بده", "feed", "خوراک"):
                await self._do_feed(uid, event.chat_id, reply_to=event.id); return

            # ─── پاداش ───
            if low in ("پاداش", "پاداش روزانه", "daily"):
                await self._do_daily(uid, event.chat_id, reply_to=event.id); return

            # ─── گردونه ───
            if low in ("گردونه", "شانس", "spin"):
                await self._do_spin(uid, event.chat_id, reply_to=event.id); return

            # ─── راهنما ───
            if low in ("راهنما", "کمک", "help", "اموزش", "آموزش"):
                await self._show_help(event.chat_id, reply_to=event.id); return

            # ─── لیدربورد ───
            if low in ("لیدربورد", "برترین", "بهترین", "top", "رتبه"):
                await self._show_leaderboard(event.chat_id, reply_to=event.id); return

            # ─── آمار ───
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

            # ─── پروفایل ───
            if low in ("یونیکورن", "تک شاخ", "یونیکورنم", "شونیکورن", "unicorn", "پروفایل"):
                await self._show_profile(uid, event.chat_id, reply_to=event.id, force_new=True); return
        except Exception as e:
            logger.exception(f"uni msg: {e}")

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

        # eggs & babies
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
        parts.append(line6 + family_line)
        parts.append(DIV2)
        parts.append(lvl_block)
        return "\n".join(parts)

    def _profile_buttons(self, uid):
        return [
            [Button.inline("🍰 غذا", data=f"uni:feed:{uid}".encode()),
             Button.inline("💰 برداشت", data=f"uni:withdraw:{uid}".encode())],
            [Button.inline("🎁 روزانه", data=f"uni:daily:{uid}".encode()),
             Button.inline("🎰 گردونه", data=f"uni:spin:{uid}".encode())],
            [Button.inline("🎨 رنگ‌ها", data=f"uni:skins:{uid}".encode()),
             Button.inline("🏆 دستاوردها", data=f"uni:ach:{uid}".encode())],
            [Button.inline("🥊 دوئل", data=f"uni:battle:{uid}".encode()),
             Button.inline("💍 ازدواج", data=f"uni:marry:{uid}".encode())],
            [Button.inline("🥚 تخم", data=f"uni:breed:{uid}".encode()),
             Button.inline("🐣 بیبی‌ها", data=f"uni:babies:{uid}".encode())],
            [Button.inline("💔 طلاق", data=f"uni:divorce:{uid}".encode()),
             Button.inline("💸 انتقال", data=f"uni:transfer:{uid}".encode())],
            [Button.inline("🏠 خانه", data=f"uni:home:{uid}".encode()),
             Button.inline("🏅 لیدربورد", data=f"uni:top:{uid}".encode())],
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
                # تخم جدید در جدول
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
    async def _battle_hint(self, event):
        await self._safe_send(event.chat_id,
            f"🥊 {PE('fire','🔥')} <b>دوئل</b>\n"
            f"{DIV}\n"
            f"روی پیام حریف <b>ریپلای</b> کن و بنویس <code>دوئل</code>\n"
            f"{PE('gift','🎁')} جایزه <code>1000-10000</code>",
            parse_mode="html", reply_to=event.id)

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

    # ═══════════ BATTLE ═══════════
    async def _handle_battle(self, event, uid):
        try:
            rm = await event.get_reply_message()
            if not rm: return
            target = rm.sender_id
            if target == uid:
                await self._safe_send(event.chat_id, f"{PE('cross','❌')} با خودت!",
                    parse_mode="html", reply_to=event.id); return
            try:
                ts = await self.client.get_entity(target); tname = user_name(ts)
            except Exception: tname = str(target)
            self.get_or_create(target, tname)
            a = self.get_unicorn(uid); b = self.get_unicorn(target)
            if a.get("angry") or b.get("angry"):
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} یه یونیکورن قهره! اول غذا بدین.",
                    parse_mode="html", reply_to=event.id); return
            a_pow = ((a.get("level") or 1) * 100 + (a.get("neigh_count") or 0) +
                     (a.get("battles_won") or 0) * 20 + random.randint(0, 200))
            b_pow = ((b.get("level") or 1) * 100 + (b.get("neigh_count") or 0) +
                     (b.get("battles_won") or 0) * 20 + random.randint(0, 200))
            a_name = h(a.get("name") or "—"); b_name = h(b.get("name") or "—")
            if a_pow >= b_pow:
                winner, loser = a, b; winner_uid, loser_uid = uid, target
            else:
                winner, loser = b, a; winner_uid, loser_uid = target, uid
            reward = min(1000 + (winner.get("level") or 1) * 300, 10000)
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
            await self._safe_send(event.chat_id,
                f"        {anim}\n"
                f"    🥊 {PE('fire','🔥')} <b>نَـبـرد!</b> {PE('fire','🔥')} 🥊\n"
                f"        {anim}\n"
                f"{DIV}\n"
                f"🦄 <a href=\"tg://user?id={uid}\">{a_name}</a>  ⚔️  "
                f"<a href=\"tg://user?id={target}\">{b_name}</a>\n"
                f"{DIV2}\n"
                f"⚡ {a_name}: <code>{a_pow}</code>\n"
                f"⚡ {b_name}: <code>{b_pow}</code>\n"
                f"{DIV2}\n"
                f"<i>{cry}</i>\n"
                f"{PE('crown','👑')} <b>{h(winner.get('name') or '—')}</b>\n"
                f"{PE('gift','🎁')} <code>+{fmt_num(reward)}</code>",
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
                ts = await self.client.get_entity(target); tname = user_name(ts)
            except Exception: tname = str(target)
            self.get_or_create(target, tname)
            a = self.get_unicorn(uid); b = self.get_unicorn(target)

            # 🚫 چک متاهل بودن هر دو
            if a.get("married_to") and a.get("married_to") != 0:
                await self._safe_send(event.chat_id,
                    f"{PE('cross','❌')} <b>تو خودت متأهلی!</b>\n"
                    f"{DIV}\n"
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
                    f"<a href=\"tg://user?id={spouse_id}\">{h(sp_name)}</a>\n"
                    f"{PE('id','🆔')} <code>{spouse_id}</code>\n\n"
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
                f"🎉 با <code>تخم</code> بچه بسازید!\n"
                f"{PE('info','ℹ️')} <i>تخم و بیبی مشترکه!</i>",
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
                    f"{PE('warning','⚠️')} <b>این شخص همسرت نیست!</b>\n"
                    f"{PE('info','ℹ️')} روی پیام همسرت ریپلای کن.",
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
                f"می‌خوای از <b>{h(sp_name)}</b> جدا بشی؟\n"
                f"{PE('heart','💔')} <i>با این کار همه چیز از بین می‌ره:</i>\n\n"
                f"   🥚 تخم‌ها: <code>{eggs}</code>\n"
                f"   🐣 بیبی‌ها: <code>{babies}</code>\n\n"
                f"{DIV2}\n"
                f"{PE('alert','⚠️')} <b>این کار برگشت‌ناپذیره!</b>"
            )
            btns = [
                [Button.inline("💔 آره جدا شو", data=f"uni:divorce_yes:{uid}:{spouse}".encode())],
                [Button.inline("❤️ نه، پشیمون شدم", data=f"uni:divorce_no:{uid}".encode())],
            ]
            await self._safe_send(event.chat_id, text, buttons=btns,
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"divorce: {e}")

    # ═══════════ BREED (تخم‌گذاری) ═══════════
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
                f"🌸 یه تخم کیوت گذاشتی!\n"
                f"🥚 تخم‌های در انتظار: <code>{total_eggs}</code>\n"
                f"{PE('hourglass','⏰')} بعد <b>۶ ساعت</b> هچ می‌شه!\n"
                f"{PE('heart','💖')} <i>همسرت هم شریکه</i>",
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
                f"🏠 {PE('sparkle','✨')} <b>خانواده‌ی یونیکورن</b> {PE('sparkle','✨')}",
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
                    lines.append(f"{PE('gem','💎')} درآمد روزانه: <code>{fmt_num(income)}</code>")
                    lines.append("")
                    for b in babies[:10]:
                        lvl = b.get("level", 1)
                        stars = "⭐" * lvl
                        lines.append(f"   {b['name']}  {stars}")
                        lines.append(f"      Lv{lvl} · {fmt_num(lvl*BABY_INCOME_PER_LEVEL_PER_DAY)}/روز")

            btns = []
            if babies:
                btns.append([Button.inline("🐣 رشد یه بیبی", data=f"uni:grow_menu:{uid}".encode())])
            btns.append([Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())])

            text = "\n".join(lines)
            if edit_msg:
                await self._safe_edit_msg(event.chat_id, edit_msg, text, buttons=btns)
            else:
                kwargs = {"parse_mode": "html", "buttons": btns, "reply_to": event.id}
                await self._safe_send(event.chat_id, text, **kwargs)
        except Exception as e:
            logger.exception(f"babies: {e}")

    async def _show_grow_menu(self, event, uid):
        try:
            babies = self.get_babies(uid)
            if not babies:
                await self._safe_answer(event, "بیبی نداری!", alert=True); return

            u = self.get_unicorn(uid)
            pts = u.get("points") or 0
            lines = [
                f"🐣 {PE('star','⭐')} <b>کدوم بیبی رو بزرگ کنم؟</b>",
                f"{DIV}",
                f"{PE('gem','💎')} موجودی تو: <code>{fmt_num(pts)}</code>",
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
                    f"{b['name']} Lv{lvl}→{lvl+1} · {fmt_num(cost)}",
                    data=f"uni:grow:{b['id']}".encode())])
            if not btns:
                lines.append(f"{PE('check','✅')} همه بیبی‌ها مکس لول!")
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
            # چک مالکیت
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
                await self._safe_answer(event, f"❌ {fmt_num(cost)} پوینت لازمه!",
                                        alert=True); return
            self.update(uid, points=(u.get("points") or 0) - cost)
            c2 = self._c()
            c2.execute("UPDATE unicorn_babies SET level=level+1 WHERE id=%s", (baby_id,))
            await self._safe_answer(event, f"🎉 {baby['name']} لول {lvl+1} شد!")
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
            per_day = per_hour * 24
            skin_e, skin_n, _ = SKINS.get(u.get("color") or "classic", SKINS["classic"])
            face = hunger_face(u.get("hunger", 100), u.get("angry", 0))
            try: ach = json.loads(u.get("achievements") or "[]")
            except Exception: ach = []
            eggs = self.count_eggs(uid)
            babies = self.count_babies(uid)
            baby_income = self.babies_income_per_day(uid)

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
                f"{PE('chart','📊')} <b>آمـار کـامـل</b>\n"
                f"{DIV}\n"
                f"{face} <b>{skin_e} <a href=\"tg://user?id={uid}\">{h(u.get('name') or '—')}</a></b>\n"
                f"{PE('crown','👑')} {LEVEL_NAMES[level-1]}  ·  Lv{level}/10\n"
                f"{PE('diamond','💎')} {skin_n}\n"
                f"{DIV2}\n"
                f"{PE('gem','💎')} موجودی: <code>{fmt_num(u.get('points', 0))}</code>\n"
                f"{PE('trophy','🏆')} کل درآمد: <code>{fmt_num(u.get('total_earned', 0))}</code>\n"
                f"{PE('gift','🎁')} در تولید: <code>{fmt_num(int(u.get('pending') or 0))}</code>\n"
                f"{PE('bolt','⚡')} سرعت: <code>{per_hour:.0f}/س</code> ≈ "
                f"<code>{fmt_num(per_day)}/روز</code>\n"
                f"{PE('wave','👋')} نیه: <code>{u.get('total_neigh_ever', 0)}</code>\n"
                f"🍰 سیری: <code>{u.get('hunger', 100)}%</code>  ·  "
                f"🍽 غذا: <code>{u.get('total_fed', 0)}</code>\n"
                f"{DIV2}\n"
                f"🎁 استریک: <code>{u.get('daily_streak', 0)}</code> "
                f"(رکورد {u.get('daily_best', 0)})\n"
                f"🎰 گردونه: <code>{u.get('spin_count', 0)}</code>\n"
                f"🥊 برد/باخت: <code>{u.get('battles_won', 0)}/{u.get('battles_lost', 0)}</code>\n"
                f"💍 همسر: {marry_val}\n"
                f"🥚 تخم: <code>{eggs}</code>  ·  🐣 بیبی: <code>{babies}</code>\n"
                f"💰 درآمد بیبی‌ها: <code>{fmt_num(baby_income)}/روز</code>\n"
                f"🏆 دستاورد: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>\n"
                f"{DIV2}\n"
                f"{PE('trophy','🏆')} <b>دستاوردها:</b>\n" + "\n".join(ach_lines) + "\n\n"
                f"{PE('sparkle','✨')} <i>ادامه بده تا افسانه‌ای بشی!</i>"
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
            f"🆘 {PE('sparkle','✨')} <b>راهنما</b> {PE('sparkle','✨')}\n"
            f"{DIV}\n"
            f"{PE('brain','🧠')} <b>دستورات اصلی:</b>\n"
            f"  {PE('wave','👋')} <code>نیه</code> — پاداش (هر ۵ دقیقه)\n"
            f"  {PE('star','⭐')} <code>یونیکورن</code> — پروفایل\n"
            f"  {PE('gift','🎁')} <code>برداشت</code> — پوینت تولیدی\n"
            f"  🍰 <code>غذا</code> — سیری (500)\n"
            f"  {PE('party','🎉')} <code>پاداش</code> · 🎰 <code>گردونه</code>\n"
            f"{DIV2}\n"
            f"{PE('heart','💖')} <b>خانواده:</b>\n"
            f"  💍 <code>ازدواج</code> (ریپلای) — ازدواج\n"
            f"  🥚 <code>تخم</code> — گذاشتن تخم (مشترک)\n"
            f"  🐣 <code>بیبی هام</code> — دیدن بچه‌ها\n"
            f"  💔 <code>طلاق</code> (ریپلای) — جدا شدن\n"
            f"{DIV2}\n"
            f"{PE('fire','🔥')} <b>اجتماعی:</b>\n"
            f"  🥊 <code>دوئل</code> (ریپلای)\n"
            f"  {PE('rocket','🚀')} <code>انتقال یونیکورن 100k</code>\n"
            f"{DIV2}\n"
            f"{PE('diamond','💎')} 🎨 <code>رنگ</code> · 🏆 <code>دستاورد</code> · 🏅 <code>لیدربورد</code>\n"
            f"{DIV2}\n"
            f"{PE('info','ℹ️')} <i>🥚 بعد از ۶ ساعت → 🐣 خودکار</i>\n"
            f"{PE('gem','💎')} <i>بیبی‌ها پسیو پوینت می‌دن!</i>"
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
        lines = [f"🏅 {PE('trophy','🏆')} <b>لیدربورد</b>", DIV, ""]
        for i, r in enumerate(top):
            m = medals[i] if i < len(medals) else "•"
            lines.append(f"{m} <a href=\"tg://user?id={r['user_id']}\">"
                         f"{h(r.get('name') or '—')}</a> — Lv{r.get('level',1)} · "
                         f"{PE('gem','💎')} <code>{fmt_num(r.get('points', 0))}</code>")
        lines.append(f"\n{DIV2}")
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

            # ─── طلاق تایید ───
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

            # ─── رشد بیبی ───
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

            # ─── دکمه‌های عادی ───
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
                await self._safe_answer(event, "🥊")
                await self._safe_send(event.chat_id,
                    f"🥊 {PE('fire','🔥')} <b>دوئل!</b>\n"
                    f"{DIV}\n"
                    f"روی پیام حریف <b>ریپلای</b> کن و بنویس <code>دوئل</code>",
                    parse_mode="html"); return

            if action == "marry":
                await self._safe_answer(event, "💍")
                await self._safe_send(event.chat_id,
                    f"💍 {PE('heart','💖')} <b>ازدواج!</b>\n"
                    f"{DIV}\n"
                    f"روی پیام طرف <b>ریپلای</b> کن و بنویس <code>ازدواج</code>",
                    parse_mode="html"); return

            if action == "divorce":
                await self._safe_answer(event, "💔")
                await self._safe_send(event.chat_id,
                    f"💔 <b>طلاق</b>\n"
                    f"{DIV}\n"
                    f"روی پیام همسرت <b>ریپلای</b> کن و بنویس <code>طلاق</code>\n\n"
                    f"{PE('warning','⚠️')} <i>تخم و بیبی‌ها از بین می‌رن!</i>",
                    parse_mode="html"); return

            if action == "breed":
                await self._safe_answer(event, "🥚")
                fake = type("E", (), {"chat_id": event.chat_id, "id": event.message_id,
                                       "reply_to_msg_id": None})()
                await self._handle_breed(fake, uid); return

            if action == "transfer":
                await self._safe_answer(event, "💸")
                await self._safe_send(event.chat_id,
                    f"💸 {PE('rocket','🚀')} <b>انتقال</b>\n"
                    f"{DIV}\n"
                    f"روی پیام طرف <b>ریپلای</b> کن:\n"
                    f"<code>انتقال یونیکورن 100k</code>",
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
        """طلاق رو انجام بده"""
        try:
            u = self.get_unicorn(uid)
            sp = self.get_unicorn(spouse_uid)
            if not u or not sp:
                await self._safe_answer(event, "خطا", alert=True); return
            if u.get("married_to") != spouse_uid or sp.get("married_to") != uid:
                await self._safe_answer(event, "شما دیگه زوج نیستید!", alert=True); return

            eggs = self.count_eggs(uid)
            babies = self.count_babies(uid)

            # پاک کردن همه چیز
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
                f"{PE('heart','💔')} <a href=\"tg://user?id={uid}\">شما</a> و "
                f"<a href=\"tg://user?id={spouse_uid}\">{h(sp_name)}</a>\n"
                f"از هم جدا شدید.\n\n"
                f"{PE('warning','⚠️')} <b>نابود شد:</b>\n"
                f"   🥚 تخم‌ها: <code>{eggs}</code>\n"
                f"   🐣 بیبی‌ها: <code>{babies}</code>\n\n"
                f"{DIV2}\n"
                f"{PE('sparkle','✨')} <i>امیدواریم دفعه بعد بهتر باشه...</i>"
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
                f"{PE('diamond','💎')} <b>رنگ‌ها</b>",
                f"{DIV}",
                f"{PE('gem','💎')} موجودی: <code>{fmt_num(pts)}</code>",
                f"🎨 فعلی: <code>{SKINS.get(cur, SKINS['classic'])[1]}</code>",
                f"{DIV2}",
            ]
            for k, (em, name, cost) in SKINS.items():
                if k == cur:
                    lines.append(f"  ✅ {em} <b>{name}</b> <i>(فعلی)</i>")
                elif cost == 0:
                    lines.append(f"  🎨 {em} <b>{name}</b> <i>رایگان</i>")
                else:
                    mark = "🟢" if pts >= cost else "🔴"
                    lines.append(f"  {mark} {em} <b>{name}</b> — <code>{fmt_num(cost)}</code>")
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
            await self._safe_answer(event, f"✅ {name} فعال شد!")
            u2 = self.get_unicorn(uid)
            text = self._render_profile(u2, flash=f"✅ اسکین <b>{name}</b> فعال! {em}")
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
                f"{PE('trophy','🏆')} <b>دستاوردها</b>",
                f"{DIV}",
                f"✅ باز شده: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>",
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
                f"🏠 {PE('sparkle','✨')} <b>خـانـه‌ی یـونـیـکـورن</b>",
                f"{DIV}",
                f"     {decorations}",
                f"     {skin_e} {face}",
                f"     {decorations}",
                f"{DIV2}",
                f"{PE('crown','👑')} {LEVEL_NAMES[level-1]}",
                f"{PE('diamond','💎')} {skin_n}  ·  🍰 {u.get('hunger', 100)}%",
                f"{PE('wave','👋')} نیه: <b>{u.get('neigh_count', 0)}</b>",
            ]
            if marr:
                try:
                    sp = await self.client.get_entity(marr)
                    sp_n = user_name(sp)
                except Exception: sp_n = "—"
                lines.append(f"{PE('heart','💖')} همسر: <a href=\"tg://user?id={marr}\">{h(sp_n)}</a>")
            else:
                lines.append(f"{PE('heart','💖')} مجرد")
            lines.append(f"🥚 تخم: <code>{eggs}</code>  ·  🐣 بیبی: <code>{babies}</code>")
            lines.append(f"{PE('trophy','🏆')} دستاورد: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>")
            btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
            await self._safe_edit_msg(event.chat_id, event.message_id,
                "\n".join(lines), buttons=btns)
        except Exception as e:
            logger.exception(f"home: {e}")


# ═══════════════════════════════════════════════════════════
_game = None


def init_unicorn(client, db):
    global _game
    _game = UnicornGame(client, db)
    _game.setup()
    _game.register_handlers()
    _game.start_ticker()
    logger.info("🦄 Unicorn module initialized!")
    return _game