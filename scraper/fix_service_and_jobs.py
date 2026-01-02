"""
清理服務帖子的 default-img.jpg
並檢查工作-商家關聯問題
"""
import sqlite3
import json

DB_PATH = '../data/51ca.db'

def clean_service_images():
    """移除 default-img.jpg"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('=== 清理服務帖子圖片 ===')
    
    c.execute("SELECT post_id, image_urls FROM service_posts WHERE image_urls LIKE '%default-img%'")
    rows = c.fetchall()
    print(f'含 default-img 的帖子: {len(rows)}')
    
    cleaned = 0
    for post_id, image_urls_json in rows:
        images = json.loads(image_urls_json) if image_urls_json else []
        # 過濾掉 default-img
        valid_images = [img for img in images if 'default-img' not in img]
        
        removed = len(images) - len(valid_images)
        if removed > 0:
            new_json = json.dumps(valid_images, ensure_ascii=False) if valid_images else None
            c.execute('UPDATE service_posts SET image_urls = ? WHERE post_id = ?', (new_json, post_id))
            cleaned += 1
    
    conn.commit()
    print(f'已清理 {cleaned} 條記錄')
    
    conn.close()

def check_job_merchant_links():
    """檢查工作-商家關聯"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('\n=== 工作-商家關聯檢查 ===')
    
    # 獲取所有工作的 merchant_id
    c.execute('SELECT job_id, title, merchant_id, company_name, company_url FROM job_listings')
    jobs = c.fetchall()
    
    print(f'總工作數: {len(jobs)}')
    
    # 檢查每個 merchant_id 是否存在於 service_merchants
    missing_merchants = []
    linked = 0
    no_id = 0
    
    for job_id, title, merchant_id, company_name, company_url in jobs:
        if not merchant_id:
            no_id += 1
            print(f'  ⚠ 無 merchant_id: {title[:30]} ({company_name})')
            continue
        
        c.execute('SELECT merchant_id, name FROM service_merchants WHERE merchant_id = ?', (merchant_id,))
        merchant = c.fetchone()
        
        if merchant:
            linked += 1
        else:
            missing_merchants.append((merchant_id, title, company_name, company_url))
    
    print(f'\n已關聯: {linked}')
    print(f'無 merchant_id: {no_id}')
    print(f'merchant_id 不在資料庫: {len(missing_merchants)}')
    
    if missing_merchants:
        print('\n=== 缺失的商家 ===')
        for mid, title, name, url in missing_merchants:
            print(f'  merchant_id={mid}: {name} ({title[:30]})')
            print(f'    URL: {url}')
    
    conn.close()
    return missing_merchants

if __name__ == '__main__':
    clean_service_images()
    missing = check_job_merchant_links()
