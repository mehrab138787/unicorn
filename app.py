# -*- coding: utf-8 -*-
"""
✨ UNICORN ANONY BOT — Web Service + PostgreSQL ✨
"""

import os
import re
import csv
import io
import json
import asyncio
import logging
from datetime import datetime, timedelta, timezone

import socks
import requests
import psycopg2
import psycopg2.extras
from aiohttp import web
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.errors import MessageNotModifiedError, FloodWaitError

load_dotenv()

API_ID = int(os.getenv("API_ID", "6") or 6)
API_HASH = os.getenv("API_HASH", "eb06d4abfb49dc3eeb1aeb98ae0f581e").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

# ═════════════════════════════════════════════
# 👥 ادمین‌ها (کل = ۴ نفر)
# ═════════════════════════════════════════════
# OWNER_ID = ادمین اصلی (۱ نفر)
# ADMIN_IDS = ۳ ادمین دیگه (با کاما جدا کن)
# مثال توی .env: ADMIN_IDS=123456789,987654321,555555555
_admins_str = os.getenv("ADMIN_IDS", "").strip()
EXTRA_ADMINS = [int(x) for x in _admins_str.split(",") if x.strip().isdigit()]
ALL_ADMINS = set([OWNER_ID] + EXTRA_ADMINS)
ALL_ADMINS.discard(0)

# ═════════════════════════════════════════════
# 🗄️ PostgreSQL
# ═════════════════════════════════════════════
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# اضافه کردن SSL برای Render اگه نبود
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

# ═════════════════════════════════════════════
# 🎨 ایموجی‌های پرمیوم
# ═════════════════════════════════════════════
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
    "medal": "5458603043203327669",
    "skip": "5424972470023104089",
}


def E(key, fallback):
    eid = PREMIUM.get(key)
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback


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


MAX_ANSWER_LEN = 1500

TEMPLATES = [
    ("💎 صادق‌ترین نظرت", "صادق‌ترین نظرت درباره من چیه؟"),
    ("💎 بدترین خصلت من", "بدترین خصلت من چیه که باید تغییرش بدم؟"),
    ("💎 بهترین خاطره", "بهترین خاطره‌ای که با من داری چیه؟"),
    ("💎 اولین برداشت", "اولین برداشتی که از من داشتی چی بود؟"),
    ("💎 اگه یه آرزو", "اگه یه آرزو داشتی، چی بود؟"),
    ("💎 راز نگفته", "چی رو همیشه می‌خواستی بهم بگی ولی نگفتی؟"),
]

# ═════════════════════════════════════════════
# 🧠 AI
# ═════════════════════════════════════════════
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

AI_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "llama-3.1-8b-instant",
]

QUIZ_CATEGORIES = [
    ("book", "📖", "تاریخی"),
    ("ball", "⚽", "ورزشی"),
    ("star", "🌟", "دینی"),
    ("bolt", "⚡", "علمی"),
    ("globe", "🌍", "جغرافیایی"),
    ("movie", "🎬", "سینما"),
    ("music", "🎵", "موسیقی"),
    ("book", "📚", "ادبیات"),
    ("laptop", "💻", "فناوری"),
    ("brain", "🧠", "عمومی"),
]

QUIZ_TIME_OPTIONS = [15, 30, 45, 60]
QUIZ_Q_OPTIONS = [3, 5, 7, 10]
QUIZ_TARGET_OPTIONS = [0, 5, 10, 15, 20]

SETUP_GAMES = {}
ACTIVE_GAMES = {}


async def ai_generate_question(category: str):
    import random

    sys_msg = (
        "You are a professional Persian quiz maker for Telegram group games. "
        "Always respond with ONLY a valid JSON object (no markdown):\n"
        '{"question": "متن سوال", "options": ["گزینه1","گزینه2","گزینه3","گزینه4"], "correct": 0}\n'
        "Rules:\n"
        "- All text in Persian (Farsi).\n"
        "- 'correct' = 0-based index of the correct option.\n"
        "- Exactly 4 options, each concise (max 6 words).\n"
        "- Factual, interesting, medium-to-hard difficulty.\n"
        "- Ensure only ONE option is correct.\n"
        "- IMPORTANT: Place the correct answer at a RANDOM position.\n"
    )
    user_msg = f"یک سوال چهارگزینه‌ای جذاب از دسته «{category}» بساز."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    def _call(model, temperature):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=35)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}")
        return r.json()

    last_err = None
    for model in AI_MODELS:
        for attempt in range(2):
            try:
                temp = 0.9 if attempt == 0 else 1.1
                data = await asyncio.to_thread(_call, model, temp)
                content = data["choices"][0]["message"]["content"]
                obj = json.loads(content)
                opts = obj.get("options")
                if not isinstance(opts, list) or len(opts) != 4:
                    raise ValueError("bad options")
                if not isinstance(obj.get("correct"), int) or not (0 <= obj["correct"] <= 3):
                    raise ValueError("bad correct index")
                if not obj.get("question"):
                    raise ValueError("empty question")
                opts = [str(o).strip()[:80] for o in opts]
                if len(set(opts)) < 4:
                    raise ValueError("duplicate options")

                # 🔀 شافل
                correct_text = opts[obj["correct"]]
                random.shuffle(opts)
                new_correct_idx = opts.index(correct_text)

                logger.info(f"🎲 correct: {obj['correct']}→{new_correct_idx}")

                return {
                    "question": str(obj["question"]).strip()[:400],
                    "options": opts,
                    "correct": new_correct_idx,
                }
            except Exception as e:
                last_err = e
                await asyncio.sleep(0.4)
                continue
    logger.error(f"all AI models failed: {last_err}")
    return None


