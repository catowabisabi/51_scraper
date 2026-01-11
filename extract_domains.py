"""
提取經紀域名與ID的對應表
"""
import requests
import json
import time

# 獲取不同房源的經紀信息
domains = {}
listing_ids = []

print("正在獲取房源列表...")

# 先獲取一批房源ID (買賣+出租)
for trans_type in [1, 2]:
    for page in range(1, 6):
        url = f'https://house.51.ca/api/v7/property?limit=50&page={page}&transactionType={trans_type}&province=ontario'
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        for prop in data.get('data', []):
            listing_ids.append(prop['listingId'])
        time.sleep(0.2)

print(f'獲取了 {len(listing_ids)} 個房源ID')
print("正在提取經紀域名...")

# 抓取前100個的詳情，提取域名映射
for i, lid in enumerate(listing_ids[:100]):
    url = f'https://house.51.ca/api/v7/property/detail/{lid}'
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        data = response.json()
        detail = data.get('data', {})
        section13 = detail.get('section13', {})
        if section13:
            agent_id = section13.get('id')
            domain = section13.get('domain', '')
            name = section13.get('realName', '')
            if domain and agent_id:
                domains[domain] = {
                    'agent_id': agent_id,
                    'name': name
                }
    
    if (i + 1) % 10 == 0:
        print(f"  已處理 {i + 1} 個房源...")
    time.sleep(0.2)

print(f'\n{"="*70}')
print(f'發現 {len(domains)} 個不同的經紀域名:')
print(f'{"="*70}')
print(f'{"Agent ID":>8} | {"Name":<25} | Domain')
print(f'{"-"*70}')

for domain, info in sorted(domains.items(), key=lambda x: x[1]['agent_id']):
    print(f"{info['agent_id']:>8} | {info['name']:<25} | {domain}")

print(f'{"="*70}')

# 保存為JSON
with open('agent_domains.json', 'w', encoding='utf-8') as f:
    json.dump(domains, f, ensure_ascii=False, indent=2)
print("\n已保存到 agent_domains.json")
