from analysis.sentiment_classifier import rule_based_analyze


def test_positive_news():
    result = rule_based_analyze(
        "台積電營收創高，AI 需求強勁",
        "公司表示先進製程需求強勁，產能滿載。",
        "2330",
        "台積電",
    )
    assert "利多" in result["label"]


def test_negative_news():
    result = rule_based_analyze(
        "公司營收低於預期，庫存過高",
        "法人下修目標價。",
        "0000",
        "測試公司",
    )
    assert "利空" in result["label"]
