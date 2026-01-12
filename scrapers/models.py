"""
51.ca 爬蟲 - 資料庫模型 (整合版)
定義所有資料表結構
"""

import sqlite3
import json
from datetime import datetime
import os

# 資料庫路徑
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "51ca.db")


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
            article_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            content TEXT,
            category TEXT,
            author TEXT,
            source TEXT,
            publish_date TIMESTAMP,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            image_urls TEXT,
            tags TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 房屋列表表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS house_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            listing_type TEXT,
            property_type TEXT,
            price REAL,
            price_unit TEXT,
            address TEXT,
            city TEXT,
            province TEXT,
            community TEXT,
            bedrooms TEXT,
            bathrooms TEXT,
            parking TEXT,
            sqft TEXT,
            description TEXT,
            features TEXT,
            agent_name TEXT,
            agent_phone TEXT,
            agent_company TEXT,
            image_urls TEXT,
            amenities TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 工作職位表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            company_name TEXT,
            company_url TEXT,
            salary TEXT,
            salary_unit TEXT,
            location TEXT,
            job_type TEXT,
            work_period TEXT,
            shift TEXT,
            category TEXT,
            description TEXT,
            requirements TEXT,
            benefits TEXT,
            contact_info TEXT,
            post_date TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            merchant_id TEXT
        )
    """)
    
    # ============== 商家表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT UNIQUE,
            url TEXT NOT NULL,
            name TEXT,
            english_name TEXT,
            category TEXT,
            subcategory TEXT,
            description TEXT,
            services TEXT,
            address TEXT,
            phone TEXT,
            website TEXT,
            business_hours TEXT,
            logo_url TEXT,
            image_urls TEXT,
            rating REAL,
            review_count INTEGER,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 服務帖子表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,
            url TEXT NOT NULL,
            merchant_id TEXT,
            title TEXT,
            category TEXT,
            subcategory TEXT,
            content TEXT,
            contact_phone TEXT,
            price TEXT,
            location TEXT,
            image_urls TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 二手市場表 (基於schema) ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            description TEXT,
            format_price TEXT,
            price REAL,
            original_price REAL,
            negotiable INTEGER DEFAULT 0,
            condition INTEGER,
            category_id INTEGER,
            category_name TEXT,
            category_slug TEXT,
            location_id INTEGER,
            location_zh TEXT,
            location_en TEXT,
            pickup_methods TEXT,
            contact_phone TEXT,
            email TEXT,
            wechat_no TEXT,
            wechat_qrcode TEXT,
            photos TEXT,
            user_uid INTEGER,
            user_name TEXT,
            user_avatar TEXT,
            favorite_count INTEGER DEFAULT 0,
            published_at TIMESTAMP,
            source TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 汽車列表表 (基於schema) ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            listing_type TEXT,
            make TEXT,
            model TEXT,
            year INTEGER,
            trim TEXT,
            body_type TEXT,
            color TEXT,
            transmission TEXT,
            drivetrain TEXT,
            fuel_type TEXT,
            kilometers INTEGER,
            price REAL,
            currency TEXT DEFAULT 'CAD',
            city TEXT,
            province TEXT,
            dealer_name TEXT,
            dealer_address TEXT,
            dealer_phone TEXT,
            vin TEXT,
            carfax_available INTEGER DEFAULT 0,
            features TEXT,
            description TEXT,
            images TEXT,
            promo_same_day_approval INTEGER DEFAULT 0,
            promo_no_credit_ok INTEGER DEFAULT 0,
            promo_no_job_ok INTEGER DEFAULT 0,
            promo_delivery_available INTEGER DEFAULT 0,
            promo_warranty_available INTEGER DEFAULT 0,
            post_date TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== 活動表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            event_type TEXT,
            image_url TEXT,
            time_text TEXT,
            location TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            region TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            address TEXT,
            content TEXT,
            content_images TEXT,
            published_at TIMESTAMP,
            source TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============== URL隊列表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            url_type TEXT,
            source_url TEXT,
            priority INTEGER DEFAULT 0,
            visited INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visited_at TIMESTAMP
        )
    """)
    
    # ============== 爬蟲日誌表 ==============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_name TEXT,
            url TEXT,
            status TEXT,
            items_count INTEGER DEFAULT 0,
            error_message TEXT,
            duration_seconds REAL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("資料庫初始化完成")


def add_url_to_queue(url: str, url_type: str, source_url: str = None, priority: int = 0):
    """添加URL到爬蟲隊列"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO url_queue (url, url_type, source_url, priority)
            VALUES (?, ?, ?, ?)
        """, (url, url_type, source_url, priority))
        conn.commit()
    finally:
        conn.close()


def mark_url_visited(url: str, error: str = None):
    """標記URL為已訪問"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if error:
            cursor.execute("""
                UPDATE url_queue 
                SET visited = 1, visited_at = ?, last_error = ?, retry_count = retry_count + 1
                WHERE url = ?
            """, (datetime.now(), error, url))
        else:
            cursor.execute("""
                UPDATE url_queue 
                SET visited = 1, visited_at = ?
                WHERE url = ?
            """, (datetime.now(), url))
        conn.commit()
    finally:
        conn.close()


def get_unvisited_urls(url_type: str, limit: int = 10):
    """獲取未訪問的URL"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT url FROM url_queue 
            WHERE url_type = ? AND visited = 0 AND retry_count < 3
            ORDER BY priority DESC, added_at ASC
            LIMIT ?
        """, (url_type, limit))
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def log_scrape(scraper_name: str, url: str, status: str, items_count: int = 0, 
               error_message: str = None, duration_seconds: float = 0):
    """記錄爬蟲日誌"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO scrape_logs (scraper_name, url, status, items_count, error_message, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scraper_name, url, status, items_count, error_message, duration_seconds))
        conn.commit()
    finally:
        conn.close()


def to_json(data):
    """將數據轉換為JSON字符串"""
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def from_json(json_str):
    """從JSON字符串解析數據"""
    if json_str is None:
        return None
    try:
        return json.loads(json_str)
    except:
        return None


# 初始化資料庫
if __name__ == "__main__":
    init_database()