import hmac
import os

from flask import Flask, request

from config import CRON_SECRET, ENABLE_SCHEDULER, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from database.db import init_db, using_postgres
from line_bot.webhook import register_line_webhook
from scheduler.daily_job import run_daily_report, start_scheduler
from utils.logger import setup_logger


def _is_authorized_cron_request() -> bool:
    """Protect /run-daily-report if you use an external cron service."""
    if not CRON_SECRET:
        return False
    supplied = request.headers.get("X-Cron-Secret") or request.args.get("token") or ""
    return hmac.compare_digest(supplied, CRON_SECRET)


def create_app() -> Flask:
    setup_logger()
    init_db()

    app = Flask(__name__)
    register_line_webhook(app)

    @app.route("/", methods=["GET"])
    def index():
        return {
            "status": "ok",
            "message": "LINE 台股新聞 Bot 正常運作中",
            "routes": ["/health", "/callback", "/run-daily-report"],
        }

    @app.route("/health", methods=["GET"])
    def health():
        return {
            "status": "ok",
            "message": "LINE 台股新聞 Bot 正常運作中",
            "database": "postgres" if using_postgres() else "sqlite",
        }

    @app.route("/run-daily-report", methods=["POST", "GET"])
    def manual_run_daily_report():
        # Prefer Render Cron Job command: python -m scheduler.daily_job
        # If you use this HTTP endpoint from cron-job.org/GitHub Actions, set CRON_SECRET.
        if not _is_authorized_cron_request():
            return {"status": "error", "message": "未授權，請設定 CRON_SECRET 並附上 token。"}, 403
        run_daily_report()
        return {"status": "ok", "message": "已執行每日報告"}

    if ENABLE_SCHEDULER:
        start_scheduler()

    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
        print("[提醒] 尚未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET，Webhook 會無法正常運作。")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
