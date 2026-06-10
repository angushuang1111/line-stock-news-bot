from typing import Tuple


def score_to_label(score: int) -> Tuple[str, int]:
    """把正負分轉成中文標籤與信心分數。"""
    abs_score = abs(score)
    confidence = min(95, 50 + abs_score * 10)

    if score >= 2:
        return "利多", confidence
    if score <= -2:
        return "利空", confidence
    if score == 1:
        return "中性偏利多", 60
    if score == -1:
        return "中性偏利空", 60
    return "中性 / 不確定", 50
