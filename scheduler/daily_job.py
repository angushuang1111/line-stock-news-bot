from apscheduler.schedulers.background import BackgroundScheduler

from config import DAILY_REPORT_HOUR, DAILY_REPORT_MINUTE, TIMEZONE
from database.db import get_all_users
from line_bot.push_message import push_text_chunks
from services.report_service import generate_user_report, split_line_message

_scheduler = None


def run_daily_report() -> None:
    users = get_all_users()
    print(f"[每日推播] 準備推播給 {len(users)} 位使用者")

    for user_id in users:
        try:
            report = generate_user_report(user_id)
            chunks = split_line_message(report)
            push_text_chunks(user_id, chunks)
            print(f"[每日推播成功] {user_id}")
        except Exception as exc:
            print(f"[每日推播失敗] {user_id}: {exc}")


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone=TIMEZONE)
    _scheduler.add_job(
        run_daily_report,
        trigger="cron",
        hour=DAILY_REPORT_HOUR,
        minute=DAILY_REPORT_MINUTE,
        id="daily_stock_news_report",
        replace_existing=True,
    )
    _scheduler.start()
    print(f"[排程啟動] 每天 {DAILY_REPORT_HOUR:02d}:{DAILY_REPORT_MINUTE:02d} ({TIMEZONE}) 推播")


if __name__ == "__main__":
    # 可以手動執行：python -m scheduler.daily_job
    run_daily_report()
