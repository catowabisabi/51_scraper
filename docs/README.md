# 51.ca 爬蟲系統

> 一個整合的網頁爬蟲系統，用於爬取 51.ca 網站的各類資料

## 📁 專案結構

```
51_scraper/
├── run.py                  # 統一入口點 (CLI)
├── scrapers/
│   ├── __init__.py
│   ├── base.py             # 基礎爬蟲類
│   ├── models.py           # 資料庫模型
│   ├── news_scraper.py     # 新聞爬蟲
│   ├── house_scraper.py    # 房屋爬蟲
│   ├── market_scraper.py   # 集市爬蟲
│   ├── auto_scraper.py     # 汽車爬蟲
│   ├── event_scraper.py    # 活動爬蟲
│   └── data/
│       └── 51ca.db         # SQLite 資料庫
├── docs/
│   ├── README.md           # 本文件
│   └── SCRAPING_GUIDE.md   # CSS 選擇器指南
└── data_structures_人類defined/
    ├── auto.json           # 汽車 schema
    ├── 二手物件買賣.json    # 集市 schema
    └── 活動頁面*.txt       # 活動 CSS 選擇器
```

---

## 🚀 快速開始

### 安裝依賴

```bash
pip install requests beautifulsoup4 lxml opencc-python-reimplemented
```

### 運行爬蟲

```bash
# 運行所有爬蟲
python run.py --all --max 20

# 只運行特定爬蟲
python run.py --news --max 10
python run.py --house --max 15
python run.py --market --max 20
python run.py --auto --max 30

# 查看統計
python run.py --stats

# 初始化資料庫（不運行爬蟲）
python run.py --init
```

---

## 📊 資料庫統計

| 表名 | 說明 | 唯一鍵 |
|------|------|--------|
| `news_articles` | 新聞文章 | `article_id` |
| `house_listings` | 房屋列表 | `listing_id` |
| `market_posts` | 集市商品 | `post_id` |
| `auto_listings` | 汽車列表 | `listing_id` |
| `events` | 社區活動 | `event_id` |
| `url_queue` | URL 隊列 | `url` |

---

## ❓ 重複資料處理

### Q: 如果有相同的資料會怎樣？

**A: 會自動更新，不會產生重複記錄。**

#### 原理：

1. **唯一約束 (UNIQUE)**
   - 每個表都有唯一鍵（如 `article_id`、`listing_id`、`post_id`）
   - SQLite 會根據這個鍵判斷是否為重複資料

2. **INSERT OR REPLACE 策略**
   ```sql
   INSERT OR REPLACE INTO news_articles (article_id, title, ...) VALUES (?, ?, ...)
   ```
   - 如果 `article_id` 已存在 → **更新**該記錄
   - 如果 `article_id` 不存在 → **插入**新記錄

#### 實際效果：

```
第一次爬取:
  - 文章 A (id=123) → 插入
  - 文章 B (id=456) → 插入

第二次爬取:
  - 文章 A (id=123) → 更新（內容可能有變動）
  - 文章 B (id=456) → 更新
  - 文章 C (id=789) → 插入（新資料）

資料庫始終只有 3 條記錄，不會有重複
```

#### 更新時間戳：

