import re

from analysis.stock_mapper import get_stock_name, normalize_stock_code
from database.db import add_user, add_watch_stock, get_watchlist, remove_watch_stock
from line_bot.push_message import reply_text
from services.report_service import generate_user_report, split_line_message

HELP_TEXT = """您好，我是台股新聞利多利空 Bot 📈

我可以幫你追蹤股票新聞，並用中文整理成：
利多 / 利空 / 中性 / 不確定。

可用指令：
新增 2330 台積電
新增 2454 聯發科
刪除 2330
清單
今日
說明

提醒：這不是投資建議，只是新聞摘要與事件分類。"""


def _parse_add_command(text: str):
    # 支援：新增 2330 台積電 / add 2330 TSMC
    m = re.match(r"^(新增|加入|追蹤|add)\s+([0-9]{4,6})(?:\s+(.+))?$", text, re.IGNORECASE)
    if not m:
        return None
    code = normalize_stock_code(m.group(2))
    name = (m.group(3) or "").strip()
    return code, name


def _parse_remove_command(text: str):
    # 支援：刪除 2330 / remove 2330
    m = re.match(r"^(刪除|移除|取消|remove|delete)\s+([0-9]{4,6})$", text, re.IGNORECASE)
    if not m:
        return None
    return normalize_stock_code(m.group(2))


def _format_watchlist(user_id: str) -> str:
    rows = get_watchlist(user_id)
    if not rows:
        return "你目前沒有追蹤任何股票。\n可以輸入：新增 2330 台積電"

    lines = ["📌 你的追蹤清單："]
    for row in rows:
        code = row["stock_code"]
        name = get_stock_name(code, row.get("stock_name") or "")
        lines.append(f"- {code} {name}".rstrip())
    return "\n".join(lines)


def handle_follow(event) -> None:
    user_id = event.source.user_id
    add_user(user_id)
    reply_text(event.reply_token, HELP_TEXT)


def handle_text_message(event) -> None:
    user_id = event.source.user_id
    add_user(user_id)

    text = event.message.text.strip()
    lower = text.lower()

    if text in ["說明", "幫助", "help", "Help", "HELP", "指令"]:
        reply_text(event.reply_token, HELP_TEXT)
        return

    add_result = _parse_add_command(text)
    if add_result:
        code, name = add_result
        final_name = get_stock_name(code, name)
        add_watch_stock(user_id, code, final_name)
        display = f"{code} {final_name}".strip()
        reply_text(event.reply_token, f"已加入追蹤清單：{display}\n\n輸入「今日」可以立刻產生新聞分析。")
        return

    remove_code = _parse_remove_command(text)
    if remove_code:
        count = remove_watch_stock(user_id, remove_code)
        if count:
            reply_text(event.reply_token, f"已刪除追蹤股票：{remove_code}")
        else:
            reply_text(event.reply_token, f"你的清單裡沒有 {remove_code}。")
        return

    if text in ["清單", "列表", "list", "watchlist"]:
        reply_text(event.reply_token, _format_watchlist(user_id))
        return

    if text in ["今日", "今天", "報告", "新聞", "today", "report"]:
        report = generate_user_report(user_id)
        chunks = split_line_message(report)
        # reply_message 只能用一次，先回第一段，其餘用 push 會比較複雜；MVP 先回第一段
        reply_text(event.reply_token, chunks[0])
        return

    reply_text(
        event.reply_token,
        "我看不懂這個指令。\n\n請輸入「說明」查看用法，例如：\n新增 2330 台積電\n清單\n今日",
    )
