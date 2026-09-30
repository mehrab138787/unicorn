# -*- coding: utf-8 -*-
"""
🕵️ UNICORN SPY GAME — Detective Edition v2.0
هوش مصنوعی: انتخاب کلمه + تحلیل کلمات + بررسی حدس جاسوس
+ حالت‌های چند‌جاسوسه + XP + لیدربورد + دستاورد + تایمر زنده
+ رای مخفی + AI Narrator + کلمات ممنوعه + Rematch
"""

import re, random, asyncio, logging, time, json
from collections import OrderedDict
import requests
from telethon import events, Button
from telethon.errors import MessageNotModifiedError

logger = logging.getLogger("SpyGame")

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
SPY_REGISTRATION_TIMEOUT = 180   # 3 min برای ثبت‌نام
SPY_TURN_TIMEOUT = 200           # 200s برای هر نوبت
SPY_VOTE_TIMEOUT = 120           # 2 min برای رای‌گیری
SPY_MIN_PLAYERS = 3
SPY_MAX_PLAYERS = 15
SPY_SPEED_TURN_TIMEOUT = 45      # حالت سرعتی

# ⚠️ گیم‌های فعال — باید قبل از کلاس تعریف بشه
SPY_ACTIVE_GAMES = {}

# حالت‌های بازی
SPY_MODES = {
    "classic":    {"spies": 1, "label": "🎩 کلاسیک",     "min": 3, "desc": "یه جاسوس، یه کلمه"},
    "double":     {"spies": 2, "label": "👥 دو جاسوس",   "min": 6, "desc": "دو جاسوس که همدیگه رو می‌شناسن"},
    "mrwhite":    {"spies": 1, "label": "🎭 مستر وایت",  "min": 4, "desc": "جاسوس فقط دسته رو می‌دونه"},
    "speed":      {"spies": 1, "label": "⚡ سرعتی",      "min": 4, "desc": "زمان نوبت فقط ۴۵ ثانیه"},
    "undercover": {"spies": 1, "label": "🕵️ مخفی",       "min": 5, "desc": "دو کلمه‌ی مشابه بین بازیکنا پخش می‌شه"},
}

# دستاوردها
SPY_ACHIEVEMENTS = {
    "first_win":  ("🎖", "اولین برد"),
    "spy_master": ("🕵️", "استاد جاسوسی — ۵ برد جاسوس"),
    "detective":  ("🔍", "کارآگاه — ۱۰ برد شهروند"),
    "streak3":    ("🔥", "۳ برد پشت‌سرهم"),
    "mvp":        ("👑", "MVP بازی"),
    "survivor":   ("🛡", "بازمانده — زنده تا آخر"),
    "liar":       ("🎭", "دروغگوی حرفه‌ای"),
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
    "detective": "5424972470023104089", "brain": "5404654051945521778",
    "lock": "5397782960512444700", "vote": "5206607081334906820",
    "list": "5447410659077661506", "skip": "5424972470023104089",
    "clue": "5271604874419647061", "pin": "5397782960512444700",
    "point": "5397782960512444700",   # ✅ اضافه شد
    "medal": "5458603043203327669",    # ✅ اضافه شد
    "badge": "5447410659077661506",    # ✅ اضافه شد
    "xp": "6337048821603763745",       # ✅ اضافه شد
}

_TG_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="\d+">([^<]*)</tg-emoji>')


def PE(k, fb):
    eid = PREM.get(k)
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>' if eid else fb


def strip_premium(t):
    return _TG_EMOJI_RE.sub(r"\1", t)


def _emoji_err(ex):
    s = str(ex).lower()
    return ("document" in s) or ("invalid" in s and "inline" in s) or \
           ("custom emoji" in s) or ("emoji" in s and "invalid" in s)


def h(t):
    if t is None: return ""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def user_name(u):
    if not u: return "ناشناس"
    n = (getattr(u, "first_name", "") or "").strip()
    l = (getattr(u, "last_name", "") or "").strip()
    full = (n + " " + l).strip()
    return full or getattr(u, "username", None) or str(getattr(u, "id", "?"))


def now_ts():
    return int(time.time())


def normalize_fa(text):
    if not text: return text
    return (text.replace("ي", "ی").replace("ك", "ک")
                .replace("\u200c", "").replace("\u200f", "").replace("\u200e", ""))


