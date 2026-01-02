"""
51.ca 資料庫模型
定義所有資料表結構
"""

import sqlite3
from datetime import datetime
import os

# 資料庫路徑
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "51ca.db")


def get_connection():
    """獲取資料庫連接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """初始化資料庫，創建所有資料表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # ============== 新聞文章表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT UNIQUE,           -- 文章唯一ID (從URL提取)
            url TEXT NOT NULL,                -- 文章URL
            title TEXT,                       -- 標題
            summary TEXT,                     -- 摘要
            content TEXT,                     -- 正文內容
            category TEXT,                    -- 分類 (加國/國際/中國/綜合等)
            author TEXT,                      -- 作者
            source TEXT,                      -- 來源
            publish_date TIMESTAMP,           -- 發布時間
            comment_count INTEGER DEFAULT 0,  -- 評論數
            view_count INTEGER DEFAULT 0,     -- 閱讀數
            image_urls TEXT,                  -- 圖片URLs (JSON格式)
            tags TEXT,                        -- 標籤 (JSON格式)
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 房屋列表表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS house_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE,           -- 房源ID (MLS號碼)
            url TEXT NOT NULL,                -- 房源URL
            title TEXT,                       -- 標題
            listing_type TEXT,                -- 類型 (出售/出租)
            property_type TEXT,               -- 房屋類型 (獨立屋/公寓/鎮屋等)
            price REAL,                       -- 價格
            price_unit TEXT,                  -- 價格單位 (CAD/月等)
            address TEXT,                     -- 地址
            city TEXT,                        -- 城市
            community TEXT,                   -- 社區
            bedrooms TEXT,                    -- 臥室數
            bathrooms TEXT,                   -- 浴室數
            parking TEXT,                     -- 車位數
            sqft TEXT,                        -- 面積
            description TEXT,                 -- 描述
            features TEXT,                    -- 特點 (JSON格式)
            agent_name TEXT,                  -- 經紀人姓名
            agent_phone TEXT,                 -- 經紀人電話
            agent_company TEXT,               -- 經紀公司
            image_urls TEXT,                  -- 圖片URLs (JSON格式)
            amenities TEXT,                   -- 設施 (JSON格式: 華人超市/Costco/地鐵等)
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 工作職位表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE,               -- 職位ID
            url TEXT NOT NULL,                -- 職位URL
            title TEXT,                       -- 職位標題
            company_name TEXT,                -- 公司名稱
            company_url TEXT,                 -- 公司URL
            salary TEXT,                      -- 薪資
            salary_unit TEXT,                 -- 薪資單位 (時薪/年薪)
            location TEXT,                    -- 工作地點
            job_type TEXT,                    -- 工作類型 (全職/兼職)
            work_period TEXT,                 -- 工作時長 (長期工/短期工)
            shift TEXT,                       -- 班次 (白班/中班/夜班)
            category TEXT,                    -- 職位類別
            description TEXT,                 -- 職位描述
            requirements TEXT,                -- 要求 (JSON格式)
            benefits TEXT,                    -- 福利 (JSON格式)
            contact_info TEXT,                -- 聯繫方式
            post_date TIMESTAMP,              -- 發布日期
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 黃頁商家表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT UNIQUE,          -- 商家ID
            url TEXT NOT NULL,                -- 商家URL
            name TEXT,                        -- 商家名稱
            english_name TEXT,                -- 英文名稱
            category TEXT,                    -- 主分類
            subcategory TEXT,                 -- 子分類
            description TEXT,                 -- 描述
            services TEXT,                    -- 提供的服務 (JSON格式)
            address TEXT,                     -- 地址
            phone TEXT,                       -- 電話
            website TEXT,                     -- 網站
            business_hours TEXT,              -- 營業時間
            logo_url TEXT,                    -- Logo圖片
            image_urls TEXT,                  -- 圖片URLs (JSON格式)
            rating REAL,                      -- 評分
            review_count INTEGER DEFAULT 0,   -- 評論數
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 黃頁服務帖子表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,              -- 帖子ID
            url TEXT NOT NULL,                -- 帖子URL
            merchant_id TEXT,                 -- 關聯商家ID
            title TEXT,                       -- 標題
            category TEXT,                    -- 分類
            subcategory TEXT,                 -- 子分類
            content TEXT,                     -- 內容
            contact_phone TEXT,               -- 聯繫電話
            price TEXT,                       -- 價格
            location TEXT,                    -- 位置
            image_urls TEXT,                  -- 圖片URLs (JSON格式)
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (merchant_id) REFERENCES service_merchants(merchant_id)
        )
    """)
    
    # ============== 集市帖子表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,              -- 帖子ID
            url TEXT NOT NULL,                -- 帖子URL
            title TEXT,                       -- 標題
            category TEXT,                    -- 分類
            price REAL,                       -- 價格
            original_price REAL,              -- 原價
            price_unit TEXT,                  -- 價格單位
            description TEXT,                 -- 描述
            condition TEXT,                   -- 物品狀態 (全新/二手等)
            location TEXT,                    -- 位置
            contact_info TEXT,                -- 聯繫方式
            image_urls TEXT,                  -- 圖片URLs (JSON格式)
            post_date TIMESTAMP,              -- 發布日期
            view_count INTEGER DEFAULT 0,     -- 瀏覽次數
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 汽車帖子表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE,           -- 帖子ID
            url TEXT NOT NULL,                -- 帖子URL
            title TEXT,                       -- 標題
            listing_type TEXT,                -- 類型 (出售/求購)
            make TEXT,                        -- 品牌
            model TEXT,                       -- 型號
            year INTEGER,                     -- 年份
            mileage INTEGER,                  -- 里程 (公里)
            body_type TEXT,                   -- 車身類型 (SUV/轎車等)
            price REAL,                       -- 價格
            transmission TEXT,                -- 變速箱 (自動/手動)
            fuel_type TEXT,                   -- 燃料類型
            color TEXT,                       -- 顏色
            vin TEXT,                         -- VIN碼
            description TEXT,                 -- 描述
            features TEXT,                    -- 特點 (JSON格式)
            seller_type TEXT,                 -- 賣家類型 (車行/私人)
            seller_name TEXT,                 -- 賣家名稱
            contact_phone TEXT,               -- 聯繫電話
            location TEXT,                    -- 位置
            image_urls TEXT,                  -- 圖片URLs (JSON格式)
            post_date TIMESTAMP,              -- 發布日期
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 爬取日誌表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_name TEXT,                -- 爬蟲名稱
            url TEXT,                         -- 爬取的URL
            status TEXT,                      -- 狀態 (success/failed)
            items_count INTEGER DEFAULT 0,    -- 爬取項目數
            error_message TEXT,               -- 錯誤信息
            duration_seconds REAL,            -- 耗時(秒)
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== URL隊列表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,         -- URL
            url_type TEXT,                    -- URL類型 (news/house/job/service等)
            source_url TEXT,                  -- 來源URL
            priority INTEGER DEFAULT 0,       -- 優先級
            visited INTEGER DEFAULT 0,        -- 是否已訪問
            retry_count INTEGER DEFAULT 0,    -- 重試次數
            last_error TEXT,                  -- 最後錯誤
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visited_at TIMESTAMP
        )
    """)
    
    # 創建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_publish_date ON news_articles(publish_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_house_city ON house_listings(city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_house_type ON house_listings(listing_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_location ON job_listings(location)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_category ON job_listings(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_category ON service_merchants(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_queue_visited ON url_queue(visited)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_queue_type ON url_queue(url_type)")
    
    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成")


