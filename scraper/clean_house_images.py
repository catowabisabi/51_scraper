"""清理房源中的無效圖片"""
import sqlite3
import json

conn = sqlite3.connect('../data/51ca.db')
c = conn.cursor()

# 檢查房源圖片
c.execute('SELECT listing_id, image_urls FROM house_listings WHERE image_urls IS NOT NULL')
rows = c.fetchall()

print("=== 檢查房源圖片 ===")
count = 0
for row in rows:
    listing_id, image_urls = row
    if image_urls and 'dialog-bg-img.png' in image_urls:
        count += 1
        print(f'房源 {listing_id} 包含 dialog-bg-img.png')
        
        # 解析並清理
        try:
            images = json.loads(image_urls)
            cleaned = [img for img in images if 'dialog-bg-img.png' not in img]
            print(f'  原有 {len(images)} 張, 清理後 {len(cleaned)} 張')
            
            # 更新資料庫
            c.execute('UPDATE house_listings SET image_urls = ? WHERE listing_id = ?',
                     (json.dumps(cleaned, ensure_ascii=False), listing_id))
        except:
            pass

conn.commit()
print(f'\n共清理 {count} 個房源的無效圖片')
conn.close()
