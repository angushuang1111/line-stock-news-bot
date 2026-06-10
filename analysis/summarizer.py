import json
import re
from typing import Dict, Optional

from config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)


def _strip_json_codeblock(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _safe_int(value, default: int = 50) -> int:
    try:
        n = int(value)
    except Exception:
        return default
    return max(0, min(100, n))


def _normalize_ai_result(data: Dict, method: str) -> Dict:
    return {
        "label": str(data.get("label", "中性 / 不確定")),
        "confidence": _safe_int(data.get("confidence", 50)),
        "summary": str(data.get("summary", "")),
        "reason": str(data.get("reason", "")),
        "risk_note": str(data.get("risk_note") or data.get("risk") or "資訊可能不完整，建議再查公司公告與財報。"),
        "method": method,
    }


def _build_prompt(title: str, content: str, stock_code: str, stock_name: str) -> Dict:
    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "news_title": title,
        "news_content": content,
        "task": "判斷這則新聞對該股票是利多、利空、中性偏利多、中性偏利空、或中性/不確定。請輸出 JSON。",
        "rules": [
            "不要給買賣建議，只做新聞事件分類。",
            "資訊不足時要標示不確定，不要硬判斷。",
            "一律使用繁體中文。",
            "只輸出 JSON，不要加 markdown。",
        ],
        "json_schema": {
            "label": "利多 / 利空 / 中性偏利多 / 中性偏利空 / 中性 / 不確定",
            "confidence": "0-100 整數",
            "summary": "30-60 字中文摘要",
            "reason": "用 1-2 句中文說明原因",
            "risk_note": "如果資訊不足，說明要再查什麼",
        },
    }


def analyze_with_gemini(title: str, content: str, stock_code: str, stock_name: str) -> Optional[Dict]:
    """如果有 GEMINI_API_KEY，就用 Gemini 做中文分析；失敗時回傳 None。"""
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai

        prompt = _build_prompt(title, content, stock_code, stock_name)
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=json.dumps(prompt, ensure_ascii=False),
        )

        text = _strip_json_codeblock(getattr(response, "text", "") or "")
        data = json.loads(text)
        return _normalize_ai_result(data, "gemini")
    except Exception as exc:
        print(f"[Gemini 分析失敗，改用下一個方法] {exc}")
        return None


def analyze_with_openai(title: str, content: str, stock_code: str, stock_name: str) -> Optional[Dict]:
    """如果有 OPENAI_API_KEY，就用 OpenAI 做中文分析；失敗時回傳 None。"""
    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = _build_prompt(title, content, stock_code, stock_name)

        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=(
                "你是謹慎的台股新聞分析助理。"
                "不要給買賣建議，只做新聞事件分類。"
                "不要誇大，資訊不足時要標示不確定。"
                "一律使用繁體中文，且只輸出 JSON，不要加 markdown。"
            ),
            input=json.dumps(prompt, ensure_ascii=False),
        )
        text = _strip_json_codeblock(response.output_text)
        data = json.loads(text)
        return _normalize_ai_result(data, "openai")
    except Exception as exc:
        print(f"[OpenAI 分析失敗，改用下一個方法] {exc}")
        return None


def analyze_with_selected_ai(title: str, content: str, stock_code: str, stock_name: str) -> Optional[Dict]:
    """依 AI_PROVIDER 選擇 Gemini / OpenAI / 規則備援。"""
    provider = AI_PROVIDER or "auto"

    if provider == "rule":
        return None

    if provider == "gemini":
        return analyze_with_gemini(title, content, stock_code, stock_name)

    if provider == "openai":
        return analyze_with_openai(title, content, stock_code, stock_name)

    # auto 模式：Gemini 優先，OpenAI 備援，最後才交給 rule-based。
    gemini_result = analyze_with_gemini(title, content, stock_code, stock_name)
    if gemini_result:
        return gemini_result

    openai_result = analyze_with_openai(title, content, stock_code, stock_name)
    if openai_result:
        return openai_result

    return None
