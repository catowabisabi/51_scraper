"""
清理並修復汽車圖片 - 移除無效的 UI 圖片
"""
import sqlite3
import json
import re
from urllib.parse import urlparse

DB_PATH = '../data/51ca.db'

def is_valid_car_image(url: str) -> bool:
    """檢查是否為有效的汽車圖片"""
    if not url:
        return False
    
    # 排除的關鍵字
    exclude_keywords = [
        'logo', 'icon', 'avatar', 'button', 'ad', 'static-maps', 
        'placeholder', 'loading', 'assets/images', 'common/', 
        'detail/', 'radio_', 'checkbox', 'carfax', 'bell.png',
        'test-driv', 'empty', 'search', '.svg'
    ]
    
    url_lower = url.lower()
    if any(x in url_lower for x in exclude_keywords):
        return False
    
    # 必須來自 storage.51yun.ca
    domain = urlparse(url).netloc
    if 'storage.51yun.ca' not in domain:
        return False
    
    # 排除經銷商 logo 和銷售員頭像
    if 'dealer-logo' in url or 'salesperson' in url:
        return False
    
    return True

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('=== 清理汽車圖片 ===')
    
    c.execute('SELECT listing_id, title, image_urls FROM auto_listings')
    rows = c.fetchall()
    
    print(f'總汽車列表: {len(rows)}')
    
    cleaned_count = 0
    total_removed = 0
    
    for listing_id, title, image_urls_json in rows:
        if not image_urls_json:
            continue
        
        try:
            images = json.loads(image_urls_json)
        except json.JSONDecodeError:
            continue
        
        if not images:
            continue
        
        # 過濾有效圖片
        valid_images = [img for img in images if is_valid_car_image(img)]
        
        removed = len(images) - len(valid_images)
        if removed > 0:
            total_removed += removed
            cleaned_count += 1
            
            # 更新數據庫
            new_json = json.dumps(valid_images, ensure_ascii=False) if valid_images else None
            c.execute('UPDATE auto_listings SET image_urls = ? WHERE listing_id = ?', 
                     (new_json, listing_id))
    
    conn.commit()
    
    print(f'已清理 {cleaned_count} 條記錄')
    print(f'移除無效圖片: {total_removed} 張')
    
    # 顯示結果
    print('\n=== 清理後統計 ===')
    c.execute("SELECT COUNT(*) FROM auto_listings WHERE image_urls IS NOT NULL AND image_urls != '[]'")
    with_images = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM auto_listings')
    total = c.fetchone()[0]
    print(f'有圖片的記錄: {with_images}/{total}')
    
    # 顯示樣本
    print('\n保留的圖片樣本:')
    c.execute("SELECT title, image_urls FROM auto_listings WHERE image_urls IS NOT NULL AND image_urls != '[]' LIMIT 3")
    for row in c.fetchall():
        title = row[0][:30] if row[0] else 'N/A'
        images = json.loads(row[1]) if row[1] else []
        print(f'  {title}: {len(images)} 張')
        for img in images[:2]:
            print(f'    - {img[:60]}...')
    
    conn.close()
    print('\n清理完成!')

if __name__ == '__main__':
    main()
