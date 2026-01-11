"""
對比舊/新爬蟲的資料提取效果
找出哪些欄位是舊方法能提取但新方法提取不到的
"""

import sys
import os
import sqlite3
from datetime import datetime

from bs4 import BeautifulSoup
import requests


# ============== 資料庫路徑 ==============
OLD_DB_PATH = os.path.join(os.path.dirname(__file__), "51ca-old.db")
NEW_DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")


def init_old_db():
    """初始化舊資料庫"""
    conn = sqlite3.connect(OLD_DB_PATH)
    cursor = conn.cursor()
    
    # 新聞表
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
            image_urls TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 汽車表
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
            price REAL,
            mileage INTEGER,
            body_type TEXT,
            transmission TEXT,
            fuel_type TEXT,
            drivetrain TEXT,
            color TEXT,
            vin TEXT,
            description TEXT,
            features TEXT,
            seller_type TEXT,
            seller_name TEXT,
            contact_phone TEXT,
            location TEXT,
            post_date TEXT,
            image_urls TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 房屋表
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
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 集市表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,
            url TEXT NOT NULL,
            title TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            location TEXT,
            contact_phone TEXT,
            user_name TEXT,
            photos TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    return conn


class OldStyleScraper:
    """模擬舊爬蟲的提取邏輯"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch(self, url):
        """獲取頁面"""
        try:
            resp = self.session.get(url, timeout=30)
            resp.encoding = 'utf-8'
            return resp.text
        except Exception as e:
            print(f"獲取失敗: {url} - {e}")
            return None
    
    def clean_text(self, text):
        """清理文本"""
        if not text:
            return None
        import re
        text = re.sub(r'\s+', ' ', str(text)).strip()
        return text if text else None
    
    # ============== 新聞解析（舊方法）==============
    def parse_news_old(self, html, url):
        """舊方法解析新聞"""
        soup = BeautifulSoup(html, "lxml")
        
        import re
        match = re.search(r'/articles/(\d+)', url)
        article_id = match.group(1) if match else None
        
        # 標題 - 多種選擇器
        title = None
        for selector in ['h1.article-title', 'h1', '.article-header h1', '#article-main h1']:
            elem = soup.select_one(selector)
            if elem:
                title = self.clean_text(elem.get_text())
                if title:
                    break
        
        # 摘要
        summary = None
        summary_elem = soup.select_one('.article-summary, .summary, .lead, .article-intro')
        if summary_elem:
            summary = self.clean_text(summary_elem.get_text())
        
        # 正文
        content = None
        for selector in ['#arcbody', '.article-content', '.article-body', '#article-content']:
            elem = soup.select_one(selector)
            if elem:
                # 移除腳本和樣式
                for tag in elem.find_all(['script', 'style', 'iframe']):
                    tag.decompose()
                content = self.clean_text(elem.get_text())
                if content and len(content) > 50:
                    break
        
        # 分類
        category = None
        cat_elem = soup.select_one('.article-category, .category, .breadcrumb a:last-child')
        if cat_elem:
            category = self.clean_text(cat_elem.get_text())
        
        # 來源
        source = None
        source_elem = soup.select_one('.article-source, .source, .article-meta .source')
        if source_elem:
            source = self.clean_text(source_elem.get_text())
        
        # 作者
        author = None
        author_elem = soup.select_one('.article-author, .author, .byline')
        if author_elem:
            author = self.clean_text(author_elem.get_text())
        
        # 發布日期
        publish_date = None
        date_elem = soup.select_one('.article-date, .publish-time, .time, .article-meta time')
        if date_elem:
            publish_date = self.clean_text(date_elem.get_text())
        
        # 圖片
        import json
        images = []
        for img in soup.select('#arcbody img, .article-content img'):
            src = img.get('data-src') or img.get('src')
            if src and 'logo' not in src.lower():
                images.append(src)
        image_urls = json.dumps(images[:10]) if images else None
        
        return {
            'article_id': article_id,
            'url': url,
            'title': title,
            'summary': summary,
            'content': content,
            'category': category,
            'author': author,
            'source': source,
            'publish_date': publish_date,
            'image_urls': image_urls,
        }
    
    # ============== 汽車解析（舊方法）==============
    def parse_auto_old(self, html, url):
        """舊方法解析汽車"""
        soup = BeautifulSoup(html, "lxml")
        
        import re
        match = re.search(r'/(\d+)$', url)
        listing_id = match.group(1) if match else None
        
        # 標題
        title = None
        title_elem = soup.find('h1')
        if title_elem:
            title = self.clean_text(title_elem.get_text())
            # 清理標題後綴
            if title:
                title = re.sub(r'\s*[-|_].*51.*$', '', title)
        
        # 類型
        listing_type = '二手'
        if '/new-cars/' in url:
            listing_type = '新車'
        elif '/lease-cars/' in url:
            listing_type = '轉lease'
        
        # 價格 - 多種模式
        price = None
        price_patterns = [
            r'\$\s*([\d,]+)',
            r'([\d,]+)\s*\$',
            r'價格[：:]\s*\$?([\d,]+)',
        ]
        text = soup.get_text()
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if price > 100:  # 排除太小的數字
                        break
                except:
                    pass
        
        # 年份
        year = None
        if title:
            match = re.search(r'\b(19|20)\d{2}\b', title)
            if match:
                year = int(match.group(0))
        
        # 品牌和型號
        make = None
        model = None
        brands = ['Toyota', 'Honda', 'Nissan', 'BMW', 'Mercedes', 'Audi', 'Lexus', 
                  'Ford', 'Chevrolet', 'Hyundai', 'Kia', 'Volkswagen', 'Mazda',
                  'Subaru', 'Jeep', 'Chrysler', 'Dodge', 'Porsche', 'Infiniti', 'Acura']
        if title:
            for brand in brands:
                if brand.lower() in title.lower():
                    make = brand
                    # 嘗試提取型號
                    pattern = rf'{brand}\s+(\w+)'
                    m = re.search(pattern, title, re.IGNORECASE)
                    if m:
                        model = m.group(1)
                    break
        
        # 里程
        mileage = None
        mileage_patterns = [
            r'([\d,]+)\s*(?:km|公里|KM)',
            r'里程[：:]\s*([\d,]+)',
            r'Mileage[：:]\s*([\d,]+)',
        ]
        for pattern in mileage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    mileage = int(match.group(1).replace(',', ''))
                    break
                except:
                    pass
        
        # 變速箱
        transmission = None
        if 'automatic' in text.lower() or '自動' in text:
            transmission = '自動'
        elif 'manual' in text.lower() or '手動' in text:
            transmission = '手動'
        
        # VIN
        vin = None
        vin_match = re.search(r'VIN[：:\s]*([A-HJ-NPR-Z0-9]{17})', text, re.IGNORECASE)
        if vin_match:
            vin = vin_match.group(1)
        
        # 賣家信息
        seller_name = None
        seller_elem = soup.select_one('.dealer-name, .seller-name, .contact-name')
        if seller_elem:
            seller_name = self.clean_text(seller_elem.get_text())
        
        # 電話
        contact_phone = None
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            contact_phone = phone_match.group(1)
        
        # 位置
        location = None
        loc_elem = soup.select_one('.location, .address, .dealer-address')
        if loc_elem:
            location = self.clean_text(loc_elem.get_text())
        
        # 描述
        description = None
        desc_elem = soup.select_one('.description, .vehicle-description, .listing-description')
        if desc_elem:
            description = self.clean_text(desc_elem.get_text())
        
        # 圖片
        import json
        images = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src and ('51img' in src or 'storage' in src) and 'logo' not in src.lower():
                images.append(src)
        image_urls = json.dumps(list(set(images))[:10]) if images else None
        
        return {
            'listing_id': listing_id,
            'url': url,
            'title': title,
            'listing_type': listing_type,
            'make': make,
            'model': model,
            'year': year,
            'price': price,
            'mileage': mileage,
            'transmission': transmission,
            'vin': vin,
            'seller_name': seller_name,
            'contact_phone': contact_phone,
            'location': location,
            'description': description,
            'image_urls': image_urls,
        }
    
    # ============== 房屋解析（舊方法）==============
    def parse_house_old(self, html, url):
        """舊方法解析房屋"""
        soup = BeautifulSoup(html, "lxml")
        
        import re
        # 提取 ID
        listing_id = None
        match = re.search(r'/(\d+)$', url)
        if match:
            listing_id = match.group(1)
        else:
            match = re.search(r'/property/([A-Z]\d+)', url)
            if match:
                listing_id = match.group(1)
        
        # 標題
        title = None
        title_elem = soup.find('h1')
        if title_elem:
            title = self.clean_text(title_elem.get_text())
        
        # 類型
        listing_type = '出售'
        if '/rental/' in url:
            listing_type = '出租'
        
        # 價格
        price = None
        price_elem = soup.select_one('.price, .listing-price, .property-price')
        if price_elem:
            price_text = price_elem.get_text()
            match = re.search(r'\$?([\d,]+)', price_text)
            if match:
                try:
                    price = float(match.group(1).replace(',', ''))
                except:
                    pass
        
        # 地址
        address = None
        addr_elem = soup.select_one('.address, .property-address, .listing-address')
        if addr_elem:
            address = self.clean_text(addr_elem.get_text())
        
        # 城市
        city = None
        if '/toronto/' in url.lower():
            city = 'Toronto'
        elif '/markham/' in url.lower():
            city = 'Markham'
        elif '/vaughan/' in url.lower():
            city = 'Vaughan'
        elif '/richmond-hill/' in url.lower():
            city = 'Richmond Hill'
        elif '/mississauga/' in url.lower():
            city = 'Mississauga'
        
        # 臥室/浴室
        bedrooms = None
        bathrooms = None
        room_text = soup.get_text()
        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|臥室|房)', room_text, re.IGNORECASE)
        if bed_match:
            bedrooms = bed_match.group(1)
        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom|浴室|衛)', room_text, re.IGNORECASE)
        if bath_match:
            bathrooms = bath_match.group(1)
        
        # 描述
        description = None
        desc_elem = soup.select_one('.description, .property-description, .listing-description')
        if desc_elem:
            description = self.clean_text(desc_elem.get_text())
        
        # 圖片
        import json
        images = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src and ('51img' in src or 'storage' in src) and 'logo' not in src.lower():
                images.append(src)
        image_urls = json.dumps(list(set(images))[:10]) if images else None
        
        return {
            'listing_id': listing_id,
            'url': url,
            'title': title,
            'listing_type': listing_type,
            'price': price,
            'address': address,
            'city': city,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'description': description,
            'image_urls': image_urls,
        }


def run_old_scraper(max_items=10):
    """運行舊爬蟲提取資料"""
    print("=" * 60)
    print("使用舊方法爬取資料到 51ca-old.db")
    print("=" * 60)
    
    conn = init_old_db()
    cursor = conn.cursor()
    scraper = OldStyleScraper()
    
    # ============== 爬取新聞 ==============
    print("\n--- 爬取新聞 ---")
    news_list_url = "https://info.51.ca/"
    html = scraper.fetch(news_list_url)
    if html:
        soup = BeautifulSoup(html, "lxml")
        import re
        links = soup.find_all('a', href=re.compile(r'/articles/\d+'))
        urls = list(set([f"https://info.51.ca{a['href'].split('?')[0]}" 
                        for a in links if a.get('href', '').startswith('/')]))[:max_items]
        
        for url in urls:
            print(f"  爬取: {url}")
            html = scraper.fetch(url)
            if html:
                data = scraper.parse_news_old(html, url)
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO news_articles 
                        (article_id, url, title, summary, content, category, author, source, publish_date, image_urls)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['article_id'], data['url'], data['title'], data['summary'],
                        data['content'], data['category'], data['author'], data['source'],
                        data['publish_date'], data['image_urls']
                    ))
                    conn.commit()
                    print(f"    ✓ 保存: {data['title'][:30] if data['title'] else 'N/A'}...")
                except Exception as e:
                    print(f"    ✗ 錯誤: {e}")
    
    # ============== 爬取汽車 ==============
    print("\n--- 爬取汽車 ---")
    auto_list_url = "https://www.51.ca/autos/used-cars"
    html = scraper.fetch(auto_list_url)
    if html:
        soup = BeautifulSoup(html, "lxml")
        import re
        links = soup.find_all('a', href=re.compile(r'/autos/(used-cars|new-cars)/\d+'))
        urls = list(set([f"https://www.51.ca{a['href'].split('?')[0]}" 
                        for a in links if a.get('href', '').startswith('/')]))[:max_items]
        
        for url in urls:
            print(f"  爬取: {url}")
            html = scraper.fetch(url)
            if html:
                data = scraper.parse_auto_old(html, url)
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO auto_listings 
                        (listing_id, url, title, listing_type, make, model, year, price, 
                         mileage, transmission, vin, seller_name, contact_phone, location, 
                         description, image_urls)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['listing_id'], data['url'], data['title'], data['listing_type'],
                        data['make'], data['model'], data['year'], data['price'],
                        data['mileage'], data['transmission'], data['vin'], data['seller_name'],
                        data['contact_phone'], data['location'], data['description'], data['image_urls']
                    ))
                    conn.commit()
                    print(f"    ✓ 保存: {data['title'][:30] if data['title'] else 'N/A'}...")
                except Exception as e:
                    print(f"    ✗ 錯誤: {e}")
    
    # ============== 爬取房屋 ==============
    print("\n--- 爬取房屋 ---")
    house_list_url = "https://house.51.ca/rental"
    html = scraper.fetch(house_list_url)
    if html:
        soup = BeautifulSoup(html, "lxml")
        import re
        links = soup.find_all('a', href=re.compile(r'/rental/ontario/[^/]+/[^/]+/\d+'))
        urls = list(set([f"https://house.51.ca{a['href'].split('?')[0]}" 
                        for a in links if a.get('href', '').startswith('/')]))[:max_items]
        
        for url in urls:
            print(f"  爬取: {url}")
            html = scraper.fetch(url)
            if html:
                data = scraper.parse_house_old(html, url)
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO house_listings 
                        (listing_id, url, title, listing_type, price, address, city, 
                         bedrooms, bathrooms, description, image_urls)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['listing_id'], data['url'], data['title'], data['listing_type'],
                        data['price'], data['address'], data['city'],
                        data['bedrooms'], data['bathrooms'], data['description'], data['image_urls']
                    ))
                    conn.commit()
                    print(f"    ✓ 保存: {data['title'][:30] if data['title'] else 'N/A'}...")
                except Exception as e:
                    print(f"    ✗ 錯誤: {e}")
    
    conn.close()
    print("\n✓ 舊方法爬取完成!")
    return OLD_DB_PATH


def compare_databases():
    """對比兩個資料庫的資料質量"""
    print("\n" + "=" * 60)
    print("對比新舊爬蟲資料質量")
    print("=" * 60)
    
    old_conn = sqlite3.connect(OLD_DB_PATH)
    new_conn = sqlite3.connect(NEW_DB_PATH)
    old_conn.row_factory = sqlite3.Row
    new_conn.row_factory = sqlite3.Row
    
    results = []
    
    # ============== 對比新聞 ==============
    print("\n📰 新聞對比:")
    print("-" * 40)
    
    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()
    
    # 獲取共同的 article_id
    old_cur.execute("SELECT article_id FROM news_articles")
    old_ids = set(r[0] for r in old_cur.fetchall())
    
    new_cur.execute("SELECT article_id FROM news_articles")
    new_ids = set(r[0] for r in new_cur.fetchall())
    
    common_ids = old_ids & new_ids
    print(f"  舊DB文章數: {len(old_ids)}")
    print(f"  新DB文章數: {len(new_ids)}")
    print(f"  共同文章數: {len(common_ids)}")
    
    if common_ids:
        news_fields = ['title', 'summary', 'content', 'category', 'author', 'source', 'publish_date', 'image_urls']
        
        for article_id in list(common_ids)[:5]:  # 只對比前5個
            old_cur.execute("SELECT * FROM news_articles WHERE article_id = ?", (article_id,))
            new_cur.execute("SELECT * FROM news_articles WHERE article_id = ?", (article_id,))
            
            old_row = dict(old_cur.fetchone())
            new_row = dict(new_cur.fetchone())
            
            print(f"\n  文章 {article_id}:")
            for field in news_fields:
                old_val = old_row.get(field)
                new_val = new_row.get(field)
                
                old_null = old_val is None or old_val == '' or old_val == 'null'
                new_null = new_val is None or new_val == '' or new_val == 'null'
                
                if old_null and not new_null:
                    status = "🆕 新方法有"
                elif not old_null and new_null:
                    status = "⚠️ 舊方法有"
                    results.append(('news', article_id, field, 'old_has_new_missing'))
                elif old_null and new_null:
                    status = "❌ 都沒有"
                else:
                    status = "✅ 都有"
                
                print(f"    {field:15}: {status}")
    
    # ============== 對比汽車 ==============
    print("\n🚗 汽車對比:")
    print("-" * 40)
    
    old_cur.execute("SELECT listing_id FROM auto_listings")
    old_ids = set(r[0] for r in old_cur.fetchall())
    
    new_cur.execute("SELECT listing_id FROM auto_listings")
    new_ids = set(r[0] for r in new_cur.fetchall())
    
    common_ids = old_ids & new_ids
    print(f"  舊DB汽車數: {len(old_ids)}")
    print(f"  新DB汽車數: {len(new_ids)}")
    print(f"  共同汽車數: {len(common_ids)}")
    
    if common_ids:
        auto_fields = ['title', 'make', 'model', 'year', 'price', 'mileage', 
                       'transmission', 'vin', 'seller_name', 'contact_phone', 'location', 'description']
        
        for listing_id in list(common_ids)[:5]:
            old_cur.execute("SELECT * FROM auto_listings WHERE listing_id = ?", (listing_id,))
            new_cur.execute("SELECT * FROM auto_listings WHERE listing_id = ?", (listing_id,))
            
            old_row = dict(old_cur.fetchone())
            new_row = dict(new_cur.fetchone())
            
            print(f"\n  汽車 {listing_id}:")
            for field in auto_fields:
                old_val = old_row.get(field)
                new_val = new_row.get(field)
                
                old_null = old_val is None or old_val == '' or old_val == 'null'
                new_null = new_val is None or new_val == '' or new_val == 'null'
                
                if old_null and not new_null:
                    status = "🆕 新方法有"
                elif not old_null and new_null:
                    status = "⚠️ 舊方法有"
                    results.append(('auto', listing_id, field, 'old_has_new_missing'))
                elif old_null and new_null:
                    status = "❌ 都沒有"
                else:
                    status = "✅ 都有"
                
                print(f"    {field:15}: {status}")
    
    # ============== 對比房屋 ==============
    print("\n🏠 房屋對比:")
    print("-" * 40)
    
    old_cur.execute("SELECT listing_id FROM house_listings")
    old_ids = set(r[0] for r in old_cur.fetchall())
    
    new_cur.execute("SELECT listing_id FROM house_listings")
    new_ids = set(r[0] for r in new_cur.fetchall())
    
    common_ids = old_ids & new_ids
    print(f"  舊DB房屋數: {len(old_ids)}")
    print(f"  新DB房屋數: {len(new_ids)}")
    print(f"  共同房屋數: {len(common_ids)}")
    
    if common_ids:
        house_fields = ['title', 'price', 'address', 'city', 'bedrooms', 'bathrooms', 'description']
        
        for listing_id in list(common_ids)[:5]:
            old_cur.execute("SELECT * FROM house_listings WHERE listing_id = ?", (listing_id,))
            new_cur.execute("SELECT * FROM house_listings WHERE listing_id = ?", (listing_id,))
            
            old_row = dict(old_cur.fetchone())
            new_row = dict(new_cur.fetchone())
            
            print(f"\n  房屋 {listing_id}:")
            for field in house_fields:
                old_val = old_row.get(field)
                new_val = new_row.get(field)
                
                old_null = old_val is None or old_val == '' or old_val == 'null'
                new_null = new_val is None or new_val == '' or new_val == 'null'
                
                if old_null and not new_null:
                    status = "🆕 新方法有"
                elif not old_null and new_null:
                    status = "⚠️ 舊方法有"
                    results.append(('house', listing_id, field, 'old_has_new_missing'))
                elif old_null and new_null:
                    status = "❌ 都沒有"
                else:
                    status = "✅ 都有"
                
                print(f"    {field:15}: {status}")
    
    old_conn.close()
    new_conn.close()
    
    # ============== 總結 ==============
    print("\n" + "=" * 60)
    print("總結: 舊方法有但新方法缺失的欄位")
    print("=" * 60)
    
    if results:
        for table, item_id, field, _ in results:
            print(f"  [{table}] {item_id}: {field}")
    else:
        print("  沒有發現舊方法獨有的資料")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='對比新舊爬蟲')
    parser.add_argument('--max', type=int, default=10, help='每類最多爬取數量')
    parser.add_argument('--compare-only', action='store_true', help='只對比，不爬取')
    args = parser.parse_args()
    
    if not args.compare_only:
        run_old_scraper(max_items=args.max)
    
    compare_databases()
