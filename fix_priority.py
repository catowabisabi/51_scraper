import sqlite3

db_path = 'c:/Users/Chris/Desktop/app/CICD/HK-Garden-App/51_scraper/scrapers/data/51ca.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 查看優先級分佈
c.execute("""
    SELECT priority, COUNT(*) as cnt 
    FROM url_queue 
    WHERE url_type = 'auto' AND visited = 0
    GROUP BY priority
    ORDER BY priority DESC
""")
print("未訪問URL優先級分佈:")
for row in c.fetchall():
    print(f"  優先級 {row[0]}: {row[1]} 個")

# 把列表頁面 (帶 ?page=) 優先級降為 0
c.execute("""
    UPDATE url_queue 
    SET priority = 0 
    WHERE url_type = 'auto' 
    AND visited = 0 
    AND url LIKE '%?page=%'
""")
updated_list = c.rowcount
print(f"\n已降低 {updated_list} 個列表頁面優先級為 0")

# 把詳情頁面優先級設為 10
c.execute("""
    UPDATE url_queue 
    SET priority = 10 
    WHERE url_type = 'auto' 
    AND visited = 0 
    AND url NOT LIKE '%?page=%'
    AND url LIKE '%/autos/%/%'
""")
updated_detail = c.rowcount
print(f"已提高 {updated_detail} 個詳情頁面優先級為 10")

conn.commit()

# 再次查看優先級分佈
c.execute("""
    SELECT priority, COUNT(*) as cnt 
    FROM url_queue 
    WHERE url_type = 'auto' AND visited = 0
    GROUP BY priority
    ORDER BY priority DESC
""")
print("\n更新後的優先級分佈:")
for row in c.fetchall():
    print(f"  優先級 {row[0]}: {row[1]} 個")

conn.close()
