import sqlite3

db_path = 'c:/Users/Chris/Desktop/app/CICD/HK-Garden-App/51_scraper/scrapers/data/51ca.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 更新未訪問的詳情頁面優先級為 5
c.execute("""
    UPDATE url_queue 
    SET priority = 5 
    WHERE url_type = 'auto' 
    AND visited = 0 
    AND url LIKE '%/autos/%/%'
    AND url NOT LIKE '%?page=%'
""")
updated = c.rowcount
print(f"已更新 {updated} 個詳情頁面優先級為 5")

# 檢查結果
c.execute("SELECT COUNT(*) FROM url_queue WHERE url_type='auto' AND visited=0 AND priority=5")
print(f"優先級為5的未訪問URL: {c.fetchone()[0]}")

conn.commit()
conn.close()
