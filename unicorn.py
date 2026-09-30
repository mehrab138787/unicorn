# -*- coding: utf-8 -*-
"""
🦄 UNICORN PET GAME — Royal Edition v2
✨ Refactored: clean, shorter messages, all features intact
"""

import re, random, asyncio, logging, time, json
from telethon import events, Button
from telethon.errors import MessageNotModifiedError

logger = logging.getLogger("UnicornGame")

# ═══════════════════════════════════════════════════════════
# 🦄 CONFIG
# ═══════════════════════════════════════════════════════════
NEIGH_COOLDOWN_SEC = 300           # 5 دقیقه
FEED_COST = 500
FEED_HUNGER_BOOST = 25
HUNGER_DECAY_SEC = 300
PENDING_CAP_HOURS = 8
TICK_INTERVAL = 20
NEIGH_REWARD_MIN = 1
NEIGH_REWARD_MAX = 1000

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

# ═══════════════════════════════════════════════════════════
# 🎨 PREMIUM EMOJI
# ═══════════════════════════════════════════════════════════
PREM = {
    "sparkle": "5404654051945521778",
    "heart": "5443038326535759644",
    "star": "6337048821603763745",
    "crown": "5458603043203327669",
    "gem": "5404654051945521778",
    "fire": "5424972470023104089",
    "rocket": "5424972470023104089",
    "trophy": "5458603043203327669",
    "check": "5206607081334906820",
    "cross": "5210952531676504517",
    "party": "5456359790390093750",
    "wave": "5368324170671202286",
    "medal": "5458603043203327669",
    "gift": "5456359790390093750",
    "warning": "5447644880824181073",
    "info": "5323442290708985472",
    "user": "5443038326535759644",
    "id": "5397782960512444700",
    "time": "5458603043203327669",
    "point": "5436113877181941026",
    "flag": "5447644880824181073",
    "target": "5424972470023104089",
    "brain": "5404654051945521778",
    "chart": "5231200819986047254",
    "diamond": "5404654051945521778",
    "bolt": "5424972470023104089",
    "alert": "5447644880824181073",
    "lock": "5397782960512444700",
    "eye": "5397782960512444700",
    "detective": "5424972470023104089",
}

_TG_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="\d+">([^<]*)</tg-emoji>')


def PE(k, fb):
    eid = PREM.get(k)
    if not eid:
        return fb
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'


def strip_premium(text):
    return _TG_EMOJI_RE.sub(r"\1", text)


def _emoji_err(ex):
    s = str(ex).lower()
    return ("document" in s) or ("invalid" in s and "inline" in s) or \
           ("custom emoji" in s) or ("emoji" in s and "invalid" in s)


def fmt_num(n):
    try:
        n = int(n)
    except Exception:
        return "0"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def parse_amount(s):
    if not s:
        return None
    s = s.strip().lower().replace(",", "").replace("،", "").replace(" ", "")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([kmb])?$", s)
    if not m:
        return None
    n = float(m.group(1))
    u = m.group(2)
    if u == "k":
        n *= 1_000
    elif u == "m":
        n *= 1_000_000
    elif u == "b":
        n *= 1_000_000_000
    return int(n)


def now_ts():
    return int(time.time())


def user_name(u):
    if not u:
        return "ناشناس"
    n = (getattr(u, "first_name", "") or "").strip()
    l = (getattr(u, "last_name", "") or "").strip()
    full = (n + " " + l).strip()
    return full or getattr(u, "username", None) or str(getattr(u, "id", "?"))


def h(t):
    if t is None:
        return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hunger_face(hunger, angry):
    if angry or hunger <= 0:
        return "😭"
    if hunger < 20:
        return "😫"
    if hunger < 50:
        return "😕"
    if hunger < 80:
        return "🙂"
    return "😍"


