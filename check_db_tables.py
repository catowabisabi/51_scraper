import sqlite3

db_path = 'c:/Users/Chris/Desktop/app/CICD/HK-Garden-App/51_scraper/scrapers/data/51ca.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 列出所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

# 檢查 auto_listings 表
if 'auto_listings' in tables:
    c.execute("SELECT COUNT(*) FROM auto_listings")
    print(f"auto_listings 記錄數: {c.fetchone()[0]}")

# 檢查 url_queue 表
if 'url_queue' in tables:
    c.execute("SELECT COUNT(*) FROM url_queue WHERE url_type='auto' AND visited=0")
    print(f"未訪問的 auto URLs: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM url_queue WHERE url_type='auto' AND visited=1")
    print(f"已訪問的 auto URLs: {c.fetchone()[0]}")
    c.execute("SELECT url FROM url_queue WHERE url_type='auto' AND visited=0 LIMIT 5")
    print("前5個未訪問URL:")
    for r in c.fetchall():
        print(f"  {r[0]}")

conn.close()