每個表都有 `updated_at` 欄位，會自動記錄最後更新時間：
```sql
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## 🔤 繁體中文轉換

所有爬取的資料會自動從**簡體中文轉換為繁體中文**：

- 使用 `OpenCC` 庫
- 配置：`s2twp`（簡體 → 台灣繁體 + 詞彙轉換）

### 範例：

| 原始（簡體） | 轉換後（繁體） |
|-------------|---------------|
| 加拿大央行裁员 | 加拿大央行裁員 |
| 动真格 | 動真格 |
| 信息 | 資訊 |
| 软件 | 軟體 |

---

## 🗃️ 資料庫表結構

### news_articles（新聞）

| 欄位 | 類型 | 說明 |
|------|------|------|
| article_id | TEXT | 文章 ID（唯一） |
| url | TEXT | 文章 URL |
| title | TEXT | 標題 |
| summary | TEXT | 摘要 |
| content | TEXT | 正文 |
| category | TEXT | 分類 |
| author | TEXT | 作者 |
| source | TEXT | 來源 |
| image_url | TEXT | 封面圖 |
| published_at | TIMESTAMP | 發布時間 |

### house_listings（房屋）

| 欄位 | 類型 | 說明 |
|------|------|------|
| listing_id | TEXT | 房源 ID（唯一） |
| listing_type | TEXT | 類型（出售/出租） |
| property_type | TEXT | 房屋類型 |
| address | TEXT | 地址 |
| city | TEXT | 城市 |
| price | REAL | 價格 |
| bedrooms | INTEGER | 臥室數 |
| bathrooms | INTEGER | 浴室數 |
| sqft | INTEGER | 面積 |
| agent_name | TEXT | 經紀人 |

### market_posts（集市）

| 欄位 | 類型 | 說明 |
|------|------|------|
| post_id | TEXT | 商品 ID（唯一） |
| title | TEXT | 標題 |
| description | TEXT | 描述 |
| price | REAL | 價格 |
| format_price | TEXT | 格式化價格 |
| category_name | TEXT | 分類名稱 |
| location_zh | TEXT | 地點（中文） |
| photos | TEXT | 圖片 JSON |
| user_name | TEXT | 賣家名稱 |
| contact_phone | TEXT | 聯絡電話 |

### auto_listings（汽車）

| 欄位 | 類型 | 說明 |
|------|------|------|
| listing_id | TEXT | 車輛 ID（唯一） |
| listing_type | TEXT | 類型（二手/新車/轉lease） |
| make | TEXT | 品牌 |
| model | TEXT | 型號 |
| year | INTEGER | 年份 |
| price | REAL | 價格 |
| kilometers | INTEGER | 公里數 |
| transmission | TEXT | 變速箱 |
| fuel_type | TEXT | 燃料類型 |
| dealer_name | TEXT | 車行名稱 |
| promo_* | INTEGER | 優惠標籤（5種） |

### events（活動）

| 欄位 | 類型 | 說明 |
|------|------|------|
| event_id | TEXT | 活動 ID（唯一） |
| title | TEXT | 標題 |
| event_type | TEXT | 類型（活動/優惠） |
| start_time | TIMESTAMP | 開始時間 |
| end_time | TIMESTAMP | 結束時間 |
| location | TEXT | 地點 |
| address | TEXT | 地址 |
| contact_person | TEXT | 聯絡人 |
| content | TEXT | 內容 |

---

## 🔗 爬取 URL

| 爬蟲 | 起始 URL |
|------|----------|
| 新聞 | `https://info.51.ca/` |
| 房屋 | `https://house.51.ca/mls`, `/rental` |
| 集市 | `https://www.51.ca/market/` |
| 汽車 | `https://www.51.ca/autos/` |
| 活動 | `https://www.51.ca/events` ⚠️ 目前404 |

---

## ⚠️ 已知問題

1. **活動頁面 404** - `/events` 和 `/promotions` 返回 404，可能需要更新 URL
2. **MLS 頁面** - `/mls` 某些頁面返回 0 結果，租房 `/rental` 正常

---

## 📝 開發指南

### 添加新爬蟲

1. 繼承 `BaseScraper`
2. 實現以下方法：
   - `get_start_urls()` - 起始 URL
   - `is_list_page()` - 判斷列表/詳情頁
   - `parse_list_page()` - 解析列表頁
   - `parse_detail_page()` - 解析詳情頁
   - `save_item()` - 保存資料

3. 在 `run.py` 中註冊

### 繁體轉換

在 `save_item()` 中使用：
```python
title = self.to_traditional(data['title'])
```

---

## 📄 License

MIT License
