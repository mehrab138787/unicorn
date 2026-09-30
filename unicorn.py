# -*- coding: utf-8 -*-
"""
🦄 UNICORN PET GAME — Advanced Royal Edition
همه چیز زنده، همه چیز کیوت، همه چیز توی یه پیام
"""

import re, random, asyncio, logging, time, json
from datetime import datetime, timezone, timedelta
from telethon import events, Button
from telethon.errors import MessageNotModifiedError

logger = logging.getLogger("UnicornGame")

# ═══════════════════════════════════════════════════════════
# 🦄 CONFIG
# ═══════════════════════════════════════════════════════════
NEIGH_COOLDOWN_SEC = 300
FEED_COST = 500
FEED_HUNGER_BOOST = 25
HUNGER_DECAY_SEC = 300
PENDING_CAP_HOURS = 8
TICK_INTERVAL = 20
NEIGH_REWARD_MIN = 1
NEIGH_REWARD_MAX = 1000

LEVEL_THRESHOLDS  = [0, 15, 30, 45, 60, 80, 100, 125, 155, 200]
LEVEL_POINT_COST  = [0, 1000, 3000, 6000, 10000, 15000, 25000, 40000, 60000, 100000]
LEVEL_RATES       = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

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
    "medal": "5458603043203327669", "gift": "5456359790390093750",
    "warning": "5447644880824181073", "info": "5323442290708985472",
    "user": "5443038326535759644", "id": "5397782960512444700",
    "time": "5458603043203327669", "point": "5436113877181941026",
    "flag": "5447644880824181073", "target": "5424972470023104089",
    "brain": "5404654051945521778", "chart": "5231200819986047254",
    "diamond": "5404654051945521778", "bolt": "5424972470023104089",
    "alert": "5447644880824181073", "lock": "5397782960512444700",
    "eye": "5397782960512444700", "detective": "5424972470023104089",
}


def PE(k, fb):
    eid = PREM.get(k)
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>' if eid else fb


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