# ============== 資料操作函數 ==============

def save_news_article(data: dict) -> bool:
    """保存新聞文章"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO news_articles 
            (article_id, url, title, summary, content, category, author, source, 
             publish_date, comment_count, view_count, image_urls, tags, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('article_id'),
            data.get('url'),
            data.get('title'),
            data.get('summary'),
            data.get('content'),
            data.get('category'),
            data.get('author'),
            data.get('source'),
            data.get('publish_date'),
            data.get('comment_count', 0),
            data.get('view_count', 0),
            data.get('image_urls'),
            data.get('tags'),
            datetime.now()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"保存新聞失敗: {e}")
        return False
    finally:
        conn.close()


def save_house_listing(data: dict) -> bool:
    """保存房屋列表"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO house_listings 
            (listing_id, url, title, listing_type, property_type, price, price_unit,
             address, city, community, bedrooms, bathrooms, parking, sqft, description,
             features, agent_name, agent_phone, agent_company, image_urls, amenities, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('listing_id'),
            data.get('url'),
            data.get('title'),
            data.get('listing_type'),
            data.get('property_type'),
            data.get('price'),
            data.get('price_unit'),
            data.get('address'),
            data.get('city'),
            data.get('community'),
            data.get('bedrooms'),
            data.get('bathrooms'),
            data.get('parking'),
            data.get('sqft'),
            data.get('description'),
            data.get('features'),
            data.get('agent_name'),
            data.get('agent_phone'),
            data.get('agent_company'),
            data.get('image_urls'),
            data.get('amenities'),
            datetime.now()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"保存房屋失敗: {e}")
        return False
    finally:
        conn.close()


