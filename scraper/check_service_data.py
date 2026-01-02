"""
黃頁/服務數據完整性檢查
分析 service_posts 和 service_merchants 表的數據質量
"""
import sqlite3
import json

DB_PATH = '../data/51ca.db'

def analyze_table(c, table_name: str):
    """分析表的欄位填充率"""
    print(f'\n=== {table_name} 表分析 ===')
    
    # 獲取表結構
    c.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in c.fetchall()]
    
    # 總數
    c.execute(f'SELECT COUNT(*) FROM {table_name}')
    total = c.fetchone()[0]
    print(f'總記錄數: {total}')
    
    if total == 0:
        return
    
    print('\n欄位填充率:')
    for col in columns:
        c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NOT NULL AND {col} != ''")
        count = c.fetchone()[0]
        pct = count * 100 // total
        status = '✓' if pct >= 70 else '⚠' if pct >= 30 else '✗'
        print(f'  {status} {col}: {count}/{total} ({pct}%)')

def show_samples(c, table_name: str, field: str, limit: int = 3):
    """顯示欄位樣本"""
    print(f'\n{field} 樣本:')
    c.execute(f"SELECT {field} FROM {table_name} WHERE {field} IS NOT NULL AND {field} != '' LIMIT ?", (limit,))
    for row in c.fetchall():
        val = str(row[0])[:80] if row[0] else 'N/A'
        print(f'  - {val}')

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('=' * 60)
    print('黃頁/服務數據完整性報告')
    print('=' * 60)
    
    # 1. 分析 service_merchants
    analyze_table(c, 'service_merchants')
    show_samples(c, 'service_merchants', 'category')
    show_samples(c, 'service_merchants', 'address')
    
    # 2. 分析 service_posts
    analyze_table(c, 'service_posts')
    show_samples(c, 'service_posts', 'title')
    show_samples(c, 'service_posts', 'category')
    
    # 3. 檢查商家與帖子的關聯
    print('\n=== 數據關聯分析 ===')
    c.execute('''
        SELECT COUNT(DISTINCT sp.post_id) 
        FROM service_posts sp 
        LEFT JOIN service_merchants sm ON sp.merchant_id = sm.merchant_id
        WHERE sm.merchant_id IS NOT NULL
    ''')
    linked = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM service_posts')
    total_posts = c.fetchone()[0]
    print(f'帖子關聯到商家: {linked}/{total_posts}')
    
    # 4. 檢查工作與商家的關聯
    c.execute('''
        SELECT COUNT(*) FROM job_listings 
        WHERE merchant_id IS NOT NULL
    ''')
    jobs_linked = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM job_listings')
    total_jobs = c.fetchone()[0]
    print(f'工作關聯到商家: {jobs_linked}/{total_jobs}')
    
    # 5. 提出 schema 建議
    print('\n=== Schema 建議 ===')
    print('''
service_merchants 表穩定欄位:
  - merchant_id (PRIMARY KEY): 商家唯一ID
  - name: 中文名稱 (98%)
  - english_name: 英文名稱 (69%)
  - logo_url: Logo圖片 (96%)
  - description: 公司介紹 (68%)
  - phone: 聯繫電話 (76%)
  - address: 地址 (78%)
  - image_urls: 環境圖片JSON (78%)
  - category: 分類 (需改進提取)
  - website: 網站/郵箱
  - review_count: 瀏覽數

建議新增欄位:
  - contact_name: 聯繫人姓名
  - email: 電子郵箱 (從 website 分離)
  - business_hours: 營業時間
  - is_verified: 是否認證商家 (VIP標記)
''')
    
    conn.close()
    print('\n分析完成!')

if __name__ == '__main__':
    main()
