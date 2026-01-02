"""檢查服務帖子的 default-img 問題"""
import sqlite3
import json

conn = sqlite3.connect('../data/51ca.db')
c = conn.cursor()

# 檢查含 default-img 的帖子
c.execute("SELECT post_id, title, image_urls FROM service_posts WHERE image_urls LIKE '%default-img%'")
rows = c.fetchall()
print(f'含 default-img 的帖子: {len(rows)}')

for row in rows:
    print(f'  {row[0]}: {row[1][:30]}')
    images = json.loads(row[2]) if row[2] else []
    for img in images:
        if 'default-img' in img:
            print(f'    => {img}')

conn.close()
