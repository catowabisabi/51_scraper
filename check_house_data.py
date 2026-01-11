import sqlite3
import json

conn = sqlite3.connect('scrapers/data/51ca.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 查看表結構
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='house_listings'")
result = c.fetchone()
if result:
    print("=== Table Schema ===")
    print(result[0])

# 統計資料
print("\n=== Data Stats ===")
c.execute('SELECT COUNT(*) FROM house_listings')
print(f'Total: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM house_listings WHERE description IS NOT NULL')
print(f'With desc: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM house_listings WHERE agent_phone IS NOT NULL')
print(f'With phone: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM house_listings WHERE lat IS NOT NULL')
print(f'With coords: {c.fetchone()[0]}')

c.execute('SELECT listing_type, COUNT(*) FROM house_listings GROUP BY listing_type')
print(f'\nBy type:')
for row in c.fetchall():
    print(f'  {row[0]}: {row[1]}')

# 查看買賣和出租各一條記錄
print("\n=== Sample Records ===")
for lt in ['買賣', '出租']:
    c.execute('SELECT * FROM house_listings WHERE listing_type=? LIMIT 1', (lt,))
    row = c.fetchone()
    if row:
        print(f'\n--- {lt} ---')
        print(f"ID: {row['listing_id']}")
        print(f"Title: {row['title']}")
        print(f"Price: ${row['price']:,.0f} ({row['price_unit']})" if row['price'] else "Price: N/A")
        print(f"Address: {row['address']}, {row['city']}")
        print(f"Rooms: {row['bedrooms']}房 {row['bathrooms']}衛")
        print(f"Coords: {row['lat']}, {row['lon']}")
        desc = row['description']
        print(f"Desc: {desc[:80] if desc else None}...")
        print(f"Agent: {row['agent_name']} | {row['agent_phone']}")
        imgs = json.loads(row['image_urls']) if row['image_urls'] else []
        print(f"Images: {len(imgs)} photos")

conn.close()
