"""测试 market_scraper_playwright 获取解密电话"""
import sys
sys.path.insert(0, '.')

from scrapers.market_scraper_playwright import MarketScraperPlaywright

scraper = MarketScraperPlaywright()
scraper.run(
    category='all',
    max_items=10,
    fetch_details=True,
    headless=False
)

# 检查保存的数据
import sqlite3
conn = sqlite3.connect('scrapers/data/51ca.db')
c = conn.cursor()

# 查找有真正电话号码的记录（不是加密的 base64）
c.execute("""
    SELECT post_id, title, contact_phone, email 
    FROM market_posts 
    WHERE contact_phone LIKE '%-%' OR contact_phone LIKE '%(%)%'
    ORDER BY ROWID DESC 
    LIMIT 10
""")

print("\n" + "="*60)
print("Records with decrypted phone numbers:")
print("="*60)
for r in c.fetchall():
    print(f"  {r[0]}: {r[1][:30]}")
    print(f"    Phone: {r[2]}")
    print(f"    Email: {r[3]}")
    print()

conn.close()
