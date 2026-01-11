"""检查数据库表"""
import sqlite3

conn = sqlite3.connect('scrapers/data/51ca.db')
c = conn.cursor()

# 列出所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

# 检查 market_posts 表
if 'market_posts' in tables:
    # 总记录数
    c.execute("SELECT COUNT(*) FROM market_posts")
    print(f"Total records: {c.fetchone()[0]}")
    
    # 统计有联系方式的记录
    c.execute("SELECT COUNT(*) FROM market_posts WHERE contact_phone IS NOT NULL AND contact_phone != ''")
    print(f"With phone: {c.fetchone()[0]}")
    
    c.execute("SELECT COUNT(*) FROM market_posts WHERE email IS NOT NULL AND email != ''")
    print(f"With email: {c.fetchone()[0]}")
    
    c.execute("SELECT COUNT(*) FROM market_posts WHERE wechat_no IS NOT NULL AND wechat_no != ''")
    print(f"With wechat: {c.fetchone()[0]}")
    
    c.execute("SELECT COUNT(*) FROM market_posts WHERE category_id IS NOT NULL")
    print(f"With category_id: {c.fetchone()[0]}")
    
    c.execute("SELECT COUNT(*) FROM market_posts WHERE location_id IS NOT NULL")
    print(f"With location_id: {c.fetchone()[0]}")
    
    # 按分类统计
    print("\n=== By Category ===")
    c.execute("SELECT category_slug, COUNT(*) FROM market_posts GROUP BY category_slug ORDER BY category_slug")
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}")
    
    # 显示几条有联系方式的记录
    print("\n=== Samples with contact info ===")
    c.execute("""
        SELECT post_id, title, contact_phone, email, wechat_no 
        FROM market_posts 
        WHERE email IS NOT NULL AND email != '' 
        LIMIT 5
    """)
    for r in c.fetchall():
        phone = r[2][:30] + '...' if r[2] and len(r[2]) > 30 else r[2]
        print(f"  {r[0]}: {r[1][:25]}...")
        print(f"    phone: {phone}")
        print(f"    email: {r[3]}")
        print(f"    wechat: {r[4]}")

conn.close()
