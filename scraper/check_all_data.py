"""檢查所有數據統計"""
import sqlite3

conn = sqlite3.connect('../data/51ca.db')
c = conn.cursor()

print('=== 商家數據統計 ===')
c.execute('SELECT COUNT(*) FROM service_merchants')
print(f'總商家數: {c.fetchone()[0]}')

print('\n=== 商家樣本 (前5個) ===')
c.execute('SELECT merchant_id, name, english_name, phone, address FROM service_merchants LIMIT 5')
for row in c.fetchall():
    print(f'  ID: {row[0]}')
    print(f'    名稱: {row[1]}')
    print(f'    英文: {row[2]}')
    print(f'    電話: {row[3]}')
    print(f'    地址: {row[4]}')
    print()

print('=== 有公司介紹的商家 ===')
c.execute('SELECT COUNT(*) FROM service_merchants WHERE description IS NOT NULL AND description != ""')
print(f'有介紹: {c.fetchone()[0]}')

print('\n=== 有圖片的商家 ===')
c.execute('SELECT COUNT(*) FROM service_merchants WHERE image_urls IS NOT NULL')
print(f'有圖片: {c.fetchone()[0]}')

print('\n' + '='*50)
print('全部資料統計')
print('='*50)

tables = [
    ('news_articles', '新聞'),
    ('house_listings', '房屋'),
    ('job_listings', '工作'),
    ('service_posts', '服務帖子'),
    ('service_merchants', '商家'),
    ('market_posts', '集市'),
    ('auto_listings', '汽車'),
]

total = 0
for table, name in tables:
    c.execute(f'SELECT COUNT(*) FROM {table}')
    count = c.fetchone()[0]
    total += count
    print(f'{name}: {count}')

print(f'\n總計: {total}')
conn.close()
