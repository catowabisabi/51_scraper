"""
分析商家資料完整性
"""
import sqlite3

DB_PATH = '../data/51ca.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print('=== 商家資料完整性分析 ===')

c.execute('SELECT COUNT(*) FROM service_merchants')
total = c.fetchone()[0]
print(f'總商家數: {total}')

# 各欄位填充率
fields = [
    ('name', '名稱'),
    ('english_name', '英文名'),
    ('description', '描述'),
    ('phone', '電話'),
    ('address', '地址'),
    ('website', '網站/郵箱'),
    ('logo_url', 'Logo'),
    ('image_urls', '圖片'),
    ('category', '分類'),
]

print('\n欄位填充率:')
for field, label in fields:
    c.execute(f"SELECT COUNT(*) FROM service_merchants WHERE {field} IS NOT NULL AND {field} != ''")
    count = c.fetchone()[0]
    pct = count * 100 // total if total else 0
    status = '✓' if pct >= 70 else '⚠' if pct >= 30 else '✗'
    print(f'  {status} {label}: {count}/{total} ({pct}%)')

# 顯示幾個商家的詳細資料
print('\n=== 商家樣本 ===')
c.execute('SELECT merchant_id, name, phone, address, description FROM service_merchants LIMIT 5')
for row in c.fetchall():
    mid, name, phone, addr, desc = row
    print(f'\n商家 {mid}: {name}')
    print(f'  電話: {phone or "無"}')
    print(f'  地址: {addr or "無"}')
    if desc:
        # 只顯示描述的前100字
        print(f'  描述: {desc[:100]}...')
    else:
        print(f'  描述: 無')

# 檢查描述欄位是否包含「最新動態」(表示抓取不精準)
print('\n=== 描述質量檢查 ===')
c.execute("SELECT COUNT(*) FROM service_merchants WHERE description LIKE '%最新动态%'")
bad_desc = c.fetchone()[0]
print(f'描述含「最新動態」(抓取不精準): {bad_desc}/{total}')

c.execute("SELECT COUNT(*) FROM service_merchants WHERE description LIKE '%公司介绍%'")
bad_desc2 = c.fetchone()[0]
print(f'描述含「公司介紹」標題: {bad_desc2}/{total}')

conn.close()
