# LINE 台股新聞利多利空 Bot

這是一個中文 LINE Bot MVP。使用者可以加入股票追蹤清單，Bot 會抓取財經 RSS 新聞，分析每則新聞偏利多、利空、中性或不確定，並每天早上推播摘要。

> 注意：這不是投資建議，只是新聞摘要與事件分類工具。

## 功能

- LINE 指令互動，全中文回覆
- 新增 / 刪除 / 查看追蹤股票
- 即時產生今日新聞分析
- 每天早上自動推播
- SQLite 儲存使用者與追蹤清單
- 支援 Gemini API 分析
- 也保留 OpenAI API 分析
- 沒有 API key 或 API 失敗時，自動改用關鍵字規則分析

## AI 模式說明

`.env` 裡的 `AI_PROVIDER` 可以選：

```env
AI_PROVIDER=gemini
```

可用值：

```text
auto    = 有 Gemini key 先用 Gemini，沒有 Gemini 才試 OpenAI，最後用規則
gemini  = 只用 Gemini，失敗就用規則
openai  = 只用 OpenAI，失敗就用規則
rule    = 完全不用 AI，只用關鍵字規則
```

建議你現在先用：

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=你的_Gemini_API_Key
GEMINI_MODEL=gemini-2.5-flash
```

如果你想完全免費、不呼叫任何 AI API：

```env
AI_PROVIDER=rule
GEMINI_API_KEY=
OPENAI_API_KEY=
```

## 安裝

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows PowerShell
# 或 source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env   # Windows
# 或 cp .env.example .env
```

打開 `.env`，至少填入：

```env
LINE_CHANNEL_ACCESS_TOKEN=你的 Channel access token
LINE_CHANNEL_SECRET=你的 Channel secret
AI_PROVIDER=gemini
GEMINI_API_KEY=你的 Gemini API key
GEMINI_MODEL=gemini-2.5-flash
```

## 啟動

```bash
python app.py
```

本機測試 LINE webhook 可使用 ngrok：

```bash
ngrok http 5000
```

然後把 LINE Developers Console 的 Webhook URL 設成：

```text
https://你的-ngrok-url/callback
```

## LINE 指令

```text
說明
新增 2330 台積電
新增 2454 聯發科
刪除 2330
清單
今日
```

也支援簡單英文：

```text
add 2330 TSMC
remove 2330
list
today
help
```

## 專案結構

```text
line_stock_news_bot/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── line_bot/
│   ├── webhook.py
│   ├── message_handler.py
│   └── push_message.py
├── news/
│   ├── rss_fetcher.py
│   └── news_cleaner.py
├── analysis/
│   ├── sentiment_classifier.py
│   ├── summarizer.py
│   ├── stock_mapper.py
│   └── scoring.py
├── database/
│   └── db.py
├── services/
│   └── report_service.py
├── scheduler/
│   └── daily_job.py
├── utils/
│   └── logger.py
└── tests/
    └── test_rule_classifier.py
```

## Gemini 測試方式

你可以先不接 LINE，只測 AI 分析：

```bash
python -c "from analysis.sentiment_classifier import analyze_news; print(analyze_news('台積電營收創高，AI需求強勁','公司表示先進製程需求增加，產能滿載。','2330','台積電'))"
```

如果 Gemini key 沒填、額度不夠、或 API 呼叫失敗，程式會印出錯誤，然後自動改用規則判斷，所以 bot 不會直接壞掉。

## 部署提醒

如果部署到 Render / Railway / VPS，可以直接跑 Flask app。免費雲端可能會睡眠，排程不一定準；正式使用建議用 VPS、Cloud Run + Cloud Scheduler，或另外用 GitHub Actions 每天呼叫 `/run-daily-report`。

## 後續建議

現在 MVP 主要用 RSS。下一步建議加入：

```text
公開資訊觀測站 MOPS
TWSE / TPEx 官方資料
公司重大訊息
每月營收
財報 EPS / 毛利率
外資買賣超
融資融券變化
```

這樣利多 / 利空判斷會比只看新聞標題更穩。
