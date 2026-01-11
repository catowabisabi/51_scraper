"""
51.ca 工作爬蟲 Playwright 測試
探索 API 和電話解密
"""

import json
import time
import re
from playwright.sync_api import sync_playwright


def test_jobs_scraper():
    """測試工作頁面，尋找 API 和電話"""
    
    api_responses = []
    
    def handle_response(response):
        """攔截網絡響應"""
        url = response.url
        # 捕獲可能的 API 請求
        if '/api/' in url or '/_next/data/' in url:
            try:
                if response.status == 200 and 'json' in response.headers.get('content-type', ''):
                    data = response.json()
                    api_responses.append({
                        'url': url,
                        'method': response.request.method,
                        'data_keys': list(data.keys()) if isinstance(data, dict) else 'array',
                        'data': data
                    })
                    print(f"[API] {response.request.method} {url[:80]}...")
            except:
                pass
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})
        
        # 攔截響應
        page.on("response", handle_response)
        
        # 訪問工作列表頁
        print("\n=== 訪問工作列表頁 ===")
        page.goto("https://www.51.ca/jobs/job-posts?page=1", wait_until='networkidle')
        time.sleep(2)
        
        # 提取 __NEXT_DATA__
        print("\n=== 提取 __NEXT_DATA__ ===")
        next_data = page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? JSON.parse(el.textContent) : null;
        }''')
        
        if next_data:
            build_id = next_data.get('buildId')
            print(f"Build ID: {build_id}")
            
            # 查看數據結構
            page_props = next_data.get('props', {}).get('pageProps', {})
            print(f"pageProps keys: {list(page_props.keys())}")
            
            # 找工作數據
            for key, value in page_props.items():
                if isinstance(value, dict) and 'data' in value:
                    print(f"\n{key} 包含 data:")
                    data = value.get('data', [])
                    if isinstance(data, list) and len(data) > 0:
                        print(f"  - 共 {len(data)} 條記錄")
                        if len(data) > 0:
                            print(f"  - 第一條 keys: {list(data[0].keys())}")
                            # 保存示例
                            with open('testing/job_sample.json', 'w', encoding='utf-8') as f:
                                json.dump(data[:3], f, ensure_ascii=False, indent=2)
                            print(f"  - 已保存前3條到 testing/job_sample.json")
                elif isinstance(value, list) and len(value) > 0:
                    print(f"\n{key} 是列表, 共 {len(value)} 條")
        
        # 滾動看看有沒有無限滾動
        print("\n=== 測試滾動加載 ===")
        initial_api_count = len(api_responses)
        
        for i in range(3):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1.5)
            page.wait_for_load_state('networkidle', timeout=5000)
            print(f"滾動 #{i+1}, API 響應數: {len(api_responses)}")
        
        if len(api_responses) > initial_api_count:
            print("檢測到滾動觸發的 API 請求!")
        
        # 點擊"加載更多"按鈕
        print("\n=== 尋找加載更多按鈕 ===")
        load_more = page.locator('button:has-text("加载更多"), button:has-text("載入更多"), a:has-text("加载更多")')
        if load_more.count() > 0:
            print(f"找到加載更多按鈕: {load_more.count()}")
            load_more.first.click()
            time.sleep(2)
            page.wait_for_load_state('networkidle')
            print(f"點擊後 API 響應數: {len(api_responses)}")
        else:
            print("沒有找到加載更多按鈕")
        
        # 收集職位列表
        print("\n=== 收集職位卡片 ===")
        job_cards = page.locator('a[href*="/jobs/job-posts/"]')
        job_count = job_cards.count()
        print(f"找到 {job_count} 個職位連結")
        
        # 獲取前10個職位 URL
        job_urls = []
        for i in range(min(10, job_count)):
            href = job_cards.nth(i).get_attribute('href')
            if href and '/jobs/job-posts/' in href and 'create' not in href:
                full_url = f"https://www.51.ca{href}" if href.startswith('/') else href
                if full_url not in job_urls:
                    job_urls.append(full_url)
        
        print(f"收集到 {len(job_urls)} 個職位 URL")
        for url in job_urls[:5]:
            print(f"  - {url}")
        
        # 訪問詳情頁測試電話
        print("\n=== 測試職位詳情頁電話 ===")
        if job_urls:
            test_url = job_urls[0]
            print(f"訪問: {test_url}")
            page.goto(test_url, wait_until='networkidle')
            time.sleep(1)
            
            # 截圖看看
            page.screenshot(path='testing/job_detail.png')
            print("截圖已保存到 testing/job_detail.png")
            
            # 查看頁面內容
            page_text = page.inner_text('body')
            
            # 尋找電話相關按鈕
            print("\n尋找電話相關元素...")
            
            # 方法1: 查看电话/查看電話 按鈕
            phone_btn = page.locator('button:has-text("查看电话"), button:has-text("查看電話")')
            if phone_btn.count() > 0:
                print(f"找到查看電話按鈕: {phone_btn.count()}")
                phone_btn.first.click()
                time.sleep(1)
                
                # 確認彈窗
                confirm_btn = page.locator('button:has-text("知道了")')
                if confirm_btn.count() > 0:
                    print("找到確認按鈕，點擊...")
                    confirm_btn.first.click()
                    time.sleep(0.5)
                
                # 截圖
                page.screenshot(path='testing/job_detail_after_click.png')
                print("截圖已保存到 testing/job_detail_after_click.png")
                
                # 尋找電話號碼
                page_text = page.inner_text('body')
                phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                phones = re.findall(phone_pattern, page_text)
                if phones:
                    print(f"找到電話: {phones}")
            else:
                print("沒有找到查看電話按鈕")
            
            # 方法2: 直接顯示的電話
            tel_links = page.locator('a[href^="tel:"]')
            if tel_links.count() > 0:
                for i in range(tel_links.count()):
                    href = tel_links.nth(i).get_attribute('href')
                    print(f"找到 tel: 連結: {href}")
            
            # 方法3: 提取詳情頁 __NEXT_DATA__
            detail_data = page.evaluate('''() => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? JSON.parse(el.textContent) : null;
            }''')
            
            if detail_data:
                detail_props = detail_data.get('props', {}).get('pageProps', {})
                print(f"\n詳情頁 pageProps keys: {list(detail_props.keys())}")
                
                # 保存詳情數據
                with open('testing/job_detail_data.json', 'w', encoding='utf-8') as f:
                    json.dump(detail_props, f, ensure_ascii=False, indent=2)
                print("詳情數據已保存到 testing/job_detail_data.json")
                
                # 查看是否有電話字段
                data = detail_props.get('data', {})
                if isinstance(data, dict):
                    for key in data.keys():
                        if 'phone' in key.lower() or 'tel' in key.lower() or 'contact' in key.lower():
                            print(f"找到電話相關字段: {key} = {data[key]}")
        
        # 打印攔截到的 API
        print("\n=== 攔截到的 API 請求 ===")
        for api in api_responses:
            print(f"\n{api['method']} {api['url'][:100]}")
            print(f"  Keys: {api['data_keys']}")
        
        # 保存 API 數據
        if api_responses:
            with open('testing/jobs_api_responses.json', 'w', encoding='utf-8') as f:
                json.dump(api_responses, f, ensure_ascii=False, indent=2, default=str)
            print(f"\nAPI 響應已保存到 testing/jobs_api_responses.json")
        
        print("\n=== 測試完成 ===")
        input("按 Enter 關閉瀏覽器...")
        browser.close()


if __name__ == '__main__':
    test_jobs_scraper()
