from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

from analysis.sentiment_classifier import analyze_news
from analysis.stock_mapper import get_stock_name
from config import MAX_NEWS_PER_STOCK, TIMEZONE
from database.db import get_watchlist, save_report_log
from news.rss_fetcher import fetch_stock_news, NewsItem


def _emoji(label: str) -> str:
    if "利多" in label and "偏利空" not in label:
        return "🟢"
    if "利空" in label:
        return "🔴"
    if "偏" in label:
        return "🟡"
    return "⚪"


def _format_news(stock_code: str, stock_name: str, item: NewsItem, index: int) -> str:
    result = analyze_news(item.title, item.summary, stock_code, stock_name)
    label = result["label"]
    confidence = result["confidence"]
    summary = result["summary"]
    reason = result["reason"]
    risk_note = result.get("risk_note", "")
    method_map = {"gemini": "Gemini", "openai": "OpenAI", "rule": "規則"}
    method = method_map.get(result.get("method"), "規則")

    return (
        f"{index}. {item.title}\n"
        f"判斷：{_emoji(label)} {label}\n"
        f"信心：{confidence}%（{method}）\n"
        f"摘要：{summary}\n"
        f"原因：{reason}\n"
        f"提醒：{risk_note}\n"
        f"來源：{item.source}\n"
        f"連結：{item.link}"
    )


def generate_user_report(user_id: str) -> str:
    watchlist = get_watchlist(user_id)
    today = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y/%m/%d")

    if not watchlist:
        return (
            "你目前還沒有追蹤任何股票。\n\n"
            "可以輸入：\n"
            "新增 2330 台積電\n"
            "新增 2454 聯發科\n\n"
            "之後輸入「今日」就可以看新聞利多利空分析。"
        )

    sections: List[str] = [
        f"📈 今日台股新聞利多利空摘要 {today}",
        "⚠️ 這不是投資建議，只是新聞摘要與事件分類。",
    ]

    for stock in watchlist:
        stock_code = stock["stock_code"]
        stock_name = get_stock_name(stock_code, stock.get("stock_name") or "")
        display_name = f"{stock_code} {stock_name}".strip()
        sections.append(f"\n==========\n📌 {display_name}")

        items = fetch_stock_news(stock_code, stock_name, max_items=MAX_NEWS_PER_STOCK)
        if not items:
            sections.append(
                "目前 RSS 裡沒有找到明確相關新聞。\n"
                "建議後續加入公開資訊觀測站 MOPS、公司公告或券商資料來源，提高命中率。"
            )
            continue

        for i, item in enumerate(items, start=1):
            sections.append(_format_news(stock_code, stock_name, item, i))

    report = "\n\n".join(sections)
    save_report_log(user_id, report)
    return report


def split_line_message(text: str, max_len: int = 4500) -> List[str]:
    """LINE 文字訊息上限約 5000 字，保守切成 4500。"""
    chunks = []
    while len(text) > max_len:
        cut = text.rfind("\n\n", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut])
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks
