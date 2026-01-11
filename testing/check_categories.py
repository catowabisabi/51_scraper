"""列出所有分类及其帖子数量"""
import requests
import json

r = requests.get('https://www.51.ca/market/_next/data/xKpWRlbD9otyW4XsOSXBt/all.json')
d = r.json()
cats = d['pageProps']['categories']
locs = d['pageProps']['locations']
pagination = d['pageProps']['initData']['pagination']

print('=== Pagination Info ===')
print(json.dumps(pagination, indent=2))

print(f'\n=== {len(cats)} Categories ===')
for c in cats:
    print(f"  - {c['slug']}")

print(f'\n=== Locations with postCount ===')
total = 0
for loc in locs:
    if loc.get('postCount', 0) > 0:
        print(f"  {loc['titleZh']}: {loc['postCount']} posts")
        total += loc['postCount']
print(f'\nTotal posts across locations: {total}')
