# 51.ca 爬蟲指南

本文檔整合了所有對 51.ca 網站爬蟲有用的資料，包括 CSS Selectors、JSON Schema、URL 模式等。

---

## 目錄

1. [項目結構](#項目結構)
2. [新聞爬蟲 (info.51.ca)](#新聞爬蟲)
3. [房屋爬蟲 (house.51.ca)](#房屋爬蟲)
4. [集市爬蟲 (market)](#集市爬蟲)
5. [汽車爬蟲 (auto)](#汽車爬蟲)
6. [活動爬蟲 (events)](#活動爬蟲)
7. [通用技術](#通用技術)

---

## 項目結構

```
51_scraper/
├── run.py                    # 統一運行入口
├── scrapers/
│   ├── __init__.py
│   ├── models.py             # 資料庫模型
│   ├── base.py               # 基礎爬蟲類
│   ├── news_scraper.py       # 新聞爬蟲
│   ├── house_scraper.py      # 房屋爬蟲
│   ├── market_scraper.py     # 集市爬蟲
│   ├── auto_scraper.py       # 汽車爬蟲
│   └── event_scraper.py      # 活動爬蟲
├── logs/                     # 日誌目錄
└── docs/
    └── SCRAPING_GUIDE.md     # 本文檔
```

### 使用方法

```bash
# 運行所有爬蟲
python run.py --all

# 運行特定爬蟲
python run.py --news
python run.py --house --auto

# 設置最大頁數
python run.py --market --max 100

# 查看資料庫統計
python run.py --stats

# 初始化資料庫
python run.py --init
```

---

## 新聞爬蟲

**網站**: `https://info.51.ca`

### URL 模式

| 類型 | URL 格式 |
|------|----------|
| 首頁 | `https://info.51.ca/` |
| 分類 | `https://info.51.ca/canada`, `/world`, `/china` |
| 文章 | `https://info.51.ca/articles/1500533` |

### 分類

| 路徑 | 中文名 |
|------|--------|
| `/canada` | 加國 |
| `/world` | 國際 |
| `/china` | 中國 |
| `/entertainment` | 體娛 |
| `/shopping` | 購物 |
| `/real-estate` | 房產 |
| `/money` | 理財 |
| `/deals` | 打折 |

### CSS Selectors

| 字段 | Selector |
|------|----------|
| 標題 | `h1` 或 `title` |
| 正文 | `.article-body`, `.content`, `#arcbody` |
| 圖片 | `.article-body img` |
| 來源 | `.source` |

---

## 房屋爬蟲

**網站**: `https://house.51.ca`

### URL 模式

| 類型 | URL 格式 |
|------|----------|
| MLS 列表 | `https://house.51.ca/mls` |
| 租房列表 | `https://house.51.ca/rental` |
| MLS 詳情 | `https://house.51.ca/property/C1234567` |
| 租房詳情 | `https://house.51.ca/rental/ontario/toronto/area/12345` |
| 城市過濾 | `https://house.51.ca/mls?city=toronto` |

### 發現連結的方法

來源: `data_structures_人類defined/HOUSING的主頁.txt`

```python
# 使用 class="feed-list" 找到連結
soup.find(class_='feed-list')
```

### 連結 Pattern

```python
# MLS 房源
'/property/[A-Z]\d+'          # e.g. /property/C1234567

# Redirect 格式
'/redirect/property/[A-Z]\d+' # 需要提取 MLS ID

# 租房
'/rental/ontario/[^/]+/[^/]+/\d+'
```

### 房屋類型映射

| 英文 | 中文 |
|------|------|
| detached | 獨立屋 |
| semi-detached | 半獨立屋 |
| townhouse | 鎮屋 |
| condo, apartment | 公寓 |
| bungalow | 平房 |

---

## 集市爬蟲

**網站**: `https://www.51.ca/market`

### 關鍵技術: Next.js `__NEXT_DATA__`

集市使用 Next.js 框架，所有數據都在 `<script id="__NEXT_DATA__">` 中。

來源: `data_structures_人類defined/二手物件買賣.json`

### JSON Schema

```json
{
  "props": {
    "pageProps": {
      "data": {
        "id": 123456,
        "title": "商品標題",
        "description": "描述",
        "formatPrice": "100",
        "negotiable": true,
        "condition": 1,
        "locationInfo": {
          "id": 1,
          "titleZh": "多倫多",
          "titleEn": "Toronto"
        },
        "categoryInfo": {
          "id": 1,
          "titleCn": "家具",
          "slug": "furniture"
        },
        "photos": ["url1", "url2"],
        "publishedAt": "2024-01-01T00:00:00Z",
        "user": {
          "uid": 123,
          "name": "賣家名稱"
        },
        "favoriteCount": 10
      }
    }
  }
}
```

### 分類列表

| Slug | 類別 |
|------|------|
| `furniture` | 家具 |
| `home-appliance` | 家電 |
| `kitchen-supplies` | 廚具 |
| `electronics` | 電子產品 |
| `auto-parts` | 汽車配件 |
| `gardening` | 園藝 |
| `books` | 書籍 |
| `others` | 其他 |

### 狀態碼

| Code | 狀態 |
|------|------|
| 0 | 未指定 |
| 1 | 全新 |
| 2 | 九成新 |
| 3 | 八成新 |
| 4 | 二手 |
| 5 | 較舊 |

---

## 汽車爬蟲

**網站**: `https://www.51.ca/autos`

### URL 模式

| 類型 | URL 格式 |
|------|----------|
| 二手車列表 | `/autos/used-cars` |
| 新車列表 | `/autos/new-cars` |
| 轉 Lease | `/autos/lease-cars` |
| 詳情頁 | `/autos/used-cars/12345` |

### JSON Schema (promotions)

來源: `data_structures_人類defined/二手車項目頁頁schema.json`

```json
{
  "listing": {
    "id": "12345",
    "title": "2020 Toyota Camry",
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "price": 25000,
    "currency": "CAD",
    "kilometers": 50000,
    "location": {
      "city": "Toronto",
      "province": "ON"
    },
    "dealer": {
      "name": "ABC Motors",
      "phone": "416-123-4567"
    },
    "promotions": {
      "same_day_approval": true,
      "no_credit_ok": true,
      "no_job_ok": false,
      "delivery_available": true,
      "warranty_available": true
    }
  }
}
```

### Promotion 標籤識別

| 中文標籤 | JSON Key |
|----------|----------|
| 当日批核 / 当天批核 | `same_day_approval` |
| 零信用OK / 无信用OK | `no_credit_ok` |
| 无工作OK / 没工作OK | `no_job_ok` |
| 送车上门 | `delivery_available` |
| 原厂保修 / 保修 | `warranty_available` |

### 汽車品牌列表

```python
CAR_BRANDS = [
    'Toyota', 'Honda', 'Nissan', 'Mazda', 'BMW', 'Mercedes', 'Audi',
    'Lexus', 'Acura', 'Infiniti', 'Ford', 'Chevrolet', 'Hyundai',
    'Kia', 'Volkswagen', 'Subaru', 'Tesla', 'Porsche', 'Jeep',
    'GMC', 'Ram', 'Dodge', 'Chrysler', 'Buick', 'Cadillac',
]
```

---

## 活動爬蟲

**網站**: `https://www.51.ca/events`

### URL 模式

| 類型 | URL 格式 |
|------|----------|
| 活動列表 | `/events` |
| 優惠列表 | `/promotions` |
| 詳情頁 | `/events/12345` 或 `/event/12345` |

### CSS Selectors (列表頁)

來源: `data_structures_人類defined/活動頁面的活動的locat方法.txt`

```css
/* 活動項目 */
li.wg51__feeds-item.event

/* 推廣/廣告 */
li.wg51__feeds-item.stream-mixed-large

/* ID */
li.wg51__feeds-item.event a[data-id]

/* 標題 */
li.wg51__feeds-item.event h3 a

/* 封面圖 */
li.wg51__feeds-item.event img.cover-img

/* 時間 */
li.wg51__feeds-item.event span.time

/* 地點 */
li.wg51__feeds-item.event span.location
```

### CSS Selectors (詳情頁)

來源: `data_structures_人類defined/活動詳情頁面結構.txt`

| 字段 | CSS Selector |
|------|--------------|
| 標題 | `#article-main h1` |
| 發佈時間 | `#article-main .article-meta .source span:nth-of-type(1)` |
| 來源 | `#article-main .article-meta .source span:nth-of-type(2)` |
| 活動時間 | `.events-card dl:nth-of-type(1) dd` |
| 開始時間 | `.events-card dt:contains("开始时间") + dd` |
| 結束時間 | `.events-card dt:contains("结束时间") + dd` |
| 地區 | `.events-card dt:contains("所在地区") + dd` |
| 聯絡人 | `.events-card dt:contains("联系人") + dd` |
| 電話 | `.events-card a.phone` |
| 電郵 | `.events-card a.email span.__cf_email__` |
| 地址 | `.events-card dt:contains("相关地址") + dd` |
| 正文 | `#arcbody` |
| 圖片 | `#arcbody img.detail-lazy-image` (使用 `data-src`) |

### XPath 替代方案

```xpath
# 標題
//div[@id="article-main"]//h1/text()

# 發佈時間
//div[@class="article-meta"]//span[1]/text()

# 地址 (dt+dd pair)
//dt[contains(.,"相关地址")]/following-sibling::dd[1]/text()
```

### BeautifulSoup 示例

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
card = soup.select_one(".events-card")

data = {
    "title": soup.select_one("#article-main h1").get_text(strip=True),
    "published_at": soup.select_one(".article-meta .source span").get_text(strip=True),
    "region": card.select_one("dt:contains('所在地区') + dd").get_text(strip=True),
    "contact": card.select_one("dt:contains('联系人') + dd").get_text(strip=True),
    "phone": card.select_one("a.phone").get_text(strip=True),
    "email_cf": card.select_one("span.__cf_email__")["data-cfemail"],
    "address": card.select_one("dt:contains('相关地址') + dd").get_text(strip=True),
    "content_html": str(soup.select_one("#arcbody")),
    "images": [img["data-src"] for img in soup.select("#arcbody img.detail-lazy-image")]
}
```

---

## 通用技術

### Cloudflare 郵箱解碼

51.ca 使用 Cloudflare 保護郵箱地址。解碼方法：

```python
def decode_cloudflare_email(encoded: str) -> str:
    """解碼 Cloudflare 保護的郵箱"""
    try:
        r = int(encoded[:2], 16)
        email = ''.join([chr(int(encoded[i:i+2], 16) ^ r) 
                        for i in range(2, len(encoded), 2)])
        return email
    except:
        return ""

# 使用
email_elem = soup.select_one('span.__cf_email__')
encoded = email_elem.get('data-cfemail', '')
email = decode_cloudflare_email(encoded)
```

### 圖片懶加載

許多圖片使用懶加載，真正的 URL 在 `data-src` 或 `data-srcset`：

```python
for img in soup.select('img.detail-lazy-image'):
    src = img.get('data-src') or img.get('data-srcset') or img.get('src')
```

### 相對時間轉換

```python
from datetime import datetime, timedelta
import re

def parse_relative_time(text: str) -> str:
    """轉換相對時間為絕對時間"""
    match = re.search(r'(\d+)小時前', text)
    if match:
        hours = int(match.group(1))
        return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    match = re.search(r'(\d+)天前', text)
    if match:
        days = int(match.group(1))
        return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    return None
```

### 防止被封禁

1. **請求間隔**: 每次請求間隔 1-2 秒
2. **User-Agent**: 使用真實瀏覽器的 User-Agent
3. **Session**: 使用 requests.Session 保持連接
4. **錯誤處理**: 遇到 429/503 時暫停重試

```python
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
```

---

## 資料庫表結構

### news_articles
- `article_id` (PRIMARY KEY)
- `url`, `title`, `summary`, `content`
- `category`, `author`, `source`
- `publish_date`, `comment_count`, `view_count`
- `image_urls` (JSON), `tags`

### house_listings
- `listing_id` (PRIMARY KEY) - MLS號或租房ID
- `url`, `title`, `listing_type` (出售/出租)
- `property_type`, `address`, `city`, `community`
- `price`, `price_unit`, `bedrooms`, `bathrooms`, `parking`, `sqft`
- `description`, `features` (JSON)
- `agent_name`, `agent_phone`, `agent_company`
- `image_urls` (JSON)

### market_posts
- `post_id` (PRIMARY KEY)
- `url`, `title`, `category`, `category_name`
- `price`, `original_price`, `negotiable`, `condition`
- `description`, `location`
- `seller_name`, `seller_id`, `contact_info` (JSON)
- `image_urls` (JSON), `post_date`
- `view_count`, `favorite_count`

### auto_listings
- `listing_id` (PRIMARY KEY)
- `url`, `title`, `listing_type` (二手/新車/轉lease)
- `make`, `model`, `year`, `price`
- `mileage`, `body_type`, `transmission`, `fuel_type`, `drivetrain`
- `color`, `vin`
- `description`, `features` (JSON)
- `seller_type`, `seller_name`, `contact_phone`
- `location` (JSON), `promotions` (JSON)
- `image_urls` (JSON), `post_date`

### events
- `event_id` (PRIMARY KEY)
- `url`, `title`, `event_type` (活動/優惠)
- `start_time`, `end_time`, `location`, `address`
- `contact_person`, `contact_phone`, `contact_email`
- `description`, `source`, `published_at`
- `image_urls` (JSON)

---

## 更新日誌

- **2024-01**: 整合所有爬蟲，統一結構
- 添加 Promotions 支援 (汽車爬蟲)
- 添加 Next.js JSON 提取 (集市爬蟲)
- 整合 CSS Selectors 文檔 (活動爬蟲)
