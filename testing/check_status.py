"""快速檢查數據庫狀態"""
from scrapers.models import get_connection

conn = get_connection()
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM url_queue WHERE url_type='auto'")
print(f"汽車URL總數: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM url_queue WHERE url_type='auto' AND visited=0")
print(f"未訪問: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM auto_listings")
print(f"汽車數據: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM house_listings")
print(f"房屋數據: {c.fetchone()[0]}")

# 看看有哪些詳情頁 URL
c.execute("SELECT url FROM url_queue WHERE url_type='auto' AND url LIKE '%/used-cars/%' LIMIT 5")
for row in c.fetchall():
    print(f"  {row[0]}")

conn.close()
