"""查看工作數據庫"""

import sqlite3
import json

conn = sqlite3.connect('scrapers/data/51ca.db')
cursor = conn.cursor()

# 查看表結構
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# 查看 jobs 表
cursor.execute("SELECT COUNT(*) FROM jobs")
count = cursor.fetchone()[0]
print(f"\nJobs count: {count}")

# 查看前5條
print("\n最近的工作:")
cursor.execute("""
    SELECT id, title, phone, location, address, category, publisher
    FROM jobs 
    ORDER BY id DESC
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    title = row[1][:40] if row[1] else 'N/A'
    print(f"  標題: {title}")
    print(f"  電話: {row[2] or 'N/A'}")
    print(f"  地點: {row[3] or 'N/A'}")
    print(f"  地址: {row[4] or 'N/A'}")
    print(f"  分類: {row[5] or 'N/A'}")
    print(f"  發布者: {row[6] or 'N/A'}")

# 統計有電話的
cursor.execute("SELECT COUNT(*) FROM jobs WHERE phone IS NOT NULL AND phone != ''")
with_phone = cursor.fetchone()[0]
print(f"\n有電話: {with_phone}/{count}")

conn.close()
