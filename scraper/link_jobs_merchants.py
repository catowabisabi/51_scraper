"""
為工作表添加商家關聯
1. 添加 merchant_id 欄位
2. 根據 company_url 提取 merchant_id 並更新
"""
import sqlite3
import re

conn = sqlite3.connect('../data/51ca.db')
c = conn.cursor()

# 1. 檢查是否已有 merchant_id 欄位
c.execute('PRAGMA table_info(job_listings)')
columns = [col[1] for col in c.fetchall()]

if 'merchant_id' not in columns:
    print('添加 merchant_id 欄位到 job_listings...')
    c.execute('ALTER TABLE job_listings ADD COLUMN merchant_id TEXT')
    conn.commit()
    print('✅ 欄位添加成功')
else:
    print('merchant_id 欄位已存在')

# 2. 從 company_url 提取 merchant_id 並更新
print('\n更新工作的商家關聯...')
c.execute('SELECT id, company_url FROM job_listings WHERE company_url IS NOT NULL')
rows = c.fetchall()

updated = 0
for row in rows:
    job_id, company_url = row
    if company_url:
        # 提取 merchant_id: https://merchant.51.ca/merchants/1234
        match = re.search(r'/merchants/(\d+)', company_url)
        if match:
            merchant_id = match.group(1)
            c.execute('UPDATE job_listings SET merchant_id = ? WHERE id = ?', (merchant_id, job_id))
            updated += 1

conn.commit()
print(f'✅ 更新了 {updated} 個工作的商家關聯')

# 3. 檢查結果
print('\n=== 關聯結果 ===')
c.execute('''
    SELECT j.job_id, j.company_name, j.merchant_id, m.name as merchant_name
    FROM job_listings j
    LEFT JOIN service_merchants m ON j.merchant_id = m.merchant_id
    LIMIT 10
''')
for row in c.fetchall():
    print(f'  工作 {row[0]}: merchant_id={row[2]} -> 商家: {row[3]}')

# 統計
c.execute('SELECT COUNT(*) FROM job_listings WHERE merchant_id IS NOT NULL')
with_merchant = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM job_listings')
total = c.fetchone()[0]
print(f'\n共 {with_merchant}/{total} 個工作已關聯商家')

# 缺少的商家
c.execute('''
    SELECT DISTINCT j.merchant_id 
    FROM job_listings j
    LEFT JOIN service_merchants m ON j.merchant_id = m.merchant_id
    WHERE j.merchant_id IS NOT NULL AND m.merchant_id IS NULL
''')
missing = c.fetchall()
if missing:
    print(f'\n⚠️ 有 {len(missing)} 個商家尚未爬取:')
    for m in missing[:10]:
        print(f'  商家 ID: {m[0]}')

conn.close()
