"""測試 market API"""
import requests
from bs4 import BeautifulSoup
import json

def get_build_id():
    """獲取 Next.js buildId"""
    r = requests.get('https://www.51.ca/market/', timeout=10)
    soup = BeautifulSoup(r.text, 'lxml')
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        data = json.loads(next_data.string)
        return data.get('buildId', '')
    return None

def test_pagination():
    """測試分頁"""
    build_id = get_build_id()
    print(f"Build ID: {build_id}")
    
    seen_ids = set()
    for page in [1, 2, 3]:
        url = f"https://www.51.ca/market/_next/data/{build_id}/all.json?page={page}"
        r = requests.get(url, timeout=10)
        d = r.json()
        init = d['pageProps']['initData']
        pagination = init['pagination']
        items = init['data']
        first_id = items[0]['id'] if items else None
        
        # 檢查是否有重複
        new_ids = [item['id'] for item in items]
        duplicates = set(new_ids) & seen_ids
        seen_ids.update(new_ids)
        
        print(f"Page {page}: API page={pagination['page']}, first_id={first_id}, items={len(items)}, dups={len(duplicates)}")

def test_category():
    """測試分類 API"""
    build_id = get_build_id()
    
    categories = ['furniture', 'electronics', 'home-appliance']
    for cat in categories:
        url = f"https://www.51.ca/market/_next/data/{build_id}/{cat}.json?page=1"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            init = d['pageProps']['initData']
            pagination = init['pagination']
            print(f"Category {cat}: total={pagination['total']}, pages={pagination['lastPage']}")

def test_detail():
    """測試商品詳情"""
    build_id = get_build_id()
    
    # 獲取一個商品 ID
    url = f"https://www.51.ca/market/_next/data/{build_id}/all.json?page=1"
    r = requests.get(url, timeout=10)
    d = r.json()
    items = d['pageProps']['initData']['data']
    
    # 找一個 market 來源的商品
    for item in items:
        if item.get('source') == 'market':
            item_id = item['id']
            cat = item['categorySlug']
            print(f"\nTesting detail for ID {item_id} (category: {cat})")
            
            # 嘗試詳情頁 API
            detail_url = f"https://www.51.ca/market/_next/data/{build_id}/{cat}/{item_id}.json"
            print(f"URL: {detail_url}")
            r2 = requests.get(detail_url, timeout=10)
            print(f"Status: {r2.status_code}")
            if r2.status_code == 200 and 'json' in r2.headers.get('Content-Type', ''):
                d2 = r2.json()
                pp = d2.get('pageProps', {})
                print(f"pageProps keys: {list(pp.keys())}")
                if 'data' in pp:
                    detail = pp['data']
                    print(f"Detail keys: {list(detail.keys())}")
                    # 看看有沒有更多欄位
                    extra_keys = set(detail.keys()) - set(item.keys())
                    print(f"Extra keys in detail: {extra_keys}")
            break

if __name__ == '__main__':
    print("=== Testing Pagination ===")
    test_pagination()
    
    print("\n=== Testing Categories ===")
    test_category()
    
    print("\n=== Testing Detail ===")
    test_detail()
