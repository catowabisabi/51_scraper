"""檢查為什麼沒有獲取更多房屋"""
import requests
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

# 獲取數據庫中的 listing IDs
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT listing_id FROM house_listings")
db_ids = set(r[0] for r in c.fetchall())
print(f"數據庫中的房屋數量: {len(db_ids)}")
print(f"數據庫中的 ID 樣本: {list(db_ids)[:5]}")

# 獲取 API 第一頁的 IDs
r = requests.get('https://house.51.ca/api/v7/property', 
    params={'limit': 50, 'page': 1, 'transactionType': 1, 'province': 'ontario'}, 
    timeout=30)
data = r.json()
props = data.get('data', [])
api_ids = [p.get('listingId') for p in props]
print(f"\nAPI 第一頁房屋數量: {len(api_ids)}")
print(f"API 返回的 ID 樣本: {api_ids[:5]}")

# 檢查重複
overlap = set(api_ids) & db_ids
print(f"\n重複的 ID 數量: {len(overlap)}")

# 新的 ID
new_ids = set(api_ids) - db_ids
print(f"新的 ID 數量: {len(new_ids)}")
print(f"新的 ID 樣本: {list(new_ids)[:5]}")

# 嘗試獲取第 5 頁看看
r = requests.get('https://house.51.ca/api/v7/property', 
    params={'limit': 50, 'page': 5, 'transactionType': 1, 'province': 'ontario'}, 
    timeout=30)
data = r.json()
props = data.get('data', [])
page5_ids = [p.get('listingId') for p in props]
print(f"\nAPI 第5頁房屋數量: {len(page5_ids)}")
print(f"第5頁 ID 樣本: {page5_ids[:5]}")

# 與第一頁比較
same_as_page1 = set(page5_ids) & set(api_ids)
print(f"與第一頁相同的 ID 數量: {len(same_as_page1)}")

conn.close()
