"""使用不同的城市參數獲取更多房屋"""
import requests
import sqlite3
import os
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 安省主要城市 - 擴展列表
CITIES = [
    'toronto', 'mississauga', 'brampton', 'hamilton', 'ottawa',
    'london', 'markham', 'vaughan', 'kitchener', 'windsor',
    'richmond-hill', 'oakville', 'burlington', 'oshawa', 'barrie',
    'cambridge', 'guelph', 'waterloo', 'ajax', 'whitby',
    'scarborough', 'north-york', 'etobicoke', 'pickering', 'newmarket',
    'aurora', 'milton', 'stouffville', 'king', 'caledon',
    'georgina', 'clarington', 'brock', 'scugog', 'uxbridge',
    'east-gwillimbury', 'whitchurch-stouffville', 'halton-hills',
    'niagara-falls', 'st-catharines', 'welland', 'thorold', 'fort-erie',
    'grimsby', 'lincoln', 'pelham', 'wainfleet', 'west-lincoln',
    'peterborough', 'kawartha-lakes', 'cobourg', 'port-hope', 'belleville',
    'kingston', 'brockville', 'cornwall', 'hawkesbury', 'pembroke',
    'sudbury', 'north-bay', 'timmins', 'sault-ste-marie', 'thunder-bay',
]

# 不同價格區間 - 更細分
PRICE_RANGES = [
    {'minPrice': 0, 'maxPrice': 300000},
    {'minPrice': 300000, 'maxPrice': 500000},
    {'minPrice': 500000, 'maxPrice': 600000},
    {'minPrice': 600000, 'maxPrice': 700000},
    {'minPrice': 700000, 'maxPrice': 800000},
    {'minPrice': 800000, 'maxPrice': 900000},
    {'minPrice': 900000, 'maxPrice': 1000000},
    {'minPrice': 1000000, 'maxPrice': 1200000},
    {'minPrice': 1200000, 'maxPrice': 1500000},
    {'minPrice': 1500000, 'maxPrice': 2000000},
    {'minPrice': 2000000, 'maxPrice': 3000000},
    {'minPrice': 3000000, 'maxPrice': 10000000},
]

# 建築類型
BUILDING_TYPES = [1, 2, 3, 5, 6, 7, 14, 17, 18, 19]  # 獨立屋, 半獨立, 鎮屋, 等等

def fetch_houses():
    """從 API 獲取房屋 - 使用不同參數"""
    print("=" * 50)
    print("獲取房屋數據 (使用不同城市和價格區間)")
    print("=" * 50)
    
    API_URL = "https://house.51.ca/api/v7/property"
    
    conn = get_connection()
    c = conn.cursor()
    
    # 獲取已有的 listing_id
    c.execute("SELECT listing_id FROM house_listings")
    existing = set(r[0] for r in c.fetchall())
    print(f"已有房屋: {len(existing)}")
    
    total_saved = 0
    
    # 嘗試不同城市
    for city in CITIES:
        for trans_type in [1, 2]:
            try:
                params = {
                    'limit': 100,
                    'page': 1,
                    'transactionType': trans_type,
                    'cities': city,
                }
                
                r = requests.get(API_URL, params=params, timeout=30)
                if r.status_code != 200:
                    continue
                
                data = r.json()
                props = data.get('data', [])
                
                if not props:
                    continue
                
                new_count = 0
                for prop in props:
                    listing_id = prop.get('listingId')
                    if not listing_id or listing_id in existing:
                        continue
                    
                    existing.add(listing_id)
                    
                    location = prop.get('location', {})
                    address = location.get('streetAddress', '')
                    city_name = location.get('city', '')
                    full_address = f"{address}, {city_name}" if city_name else address
                    
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
                    print(f"  {city} (type={trans_type}): 新增 {new_count}")
                    conn.commit()
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"  {city}: 錯誤 {e}")
                continue
    
    # 嘗試不同價格區間
    print("\n使用價格區間獲取更多...")
    for price_range in PRICE_RANGES:
        for trans_type in [1, 2]:
            try:
                params = {
                    'limit': 100,
                    'page': 1,
                    'transactionType': trans_type,
                    'province': 'ontario',
                    **price_range
                }
                
                r = requests.get(API_URL, params=params, timeout=30)
                if r.status_code != 200:
                    continue
                
                data = r.json()
                props = data.get('data', [])
                
                if not props:
                    continue
                
                new_count = 0
                for prop in props:
                    listing_id = prop.get('listingId')
                    if not listing_id or listing_id in existing:
                        continue
                    
                    existing.add(listing_id)
                    
                    location = prop.get('location', {})
                    address = location.get('streetAddress', '')
                    city_name = location.get('city', '')
                    full_address = f"{address}, {city_name}" if city_name else address
                    
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
                    print(f"  價格 {price_range['minPrice']}-{price_range['maxPrice']} (type={trans_type}): 新增 {new_count}")
                    conn.commit()
                
                time.sleep(0.3)
                
            except Exception as e:
                continue
    
    # 嘗試不同建築類型
    print("\n使用建築類型獲取更多...")
    for bldg_type in BUILDING_TYPES:
        for trans_type in [1, 2]:
            try:
                params = {
                    'limit': 100,
                    'page': 1,
                    'transactionType': trans_type,
                    'province': 'ontario',
                    'propertyType': bldg_type
                }
                
                r = requests.get(API_URL, params=params, timeout=30)
                if r.status_code != 200:
                    continue
                
                data = r.json()
                props = data.get('data', [])
                
                if not props:
                    continue
                
                new_count = 0
                for prop in props:
                    listing_id = prop.get('listingId')
                    if not listing_id or listing_id in existing:
                        continue
                    
                    existing.add(listing_id)
                    
                    location = prop.get('location', {})
                    address = location.get('streetAddress', '')
                    city_name = location.get('city', '')
                    full_address = f"{address}, {city_name}" if city_name else address
                    
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
                    print(f"  建築類型 {bldg_type} (trans={trans_type}): 新增 {new_count}")
                    conn.commit()
                
                time.sleep(0.3)
                
            except Exception as e:
                continue
    
    # 城市 + 價格組合
    print("\n城市+價格組合...")
    for city in CITIES[:20]:  # 主要城市
        for price_range in PRICE_RANGES:
            try:
                params = {
                    'limit': 100,
                    'page': 1,
                    'transactionType': 1,
                    'cities': city,
                    **price_range
                }
                
                r = requests.get(API_URL, params=params, timeout=30)
                if r.status_code != 200:
                    continue
                
                data = r.json()
                props = data.get('data', [])
                
                new_count = 0
                for prop in props:
                    listing_id = prop.get('listingId')
                    if not listing_id or listing_id in existing:
                        continue
                    
                    existing.add(listing_id)
                    
                    location = prop.get('location', {})
                    address = location.get('streetAddress', '')
                    city_name = location.get('city', '')
                    full_address = f"{address}, {city_name}" if city_name else address
                    
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
                    print(f"  {city} ${price_range['minPrice']}-{price_range['maxPrice']}: 新增 {new_count}")
                    conn.commit()
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
    
    conn.commit()
    conn.close()
    
    print(f"\n房屋新增: {total_saved}")
    return total_saved


if __name__ == "__main__":
    saved = fetch_houses()
    
    # 檢查最終數量
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM house_listings")
    print(f"\n房屋總數: {c.fetchone()[0]}")
    conn.close()
