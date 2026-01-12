"""測試 API"""
import requests
import json

# 測試房屋 API
r = requests.get('https://house.51.ca/api/v7/property', 
    params={'limit': 5, 'page': 1, 'transactionType': 1, 'province': 'ontario'}, 
    timeout=30)
data = r.json()
print('Status:', data.get('status'))
props = data.get('data', [])
print('Count this page:', len(props))
print('Total available:', data.get('total'))
print('Pagination:', data.get('pagination'))

print('\nSample property (first one):')
if props:
    print(json.dumps(props[0], indent=2, ensure_ascii=False)[:1000])
