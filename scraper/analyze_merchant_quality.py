"""分析商家數據質量"""
import sqlite3

conn = sqlite3.connect('../data/51ca.db')
c = conn.cursor()

print('=== 商家數據質量分析 ===')

# 各欄位填充率
fields = ['name', 'english_name', 'description', 'phone', 'address', 'logo_url', 'image_urls', 'category']
c.execute('SELECT COUNT(*) FROM service_merchants')
total = c.fetchone()[0]
print(f'總商家數: {total}')
print()

for field in fields:
    c.execute(f"SELECT COUNT(*) FROM service_merchants WHERE {field} IS NOT NULL AND {field} != ''")
    count = c.fetchone()[0]
    pct = count * 100 // total if total else 0
    print(f'  {field}: {count}/{total} ({pct}%)')

# 檢查 phone 欄位實際值
print('\n=== 電話樣本 ===')
c.execute('SELECT merchant_id, name, phone FROM service_merchants WHERE phone IS NOT NULL LIMIT 5')
for row in c.fetchall():
    name = row[1][:25] if row[1] else 'N/A'
    print(f'  {name}: {row[2]}')

# 檢查 address 欄位
print('\n=== 地址樣本 ===')
c.execute("SELECT merchant_id, name, address FROM service_merchants WHERE address IS NOT NULL AND address != '' LIMIT 5")
for row in c.fetchall():
    name = row[1][:20] if row[1] else 'N/A'
    addr = row[2][:80] if row[2] else 'N/A'
    print(f'  {name}: {addr}')

# 檢查 description
print('\n=== 描述樣本 ===')
c.execute("SELECT merchant_id, name, description FROM service_merchants WHERE description IS NOT NULL AND description != '' LIMIT 3")
for row in c.fetchall():
    name = row[1][:20] if row[1] else 'N/A'
    desc = row[2][:100] if row[2] else 'N/A'
    print(f'  {name}: {desc}...')

conn.close()
