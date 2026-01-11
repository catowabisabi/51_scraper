"""
51.ca 工作 API 深入測試
"""

import json
import requests
from playwright.sync_api import sync_playwright


def test_api_with_requests():
    """用 requests 測試 API"""
    print("=== 用 Requests 測試 API ===\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.51.ca/jobs/job-posts',
    }
    
    # 測試不同參數
    test_urls = [
        "https://www.51.ca/jobs/api/job-posts",
        "https://www.51.ca/jobs/api/job-posts?page=1",
        "https://www.51.ca/jobs/api/job-posts?perPage=20",
        "https://www.51.ca/jobs/api/job-posts?page=1&perPage=20",
    ]
    
    for url in test_urls:
        print(f"\nGET {url}")
        resp = requests.get(url, headers=headers)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"  Keys: {list(data.keys())}")
                print(f"  Pagination: {data.get('pagination')}")
                items = data.get('data', [])
                print(f"  Data count: {len(items)}")
                if items and len(items) > 0:
                    print(f"  First item: {items[0]}")
            except:
                print(f"  Not JSON: {resp.text[:200]}")
    
    # 嘗試 POST
    print("\n\n=== 測試 POST ===")
    post_urls = [
        "https://www.51.ca/jobs/api/job-posts",
        "https://www.51.ca/jobs/web/api/job-posts",
    ]
    
    for url in post_urls:
        print(f"\nPOST {url}")
        try:
            resp = requests.post(url, headers=headers, json={})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Keys: {list(data.keys())}")
        except Exception as e:
            print(f"  Error: {e}")


def test_with_playwright():
    """用 Playwright 測試，獲取完整數據"""
    print("\n\n=== 用 Playwright 測試 ===\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 先訪問頁面獲取數據結構
        page.goto("https://www.51.ca/jobs/job-posts?page=1", wait_until='networkidle')
        
        # 提取 __NEXT_DATA__
        next_data = page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? JSON.parse(el.textContent) : null;
        }''')
        
        if next_data:
            build_id = next_data.get('buildId')
            print(f"Build ID: {build_id}")
            
            page_props = next_data.get('props', {}).get('pageProps', {})
            print(f"pageProps keys: {list(page_props.keys())}")
            
            # 詳細查看每個 key
            for key, value in page_props.items():
                if isinstance(value, dict):
                    print(f"\n{key}: {list(value.keys())}")
                    if 'data' in value:
                        items = value.get('data', [])
                        if isinstance(items, list):
                            print(f"  data: {len(items)} 條")
                            if len(items) > 0 and isinstance(items[0], dict):
                                print(f"  第一條 keys: {list(items[0].keys())}")
                                # 保存完整數據
                                with open('testing/jobs_full_data.json', 'w', encoding='utf-8') as f:
                                    json.dump(items[:5], f, ensure_ascii=False, indent=2)
                                print(f"  已保存前5條到 testing/jobs_full_data.json")
                    if 'pagination' in value:
                        print(f"  pagination: {value.get('pagination')}")
                elif isinstance(value, list):
                    print(f"\n{key}: 列表, {len(value)} 條")
            
            # 測試 page=2
            print("\n\n=== 測試第2頁 ===")
            page.goto("https://www.51.ca/jobs/job-posts?page=2", wait_until='networkidle')
            
            next_data2 = page.evaluate('''() => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? JSON.parse(el.textContent) : null;
            }''')
            
            if next_data2:
                page_props2 = next_data2.get('props', {}).get('pageProps', {})
                for key, value in page_props2.items():
                    if isinstance(value, dict) and 'data' in value:
                        items = value.get('data', [])
                        if isinstance(items, list) and len(items) > 0:
                            first_id = items[0].get('id')
                            print(f"{key}: {len(items)} 條, 第一條 ID: {first_id}")
        
        browser.close()


def test_pagination():
    """測試分頁是否有效"""
    print("\n\n=== 測試分頁 ===\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        first_ids = []
        
        for page_num in range(1, 4):
            url = f"https://www.51.ca/jobs/job-posts?page={page_num}"
            print(f"訪問: {url}")
            page.goto(url, wait_until='networkidle')
            
            next_data = page.evaluate('''() => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? JSON.parse(el.textContent) : null;
            }''')
            
            if next_data:
                page_props = next_data.get('props', {}).get('pageProps', {})
                for key, value in page_props.items():
                    if isinstance(value, dict) and 'data' in value:
                        items = value.get('data', [])
                        if isinstance(items, list) and len(items) > 0:
                            first_id = items[0].get('id')
                            first_title = items[0].get('title', '')[:30]
                            first_ids.append(first_id)
                            print(f"  第 {page_num} 頁: {len(items)} 條, 第一條: {first_id} - {first_title}")
                            
                            if 'pagination' in value:
                                pagination = value.get('pagination')
                                print(f"  Pagination: {pagination}")
        
        # 檢查分頁是否有效
        print(f"\n各頁第一條 ID: {first_ids}")
        if len(set(first_ids)) == len(first_ids):
            print("✓ 分頁有效! 每頁數據不同")
        else:
            print("✗ 分頁無效! 數據重複")
        
        browser.close()


if __name__ == '__main__':
    test_api_with_requests()
    test_with_playwright()
    test_pagination()
