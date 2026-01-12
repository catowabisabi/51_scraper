"""
直接從 house.51.ca HTML 頁面抓取房屋數據
繞過 API 限制
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
from datetime import datetime
import json

DB_PATH = "scrapers/data/51ca.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def scrape_house_listings():
    """從 HTML 頁面抓取房屋列表"""
    print("=" * 50)
    print("從 HTML 頁面抓取房屋數據")
    print("=" * 50)
    
    conn = get_connection()
    c = conn.cursor()
    
    # 獲取已有的 listing_id
    c.execute("SELECT listing_id FROM house_listings")
    existing = set(r[0] for r in c.fetchall())
    print(f"已有房屋: {len(existing)}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 不同的搜索URL
    urls = [
        # 出售 - 不同城市
        "https://house.51.ca/list?transactionType=1&cities=toronto",
        "https://house.51.ca/list?transactionType=1&cities=mississauga",
        "https://house.51.ca/list?transactionType=1&cities=brampton",
        "https://house.51.ca/list?transactionType=1&cities=markham",
        "https://house.51.ca/list?transactionType=1&cities=vaughan",
        "https://house.51.ca/list?transactionType=1&cities=richmond-hill",
        "https://house.51.ca/list?transactionType=1&cities=oakville",
        "https://house.51.ca/list?transactionType=1&cities=burlington",
        "https://house.51.ca/list?transactionType=1&cities=hamilton",
        "https://house.51.ca/list?transactionType=1&cities=ottawa",
        # 出租
        "https://house.51.ca/list?transactionType=2&cities=toronto",
        "https://house.51.ca/list?transactionType=2&cities=mississauga",
        "https://house.51.ca/list?transactionType=2&cities=brampton",
        "https://house.51.ca/list?transactionType=2&cities=markham",
        "https://house.51.ca/list?transactionType=2&cities=vaughan",
        # 不同價格
        "https://house.51.ca/list?transactionType=1&minPrice=0&maxPrice=500000",
        "https://house.51.ca/list?transactionType=1&minPrice=500000&maxPrice=800000",
        "https://house.51.ca/list?transactionType=1&minPrice=800000&maxPrice=1000000",
        "https://house.51.ca/list?transactionType=1&minPrice=1000000&maxPrice=1500000",
        "https://house.51.ca/list?transactionType=1&minPrice=1500000&maxPrice=2000000",
        "https://house.51.ca/list?transactionType=1&minPrice=2000000&maxPrice=5000000",
    ]
    
    total_saved = 0
    
    for url in urls:
        try:
            print(f"\n處理: {url}")
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"  跳過 (status={r.status_code})")
                continue
            
            # 找 __NEXT_DATA__ 中的數據
            soup = BeautifulSoup(r.text, 'lxml')
            script = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if not script:
                print("  沒有找到 __NEXT_DATA__")
                continue
            
            data = json.loads(script.string)
            props_data = data.get('props', {}).get('pageProps', {}).get('data', [])
            
            if not props_data:
                print("  沒有數據")
                continue
            
            new_count = 0
            for prop in props_data:
                listing_id = prop.get('listingId')
                if not listing_id or listing_id in existing:
                    continue
                
                existing.add(listing_id)
                
                location = prop.get('location', {})
                address = location.get('streetAddress', '')
                city = location.get('city', '')
                full_address = f"{address}, {city}" if city else address
                
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
                total_saved += 1
            
            if new_count > 0:
                print(f"  新增: {new_count}")
                conn.commit()
            else:
                print("  無新數據")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  錯誤: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n總共新增: {total_saved}")
    return total_saved


def scrape_auto_listings():
    """從 auto.51.ca 抓取汽車數據"""
    print("\n" + "=" * 50)
    print("從 auto.51.ca 抓取汽車數據")
    print("=" * 50)
    
    conn = get_connection()
    c = conn.cursor()
    
    # 檢查表結構
    c.execute("PRAGMA table_info(auto_listings)")
    columns = [col[1] for col in c.fetchall()]
    print(f"auto_listings 欄位: {columns}")
    
    # 確定 ID 欄位
    id_col = 'listing_id' if 'listing_id' in columns else 'id'
    
    # 獲取已有的 ID
    c.execute(f"SELECT {id_col} FROM auto_listings")
    existing = set(str(r[0]) for r in c.fetchall())
    print(f"已有汽車: {len(existing)}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 不同搜索條件
    urls = []
    
    # 不同品牌
    makes = ['toyota', 'honda', 'bmw', 'mercedes-benz', 'lexus', 'audi', 'mazda', 
             'hyundai', 'kia', 'ford', 'chevrolet', 'nissan', 'volkswagen', 'subaru',
             'jeep', 'gmc', 'dodge', 'chrysler', 'acura', 'infiniti', 'porsche', 'tesla']
    
    for make in makes:
        urls.append(f"https://auto.51.ca/search?make={make}")
    
    # 不同年份
    for year in range(2024, 2015, -1):
        urls.append(f"https://auto.51.ca/search?year_from={year}&year_to={year}")
    
    # 不同價格
    price_ranges = [
        (0, 10000), (10000, 20000), (20000, 30000), (30000, 40000),
        (40000, 50000), (50000, 75000), (75000, 100000), (100000, 200000)
    ]
    for min_p, max_p in price_ranges:
        urls.append(f"https://auto.51.ca/search?price_from={min_p}&price_to={max_p}")
    
    # 不同頁面
    for page in range(1, 21):
        urls.append(f"https://auto.51.ca/search?page={page}")
    
    total_saved = 0
    
    for url in urls:
        try:
            print(f"\n處理: {url}")
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"  跳過 (status={r.status_code})")
                continue
            
            soup = BeautifulSoup(r.text, 'lxml')
            
            # 找汽車列表
            car_links = soup.find_all('a', href=re.compile(r'/detail/\d+'))
            
            if not car_links:
                # 嘗試其他選擇器
                car_links = soup.select('.car-item a, .listing-item a, .search-result a')
            
            new_count = 0
            for link in car_links:
                href = link.get('href', '')
                match = re.search(r'/detail/(\d+)', href)
                if not match:
                    continue
                
                car_id = match.group(1)
                if car_id in existing:
                    continue
                
                existing.add(car_id)
                
                # 提取基本信息
                title = link.get_text(strip=True)[:200] if link.get_text(strip=True) else ''
                
                # 簡單插入
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO auto_listings (
                            listing_id, url, title, scraped_at
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        car_id,
                        f"https://auto.51.ca/detail/{car_id}",
                        title,
                        datetime.now().isoformat()
                    ))
                    new_count += 1
                    total_saved += 1
                except Exception as e:
                    print(f"    插入錯誤: {e}")
                    continue
            
            if new_count > 0:
                print(f"  新增: {new_count}")
                conn.commit()
            else:
                print("  無新數據")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  錯誤: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n汽車總共新增: {total_saved}")
    return total_saved


if __name__ == "__main__":
    # 抓取房屋
    house_saved = scrape_house_listings()
    
    # 抓取汽車
    auto_saved = scrape_auto_listings()
    
    # 檢查最終數量
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM house_listings")
    print(f"\n房屋總數: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM auto_listings")
    print(f"汽車總數: {c.fetchone()[0]}")
    conn.close()