# ═══════════════════════════════════════════════════════════
# SPY GAME
# ═══════════════════════════════════════════════════════════
class SpyGame:
    def __init__(self, client, db, groq_key, ai_models):
        self.client = client
        self.db = db
        self.groq_key = groq_key
        self.ai_models = ai_models
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self._running = False

    # ═══════════════ DB ═══════════════
    def _c(self):
        import psycopg2, psycopg2.extras
        try:
            if self.db.conn is None or self.db.conn.closed:
                self.db.reconnect()
            return self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        except Exception:
            self.db.reconnect()
            return self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def setup(self):
        c = self._c()
        c.execute("""CREATE TABLE IF NOT EXISTS spy_games (
            id BIGSERIAL PRIMARY KEY,
            group_id BIGINT,
            admin_id BIGINT,
            word TEXT,
            spy_uid BIGINT,
            winner TEXT,
            players_json TEXT,
            created_at BIGINT,
            finished_at BIGINT
        )""")
        # جدول آمار بازیکنا
        c.execute("""CREATE TABLE IF NOT EXISTS spy_stats (
            uid BIGINT PRIMARY KEY,
            name TEXT,
            xp INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            games INTEGER DEFAULT 0,
            spy_wins INTEGER DEFAULT 0,
            civ_wins INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]',
            updated_at BIGINT
        )""")
        # جدول تاریخچه دستاوردها
        c.execute("""CREATE TABLE IF NOT EXISTS spy_achievements_log (
            id BIGSERIAL PRIMARY KEY,
            uid BIGINT,
            key TEXT,
            name TEXT,
            group_id BIGINT,
            created_at BIGINT
        )""")
        logger.info("🕵️ Spy tables ready")

    # ═══════════════ SAFE SEND ═══════════════
    async def _safe_send(self, chat_id, text, **kw):
        try: return await self.client.send_message(chat_id, text, **kw)
        except MessageNotModifiedError: return None
        except Exception as ex:
            if _emoji_err(ex):
                try:
                    return await self.client.send_message(chat_id, strip_premium(text), **kw)
                except Exception: return None
            raise

    async def _safe_edit(self, chat_id, msg_id, text, buttons=None):
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
                except Exception: return False
            return False

    async def _safe_answer(self, event, text=None, alert=False):
        try: await event.answer(text, alert=alert)
        except Exception: pass

    # ═══════════════ AI CALLS ═══════════════
    def _ai_call(self, msgs, temp, model, max_tokens=400, json_mode=False):
        payload = {
            "model": model, "messages": msgs,
            "temperature": temp, "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = requests.post(self.groq_url,
                          headers={"Authorization": f"Bearer {self.groq_key}",
                                   "Content-Type": "application/json"},
                          json=payload, timeout=40)
        if r.status_code >= 400:
            try:
                logger.warning(f"Groq {r.status_code}: {r.text[:300]}")
            except Exception: pass
            raise RuntimeError(f"HTTP {r.status_code}")
        return r.json()

    async def ai_pick_word(self):
        """🎯 AI یه کلمه مناسب انتخاب می‌کنه"""
        sys_msg = (
            "تو یه طراح بازی «جاسوس» هستی.\n"
            "خروجی فقط JSON:\n"
            '{"word": "کلمه", "category": "دسته"}\n\n'
            "قوانین:\n"
            "1. کلمه باید فارسی، ساده، قابل توصیف باشه\n"
            "2. کلمه باید یکی از این دسته‌ها باشه: "
            "میوه، حیوان، شهر، غذا، شیء، مکان، ورزش، شغل، وسیله، فیلم، کتاب\n"
            "3. کلمه‌ای که همه بشناسن ولی نیاز به توصیف داشته باشه\n"
            "4. کلمه خیلی خاص یا خیلی عام نباشه\n"
            "5. فقط یک کلمه — نه دو کلمه\n"
            "6. مثل: پیتزا، شیر، تهران، فوتبال، کتاب، پلنگ، دریا، و...\n"
            "7. توضیح اضافه نده، فقط JSON"
        )
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": "یه کلمه جالب برای بازی جاسوس انتخاب کن."}]
        for model in self.ai_models:
            for att in range(2):
                try:
                    data = await asyncio.to_thread(self._ai_call,
                        msgs, 1.0 if att == 0 else 1.2, model, 200, True)
                    obj = json.loads(data["choices"][0]["message"]["content"])
                    word = str(obj.get("word", "")).strip()
                    cat = str(obj.get("category", "")).strip()
                    if not word or len(word) > 30: raise ValueError("bad")
                    if len(word.split()) > 2: raise ValueError("multi")
                    logger.info(f"🕵️ AI word: {word} ({cat}) via {model}")
                    return {"word": word, "category": cat}
                except Exception as e:
                    logger.warning(f"spy word fail {model}: {e}")
                    await asyncio.sleep(0.4)
        fallback = [("پیتزا", "غذا"), ("شیر", "حیوان"), ("تهران", "شهر"),
                    ("فوتبال", "ورزش"), ("کتاب", "شیء"), ("پلنگ", "حیوان"),
                    ("دریا", "مکان"), ("سیب", "میوه"), ("معلم", "شغل"),
                    ("موبایل", "وسیله")]
        w, c = random.choice(fallback)
        logger.info(f"🕵️ Fallback word: {w}")
        return {"word": w, "category": c}

    async def ai_pick_undercover_pair(self):
        """🎭 دو کلمه‌ی مشابه برای حالت مخفی"""
        sys_msg = (
            "تو یه طراح بازی «جاسوس — حالت مخفی» هستی.\n"
            "خروجی فقط JSON:\n"
            '{"main": "کلمه اصلی", "alt": "کلمه‌ی مشابه", "category": "دسته"}\n\n'
            "قوانین:\n"
            "- دو کلمه که خیلی شبیهن ولی یکسان نیستن (مثل پرتقال/نارنگی)\n"
            "- هر دو تک‌کلمه‌ای، فارسی، ساده باشن\n"
            "- فقط JSON"
        )
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": "یه جفت کلمه مشابه بده."}]
        for model in self.ai_models:
            for att in range(2):
                try:
                    data = await asyncio.to_thread(self._ai_call,
                        msgs, 0.9, model, 200, True)
                    obj = json.loads(data["choices"][0]["message"]["content"])
                    m = str(obj.get("main", "")).strip()
                    a = str(obj.get("alt", "")).strip()
                    cat = str(obj.get("category", "")).strip()
                    if not m or not a or m == a: raise ValueError("bad")
                    return {"main": m, "alt": a, "category": cat}
                except Exception as e:
                    logger.warning(f"undercover pair fail {model}: {e}")
                    await asyncio.sleep(0.4)
        return {"main": "پرتقال", "alt": "نارنگی", "category": "میوه"}

    async def ai_pick_forbidden(self, word, category):
        """🚫 AI چند کلمه‌ی ممنوعه انتخاب می‌کنه"""
        sys_msg = (
            "تو داور بازی جاسوسی.\n"
            "خروجی فقط JSON:\n"
            '{"forbidden": ["کلمه1", "کلمه2", "کلمه3"]}\n\n'
            f"کلمه مخفی: «{word}» — دسته: «{category}»\n"
            "سه کلمه‌ی خیلی نزدیک به کلمه اصلی که بازی‌کنا نباید مستقیم بگن رو انتخاب کن.\n"
            "کلمه‌ها تک‌کلمه‌ای و فارسی باشن. فقط JSON"
        )
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": "سه کلمه ممنوعه بده."}]
        for model in self.ai_models[:2]:
            for att in range(2):
                try:
                    data = await asyncio.to_thread(self._ai_call,
                        msgs, 0.6, model, 200, True)
                    obj = json.loads(data["choices"][0]["message"]["content"])
                    fw = [str(x).strip() for x in obj.get("forbidden", []) if str(x).strip()]
                    fw = [x for x in fw if normalize_fa(x) != normalize_fa(word)][:3]
                    if fw: return fw
                except Exception as e:
                    logger.warning(f"forbidden fail {model}: {e}")
                    await asyncio.sleep(0.3)
        return []

    async def ai_give_hint(self, word, category):
        """💡 AI یه راهنمای مبهم می‌ده"""
        sys_msg = (
            "تو راوی یه بازی جاسوسی هستی.\n"
            f"کلمه‌ی مخفی: «{word}» — دسته: «{category}»\n"
            "یه راهنمای خیلی مبهم بده که کلمه رو لو نده ولی کمک کنه.\n"
            "حداکثر ۱۰ کلمه. فقط متن، بدون JSON، بدون گیومه."
        )
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": "راهنمای مبهم بده."}]
        for model in self.ai_models[:3]:
            for att in range(2):
                try:
                    data = await asyncio.to_thread(self._ai_call,
                        msgs, 0.8, model, 100, False)
                    txt = data["choices"][0]["message"]["content"].strip()
                    txt = txt.strip('"').strip("«»").strip()
                    if txt and len(txt) < 200:
                        return txt
                except Exception as e:
                    logger.warning(f"hint fail {model}: {e}")
                    await asyncio.sleep(0.3)
        return f"به «{category}» فکر کن، ولی نه اون‌قدر نزدیک که لو بره!"

    async def ai_narrate(self, word, category, event_type, extra=""):
        """🎬 AI یه جمله‌ی دراماتیک می‌گه"""
        prompts = {
            "wrong_vote": f"یه شهروند اشتباهی اعدام شد. یه جمله‌ی دراماتیک بگو. {extra}",
            "round_start": f"راند جدید شروع شد. یه جمله‌ی هیجان‌انگیز برای شروع بگو. {extra}",
            "spy_caught": f"جاسوس لو رفت. یه جمله‌ی هیجانی بگو. {extra}",
            "spy_win": f"جاسوس برد. یه جمله‌ی پیروزمندانه بگو. {extra}",
            "civ_win": f"شهروندها بردن. یه جمله‌ی جشن بگو. {extra}",
        }
        sys_msg = (
            "تو راوی یه بازی جاسوسی هستی. لحن باحال، خودمونی، کوتاه.\n"
            f"کلمه مخفی: «{word}» — دسته: «{category}»\n"
            "فقط یک جمله (حداکثر ۱۵ کلمه). بدون JSON، بدون هشتگ، بدون ایموجی زیاد."
        )
        user_msg = prompts.get(event_type, "یه جمله باحال بگو.")
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}]
        for model in self.ai_models[:2]:
            try:
                data = await asyncio.to_thread(self._ai_call,
                    msgs, 0.95, model, 80, False)
                txt = data["choices"][0]["message"]["content"].strip()
                txt = txt.strip('"').strip("«»").strip()
                if txt and len(txt) < 200: return txt
            except Exception as e:
                logger.warning(f"narrate fail {model}: {e}")
        return None

    async def ai_check_guess(self, real_word, guess):
        """🎯 AI چک می‌کنه حدس درسته یا نه"""
        sys_msg = (
            "تو یه داور بازی جاسوس هستی.\n"
            "خروجی فقط JSON:\n"
            '{"correct": true/false}\n\n'
            "قوانین:\n"
            "- اگه حدس، همون کلمه‌ی درست یا مترادف نزدیکش باشه → correct: true\n"
            "- اگه کلمه متفاوت باشه → correct: false\n"
            "- به اختلاف حروف فارسی (ی/ي) توجه نکن\n"
            "- فقط JSON"
        )
        user_msg = f"کلمه درست: «{real_word}»\nحدس بازیکن: «{guess}»\n\nدرسته؟"
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}]
        for model in self.ai_models[:3]:
            for att in range(2):
                try:
                    data = await asyncio.to_thread(self._ai_call,
                        msgs, 0.3, model, 100, True)
                    obj = json.loads(data["choices"][0]["message"]["content"])
                    return bool(obj.get("correct", False))
                except Exception as e:
                    logger.warning(f"guess check fail {model}: {e}")
                    await asyncio.sleep(0.3)
        return normalize_fa(guess).strip() == normalize_fa(real_word).strip()

    async def ai_analyze_words(self, real_word, spy_name, spy_idx, messages):
        """🧠 AI همه پیام‌ها رو تحلیل می‌کنه و به هر نفر امتیاز می‌ده"""
        msgs_txt = "\n".join([f"#{i+1} {m['name']}: {m['msg']}"
                              for i, m in enumerate(messages)])
        sys_msg = (
            "تو یه کارآگاه باحال و تحلیل‌گر حرفه‌ای بازی جاسوس هستی.\n"
            f"کلمه اصلی: «{real_word}»\n"
            f"جاسوس: {spy_name} (شماره {spy_idx} توی لیست پیام‌ها)\n\n"
            "خروجی فقط JSON:\n"
            '{"analyses":[{"idx":1,"score":7,"reason":"جمله کوتاه ۱ خطی"}],'
            '"mvp_idx":1,"summary":"خلاصه‌ی ۱ جمله‌ای جذاب"}\n\n'
            "قوانین:\n"
            "- score از 0 تا 10: چقدر این نفر خوب بازی کرد\n"
            "- بازیکن خوب = توصیف دقیق ولی بدون لو دادن کلمه\n"
            "- جاسوس اگه موفق به مخفی‌کاری شده → امتیاز بالا\n"
            "- جاسوس اگه لو رفته → امتیاز پایین\n"
            "- reason: حداکثر ۱ خط کوتاه بامزه و مفید\n"
            "- لحن خودمونی، باحال، بدون تعارف\n"
            "- mvp_idx: بهترین بازیکن (شماره idx)\n"
            "- فقط JSON"
        )
        user_msg = (
            f"پیام‌های بازیکنان:\n{msgs_txt}\n\n"
            f"حالا همه رو تحلیل کن و به هرکس امتیاز بده."
        )
        msgs = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}]
        for model in self.ai_models:
            for att in range(2):
                try:
                    data = await asyncio.to_thread(self._ai_call,
                        msgs, 0.6, model, 1500, True)
                    obj = json.loads(data["choices"][0]["message"]["content"])
                    if "analyses" not in obj: raise ValueError("no analyses")
                    for a in obj["analyses"]:
                        a["score"] = max(0, min(10, int(a.get("score", 0))))
                        a.setdefault("reason", "—")
                    obj.setdefault("mvp_idx", 0)
                    obj.setdefault("summary", "بازی خوبی بود!")
                    return obj
                except Exception as e:
                    logger.warning(f"analyze fail {model}: {e}")
                    await asyncio.sleep(0.4)
        return {
            "analyses": [{"idx": i+1, "score": 5, "reason": "بازی خوب بود!"}
                         for i in range(len(messages))],
            "mvp_idx": 1, "summary": "بازی تموم شد!"
        }

    # ═══════════════ STATS / LEADERBOARD ═══════════════
    async def _update_stats(self, game, winner, unique_msgs, analyses):
        """ذخیره XP و آمار بازیکنا"""
        try:
            c = self._c()
        except Exception as e:
            logger.warning(f"stats cursor fail: {e}"); return

        # مپ idx → uid
        idx_uid = {}
        for i, m in enumerate(unique_msgs, 1):
            idx_uid[i] = m["uid"]
        scores = {idx_uid.get(a.get("idx"), 0): int(a.get("score", 5))
                  for a in analyses.get("analyses", [])}
        mvp_uid = idx_uid.get(analyses.get("mvp_idx"), None)

        spy_uids = game.get("spy_uids") or ([game["spy_uid"]] if game.get("spy_uid") else [])

        for uid, p in game["players"].items():
            is_spy = uid in spy_uids
            won = (winner == "spy" and is_spy) or (winner == "civilians" and not is_spy)

            # XP
            xp = 5
            if won: xp += 20
            if is_spy and won: xp += 15
            if uid == mvp_uid: xp += 10
            xp += min(10, scores.get(uid, 0))

            spy_win_inc = 1 if (is_spy and won) else 0
            civ_win_inc = 1 if (not is_spy and won) else 0
            win_inc = 1 if won else 0

            # دستاورد
            new_achs = []
            try:
                c.execute("SELECT * FROM spy_stats WHERE uid=%s", (uid,))
                row = c.fetchone()
                old_achs = []
                if row:
                    try: old_achs = json.loads(row.get("achievements") or "[]")
                    except Exception: old_achs = []
                streak = (row.get("streak") or 0) if row else 0
                new_streak = streak + 1 if won else 0

                # چک دستاوردها
                total_wins = ((row.get("wins") or 0) if row else 0) + win_inc
                spy_wins = ((row.get("spy_wins") or 0) if row else 0) + spy_win_inc
                civ_wins = ((row.get("civ_wins") or 0) if row else 0) + civ_win_inc

                if win_inc and "first_win" not in old_achs:
                    new_achs.append("first_win")
                if spy_wins >= 5 and "spy_master" not in old_achs:
                    new_achs.append("spy_master")
                if civ_wins >= 10 and "detective" not in old_achs:
                    new_achs.append("detective")
                if new_streak >= 3 and "streak3" not in old_achs:
                    new_achs.append("streak3")
                if uid == mvp_uid and "mvp" not in old_achs:
                    new_achs.append("mvp")
                if not is_spy and uid not in spy_uids and winner == "civilians" \
                        and p.get("alive", True) and "survivor" not in old_achs:
                    new_achs.append("survivor")
                if is_spy and won and game.get("spy_never_caught") and "liar" not in old_achs:
                    new_achs.append("liar")

                all_achs = list(set(old_achs + new_achs))
            except Exception as e:
                logger.warning(f"achievement check {uid}: {e}")
                all_achs = []
                new_streak = 0

            try:
                c.execute("""
                    INSERT INTO spy_stats
                        (uid, name, xp, wins, games, spy_wins, civ_wins,
                         streak, best_streak, achievements, updated_at)
                    VALUES (%s,%s,%s,%s,1,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (uid) DO UPDATE SET
                        name=EXCLUDED.name,
                        xp=spy_stats.xp + EXCLUDED.xp,
                        wins=spy_stats.wins + EXCLUDED.wins,
                        games=spy_stats.games + 1,
                        spy_wins=spy_stats.spy_wins + EXCLUDED.spy_wins,
                        civ_wins=spy_stats.civ_wins + EXCLUDED.civ_wins,
                        streak=%s,
                        best_streak=GREATEST(spy_stats.best_streak, %s),
                        achievements=%s,
                        updated_at=%s
                """, (
                    uid, p["name"], xp, win_inc, spy_win_inc, civ_win_inc,
                    new_streak, new_streak, json.dumps(all_achs, ensure_ascii=False),
                    now_ts(),
                    new_streak, new_streak,
                    json.dumps(all_achs, ensure_ascii=False), now_ts()
                ))
                # log new achievements
                for k in new_achs:
                    nm = SPY_ACHIEVEMENTS.get(k, ("", k))[1]
                    c.execute("""INSERT INTO spy_achievements_log
                        (uid, key, name, group_id, created_at)
                        VALUES (%s,%s,%s,%s,%s)""",
                        (uid, k, nm, game["group_id"], now_ts()))
            except Exception as e:
                logger.warning(f"save stats {uid}: {e}")

        # ذخیره دستاوردهای جدید برای اعلان
        game["_new_achievements"] = []
        for uid in game["players"]:
            for k in []:  # پر می‌شه در جای دیگه
                pass

    async def _fetch_leaderboard(self, limit=10):
        try:
            c = self._c()
            c.execute("""SELECT uid, name, xp, wins, games, spy_wins, civ_wins
                         FROM spy_stats ORDER BY xp DESC LIMIT %s""", (limit,))
            return c.fetchall() or []
        except Exception as e:
            logger.warning(f"lb fail: {e}"); return []

    async def _fetch_player_stats(self, uid):
        try:
            c = self._c()
            c.execute("SELECT * FROM spy_stats WHERE uid=%s", (uid,))
            return c.fetchone()
        except Exception: return None

    async def _fetch_group_stats(self, group_id):
        try:
            c = self._c()
            c.execute("""SELECT winner, COUNT(*) as c FROM spy_games
                         WHERE group_id=%s GROUP BY winner""", (group_id,))
            return c.fetchall() or []
        except Exception: return []

    # ═══════════════ LIVE COUNTDOWN ═══════════════
    async def _live_countdown(self, group_id, msg_id, base_text, seconds,
                               check_fn, tick=10):
        """هر tick ثانیه پیام رو با زمان باقی‌مونده ویرایش می‌کنه"""
        start = now_ts()
        try:
            while True:
                elapsed = now_ts() - start
                left = seconds - elapsed
                if left <= 0: break
                if not check_fn(): return
                bar_len = 12
                filled = max(0, int(bar_len * left / seconds))
                bar = "█" * filled + "░" * (bar_len - filled)
                try:
                    await self._safe_edit(group_id, msg_id,
                        f"{base_text}\n\n<code>{bar}</code>  {left}s")
                except Exception: pass
                await asyncio.sleep(tick)
        except asyncio.CancelledError: return

    # ═══════════════ HANDLERS ═══════════════
    def register_handlers(self):
        self.client.add_event_handler(self.on_message, events.NewMessage())
        self.client.add_event_handler(self.on_callback, events.CallbackQuery())
        self._running = True

    async def on_message(self, event):
        try:
            if event.is_private: return
            me = await self.client.get_me()
            if event.sender_id == me.id: return
            raw = (event.raw_text or "").strip()
            if not raw: return
            uid = event.sender_id
            low = normalize_fa(raw.lower().strip())

            # ─── بازی فعال در این گروه ───
            game = SPY_ACTIVE_GAMES.get(event.chat_id)
            if game:
                if (game["state"] == "playing"
                        and game.get("current_speaker") == uid):
                    await self._handle_player_turn(event, game, raw)
                    return
                if (game["state"] == "spy_guess"
                        and uid in (game.get("spy_uids") or [game.get("spy_uid")])):
                    await self._handle_spy_guess(event, game, raw)
                    return

            # ─── دستور لیدربورد ───
            if low in ("لیدربورد جاسوس", "spytop", "تاپ جاسوس", "لیدربورد"):
                await self._show_leaderboard(event.chat_id)
                return

            # ─── آمار شخصی ───
            if low in ("آمار جاسوس", "spystats", "آمار من"):
                await self._show_my_stats(event.chat_id, uid)
                return

            # ─── آمار گروه ───
            if low in ("آمار گروه جاسوس", "spygroup"):
                await self._show_group_stats(event.chat_id)
                return

            # ─── راهنما ───
            if low in ("راهنمای جاسوس", "spyhelp"):
                await self._show_help(event.chat_id)
                return

            # ─── دستور شروع (ادمین) ───
            if low in ("جاسوس", "بازی جاسوس", "spy"):
                if uid not in self._get_admins():
                    await self._safe_send(event.chat_id,
                        f"{PE('cross','❌')} <b>فقط ادمین‌ها می‌تونن بازی بسازن</b>",
                        parse_mode="html", reply_to=event.id)
                    return
                if event.chat_id in SPY_ACTIVE_GAMES:
                    await self._safe_send(event.chat_id,
                        f"{PE('warning','⚠️')} <b>یه بازی جاسوس در جریانه!</b>\n"
                        f"{PE('info','ℹ️')} صبر کن تموم بشه.",
                        parse_mode="html", reply_to=event.id)
                    return
                await self._start_registration(event.chat_id, uid)
                return

        except Exception as e:
            logger.exception(f"spy on_message: {e}")

    def _get_admins(self):
        try:
            from app import ALL_ADMINS
            return ALL_ADMINS
        except Exception:
            return set()

    # ═══════════════ LEADERBOARD / STATS UI ═══════════════
    async def _show_leaderboard(self, chat_id):
        rows = await self._fetch_leaderboard(10)
        if not rows:
            await self._safe_send(chat_id,
                f"{PE('info','ℹ️')} <i>هنوز کسی بازی نکرده!</i>",
                parse_mode="html")
            return
        lines = [f"{PE('trophy','🏆')}  <b>لیدربورد جاسوس</b>  {PE('trophy','🏆')}",
                 DIV, ""]
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(rows):
            badge = medals[i] if i < 3 else f"<code>{i+1}.</code>"
            xp = r.get("xp", 0)
            wins = r.get("wins", 0)
            games = r.get("games", 0)
            wr = f"{int(wins*100/games)}%" if games else "0%"
            lines.append(
                f"{badge} <b>{h(r.get('name','?'))}</b>\n"
                f"     {PE('xp','⚡')} <code>{xp}</code> XP  ·  "
                f"{PE('trophy','🏆')} <code>{wins}</code> برد  ·  "
                f"{PE('chart','📊')} <code>{wr}</code> نرخ برد"
            )
        lines.append("")
        lines.append(DIV2)
        lines.append(f"{PE('info','ℹ️')} <i>برای دیدن آمار خودت: «آمار جاسوس»</i>")
        await self._safe_send(chat_id, "\n".join(lines), parse_mode="html")

    async def _show_my_stats(self, chat_id, uid):
        row = await self._fetch_player_stats(uid)
        if not row:
            await self._safe_send(chat_id,
                f"{PE('info','ℹ️')} <i>هنوز بازی نکردی!</i>",
                parse_mode="html")
            return
        achs = []
        try: achs = json.loads(row.get("achievements") or "[]")
        except Exception: achs = []
        ach_lines = []
        for k in achs:
            em, nm = SPY_ACHIEVEMENTS.get(k, ("🏅", k))
            ach_lines.append(f"  {em} <i>{h(nm)}</i>")
        if not ach_lines:
            ach_lines = ["  <i>هنوز دستاوردی نداری</i>"]

        games = row.get("games", 0) or 0
        wins = row.get("wins", 0) or 0
        wr = f"{int(wins*100/games)}%" if games else "0%"
        text = (
            f"{PE('user','👤')}  <b>آمار {h(row.get('name','?'))}</b>\n"
            f"{DIV}\n\n"
            f"{PE('xp','⚡')} XP: <code>{row.get('xp',0)}</code>\n"
            f"{PE('trophy','🏆')} برد کل: <code>{wins}</code>\n"
            f"{PE('chart','📊')} نرخ برد: <code>{wr}</code>\n"
            f"{PE('detective','🕵️')} برد جاسوس: <code>{row.get('spy_wins',0)}</code>\n"
            f"{PE('trophy','🏅')} برد شهروند: <code>{row.get('civ_wins',0)}</code>\n"
            f"{PE('fire','🔥')} بهترین استریک: <code>{row.get('best_streak',0)}</code>\n\n"
            f"{DIV2}\n"
            f"{PE('medal','🎖')} <b>دستاوردها:</b>\n" + "\n".join(ach_lines)
        )
        await self._safe_send(chat_id, text, parse_mode="html")

    async def _show_group_stats(self, chat_id):
        rows = await self._fetch_group_stats(chat_id)
        if not rows:
            await self._safe_send(chat_id,
                f"{PE('info','ℹ️')} <i>هنوز بازی‌ای اینجا انجام نشده!</i>",
                parse_mode="html")
            return
        total = sum(r["c"] for r in rows)
        spy_w = next((r["c"] for r in rows if r["winner"] == "spy"), 0)
        civ_w = next((r["c"] for r in rows if r["winner"] == "civilians"), 0)
        text = (
            f"{PE('chart','📊')}  <b>آمار گروه</b>  {PE('chart','📊')}\n"
            f"{DIV}\n\n"
            f"{PE('list','📋')} کل بازی‌ها: <code>{total}</code>\n"
            f"{PE('detective','🕵️')} برد جاسوس: <code>{spy_w}</code>\n"
            f"{PE('trophy','🏆')} برد شهروند: <code>{civ_w}</code>\n"
        )
        await self._safe_send(chat_id, text, parse_mode="html")

    async def _show_help(self, chat_id):
        text = (
            f"{PE('detective','🕵️')}  <b>راهنمای بازی جاسوس</b>  {PE('detective','🕵️')}\n"
            f"{DIV}\n\n"
            f"{PE('rocket','🚀')} <b>شروع:</b> ادمین بنویسه <code>جاسوس</code>\n\n"
            f"{PE('list','📋')} <b>دستورات:</b>\n"
            f"  <code>جاسوس</code> — شروع بازی\n"
            f"  <code>لیدربورد جاسوس</code> — تاپ ۱۰\n"
            f"  <code>آمار جاسوس</code> — آمار خودت\n"
            f"  <code>آمار گروه جاسوس</code> — آمار این گروه\n"
            f"  <code>راهنمای جاسوس</code> — همین پیام\n\n"
            f"{PE('brain','🧠')} <b>حالت‌ها:</b>\n" +
            "\n".join([f"  {m['label']} — <i>{m['desc']}</i>"
                       for m in SPY_MODES.values()])
        )
        await self._safe_send(chat_id, text, parse_mode="html")

    # ═══════════════ REGISTRATION ═══════════════
    async def _start_registration(self, group_id, admin_id):
        game = {
            "group_id": group_id,
            "admin_id": admin_id,
            "state": "waiting",
            "mode": "classic",
            "word": None,
            "category": None,
            "word_alt": None,
            "spy_uid": None,
            "spy_uids": [],
            "spy_name": None,
            "spy_name_list": [],
            "players": {},
            "order": [],
            "current_index": 0,
            "round": 1,
            "join_msg_id": None,
            "turn_msg_id": None,
            "vote_msg_id": None,
            "current_speaker": None,
            "votes": {},
            "msg_history": [],
            "registration_task": None,
            "turn_task": None,
            "vote_task": None,
            "countdown_task": None,
            "forbidden": [],
            "round_marker": 1,
            "round_spoken": set(),
            "spy_never_caught": True,
        }
        SPY_ACTIVE_GAMES[group_id] = game

        await self._refresh_join_msg(game)

        game["registration_task"] = asyncio.create_task(
            self._registration_timeout(group_id))

    def _mode_desc_line(self, mode_key):
        m = SPY_MODES.get(mode_key, SPY_MODES["classic"])
        return f"  {m['label']} — <i>{m['desc']}</i>"

    async def _registration_timeout(self, group_id):
        try:
            await asyncio.sleep(SPY_REGISTRATION_TIMEOUT)
            game = SPY_ACTIVE_GAMES.get(group_id)
            if not game or game["state"] != "waiting": return
            min_req = SPY_MODES.get(game.get("mode","classic"), {}).get("min", SPY_MIN_PLAYERS)
            if len(game["players"]) < min_req:
                await self._safe_send(group_id,
                    f"{PE('hourglass','⏰')} <b>زمان ثبت‌نام تموم شد!</b>\n"
                    f"{PE('cross','❌')} تعداد بازیکن کافی نیست.",
                    parse_mode="html")
                SPY_ACTIVE_GAMES.pop(group_id, None)
            else:
                await self._begin_game(group_id)
        except asyncio.CancelledError: return
        except Exception as e: logger.exception(f"reg timeout: {e}")

    async def _refresh_join_msg(self, game):
        mid = game.get("join_msg_id")
        c = len(game["players"])
        pl = list(game["players"].values())
        mode = SPY_MODES.get(game.get("mode","classic"), SPY_MODES["classic"])
        if c == 0:
            nb = f"     {PE('cross','➖')} <i>هنوز کسی نیست</i>"
        else:
            lines = []
            for i, p in enumerate(pl[:15]):
                u = f"  <i>@{p['username']}</i>" if p.get("username") else ""
                lines.append(f"  {PE('check','✅')} <b>{h(p['name'])}</b>{u}")
            nb = "\n".join(lines)
        min_req = mode["min"]
        text = (
            f"{PE('detective','🕵️')}  <b>بازی جـاسـوس</b>  {PE('detective','🕵️')}\n"
            f"{DIV}\n\n"
            f"{PE('sparkle','✨')} <b>یه بازی هیجان‌انگیز شروع می‌شه!</b>\n\n"
            f"{PE('brain','🧠')} <b>حالت فعلی:</b> {mode['label']}\n"
            f"     <i>{mode['desc']}</i>\n\n"
            f"{PE('info','ℹ️')} <b>قوانین:</b>\n"
            f"   {PE('brain','🧠')} همه یه کلمه‌ی مخفی می‌گیرن\n"
            f"   {PE('lock','🔒')} به یکی می‌گیم «تو جاسوسی»\n"
            f"   {PE('message','💬')} نوبتی در مورد کلمه حرف می‌زنید\n"
            f"   {PE('vote','🗳')} بعدش رای می‌دید کی جاسوسه\n"
            f"   {PE('target','🎯')} جاسوس فرصت حدس کلمه داره\n\n"
            f"{DIV2}\n"
            f"{PE('crown','👑')} <b>شرکت‌کنندگان ({c}):</b>\n{nb}\n"
            f"{DIV2}\n"
            f"{PE('alert','⚠️')} حداقل <code>{min_req}</code> نفر لازمه\n\n"
            f"{PE('rocket','🚀')} <b>برای شرکت دکمه بزن:</b>"
        )
        rows = []
        rows.append([Button.inline(f"✋ شرکت می‌کنم ({c})",
                                    data=f"spy:join:{game['group_id']}".encode())])
        # دکمه‌های حالت
        mkeys = list(SPY_MODES.keys())
        mrow = []
        for k in mkeys[:3]:
            m = SPY_MODES[k]
            label = ("🟢 " if k == game.get("mode") else "") + m["label"]
            mrow.append(Button.inline(label, data=f"spy:mode:{game['group_id']}:{k}".encode()))
        rows.append(mrow)
        mrow2 = []
        for k in mkeys[3:]:
            m = SPY_MODES[k]
            label = ("🟢 " if k == game.get("mode") else "") + m["label"]
            mrow2.append(Button.inline(label, data=f"spy:mode:{game['group_id']}:{k}".encode()))
        if mrow2: rows.append(mrow2)
        rows.append([Button.inline("▶️ شروع بازی (ادمین)",
                                    data=f"spy:start:{game['group_id']}".encode())])
        rows.append([Button.inline("❌ لغو",
                                    data=f"spy:cancel:{game['group_id']}".encode())])

        if mid:
            await self._safe_edit(game["group_id"], mid, text, buttons=rows)
        else:
            sent = await self._safe_send(game["group_id"], text,
                                          buttons=rows, parse_mode="html")
            if sent: game["join_msg_id"] = sent.id

    # ═══════════════ BEGIN GAME ═══════════════
    async def _begin_game(self, group_id):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game: return

        if game.get("registration_task"):
            try: game["registration_task"].cancel()
            except Exception: pass

        players = list(game["players"].keys())
        mode_key = game.get("mode", "classic")
        mode = SPY_MODES.get(mode_key, SPY_MODES["classic"])
        min_req = mode["min"]
        if len(players) < min_req:
            await self._safe_send(group_id,
                f"{PE('cross','❌')} <b>برای این حالت حداقل {min_req} نفر لازمه!</b>",
                parse_mode="html")
            SPY_ACTIVE_GAMES.pop(group_id, None)
            return

        # انتخاب کلمه با AI
        wm = await self._safe_send(group_id,
            f"{PE('brain','🧠')} <b>AI در حال انتخاب کلمه...</b>\n"
            f"{PE('hourglass','⏳')} <i>چند لحظه صبر کنید...</i>",
            parse_mode="html")

        # حالت مخفی: دو کلمه مشابه
        if mode_key == "undercover":
            pair = await ai_pick_undercover_pair_safe(self)
            game["word"] = pair["main"]
            game["word_alt"] = pair["alt"]
            game["category"] = pair.get("category", "")
        else:
            w = await self.ai_pick_word()
            game["word"] = w["word"]
            game["word_alt"] = None
            game["category"] = w.get("category", "")

        # کلمات ممنوعه
        try:
            game["forbidden"] = await self.ai_pick_forbidden(
                game["word"], game.get("category", ""))
        except Exception:
            game["forbidden"] = []

        # انتخاب جاسوس(ها)
        n_spies = mode["spies"]
        spy_uids = random.sample(players, min(n_spies, len(players) - 1))
        game["spy_uids"] = spy_uids
        game["spy_uid"] = spy_uids[0]
        game["spy_name_list"] = [game["players"][u]["name"] for u in spy_uids]
        game["spy_name"] = " و ".join(game["spy_name_list"])

        # ارسال PV
        for uid in players:
            try:
                p = game["players"][uid]
                is_spy = uid in spy_uids
                if is_spy:
                    if mode_key == "mrwhite":
                        spy_text = (
                            f"{PE('detective','🕵️')}  <b>تو مستر وایت هستی!</b>  {PE('detective','🕵️')}\n"
                            f"{DIV}\n\n"
                            f"{PE('lock','🔒')} کلمه‌ی مخفی رو <b>نمی‌دونی</b>!\n"
                            f"{PE('info','ℹ️')} فقط دسته رو می‌دونی: <b>{h(game.get('category','؟'))}</b>\n"
                            f"{PE('eye','👁')} باید خودت کلمه رو حدس بزنی و مثل بقیه حرف بزنی\n\n"
                            f"{PE('rocket','🚀')} <b>موفق باشی!</b>"
                        )
                    else:
                        mates = [game["players"][u]["name"] for u in spy_uids if u != uid]
                        mate_line = ""
                        if mates:
                            mate_line = (f"\n{PE('user','👥')} هم‌تیمی: "
                                         f"<b>{h(' و '.join(mates))}</b>\n")
                        spy_text = (
                            f"{PE('detective','🕵️')}  <b>تو جـاسـوسـی!</b>  {PE('detective','🕵️')}\n"
                            f"{DIV}\n\n"
                            f"{PE('lock','🔒')} کلمه‌ی مخفی رو <b>نمی‌دونی</b>!\n"
                            f"{mate_line}"
                            f"{PE('eye','👁')} سعی کن با حرف‌هات مثل بقیه به نظر بیای\n"
                            f"{PE('alert','⚠️')} اگه لو بری، باید کلمه رو حدس بزنی!\n\n"
                            f"{PE('info','ℹ️')} <i>دسته:</i> {h(game.get('category','؟'))}\n\n"
                            f"{PE('rocket','🚀')} <b>موفق باشی!</b>"
                        )
                    await self._safe_send(uid, spy_text, parse_mode="html")
                else:
                    # شهروند
                    if mode_key == "undercover":
                        # بعضی‌ها کلمه اصلی، بعضی‌ها کلمه‌ی مشابه
                        my_word = game["word_alt"] if random.random() < 0.5 else game["word"]
                        civ_text = (
                            f"{PE('sparkle','✨')}  <b>کلمه‌ی مخفی تو</b>  {PE('sparkle','✨')}\n"
                            f"{DIV}\n\n"
                            f"{PE('diamond','💎')} <b>{h(my_word)}</b>\n\n"
                            f"{PE('info','ℹ️')} <i>دسته:</i> {h(game.get('category','؟'))}\n\n"
                            f"{PE('alert','⚠️')} <b>به هیچ‌کس کلمه رو نگو!</b>\n"
                            f"{PE('message','💬')} توضیح بده ولی مستقیم نگو!"
                        )
                    else:
                        civ_text = (
                            f"{PE('sparkle','✨')}  <b>کلمه‌ی مخفی تو</b>  {PE('sparkle','✨')}\n"
                            f"{DIV}\n\n"
                            f"{PE('diamond','💎')} <b>{h(game['word'])}</b>\n\n"
                            f"{PE('info','ℹ️')} <i>دسته:</i> {h(game.get('category','؟'))}\n\n"
                            f"{PE('alert','⚠️')} <b>به هیچ‌کس کلمه رو نگو!</b>\n"
                            f"{PE('message','💬')} توضیح بده ولی مستقیم نگو!"
                        )
                    await self._safe_send(uid, civ_text, parse_mode="html")
            except Exception as e:
                logger.warning(f"PM {uid} failed: {e}")

        try: await wm.delete()
        except Exception: pass

        # نمایش شروع
        mode_line = f"{PE('brain','🧠')} حالت: <b>{mode['label']}</b>\n"
        forbid_line = ""
        if game["forbidden"]:
            fw = "، ".join([f"<code>{h(x)}</code>" for x in game["forbidden"]])
            forbid_line = f"{PE('cross','🚫')} کلمات ممنوعه: {fw}\n"
        await self._safe_send(group_id,
            f"{PE('party','🎉')}  <b>بازی شـروع شد!</b>  {PE('party','🎉')}\n"
            f"{DIV}\n\n"
            f"{mode_line}"
            f"{PE('gem','💎')} کلمه‌ها به پیوی فرستاده شد\n"
            f"{PE('crown','👑')} <b>{len(spy_uids)} نفر جاسوسن!</b>\n"
            f"{forbid_line}\n"
            f"{PE('info','ℹ️')} به ترتیب، هر کس یه جمله/کلمه در مورد کلمه بگه\n"
            f"{PE('alert','⚠️')} <b>مستقیم نگو کلمه چیه!</b>",
            parse_mode="html")

        # شروع نوبت‌ها
        game["order"] = list(players)
        random.shuffle(game["order"])
        game["current_index"] = 0
        game["state"] = "playing"
        game["round"] = 1
        game["round_marker"] = 1
        game["round_spoken"] = set()
        await asyncio.sleep(2)
        await self._next_turn(group_id)

    # ═══════════════ TURN SYSTEM ═══════════════
    async def _next_turn(self, group_id):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game or game["state"] not in ("playing",): return

        if game.get("turn_msg_id"):
            try: await self.client.delete_messages(group_id, game["turn_msg_id"])
            except Exception: pass
            game["turn_msg_id"] = None

        if game.get("turn_task"):
            try: game["turn_task"].cancel()
            except Exception: pass
            game["turn_task"] = None

        if game.get("countdown_task"):
            try: game["countdown_task"].cancel()
            except Exception: pass
            game["countdown_task"] = None

        alive_order = [u for u in game["order"] if game["players"][u]["alive"]]
        if not alive_order:
            await self._end_game(group_id, "spy")
            return

        while game["current_index"] < len(game["order"]):
            uid = game["order"][game["current_index"]]
            if game["players"][uid]["alive"]:
                break
            game["current_index"] += 1

        if game["current_index"] >= len(game["order"]):
            await self._round_end(group_id)
            return

        uid = game["order"][game["current_index"]]
        p = game["players"][uid]
        game["current_speaker"] = uid

        alive_uids = [u for u in game["order"] if game["players"][u]["alive"]]
        pos = alive_uids.index(uid) + 1

        # نمایش وضعیت حرف‌زده‌ها
        status = []
        for u in alive_uids:
            mark = "✅" if u in game["round_spoken"] else "⏳"
            nm = game["players"][u]["name"]
            if u == uid:
                status.append(f"  {PE('target','🎯')} <b>{h(nm)}</b>")
            else:
                status.append(f"  {mark} {h(nm)}")
        status_txt = "\n".join(status)

        # زمان
        timeout = SPY_SPEED_TURN_TIMEOUT if game.get("mode") == "speed" else SPY_TURN_TIMEOUT
        forbid_txt = ""
        if game.get("forbidden"):
            forbid_txt = (f"\n{PE('cross','🚫')} ممنوع: "
                          + "، ".join([f"<code>{h(x)}</code>" for x in game["forbidden"]]))

        base_text = (
            f"{PE('target','🎯')}  <b>نوبت {h(p['name'])}</b>\n"
            f"{DIV}\n\n"
            f"{PE('chart','📊')} دور <code>{game['round']}</code>  ·  "
            f"نفر <code>{pos}/{len(alive_uids)}</code>\n\n"
            f"{PE('message','💬')} <b>{h(p['name'])}</b> یه کلمه یا جمله در مورد "
            f"کلمه‌ی مخفی بگو\n"
            f"{PE('alert','⚠️')} <i>مستقیم نگو کلمه چیه!</i>"
            f"{forbid_txt}\n\n"
            f"{PE('list','📋')} <b>وضعیت:</b>\n{status_txt}\n\n"
            f"{PE('hourglass','⏳')} فرصت: <code>{timeout}</code> ثانیه"
        )
        sent = await self._safe_send(group_id, base_text, parse_mode="html")
        if sent:
            game["turn_msg_id"] = sent.id
            # استارت countdown
            game["countdown_task"] = asyncio.create_task(
                self._live_countdown(group_id, sent.id, base_text, timeout,
                    lambda: (SPY_ACTIVE_GAMES.get(group_id) is game
                             and game["state"] == "playing"
                             and game.get("current_speaker") == uid)))

        game["turn_task"] = asyncio.create_task(
            self._turn_timeout(group_id, uid))

    async def _turn_timeout(self, group_id, uid):
        try:
            timeout = SPY_TURN_TIMEOUT
            g = SPY_ACTIVE_GAMES.get(group_id)
            if g and g.get("mode") == "speed":
                timeout = SPY_SPEED_TURN_TIMEOUT
            await asyncio.sleep(timeout)
            game = SPY_ACTIVE_GAMES.get(group_id)
            if not game or game["state"] != "playing": return
            if game.get("current_speaker") != uid: return
            p = game["players"].get(uid)
            if not p: return
            await self._safe_send(group_id,
                f"{PE('hourglass','⏰')} <b>وقت {h(p['name'])} تموم شد!</b>\n"
                f"{PE('skip','⏭')} نوبت می‌ره بعدی...",
                parse_mode="html")
            game["msg_history"].append({
                "uid": uid, "name": p["name"], "msg": "(سکوت)"
            })
            game["current_index"] += 1
            game["current_speaker"] = None
            await self._next_turn(group_id)
        except asyncio.CancelledError: return
        except Exception as e: logger.exception(f"turn timeout: {e}")

    async def _handle_player_turn(self, event, game, raw):
        uid = event.sender_id
        if uid != game.get("current_speaker"): return
        p = game["players"].get(uid)
        if not p: return

        # چک کلمات ممنوعه
        if game.get("forbidden"):
            low = normalize_fa(raw.lower())
            for fw in game["forbidden"]:
                if normalize_fa(fw).lower() in low:
                    await self._safe_send(event.chat_id,
                        f"{PE('warning','🚫')} <b>{h(p['name'])}</b>، "
                        f"کلمه‌ی «<code>{h(fw)}</code>» ممنوعه بود!\n"
                        f"{PE('skip','⏭')} این نوبت سوخت.",
                        parse_mode="html")
                    game["msg_history"].append({
                        "uid": uid, "name": p["name"], "msg": "(کلمه ممنوعه)"
                    })
                    if game.get("turn_task"):
                        try: game["turn_task"].cancel()
                        except Exception: pass
                        game["turn_task"] = None
                    if game.get("countdown_task"):
                        try: game["countdown_task"].cancel()
                        except Exception: pass
                        game["countdown_task"] = None
                    if game.get("turn_msg_id"):
                        try: await self.client.delete_messages(game["group_id"], game["turn_msg_id"])
                        except Exception: pass
                        game["turn_msg_id"] = None
                    game["current_speaker"] = None
                    game["current_index"] += 1
                    await asyncio.sleep(1)
                    await self._next_turn(game["group_id"])
                    return

        if game.get("turn_task"):
            try: game["turn_task"].cancel()
            except Exception: pass
            game["turn_task"] = None
        if game.get("countdown_task"):
            try: game["countdown_task"].cancel()
            except Exception: pass
            game["countdown_task"] = None

        game["msg_history"].append({
            "uid": uid, "name": p["name"], "msg": raw[:200]
        })
        game["round_spoken"].add(uid)

        try:
            await event.reply(f"{PE('check','✅')} <b>ثبت شد!</b>",
                              parse_mode="html")
        except Exception: pass

        if game.get("turn_msg_id"):
            try: await self.client.delete_messages(game["group_id"], game["turn_msg_id"])
            except Exception: pass
            game["turn_msg_id"] = None

        game["current_speaker"] = None
        game["current_index"] += 1
        await asyncio.sleep(1)
        await self._next_turn(game["group_id"])

    # ═══════════════ ROUND END ═══════════════
    async def _round_end(self, group_id):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game: return
        game["state"] = "round_end"

        text = (
            f"{PE('flag','🏁')}  <b>راند {game['round']} تموم شد!</b>\n"
            f"{DIV}\n\n"
            f"{PE('info','ℹ️')} حالا چی می‌خواید بکنید؟\n\n"
            f"{PE('vote','🗳')} <b>رای‌گیری</b> — کی جاسوسه؟\n"
            f"{PE('rocket','🚀')} <b>ادامه</b> — یه راند دیگه حرف بزنید"
        )
        btns = [
            [Button.inline("🗳 رای‌گیری", data=f"spy:vote_start:{group_id}".encode())],
            [Button.inline("🚀 ادامه بازی", data=f"spy:next_round:{group_id}".encode())],
        ]
        await self._safe_send(group_id, text, buttons=btns, parse_mode="html")

    # ═══════════════ VOTING ═══════════════
    async def _start_voting(self, group_id):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game: return
        game["state"] = "voting"
        game["votes"] = {}

        alive_uids = [u for u in game["order"] if game["players"][u]["alive"]]
        rows = []
        row = []
        for u in alive_uids:
            p = game["players"][u]
            row.append(Button.inline(f"🕵️ {p['name'][:20]}",
                                      data=f"spy:vote:{group_id}:{u}".encode()))
            if len(row) == 2:
                rows.append(row); row = []
        if row: rows.append(row)

        text = (
            f"{PE('vote','🗳')}  <b>رای‌گیری شروع شد!</b>  {PE('vote','🗳')}\n"
            f"{DIV}\n\n"
            f"{PE('info','ℹ️')} به کی رای می‌دید؟ کی جاسوسه؟\n"
            f"{PE('alert','⚠️')} <i>رای‌ها مخفی‌ان تا آخر</i>\n\n"
            f"{PE('chart','📊')} رای داده: <code>0/{len(alive_uids)}</code>\n"
            f"{PE('hourglass','⏳')} زمان: <code>{SPY_VOTE_TIMEOUT}</code> ثانیه"
        )
        sent = await self._safe_send(group_id, text, buttons=rows, parse_mode="html")
        if sent: game["vote_msg_id"] = sent.id

        game["vote_task"] = asyncio.create_task(
            self._vote_timeout(group_id, len(alive_uids)))

    async def _vote_timeout(self, group_id, total):
        try:
            await asyncio.sleep(SPY_VOTE_TIMEOUT)
            await self._tally_votes(group_id)
        except asyncio.CancelledError: return
        except Exception as e: logger.exception(f"vote timeout: {e}")

    async def _refresh_vote_msg(self, game):
        mid = game.get("vote_msg_id")
        if not mid: return
        alive_uids = [u for u in game["order"] if game["players"][u]["alive"]]
        total = len(alive_uids)
        done = len(game["votes"])

        rows = []
        row = []
        for u in alive_uids:
            p = game["players"][u]
            row.append(Button.inline(f"🕵️ {p['name'][:20]}",
                                      data=f"spy:vote:{game['group_id']}:{u}".encode()))
            if len(row) == 2:
                rows.append(row); row = []
        if row: rows.append(row)

        text = (
            f"{PE('vote','🗳')}  <b>رای‌گیری</b>  {PE('vote','🗳')}\n"
            f"{DIV}\n\n"
            f"{PE('info','ℹ️')} به کی رای می‌دید؟ کی جاسوسه؟\n"
            f"{PE('alert','⚠️')} <i>رای‌ها مخفی‌ان</i>\n\n"
            f"{PE('chart','📊')} رای داده: <code>{done}/{total}</code>"
        )
        await self._safe_edit(game["group_id"], mid, text, buttons=rows)

    async def _handle_vote(self, event, group_id, target_uid):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game or game["state"] != "voting":
            await self._safe_answer(event, "الان رای‌گیری نیست", alert=True); return
        voter = event.sender_id
        if voter not in game["players"] or not game["players"][voter]["alive"]:
            await self._safe_answer(event, "تو بازیکن نیستی", alert=True); return
        if target_uid == voter:
            await self._safe_answer(event, "به خودت نمی‌تونی رای بدی", alert=True); return
        if voter in game["votes"]:
            await self._safe_answer(event, "قبلاً رای دادی!", alert=True); return
        if target_uid not in game["players"] or not game["players"][target_uid]["alive"]:
            await self._safe_answer(event, "این بازیکن نیست", alert=True); return

        game["votes"][voter] = target_uid
        tname = game["players"][target_uid]["name"]
        # فقط به خود رای‌دهنده بگو
        await self._safe_answer(event, f"✅ رای تو به {tname} ثبت شد (مخفی)")
        await self._refresh_vote_msg(game)

        alive_uids = [u for u in game["order"] if game["players"][u]["alive"]]
        if len(game["votes"]) >= len(alive_uids):
            if game.get("vote_task"):
                try: game["vote_task"].cancel()
                except Exception: pass
            await asyncio.sleep(1)
            await self._tally_votes(group_id)

    async def _tally_votes(self, group_id):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game or game["state"] != "voting": return
        game["state"] = "tally"

        if not game["votes"]:
            await self._safe_send(group_id,
                f"{PE('info','ℹ️')} هیچ‌کس رای نداد!\n"
                f"{PE('rocket','🚀')} بازی ادامه داره...",
                parse_mode="html")
            game["state"] = "playing"
            game["current_index"] = 0
            game["round"] += 1
            game["round_spoken"] = set()
            await asyncio.sleep(2)
            await self._next_turn(group_id)
            return

        counts = {}
        for voter, target in game["votes"].items():
            counts[target] = counts.get(target, 0) + 1

        max_v = max(counts.values())
        top = [u for u, c in counts.items() if c == max_v]

        if len(top) > 1:
            await self._safe_send(group_id,
                f"{PE('warning','⚠️')} <b>رای‌ها مساوی شد!</b>\n"
                f"{PE('info','ℹ️')} کسی حذف نمی‌شه — بازی ادامه داره.",
                parse_mode="html")
            game["state"] = "playing"
            game["current_index"] = 0
            game["round"] += 1
            game["round_spoken"] = set()
            await asyncio.sleep(2)
            await self._next_turn(group_id)
            return

        voted_uid = top[0]
        voted_name = game["players"][voted_uid]["name"]

        # ─── افشای تدریجی رای‌ها ───
        reveal = [f"{PE('vote','🗳')} <b>افشای رای‌ها...</b>", DIV, ""]
        for voter, target in game["votes"].items():
            vn = game["players"][voter]["name"]
            tn = game["players"][target]["name"]
            reveal.append(f"  {PE('point','👉')} <b>{h(vn)}</b> → <b>{h(tn)}</b>")
        await self._safe_send(group_id, "\n".join(reveal), parse_mode="html")
        await asyncio.sleep(1)

        # نتیجه
        lines = [f"{PE('vote','🗳')} <b>نتیجه نهایی:</b>", DIV, ""]
        by_voter = {}
        for v, t in game["votes"].items():
            by_voter.setdefault(t, []).append(game["players"][v]["name"])
        for target_uid, voters in sorted(by_voter.items(),
                                          key=lambda x: -len(x[1])):
            tn = game["players"][target_uid]["name"]
            voters_str = "، ".join(voters)
            lines.append(f"  {PE('point','👉')} <b>{h(tn)}</b> "
                         f"({len(voters)}) — از: {h(voters_str)}")
        lines.append("")
        lines.append(f"{DIV2}")
        lines.append(f"{PE('alert','⚠️')} <b>بیشترین رای:</b> {h(voted_name)}")
        await self._safe_send(group_id, "\n".join(lines), parse_mode="html")
        await asyncio.sleep(1.5)

        spy_uids = game.get("spy_uids") or [game["spy_uid"]]

        if voted_uid in spy_uids:
            # جاسوس لو رفت — حذفش از لیست
            game["spy_never_caught"] = False
            await self._safe_send(group_id,
                f"{PE('fire','🔥')} <b>جاسوس لو رفت!</b> {PE('fire','🔥')}\n"
                f"{DIV}\n\n"
                f"{PE('crown','👑')} <b>{h(voted_name)}</b> جاسوس بود!\n\n"
                f"{PE('target','🎯')} ولی هنوز یه فرصت داره:\n"
                f"{PE('brain','🧠')} <b>کلمه‌ی مخفی رو حدس بزنه!</b>",
                parse_mode="html")
            await asyncio.sleep(2)
            game["state"] = "spy_guess"
            game["guessing_spy"] = voted_uid
            await self._safe_send(group_id,
                f"{PE('message','💬')} <b>{h(voted_name)}</b> جان، "
                f"کلمه رو توی گروه بنویس!",
                parse_mode="html")
        else:
            game["players"][voted_uid]["alive"] = False
            # AI hint بده
            try:
                hint = await self.ai_give_hint(game["word"], game.get("category", ""))
            except Exception:
                hint = None

            # AI narration
            narr = None
            try:
                narr = await self.ai_narrate(game["word"], game.get("category", ""),
                                              "wrong_vote",
                                              extra=f"بازیکن حذف‌شده: {voted_name}")
            except Exception: pass

            hint_line = f"\n{PE('clue','💡')} <b>راهنما:</b> <i>{h(hint)}</i>" if hint else ""
            narr_line = f"\n\n{PE('wave','🎬')} <i>{h(narr)}</i>" if narr else ""

            await self._safe_send(group_id,
                f"{PE('warning','😢')} <b>اشتباه بود!</b>\n"
                f"{DIV}\n\n"
                f"{PE('cross','❌')} <b>{h(voted_name)}</b> یه شهروند بود!\n"
                f"{PE('info','ℹ️')} جاسوس هنوز توی بازیه!\n"
                f"{hint_line}"
                f"{narr_line}",
                parse_mode="html")
            await asyncio.sleep(2)

            alive_uids = [u for u in game["order"] if game["players"][u]["alive"]]
            spy_alive = [u for u in alive_uids if u in spy_uids]
            civilians = [u for u in alive_uids if u not in spy_uids]

            # شرط برد: تعداد جاسوس‌ها >= تعداد شهروندها یا شهروند <= 1
            if len(civilians) <= len(spy_alive) or len(civilians) <= 1:
                await self._end_game(group_id, "spy")
            else:
                game["state"] = "playing"
                game["current_index"] = 0
                game["round"] += 1
                game["round_spoken"] = set()
                await self._safe_send(group_id,
                    f"{PE('rocket','🚀')} <b>راند {game['round']} شروع می‌شه!</b>",
                    parse_mode="html")
                await asyncio.sleep(2)
                await self._next_turn(group_id)

    # ═══════════════ SPY GUESS ═══════════════
    async def _handle_spy_guess(self, event, game, raw):
        uid = event.sender_id
        spy_uids = game.get("spy_uids") or [game["spy_uid"]]
        if uid not in spy_uids: return
        if game["state"] != "spy_guess": return
        if game.get("guessing_spy") and uid != game["guessing_spy"]: return

        guess = raw.strip()[:50]
        game["state"] = "checking_guess"

        wm = await self._safe_send(event.chat_id,
            f"{PE('brain','🧠')} <b>AI در حال بررسی حدس...</b>",
            parse_mode="html")

        correct = await self.ai_check_guess(game["word"], guess)

        try: await wm.delete()
        except Exception: pass

        if correct:
            await self._safe_send(event.chat_id,
                f"{PE('check','✅')} <b>درست بود!</b>\n"
                f"{DIV}\n\n"
                f"{PE('diamond','💎')} کلمه‌ی مخفی: <b>{h(game['word'])}</b>\n"
                f"{PE('target','🎯')} حدس: <b>{h(guess)}</b>\n\n"
                f"{PE('crown','👑')} <b>جاسوس برد!</b> {PE('party','🎉')}",
                parse_mode="html")
            await self._end_game(event.chat_id, "spy")
        else:
            await self._safe_send(event.chat_id,
                f"{PE('cross','❌')} <b>اشتباه بود!</b>\n"
                f"{DIV}\n\n"
                f"{PE('diamond','💎')} کلمه‌ی مخفی: <b>{h(game['word'])}</b>\n"
                f"{PE('target','🎯')} حدس تو: <b>{h(guess)}</b>\n\n"
                f"{PE('trophy','🏆')} <b>شهروندها بردن!</b> {PE('party','🎉')}",
                parse_mode="html")
            await self._end_game(event.chat_id, "civilians")

    # ═══════════════ END GAME ═══════════════
    async def _end_game(self, group_id, winner):
        game = SPY_ACTIVE_GAMES.get(group_id)
        if not game: return
        game["state"] = "finished"

        for k in ("turn_task", "vote_task", "registration_task", "countdown_task"):
            if game.get(k):
                try: game[k].cancel()
                except Exception: pass

        # AI narration
        narr = None
        try:
            narr = await self.ai_narrate(game["word"], game.get("category", ""),
                                          "spy_win" if winner == "spy" else "civ_win")
        except Exception: pass

        wm = await self._safe_send(group_id,
            f"{PE('brain','🧠')} <b>AI در حال تحلیل بازی...</b>\n"
            f"{PE('hourglass','⏳')} <i>چند لحظه صبر کنید...</i>",
            parse_mode="html")

        history = game["msg_history"] or []
        if not history:
            history = [{"uid": u, "name": game["players"][u]["name"], "msg": "(بی‌حرکت)"}
                       for u in game["players"]]
        # حذف تکراری — فقط آخرین پیام هر نفر، با حفظ ترتیب
        seen_ordered = OrderedDict()
        for m in history:
            seen_ordered[m["uid"]] = m
        unique = list(seen_ordered.values())

        # spy_idx توی لیست unique
        spy_uids = game.get("spy_uids") or [game["spy_uid"]]
        spy_idx = 0
        for i, m in enumerate(unique, 1):
            if m["uid"] in spy_uids:
                spy_idx = i
                break

        analysis = await self.ai_analyze_words(
            game["word"], game["spy_name"], spy_idx, unique)

        try: await wm.delete()
        except Exception: pass

        # آپدیت آمار
        try:
            await self._update_stats(game, winner, unique, analysis)
        except Exception as e:
            logger.warning(f"update_stats fail: {e}")

        # آمار قبلی برای نمایش XP جدید
        stats_after = {}
        try:
            c = self._c()
            for uid in game["players"]:
                c.execute("SELECT xp, achievements FROM spy_stats WHERE uid=%s", (uid,))
                row = c.fetchone()
                if row:
                    stats_after[uid] = {
                        "xp": row.get("xp", 0),
                        "achievements": row.get("achievements", "[]")
                    }
        except Exception: pass

        winner_txt = {
            "spy": f"{PE('detective','🕵️')} <b>جاسوس برد!</b>",
            "civilians": f"{PE('trophy','🏆')} <b>شهروندها بردن!</b>",
        }.get(winner, "🏁 پایان بازی")

        mode = SPY_MODES.get(game.get("mode", "classic"), SPY_MODES["classic"])
        narr_line = f"\n{PE('wave','🎬')} <i>{h(narr)}</i>\n" if narr else ""

        header = (
            f"{PE('flag','🏁')}  <b>بازی جاسوس تموم شد!</b>\n"
            f"{DIV}\n\n"
            f"{winner_txt}\n"
            f"{PE('brain','🧠')} حالت: <b>{mode['label']}</b>\n"
            f"{PE('diamond','💎')} کلمه‌ی مخفی: <b>{h(game['word'])}</b>\n"
            f"{PE('detective','🕵️')} جاسوس: <b>{h(game['spy_name'])}</b>\n"
            f"{PE('chart','📊')} راندها: <code>{game['round']}</code>\n"
            f"{narr_line}"
            f"{DIV2}\n"
            f"{PE('brain','🧠')} <b>تحلیل AI:</b>"
        )
        await self._safe_send(group_id, header, parse_mode="html")

        # لیست تحلیل‌ها
        analyses_map = {a.get("idx"): a for a in analysis.get("analyses", [])}
        lines = []
        new_ach_notifs = []
        for i, m in enumerate(unique, 1):
            a = analyses_map.get(i, {})
            score = int(a.get("score", 0))
            reason = a.get("reason", "—")
            if score >= 8: badge = "🌟"
            elif score >= 6: badge = "⭐"
            elif score >= 4: badge = "✨"
            else: badge = "💫"
            is_spy = (m["uid"] in spy_uids)
            role = f" {PE('detective','🕵️')}" if is_spy else ""
            xp_info = ""
            if m["uid"] in stats_after:
                xp_info = f"  ·  {PE('xp','⚡')} <code>{stats_after[m['uid']]['xp']}</code>"
            lines.append(
                f"{badge} <b>{h(m['name'])}</b>{role}  —  <code>{score}/10</code>{xp_info}\n"
                f"     <i>{h(reason)}</i>"
            )
        lines.append("")
        lines.append(f"{DIV2}")
        lines.append(f"{PE('crown','👑')} <i>{h(analysis.get('summary','بازی خوبی بود!'))}</i>")

        full = "\n".join(lines)
        if len(full) > 4000:
            chunks = [full[i:i+3500] for i in range(0, len(full), 3500)]
            for c in chunks:
                await self._safe_send(group_id, c, parse_mode="html")
                await asyncio.sleep(0.5)
        else:
            await self._safe_send(group_id, full, parse_mode="html")

        # ذخیره در دیتابیس
        try:
            c = self._c()
            c.execute("""INSERT INTO spy_games
                (group_id, admin_id, word, spy_uid, winner, players_json,
                 created_at, finished_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (group_id, game["admin_id"], game["word"], game["spy_uid"],
                 winner, json.dumps({str(k): v["name"] for k, v in game["players"].items()}),
                 now_ts(), now_ts()))
        except Exception as e:
            logger.warning(f"save spy game: {e}")

        # دکمه‌های rematch + lobby
        btns = [
            [Button.inline("🔄 دوباره با همینا",
                            data=f"spy:rematch:{group_id}".encode())],
            [Button.inline("🎩 منوی جدید",
                            data=f"spy:newgame:{group_id}".encode())],
        ]
        try:
            await self._safe_send(group_id,
                f"{PE('party','🎉')} <b>دوباره بازی کنیم؟</b>",
                buttons=btns, parse_mode="html")
        except Exception: pass

        SPY_ACTIVE_GAMES.pop(group_id, None)

    # ═══════════════ CALLBACKS ═══════════════
    async def on_callback(self, event):
        try:
            data = event.data.decode("utf-8", "ignore")
            if not data.startswith("spy:"): return
            parts = data.split(":")
            action = parts[1]
            uid = event.sender_id

            # ═══ شرکت ═══
            if action == "join":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                game = SPY_ACTIVE_GAMES.get(group_id)
                if not game or game["state"] != "waiting":
                    await self._safe_answer(event, "بازی در جریان نیست", alert=True); return
                if uid in game["players"]:
                    await self._safe_answer(event, "قبلاً ثبت‌نام کردی!", alert=True); return
                if len(game["players"]) >= SPY_MAX_PLAYERS:
                    await self._safe_answer(event, "ظرفیت پر شد!", alert=True); return
                try:
                    s = await event.get_sender()
                    name = user_name(s)
                    uu = getattr(s, "username", None)
                except Exception:
                    name = str(uid); uu = None
                game["players"][uid] = {"name": name, "username": uu, "alive": True}
                await self._safe_answer(event, f"✅ {name} ثبت شد!")
                await self._refresh_join_msg(game)
                return

            # ═══ تغییر حالت (فقط ادمین) ═══
            if action == "mode":
                try:
                    group_id = int(parts[2])
                    mode_key = parts[3]
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                game = SPY_ACTIVE_GAMES.get(group_id)
                if not game or game["state"] != "waiting":
                    await self._safe_answer(event, "الان نمی‌شه", alert=True); return
                if uid != game["admin_id"] and uid not in self._get_admins():
                    await self._safe_answer(event, "⛔ فقط ادمین!", alert=True); return
                if mode_key not in SPY_MODES:
                    await self._safe_answer(event, "حالت نامعتبر", alert=True); return
                game["mode"] = mode_key
                await self._safe_answer(event,
                    f"✅ حالت: {SPY_MODES[mode_key]['label']}")
                await self._refresh_join_msg(game)
                return

            # ═══ شروع بازی (ادمین) ═══
            if action == "start":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                game = SPY_ACTIVE_GAMES.get(group_id)
                if not game or game["state"] != "waiting":
                    await self._safe_answer(event, "بازی آماده نیست", alert=True); return
                if uid != game["admin_id"] and uid not in self._get_admins():
                    await self._safe_answer(event, "⛔ فقط ادمین!", alert=True); return
                min_req = SPY_MODES.get(game.get("mode","classic"), {}).get("min", SPY_MIN_PLAYERS)
                if len(game["players"]) < min_req:
                    await self._safe_answer(event,
                        f"حداقل {min_req} نفر لازمه!", alert=True); return
                await self._safe_answer(event, "🚀 شروع!")
                await self._begin_game(group_id)
                return

            # ═══ لغو ═══
            if action == "cancel":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                game = SPY_ACTIVE_GAMES.get(group_id)
                if not game: return
                if uid != game["admin_id"] and uid not in self._get_admins():
                    await self._safe_answer(event, "⛔ فقط ادمین!", alert=True); return
                for k in ("registration_task", "turn_task", "vote_task", "countdown_task"):
                    if game.get(k):
                        try: game[k].cancel()
                        except Exception: pass
                SPY_ACTIVE_GAMES.pop(group_id, None)
                await self._safe_answer(event, "لغو شد")
                try:
                    await event.edit(f"{PE('cross','❌')} <b>بازی جاسوس لغو شد</b>",
                                      parse_mode="html", buttons=None)
                except Exception: pass
                return

            # ═══ شروع رای‌گیری ═══
            if action == "vote_start":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                game = SPY_ACTIVE_GAMES.get(group_id)
                if not game or game["state"] != "round_end":
                    await self._safe_answer(event, "الان نمی‌شه", alert=True); return
                await self._safe_answer(event, "🗳")
                try:
                    await event.edit(f"{PE('vote','🗳')} <b>رای‌گیری شروع شد...</b>",
                                      parse_mode="html", buttons=None)
                except Exception: pass
                await self._start_voting(group_id)
                return

            # ═══ ادامه بازی ═══
            if action == "next_round":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                game = SPY_ACTIVE_GAMES.get(group_id)
                if not game or game["state"] != "round_end":
                    await self._safe_answer(event, "الان نمی‌شه", alert=True); return
                await self._safe_answer(event, "🚀")
                try:
                    await event.edit(f"{PE('rocket','🚀')} <b>راند بعدی!</b>",
                                      parse_mode="html", buttons=None)
                except Exception: pass
                game["state"] = "playing"
                game["current_index"] = 0
                game["round"] += 1
                game["round_spoken"] = set()
                await asyncio.sleep(1.5)
                await self._next_turn(group_id)
                return

            # ═══ رای ═══
            if action == "vote":
                try:
                    group_id = int(parts[2])
                    target_uid = int(parts[3])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                await self._handle_vote(event, group_id, target_uid)
                return

            # ═══ Rematch ═══
            if action == "rematch":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                # فقط بازیکن قبلی یا ادمین
                if uid not in self._get_admins():
                    await self._safe_answer(event, "⛔ فقط ادمین!", alert=True); return
                # بازی جدید با همون بازیکنای قبلی
                if group_id in SPY_ACTIVE_GAMES:
                    await self._safe_answer(event, "بازی در جریانه", alert=True); return
                await self._safe_answer(event, "🔄 بازی جدید ساخته شد!")
                # پیام قبلی رو غیرفعال کن
                try:
                    await event.edit(
                        f"{PE('rocket','🚀')} <b>بازی جدید در راهه...</b>",
                        parse_mode="html", buttons=None)
                except Exception: pass
                # شروع رجیستر جدید — بازیکنای قبلی رو نمی‌تونیم بیاریم چون
                # توی game قبلی بودن و پاک شدن. فقط یه لابی جدید باز می‌کنیم.
                await self._start_registration(group_id, uid)
                return

            # ═══ منوی جدید ═══
            if action == "newgame":
                try: group_id = int(parts[2])
                except Exception:
                    await self._safe_answer(event, "خطا", alert=True); return
                if uid not in self._get_admins():
                    await self._safe_answer(event, "⛔ فقط ادمین!", alert=True); return
                if group_id in SPY_ACTIVE_GAMES:
                    await self._safe_answer(event, "بازی در جریانه", alert=True); return
                await self._safe_answer(event, "🎩 لابی جدید!")
                try:
                    await event.edit(
                        f"{PE('sparkle','✨')} <b>لابی جدید ساخته شد</b>",
                        parse_mode="html", buttons=None)
                except Exception: pass
                await self._start_registration(group_id, uid)
                return

        except Exception as e:
            logger.exception(f"spy cb: {e}")
            await self._safe_answer(event, "خطا!", alert=True)


# ═══════════════════════════════════════════════════════════
# helper برای undercover (به خاطر اینکه داخل متد صدا زده می‌شه)
async def ai_pick_undercover_pair_safe(game_self):
    return await game_self.ai_pick_undercover_pair()


# ═══════════════════════════════════════════════════════════
_game = None


def init_spy(client, db, groq_key, ai_models):
    """بعد از client.start() صدا بزن"""
    global _game
    _game = SpyGame(client, db, groq_key, ai_models)
    _game.setup()
    _game.register_handlers()
    logger.info("🕵️ Spy module v2.0 initialized!")
    return _game