def save_job_listing(data: dict) -> bool:
    """保存工作職位"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO job_listings 
            (job_id, url, title, company_name, company_url, salary, salary_unit,
             location, job_type, work_period, shift, category, description,
             requirements, benefits, contact_info, post_date, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('job_id'),
            data.get('url'),
            data.get('title'),
            data.get('company_name'),
            data.get('company_url'),
            data.get('salary'),
            data.get('salary_unit'),
            data.get('location'),
            data.get('job_type'),
            data.get('work_period'),
            data.get('shift'),
            data.get('category'),
            data.get('description'),
            data.get('requirements'),
            data.get('benefits'),
            data.get('contact_info'),
            data.get('post_date'),
            datetime.now()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"保存工作失敗: {e}")
        return False
    finally:
        conn.close()


def add_url_to_queue(url: str, url_type: str, source_url: str = None, priority: int = 0) -> bool:
    """添加URL到隊列"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO url_queue (url, url_type, source_url, priority)
            VALUES (?, ?, ?, ?)
        """, (url, url_type, source_url, priority))
        conn.commit()
        return True
    except Exception as e:
        print(f"添加URL失敗: {e}")
        return False
    finally:
        conn.close()


def get_unvisited_urls(url_type: str = None, limit: int = 10) -> list:
    """獲取未訪問的URL"""
    conn = get_connection()
    cursor = conn.cursor()
    if url_type:
        cursor.execute("""
            SELECT url FROM url_queue 
            WHERE visited = 0 AND url_type = ? AND retry_count < 3
            ORDER BY priority DESC, added_at ASC
            LIMIT ?
        """, (url_type, limit))
    else:
        cursor.execute("""
            SELECT url FROM url_queue 
            WHERE visited = 0 AND retry_count < 3
            ORDER BY priority DESC, added_at ASC
            LIMIT ?
        """, (limit,))
    urls = [row[0] for row in cursor.fetchall()]
    conn.close()
    return urls


def mark_url_visited(url: str, success: bool = True, error: str = None):
    """標記URL為已訪問"""
    conn = get_connection()
    cursor = conn.cursor()
    if success:
        cursor.execute("""
            UPDATE url_queue SET visited = 1, visited_at = ? WHERE url = ?
        """, (datetime.now(), url))
    else:
        cursor.execute("""
            UPDATE url_queue SET retry_count = retry_count + 1, last_error = ? WHERE url = ?
        """, (error, url))
    conn.commit()
    conn.close()


def log_scrape(scraper_name: str, url: str, status: str, items_count: int = 0, 
               error_message: str = None, duration: float = 0):
    """記錄爬取日誌"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scrape_logs (scraper_name, url, status, items_count, error_message, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (scraper_name, url, status, items_count, error_message, duration))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """獲取資料庫統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    tables = ['news_articles', 'house_listings', 'job_listings', 
              'service_merchants', 'service_posts', 'market_posts', 'auto_listings']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM url_queue WHERE visited = 0")
    stats['pending_urls'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM url_queue WHERE visited = 1")
    stats['visited_urls'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


if __name__ == "__main__":
    init_database()
    print("資料庫模型初始化完成！")
