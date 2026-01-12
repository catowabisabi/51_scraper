"""直接檢查數據庫實際數據量"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

print(f"數據庫路徑: {DB_PATH}")
print(f"文件存在: {os.path.exists(DB_PATH)}")
print(f"文件大小: {os.path.getsize(DB_PATH) / 1024:.1f} KB")
print()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 獲取所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]

print("=" * 50)
print("實際數據庫統計:")
print("=" * 50)

for table in tables:
    if table == 'sqlite_sequence':
        continue
    c.execute(f"SELECT COUNT(*) FROM {table}")
    count = c.fetchone()[0]
    print(f"  {table}: {count}")

print()
print("=" * 50)
print("詳細檢查:")
print("=" * 50)

# 房屋
c.execute("SELECT COUNT(*) FROM house_listings")
print(f"\n房屋總數: {c.fetchone()[0]}")
c.execute("SELECT listing_id, price, address FROM house_listings LIMIT 5")
print("房屋樣本:")
for r in c.fetchall():
    print(f"  ID:{r[0]}, 價格:{r[1]}, 地址:{r[2][:30] if r[2] else 'N/A'}...")

# 汽車
c.execute("SELECT COUNT(*) FROM auto_listings")
print(f"\n汽車總數: {c.fetchone()[0]}")
c.execute("SELECT car_id, title, price FROM auto_listings LIMIT 5")
print("汽車樣本:")
for r in c.fetchall():
    print(f"  ID:{r[0]}, 標題:{r[1][:30] if r[1] else 'N/A'}..., 價格:{r[2]}")

# 新聞
c.execute("SELECT COUNT(*) FROM news_articles")
print(f"\n新聞總數: {c.fetchone()[0]}")

# 工作
c.execute("SELECT COUNT(*) FROM jobs")
print(f"\n工作總數: {c.fetchone()[0]}")

# 集市
c.execute("SELECT COUNT(*) FROM market_posts")
print(f"\n集市總數: {c.fetchone()[0]}")

# 活動
c.execute("SELECT COUNT(*) FROM events")
print(f"\n活動總數: {c.fetchone()[0]}")

conn.close()
