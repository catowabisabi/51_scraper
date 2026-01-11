"""檢查 market 數據"""
import sqlite3
import os

# 使用正確的數據庫路徑
db_path = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看記錄數
cursor.execute('SELECT COUNT(*) FROM market_posts')
print(f'Total records: {cursor.fetchone()[0]}')

# 查看有聯繫方式的記錄
cursor.execute("SELECT COUNT(*) FROM market_posts WHERE contact_phone != '' OR email != '' OR wechat_no != ''")
print(f'With contact: {cursor.fetchone()[0]}')

# 查看有位置的記錄
cursor.execute("SELECT COUNT(*) FROM market_posts WHERE location_en != '' OR location_zh != ''")
print(f'With location: {cursor.fetchone()[0]}')

# 查看有分類信息的記錄
cursor.execute("SELECT COUNT(*) FROM market_posts WHERE category_id IS NOT NULL")
print(f'With category_id: {cursor.fetchone()[0]}')

# 按分類統計
print("\n=== By Category ===")
cursor.execute("SELECT category_slug, COUNT(*) FROM market_posts GROUP BY category_slug")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# 查看樣本
print("\n=== Samples ===")
cursor.execute('''
    SELECT post_id, title, price, category_slug, location_en, contact_phone, email, wechat_no, photos
    FROM market_posts LIMIT 3
''')
for row in cursor.fetchall():
    print(f'\n{row[0]}: {row[1][:40]}')
    print(f'  Price: ${row[2]}, Category: {row[3]}')
    print(f'  Location: {row[4]}')
    print(f'  Phone: {row[5]}, Email: {row[6]}, WeChat: {row[7]}')
    photos = row[8]
    if photos:
        import json
        try:
            p = json.loads(photos)
            print(f'  Photos: {len(p)} images')
        except:
            print(f'  Photos: {photos[:50]}...')

conn.close()
