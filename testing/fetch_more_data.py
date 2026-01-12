"""
直接從 API 獲取更多房屋和汽車數據
"""
import requests
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_houses(max_pages=100):
    """從 API 獲取房屋"""
    print("=" * 50)
    print("獲取房屋數據...")
    print("=" * 50)
    
    API_URL = "https://house.51.ca/api/v7/property"
    saved = 0
    
    conn = get_connection()
    c = conn.cursor()
    
    # 獲取已有的 listing_id
    c.execute("SELECT listing_id FROM house_listings")
    existing = set(r[0] for r in c.fetchall())
    print(f"已有房屋: {len(existing)}")
    
    for trans_type in [1, 2]:  # 1=買賣, 2=出租
        type_name = "買賣" if trans_type == 1 else "出租"
        print(f"\n正在獲取{type_name}房屋...")
        
        for page in range(1, max_pages + 1):
            try:
                params = {
                    'limit': 50,
                    'page': page,
                    'transactionType': trans_type,
                    'province': 'ontario',
                }
                
                r = requests.get(API_URL, params=params, timeout=30)
                if r.status_code != 200:
                    print(f"  頁 {page}: API 錯誤 {r.status_code}")
                    break
                
                data = r.json()
                properties = data.get('data', [])
                
                if not properties:
                    print(f"  頁 {page}: 沒有更多數據")
                    break
                
                new_count = 0
                for prop in properties:
                    listing_id = prop.get('listingId')  # 注意: API 返回的是 listingId 不是 mlsNumber
                    if not listing_id or listing_id in existing:
                        continue
                    
                    existing.add(listing_id)
                    
                    # 提取地址
                    location = prop.get('location', {})
                    address = location.get('streetAddress', '')
                    city = location.get('city', '')
                    full_address = f"{address}, {city}" if city else address
                    
                    # 解析數據
                    c.execute("""
                        INSERT OR REPLACE INTO house_listings (
                            listing_id, url, title, price, address, bedrooms, 
                            bathrooms, sqft, property_type, description, 
                            image_urls, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        listing_id,
                        f"https://house.51.ca/mls/{listing_id}",
                        full_address,
                        prop.get('listingPrice'),
                        full_address,
                        prop.get('bedrooms'),
                        prop.get('bathrooms'),
                        prop.get('approximateSf'),
                        prop.get('buildingType'),
                        None,
                        prop.get('coverPage'),
                        datetime.now().isoformat()
                    ))
                    new_count += 1
                    saved += 1
                
                if new_count > 0:
                    print(f"  頁 {page}: 新增 {new_count} 筆")
                    conn.commit()
                
                if page % 10 == 0:
                    print(f"  已處理 {page} 頁，共新增 {saved} 筆")
                    
            except Exception as e:
                print(f"  頁 {page}: 錯誤 {e}")
                continue
    
    conn.commit()
    conn.close()
    print(f"\n房屋新增: {saved} 筆")
    return saved


def fetch_autos(max_pages=100):
    """從網站獲取汽車"""
    print("\n" + "=" * 50)
    print("獲取汽車數據...")
    print("=" * 50)
    
    from bs4 import BeautifulSoup
    
    BASE_URL = "https://www.51.ca/autos"
    saved = 0
    
    conn = get_connection()
    c = conn.cursor()
    
    # 獲取已有的 ID
    c.execute("SELECT id FROM auto_listings")
    existing = set(r[0] for r in c.fetchall())
    print(f"已有汽車: {len(existing)}")
    
    categories = ['used-cars', 'new-cars', 'lease-cars']
    
    for category in categories:
        print(f"\n正在獲取 {category}...")
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{BASE_URL}/{category}?page={page}"
                
                r = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if r.status_code != 200:
                    print(f"  頁 {page}: 錯誤 {r.status_code}")
                    break
                
                soup = BeautifulSoup(r.text, 'lxml')
                
                # 找汽車列表
                car_items = soup.select('a[href*="/autos/"][href*="/cars/"]')
                
                if not car_items:
                    print(f"  頁 {page}: 沒有更多數據")
                    break
                
                new_count = 0
                seen = set()
                
                for item in car_items:
                    href = item.get('href', '')
                    if '/my/' in href:
                        continue
                    
                    # 提取 ID
                    import re
                    match = re.search(r'/cars/(\d+)', href)
                    if not match:
                        continue
                    
                    car_id = int(match.group(1))
                    if car_id in existing or car_id in seen:
                        continue
                    
                    seen.add(car_id)
                    existing.add(car_id)
                    
                    # 提取標題
                    title = item.get_text(strip=True)[:200] if item.get_text(strip=True) else ''
                    
                    c.execute("""
                        INSERT OR REPLACE INTO auto_listings (
                            id, url, title, scraped_at
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        car_id,
                        f"https://www.51.ca{href}" if href.startswith('/') else href,
                        title,
                        datetime.now().isoformat()
                    ))
                    new_count += 1
                    saved += 1
                
                if new_count > 0:
                    print(f"  頁 {page}: 新增 {new_count} 筆")
                    conn.commit()
                    
            except Exception as e:
                print(f"  頁 {page}: 錯誤 {e}")
                continue
    
    conn.commit()
    conn.close()
    print(f"\n汽車新增: {saved} 筆")
    return saved


if __name__ == "__main__":
    print("=" * 50)
    print(f"開始獲取更多數據 - {datetime.now()}")
    print("=" * 50)
    
    houses = fetch_houses(max_pages=50)
    autos = fetch_autos(max_pages=50)
    
    print("\n" + "=" * 50)
    print("完成!")
    print(f"  房屋新增: {houses}")
    print(f"  汽車新增: {autos}")
    print("=" * 50)
    
    # 檢查最終數量
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM house_listings")
    print(f"\n房屋總數: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM auto_listings")
    print(f"汽車總數: {c.fetchone()[0]}")
    conn.close()