def hunger_bar(h):
    h = max(0, min(100, int(h)))
    return "🍰" * (h // 10) + "🖤" * (10 - h // 10)


def progress_bar(cur, total, width=10):
    if total <= 0: return "▰" * width
    p = max(0, min(100, int(100 * cur / total)))
    filled = int(p / 100 * width)
    return "▰" * filled + "▱" * (width - filled)


def next_level_info(level, neigh_count, points):
    if level >= 10: return None
    nxt = level + 1
    return {
        "next": nxt,
        "neigh_need": max(0, LEVEL_THRESHOLDS[nxt - 1] - neigh_count),
        "neigh_total": LEVEL_THRESHOLDS[nxt - 1],
        "neigh_cur": neigh_count,
        "pts_need": max(0, LEVEL_POINT_COST[nxt - 1] - points),
        "pts_total": LEVEL_POINT_COST[nxt - 1],
        "pts_cur": points,
    }


def time_ago(ts):
    if not ts: return "—"
    d = now_ts() - ts
    if d < 60: return f"{d} ثانیه"
    if d < 3600: return f"{d//60} دقیقه"
    if d < 86400: return f"{d//3600} ساعت"
    return f"{d//86400} روز"


# ═══════════════════════════════════════════════════════════
# 🦄 GAME CLASS
# ═══════════════════════════════════════════════════════════
class UnicornGame:
    def __init__(self, client, db):
        self.client = client
        self.db = db
        self.conn = db.conn
        self._running = False

    def _c(self):
        import psycopg2.extras
        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ═══════════════ SETUP ═══════════════
    def setup(self):
        c = self._c()
        c.execute("""CREATE TABLE IF NOT EXISTS unicorns (
            user_id BIGINT PRIMARY KEY,
            name TEXT,
            level INTEGER DEFAULT 1,
            neigh_count INTEGER DEFAULT 0,
            points BIGINT DEFAULT 0,
            pending REAL DEFAULT 0,
            hunger INTEGER DEFAULT 100,
            angry INTEGER DEFAULT 0,
            last_neigh BIGINT DEFAULT 0,
            last_feed BIGINT DEFAULT 0,
            last_produce BIGINT DEFAULT 0,
            last_hunger_tick BIGINT DEFAULT 0,
            created_at BIGINT DEFAULT 0,
            total_earned BIGINT DEFAULT 0,
            total_fed INTEGER DEFAULT 0,
            color TEXT DEFAULT 'classic',
            daily_streak INTEGER DEFAULT 0,
            daily_best INTEGER DEFAULT 0,
            last_daily BIGINT DEFAULT 0,
            last_spin BIGINT DEFAULT 0,
            spin_count INTEGER DEFAULT 0,
            battles_won INTEGER DEFAULT 0,
            battles_lost INTEGER DEFAULT 0,
            married_to BIGINT DEFAULT 0,
            married_at BIGINT DEFAULT 0,
            eggs INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]',
            boost_mult REAL DEFAULT 1.0,
            boost_until BIGINT DEFAULT 0,
            last_profile_msg BIGINT DEFAULT 0,
            last_profile_chat BIGINT DEFAULT 0,
            total_neigh_ever INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS unicorn_transfers (
            id BIGSERIAL PRIMARY KEY, from_id BIGINT, to_id BIGINT,
            amount BIGINT, at BIGINT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS unicorn_battles (
            id BIGSERIAL PRIMARY KEY, winner_id BIGINT, loser_id BIGINT,
            amount BIGINT, at BIGINT)""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_uni_points ON unicorns(points DESC)""")
        logger.info("🦄 Unicorn tables ready")

    def register_handlers(self):
        self.client.add_event_handler(self.on_message, events.NewMessage())
        self.client.add_event_handler(self.on_callback, events.CallbackQuery())
        self._running = True

    def start_ticker(self):
        asyncio.create_task(self._ticker())

    # ═══════════════ DB ═══════════════
    def get_unicorn(self, uid):
        c = self._c()
        c.execute("SELECT * FROM unicorns WHERE user_id=%s", (uid,))
        row = c.fetchone()
        return dict(row) if row else None

    def get_or_create(self, uid, name):
        u = self.get_unicorn(uid)
        if u: return u
        ts = now_ts()
        c = self._c()
        c.execute("""INSERT INTO unicorns
            (user_id, name, created_at, last_neigh, last_feed,
             last_produce, last_hunger_tick, achievements)
            VALUES (%s, %s, %s, 0, %s, %s, %s, '[]')""",
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
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception:
            ach = []
        if key in ach: return False
        ach.append(key)
        self.update(uid, achievements=json.dumps(ach))
        return True

    def has_achievement(self, uid, key):
        u = self.get_unicorn(uid)
        if not u: return False
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception:
            ach = []
        return key in ach

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

    # ═══════════════ TICKER ═══════════════
    async def _ticker(self):
        await asyncio.sleep(8)
        while self._running:
            try: self._tick_all()
            except Exception as e: logger.exception(f"uni tick: {e}")
            await asyncio.sleep(TICK_INTERVAL)

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
        # boost
        boost_mult = 1.0
        if row.get("boost_until", 0) > ts:
            boost_mult = row.get("boost_mult") or 1.0

        # hunger decay
        last_h = row.get("last_hunger_tick") or ts
        dec = (ts - last_h) // HUNGER_DECAY_SEC
        hunger = row.get("hunger", 100)
        new_last_h = last_h
        if dec > 0:
            hunger = max(0, hunger - dec)
            new_last_h = last_h + dec * HUNGER_DECAY_SEC
        angry = 1 if hunger <= 0 else 0

        # production
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

    # ═══════════════ MESSAGE HANDLER ═══════════════
    async def on_message(self, event):
        try:
            if event.is_private: return
            me = await self.client.get_me()
            if event.sender_id == me.id: return
            raw = (event.raw_text or "").strip()
            if not raw: return
            uid = event.sender_id
            low = raw.lower().strip()

            # اطمینان از ثبت کاربر
            try:
                s = await event.get_sender()
                name = user_name(s)
            except Exception: name = str(uid)
            self.get_or_create(uid, name)

            # ─── انتقال ───
            if event.reply_to_msg_id and "انتقال" in raw and "یونیکورن" in raw:
                await self._handle_transfer(event, uid, raw); return

            # ─── دوئل ───
            if event.reply_to_msg_id and low in ("دوئل", "نبرد", "مبارزه"):
                await self._handle_battle(event, uid); return

            # ─── ازدواج ───
            if event.reply_to_msg_id and low in ("ازدواج", "ازدواج کن", "بگیر"):
                await self._handle_marry(event, uid); return

            # ─── تخم ───
            if low in ("تخم", "پرورش", "جوجه"):
                await self._handle_breed(event, uid); return

            # ─── نیه ───
            if low in ("نیه", "نيه", "نیییه", "نههه", "neigh"):
                await self._handle_neigh(event, uid); return

            # ─── برداشت ───
            if low in ("برداشت", "برداشت کن", "جمع", "جمع کن", "collect"):
                await self._show_profile(uid, event.chat_id, reply_to=event.id, flash="💰 برداشت شد!"); return

            # ─── غذا ───
            if low in ("غذا", "غذا بده", "feed", "خوراک"):
                await self._do_feed(uid, event.chat_id, reply_to=event.id); return

            # ─── پاداش روزانه ───
            if low in ("پاداش", "پاداش روزانه", "daily"):
                await self._do_daily(uid, event.chat_id, reply_to=event.id); return

            # ─── گردونه ───
            if low in ("گردونه", "شانس", "spin"):
                await self._do_spin(uid, event.chat_id, reply_to=event.id); return

            # ─── آمار کامل ───
            if low in ("یونیکورن هام", "یونیکورنهام", "یونیکورن های من",
                       "یونیکورن‌هام", "امار یونیکورن", "آمار یونیکورن",
                       "یونیکورن هام کامل"):
                await self._show_full_stats(event.chat_id, uid, reply_to=event.id); return

            # ─── آمار شخص دیگه (ریپلای) ───
            if (event.reply_to_msg_id and low in ("یونیکورن هاش", "یونیکورن‌هاش",
                                                  "یونیکورن های اون", "یونیکورن هاش کامل")):
                rm = await event.get_reply_message()
                target = rm.sender_id if rm else None
                if target:
                    self.get_or_create(target, "—")
                    await self._show_full_stats(event.chat_id, target, reply_to=event.id); return

            # ─── پروفایل ───
            if low in ("یونیکورن", "تک شاخ", "تک‌شاخ", "یونیکورنم",
                       "شونیکورن", "unicorn", "پروفایل"):
                await self._show_profile(uid, event.chat_id, reply_to=event.id); return
        except Exception as e:
            logger.exception(f"uni msg: {e}")

    # ═══════════════ PROFILE ═══════════════
    async def _show_profile(self, uid, chat_id, reply_to=None, flash=None, force_new=False):
        u = self.get_unicorn(uid)
        if not u: return
        try:
            self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
        except Exception: pass

        text = self._render_profile(u, flash=flash)
        btns = self._profile_buttons(uid)

        msg_id = u.get("last_profile_msg") or 0
        stored_chat = u.get("last_profile_chat") or 0

        if not force_new and msg_id and stored_chat == chat_id:
            try:
                await self.client.edit_message(chat_id, msg_id, text=text,
                                                buttons=btns, parse_mode="html")
                return
            except MessageNotModifiedError:
                return
            except Exception:
                pass

        kwargs = {"parse_mode": "html", "buttons": btns}
        if reply_to: kwargs["reply_to"] = reply_to
        try:
            sent = await self.client.send_message(chat_id, text, **kwargs)
            self.update(uid, last_profile_msg=sent.id, last_profile_chat=chat_id)
        except Exception as e:
            logger.warning(f"send profile: {e}")

    def _render_profile(self, u, flash=None):
        uid = u["user_id"]
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

        # boost line
        boost_line = ""
        if boost_mult and boost_mult > 1.0:
            rem = max(0, (u.get("boost_until", 0) or 0) - now_ts())
            boost_line = f"\n{PE('bolt','⚡')} <b>بونوس فعال:</b> <code>x{boost_mult:g}</code>  ·  ⏰ {rem//60}:{rem%60:02d}"

        # status
        if angry:
            status = f"{PE('cross','❌')} <b>قهر کرده!</b> — غذا بده تا برگرده"
        elif hunger < 30:
            status = f"{PE('warning','⚠️')} <b>گشنه‌ست</b> — یه غذا بده"
        else:
            status = f"{PE('check','✅')} <b>خوشحال و پرانرژی</b>"

        # level info
        nxt = next_level_info(level, neigh, points)
        if nxt:
            neigh_bar = progress_bar(nxt["neigh_cur"], nxt["neigh_total"])
            pts_bar = progress_bar(nxt["pts_cur"], nxt["pts_total"])
            lvl_block = (
                f"{PE('star','⭐')} <b>تا لول {nxt['next']}:</b>\n"
                f"   👋 {neigh_bar}  <code>{nxt['neigh_cur']}/{nxt['neigh_total']}</code>\n"
                f"   {PE('gem','💎')} {pts_bar}  <code>{fmt_num(nxt['pts_cur'])}/{fmt_num(nxt['pts_total'])}</code>"
            )
        else:
            lvl_block = f"{PE('crown','👑')} <b>به بالاترین لول رسیدی!</b>"

        # flash
        flash_block = ""
        if flash:
            flash_block = f"{flash}\n{DIV2}\n\n"

        # marriage
        marry = u.get("married_to") or 0
        marry_line = ""
        if marry:
            marry_line = f"\n{PE('heart','💖')} <b>همسر:</b> <a href=\"tg://user?id={marry}\">دوست‌داشتنی</a>"

        return (
            f"{flash_block}"
            f"{PE('sparkle','✨')}  <b>پروفایل یونیکورن</b>  {PE('sparkle','✨')}\n"
            f"{DIV}\n\n"
            f"{face}  <b>{skin_emoji} {h(u.get('name') or '—')}</b>\n"
            f"{PE('crown','👑')} <b>{LEVEL_NAMES[level-1]}</b>\n"
            f"{PE('trophy','🏆')} <b>لول</b> <code>{level}/10</code>  {PE('diamond','💎')} <b>اسکین</b> <code>{skin_name}</code>{marry_line}\n\n"
            f"{PE('info','ℹ️')} <b>وضعیت:</b> {status}\n"
            f"🍰 <b>سیری:</b> {hunger_bar(hunger)} <code>{hunger}%</code>\n"
            f"{DIV2}\n"
            f"{PE('gem','💎')} <b>موجودی:</b> <code>{fmt_num(points)}</code>\n"
            f"{PE('gift','🎁')} <b>در حال تولید:</b> <code>{fmt_num(pending)}</code>\n"
            f"{PE('bolt','⚡')} <b>سرعت:</b> <code>{per_hour:.0f}/ساعت</code>{boost_line}\n"
            f"{PE('wave','👋')} <b>تعداد نیه:</b> <code>{neigh}</code>\n"
            f"{DIV2}\n"
            f"{lvl_block}\n\n"
            f"{PE('rocket','🚀')} <i>نیه بزن → پوینت بگیر → برداشت کن!</i>"
        )

    def _profile_buttons(self, uid):
        return [
            [Button.inline("🍰 غذا", data=f"uni:feed:{uid}".encode()),
             Button.inline("💰 برداشت", data=f"uni:withdraw:{uid}".encode())],
            [Button.inline("🎁 روزانه", data=f"uni:daily:{uid}".encode()),
             Button.inline("🎰 گردونه", data=f"uni:spin:{uid}".encode())],
            [Button.inline("🎨 رنگ‌ها", data=f"uni:skins:{uid}".encode()),
             Button.inline("🏆 دستاوردها", data=f"uni:ach:{uid}".encode())],
            [Button.inline("🏠 خانه", data=f"uni:home:{uid}".encode()),
             Button.inline("📊 آمار کامل", data=f"uni:stats:{uid}".encode())],
            [Button.inline("🔄 بروزرسانی", data=f"uni:refresh:{uid}".encode())],
        ]

    # ═══════════════ NEIGH ═══════════════
    async def _handle_neigh(self, event, uid):
        u = self.get_or_create(uid, "—")
        ts = now_ts()

        if u.get("angry"):
            await self._show_profile(uid, event.chat_id, reply_to=event.id,
                flash=f"{PE('cross','❌')} <b>یونیکورنت قهره!</b> اول غذا بده 💔")
            return

        last = u.get("last_neigh") or 0
        if ts - last < NEIGH_COOLDOWN_SEC:
            rem = NEIGH_COOLDOWN_SEC - (ts - last)
            await self._show_profile(uid, event.chat_id, reply_to=event.id,
                flash=f"⏰ <b>هنوز خسته‌ست!</b> تا <code>{rem//60}:{rem%60:02d}</code> صبر کن 💤")
            return

        reward = random.randint(NEIGH_REWARD_MIN, NEIGH_REWARD_MAX)
        level = max(1, min(10, u.get("level") or 1))
        if level >= 8: reward *= 2
        elif level >= 5: reward = int(reward * 1.5)

        new_neigh = (u.get("neigh_count") or 0) + 1
        new_points = (u.get("points") or 0) + reward
        new_total = (u.get("total_earned") or 0) + reward
        new_total_neigh = (u.get("total_neigh_ever") or 0) + 1

        self.update(uid, last_neigh=ts, neigh_count=new_neigh,
                    points=new_points, total_earned=new_total,
                    total_neigh_ever=new_total_neigh)

        u2 = self.get_unicorn(uid)
        leveled = self._check_levelup(uid, u2)
        new_ach = self.check_achievements(uid)

        # ساخت flash
        visuals = ["🦄💖", "🌈✨", "💫🌟", "🎀💝", "🌙⭐", "🦄💫", "💖✨", "🌸🦄"]
        v = random.choice(visuals)
        flash = (f"{v}  <b>نـیـه‌ه‌ه‌ه!</b>  {v}\n"
                 f"{PE('gift','🎁')} پاداش: <code>+{fmt_num(reward)}</code>  ·  "
                 f"{PE('gem','💎')} موجودی: <code>{fmt_num(new_points)}</code>")

        if leveled:
            nxt = leveled["new_level"]
            flash += (f"\n\n{PE('party','🎉')} <b>لول آپ! {LEVEL_NAMES[nxt-1]}</b>\n"
                      f"{PE('check','✅')} قفل باز شد: <i>{LEVEL_UNLOCKS[nxt-1]}</i>")

        if new_ach:
            ach_names = " · ".join([ACHIEVEMENTS[k][0] + " " + ACHIEVEMENTS[k][1] for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} <b>دستاورد جدید:</b> {ach_names}"

        await self._show_profile(uid, event.chat_id, reply_to=event.id, flash=flash)

    def _check_levelup(self, uid, u):
        if not u: return None
        level = max(1, min(10, u.get("level") or 1))
        if level >= 10: return None
        neigh = u.get("neigh_count") or 0
        points = u.get("points") or 0
        nxt = level + 1
        if neigh >= LEVEL_THRESHOLDS[nxt-1] and points >= LEVEL_POINT_COST[nxt-1]:
            self.update(uid, level=nxt, points=points - LEVEL_POINT_COST[nxt-1])
            return {"new_level": nxt}
        return None

    # ═══════════════ FEED ═══════════════
    async def _do_feed(self, uid, chat_id, reply_to=None):
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
                flash=f"{PE('cross','❌')} <b>پوینت کافی نداری!</b> لازم: <code>{fmt_num(FEED_COST)}</code>")
            return
        new_h = min(100, hunger + FEED_HUNGER_BOOST)
        new_pts = points - FEED_COST
        self.update(uid, hunger=new_h, points=new_pts, angry=0,
                    last_feed=now_ts(), total_fed=(u.get("total_fed") or 0) + 1,
                    last_hunger_tick=now_ts())
        v = random.choice(["🍰🍬", "🧁🍭", "🍪🍩", "🎂🌸", "🍯💖"])
        await self._show_profile(uid, chat_id, reply_to=reply_to,
            flash=f"{v} <b>نـوم‌نـوم!</b> سیری: <code>{new_h}%</code> {PE('heart','💖')}")

    # ═══════════════ WITHDRAW ═══════════════
    async def _do_withdraw(self, uid, chat_id, reply_to=None):
        u = self.get_unicorn(uid)
        if not u: return
        try:
            self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
        except Exception: pass
        pending = int(u.get("pending") or 0)
        if pending < 1:
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{PE('info','ℹ️')} <b>چیزی برای برداشت نیست!</b> کمی صبر کن 🦄")
            return
        if u.get("angry"):
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{PE('cross','❌')} <b>قهره!</b> اول غذا بده 💔")
            return
        new_pts = (u.get("points") or 0) + pending
        new_tot = (u.get("total_earned") or 0) + pending
        self.update(uid, points=new_pts, pending=0, total_earned=new_tot,
                    last_produce=now_ts())
        new_ach = self.check_achievements(uid)
        flash = f"{PE('gift','🎁')} <b>برداشت شد!</b> <code>+{fmt_num(pending)}</code>"
        if new_ach:
            ach_names = " · ".join([ACHIEVEMENTS[k][0] + " " + ACHIEVEMENTS[k][1] for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} <b>دستاورد جدید:</b> {ach_names}"
        await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)

    # ═══════════════ DAILY ═══════════════
    async def _do_daily(self, uid, chat_id, reply_to=None, edit_msg=None):
        u = self.get_unicorn(uid)
        if not u: return
        ts = now_ts()
        last = u.get("last_daily") or 0
        if ts - last < DAILY_COOLDOWN_SEC:
            rem = DAILY_COOLDOWN_SEC - (ts - last)
            msg = (f"⏰ <b>پاداش بعدی:</b> <code>{rem//3600}:{(rem%3600)//60:02d}</code>"
                   f"\n{PE('info','ℹ️')} هر ۲۴ ساعت یه بار می‌تونی بگیری")
            if edit_msg:
                try:
                    await self.client.edit_message(chat_id, edit_msg, text=msg,
                                                    buttons=self._profile_buttons(uid),
                                                    parse_mode="html")
                except Exception: pass
            elif reply_to:
                await self._show_profile(uid, chat_id, reply_to=reply_to, flash=msg)
            return

        # streak logic
        streak = u.get("daily_streak") or 0
        if last and ts - last < DAILY_COOLDOWN_SEC * 2:
            streak += 1
        else:
            streak = 1
        best = max(streak, u.get("daily_best") or 0)
        reward = DAILY_BASE_REWARD + (streak - 1) * DAILY_STREAK_BONUS
        reward = min(reward, DAILY_BASE_REWARD + DAILY_MAX_STREAK * DAILY_STREAK_BONUS)

        new_pts = (u.get("points") or 0) + reward
        new_tot = (u.get("total_earned") or 0) + reward
        self.update(uid, last_daily=ts, daily_streak=streak, daily_best=best,
                    points=new_pts, total_earned=new_tot)
        new_ach = self.check_achievements(uid)

        flash = (f"🎁 <b>پاداش روزانه!</b>\n"
                 f"🔥 استریک: <code>{streak}</code> روز\n"
                 f"{PE('gem','💎')} پاداش: <code>+{fmt_num(reward)}</code>")
        if new_ach:
            ach_names = " · ".join([ACHIEVEMENTS[k][0] + " " + ACHIEVEMENTS[k][1] for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} <b>دستاورد جدید:</b> {ach_names}"

        if edit_msg:
            try:
                u2 = self.get_unicorn(uid)
                text = self._render_profile(u2, flash=flash)
                await self.client.edit_message(chat_id, edit_msg, text=text,
                                                buttons=self._profile_buttons(uid),
                                                parse_mode="html")
            except Exception: pass
        else:
            await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)

    # ═══════════════ SPIN ═══════════════
    async def _do_spin(self, uid, chat_id, reply_to=None, edit_msg=None):
        u = self.get_unicorn(uid)
        if not u: return
        ts = now_ts()
        last = u.get("last_spin") or 0
        if ts - last < SPIN_COOLDOWN_SEC:
            rem = SPIN_COOLDOWN_SEC - (ts - last)
            msg = (f"🎰 <b>گردونه هنوز آماده نیست!</b>\n"
                   f"⏰ تا <code>{rem//3600}:{(rem%3600)//60:02d}</code> صبر کن")
            if edit_msg:
                try:
                    await self.client.edit_message(chat_id, edit_msg, text=msg,
                                                    buttons=self._profile_buttons(uid),
                                                    parse_mode="html")
                except Exception: pass
            elif reply_to:
                await self._show_profile(uid, chat_id, reply_to=reply_to, flash=msg)
            return

        # انتخاب جایزه
        total_w = sum(r[4] for r in SPIN_REWARDS)
        pick = random.randint(1, total_w); acc = 0
        chosen = SPIN_REWARDS[0]
        for r in SPIN_REWARDS:
            acc += r[4]
            if pick <= acc: chosen = r; break

        emoji, label, kind, val, _ = chosen
        flash = f"🎰 <b>گردونه شانس!</b>\n{emoji} {label}"

        upd = {"last_spin": ts, "spin_count": (u.get("spin_count") or 0) + 1}
        if kind == "points":
            upd["points"] = (u.get("points") or 0) + val
            upd["total_earned"] = (u.get("total_earned") or 0) + val
            flash += f"\n{PE('gem','💎')} <code>+{fmt_num(val)}</code> پوینت!"
        elif kind.startswith("boost"):
            parts = kind.split("_")
            mult = int(parts[0].replace("boost", ""))
            dur = int(parts[1])
            upd["boost_mult"] = float(mult)
            upd["boost_until"] = ts + dur
            flash += f"\n{PE('bolt','⚡')} بونوس <code>x{mult}</code> برای <code>{dur//60}</code> دقیقه!"
        elif kind == "hunger":
            upd["hunger"] = 100; upd["angry"] = 0; upd["last_hunger_tick"] = ts
            flash += f"\n🍰 سیری فول شد!"
        elif kind == "egg":
            upd["eggs"] = (u.get("eggs") or 0) + 1
            flash += f"\n🥚 یه تخم یونیکورن گرفتی!"

        self.update(uid, **upd)
        new_ach = self.check_achievements(uid)
        if new_ach:
            ach_names = " · ".join([ACHIEVEMENTS[k][0] + " " + ACHIEVEMENTS[k][1] for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} <b>دستاورد جدید:</b> {ach_names}"

        if edit_msg:
            try:
                u2 = self.get_unicorn(uid)
                text = self._render_profile(u2, flash=flash)
                await self.client.edit_message(chat_id, edit_msg, text=text,
                                                buttons=self._profile_buttons(uid),
                                                parse_mode="html")
            except Exception: pass
        else:
            await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)

    # ═══════════════ TRANSFER ═══════════════
    async def _handle_transfer(self, event, uid, raw):
        try:
            m = re.search(r"(\d+(?:[.,]\d+)?\s*[kmbKMB]?)",
                          raw.replace("انتقال", "").replace("یونیکورن", ""))
            if not m:
                await event.reply(
                    f"{PE('warning','⚠️')} فرمت: ریپلای + <code>انتقال یونیکورن 100k</code>",
                    parse_mode="html"); return
            amount = parse_amount(m.group(1))
            if not amount or amount < 1:
                await event.reply(f"{PE('cross','❌')} مقدار نامعتبر!", parse_mode="html"); return

            rm = await event.get_reply_message()
            if not rm: return
            to_uid = rm.sender_id
            if to_uid == uid:
                await event.reply(f"{PE('cross','❌')} به خودت نمی‌تونی!", parse_mode="html"); return

            su = self.get_unicorn(uid) or self.get_or_create(uid, "—")
            if (su.get("points") or 0) < amount:
                await event.reply(
                    f"{PE('cross','❌')} پوینت کافی نداری!\n"
                    f"داری: <code>{fmt_num(su.get('points', 0))}</code>", parse_mode="html"); return

            try:
                s = await self.client.get_entity(to_uid)
                to_name = user_name(s)
            except Exception: to_name = str(to_uid)
            self.get_or_create(to_uid, to_name)
            tu = self.get_unicorn(to_uid)

            self.update(uid, points=(su.get("points") or 0) - amount)
            self.update(to_uid, points=(tu.get("points") or 0) + amount)
            c = self._c()
            c.execute("INSERT INTO unicorn_transfers (from_id, to_id, amount, at) VALUES (%s,%s,%s,%s)",
                      (uid, to_uid, amount, now_ts()))

            self.check_achievements(uid); self.check_achievements(to_uid)

            try:
                so = await event.get_sender(); fname = user_name(so)
            except Exception: fname = str(uid)

            await event.reply(
                f"{PE('rocket','🚀')} <b>انتقال موفق!</b>\n"
                f"{DIV}\n"
                f"{PE('user','👤')} <a href=\"tg://user?id={uid}\">{h(fname)}</a>\n"
                f"    ⬇️ <code>{fmt_num(amount)}</code> ⬇️\n"
                f"{PE('target','🎯')} <a href=\"tg://user?id={to_uid}\">{h(to_name)}</a>",
                parse_mode="html")
        except Exception as e:
            logger.exception(f"transfer: {e}")

    # ═══════════════ BATTLE ═══════════════
    async def _handle_battle(self, event, uid):
        rm = await event.get_reply_message()
        if not rm: return
        target = rm.sender_id
        if target == uid:
            await event.reply(f"{PE('cross','❌')} با خودت نمی‌تونی بجنگی!", parse_mode="html"); return

        try:
            ts = await self.client.get_entity(target)
            tname = user_name(ts)
        except Exception: tname = str(target)
        self.get_or_create(target, tname)
        a = self.get_unicorn(uid); b = self.get_unicorn(target)

        if a.get("angry") or b.get("angry"):
            await event.reply(f"{PE('cross','❌')} یه یونیکورن قهره! اول غذا بدین.", parse_mode="html"); return

        a_pow = ((a.get("level") or 1) * 100 + (a.get("neigh_count") or 0) +
                 (a.get("battles_won") or 0) * 20 + random.randint(0, 200))
        b_pow = ((b.get("level") or 1) * 100 + (b.get("neigh_count") or 0) +
                 (b.get("battles_won") or 0) * 20 + random.randint(0, 200))

        a_name = h(a.get("name") or "—"); b_name = h(b.get("name") or "—")
        # قربانی: مقدار کم از پوینت‌ها
        stake = 500

        if a_pow >= b_pow:
            winner, loser = a, b; winner_uid, loser_uid = uid, target
            reward = min(1000 + (winner.get("level") or 1) * 300, 10000)
        else:
            winner, loser = b, a; winner_uid, loser_uid = target, uid
            reward = min(1000 + (winner.get("level") or 1) * 300, 10000)

        # جایزه فقط پوینت اضافه می‌شه (بدون کم کردن از بازنده)
        self.update(winner_uid,
                    points=(winner.get("points") or 0) + reward,
                    total_earned=(winner.get("total_earned") or 0) + reward,
                    battles_won=(winner.get("battles_won") or 0) + 1)
        self.update(loser_uid, battles_lost=(loser.get("battles_lost") or 0) + 1)
        c = self._c()
        c.execute("INSERT INTO unicorn_battles (winner_id, loser_id, amount, at) VALUES (%s,%s,%s,%s)",
                  (winner_uid, loser_uid, reward, now_ts()))
        self.check_achievements(winner_uid); self.check_achievements(loser_uid)

        await event.reply(
            f"🥊  <b>نـبـرد یـونـیـکـورن‌هـا!</b>  🥊\n"
            f"{DIV}\n\n"
            f"🦄 <a href=\"tg://user?id={uid}\">{a_name}</a>  vs  🦄 <a href=\"tg://user?id={target}\">{b_name}</a>\n"
            f"{DIV2}\n"
            f"⚔️ قدرت {a_name}: <code>{a_pow}</code>\n"
            f"⚔️ قدرت {b_name}: <code>{b_pow}</code>\n"
            f"{DIV2}\n"
            f"{PE('crown','👑')} <b>برنده:</b> <a href=\"tg://user?id={winner_uid}\">{h(winner.get('name') or '—')}</a>\n"
            f"{PE('gift','🎁')} جایزه: <code>+{fmt_num(reward)}</code> پوینت\n"
            f"{PE('heart','💖')} بازنده هم بدون آسیب رفت 💕",
            parse_mode="html")

    # ═══════════════ MARRY ═══════════════
    async def _handle_marry(self, event, uid):
        rm = await event.get_reply_message()
        if not rm: return
        target = rm.sender_id
        if target == uid:
            await event.reply(f"{PE('cross','❌')} با خودت نمی‌تونی!", parse_mode="html"); return

        try:
            ts = await self.client.get_entity(target); tname = user_name(ts)
        except Exception: tname = str(target)
        self.get_or_create(target, tname)
        a = self.get_unicorn(uid); b = self.get_unicorn(target)

        if a.get("married_to") and a.get("married_to") != 0:
            await event.reply(f"{PE('cross','❌')} تو الان متأهلی! اول جدا شو.", parse_mode="html"); return
        if b.get("married_to") and b.get("married_to") != 0:
            await event.reply(f"{PE('cross','❌')} یونیکورن اون متأهله!", parse_mode="html"); return

        self.update(uid, married_to=target, married_at=now_ts())
        self.update(target, married_to=uid, married_at=now_ts())
        self.check_achievements(uid); self.check_achievements(target)

        await event.reply(
            f"💍  <b>ازدواج یـونـیـکـورنـی!</b>  💍\n"
            f"{DIV}\n\n"
            f"🌸 <a href=\"tg://user?id={uid}\">{h(a.get('name') or '—')}</a>  {PE('heart','💖')}  "
            f"<a href=\"tg://user?id={target}\">{h(b.get('name') or '—')}</a>\n\n"
            f"🎉 حالا می‌تونید با «تخم» پرورش بدید!\n"
            f"🥚 تخم فعلی شما: <code>{a.get('eggs') or 0}</code>",
            parse_mode="html")

    # ═══════════════ BREED ═══════════════
    async def _handle_breed(self, event, uid):
        u = self.get_unicorn(uid)
        if not u: return
        marr = u.get("married_to") or 0
        if not marr:
            await event.reply(
                f"{PE('cross','❌')} <b>اول باید ازدواج کنی!</b>\n"
                f"روی پیام کسی ریپلای کن و بنویس <code>ازدواج</code> 💍",
                parse_mode="html"); return

        ts = now_ts()
        last_breed = u.get("last_daily") or 0  # reuse
        # کول‌داون ۶ ساعت
        last_breed_real = u.get("boost_until") if False else 0  # unused
        # استفاده از فیلد جداگانه بهتره، فعلا یه کول‌داون ساده با زمان حال
        last_egg = u.get("created_at") or 0
        # real kool: استفاده از last_feed به عنوان breed cd? بهتره جداگانه. فعلا هر ۶ ساعت
        last_breed_at = getattr(self, "_last_breed_cache", {}).get(uid, 0)
        if ts - last_breed_at < 6 * 3600:
            rem = 6 * 3600 - (ts - last_breed_at)
            await event.reply(
                f"🥚 <b>هنوز آماده نیست!</b>\n⏰ تا <code>{rem//3600}:{(rem%3600)//60:02d}</code> صبر کن",
                parse_mode="html"); return

        if not hasattr(self, "_last_breed_cache"): self._last_breed_cache = {}
        self._last_breed_cache[uid] = ts
        cost = 5000
        if (u.get("points") or 0) < cost:
            await event.reply(
                f"{PE('cross','❌')} برای پرورش <code>{fmt_num(cost)}</code> پوینت لازمه!",
                parse_mode="html"); return

        self.update(uid, points=(u.get("points") or 0) - cost, eggs=(u.get("eggs") or 0) + 1)
        self.update(marr, eggs=(self.get_unicorn(marr).get("eggs") or 0) + 1 if self.get_unicorn(marr) else 1)
        self.add_achievement(uid, "breeder")

        await event.reply(
            f"👶  <b>تـخـم جـدیـد!</b>  🥚\n"
            f"{DIV}\n\n"
            f"🌸 یه تخم یونیکورن کوچولوی کیوت ساختی!\n"
            f"🥚 تخم‌های تو: <code>{(u.get('eggs') or 0) + 1}</code>\n"
            f"💕 همسرت هم یه تخم گرفت!\n\n"
            f"{PE('sparkle','✨')} <i>تخم‌ها در لول ۱۰ به یونیکورن واقعی تبدیل می‌شن!</i>",
            parse_mode="html")

    # ═══════════════ FULL STATS ═══════════════
    async def _show_full_stats(self, chat_id, uid, reply_to=None):
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
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception: ach = []

        # مسیر لول‌ها
        lvl_lines = []
        for i in range(10):
            lvl = i + 1
            status = "✅" if level > lvl else ("🔵" if level == lvl else "🔒")
            lock_status = "🔓" if level >= lvl else "🔒"
            lvl_lines.append(f"  {lock_status} Lv{lvl}  {LEVEL_NAMES[i]}")
            if lvl < 10:
                need_n = LEVEL_THRESHOLDS[lvl]
                need_p = LEVEL_POINT_COST[lvl]
                lvl_lines.append(f"        └ {need_n}👋 + {fmt_num(need_p)}💎")

        # دستاوردها
        ach_lines = []
        for k, (emoji, name, desc) in ACHIEVEMENTS.items():
            if k in ach:
                ach_lines.append(f"  ✅ {emoji} <b>{name}</b>")
            else:
                ach_lines.append(f"  🔒 {emoji} <s>{name}</s>")
        ach_text = "\n".join(ach_lines[:14])
        ach_count = len(ach)

        text = (
            f"{PE('chart','📊')}  <b>آمـار کـامـل یـونـیـکـورن</b>  {PE('chart','📊')}\n"
            f"{DIV}\n\n"
            f"{face}  <b>{skin_e} <a href=\"tg://user?id={uid}\">{h(u.get('name') or '—')}</a></b>\n"
            f"{PE('crown','👑')} <b>{LEVEL_NAMES[level-1]}</b>  ·  <b>Lv {level}/10</b>\n"
            f"{PE('diamond','💎')} اسکین: <b>{skin_n}</b>\n\n"
            f"{DIV2}\n"
            f"{PE('gem','💎')} <b>موجودی فعلی:</b> <code>{fmt_num(u.get('points', 0))}</code>\n"
            f"{PE('trophy','🏆')} <b>کل درآمد:</b> <code>{fmt_num(u.get('total_earned', 0))}</code>\n"
            f"{PE('gift','🎁')} <b>در حال تولید:</b> <code>{fmt_num(int(u.get('pending') or 0))}</code>\n"
            f"{PE('bolt','⚡')} <b>تولید:</b> <code>{per_hour:.0f}/ساعت</code> ≈ <code>{fmt_num(per_day)}/روز</code>\n"
            f"{PE('wave','👋')} <b>مجموع نیه:</b> <code>{u.get('total_neigh_ever', 0)}</code>  "
            f"(فعلی: <code>{u.get('neigh_count', 0)}</code>)\n"
            f"🍰 <b>سیری:</b> <code>{u.get('hunger', 100)}%</code>  ·  "
            f"🍽 <b>تعداد غذا:</b> <code>{u.get('total_fed', 0)}</code>\n"
            f"{DIV2}\n"
            f"🎁 <b>استریک روزانه:</b> <code>{u.get('daily_streak', 0)}</code>  ·  "
            f"رکورد: <code>{u.get('daily_best', 0)}</code>\n"
            f"🎰 <b>گردونه:</b> <code>{u.get('spin_count', 0)}</code> بار\n"
            f"🥊 <b>برد/باخت:</b> <code>{u.get('battles_won', 0)}/{u.get('battles_lost', 0)}</code>\n"
            f"💍 <b>همسر:</b> "
            + (f"<a href=\"tg://user?id={u.get('married_to')}\">متأهل</a>" if u.get("married_to") else "<i>مجرد</i>")
            + f"\n🥚 <b>تخم‌ها:</b> <code>{u.get('eggs', 0)}</code>\n"
            f"🏆 <b>دستاورد:</b> <code>{ach_count}/{len(ACHIEVEMENTS)}</code>\n"
            f"{DIV2}\n"
            f"{PE('star','⭐')} <b>مسیر لول‌ها:</b>\n"
            + "\n".join(lvl_lines) +
            f"\n\n{PE('trophy','🏆')} <b>دستاوردها:</b>\n{ach_text}\n\n"
            f"{DIV}\n"
            f"{PE('sparkle','✨')} <i>ادامه بده تا افسانه‌ای بشی!</i>"
        )

        # تقسیم اگه خیلی طولانی
        if len(text) > 4000:
            chunks = [text[i:i+3500] for i in range(0, len(text), 3500)]
            kwargs = {"parse_mode": "html"}
            if reply_to: kwargs["reply_to"] = reply_to
            for c in chunks:
                try:
                    await self.client.send_message(chat_id, c, **kwargs)
                    await asyncio.sleep(0.4)
                    kwargs.pop("reply_to", None)
                except Exception: pass
        else:
            kwargs = {"parse_mode": "html"}
            if reply_to: kwargs["reply_to"] = reply_to
            try:
                await self.client.send_message(chat_id, text, **kwargs)
            except Exception as e:
                logger.warning(f"stats send: {e}")

    # ═══════════════ CALLBACK ═══════════════
    async def on_callback(self, event):
        try:
            data = event.data.decode("utf-8", "ignore")
            if not data.startswith("uni:"): return
            uid = event.sender_id
            parts = data.split(":")
            action = parts[1]

            # چک مالکیت برای اکشن‌های اصلی
            if action in ("feed", "withdraw", "daily", "spin", "skins", "ach",
                          "home", "stats", "refresh"):
                target = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else uid
                if target != uid:
                    await event.answer("⛔ این پروفایل مال تو نیست!", alert=True); return

            if action == "refresh":
                await event.answer("🔄")
                u = self.get_unicorn(uid)
                if u:
                    try: self._tick_one(u, now_ts())
                    except Exception: pass
                await self._show_profile(uid, event.chat_id, force_new=False)
                return

            if action == "feed":
                await event.answer("🍰")
                await self._do_feed(uid, event.chat_id); return

            if action == "withdraw":
                await event.answer("💰")
                await self._do_withdraw(uid, event.chat_id); return

            if action == "daily":
                await event.answer("🎁")
                await self._do_daily(uid, event.chat_id, edit_msg=event.message_id); return

            if action == "spin":
                await event.answer("🎰")
                await self._do_spin(uid, event.chat_id, edit_msg=event.message_id); return

            if action == "skins":
                await event.answer()
                await self._show_skins(event, uid); return

            if action == "ach":
                await event.answer()
                await self._show_achievements(event, uid); return

            if action == "home":
                await event.answer()
                await self._show_home(event, uid); return

            if action == "stats":
                await event.answer()
                await self._show_full_stats(event.chat_id, uid, reply_to=event.message_id); return

            if action == "buyskin":
                await event.answer()
                key = parts[2]
                await self._buy_skin(event, uid, key); return

            if action == "back":
                await event.answer()
                await self._show_profile(uid, event.chat_id, force_new=False); return

        except Exception as e:
            logger.exception(f"uni cb: {e}")
            try: await event.answer("خطا!", alert=True)
            except Exception: pass

    # ═══════════════ SKINS UI ═══════════════
    async def _show_skins(self, event, uid):
        u = self.get_unicorn(uid)
        if not u: return
        cur = u.get("color") or "classic"
        pts = u.get("points") or 0
        lines = [
            f"{PE('diamond','💎')}  <b>رنگ‌های یونیکورن</b>  {PE('diamond','💎')}",
            f"{DIV}",
            f"",
            f"{PE('gem','💎')} <b>موجودی:</b> <code>{fmt_num(pts)}</code>",
            f"🎨 <b>رنگ فعلی:</b> <code>{SKINS.get(cur, SKINS['classic'])[1]}</code>",
            f"",
            f"{DIV2}",
        ]
        for k, (em, name, cost) in SKINS.items():
            if k == cur:
                lines.append(f"  ✅ {em} <b>{name}</b>  <i>(فعلی)</i>")
            elif cost == 0:
                lines.append(f"  🎨 {em} <b>{name}</b>  <i>رایگان</i>")
            else:
                lines.append(f"  {'🟢' if pts >= cost else '🔴'} {em} <b>{name}</b>  —  <code>{fmt_num(cost)}</code>")
        btns = []
        row = []
        for k, (em, name, cost) in SKINS.items():
            if k == cur: continue
            row.append(Button.inline(f"{em} {name}", data=f"uni:buyskin:{k}".encode()))
            if len(row) == 2: btns.append(row); row = []
        if row: btns.append(row)
        btns.append([Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())])
        try:
            await self.client.edit_message(event.chat_id, event.message_id,
                text="\n".join(lines), buttons=btns, parse_mode="html")
        except MessageNotModifiedError: pass
        except Exception as e: logger.warning(f"skins: {e}")

    async def _buy_skin(self, event, uid, key):
        if key not in SKINS: return
        u = self.get_unicorn(uid)
        if not u: return
        em, name, cost = SKINS[key]
        if (u.get("points") or 0) < cost:
            await event.answer(f"❌ پوینت کافی نداری! ({fmt_num(cost)} لازم)", alert=True); return
        self.update(uid, points=(u.get("points") or 0) - cost, color=key)
        await event.answer(f"✅ {name} خریداری شد!")
        u2 = self.get_unicorn(uid)
        text = self._render_profile(u2, flash=f"{PE('check','✅')} اسکین <b>{name}</b> فعال شد! {em}")
        try:
            await self.client.edit_message(event.chat_id, event.message_id,
                text=text, buttons=self._profile_buttons(uid), parse_mode="html")
        except Exception: pass

    # ═══════════════ ACHIEVEMENTS UI ═══════════════
    async def _show_achievements(self, event, uid):
        u = self.get_unicorn(uid)
        if not u: return
        try: ach = json.loads(u.get("achievements") or "[]")
        except Exception: ach = []
        lines = [
            f"{PE('trophy','🏆')}  <b>دستاوردهای یونیکورن</b>  {PE('trophy','🏆')}",
            f"{DIV}", f"",
            f"{PE('check','✅')} <b>باز شده:</b> <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>",
            f"", f"{DIV2}",
        ]
        for k, (em, name, desc) in ACHIEVEMENTS.items():
            if k in ach:
                lines.append(f"  ✅ {em} <b>{name}</b>\n        <i>{desc}</i>")
            else:
                lines.append(f"  🔒 {em} <s>{name}</s>\n        <i>{desc}</i>")
        btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
        try:
            await self.client.edit_message(event.chat_id, event.message_id,
                text="\n".join(lines), buttons=btns, parse_mode="html")
        except MessageNotModifiedError: pass
        except Exception as e: logger.warning(f"ach: {e}")

    # ═══════════════ HOME UI ═══════════════
    async def _show_home(self, event, uid):
        u = self.get_unicorn(uid)
        if not u: return
        try:
            self._tick_one(u, now_ts()); u = self.get_unicorn(uid) or u
        except Exception: pass
        level = max(1, min(10, u.get("level") or 1))
        skin_e, skin_n, _ = SKINS.get(u.get("color") or "classic", SKINS["classic"])
        face = hunger_face(u.get("hunger", 100), u.get("angry", 0))
        marr = u.get("married_to") or 0
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception: ach = []

        # decorations بر اساس لول
        decorations = "🌷🌻🌷" if level < 3 else "🌹🌸🌺" if level < 6 else "🌌✨🌟"

        lines = [
            f"🏠  <b>خـانـه‌ی یـونـیـکـورن</b>  🏠",
            f"{DIV}",
            f"",
            f"     {decorations}",
            f"     {skin_e} {face}",
            f"     {skin_e}",
            f"     {decorations}",
            f"",
            f"{PE('crown','👑')} <b>{LEVEL_NAMES[level-1]}</b>",
            f"{PE('gem','💎')} اسکین: <b>{skin_n}</b>",
            f"🍰 سیری: <b>{u.get('hunger', 100)}%</b>",
            f"{PE('wave','👋')} نیه: <b>{u.get('neigh_count', 0)}</b>",
            f"",
            f"{DIV2}",
        ]
        if marr:
            lines.append(f"{PE('heart','💖')} <b>همسر:</b> <a href=\"tg://user?id={marr}\">متأهل</a>")
        else:
            lines.append(f"{PE('heart','💖')} <b>مجرد</b> — دنبال عشق باش!")
        lines.append(f"🥚 <b>تخم:</b> <code>{u.get('eggs', 0)}</code>")
        lines.append(f"{PE('trophy','🏆')} <b>دستاورد:</b> <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>")

        btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
        try:
            await self.client.edit_message(event.chat_id, event.message_id,
                text="\n".join(lines), buttons=btns, parse_mode="html")
        except MessageNotModifiedError: pass
        except Exception as e: logger.warning(f"home: {e}")


# ═══════════════════════════════════════════════════════════
# 🦄 INIT
# ═══════════════════════════════════════════════════════════
_game = None

def init_unicorn(client, db):
    """بعد از client.start() صدا بزن"""
    global _game
    _game = UnicornGame(client, db)
    _game.setup()
    _game.register_handlers()
    _game.start_ticker()
    logger.info("🦄 Unicorn module initialized!")
    return _game