def hunger_bar(h):
    h = max(0, min(100, int(h)))
    return "🍰" * (h // 10) + "🖤" * (10 - h // 10)


def progress_bar(cur, total, width=10):
    if total <= 0:
        return "▰" * width
    p = max(0, min(100, int(100 * cur / total)))
    filled = int(p / 100 * width)
    return "▰" * filled + "▱" * (width - filled)


def fmt_time(sec):
    sec = max(0, int(sec))
    if sec < 60:
        return f"{sec}s"
    m, s = divmod(sec, 60)
    if m < 60:
        return f"{m}:{s:02d}"
    hr, m = divmod(m, 60)
    return f"{hr}:{m:02d}:{s:02d}"


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

    # ═══════════════ SAFE SEND/EDIT ═══════════════
    async def _safe_send(self, chat_id, text, **kw):
        try:
            return await self.client.send_message(chat_id, text, **kw)
        except MessageNotModifiedError:
            return None
        except Exception as ex:
            if _emoji_err(ex):
                logger.warning(f"🦄 premium emoji failed: {str(ex)[:80]}")
                try:
                    return await self.client.send_message(chat_id, strip_premium(text), **kw)
                except Exception as ex2:
                    logger.error(f"🦄 fallback failed: {ex2}")
                    raise ex2
            raise

    async def _safe_edit_msg(self, chat_id, msg_id, text, buttons=None, **kw):
        try:
            await self.client.edit_message(chat_id, msg_id, text=text,
                                            buttons=buttons, parse_mode="html")
            return True
        except MessageNotModifiedError:
            return True
        except Exception as ex:
            if _emoji_err(ex):
                try:
                    await self.client.edit_message(chat_id, msg_id,
                                                    text=strip_premium(text),
                                                    buttons=buttons,
                                                    parse_mode="html")
                    return True
                except MessageNotModifiedError:
                    return True
                except Exception:
                    return False
            logger.warning(f"🦄 edit failed: {ex}")
            return False

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
        if u:
            return u
        ts = now_ts()
        c = self._c()
        c.execute("""INSERT INTO unicorns
            (user_id, name, created_at, last_neigh, last_feed,
             last_produce, last_hunger_tick, achievements)
            VALUES (%s, %s, %s, 0, %s, %s, %s, '[]')""",
            (uid, name, ts, ts, ts, ts))
        return self.get_unicorn(uid)

    def update(self, uid, **fields):
        if not fields:
            return
        keys = list(fields.keys())
        vals = [fields[k] for k in keys]
        sets = ", ".join([f"{k}=%s" for k in keys])
        vals.append(uid)
        c = self._c()
        c.execute(f"UPDATE unicorns SET {sets} WHERE user_id=%s", vals)

    def add_achievement(self, uid, key):
        u = self.get_unicorn(uid)
        if not u:
            return False
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception:
            ach = []
        if key in ach:
            return False
        ach.append(key)
        self.update(uid, achievements=json.dumps(ach))
        return True

    def check_achievements(self, uid):
        u = self.get_unicorn(uid)
        if not u:
            return []
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
            try:
                self._tick_all()
            except Exception as e:
                logger.exception(f"uni tick: {e}")
            await asyncio.sleep(TICK_INTERVAL)

    def _tick_all(self):
        ts = now_ts()
        c = self._c()
        c.execute("SELECT * FROM unicorns")
        for row in c.fetchall():
            try:
                self._tick_one(dict(row), ts)
            except Exception as e:
                logger.warning(f"tick: {e}")

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

    # ═══════════════ MESSAGE HANDLER ═══════════════
    async def on_message(self, event):
        try:
            if event.is_private:
                return
            me = await self.client.get_me()
            if event.sender_id == me.id:
                return
            raw = (event.raw_text or "").strip()
            if not raw:
                return
            uid = event.sender_id
            low = raw.lower().strip()

            try:
                s = await event.get_sender()
                name = user_name(s)
            except Exception:
                name = str(uid)
            self.get_or_create(uid, name)

            # انتقال
            if event.reply_to_msg_id and "انتقال" in raw and "یونیکورن" in raw:
                await self._handle_transfer(event, uid, raw)
                return

            # دوئل
            if event.reply_to_msg_id and low in ("دوئل", "نبرد", "مبارزه"):
                await self._handle_battle(event, uid)
                return

            # ازدواج
            if event.reply_to_msg_id and low in ("ازدواج", "ازدواج کن", "بگیر"):
                await self._handle_marry(event, uid)
                return

            # تخم
            if low in ("تخم", "پرورش", "جوجه"):
                await self._handle_breed(event, uid)
                return

            # نیه
            if low in ("نیه", "نيه", "نیییه", "نههه", "neigh"):
                await self._handle_neigh(event, uid)
                return

            # برداشت
            if low in ("برداشت", "برداشت کن", "جمع", "جمع کن", "collect"):
                await self._do_withdraw(uid, event.chat_id, reply_to=event.id)
                return

            # غذا
            if low in ("غذا", "غذا بده", "feed", "خوراک"):
                await self._do_feed(uid, event.chat_id, reply_to=event.id)
                return

            # پاداش روزانه
            if low in ("پاداش", "پاداش روزانه", "daily"):
                await self._do_daily(uid, event.chat_id, reply_to=event.id)
                return

            # گردونه
            if low in ("گردونه", "شانس", "spin"):
                await self._do_spin(uid, event.chat_id, reply_to=event.id)
                return

            # آمار کامل
            if low in ("یونیکورن هام", "یونیکورنهام", "یونیکورن های من",
                       "یونیکورن‌هام", "امار یونیکورن", "آمار یونیکورن",
                       "یونیکورن هام کامل"):
                await self._show_full_stats(event.chat_id, uid, reply_to=event.id)
                return

            # آمار شخص دیگه
            if (event.reply_to_msg_id and low in ("یونیکورن هاش", "یونیکورن‌هاش",
                                                  "یونیکورن های اون", "یونیکورن هاش کامل")):
                rm = await event.get_reply_message()
                target = rm.sender_id if rm else None
                if target:
                    self.get_or_create(target, "—")
                    await self._show_full_stats(event.chat_id, target, reply_to=event.id)
                    return

            # پروفایل
            if low in ("یونیکورن", "تک شاخ", "تک‌شاخ", "یونیکورنم",
                       "شونیکورن", "unicorn", "پروفایل"):
                await self._show_profile(uid, event.chat_id, reply_to=event.id)
                return
        except Exception as e:
            logger.exception(f"uni msg: {e}")

    # ═══════════════ PROFILE ═══════════════
    async def _show_profile(self, uid, chat_id, reply_to=None, flash=None, force_new=False):
        u = self.get_unicorn(uid)
        if not u:
            return
        try:
            self._tick_one(u, now_ts())
            u = self.get_unicorn(uid) or u
        except Exception:
            pass

        text = self._render_profile(u, flash=flash)
        btns = self._profile_buttons(uid)

        msg_id = u.get("last_profile_msg") or 0
        stored_chat = u.get("last_profile_chat") or 0

        if not force_new and msg_id and stored_chat == chat_id:
            ok = await self._safe_edit_msg(chat_id, msg_id, text, buttons=btns)
            if ok:
                return

        kwargs = {"parse_mode": "html", "buttons": btns}
        if reply_to:
            kwargs["reply_to"] = reply_to
        try:
            sent = await self._safe_send(chat_id, text, **kwargs)
            if sent:
                self.update(uid, last_profile_msg=sent.id, last_profile_chat=chat_id)
        except Exception as e:
            logger.error(f"🦄 profile send failed: {e}")

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

        # وضعیت
        if angry:
            status = f"{PE('cross','❌')} قهره — غذا بده"
        elif hunger < 30:
            status = f"{PE('warning','⚠️')} گشنه‌ست"
        else:
            status = f"{PE('check','✅')} سرحال"

        # بونوس
        boost_line = ""
        if boost_mult and boost_mult > 1.0:
            rem = max(0, (u.get("boost_until", 0) or 0) - now_ts())
            boost_line = f"  ·  ⚡x{boost_mult:g} ({fmt_time(rem)})"

        # همسر
        marry = u.get("married_to") or 0
        marry_line = f"  ·  💖 متأهل" if marry else ""

        # لول بعدی
        if level < 10:
            nxt = level + 1
            n_neigh_need = LEVEL_THRESHOLDS[nxt - 1]
            n_pts_need = LEVEL_POINT_COST[nxt - 1]
            n_bar = progress_bar(neigh, n_neigh_need)
            p_bar = progress_bar(points, n_pts_need)
            lvl_block = (
                f"{PE('star','⭐')} <b>مسیر لول {nxt}</b>\n"
                f"   👋 {n_bar} <code>{neigh}/{n_neigh_need}</code>\n"
                f"   💎 {p_bar} <code>{fmt_num(points)}/{fmt_num(n_pts_need)}</code>"
            )
        else:
            lvl_block = f"{PE('crown','👑')} <b>آخرین لول!</b>"

        flash_block = f"{flash}\n\n" if flash else ""

        return (
            f"{flash_block}"
            f"{PE('sparkle','✨')} <b>پروفایل یونیکورن</b>\n"
            f"{DIV}\n"
            f"{face} <b>{skin_emoji} {h(u.get('name') or '—')}</b>\n"
            f"{PE('crown','👑')} {LEVEL_NAMES[level-1]}  ·  <code>{level}/10</code>\n"
            f"{PE('diamond','💎')} {skin_name}{marry_line}  ·  {status}\n"
            f"🍰 {hunger_bar(hunger)} <code>{hunger}%</code>\n"
            f"{DIV2}\n"
            f"{PE('gem','💎')} <b>موجودی:</b> <code>{fmt_num(points)}</code>\n"
            f"{PE('gift','🎁')} <b>در تولید:</b> <code>{fmt_num(pending)}</code>\n"
            f"{PE('bolt','⚡')} <b>سرعت:</b> <code>{per_hour:.0f}/س</code>{boost_line}\n"
            f"{PE('wave','👋')} <b>نیه:</b> <code>{neigh}</code>\n"
            f"{DIV2}\n"
            f"{lvl_block}\n\n"
            f"{PE('rocket','🚀')} <i>نیه بزن → برداشت کن!</i>"
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
                flash=f"{PE('cross','❌')} <b>قهره!</b> اول غذا بده 💔")
            return

        last = u.get("last_neigh") or 0
        if last and ts - last < NEIGH_COOLDOWN_SEC:
            rem = NEIGH_COOLDOWN_SEC - (ts - last)
            await self._show_profile(uid, event.chat_id, reply_to=event.id,
                flash=f"⏰ <b>تازه نیه کشیدی!</b> تا <code>{fmt_time(rem)}</code> دیگه صبر کن 💤")
            return

        reward = random.randint(NEIGH_REWARD_MIN, NEIGH_REWARD_MAX)
        level = max(1, min(10, u.get("level") or 1))
        if level >= 8:
            reward *= 2
        elif level >= 5:
            reward = int(reward * 1.5)

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

        visuals = ["🦄💖", "🌈✨", "💫🌟", "🎀💝", "🌙⭐", "🦄💫", "💖✨", "🌸🦄"]
        v = random.choice(visuals)
        flash = (f"{v} <b>نیـه‌ه‌ه!</b>  <code>+{fmt_num(reward)}</code>\n"
                 f"{PE('gem','💎')} موجودی: <code>{fmt_num(new_points)}</code>")

        if leveled:
            nxt = leveled["new_level"]
            flash += (f"\n\n{PE('party','🎉')} <b>لول آپ → {nxt}</b>\n"
                      f"🔓 {LEVEL_UNLOCKS[nxt-1]}")

        if new_ach:
            names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}" for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} {names}"

        await self._show_profile(uid, event.chat_id, reply_to=event.id, flash=flash)

    def _check_levelup(self, uid, u):
        if not u:
            return None
        level = max(1, min(10, u.get("level") or 1))
        if level >= 10:
            return None
        neigh = u.get("neigh_count") or 0
        points = u.get("points") or 0
        nxt = level + 1
        if neigh >= LEVEL_THRESHOLDS[nxt - 1] and points >= LEVEL_POINT_COST[nxt - 1]:
            self.update(uid, level=nxt, points=points - LEVEL_POINT_COST[nxt - 1])
            return {"new_level": nxt}
        return None

    # ═══════════════ FEED ═══════════════
    async def _do_feed(self, uid, chat_id, reply_to=None):
        u = self.get_unicorn(uid)
        if not u:
            return
        hunger = u.get("hunger", 100)
        points = u.get("points") or 0
        if hunger >= 100:
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{PE('check','✅')} سیر کامله! 🌸")
            return
        if points < FEED_COST:
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{PE('cross','❌')} پوینت کمه! نیاز: <code>{fmt_num(FEED_COST)}</code>")
            return
        new_h = min(100, hunger + FEED_HUNGER_BOOST)
        new_pts = points - FEED_COST
        self.update(uid, hunger=new_h, points=new_pts, angry=0,
                    last_feed=now_ts(), total_fed=(u.get("total_fed") or 0) + 1,
                    last_hunger_tick=now_ts())
        v = random.choice(["🍰🍬", "🧁🍭", "🍪🍩", "🎂🌸", "🍯💖"])
        await self._show_profile(uid, chat_id, reply_to=reply_to,
            flash=f"{v} <b>نوم‌نوم!</b> سیری: <code>{new_h}%</code>")

    # ═══════════════ WITHDRAW ═══════════════
    async def _do_withdraw(self, uid, chat_id, reply_to=None):
        u = self.get_unicorn(uid)
        if not u:
            return
        try:
            self._tick_one(u, now_ts())
            u = self.get_unicorn(uid) or u
        except Exception:
            pass
        pending = int(u.get("pending") or 0)
        if pending < 1:
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{PE('info','ℹ️')} چیزی برای برداشت نیست! 🦄")
            return
        if u.get("angry"):
            await self._show_profile(uid, chat_id, reply_to=reply_to,
                flash=f"{PE('cross','❌')} قهره! اول غذا بده 💔")
            return
        new_pts = (u.get("points") or 0) + pending
        new_tot = (u.get("total_earned") or 0) + pending
        self.update(uid, points=new_pts, pending=0, total_earned=new_tot,
                    last_produce=now_ts())
        new_ach = self.check_achievements(uid)
        flash = f"{PE('gift','🎁')} <b>برداشت!</b> <code>+{fmt_num(pending)}</code>"
        if new_ach:
            names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}" for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} {names}"
        await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)

    # ═══════════════ DAILY ═══════════════
    async def _do_daily(self, uid, chat_id, reply_to=None, edit_msg=None):
        u = self.get_unicorn(uid)
        if not u:
            return
        ts = now_ts()
        last = u.get("last_daily") or 0
        if last and ts - last < DAILY_COOLDOWN_SEC:
            rem = DAILY_COOLDOWN_SEC - (ts - last)
            msg = f"⏰ <b>پاداش بعدی:</b> <code>{fmt_time(rem)}</code> دیگه"
            if edit_msg:
                await self._safe_edit_msg(chat_id, edit_msg, msg,
                    buttons=self._profile_buttons(uid))
            elif reply_to:
                await self._show_profile(uid, chat_id, reply_to=reply_to, flash=msg)
            return

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
                 f"🔥 استریک: <code>{streak}</code>  ·  "
                 f"{PE('gem','💎')} <code>+{fmt_num(reward)}</code>")
        if new_ach:
            names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}" for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} {names}"

        if edit_msg:
            try:
                u2 = self.get_unicorn(uid)
                text = self._render_profile(u2, flash=flash)
                await self._safe_edit_msg(chat_id, edit_msg, text,
                    buttons=self._profile_buttons(uid))
            except Exception:
                pass
        else:
            await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)

    # ═══════════════ SPIN ═══════════════
    async def _do_spin(self, uid, chat_id, reply_to=None, edit_msg=None):
        u = self.get_unicorn(uid)
        if not u:
            return
        ts = now_ts()
        last = u.get("last_spin") or 0
        if last and ts - last < SPIN_COOLDOWN_SEC:
            rem = SPIN_COOLDOWN_SEC - (ts - last)
            msg = f"🎰 <b>گردونه آماده نیست!</b>\n⏰ <code>{fmt_time(rem)}</code> دیگه"
            if edit_msg:
                await self._safe_edit_msg(chat_id, edit_msg, msg,
                    buttons=self._profile_buttons(uid))
            elif reply_to:
                await self._show_profile(uid, chat_id, reply_to=reply_to, flash=msg)
            return

        total_w = sum(r[4] for r in SPIN_REWARDS)
        pick = random.randint(1, total_w)
        acc = 0
        chosen = SPIN_REWARDS[0]
        for r in SPIN_REWARDS:
            acc += r[4]
            if pick <= acc:
                chosen = r
                break

        emoji, label, kind, val, _ = chosen
        flash = f"🎰 <b>گردونه!</b>\n{emoji} {label}"

        upd = {"last_spin": ts, "spin_count": (u.get("spin_count") or 0) + 1}
        if kind == "points":
            upd["points"] = (u.get("points") or 0) + val
            upd["total_earned"] = (u.get("total_earned") or 0) + val
            flash += f"\n{PE('gem','💎')} <code>+{fmt_num(val)}</code>"
        elif kind.startswith("boost"):
            parts = kind.split("_")
            mult = int(parts[0].replace("boost", ""))
            dur = int(parts[1])
            upd["boost_mult"] = float(mult)
            upd["boost_until"] = ts + dur
            flash += f"\n{PE('bolt','⚡')} x{mult} برای {dur//60} دقیقه!"
        elif kind == "hunger":
            upd["hunger"] = 100
            upd["angry"] = 0
            upd["last_hunger_tick"] = ts
            flash += "\n🍰 سیری فول شد!"
        elif kind == "egg":
            upd["eggs"] = (u.get("eggs") or 0) + 1
            flash += "\n🥚 یه تخم گرفتی!"

        self.update(uid, **upd)
        new_ach = self.check_achievements(uid)
        if new_ach:
            names = " · ".join([f"{ACHIEVEMENTS[k][0]} {ACHIEVEMENTS[k][1]}" for k in new_ach[:3]])
            flash += f"\n\n{PE('trophy','🏆')} {names}"

        if edit_msg:
            try:
                u2 = self.get_unicorn(uid)
                text = self._render_profile(u2, flash=flash)
                await self._safe_edit_msg(chat_id, edit_msg, text,
                    buttons=self._profile_buttons(uid))
            except Exception:
                pass
        else:
            await self._show_profile(uid, chat_id, reply_to=reply_to, flash=flash)

    # ═══════════════ TRANSFER ═══════════════
    async def _handle_transfer(self, event, uid, raw):
        try:
            m = re.search(r"(\d+(?:[.,]\d+)?\s*[kmbKMB]?)",
                          raw.replace("انتقال", "").replace("یونیکورن", ""))
            if not m:
                await self._safe_send(event.chat_id,
                    "⚠️ فرمت: ریپلای + <code>انتقال یونیکورن 100k</code>",
                    parse_mode="html", reply_to=event.id)
                return
            amount = parse_amount(m.group(1))
            if not amount or amount < 1:
                await self._safe_send(event.chat_id, "❌ مقدار نامعتبر!",
                    parse_mode="html", reply_to=event.id)
                return

            rm = await event.get_reply_message()
            if not rm:
                return
            to_uid = rm.sender_id
            if to_uid == uid:
                await self._safe_send(event.chat_id, "❌ به خودت نمی‌تونی!",
                    parse_mode="html", reply_to=event.id)
                return

            su = self.get_unicorn(uid) or self.get_or_create(uid, "—")
            if (su.get("points") or 0) < amount:
                await self._safe_send(event.chat_id,
                    f"❌ پوینت کافی نداری!\nداری: <code>{fmt_num(su.get('points', 0))}</code>",
                    parse_mode="html", reply_to=event.id)
                return

            try:
                s = await self.client.get_entity(to_uid)
                to_name = user_name(s)
            except Exception:
                to_name = str(to_uid)
            self.get_or_create(to_uid, to_name)
            tu = self.get_unicorn(to_uid)

            self.update(uid, points=(su.get("points") or 0) - amount)
            self.update(to_uid, points=(tu.get("points") or 0) + amount)
            c = self._c()
            c.execute("INSERT INTO unicorn_transfers (from_id, to_id, amount, at) VALUES (%s,%s,%s,%s)",
                      (uid, to_uid, amount, now_ts()))
            self.check_achievements(uid)
            self.check_achievements(to_uid)

            try:
                so = await event.get_sender()
                fname = user_name(so)
            except Exception:
                fname = str(uid)

            await self._safe_send(event.chat_id,
                f"{PE('rocket','🚀')} <b>انتقال موفق!</b>\n"
                f"{DIV}\n"
                f"👤 <a href=\"tg://user?id={uid}\">{h(fname)}</a>\n"
                f"   ⬇️ <code>{fmt_num(amount)}</code>\n"
                f"🎯 <a href=\"tg://user?id={to_uid}\">{h(to_name)}</a>",
                parse_mode="html", reply_to=event.id)
        except Exception as e:
            logger.exception(f"transfer: {e}")

    # ═══════════════ BATTLE ═══════════════
    async def _handle_battle(self, event, uid):
        rm = await event.get_reply_message()
        if not rm:
            return
        target = rm.sender_id
        if target == uid:
            await self._safe_send(event.chat_id, "❌ با خودت نمی‌تونی بجنگی!",
                parse_mode="html", reply_to=event.id)
            return

        try:
            ts = await self.client.get_entity(target)
            tname = user_name(ts)
        except Exception:
            tname = str(target)
        self.get_or_create(target, tname)
        a = self.get_unicorn(uid)
        b = self.get_unicorn(target)

        if a.get("angry") or b.get("angry"):
            await self._safe_send(event.chat_id, "❌ یه یونیکورن قهره! اول غذا بدین.",
                parse_mode="html", reply_to=event.id)
            return

        a_pow = ((a.get("level") or 1) * 100 + (a.get("neigh_count") or 0) +
                 (a.get("battles_won") or 0) * 20 + random.randint(0, 200))
        b_pow = ((b.get("level") or 1) * 100 + (b.get("neigh_count") or 0) +
                 (b.get("battles_won") or 0) * 20 + random.randint(0, 200))

        a_name = h(a.get("name") or "—")
        b_name = h(b.get("name") or "—")

        if a_pow >= b_pow:
            winner, loser = a, b
            winner_uid, loser_uid = uid, target
        else:
            winner, loser = b, a
            winner_uid, loser_uid = target, uid
        reward = min(1000 + (winner.get("level") or 1) * 300, 10000)

        self.update(winner_uid,
                    points=(winner.get("points") or 0) + reward,
                    total_earned=(winner.get("total_earned") or 0) + reward,
                    battles_won=(winner.get("battles_won") or 0) + 1)
        self.update(loser_uid, battles_lost=(loser.get("battles_lost") or 0) + 1)
        c = self._c()
        c.execute("INSERT INTO unicorn_battles (winner_id, loser_id, amount, at) VALUES (%s,%s,%s,%s)",
                  (winner_uid, loser_uid, reward, now_ts()))
        self.check_achievements(winner_uid)
        self.check_achievements(loser_uid)

        await self._safe_send(event.chat_id,
            f"🥊 <b>نـبـرد!</b>\n"
            f"{DIV}\n"
            f"🦄 <a href=\"tg://user?id={uid}\">{a_name}</a> vs "
            f"🦄 <a href=\"tg://user?id={target}\">{b_name}</a>\n"
            f"⚔️ <code>{a_pow}</code> vs <code>{b_pow}</code>\n"
            f"{DIV2}\n"
            f"👑 <b>برنده:</b> <a href=\"tg://user?id={winner_uid}\">{h(winner.get('name') or '—')}</a>\n"
            f"🎁 <code>+{fmt_num(reward)}</code>",
            parse_mode="html", reply_to=event.id)

    # ═══════════════ MARRY ═══════════════
    async def _handle_marry(self, event, uid):
        rm = await event.get_reply_message()
        if not rm:
            return
        target = rm.sender_id
        if target == uid:
            await self._safe_send(event.chat_id, "❌ با خودت نمی‌تونی!",
                parse_mode="html", reply_to=event.id)
            return

        try:
            ts = await self.client.get_entity(target)
            tname = user_name(ts)
        except Exception:
            tname = str(target)
        self.get_or_create(target, tname)
        a = self.get_unicorn(uid)
        b = self.get_unicorn(target)

        if a.get("married_to") and a.get("married_to") != 0:
            await self._safe_send(event.chat_id, "❌ تو الان متأهلی!",
                parse_mode="html", reply_to=event.id)
            return
        if b.get("married_to") and b.get("married_to") != 0:
            await self._safe_send(event.chat_id, "❌ یونیکورن اون متأهله!",
                parse_mode="html", reply_to=event.id)
            return

        self.update(uid, married_to=target, married_at=now_ts())
        self.update(target, married_to=uid, married_at=now_ts())
        self.check_achievements(uid)
        self.check_achievements(target)

        await self._safe_send(event.chat_id,
            f"💍 <b>ازدواج یـونـیـکـورنـی!</b>\n"
            f"{DIV}\n\n"
            f"🌸 <a href=\"tg://user?id={uid}\">{h(a.get('name') or '—')}</a> "
            f"{PE('heart','💖')} "
            f"<a href=\"tg://user?id={target}\">{h(b.get('name') or '—')}</a>\n\n"
            f"🎉 حالا با «تخم» پرورش بدید!",
            parse_mode="html", reply_to=event.id)

    # ═══════════════ BREED ═══════════════
    async def _handle_breed(self, event, uid):
        u = self.get_unicorn(uid)
        if not u:
            return
        marr = u.get("married_to") or 0
        if not marr:
            await self._safe_send(event.chat_id,
                f"❌ <b>اول ازدواج کن!</b>\nریپلای کن و بنویس <code>ازدواج</code> 💍",
                parse_mode="html", reply_to=event.id)
            return

        ts = now_ts()
        if not hasattr(self, "_last_breed_cache"):
            self._last_breed_cache = {}
        last_breed_at = self._last_breed_cache.get(uid, 0)
        if ts - last_breed_at < 6 * 3600:
            rem = 6 * 3600 - (ts - last_breed_at)
            await self._safe_send(event.chat_id,
                f"🥚 <b>هنوز آماده نیست!</b>\n⏰ <code>{fmt_time(rem)}</code>",
                parse_mode="html", reply_to=event.id)
            return

        self._last_breed_cache[uid] = ts
        cost = 5000
        if (u.get("points") or 0) < cost:
            await self._safe_send(event.chat_id,
                f"❌ برای پرورش <code>{fmt_num(cost)}</code> لازمه!",
                parse_mode="html", reply_to=event.id)
            return

        self.update(uid, points=(u.get("points") or 0) - cost,
                    eggs=(u.get("eggs") or 0) + 1)
        mu = self.get_unicorn(marr)
        if mu:
            self.update(marr, eggs=(mu.get("eggs") or 0) + 1)
        self.add_achievement(uid, "breeder")

        await self._safe_send(event.chat_id,
            f"👶 <b>تـخـم جـدیـد!</b> 🥚\n"
            f"{DIV}\n\n"
            f"🥚 تخم‌های تو: <code>{(u.get('eggs') or 0) + 1}</code>\n"
            f"💕 همسرت هم یه تخم گرفت!",
            parse_mode="html", reply_to=event.id)

    # ═══════════════ FULL STATS ═══════════════
    async def _show_full_stats(self, chat_id, uid, reply_to=None):
        u = self.get_unicorn(uid)
        if not u:
            return
        try:
            self._tick_one(u, now_ts())
            u = self.get_unicorn(uid) or u
        except Exception:
            pass

        level = max(1, min(10, u.get("level") or 1))
        rate = LEVEL_RATES[level - 1]
        per_hour = rate * 3600
        per_day = per_hour * 24
        skin_e, skin_n, _ = SKINS.get(u.get("color") or "classic", SKINS["classic"])
        face = hunger_face(u.get("hunger", 100), u.get("angry", 0))
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception:
            ach = []

        ach_lines = []
        for k, (emoji, name, desc) in ACHIEVEMENTS.items():
            mark = "✅" if k in ach else "🔒"
            ach_lines.append(f"  {mark} {emoji} {name}")
        ach_text = "\n".join(ach_lines)

        marry = u.get("married_to") or 0
        marry_val = (f"<a href=\"tg://user?id={marry}\">متأهل</a>"
                     if marry else "<i>مجرد</i>")

        text = (
            f"{PE('chart','📊')} <b>آمـار کـامـل</b>\n"
            f"{DIV}\n"
            f"{face} <b>{skin_e} <a href=\"tg://user?id={uid}\">{h(u.get('name') or '—')}</a></b>\n"
            f"{PE('crown','👑')} {LEVEL_NAMES[level-1]}  ·  <code>Lv{level}/10</code>\n"
            f"{PE('diamond','💎')} اسکین: <b>{skin_n}</b>\n"
            f"{DIV2}\n"
            f"{PE('gem','💎')} موجودی: <code>{fmt_num(u.get('points', 0))}</code>\n"
            f"{PE('trophy','🏆')} کل درآمد: <code>{fmt_num(u.get('total_earned', 0))}</code>\n"
            f"{PE('gift','🎁')} در تولید: <code>{fmt_num(int(u.get('pending') or 0))}</code>\n"
            f"{PE('bolt','⚡')} تولید: <code>{per_hour:.0f}/س</code> ≈ <code>{fmt_num(per_day)}/روز</code>\n"
            f"{PE('wave','👋')} نیه: <code>{u.get('total_neigh_ever', 0)}</code> (فعلی {u.get('neigh_count', 0)})\n"
            f"🍰 سیری: <code>{u.get('hunger', 100)}%</code>  ·  🍽 غذا: <code>{u.get('total_fed', 0)}</code>\n"
            f"{DIV2}\n"
            f"🎁 استریک: <code>{u.get('daily_streak', 0)}</code> (رکورد {u.get('daily_best', 0)})\n"
            f"🎰 گردونه: <code>{u.get('spin_count', 0)}</code>  ·  "
            f"🥊 برد/باخت: <code>{u.get('battles_won', 0)}/{u.get('battles_lost', 0)}</code>\n"
            f"💍 همسر: {marry_val}  ·  🥚 تخم: <code>{u.get('eggs', 0)}</code>\n"
            f"🏆 دستاورد: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>\n"
            f"{DIV2}\n"
            f"{PE('trophy','🏆')} <b>دستاوردها:</b>\n{ach_text}\n\n"
            f"{PE('sparkle','✨')} <i>ادامه بده تا افسانه‌ای بشی!</i>"
        )

        if len(text) > 4000:
            chunks = [text[i:i+3500] for i in range(0, len(text), 3500)]
            first = True
            for c in chunks:
                kwargs = {"parse_mode": "html"}
                if first and reply_to:
                    kwargs["reply_to"] = reply_to
                try:
                    await self._safe_send(chat_id, c, **kwargs)
                    await asyncio.sleep(0.4)
                    first = False
                except Exception:
                    pass
        else:
            kwargs = {"parse_mode": "html"}
            if reply_to:
                kwargs["reply_to"] = reply_to
            try:
                await self._safe_send(chat_id, text, **kwargs)
            except Exception as e:
                logger.warning(f"stats send: {e}")

    # ═══════════════ CALLBACK ═══════════════
    async def on_callback(self, event):
        try:
            data = event.data.decode("utf-8", "ignore")
            if not data.startswith("uni:"):
                return
            uid = event.sender_id
            parts = data.split(":")
            action = parts[1]

            if action in ("feed", "withdraw", "daily", "spin", "skins", "ach",
                          "home", "stats", "refresh"):
                target = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else uid
                if target != uid:
                    await event.answer("⛔ این پروفایل مال تو نیست!", alert=True)
                    return

            if action == "refresh":
                await event.answer("🔄")
                u = self.get_unicorn(uid)
                if u:
                    try:
                        self._tick_one(u, now_ts())
                    except Exception:
                        pass
                await self._show_profile(uid, event.chat_id, force_new=False)
                return

            if action == "feed":
                await event.answer("🍰")
                await self._do_feed(uid, event.chat_id)
                return

            if action == "withdraw":
                await event.answer("💰")
                await self._do_withdraw(uid, event.chat_id)
                return

            if action == "daily":
                await event.answer("🎁")
                await self._do_daily(uid, event.chat_id, edit_msg=event.message_id)
                return

            if action == "spin":
                await event.answer("🎰")
                await self._do_spin(uid, event.chat_id, edit_msg=event.message_id)
                return

            if action == "skins":
                await event.answer()
                await self._show_skins(event, uid)
                return

            if action == "ach":
                await event.answer()
                await self._show_achievements(event, uid)
                return

            if action == "home":
                await event.answer()
                await self._show_home(event, uid)
                return

            if action == "stats":
                await event.answer()
                await self._show_full_stats(event.chat_id, uid, reply_to=event.message_id)
                return

            if action == "buyskin":
                await event.answer()
                key = parts[2]
                await self._buy_skin(event, uid, key)
                return

            if action == "back":
                await event.answer()
                await self._show_profile(uid, event.chat_id, force_new=False)
                return

        except Exception as e:
            logger.exception(f"uni cb: {e}")
            try:
                await event.answer("خطا!", alert=True)
            except Exception:
                pass

    # ═══════════════ SKINS UI ═══════════════
    async def _show_skins(self, event, uid):
        u = self.get_unicorn(uid)
        if not u:
            return
        cur = u.get("color") or "classic"
        pts = u.get("points") or 0
        lines = [
            f"{PE('diamond','💎')} <b>رنگ‌های یونیکورن</b>",
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
        btns = []
        row = []
        for k, (em, name, cost) in SKINS.items():
            if k == cur:
                continue
            row.append(Button.inline(f"{em} {name}", data=f"uni:buyskin:{k}".encode()))
            if len(row) == 2:
                btns.append(row)
                row = []
        if row:
            btns.append(row)
        btns.append([Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())])
        await self._safe_edit_msg(event.chat_id, event.message_id,
            "\n".join(lines), buttons=btns)

    async def _buy_skin(self, event, uid, key):
        if key not in SKINS:
            return
        u = self.get_unicorn(uid)
        if not u:
            return
        em, name, cost = SKINS[key]
        if (u.get("points") or 0) < cost:
            await event.answer(f"❌ پوینت کمه! ({fmt_num(cost)})", alert=True)
            return
        self.update(uid, points=(u.get("points") or 0) - cost, color=key)
        await event.answer(f"✅ {name} فعال شد!")
        u2 = self.get_unicorn(uid)
        text = self._render_profile(u2, flash=f"✅ اسکین <b>{name}</b> فعال شد! {em}")
        await self._safe_edit_msg(event.chat_id, event.message_id, text,
            buttons=self._profile_buttons(uid))

    async def _show_achievements(self, event, uid):
        u = self.get_unicorn(uid)
        if not u:
            return
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception:
            ach = []
        lines = [
            f"{PE('trophy','🏆')} <b>دستاوردها</b>",
            f"{DIV}",
            f"✅ باز شده: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>",
            f"{DIV2}",
        ]
        for k, (em, name, desc) in ACHIEVEMENTS.items():
            if k in ach:
                lines.append(f"  ✅ {em} <b>{name}</b>")
            else:
                lines.append(f"  🔒 {em} <s>{name}</s>")
        btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
        await self._safe_edit_msg(event.chat_id, event.message_id,
            "\n".join(lines), buttons=btns)

    async def _show_home(self, event, uid):
        u = self.get_unicorn(uid)
        if not u:
            return
        try:
            self._tick_one(u, now_ts())
            u = self.get_unicorn(uid) or u
        except Exception:
            pass
        level = max(1, min(10, u.get("level") or 1))
        skin_e, skin_n, _ = SKINS.get(u.get("color") or "classic", SKINS["classic"])
        face = hunger_face(u.get("hunger", 100), u.get("angry", 0))
        marr = u.get("married_to") or 0
        try:
            ach = json.loads(u.get("achievements") or "[]")
        except Exception:
            ach = []

        decorations = "🌷🌻🌷" if level < 3 else "🌹🌸🌺" if level < 6 else "🌌✨🌟"

        lines = [
            f"🏠 <b>خـانـه‌ی یـونـیـکـورن</b>",
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
            lines.append(f"💖 همسر: <a href=\"tg://user?id={marr}\">متأهل</a>")
        else:
            lines.append("💖 مجرد")
        lines.append(f"🥚 تخم: <code>{u.get('eggs', 0)}</code>")
        lines.append(f"🏆 دستاورد: <code>{len(ach)}/{len(ACHIEVEMENTS)}</code>")

        btns = [[Button.inline("🔙 بازگشت", data=f"uni:back:{uid}".encode())]]
        await self._safe_edit_msg(event.chat_id, event.message_id,
            "\n".join(lines), buttons=btns)


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