import re
from html import unescape


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def short_text(text: str, limit: int = 120) -> str:
    text = clean_html(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."
