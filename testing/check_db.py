"""检查数据库表"""
import sqlite3

conn = sqlite3.connect('scrapers/data/51ca.db')
c = conn.cursor()

# 总记录数
c.execute("SELECT COUNT(*) FROM market_posts")
print(f"Total records: {c.fetchone()[0]}")

# 有解密电话的记录（包含 - 的是真实电话号码）
c.execute("SELECT COUNT(*) FROM market_posts WHERE contact_phone LIKE '%-%'")
print(f"With decrypted phone (contains -): {c.fetchone()[0]}")

# 有加密电话的记录（base64 格式）
c.execute("SELECT COUNT(*) FROM market_posts WHERE contact_phone LIKE 'eyJ%'")
print(f"With encrypted phone (base64): {c.fetchone()[0]}")

# 显示解密电话的记录
print("\n=== Samples with decrypted phone ===")
c.execute("""
    SELECT post_id, title, contact_phone 
    FROM market_posts 
    WHERE contact_phone LIKE '%-%' 
    ORDER BY ROWID DESC 
    LIMIT 10
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1][:30]} | {r[2]}")

conn.close()
