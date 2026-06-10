# Render 部署版說明

這個版本支援 Render Web Service + Render PostgreSQL + Render Cron Job。

## 1. Render 服務架構

```text
LINE 使用者
  ↓
LINE Webhook URL: https://你的服務.onrender.com/callback
  ↓
Render Web Service: Flask + gunicorn
  ↓
Render PostgreSQL: users / watchlist / report_logs
  ↓
Gemini API + RSS 新聞
  ↓
LINE reply / push message
```

每日早報建議不要靠 Flask 內建 scheduler，而是用 Render Cron Job：

```text
Render Cron Job
  schedule: 30 23 * * *  # UTC 23:30 = Taiwan 07:30
  command: python -m scheduler.daily_job
```

## 2. 本機測試

```bash
cd line_stock_news_bot
copy .env.example .env
notepad .env
pip install -r requirements.txt
python app.py
```

開瀏覽器測試：

```text
http://127.0.0.1:5000/health
```

## 3. Render Web Service 設定

把整個 `line_stock_news_bot` 資料夾上傳到 GitHub repo，然後 Render：

```text
New > Web Service
Connect GitHub repo
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Health Check Path: /health
```

Render Flask 官方 quickstart 也使用 `pip install -r requirements.txt` 和 `gunicorn app:app` 這種部署方式。

## 4. Render PostgreSQL 設定

Render：

```text
New > Postgres
Name: stock-bot-db
```

建立後，到資料庫的 Connect / Info 頁面複製 **Internal Database URL**，放到 Web Service 和 Cron Job 的環境變數：

```env
DATABASE_URL=postgresql://...
```

若沒有 `DATABASE_URL`，程式會退回 SQLite `stock_bot.db`。本機測試可以用 SQLite，但 Render 正式版建議用 PostgreSQL。

## 5. Render Environment Variables

Web Service 需要：

```env
LINE_CHANNEL_ACCESS_TOKEN=你的 LINE Channel access token
LINE_CHANNEL_SECRET=你的 LINE Channel secret
AI_PROVIDER=gemini
GEMINI_API_KEY=你的 Gemini key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=你的 Render Postgres Internal Database URL
ENABLE_SCHEDULER=false
TIMEZONE=Asia/Taipei
```

Cron Job 也要設定同樣的 LINE / Gemini / DATABASE_URL 環境變數。

## 6. LINE Webhook URL

Render 部署完成後，拿到網址，例如：

```text
https://line-stock-news-bot.onrender.com
```

LINE Developers Console 設定：

```text
Webhook URL = https://line-stock-news-bot.onrender.com/callback
Use webhook = Enabled
```

然後按 Verify。

## 7. Render Cron Job 設定

Render：

```text
New > Cron Job
Runtime: Python 3
Build Command: pip install -r requirements.txt
Command: python -m scheduler.daily_job
Schedule: 30 23 * * *
```

Render Cron 的時間使用 UTC，所以台灣早上 07:30 = UTC 前一天 23:30。

## 8. 看使用者資料

本機 SQLite：

```bash
python scripts/show_users.py
```

Render PostgreSQL：

可以在 Render 的 Shell / Job 裡執行同一個指令，或用 PostgreSQL client 連 Render 的 External Database URL。

目前 users table 主要存 LINE user_id、display_name（如果之後有抓 profile）、created_at、last_seen_at。LINE user_id 不是使用者真名。

## 9. 安全提醒

不要把 `.env` 上傳 GitHub。

如果你曾經截圖或公開 Gemini key、LINE secret、LINE token，請重新產生新的 key/token/secret。
