"""查看工作詳情頁數據結構"""

import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 訪問詳情頁
    page.goto("https://www.51.ca/jobs/job-posts/1174462", wait_until='networkidle')
    
    # 提取 __NEXT_DATA__
    next_data = page.evaluate('''() => {
        const el = document.getElementById('__NEXT_DATA__');
        return el ? JSON.parse(el.textContent) : null;
    }''')
    
    if next_data:
        page_props = next_data.get('props', {}).get('pageProps', {})
        data = page_props.get('data', {})
        
        print("pageProps keys:", list(page_props.keys()))
        print("\ndata keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        
        if isinstance(data, dict):
            # 保存完整數據
            with open('testing/job_detail_structure.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("\n已保存到 testing/job_detail_structure.json")
            
            # 顯示一些關鍵字段
            for key in ['id', 'title', 'location', 'locationName', 'category', 'categoryName', 
                       'name', 'phone', 'salary', 'content', 'createdAt']:
                if key in data:
                    value = data[key]
                    if isinstance(value, dict):
                        print(f"\n{key}: {json.dumps(value, ensure_ascii=False)}")
                    else:
                        print(f"\n{key}: {value}")
    
    browser.close()
