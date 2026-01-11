"""測試 market API 分頁"""
import requests
import json
from bs4 import BeautifulSoup

build_id = 'xKpWRlbD9otyW4XsOSXBt'

# 測試不同的分頁參數
print("=== Test different pagination params ===")
params_to_try = [
    'page=1',
    'page=2',
    'offset=40',
    'skip=40', 
    'start=40',
    'limit=40&offset=40',
]

seen_first_ids = []
for param in params_to_try:
    url = f'https://www.51.ca/market/_next/data/{build_id}/all.json?{param}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            init = d.get('pageProps', {}).get('initData', {})
            items = init.get('data', [])
            first_id = items[0]['id'] if items else None
            pagination = init.get('pagination', {})
            is_new = first_id not in seen_first_ids
            seen_first_ids.append(first_id)
            marker = "✓ NEW" if is_new else "✗ SAME"
            print(f"{param}: first_id={first_id}, page={pagination.get('page')} {marker}")
    except Exception as e:
        print(f"{param}: ERROR - {e}")

# 測試直接瀏覽器查看第二頁的 URL
print("\n=== Test browser-style URLs ===")
test_urls = [
    'https://www.51.ca/market/all?page=2',
    'https://www.51.ca/market/?page=2',
    'https://www.51.ca/market/all/page/2',
]

for url in test_urls:
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'lxml')
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                d = json.loads(next_data.string)
                init = d.get('props', {}).get('pageProps', {}).get('initData', {})
                items = init.get('data', [])
                first_id = items[0]['id'] if items else None
                pagination = init.get('pagination', {})
                is_new = first_id not in seen_first_ids
                seen_first_ids.append(first_id)
                marker = "✓ NEW" if is_new else "✗ SAME"
                print(f"{url.split('51.ca')[1]}: first_id={first_id}, page={pagination.get('page')} {marker}")
    except Exception as e:
        print(f"ERROR: {e}")
