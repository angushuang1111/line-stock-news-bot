from typing import Dict

from analysis.scoring import score_to_label
from analysis.summarizer import analyze_with_selected_ai
from news.news_cleaner import clean_html, short_text

POSITIVE_KEYWORDS = {
    "創高": 2,
    "新高": 2,
    "成長": 1,
    "增加": 1,
    "上修": 2,
    "優於預期": 2,
    "超預期": 2,
    "接單": 2,
    "大單": 2,
    "訂單": 1,
    "擴產": 1,
    "需求強勁": 2,
    "產能滿載": 2,
    "漲價": 2,
    "毛利率提升": 2,
    "獲利成長": 2,
    "營收成長": 2,
    "法說會看好": 2,
    "股利": 1,
    "回購": 1,
    "買超": 1,
    "目標價上調": 2,
}

NEGATIVE_KEYWORDS = {
    "衰退": -2,
    "下滑": -1,
    "減少": -1,
    "低於預期": -2,
    "不如預期": -2,
    "虧損": -2,
    "賠錢": -2,
    "下修": -2,
    "砍單": -3,
    "庫存過高": -2,
    "庫存調整": -1,
    "降價": -2,
    "毛利率下降": -2,
    "營收衰退": -2,
    "訴訟": -2,
    "罰款": -2,
    "裁員": -2,
    "停工": -2,
    "處置": -1,
    "注意股": -1,
    "賣超": -1,
    "目標價下調": -2,
    "現增": -1,
}

UNCERTAIN_KEYWORDS = ["傳出", "市場傳聞", "可能", "據悉", "尚未證實", "外傳"]


def rule_based_analyze(title: str, content: str, stock_code: str, stock_name: str) -> Dict:
    text = clean_html(f"{title} {content}")
    score = 0
    hit_words = []

    for word, weight in POSITIVE_KEYWORDS.items():
        if word in text:
            score += weight
            hit_words.append(word)

    for word, weight in NEGATIVE_KEYWORDS.items():
        if word in text:
            score += weight
            hit_words.append(word)

    label, confidence = score_to_label(score)

    if any(word in text for word in UNCERTAIN_KEYWORDS):
        confidence = max(45, confidence - 15)
        if label == "利多":
            label = "中性偏利多"
        elif label == "利空":
            label = "中性偏利空"

    if hit_words:
        reason = f"偵測到關鍵詞：{'、'.join(hit_words[:5])}，因此初步判斷為「{label}」。"
    else:
        reason = "沒有明確財務、訂單、毛利率或營運展望關鍵詞，因此先歸類為中性或不確定。"

    return {
        "label": label,
        "confidence": confidence,
        "summary": short_text(content or title, 60),
        "reason": reason,
        "risk_note": "此為規則判斷，建議再搭配公司公告、財報與法人說法確認。",
        "method": "rule",
    }


def analyze_news(title: str, content: str, stock_code: str, stock_name: str) -> Dict:
    ai_result = analyze_with_selected_ai(title, content, stock_code, stock_name)
    if ai_result:
        return ai_result
    return rule_based_analyze(title, content, stock_code, stock_name)