# ═════════════════════════════════════════════
# 💾 PostgreSQL DB
# ═════════════════════════════════════════════
class DB:
    def __init__(self, dsn):
        self.dsn = dsn
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True
        self._create()
        self._migrate()
        logger.info("✅ PostgreSQL connected")

    def _c(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _create(self):
        c = self._c()
        c.execute("""CREATE TABLE IF NOT EXISTS groups (
            group_id BIGINT PRIMARY KEY, title TEXT, username TEXT, last_seen TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS challenges (
            id BIGSERIAL PRIMARY KEY, admin_id BIGINT, group_id BIGINT,
            title TEXT, question TEXT, message_id BIGINT, created_at TEXT,
            is_active INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS answers (
            challenge_id BIGINT, user_id BIGINT, user_name TEXT, username TEXT,
            answer TEXT, answered_at TEXT, PRIMARY KEY (challenge_id, user_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, user_name TEXT, username TEXT,
            first_seen TEXT, last_seen TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS scores (
            user_id BIGINT PRIMARY KEY, user_name TEXT, points INTEGER DEFAULT 0,
            challenges_joined INTEGER DEFAULT 0, ngl_received INTEGER DEFAULT 0,
            ngl_sent INTEGER DEFAULT 0, last_active TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS anon_messages (
            id BIGSERIAL PRIMARY KEY, target_id BIGINT, sender_id BIGINT,
            text TEXT, sent_at TEXT, is_read INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS poll_votes (
            challenge_id BIGINT, user_id BIGINT, user_name TEXT,
            option_index INTEGER, voted_at TEXT,
            PRIMARY KEY (challenge_id, user_id))""")

    def _migrate(self):
        c = self._c()
        c.execute("""SELECT column_name FROM information_schema.columns
                     WHERE table_name='challenges'""")
        cols = {r["column_name"] for r in c.fetchall()}
        for col, ddl in [
            ("ch_type", "ALTER TABLE challenges ADD COLUMN ch_type TEXT DEFAULT 'text'"),
            ("options", "ALTER TABLE challenges ADD COLUMN options TEXT"),
            ("deadline", "ALTER TABLE challenges ADD COLUMN deadline TEXT"),
            ("results_announced", "ALTER TABLE challenges ADD COLUMN results_announced INTEGER DEFAULT 0"),
        ]:
            if col not in cols:
                try:
                    self._c().execute(ddl)
                except Exception:
                    pass

    def save_group(self, gid, title, username=None):
        self._c().execute("""INSERT INTO groups (group_id, title, username, last_seen)
            VALUES (%s, %s, %s, %s) ON CONFLICT(group_id) DO UPDATE SET
            title=EXCLUDED.title, username=EXCLUDED.username, last_seen=EXCLUDED.last_seen""",
            (gid, title, username, now_iso()))

    def get_groups(self):
        c = self._c()
        c.execute("SELECT * FROM groups ORDER BY last_seen DESC")
        return [dict(r) for r in c.fetchall()]

    def save_user(self, uid, uname, username=None):
        self._c().execute("""INSERT INTO users (user_id, user_name, username, first_seen, last_seen)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT(user_id) DO UPDATE SET
            user_name=EXCLUDED.user_name, username=EXCLUDED.username, last_seen=EXCLUDED.last_seen""",
            (uid, uname, username, now_iso(), now_iso()))

    def get_all_users(self):
        c = self._c()
        c.execute("SELECT user_id FROM users")
        return [r["user_id"] for r in c.fetchall()]

    def count_users(self):
        c = self._c()
        c.execute("SELECT COUNT(*) AS n FROM users")
        return c.fetchone()["n"]

    def create_challenge(self, admin_id, group_id, title, question,
                         ch_type="text", options=None, deadline=None):
        c = self._c()
        c.execute("""INSERT INTO challenges
            (admin_id, group_id, title, question, created_at, ch_type, options, deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (admin_id, group_id, title, question, now_iso(), ch_type,
             json.dumps(options, ensure_ascii=False) if options else None, deadline))
        return c.fetchone()["id"]

    def set_challenge_message(self, ch_id, mid):
        self._c().execute("UPDATE challenges SET message_id=%s WHERE id=%s", (mid, ch_id))

    def get_challenge(self, ch_id):
        c = self._c()
        c.execute("SELECT * FROM challenges WHERE id=%s", (ch_id,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_challenges(self, admin_id=None):
        c = self._c()
        if admin_id:
            c.execute("SELECT * FROM challenges WHERE admin_id=%s ORDER BY id DESC", (admin_id,))
        else:
            c.execute("SELECT * FROM challenges ORDER BY id DESC")
        return [dict(r) for r in c.fetchall()]

    def search_challenges(self, admin_id, query):
        c = self._c()
        q = f"%{query}%"
        c.execute("""SELECT * FROM challenges WHERE admin_id=%s AND
            (title ILIKE %s OR question ILIKE %s) ORDER BY id DESC""", (admin_id, q, q))
        return [dict(r) for r in c.fetchall()]

    def deactivate_challenge(self, ch_id):
        self._c().execute("UPDATE challenges SET is_active=0 WHERE id=%s", (ch_id,))

    def mark_results_announced(self, ch_id):
        self._c().execute("UPDATE challenges SET results_announced=1 WHERE id=%s", (ch_id,))

    def get_expired_challenges(self):
        c = self._c()
        c.execute("""SELECT * FROM challenges WHERE is_active=1 AND
            deadline IS NOT NULL AND deadline<=%s AND results_announced=0""", (now_iso(),))
        return [dict(r) for r in c.fetchall()]

    def count_active_challenges(self):
        c = self._c()
        c.execute("SELECT COUNT(*) AS n FROM challenges WHERE is_active=1")
        return c.fetchone()["n"]

    def save_answer(self, ch_id, uid, uname, username, answer):
        self._c().execute("""INSERT INTO answers (challenge_id, user_id, user_name, username, answer, answered_at)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT(challenge_id, user_id) DO UPDATE SET
            answer=EXCLUDED.answer, answered_at=EXCLUDED.answered_at,
            user_name=EXCLUDED.user_name, username=EXCLUDED.username""",
            (ch_id, uid, uname, username, answer, now_iso()))

    def get_answers(self, ch_id):
        c = self._c()
        c.execute("SELECT * FROM answers WHERE challenge_id=%s ORDER BY answered_at DESC", (ch_id,))
        return [dict(r) for r in c.fetchall()]

    def has_answered(self, ch_id, uid):
        c = self._c()
        c.execute("SELECT 1 FROM answers WHERE challenge_id=%s AND user_id=%s", (ch_id, uid))
        return c.fetchone() is not None

    def count_answers(self, ch_id):
        c = self._c()
        c.execute("SELECT COUNT(*) AS n FROM answers WHERE challenge_id=%s", (ch_id,))
        return c.fetchone()["n"]

    def save_poll_vote(self, ch_id, uid, uname, idx):
        self._c().execute("""INSERT INTO poll_votes (challenge_id, user_id, user_name, option_index, voted_at)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT(challenge_id, user_id) DO UPDATE SET
            option_index=EXCLUDED.option_index, voted_at=EXCLUDED.voted_at""",
            (ch_id, uid, uname, idx, now_iso()))

    def has_voted(self, ch_id, uid):
        c = self._c()
        c.execute("SELECT 1 FROM poll_votes WHERE challenge_id=%s AND user_id=%s", (ch_id, uid))
        return c.fetchone() is not None

    def get_poll_results(self, ch_id, n):
        c = self._c()
        c.execute("""SELECT option_index, COUNT(*) AS n FROM poll_votes
            WHERE challenge_id=%s GROUP BY option_index""", (ch_id,))
        counts = {i: 0 for i in range(n)}
        for r in c.fetchall():
            counts[r["option_index"]] = r["n"]
        return counts

    def count_poll_votes(self, ch_id):
        c = self._c()
        c.execute("SELECT COUNT(*) AS n FROM poll_votes WHERE challenge_id=%s", (ch_id,))
        return c.fetchone()["n"]

    def add_points(self, uid, uname, pts=10, joined=True, ngl=False, sent=False):
        c = self._c()
        c.execute("SELECT user_id FROM scores WHERE user_id=%s", (uid,))
        if c.fetchone() is None:
            self._c().execute("""INSERT INTO scores (user_id, user_name, points,
                challenges_joined, ngl_received, ngl_sent, last_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (uid, uname, pts, 1 if joined else 0,
                 1 if ngl else 0, 1 if sent else 0, now_iso()))
        else:
            self._c().execute("""UPDATE scores SET user_name=%s, points=points+%s,
                challenges_joined=challenges_joined+%s, ngl_received=ngl_received+%s,
                ngl_sent=ngl_sent+%s, last_active=%s WHERE user_id=%s""",
                (uname, pts, 1 if joined else 0, 1 if ngl else 0,
                 1 if sent else 0, now_iso(), uid))

    def get_score(self, uid):
        c = self._c()
        c.execute("SELECT * FROM scores WHERE user_id=%s", (uid,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_top(self, limit=10):
        c = self._c()
        c.execute("SELECT * FROM scores ORDER BY points DESC, challenges_joined DESC LIMIT %s", (limit,))
        return [dict(r) for r in c.fetchall()]

    def get_rank(self, uid):
        c = self._c()
        c.execute("SELECT points FROM scores WHERE user_id=%s", (uid,))
        r = c.fetchone()
        if not r:
            return None
        c.execute("SELECT COUNT(*) AS n FROM scores WHERE points > %s", (r["points"],))
        return c.fetchone()["n"] + 1

    def save_anon(self, target_id, sender_id, text):
        self._c().execute("""INSERT INTO anon_messages (target_id, sender_id, text, sent_at)
            VALUES (%s, %s, %s, %s)""", (target_id, sender_id, text, now_iso()))

    def get_anon_inbox(self, target_id, limit=10):
        c = self._c()
        c.execute("""SELECT * FROM anon_messages WHERE target_id=%s
            ORDER BY id DESC LIMIT %s""", (target_id, limit))
        return [dict(r) for r in c.fetchall()]

    def count_anon_received(self, target_id):
        c = self._c()
        c.execute("SELECT COUNT(*) AS n FROM anon_messages WHERE target_id=%s", (target_id,))
        return c.fetchone()["n"]

    def mark_anon_read(self, target_id):
        self._c().execute("UPDATE anon_messages SET is_read=1 WHERE target_id=%s", (target_id,))


db = DB(DATABASE_URL)

# ═════════════════════════════════════════════
# Client
# ═════════════════════════════════════════════
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


DIV = "━━━━━━━━━━━━━━━━━━━━━━━━━━"


# ═════════════════════════════════════════════
# Admin Menu
# ═════════════════════════════════════════════
async def send_admin_menu(event, edit=False):
    text = (
        f"{E('crown', '👑')} <b>پنل مدیریت UNICORN</b> {E('crown', '👑')}\n"
        f"{DIV}\n\n"
        f"{E('sparkle', '✨')} <b>سلام ادمین عزیز!</b> {E('wave', '👋')}\n\n"
        f"{E('brain', '🧠')} برای شروع کوییز، توی گروه بنویس: <code>چالش</code>\n"
        f"{E('diamond', '💎')} یا از دکمه‌های زیر استفاده کن."
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


def build_challenge_text(ch_id, title, question, ch_type, options, deadline):
    if ch_type == "poll":
        opts_txt = "\n".join([f"  {E('point', '👉')} <b>{i+1}.</b> {h(o)}"
                              for i, o in enumerate(options or [])])
        body = (f"{E('chart', '📊')} <b>نظرسنجی ناشناس</b>\n"
                f"{DIV}\n\n"
                f"{E('tag', '🏷️')} <b>عنوان:</b> {h(title)}\n\n"
                f"{E('list', '📋')} <b>گزینه‌ها:</b>\n{opts_txt}\n\n")
    else:
        body = (f"{E('diamond', '💎')} <b>چالش ناشناس</b>\n"
                f"{DIV}\n\n"
                f"{E('tag', '🏷️')} <b>عنوان:</b> {h(title)}\n\n"
                f"{E('message', '💬')} <b>سوال:</b> {h(question)}\n\n")
    extra = (f"{E('shield', '🛡')} <i>پاسخ‌ها کاملاً ناشناس</i>\n"
             f"{E('lock', '🔒')} <i>هیچ‌کس نمی‌فهمه کی جواب داده</i>\n")
    if deadline:
        try:
            extra += f"{E('hourglass', '⏳')} <b>مهلت:</b> {datetime.fromisoformat(deadline).strftime('%Y/%m/%d - %H:%M')}\n"
        except Exception:
            pass
    extra += f"\n{E('rocket', '🚀')} <b>برای شرکت روی دکمه بزن:</b>"
    return body + extra


# ═════════════════════════════════════════════
# 🎮 QUIZ ENGINE (مختصر — مثل قبل)
# ═════════════════════════════════════════════
def create_setup_game(admin_id, group_id):
    game = {
        "id": int(datetime.now(IRAN_TZ).timestamp() * 1000) % 100000000,
        "admin_id": admin_id,
        "group_id": group_id,
        "categories": [],
        "questions_per_player": 5,
        "time_per_question": 30,
        "target_score": 0,
        "players": {},
        "order": [],
        "state": "setup",
        "current_index": 0,
        "current_player": None,
        "current_state": None,
        "current_question": None,
        "join_msg_id": None,
        "turn_msg_id": None,
        "timeout_task": None,
    }
    SETUP_GAMES[admin_id] = game
    return game


def _find_game_for_callback(event):
    try:
        mid = getattr(event, "message_id", None)
        if mid:
            for g in ACTIVE_GAMES.values():
                if g.get("join_msg_id") == mid:
                    return g
                if g.get("turn_msg_id") == mid:
                    return g
                cq = g.get("current_question")
                if cq and cq.get("msg_id") == mid:
                    return g
    except Exception:
        pass
    try:
        chat_id = getattr(event, "chat_id", None)
        if chat_id and ACTIVE_GAMES.get(chat_id):
            return ACTIVE_GAMES.get(chat_id)
    except Exception:
        pass
    try:
        waiting = [g for g in ACTIVE_GAMES.values() if g.get("state") == "waiting"]
        if len(waiting) == 1:
            return waiting[0]
    except Exception:
        pass
    return None


def render_quiz_welcome(game):
    text = (
        f"{E('brain', '🧠')} <b>کوییز هوشمند UNICORN</b> {E('brain', '🧠')}\n"
        f"{DIV}\n\n"
        f"{E('sparkle', '✨')} <b>سلام ادمین عزیز!</b> {E('wave', '👋')}\n"
        f"بیا یه کوییز حرفه‌ای بسازیم.\n\n"
        f"{E('info', 'ℹ️')} <b>جریان بازی:</b>\n"
        f"  {E('gamepad', '🎮')} بازیکنان توی گروه عضو می‌شن\n"
        f"  {E('target', '🎯')} نوبتی توی گروه دسته انتخاب می‌کنن\n"
        f"  {E('brain', '🧠')} هوش مصنوعی سوال می‌سازه\n"
        f"  {E('bolt', '⚡')} درست <b>+1</b> و غلط <b>-1</b>\n"
        f"  {E('trophy', '🏆')} امتیاز هدف = برنده\n\n"
        f"{E('magic', '✨')} <i>آماده‌ای؟</i>"
    )
    buttons = [
        [Button.inline("🚀 شروع تنظیمات", data=b"quiz_setup")],
        [Button.inline("❌ لغو", data=b"quiz_cancel")],
    ]
    return text, buttons


def render_categories_menu(game):
    selected = game["categories"]
    text = (
        f"{E('target', '🎯')} <b>مرحله ۱ از ۳ — دسته‌بندی</b>\n"
        f"{DIV}\n\n"
        f"{E('info', 'ℹ️')} هر تعداد که می‌خوای انتخاب کن:\n\n"
        f"{E('list', '📋')} <b>انتخاب شده ({len(selected)}):</b>\n"
    )
    if selected:
        for c in selected:
            text += f"  {E('check', '✅')} <b>{c}</b>\n"
    else:
        text += f"  {E('cross', '➖')} <i>هنوز چیزی انتخاب نکردی</i>\n"

    buttons = []
    row = []
    for i, (key, emoji, name) in enumerate(QUIZ_CATEGORIES):
        mark = "✅" if name in selected else "◽"
        row.append(Button.inline(f"{mark} {emoji} {name}", data=f"quiz_cat:{i}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if selected:
        buttons.append([Button.inline("➡️ ادامه", data=b"quiz_settings")])
    else:
        buttons.append([Button.inline("⛔ حداقل یکی انتخاب کن", data=b"quiz_noop")])
    buttons.append([Button.inline("❌ لغو", data=b"quiz_cancel")])
    return text, buttons


def render_settings_menu(game):
    q, t, s = game["questions_per_player"], game["time_per_question"], game["target_score"]
    q_btns = [Button.inline(("✅ " if n == q else "◽ ") + str(n),
                            data=f"quiz_q:{n}".encode()) for n in QUIZ_Q_OPTIONS]
    t_btns = [Button.inline(("✅ " if n == t else "◽ ") + f"{n}s",
                            data=f"quiz_t:{n}".encode()) for n in QUIZ_TIME_OPTIONS]
    s_btns = [Button.inline(("✅ " if n == s else "◽ ") + ("♾" if n == 0 else str(n)),
                            data=f"quiz_s:{n}".encode()) for n in QUIZ_TARGET_OPTIONS]
    text = (
        f"{E('gamepad', '🎮')} <b>مرحله ۲ از ۳ — تنظیمات</b>\n"
        f"{DIV}\n\n"
        f"{E('chart', '📊')} <b>سوال هر نفر:</b> <code>{q}</code>\n"
        f"{E('hourglass', '⏳')} <b>زمان هر سوال:</b> <code>{t}</code> ثانیه\n"
        f"{E('trophy', '🏆')} <b>امتیاز هدف:</b> "
        f"{'<i>بدون هدف</i>' if s == 0 else f'<code>{s}</code>'}\n\n"
        f"{E('info', 'ℹ️')} <i>با دکمه‌ها تنظیم کن</i>"
    )
    buttons = [
        [Button.inline("— 📊 تعداد سوال —", data=b"quiz_noop")],
        q_btns,
        [Button.inline("— ⏳ زمان هر سوال —", data=b"quiz_noop")],
        t_btns,
        [Button.inline("— 🏆 امتیاز هدف —", data=b"quiz_noop")],
        s_btns,
        [Button.inline("⬅️ قبلی", data=b"quiz_backcat"),
         Button.inline("➡️ ادامه", data=b"quiz_summary")],
        [Button.inline("❌ لغو", data=b"quiz_cancel")],
    ]
    return text, buttons


def render_summary_menu(game):
    cats = "، ".join(game["categories"])
    target_txt = "بدون هدف" if game["target_score"] == 0 else f"{game['target_score']} امتیاز"
    text = (
        f"{E('check', '✅')} <b>مرحله ۳ از ۳ — خلاصه</b>\n"
        f"{DIV}\n\n"
        f"{E('brain', '🧠')} <b>کوییز هوشمند UNICORN</b>\n\n"
        f"{E('list', '📋')} <b>دسته‌ها:</b> {h(cats)}\n"
        f"{E('chart', '📊')} <b>سوال هر نفر:</b> <code>{game['questions_per_player']}</code>\n"
        f"{E('hourglass', '⏳')} <b>زمان هر سوال:</b> <code>{game['time_per_question']}</code> ثانیه\n"
        f"{E('trophy', '🏆')} <b>امتیاز هدف:</b> <code>{target_txt}</code>\n\n"
        f"{E('info', 'ℹ️')} <i>بعد از تأیید، پیام شرکت توی گروه فرستاده می‌شه</i>"
    )
    buttons = [
        [Button.inline("🚀 ایجاد بازی در گروه", data=b"quiz_create")],
        [Button.inline("⬅️ قبلی", data=b"quiz_settings")],
        [Button.inline("❌ لغو", data=b"quiz_cancel")],
    ]
    return text, buttons


async def quiz_send_setup_menu(admin_id, screen="welcome", game=None):
    if game is None:
        game = SETUP_GAMES.get(admin_id)
    if not game:
        return
    if screen == "welcome":
        text, buttons = render_quiz_welcome(game)
    elif screen == "categories":
        text, buttons = render_categories_menu(game)
    elif screen == "settings":
        text, buttons = render_settings_menu(game)
    elif screen == "summary":
        text, buttons = render_summary_menu(game)
    else:
        return
    try:
        await safe_send(admin_id, text, buttons=buttons, parse_mode="html")
    except Exception as e:
        logger.exception(f"quiz_send_setup_menu: {e}")


def _render_join_text(game):
    players = list(game["players"].values())
    count = len(players)
    if count == 0:
        names_block = f"  {E('cross', '➖')} <i>هنوز کسی شرکت نکرده</i>"
    else:
        rank_emojis = ["🥇", "🥈", "🥉"]
        lines = []
        for i, p in enumerate(players):
            rank = rank_emojis[i] if i < 3 else f"<b>{i+1}.</b>"
            uname_txt = f" <i>@{p['username']}</i>" if p.get("username") else ""
            lines.append(f"  {rank} {E('check', '✅')} <b>{h(p['name'])}</b>{uname_txt}")
        names_block = "\n".join(lines)

    cats = "، ".join(game["categories"])
    target_txt = "بدون هدف" if game["target_score"] == 0 else f"{game['target_score']} امتیاز"
    text = (
        f"{E('brain', '🧠')} <b>کوییز هوشمند UNICORN</b> {E('brain', '🧠')}\n"
        f"{DIV}\n\n"
        f"{E('party', '🎉')} <b>یه کوییز حرفه‌ای با هوش مصنوعی شروع می‌شه!</b>\n\n"
        f"{E('list', '📋')} <b>دسته‌ها:</b> {h(cats)}\n"
        f"{E('chart', '📊')} <b>سوال هر نفر:</b> <code>{game['questions_per_player']}</code>\n"
        f"{E('hourglass', '⏳')} <b>زمان هر سوال:</b> <code>{game['time_per_question']}</code> ثانیه\n"
        f"{E('trophy', '🏆')} <b>هدف:</b> <code>{target_txt}</code>\n"
        f"{E('bolt', '⚡')} درست <b>+1</b> | غلط <b>-1</b>\n\n"
        f"{DIV}\n"
        f"{E('user', '👤')} <b>شرکت‌کنندگان ({count}):</b>\n"
        f"{names_block}\n"
        f"{DIV}\n\n"
        f"{E('target', '🎯')} <b>برای شرکت، روی دکمه بزن:</b>"
    )
    join_btn = f"✋ شرکت می‌کنم ({count})" if count > 0 else "✋ شرکت می‌کنم"
    buttons = [
        [Button.inline(join_btn, data=b"quiz_join")],
        [Button.inline("▶️ شروع بازی (ادمین)", data=b"quiz_start")],
    ]
    return text, buttons


async def quiz_broadcast_join(game):
    gid = game["group_id"]
    text, buttons = _render_join_text(game)
    try:
        sent = await safe_send(gid, text, buttons=buttons, parse_mode="html")
        if sent:
            game["join_msg_id"] = sent.id
    except Exception as e:
        logger.exception(f"quiz_broadcast_join: {e}")


async def quiz_refresh_join(game):
    gid = game["group_id"]
    mid = game.get("join_msg_id")
    if not mid:
        return
    text, buttons = _render_join_text(game)
    try:
        await client.edit_message(gid, mid, text=text, buttons=buttons, parse_mode="html")
        logger.info(f"✅ join refreshed — {len(game['players'])} players")
        return
    except MessageNotModifiedError:
        return
    except Exception as e:
        logger.warning(f"m1 fail: {e}")
    try:
        msg = await client.get_messages(gid, ids=mid)
        if msg:
            await msg.edit(text=text, buttons=buttons, parse_mode="html")
            return
    except Exception as e:
        logger.warning(f"m2 fail: {e}")
    try:
        new_sent = await safe_send(gid, text, buttons=buttons, parse_mode="html")
        if new_sent:
            game["join_msg_id"] = new_sent.id
            try:
                await client.delete_messages(gid, mid)
            except Exception:
                pass
    except Exception as e:
        logger.exception(f"m3 fail: {e}")


async def quiz_start_game(game):
    gid = game["group_id"]
    game["state"] = "playing"
    game["order"] = list(game["players"].keys())
    game["current_index"] = 0
    players_list = "\n".join([f"  {E('point', '👉')} <b>{h(p['name'])}</b>" for p in game["players"].values()])
    await safe_send(gid,
                    f"{E('party', '🎉')} <b>بازی شروع شد!</b> {E('party', '🎉')}\n"
                    f"{DIV}\n\n{E('user', '👤')} <b>بازیکنان ({len(game['order'])}):</b>\n{players_list}\n\n"
                    f"{E('rocket', '🚀')} <b>آماده باشید...</b>",
                    parse_mode="html")
    await asyncio.sleep(2)
    await quiz_next_turn(game)


async def quiz_next_turn(game):
    if game["state"] != "playing":
        return
    if not game["order"]:
        await quiz_finish(game)
        return
    n = len(game["order"])
    all_done = all(game["players"][uid]["asked"] >= game["questions_per_player"] for uid in game["order"])
    if all_done:
        await quiz_finish(game)
        return
    tries = 0
    while tries < n:
        idx = game["current_index"] % n
        uid = game["order"][idx]
        if game["players"][uid]["asked"] < game["questions_per_player"]:
            break
        game["current_index"] += 1
        tries += 1
    else:
        await quiz_finish(game)
        return
    uid = game["order"][game["current_index"] % n]
    player = game["players"][uid]
    game["current_player"] = uid
    game["current_state"] = "picking_category"
    game["current_question"] = None
    prev = game.get("turn_msg_id")
    if prev:
        try:
            await client.delete_messages(game["group_id"], prev)
        except Exception:
            pass
    cat_buttons = quiz_category_buttons(game)
    cat_buttons.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"quiz_skip_turn")])
    text = (
        f"{E('target', '🎯')} <b>نوبت {h(player['name'])}</b>\n"
        f"{DIV}\n\n"
        f"{E('chart', '📊')} سوال <code>{player['asked']+1}/{game['questions_per_player']}</code>\n"
        f"{E('star', '⭐')} امتیاز: <code>{player['score']}</code>\n\n"
        f"{E('brain', '🧠')} <b>{h(player['name'])}</b> یه دسته انتخاب کن:\n"
        f"{E('info', 'ℹ️')} <i>فقط خودت می‌تونی کلیک کنی</i>"
    )
    sent = await safe_send(game["group_id"], text, buttons=cat_buttons, parse_mode="html")
    if sent:
        game["turn_msg_id"] = sent.id


def quiz_category_buttons(game):
    buttons = []
    row = []
    for i, (key, emoji, name) in enumerate(QUIZ_CATEGORIES):
        if name not in game["categories"]:
            continue
        row.append(Button.inline(f"{emoji} {name}", data=f"quiz_pick:{i}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons


async def quiz_ask_question(game, player_uid, cat_index):
    key, emoji, cat_name = QUIZ_CATEGORIES[cat_index]
    gid = game["group_id"]
    if game.get("turn_msg_id"):
        try:
            await client.delete_messages(gid, game["turn_msg_id"])
            game["turn_msg_id"] = None
        except Exception:
            pass
    wait_msg = await safe_send(gid,
                               f"{E('brain', '🧠')} <b>هوش مصنوعی در حال ساخت سوال {emoji} {h(cat_name)}...</b>\n\n"
                               f"{E('bolt', '⚡')} <i>چند لحظه صبر کن</i>",
                               parse_mode="html")
    q = await ai_generate_question(cat_name)
    if not q:
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await safe_send(gid,
                        f"{E('cross', '❌')} <b>خطا در ساخت سوال</b>\n"
                        f"{E('info', 'ℹ️')} نوبت می‌چرخه...",
                        parse_mode="html")
        await asyncio.sleep(2)
        game["current_index"] += 1
        await quiz_next_turn(game)
        return
    player = game["players"][player_uid]
    game["current_question"] = {
        "player": player_uid, "question": q["question"], "options": q["options"],
        "correct": q["correct"], "category": cat_name, "answered": False, "msg_id": None,
    }
    game["current_state"] = "answering"
    player["asked"] += 1
    text = (
        f"{emoji} <b>سوال {h(cat_name)}</b> — نوبت <b>{h(player['name'])}</b>\n"
        f"{DIV}\n\n"
        f"{E('brain', '🧠')} <b>{h(q['question'])}</b>\n\n"
        f"{E('hourglass', '⏳')} <b>زمان:</b> <code>{game['time_per_question']}</code> ثانیه\n"
        f"{E('bolt', '⚡')} درست <b>+1</b> | غلط <b>-1</b>\n"
        f"{E('star', '⭐')} امتیاز فعلی: <code>{player['score']}</code>\n\n"
        f"{E('target', '🎯')} <b>{h(player['name'])}</b> یکی رو انتخاب کن:"
    )
    labels = ["۱", "۲", "۳", "۴"]
    buttons = []
    for i, opt in enumerate(q["options"]):
        buttons.append([Button.inline(f"{labels[i]}. {opt[:60]}", data=f"quiz_ans:{i}".encode())])
    buttons.append([Button.inline("⏭ رد کردن نوبت (ادمین)", data=b"quiz_skip_turn")])
    try:
        await wait_msg.delete()
    except Exception:
        pass
    sent = await safe_send(gid, text, buttons=buttons, parse_mode="html")
    if sent:
        game["current_question"]["msg_id"] = sent.id
    if game.get("timeout_task"):
        try:
            game["timeout_task"].cancel()
        except Exception:
            pass
    game["timeout_task"] = asyncio.create_task(quiz_timeout(game, player_uid, game["time_per_question"]))


def _build_answered_buttons(options, correct_idx, user_pick=None):
    labels = ["۱", "۲", "۳", "۴"]
    buttons = []
    for i, opt in enumerate(options):
        marker = "✅" if i == correct_idx else "❌"
        buttons.append([Button.inline(f"{marker} {labels[i]}. {opt[:58]}", data=b"quiz_noop")])
    return buttons


def _build_results_block(options, correct_idx, user_pick=None):
    labels = ["۱", "۲", "۳", "۴"]
    lines = [f"{E('list', '📋')} <b>گزینه‌ها:</b>"]
    for i, opt in enumerate(options):
        if i == correct_idx:
            line = f"{E('check', '✅')} <b>درست</b>  {labels[i]}. {h(opt)}"
        else:
            line = f"{E('cross', '❌')}  {labels[i]}. {h(opt)}"
        if user_pick is not None and i == user_pick:
            line += "  <b><i>(انتخاب تو)</i></b>"
        lines.append(line)
    return "\n".join(lines)


async def quiz_timeout(game, player_uid, seconds):
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        return
    cq = game.get("current_question")
    if not cq or cq.get("answered") or cq.get("player") != player_uid:
        return
    cq["answered"] = True
    player = game["players"].get(player_uid)
    if not player:
        return
    player["score"] -= 1
    correct_idx = cq["correct"]
    correct_txt = cq["options"][correct_idx]
    new_buttons = _build_answered_buttons(cq["options"], correct_idx)
    results_block = _build_results_block(cq["options"], correct_idx)
    if cq.get("msg_id"):
        try:
            await client.edit_message(
                game["group_id"], cq["msg_id"],
                text=(f"{E('hourglass', '⏳')} <b>وقت تموم شد!</b>\n"
                      f"{DIV}\n\n{E('user', '👤')} <b>{h(player['name'])}</b> جواب نداد\n"
                      f"{E('bolt', '⚡')} امتیاز: <code>-1</code>\n\n{results_block}\n\n"
                      f"{E('check', '✅')} <b>جواب درست:</b> {h(correct_txt)}\n"
                      f"{E('star', '⭐')} امتیاز فعلی: <code>{player['score']}</code>"),
                parse_mode="html", buttons=new_buttons)
        except Exception:
            pass
    await asyncio.sleep(2)
    if await quiz_check_target(game):
        return
    game["current_index"] += 1
    await quiz_next_turn(game)


async def quiz_check_target(game):
    target = game["target_score"]
    if target <= 0:
        return False
    for uid, p in game["players"].items():
        if p["score"] >= target:
            await quiz_finish(game, winner_uid=uid)
            return True
    return False


async def quiz_answer(game, player_uid, ans_index):
    cq = game.get("current_question")
    if not cq or cq.get("answered") or cq["player"] != player_uid:
        return
    cq["answered"] = True
    if game.get("timeout_task"):
        try:
            game["timeout_task"].cancel()
        except Exception:
            pass
    player = game["players"][player_uid]
    correct = cq["correct"]
    is_correct = (ans_index == correct)
    if is_correct:
        player["score"] += 1
        delta = "+1"
        msg = f"{E('party', '🎉')} <b>آفرین! درست بود</b>"
    else:
        player["score"] -= 1
        delta = "-1"
        msg = f"{E('warning', '😢')} <b>اشتباه بود!</b>"
    correct_txt = cq["options"][correct]
    chosen_txt = cq["options"][ans_index]
    new_buttons = _build_answered_buttons(cq["options"], correct, user_pick=ans_index)
    results_block = _build_results_block(cq["options"], correct, user_pick=ans_index)
    if cq.get("msg_id"):
        try:
            await client.edit_message(
                game["group_id"], cq["msg_id"],
                text=(f"{E('check', '✅')} <b>{h(player['name'])}</b> پاسخ داد\n"
                      f"{DIV}\n\n{E('message', '💬')} <b>انتخاب:</b> {h(chosen_txt)}\n\n"
                      f"{results_block}\n\n{msg}\n"
                      f"{E('bolt', '⚡')} <b>امتیاز:</b> <code>{delta}</code>\n"
                      f"{E('star', '⭐')} <b>امتیاز کل:</b> <code>{player['score']}</code>"),
                parse_mode="html", buttons=new_buttons)
        except Exception:
            pass
    await asyncio.sleep(2)
    if await quiz_check_target(game):
        return
    game["current_index"] += 1
    await quiz_next_turn(game)


async def quiz_skip_turn(game):
    if game["state"] != "playing":
        return
    current = game.get("current_player")
    if not current:
        return
    if game.get("timeout_task"):
        try:
            game["timeout_task"].cancel()
        except Exception:
            pass
    player = game["players"].get(current)
    player_name = player["name"] if player else "?"
    if game.get("turn_msg_id"):
        try:
            await client.delete_messages(game["group_id"], game["turn_msg_id"])
            game["turn_msg_id"] = None
        except Exception:
            pass
    cq = game.get("current_question")
    if cq:
        cq["answered"] = True
        if cq.get("msg_id"):
            new_buttons = _build_answered_buttons(cq["options"], cq["correct"])
            try:
                await client.edit_message(
                    game["group_id"], cq["msg_id"],
                    text=(f"{E('skip', '⏭')} <b>نوبت رد شد</b>\n{DIV}\n\n"
                          f"{E('user', '👤')} <b>{h(player_name)}</b>\n"
                          f"{E('info', 'ℹ️')} ادمین این نوبت رو رد کرد\n\n"
                          f"{E('hourglass', '⏳')} <i>نوبت بعدی...</i>"),
                    parse_mode="html", buttons=new_buttons)
            except Exception:
                pass
        if player:
            player["asked"] += 1
    await safe_send(game["group_id"],
                    f"{E('skip', '⏭')} <b>نوبت {h(player_name)} رد شد</b>\n"
                    f"{E('info', 'ℹ️')} <i>در حال رفتن به نوبت بعدی...</i>",
                    parse_mode="html")
    await asyncio.sleep(1.5)
    if await quiz_check_target(game):
        return
    game["current_index"] += 1
    await quiz_next_turn(game)


async def quiz_finish(game, winner_uid=None):
    game["state"] = "finished"
    try:
        if game.get("timeout_task"):
            game["timeout_task"].cancel()
    except Exception:
        pass
    gid = game["group_id"]
    players = game["players"]
    sorted_players = sorted(players.items(), key=lambda x: x[1]["score"], reverse=True)
    if winner_uid and winner_uid in players:
        winner = players[winner_uid]
        header = (f"{E('trophy', '🏆')} <b>برنده کوییز!</b> {E('trophy', '🏆')}\n"
                  f"{DIV}\n\n{E('crown', '👑')} <b>{h(winner['name'])}</b>\n"
                  f"{E('star', '⭐')} امتیاز: <code>{winner['score']}</code>\n"
                  f"{E('target', '🎯')} به امتیاز هدف رسید!")
    elif sorted_players:
        winner = sorted_players[0][1]
        header = (f"{E('flag', '🏁')} <b>کوییز تموم شد!</b>\n{DIV}\n\n"
                  f"{E('trophy', '🏆')} <b>برنده:</b> {h(winner['name'])}\n"
                  f"{E('star', '⭐')} امتیاز: <code>{winner['score']}</code>")
    else:
        header = f"{E('flag', '🏁')} <b>کوییز تموم شد!</b>"
    medals = ["🥇", "🥈", "🥉"]
    lines = [header, "", f"{E('stats', '📊')} <b>جدول نهایی:</b>"]
    for i, (uid, p) in enumerate(sorted_players):
        m = medals[i] if i < 3 else "▫️"
        lines.append(f"{m} <b>{h(p['name'])}</b> — <code>{p['score']}</code> امتیاز")
    await safe_send(gid, "\n".join(lines), parse_mode="html")
    for uid, p in players.items():
        if p["score"] > 0:
            try:
                db.add_points(uid, p["name"], p["score"] * 2, joined=True)
            except Exception:
                pass
    ACTIVE_GAMES.pop(gid, None)


# ═════════════════════════════════════════════
# Group Handler
# ═════════════════════════════════════════════
@client.on(events.NewMessage())
async def on_group_message(event):
    try:
        if event.is_private:
            return
        me = await client.get_me()
        if event.sender_id == me.id:
            return
        chat = await event.get_chat()
        if hasattr(chat, "title"):
            try:
                db.save_group(event.chat_id, chat.title, getattr(chat, "username", None))
            except Exception:
                pass
        raw = (event.raw_text or "").strip()
        if "خلوته" in raw:
            await safe_reply(event, f"{E('laugh', '😂')} <b>شیک بزن شلوغ بشه</b> {E('laugh', '😂')}",
                             parse_mode="html")
            return
        if not is_admin(event.sender_id):
            return
        if raw in ("چالش", "چالش جدید", "کوییز", "کوییز جدید"):
            uid = event.sender_id
            game = create_setup_game(uid, event.chat_id)
            await safe_reply(event,
                             f"{E('check', '✅')} <b>منوی کوییز به پیوی شما فرستاده شد</b>\n"
                             f"{DIV}\n\n{E('brain', '🧠')} تنظیمات رو توی پیوی انجام بده.\n"
                             f"{E('info', 'ℹ️')} بعد از تأیید، پیام شرکت همین‌جا میاد.",
                             parse_mode="html")
            try:
                await quiz_send_setup_menu(uid, "welcome", game)
            except Exception as e:
                logger.exception(f"send quiz setup: {e}")
            return
        if raw.startswith("نظرسنجی"):
            content = raw[len("نظرسنجی"):].strip().lstrip(":").lstrip("：").strip()
            parts = [p.strip() for p in content.split("|") if p.strip()]
            if len(parts) < 3:
                await safe_reply(event, f"{E('warning', '⚠️')} <code>نظرسنجی: عنوان | گ1 | گ2</code>",
                                 parse_mode="html")
                return
            title = parts[0]
            options = parts[1:]
            deadline = None
            last = parts[-1]
            if len(parts) > 3 and re.match(r"^\d+\s*(m|min|h|hr|d|day|د|دقیقه|س|ساعت|روز)?$", last):
                maybe = parse_duration(last)
                if maybe:
                    deadline = (datetime.now(IRAN_TZ) + maybe).isoformat()
                    options = parts[1:-1]
            if len(options) < 2:
                await safe_reply(event, f"{E('cross', '❌')} حداقل ۲ گزینه!", parse_mode="html")
                return
            ch_id = db.create_challenge(event.sender_id, event.chat_id, title, "",
                                        ch_type="poll", options=options, deadline=deadline)
            link = f"https://t.me/{BOT_USERNAME}?start=ch_{ch_id}"
            msg_text = build_challenge_text(ch_id, title, "", "poll", options, deadline)
            sent = await safe_respond(event, msg_text, parse_mode="html",
                                      buttons=[[Button.url("🎯 شرکت می‌کنم", link)]])
            if sent:
                db.set_challenge_message(ch_id, sent.id)
            return
        if raw.startswith("چالش"):
            content = raw[len("چالش"):].strip().lstrip(":").lstrip("：").strip()
            parts = [p.strip() for p in content.split("|") if p.strip()]
            if len(parts) < 2:
                await safe_reply(event, f"{E('warning', '⚠️')} <code>چالش: عنوان | سوال</code>",
                                 parse_mode="html")
                return
            title = parts[0]
            question = parts[1]
            deadline = None
            if len(parts) >= 3:
                maybe = parse_duration(parts[2])
                if maybe:
                    deadline = (datetime.now(IRAN_TZ) + maybe).isoformat()
            ch_id = db.create_challenge(event.sender_id, event.chat_id, title, question,
                                        ch_type="text", deadline=deadline)
            link = f"https://t.me/{BOT_USERNAME}?start=ch_{ch_id}"
            msg_text = build_challenge_text(ch_id, title, question, "text", None, deadline)
            sent = await safe_respond(event, msg_text, parse_mode="html",
                                      buttons=[[Button.url("🎯 شرکت می‌کنم", link)]])
            if sent:
                db.set_challenge_message(ch_id, sent.id)
            return
    except Exception as ex:
        logger.exception(f"group handler: {ex}")


# ═════════════════════════════════════════════
# PM Handler
# ═════════════════════════════════════════════
@client.on(events.NewMessage(func=lambda e: e.is_private))
async def on_private(event):
    try:
        me = await client.get_me()
        if event.sender_id == me.id:
            return
        uid = event.sender_id
        raw = (event.raw_text or "").strip()
        try:
            sender = await event.get_sender()
        except Exception:
            sender = None
        uname = user_name(sender)
        username = getattr(sender, "username", None) if sender else None
        db.save_user(uid, uname, username)

        if raw.startswith("/start"):
            parts = raw.split(None, 1)
            payload = parts[1].strip() if len(parts) > 1 else ""
            if payload.startswith("anon_"):
                try:
                    target = int(payload[5:])
                except ValueError:
                    target = 0
                if target == uid or target == 0:
                    await safe_respond(event, f"{E('cross', '❌')} لینک نامعتبره", parse_mode="html")
                    return
                set_state(uid, "awaiting_anon", target=target)
                await safe_respond(event,
                                   f"{E('heart', '💌')} <b>پیام ناشناس</b>\n{DIV}\n\nپیامت رو بنویس:",
                                   parse_mode="html",
                                   buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
                return
            if payload.startswith("ch_"):
                try:
                    ch_id = int(payload[3:])
                except ValueError:
                    ch_id = 0
                ch = db.get_challenge(ch_id)
                if not ch or not ch.get("is_active"):
                    await safe_respond(event, f"{E('cross', '❌')} چالش یافت نشد یا بسته شده",
                                       parse_mode="html")
                    return
                ch_type = ch.get("ch_type") or "text"
                if ch_type == "poll":
                    if db.has_voted(ch_id, uid):
                        await safe_respond(event, f"{E('info', 'ℹ️')} قبلاً رأی دادی", parse_mode="html")
                        return
                    options = json.loads(ch["options"]) if ch.get("options") else []
                    opts_lines = "\n".join([f"  {E('point', '👉')} <b>{i+1}.</b> {h(o)}"
                                            for i, o in enumerate(options)])
                    text = (f"{E('chart', '📊')} <b>نظرسنجی ناشناس</b>\n{DIV}\n\n"
                            f"{E('tag', '🏷️')} <b>عنوان:</b> {h(ch['title'])}\n\n"
                            f"{E('list', '📋')} <b>گزینه‌ها:</b>\n{opts_lines}\n\n"
                            f"{E('rocket', '🚀')} یک گزینه انتخاب کن:")
                    buttons = []
                    for i, o in enumerate(options):
                        buttons.append([Button.inline(f"◽ {o[:30]}", data=f"vote:{ch_id}:{i}".encode())])
                    buttons.append([Button.inline("❌ لغو", data=b"cancel")])
                    await safe_respond(event, text, buttons=buttons, parse_mode="html")
                    return
                if db.has_answered(ch_id, uid):
                    await safe_respond(event, f"{E('info', 'ℹ️')} قبلاً شرکت کردی", parse_mode="html")
                    return
                text = (f"{E('diamond', '💎')} <b>چالش ناشناس</b>\n{DIV}\n\n"
                        f"{E('tag', '🏷️')} <b>عنوان:</b> {h(ch['title'])}\n\n"
                        f"{E('message', '💬')} <b>سوال:</b> {h(ch['question'])}\n\n"
                        f"{E('alert', '⚠️')} شرکت می‌کنی؟")
                buttons = [[Button.inline("✅ بله", data=f"join:{ch_id}".encode()),
                            Button.inline("❌ لغو", data=b"cancel")]]
                await safe_respond(event, text, buttons=buttons, parse_mode="html")
                return
            if is_admin(uid):
                await send_admin_menu(event)
            else:
                await safe_respond(event,
                                   f"{E('crown', '👑')} <b>UNICORN ANONY BOT</b>\n{DIV}\n\n"
                                   f"{E('wave', '👋')} سلام!\n\n"
                                   f"{E('brain', '🧠')} کوییز هوشمند در گروه‌ها\n"
                                   f"{E('diamond', '💎')} چالش ناشناس\n"
                                   f"{E('heart', '💌')} پیام ناشناس\n\n"
                                   f"{E('info', 'ℹ️')} /help",
                                   parse_mode="html")
            return

        if raw == "/help":
            await safe_respond(event, f"{E('info', 'ℹ️')} /me /top /mylink /help", parse_mode="html")
            return

        if raw == "/me":
            sc = db.get_score(uid) or {}
            rank = db.get_rank(uid)
            ngl_recv = db.count_anon_received(uid)
            await safe_respond(event,
                               f"{E('user', '👤')} <b>پروفایل</b>\n{DIV}\n\n"
                               f"{E('tag', '🏷️')} {h(uname)}\n"
                               f"{E('id', '🆔')} <code>{uid}</code>\n\n"
                               f"{E('star', '⭐')} امتیاز: <code>{sc.get('points', 0)}</code>\n"
                               f"{E('diamond', '💎')} چالش‌ها: <code>{sc.get('challenges_joined', 0)}</code>\n"
                               f"{E('heart', '💌')} پیام ناشناس: <code>{ngl_recv}</code>\n"
                               f"{E('trophy', '🏆')} رتبه: {('#' + str(rank)) if rank else '—'}",
                               parse_mode="html")
            return

        if raw == "/top":
            top = db.get_top(10)
            if not top:
                await safe_respond(event, f"{E('info', 'ℹ️')} خالیه", parse_mode="html")
                return
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
            admin_list = "، ".join([f"<code>{x}</code>" for x in sorted(ALL_ADMINS)])
            await safe_respond(event,
                               f"{E('stats', '📊')} <b>آمار</b>\n{DIV}\n\n"
                               f"{E('group', '🏢')} گروه‌ها: <code>{len(db.get_groups())}</code>\n"
                               f"{E('user', '👤')} کاربران: <code>{db.count_users()}</code>\n"
                               f"{E('diamond', '💎')} چالش‌ها: <code>{len(db.get_challenges())}</code>\n"
                               f"{E('fire', '🔥')} فعال: <code>{db.count_active_challenges()}</code>\n\n"
                               f"{E('crown', '👑')} <b>ادمین‌ها:</b>\n{admin_list}",
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
                await safe_respond(event, f"{E('search', '🔍')} <code>/search کلمه</code>",
                                   parse_mode="html")
                return
            res = db.search_challenges(uid, parts[1].strip())
            if not res:
                await safe_respond(event, f"{E('info', 'ℹ️')} نتیجه‌ای نیس", parse_mode="html")
                return
            lines = [f"{E('search', '🔍')} نتایج:\n"]
            for c_ in res[:10]:
                lines.append(f"{E('diamond', '💎')} <b>#{c_['id']}</b> {h(c_['title'])}")
            await safe_respond(event, "\n".join(lines), parse_mode="html")
            return

        st = get_state(uid)
        if st:
            state = st.get("state")
            data = st.get("data", {})
            if state == "awaiting_anon":
                if not raw or len(raw) > MAX_ANSWER_LEN:
                    await safe_respond(event, f"{E('warning', '⚠️')} پیام نامعتبره", parse_mode="html")
                    return
                target = data.get("target")
                if not target:
                    clear_state(uid)
                    return
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
                except Exception:
                    pass
                return
            if state == "awaiting_broadcast":
                clear_state(uid)
                user_ids = db.get_all_users()
                await safe_respond(event, f"{E('rocket', '🚀')} ارسال به {len(user_ids)} کاربر...",
                                   parse_mode="html")
                sent, failed = 0, 0
                for i, u in enumerate(user_ids):
                    try:
                        await safe_send(u, raw, parse_mode="html")
                        sent += 1
                    except FloodWaitError as fwe:
                        await asyncio.sleep(fwe.seconds + 1)
                        try:
                            await safe_send(u, raw, parse_mode="html")
                            sent += 1
                        except Exception:
                            failed += 1
                    except Exception:
                        failed += 1
                    if i % 25 == 24:
                        await asyncio.sleep(1.2)
                await safe_respond(event,
                                   f"{E('check', '✅')} تمام شد\n"
                                   f"ارسال: <code>{sent}</code> | ناموفق: <code>{failed}</code>",
                                   parse_mode="html")
                return
            if state == "awaiting_title":
                if not raw:
                    return
                data["title"] = raw[:200]
                ch_type = data.get("type", "text")
                set_state(uid, "awaiting_question" if ch_type == "text" else "awaiting_options", **data)
                if ch_type == "text":
                    await safe_respond(event, f"{E('message', '💬')} سوال رو بفرست:",
                                       parse_mode="html",
                                       buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
                else:
                    await safe_respond(event, f"{E('list', '📋')} گزینه‌ها با <code>|</code>:",
                                       parse_mode="html",
                                       buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
                return
            if state == "awaiting_question":
                if not raw:
                    return
                data["question"] = raw[:800]
                set_state(uid, "awaiting_deadline", **data)
                await _ask_deadline(event)
                return
            if state == "awaiting_options":
                opts = [p.strip() for p in raw.split("|") if p.strip()]
                if len(opts) < 2:
                    await safe_respond(event, f"{E('warning', '⚠️')} حداقل ۲ گزینه!", parse_mode="html")
                    return
                data["options"] = opts[:10]
                set_state(uid, "awaiting_deadline", **data)
                await _ask_deadline(event)
                return
            if state == "awaiting_deadline":
                td = parse_duration(raw)
                if td is None and raw not in ("", "-", "ندارد", "بدون", "skip"):
                    await safe_respond(event, f"{E('warning', '⚠️')} فرمت اشتباه", parse_mode="html")
                    return
                deadline = (datetime.now(IRAN_TZ) + td).isoformat() if td else None
                data["deadline"] = deadline
                set_state(uid, "awaiting_group", **data)
                await _ask_group(event, data)
                return
            if state == "awaiting_answer":
                ch_id = data.get("challenge_id")
                ch = db.get_challenge(ch_id) if ch_id else None
                if not ch:
                    clear_state(uid)
                    await safe_respond(event, f"{E('cross', '❌')} چالش یافت نشد", parse_mode="html")
                    return
                if not raw or len(raw) > MAX_ANSWER_LEN:
                    await safe_respond(event, f"{E('warning', '⚠️')} پاسخ نامعتبره", parse_mode="html")
                    return
                db.save_answer(ch_id, uid, uname, username, raw)
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
                except Exception:
                    pass
                return

        if is_admin(uid):
            await send_admin_menu(event)
        else:
            await safe_respond(event,
                               f"{E('info', 'ℹ️')} برای شرکت در چالش‌ها از دکمه‌های گروه استفاده کن.\n"
                               f"{E('rocket', '🚀')} /help",
                               parse_mode="html")
    except Exception as ex:
        logger.exception(f"pm handler: {ex}")


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
        clear_state(event.sender_id)
        return
    buttons = [[Button.inline(f"🏢 {(g.get('title') or '—')[:40]}",
                              data=f"chgrp:{g['group_id']}".encode())] for g in groups[:20]]
    buttons.append([Button.inline("❌ لغو", data=b"cancel")])
    await safe_respond(event, f"{E('group', '🏢')} کدوم گروه؟", buttons=buttons, parse_mode="html")


# ═════════════════════════════════════════════
# Callback Handler
# ═════════════════════════════════════════════
@client.on(events.CallbackQuery())
async def on_cb(event):
    try:
        uid = event.sender_id
        data = event.data.decode("utf-8", "ignore")

        if data == "quiz_join":
            game = _find_game_for_callback(event)
            if not game:
                await event.answer("❌ بازی پیدا نشد!", alert=True)
                return
            if game.get("state") != "waiting":
                await event.answer("⏳ بازی شروع شده!", alert=True)
                return
            if uid in game["players"]:
                await event.answer("⚠️ قبلاً شرکت کردی!", alert=True)
                return
            try:
                sender = await event.get_sender()
                name = user_name(sender)
                username = getattr(sender, "username", None)
            except Exception:
                name = str(uid)
                username = None
            game["players"][uid] = {
                "name": name, "username": username,
                "score": 0, "asked": 0, "joined_at": now_iso(),
            }
            logger.info(f"👤 player joined: {name} ({uid})")
            await event.answer(f"✅ {name} عزیز، ثبت شد!")
            try:
                await quiz_refresh_join(game)
            except Exception as e:
                logger.exception(f"refresh after join failed: {e}")
            return

        if data == "quiz_start":
            game = _find_game_for_callback(event)
            if not game or game.get("state") != "waiting":
                await event.answer("❌ بازی فعال نیست!", alert=True)
                return
            if uid != game["admin_id"] and not is_admin(uid):
                await event.answer("⛔ فقط ادمین!", alert=True)
                return
            if len(game["players"]) < 1:
                await event.answer("⚠️ حداقل ۱ بازیکن!", alert=True)
                return
            await event.answer("🚀 شروع!")
            try:
                if game.get("join_msg_id"):
                    await client.edit_message(
                        game["group_id"], game["join_msg_id"],
                        text=(f"{E('check', '✅')} <b>بازی شروع شد!</b>\n"
                              f"{E('user', '👤')} <b>{len(game['players'])}</b> بازیکن"),
                        parse_mode="html", buttons=None)
            except Exception:
                pass
            asyncio.create_task(quiz_start_game(game))
            return

        if data.startswith("quiz_pick:"):
            try:
                idx = int(data.split(":", 1)[1])
            except Exception:
                await event.answer("خطا", alert=True)
                return
            game = _find_game_for_callback(event)
            if not game or game.get("state") != "playing":
                await event.answer("❌ بازی فعال نیست", alert=True)
                return
            if game.get("current_player") != uid:
                await event.answer("⛔ نوبت تو نیست!", alert=True)
                return
            if game.get("current_state") != "picking_category":
                await event.answer("الان نمیشه انتخاب کرد", alert=True)
                return
            await event.answer(f"🎯 {QUIZ_CATEGORIES[idx][2]}")
            asyncio.create_task(quiz_ask_question(game, uid, idx))
            return

        if data.startswith("quiz_ans:"):
            try:
                idx = int(data.split(":", 1)[1])
            except Exception:
                await event.answer("خطا", alert=True)
                return
            game = _find_game_for_callback(event)
            if not game or game.get("state") != "playing":
                await event.answer("❌ بازی فعال نیست", alert=True)
                return
            cq = game.get("current_question")
            if not cq or cq.get("answered"):
                await event.answer("این سوال بسته شده", alert=True)
                return
            if cq.get("player") != uid:
                await event.answer("⛔ این سوال مال تو نیست!", alert=True)
                return
            await event.answer("✅")
            asyncio.create_task(quiz_answer(game, uid, idx))
            return

        if data == "quiz_skip_turn":
            game = _find_game_for_callback(event)
            if not game or game.get("state") != "playing":
                await event.answer("❌ بازی فعال نیست", alert=True)
                return
            if not is_admin(uid):
                await event.answer("⛔ فقط ادمین!", alert=True)
                return
            await event.answer("⏭ رد شد")
            asyncio.create_task(quiz_skip_turn(game))
            return

        if data == "quiz_cancel":
            SETUP_GAMES.pop(uid, None)
            await event.answer("❌ لغو شد")
            try:
                await safe_edit(event, f"{E('cross', '❌')} کوییز لغو شد",
                                parse_mode="html", buttons=None)
            except Exception:
                pass
            return

        if data == "quiz_setup":
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("جلسه منقضی، دوباره «چالش» بزن", alert=True)
                return
            await event.answer()
            text, buttons = render_categories_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data == "quiz_noop":
            await event.answer()
            return

        if data.startswith("quiz_cat:"):
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            try:
                idx = int(data.split(":", 1)[1])
                _, _, name = QUIZ_CATEGORIES[idx]
            except Exception:
                await event.answer("خطا", alert=True)
                return
            if name in game["categories"]:
                game["categories"].remove(name)
                await event.answer(f"➖ {name}")
            else:
                game["categories"].append(name)
                await event.answer(f"✅ {name}")
            text, buttons = render_categories_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data == "quiz_backcat":
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            await event.answer()
            text, buttons = render_categories_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data == "quiz_settings":
            game = SETUP_GAMES.get(uid)
            if not game or not game["categories"]:
                await event.answer("اول دسته انتخاب کن", alert=True)
                return
            await event.answer()
            text, buttons = render_settings_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data.startswith("quiz_q:"):
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            game["questions_per_player"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {game['questions_per_player']} سوال")
            text, buttons = render_settings_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data.startswith("quiz_t:"):
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            game["time_per_question"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {game['time_per_question']} ثانیه")
            text, buttons = render_settings_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data.startswith("quiz_s:"):
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            game["target_score"] = int(data.split(":", 1)[1])
            await event.answer(f"✅ {'بدون' if game['target_score'] == 0 else game['target_score']}")
            text, buttons = render_settings_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data == "quiz_summary":
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            await event.answer()
            text, buttons = render_summary_menu(game)
            await safe_edit(event, text, buttons=buttons, parse_mode="html")
            return

        if data == "quiz_create":
            game = SETUP_GAMES.get(uid)
            if not game:
                await event.answer("منقضی", alert=True)
                return
            await event.answer("✅ بازی ساخته شد")
            try:
                await safe_edit(event,
                                f"{E('check', '✅')} <b>بازی ساخته شد!</b>\n{DIV}\n\n"
                                f"{E('info', 'ℹ️')} پیام شرکت توی گروه فرستاده شد.",
                                parse_mode="html", buttons=None)
            except Exception:
                pass
            game["state"] = "waiting"
            ACTIVE_GAMES[game["group_id"]] = game
            SETUP_GAMES.pop(uid, None)
            await quiz_broadcast_join(game)
            return

        if data == "cancel":
            clear_state(uid)
            await event.answer("❌ لغو شد")
            try:
                await safe_edit(event, f"{E('cross', '❌')} لغو شد",
                                parse_mode="html", buttons=None)
            except Exception:
                pass
            return

        if data.startswith("dl:"):
            st = get_state(uid)
            if not st or st.get("state") != "awaiting_deadline":
                await event.answer("⚠️", alert=True)
                return
            val = data.split(":", 1)[1]
            td = None if val == "none" else parse_duration(val)
            deadline = (datetime.now(IRAN_TZ) + td).isoformat() if td else None
            new_data = dict(st["data"])
            new_data["deadline"] = deadline
            set_state(uid, "awaiting_group", **new_data)
            await event.answer("✅")
            await _ask_group(event, new_data)
            return

        if data.startswith("join:"):
            try:
                ch_id = int(data.split(":", 1)[1])
            except ValueError:
                await event.answer("خطا", alert=True)
                return
            ch = db.get_challenge(ch_id)
            if not ch or not ch.get("is_active"):
                await event.answer("چالش یافت نشد", alert=True)
                return
            if db.has_answered(ch_id, uid):
                await event.answer("قبلاً شرکت کردی!", alert=True)
                return
            set_state(uid, "awaiting_answer", challenge_id=ch_id)
            await event.answer("✅")
            await safe_edit(event,
                            f"{E('check', '✅')} <b>تایید شد!</b>\n\n"
                            f"{E('message', '💬')} <b>جوابت رو بفرست:</b>",
                            parse_mode="html", buttons=None)
            return

        if data.startswith("vote:"):
            try:
                _, ch_id_s, idx_s = data.split(":")
                ch_id, idx = int(ch_id_s), int(idx_s)
            except Exception:
                await event.answer("خطا", alert=True)
                return
            ch = db.get_challenge(ch_id)
            if not ch or not ch.get("is_active"):
                await event.answer("بسته شده", alert=True)
                return
            if db.has_voted(ch_id, uid):
                await event.answer("قبلاً رأی دادی", alert=True)
                return
            try:
                sender = await event.get_sender()
                uname = user_name(sender)
            except Exception:
                uname = str(uid)
            db.save_poll_vote(ch_id, uid, uname, idx)
            db.add_points(uid, uname, 5, joined=True)
            await event.answer("✅ ثبت شد")
            options = json.loads(ch["options"]) if ch.get("options") else []
            chosen = options[idx] if 0 <= idx < len(options) else "?"
            try:
                await safe_edit(event,
                                f"{E('check', '✅')} <b>رأی ثبت شد!</b>\n\n"
                                f"{E('vote', '🗳')} <b>انتخاب:</b> {h(chosen)}\n"
                                f"{E('star', '⭐')} +۵ امتیاز",
                                parse_mode="html", buttons=None)
            except Exception:
                pass
            return

        if not is_admin(uid):
            await event.answer("⛔", alert=True)
            return

        if data == "new_text":
            set_state(uid, "awaiting_title", type="text")
            await event.answer()
            await safe_edit(event,
                            f"{E('diamond', '💎')} <b>چالش متنی</b>\n{DIV}\n\n"
                            f"{E('tag', '🏷️')} عنوان رو بفرست:",
                            parse_mode="html",
                            buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
            return

        if data == "new_poll":
            set_state(uid, "awaiting_title", type="poll")
            await event.answer()
            await safe_edit(event,
                            f"{E('chart', '📊')} <b>نظرسنجی</b>\n{DIV}\n\n"
                            f"{E('tag', '🏷️')} عنوان رو بفرست:",
                            parse_mode="html",
                            buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
            return

        if data == "templates":
            buttons = [[Button.inline(t, data=f"tpl:{i}".encode())]
                       for i, (t, _) in enumerate(TEMPLATES)]
            buttons.append([Button.inline("🔙 بازگشت", data=b"menu")])
            await event.answer()
            await safe_edit(event, f"{E('gift', '🎁')} <b>قالب‌های آماده</b>",
                            parse_mode="html", buttons=buttons)
            return

        if data.startswith("tpl:"):
            try:
                idx = int(data.split(":", 1)[1])
                t, q = TEMPLATES[idx]
            except Exception:
                await event.answer("خطا", alert=True)
                return
            set_state(uid, "awaiting_deadline",
                     type="text", title=t.replace("💎 ", ""), question=q)
            await event.answer("✅")
            await _ask_deadline(event)
            return

        if data == "my_challenges":
            chs = db.get_challenges(admin_id=uid)
            if not chs:
                await event.answer("هنوز چالشی نساختی", alert=True)
                return
            await event.answer()
            await _render_challenges_page(event, chs, page=0)
            return

        if data.startswith("chpage:"):
            page = int(data.split(":", 1)[1])
            chs = db.get_challenges(admin_id=uid)
            await event.answer()
            await _render_challenges_page(event, chs, page=page)
            return

        if data == "my_groups":
            groups = db.get_groups()
            if not groups:
                await event.answer("خالیه", alert=True)
                return
            await event.answer()
            lines = [f"{E('group', '🏢')} <b>گروه‌ها</b>\n{DIV}\n"]
            for i, g in enumerate(groups[:20], 1):
                lines.append(f"{E('fire', '🔥')} <b>#{i}</b> {h(g.get('title') or '—')}\n"
                             f"{E('id', '🆔')} <code>{g['group_id']}</code>")
            await safe_edit(event, "\n".join(lines),
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]],
                            parse_mode="html")
            return

        if data == "menu":
            await event.answer()
            await send_admin_menu(event, edit=True)
            return

        if data == "top":
            top = db.get_top(10)
            if not top:
                await event.answer("خالیه", alert=True)
                return
            await event.answer()
            medals = ["🥇", "🥈", "🥉"] + ["🎖"] * 7
            lines = [f"{E('trophy', '🏆')} <b>لیدربورد</b>\n{DIV}\n"]
            for i, u in enumerate(top):
                m = medals[i] if i < len(medals) else "•"
                lines.append(f"{m} <b>{h(u['user_name'] or 'ناشناس')}</b> — <code>{u['points']}</code>")
            await safe_edit(event, "\n".join(lines),
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]],
                            parse_mode="html")
            return

        if data == "mylink":
            link = f"https://t.me/{BOT_USERNAME}?start=anon_{uid}"
            n = db.count_anon_received(uid)
            await event.answer()
            await safe_edit(event,
                            f"{E('heart', '💌')} <b>لینک NGL</b>\n{DIV}\n\n<code>{link}</code>\n\n"
                            f"{E('stats', '📊')} <code>{n}</code>",
                            parse_mode="html",
                            buttons=[
                                [Button.url("📤 اشتراک", f"https://t.me/share/url?url={link}")],
                                [Button.inline("📥 صندوق", data=b"anon_inbox")],
                                [Button.inline("🔙 بازگشت", data=b"menu")],
                            ])
            return

        if data == "anon_inbox":
            items = db.get_anon_inbox(uid, limit=10)
            if not items:
                await event.answer("صندوق خالیه", alert=True)
                return
            await event.answer()
            lines = [f"{E('heart', '💌')} <b>صندوق ناشناس</b>\n{DIV}\n"]
            for i, m in enumerate(items, 1):
                lines.append(f"\n{E('message', '💬')} <b>#{i}</b>\n"
                             f"<blockquote>{h(m['text'])}</blockquote>\n"
                             f"{E('time', '⏱')} {h((m['sent_at'] or '')[:19])}")
            db.mark_anon_read(uid)
            await safe_edit(event, "\n".join(lines),
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]],
                            parse_mode="html")
            return

        if data == "stats":
            admin_list = "، ".join([f"<code>{x}</code>" for x in sorted(ALL_ADMINS)])
            await event.answer()
            await safe_edit(event,
                            f"{E('stats', '📊')} <b>آمار</b>\n{DIV}\n\n"
                            f"{E('group', '🏢')} گروه‌ها: <code>{len(db.get_groups())}</code>\n"
                            f"{E('user', '👤')} کاربران: <code>{db.count_users()}</code>\n"
                            f"{E('diamond', '💎')} چالش‌ها: <code>{len(db.get_challenges())}</code>\n"
                            f"{E('fire', '🔥')} فعال: <code>{db.count_active_challenges()}</code>\n\n"
                            f"{E('crown', '👑')} <b>ادمین‌ها:</b>\n{admin_list}",
                            parse_mode="html",
                            buttons=[[Button.inline("🔙 بازگشت", data=b"menu")]])
            return

        if data == "broadcast":
            set_state(uid, "awaiting_broadcast")
            await event.answer()
            await safe_edit(event,
                            f"{E('message', '💬')} <b>برادکست</b>\n\nپیام رو بفرست:",
                            parse_mode="html",
                            buttons=[[Button.inline("❌ لغو", data=b"cancel")]])
            return

        if data.startswith("viewans:"):
            try:
                ch_id = int(data.split(":", 1)[1])
            except ValueError:
                await event.answer("خطا", alert=True)
                return
            ch = db.get_challenge(ch_id)
            if not ch:
                await event.answer("یافت نشد", alert=True)
                return
            await event.answer()
            await _show_challenge_answers(event, ch)
            return

        if data.startswith("chgrp:"):
            try:
                gid_c = int(data.split(":", 1)[1])
            except ValueError:
                await event.answer("خطا", alert=True)
                return
            st = get_state(uid)
            if not st or st.get("state") != "awaiting_group":
                await event.answer("⚠️", alert=True)
                return
            d = st["data"]
            ch_id = db.create_challenge(uid, gid_c, d.get("title", ""), d.get("question", ""),
                                        ch_type=d.get("type", "text"),
                                        options=d.get("options"),
                                        deadline=d.get("deadline"))
            clear_state(uid)
            link = f"https://t.me/{BOT_USERNAME}?start=ch_{ch_id}"
            msg_text = build_challenge_text(ch_id, d.get("title", ""), d.get("question", ""),
                                            d.get("type", "text"), d.get("options"), d.get("deadline"))
            try:
                sent = await safe_send(gid_c, msg_text, parse_mode="html",
                                       buttons=[[Button.url("🎯 شرکت می‌کنم", link)]])
                if sent:
                    db.set_challenge_message(ch_id, sent.id)
                await event.answer("✅")
                await safe_edit(event,
                                f"{E('check', '✅')} <b>ساخته شد!</b>\n\n"
                                f"{E('diamond', '💎')} <b>#{ch_id}</b> {h(d.get('title', ''))}",
                                parse_mode="html",
                                buttons=[[Button.inline("🔙 منو", data=b"menu")]])
            except Exception as e:
                logger.exception(f"send challenge: {e}")
                await event.answer("خطا", alert=True)
            return
    except Exception as ex:
        logger.exception(f"cb: {ex}")
        try:
            await event.answer("خطا!", alert=True)
        except Exception:
            pass


async def _render_challenges_page(event, chs, page=0, per_page=5):
    total = len(chs)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, pages - 1))
    start = page * per_page
    page_items = chs[start:start + per_page]
    lines = [f"{E('list', '📋')} <b>چالش‌های شما</b> <i>(صفحه {page+1}/{pages})</i>\n{DIV}\n"]
    buttons = []
    for ch in page_items:
        ch_type = ch.get("ch_type") or "text"
        cnt = db.count_poll_votes(ch["id"]) if ch_type == "poll" else db.count_answers(ch["id"])
        kind = f"{E('chart', '📊')}" if ch_type == "poll" else f"{E('diamond', '💎')}"
        status = "🟢" if ch.get("is_active") else "🔴"
        lines.append(f"\n{kind} <b>#{ch['id']}</b> {status} {h(ch['title'])}\n"
                     f"{E('user', '👤')} <code>{cnt}</code>\n"
                     f"{E('time', '⏱')} {h((ch.get('created_at') or '')[:19])}")
        buttons.append([Button.inline(f"📊 #{ch['id']} - {ch['title'][:25]}",
                                      data=f"viewans:{ch['id']}".encode())])
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅️ قبلی", data=f"chpage:{page-1}".encode()))
    if page < pages - 1:
        nav.append(Button.inline("بعدی ➡️", data=f"chpage:{page+1}".encode()))
    if nav:
        buttons.append(nav)
    buttons.append([Button.inline("🔙 بازگشت", data=b"menu")])
    await safe_edit(event, "\n".join(lines), buttons=buttons, parse_mode="html")


async def _show_challenge_answers(event, ch):
    ch_id = ch["id"]
    ch_type = ch.get("ch_type") or "text"
    if ch_type == "poll":
        options = json.loads(ch["options"]) if ch.get("options") else []
        results = db.get_poll_results(ch_id, len(options))
        total = sum(results.values()) or 1
        lines = [f"{E('chart', '📊')} <b>نتایج نظرسنجی</b>\n{DIV}\n\n"
                 f"{E('diamond', '💎')} {h(ch['title'])}\n"
                 f"{E('user', '👤')} <code>{sum(results.values())}</code>\n"]
        for i, o in enumerate(options):
            n = results.get(i, 0)
            pct = int(100 * n / total)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            lines.append(f"\n{E('vote', '🗳')} <b>{h(o)}</b>\n<code>{bar}</code> {pct}% (<code>{n}</code>)")
        await safe_edit(event, "\n".join(lines),
                        buttons=[[Button.inline("🔙 بازگشت", data=b"my_challenges")]],
                        parse_mode="html")
        return
    answers = db.get_answers(ch_id)
    lines = [f"{E('message', '💬')} <b>پاسخ‌ها</b>\n{DIV}\n\n"
             f"{E('diamond', '💎')} {h(ch['title'])}\n"
             f"{E('user', '👤')} <code>{len(answers)}</code>\n"]
    if not answers:
        lines.append(f"\n{E('info', 'ℹ️')} هنوز کسی شرکت نکرده.")
    else:
        for i, a in enumerate(answers[:15], 1):
            uid_l = f'<a href="tg://user?id={a["user_id"]}">{a["user_id"]}</a>'
            un = f'@{a["username"]}' if a.get("username") else "—"
            lines.append(f"\n{E('fire', '🔥')} <b>#{i}</b>\n"
                         f"├ {E('user', '👤')} {h(a.get('user_name') or '—')}\n"
                         f"├ {E('id', '🆔')} {uid_l}\n"
                         f"├ {E('link', '🔗')} {h(un)}\n"
                         f"└ <blockquote>{h(a['answer'])}</blockquote>")
    await safe_edit(event, "\n".join(lines),
                    buttons=[[Button.inline("🔙 بازگشت", data=b"my_challenges")]],
                    parse_mode="html")


async def _announce_results(ch):
    ch_id = ch["id"]
    ch_type = ch.get("ch_type") or "text"
    gid = ch["group_id"]
    try:
        if ch_type == "poll":
            options = json.loads(ch["options"]) if ch.get("options") else []
            results = db.get_poll_results(ch_id, len(options))
            total = sum(results.values()) or 1
            lines = [f"{E('flag', '🏁')} <b>نظرسنجی بسته شد!</b>\n{DIV}\n\n"
                     f"{E('diamond', '💎')} {h(ch['title'])}\n"
                     f"{E('user', '👤')} <code>{sum(results.values())}</code>\n"]
            for i, o in enumerate(options):
                n = results.get(i, 0)
                pct = int(100 * n / total)
                bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                lines.append(f"{E('vote', '🗳')} <b>{h(o)}</b>\n<code>{bar}</code> {pct}%")
        else:
            answers = db.get_answers(ch_id)
            lines = [f"{E('flag', '🏁')} <b>چالش بسته شد!</b>\n{DIV}\n\n"
                     f"{E('diamond', '💎')} {h(ch['title'])}\n"
                     f"{E('user', '👤')} <code>{len(answers)}</code>\n"]
            for i, a in enumerate(answers[:10], 1):
                lines.append(f"\n{E('fire', '🔥')} <b>#{i}</b>\n<blockquote>{h(a['answer'])}</blockquote>")
        await safe_send(gid, "\n".join(lines), parse_mode="html")
    except Exception as e:
        logger.exception(f"announce: {e}")


async def deadline_watcher():
    await asyncio.sleep(5)
    while True:
        try:
            for ch in db.get_expired_challenges():
                try:
                    await _announce_results(ch)
                except Exception:
                    pass
                db.deactivate_challenge(ch["id"])
                db.mark_results_announced(ch["id"])
        except Exception as e:
            logger.exception(f"watcher: {e}")
        await asyncio.sleep(60)


# ═════════════════════════════════════════════
# 🌐 Web Server (برای Render)
# ═════════════════════════════════════════════
async def start_web_server():
    app = web.Application()

    async def health(request):
        return web.Response(text="OK — Unicorn Bot is running ✨")

    async def root(request):
        return web.Response(text=(
            f"🦄 UNICORN ANONY BOT\n"
            f"Status: Running\n"
            f"Admins: {len(ALL_ADMINS)}\n"
            f"Time: {now_str()}"
        ), content_type="text/plain")

    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/healthz", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server listening on 0.0.0.0:{PORT}")


# ═════════════════════════════════════════════
# main
# ═════════════════════════════════════════════
async def main():
    global BOT_USERNAME
    logger.info("🦄 UNICORN Bot starting...")

    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN لازمه")
    if not OWNER_ID:
        raise ValueError("❌ OWNER_ID لازمه")
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL لازمه")
    if not GROQ_API_KEY:
        raise ValueError("❌ GROQ_API_KEY لازمه")

    logger.info(f"👥 Admins ({len(ALL_ADMINS)}): {sorted(ALL_ADMINS)}")

    # وب سرور
    await start_web_server()

    # ربات
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    BOT_USERNAME = me.username
    logger.info(f"✅ Bot connected: @{BOT_USERNAME} (ID: {me.id})")

    try:
        await safe_send(
            OWNER_ID,
            f"{E('check', '✅')} <b>ربات روشن شد</b>\n{DIV}\n\n"
            f"{E('party', '🎉')} <b>UNICORN ANONY BOT</b>\n\n"
            f"{E('rocket', '🚀')} @{BOT_USERNAME}\n"
            f"{E('id', '🆔')} <code>{me.id}</code>\n"
            f"{E('crown', '👑')} ادمین‌ها: <code>{len(ALL_ADMINS)}</code>\n"
            f"{E('time', '⏱')} {now_str()}",
            parse_mode="html")
    except Exception as e:
        logger.warning(f"notify owner: {e}")

    asyncio.create_task(deadline_watcher())
    logger.info("✅ Ready! Listening for updates...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Stopped")
    except Exception as ex:
        logger.exception(f"❌ {ex}")