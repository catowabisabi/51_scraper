"""
直接調用房屋API獲取更多數據
"""
import requests
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join("scrapers", "data", "51ca.db")

def fetch_house_data():
    """直接通過API獲取房屋數據"""
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 確保表存在
    c.execute("""
        CREATE TABLE IF NOT EXISTS house_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT UNIQUE,
            url TEXT,
            title TEXT,
            price REAL,
            address TEXT,
            city TEXT,
            province TEXT,
            postal_code TEXT,
            bedrooms INTEGER,
            bathrooms REAL,
            sqft INTEGER,
            lot_size TEXT,
            property_type TEXT,
            listing_type TEXT,
            description TEXT,
            features TEXT,
            images TEXT,
            agent_info TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://house.51.ca/'
    }
    
    total_saved = 0
    
    # 爬取買賣房屋 (transaction_type=1) 
    print("獲取買賣房屋...")
    for page in range(1, 21):  # 20頁
        try:
            url = f"https://house.51.ca/api/v7/property?limit=50&page={page}&transactionType=1"
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()
            
            properties = data.get('data', [])
            if not properties:
                break
                
            for prop in properties:
                try:
                    # 提取數據
                    property_data = {
                        'property_id': str(prop.get('id', '')),
                        'url': f"https://house.51.ca/property/{prop.get('id', '')}",
                        'title': prop.get('address', ''),
                        'price': float(prop.get('price', 0)) if prop.get('price') else None,
                        'address': prop.get('address', ''),
                        'city': prop.get('municipality', ''),
                        'province': 'Ontario',  # 默認安省
                        'postal_code': prop.get('postalCode', ''),
                        'bedrooms': int(prop.get('bedrooms', 0)) if prop.get('bedrooms') else None,
                        'bathrooms': float(prop.get('washrooms', 0)) if prop.get('washrooms') else None,
                        'sqft': int(prop.get('sqft', 0)) if prop.get('sqft') else None,
                        'property_type': prop.get('type', ''),
                        'listing_type': '買賣',
                        'description': prop.get('description', ''),
                        'images': json.dumps(prop.get('images', [])) if prop.get('images') else None,
                    }
                    
                    # 插入數據庫
                    c.execute("""
                        INSERT OR REPLACE INTO house_listings (
                            property_id, url, title, price, address, city, province, 
                            postal_code, bedrooms, bathrooms, sqft, property_type, 
                            listing_type, description, images
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(property_data.values()))
                    
                    if c.rowcount > 0:
                        total_saved += 1
                        
                except Exception as e:
                    print(f"處理房屋數據錯誤: {e}")
            
            conn.commit()
            print(f"頁面 {page}: 處理 {len(properties)} 筆，已保存 {total_saved} 筆")
            
        except Exception as e:
            print(f"獲取頁面 {page} 錯誤: {e}")
            continue
    
    # 爬取出租房屋 (transaction_type=2)
    print("獲取出租房屋...")  
    for page in range(1, 21):  # 20頁
        try:
            url = f"https://house.51.ca/api/v7/property?limit=50&page={page}&transactionType=2"
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()
            
            properties = data.get('data', [])
            if not properties:
                break
                
            for prop in properties:
                try:
                    property_data = {
                        'property_id': str(prop.get('id', '')),
                        'url': f"https://house.51.ca/property/{prop.get('id', '')}",
                        'title': prop.get('address', ''),
                        'price': float(prop.get('price', 0)) if prop.get('price') else None,
                        'address': prop.get('address', ''),
                        'city': prop.get('municipality', ''),
                        'province': 'Ontario',
                        'postal_code': prop.get('postalCode', ''),
                        'bedrooms': int(prop.get('bedrooms', 0)) if prop.get('bedrooms') else None,
                        'bathrooms': float(prop.get('washrooms', 0)) if prop.get('washrooms') else None,
                        'sqft': int(prop.get('sqft', 0)) if prop.get('sqft') else None,
                        'property_type': prop.get('type', ''),
                        'listing_type': '出租',
                        'description': prop.get('description', ''),
                        'images': json.dumps(prop.get('images', [])) if prop.get('images') else None,
                    }
                    
                    c.execute("""
                        INSERT OR REPLACE INTO house_listings (
                            property_id, url, title, price, address, city, province, 
                            postal_code, bedrooms, bathrooms, sqft, property_type, 
                            listing_type, description, images
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(property_data.values()))
                    
                    if c.rowcount > 0:
                        total_saved += 1
                        
                except Exception as e:
                    print(f"處理房屋數據錯誤: {e}")
            
            conn.commit()
            print(f"頁面 {page}: 處理 {len(properties)} 筆，總計已保存 {total_saved} 筆")
            
        except Exception as e:
            print(f"獲取頁面 {page} 錯誤: {e}")
            continue
    
    conn.close()
    print(f"完成！總共保存 {total_saved} 套房屋")

if __name__ == "__main__":
    fetch_house_data()