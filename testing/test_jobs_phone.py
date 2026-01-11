"""
51.ca 工作電話測試
測試 10 個工作的電話獲取
"""

import json
import re
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_job_ids(count=10):
    """從 API 獲取工作 ID 列表"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.51.ca/jobs/job-posts',
    }
    
    url = f"https://www.51.ca/jobs/api/job-posts?page=1&perPage={count}"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        return []
    
    data = resp.json()
    html_data = data.get('data', {})
    html_content = html_data.get('html', '') if isinstance(html_data, dict) else html_data
    
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'/job-posts/(\d+)'))
    
    jobs = []
    seen_ids = set()
    
    for link in links:
        match = re.search(r'/job-posts/(\d+)', link.get('href', ''))
        if match:
            job_id = match.group(1)
            if job_id not in seen_ids:
                seen_ids.add(job_id)
                title = link.get_text(strip=True)[:50]
                jobs.append({'id': job_id, 'title': title})
    
    return jobs[:count]


def test_phone_extraction():
    """測試電話提取"""
    print("=== 測試 Jobs 電話提取 ===\n")
    
    # 獲取工作列表
    jobs = get_job_ids(10)
    print(f"獲取到 {len(jobs)} 個工作\n")
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})
        
        for i, job in enumerate(jobs):
            job_id = job['id']
            title = job['title'][:30]
            
            print(f"\n[{i+1}/{len(jobs)}] ID: {job_id}")
            print(f"  標題: {title}")
            
            try:
                url = f"https://www.51.ca/jobs/job-posts/{job_id}"
                page.goto(url, wait_until='networkidle', timeout=15000)
                time.sleep(1)
                
                phone = None
                
                # 方法1: 直接找 tel: 連結
                tel_links = page.locator('a[href^="tel:"]')
                if tel_links.count() > 0:
                    href = tel_links.first.get_attribute('href')
                    phone = href.replace('tel:', '')
                    print(f"  ✓ 直接找到 tel: 連結: {phone}")
                
                # 方法2: 點擊查看電話按鈕
                if not phone:
                    phone_btn = page.locator('button:has-text("查看电话"), button:has-text("查看電話")')
                    if phone_btn.count() > 0:
                        print(f"  點擊查看電話按鈕...")
                        phone_btn.first.click()
                        time.sleep(1)
                        
                        # 檢查是否有確認彈窗
                        confirm_btn = page.locator('button:has-text("知道了")')
                        if confirm_btn.count() > 0:
                            confirm_btn.first.click()
                            time.sleep(0.5)
                        
                        # 再次找 tel: 連結
                        tel_links = page.locator('a[href^="tel:"]')
                        if tel_links.count() > 0:
                            href = tel_links.first.get_attribute('href')
                            phone = href.replace('tel:', '')
                            print(f"  ✓ 點擊後找到: {phone}")
                        else:
                            # 從頁面文本找
                            page_text = page.inner_text('body')
                            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                            matches = re.findall(phone_pattern, page_text)
                            if matches:
                                phone = matches[0]
                                print(f"  ✓ 從文本找到: {phone}")
                    else:
                        print(f"  ✗ 沒有查看電話按鈕")
                
                # 方法3: 從 __NEXT_DATA__ 提取
                if not phone:
                    next_data = page.evaluate('''() => {
                        const el = document.getElementById('__NEXT_DATA__');
                        return el ? JSON.parse(el.textContent) : null;
                    }''')
                    
                    if next_data:
                        page_props = next_data.get('props', {}).get('pageProps', {})
                        data = page_props.get('data', {})
                        
                        # 檢查電話字段
                        for key in ['phone', 'tel', 'contactPhone', 'contact_phone', 'mobile']:
                            if key in data:
                                phone = data[key]
                                print(f"  ✓ 從數據找到 {key}: {phone}")
                                break
                
                if not phone:
                    print(f"  ✗ 未找到電話")
                
                results.append({
                    'id': job_id,
                    'title': title,
                    'phone': phone,
                    'success': bool(phone)
                })
                
            except Exception as e:
                print(f"  ✗ 錯誤: {e}")
                results.append({
                    'id': job_id,
                    'title': title,
                    'phone': None,
                    'success': False,
                    'error': str(e)
                })
            
            time.sleep(0.5)
        
        browser.close()
    
    # 統計
    success_count = sum(1 for r in results if r['success'])
    print(f"\n\n=== 結果統計 ===")
    print(f"成功獲取電話: {success_count}/{len(results)} ({success_count*100//len(results)}%)")
    
    print("\n電話列表:")
    for r in results:
        status = '✓' if r['success'] else '✗'
        phone = r['phone'] or 'N/A'
        print(f"  {status} {r['id']}: {phone}")
    
    # 保存結果
    with open('testing/jobs_phone_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 testing/jobs_phone_test_results.json")


if __name__ == '__main__':
    test_phone_extraction()
