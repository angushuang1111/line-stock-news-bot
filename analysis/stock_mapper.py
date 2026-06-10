from typing import Optional

# MVP 先放常見台股名稱。之後可以改成從 TWSE/TPEx Open Data 更新。
STOCK_NAME_MAP = {
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2303": "聯電",
    "2308": "台達電",
    "2382": "廣達",
    "3231": "緯創",
    "2357": "華碩",
    "2356": "英業達",
    "6669": "緯穎",
    "3661": "世芯-KY",
    "3443": "創意",
    "3034": "聯詠",
    "2379": "瑞昱",
    "2603": "長榮",
    "2609": "陽明",
    "2615": "萬海",
    "2881": "富邦金",
    "2882": "國泰金",
    "2891": "中信金",
    "2886": "兆豐金",
    "2002": "中鋼",
    "1301": "台塑",
    "1303": "南亞",
    "3711": "日月光投控",
    "2618": "長榮航",
    "6505": "台塑化",
    "1519": "華城",
    "1513": "中興電",
    "6139": "亞翔",
    "2344": "華邦電",
    "4919": "新唐",
    "6719": "力智",
    "6715": "嘉基",
}


def normalize_stock_code(text: str) -> str:
    return "".join(ch for ch in text.strip() if ch.isdigit())


def get_stock_name(stock_code: str, fallback: Optional[str] = None) -> str:
    if fallback:
        return fallback.strip()
    return STOCK_NAME_MAP.get(stock_code, "")
