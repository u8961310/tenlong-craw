# 天瓏書店新書爬蟲

自動抓取[天瓏書店](https://www.tenlong.com.tw/)中文最近新書，透過 GitHub Actions 每周排程執行，並以 GitHub Pages 展示書單、Email 通知。

## 功能

- 爬取天瓏書店中文新書（含書名、封面、價格、折扣、連結）
- 自動分頁抓取所有新書
- **歷史記錄比對**：與上次爬取結果比對，標記新上架書籍（NEW badge）
- **書籍詳情抓取**：自動抓取作者、出版社、出版日、簡介、分類（含快取機制）
- **7 日內新書過濾**：僅顯示出版日期在 7 天內的書籍
- **排序功能**：依價格、折扣、出版日排序
- 產生響應式靜態網頁，透過 GitHub Pages 展示
- 每周自動寄送新書通知 Email（含 NEW 標記）

## 專案結構

```
├── scraper.py              # 爬蟲主程式（含歷史比對 + 詳情抓取）
├── generate_page.py        # 產生 GitHub Pages HTML（含排序 + 7 日過濾）
├── send_email.py           # 寄信程式（含 NEW 標記）
├── books.json              # 爬蟲結果 (自動產生)
├── books_previous.json     # 上次爬蟲結果備份 (自動產生, gitignored)
├── docs/
│   └── index.html          # GitHub Pages 頁面 (自動產生)
├── .github/
│   └── workflows/
│       └── weekly.yml      # GitHub Actions 每周排程
├── pyproject.toml          # uv 專案設定
└── .python-version         # Python 版本
```

## 本地執行

需先安裝 [uv](https://docs.astral.sh/uv/)：

```bash
# 安裝依賴
uv sync

# 執行爬蟲（完整，含詳情抓取）
uv run scraper.py

# 執行爬蟲（快速，跳過詳情抓取）
uv run scraper.py --skip-details

# 產生靜態頁面
uv run generate_page.py
```

執行後開啟 `docs/index.html` 即可預覽書單頁面。

## 部署至 GitHub

### 1. 建立 Repository 並推送

```bash
git remote add origin https://github.com/<你的帳號>/tenlong-craw.git
git push -u origin master
```

### 2. 設定 GitHub Pages

1. 進入 repo **Settings** > **Pages**
2. Source 選擇 **Deploy from a branch**
3. Branch 選擇 `master`，資料夾選擇 `/docs`
4. 儲存後即可透過 `https://<你的帳號>.github.io/tenlong-craw/` 瀏覽

### 3. 設定 Email 通知（選用）

到 repo **Settings** > **Secrets and variables** > **Actions** 新增以下 Secrets：

| Secret 名稱 | 說明 |
|---|---|
| `EMAIL_FROM` | 寄件人 Gmail 地址 |
| `EMAIL_PASSWORD` | Gmail [應用程式密碼](https://myaccount.google.com/apppasswords) |
| `EMAIL_TO` | 收件人地址（多人用逗號分隔） |

> Gmail 需開啟兩步驟驗證並產生應用程式密碼，不可使用帳號密碼。

未設定 Secrets 時，寄信步驟會自動跳過，不影響其他功能。

### 4. GitHub Actions 排程

Workflow 預設每周一台灣時間 09:00 自動執行，也可在 **Actions** 頁面手動觸發（Run workflow）。

執行流程：爬取新書 → 產生頁面 → 寄送通知 → 自動 commit 更新的 `books.json` 和 `docs/index.html`。
