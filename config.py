import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

# AI 分析設定
# AI_PROVIDER 可用：auto / gemini / openai / rule
# auto：有 Gemini key 就先用 Gemini；沒有 Gemini 才試 OpenAI；都沒有就用規則判斷。
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5-mini")

# Database
# 本機測試：使用 SQLite DATABASE_PATH
# Render 正式部署：建議設定 DATABASE_URL 使用 PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "stock_bot.db")

# Scheduler
# 本機/Render Web Service 建議 false，避免多 worker 重複跑。
# Render 每日推播建議使用 Cron Job：python -m scheduler.daily_job
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "7"))
DAILY_REPORT_MINUTE = int(os.getenv("DAILY_REPORT_MINUTE", "30"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

# Optional: protect /run-daily-report endpoint when you trigger it from an external cron service.
CRON_SECRET = os.getenv("CRON_SECRET", "").strip()

DEFAULT_RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=news",
    "https://tw.stock.yahoo.com/rss?category=tw-market",
    "https://tw.stock.yahoo.com/rss?category=research",
]

RSS_URLS = [
    u.strip() for u in os.getenv("RSS_URLS", ",".join(DEFAULT_RSS_URLS)).split(",") if u.strip()
]

MAX_NEWS_PER_STOCK = int(os.getenv("MAX_NEWS_PER_STOCK", "5"))
MAX_RSS_ITEMS_PER_SOURCE = int(os.getenv("MAX_RSS_ITEMS_PER_SOURCE", "30"))
