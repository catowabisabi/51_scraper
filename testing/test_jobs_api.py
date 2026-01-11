"""
51.ca 工作 API 測試
尋找工作列表 API 端點
"""

import json
import time
import re
from playwright.sync_api import sync_playwright


def test_jobs_api():
    """測試工作列表 API"""
    
    api_responses = []
    
    def handle_response(response):
        """攔截網絡響應"""
        url = response.url
        if '/api/' in url or '/_next/data/' in url:
            try:
                if response.status == 200 and 'json' in response.headers.get('content-type', ''):
                    data = response.json()
                    api_responses.append({
                        'url': url,
                        'method': response.request.method,
                        'data': data
                    })
                    
                    # 檢查是否是工作列表 API
                    if isinstance(data, dict):
                        data_list = data.get('data', [])
                        if isinstance(data_list, list) and len(data_list) > 0:
                            first_item = data_list[0]
                            if isinstance(first_item, dict):
                                if 'title' in first_item and ('salary' in first_item or 'location' in first_item or 'categoryName' in first_item):
                                    print(f"\n*** 找到可能的工作列表 API! ***")
                                    print(f"URL: {url}")
                                    print(f"共 {len(data_list)} 條記錄")
                                    print(f"字段: {list(first_item.keys())}")
            except Exception as e:
                pass
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})
        
        page.on("response", handle_response)
        
        # 測試不同的 API 端點
        print("=== 測試可能的 API 端點 ===")
        
        # 嘗試直接調用 API
        test_apis = [
            "https://www.51.ca/jobs/api/job-posts",
            "https://www.51.ca/jobs/api/job-posts?page=1",
            "https://www.51.ca/jobs/api/job-posts?page=1&perPage=20",
            "https://www.51.ca/jobs/api/posts",
            "https://www.51.ca/jobs/api/jobs",
            "https://www.51.ca/jobs/web/api/job-posts",
            "https://www.51.ca/jobs/web/api/posts",
        ]
        
        for api_url in test_apis:
            try:
                resp = page.request.get(api_url)
                print(f"\n{api_url}")
                print(f"  Status: {resp.status}")
                if resp.status == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, dict):
                            print(f"  Keys: {list(data.keys())}")
                            if 'data' in data and isinstance(data['data'], list):
                                print(f"  Data count: {len(data['data'])}")
                                if len(data['data']) > 0:
                                    print(f"  First item keys: {list(data['data'][0].keys())}")
                                    # 保存
                                    with open('testing/jobs_api_test.json', 'w', encoding='utf-8') as f:
                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                    print("  已保存到 testing/jobs_api_test.json")
                    except:
                        print(f"  Not JSON")
            except Exception as e:
                print(f"  Error: {e}")
        
        # 訪問頁面並點擊加載更多，看有什麼 API 被觸發
        print("\n\n=== 訪問頁面並觀察 API ===")
        page.goto("https://www.51.ca/jobs/job-posts", wait_until='networkidle')
        time.sleep(2)
        
        # 提取 __NEXT_DATA__
        next_data = page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? JSON.parse(el.textContent) : null;
        }''')
        
        if next_data:
            build_id = next_data.get('buildId')
            print(f"Build ID: {build_id}")
            
            # 嘗試用 _next/data API
            if build_id:
                next_api_urls = [
                    f"https://www.51.ca/jobs/_next/data/{build_id}/job-posts.json",
                    f"https://www.51.ca/jobs/_next/data/{build_id}/job-posts.json?page=2",
                    f"https://www.51.ca/jobs/_next/data/{build_id}/job-posts.json?page=1&perPage=20",
                ]
                
                print("\n=== 測試 _next/data API ===")
                for api_url in next_api_urls:
                    try:
                        resp = page.request.get(api_url)
                        print(f"\n{api_url}")
                        print(f"  Status: {resp.status}")
                        if resp.status == 200:
                            try:
                                data = resp.json()
                                if isinstance(data, dict):
                                    print(f"  Keys: {list(data.keys())}")
                                    page_props = data.get('pageProps', {})
                                    print(f"  pageProps keys: {list(page_props.keys())}")
                                    
                                    # 查找 data
                                    for key, value in page_props.items():
                                        if isinstance(value, dict) and 'data' in value:
                                            items = value.get('data', [])
                                            if isinstance(items, list):
                                                print(f"  {key}.data: {len(items)} 條")
                                                if len(items) > 0:
                                                    print(f"  First item keys: {list(items[0].keys())}")
                                                    # 保存
                                                    with open(f'testing/jobs_next_data.json', 'w', encoding='utf-8') as f:
                                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                                    print(f"  已保存到 testing/jobs_next_data.json")
                            except:
                                print(f"  Not JSON")
                    except Exception as e:
                        print(f"  Error: {e}")
        
        # 點擊加載更多
        print("\n\n=== 點擊加載更多 ===")
        before_count = len(api_responses)
        
        load_more = page.locator('button:has-text("加载更多")')
        if load_more.count() > 0:
            print("點擊加載更多...")
            load_more.first.click()
            time.sleep(2)
            page.wait_for_load_state('networkidle')
            
            new_apis = api_responses[before_count:]
            print(f"新增 {len(new_apis)} 個 API 響應")
            
            for api in new_apis:
                url = api['url']
                if 'job' in url.lower():
                    print(f"\n工作相關 API: {url[:100]}")
                    data = api['data']
                    if isinstance(data, dict):
                        print(f"  Keys: {list(data.keys())}")
                        if 'data' in data and isinstance(data['data'], list):
                            print(f"  Data count: {len(data['data'])}")
        
        # 嘗試分頁 URL
        print("\n\n=== 測試分頁 URL ===")
        page.goto("https://www.51.ca/jobs/job-posts?page=2", wait_until='networkidle')
        time.sleep(2)
        
        # 檢查 URL 是否改變
        current_url = page.url
        print(f"當前 URL: {current_url}")
        
        # 提取數據
        next_data2 = page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? JSON.parse(el.textContent) : null;
        }''')
        
        if next_data2:
            page_props = next_data2.get('props', {}).get('pageProps', {})
            for key, value in page_props.items():
                if isinstance(value, dict) and 'data' in value:
                    items = value.get('data', [])
                    if isinstance(items, list):
                        print(f"第2頁 {key}.data: {len(items)} 條")
                        if len(items) > 0:
                            first_id = items[0].get('id')
                            print(f"第一條 ID: {first_id}")
                        
                        # 保存
                        with open('testing/jobs_page2_data.json', 'w', encoding='utf-8') as f:
                            json.dump(next_data2, f, ensure_ascii=False, indent=2)
                        print("已保存到 testing/jobs_page2_data.json")
        
        print("\n=== 測試完成 ===")
        input("按 Enter 關閉瀏覽器...")
        browser.close()


if __name__ == '__main__':
    test_jobs_api()
