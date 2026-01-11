"""查看工作詳情頁數據結構"""

import json
from playwright.sync_api import sync_playwright

print("Starting...")

with sync_playwright() as p:
    print("Launching browser...")
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Navigating to page...")
    page.goto("https://www.51.ca/jobs/job-posts/1174462", wait_until='networkidle')
    print("Page loaded")
    
    # 提取 __NEXT_DATA__
    next_data = page.evaluate('''() => {
        const el = document.getElementById('__NEXT_DATA__');
        return el ? JSON.parse(el.textContent) : null;
    }''')
    
    print(f"next_data exists: {next_data is not None}")
    
    if next_data:
        print(f"\nTop-level keys: {list(next_data.keys())}")
        
        props = next_data.get('props', {})
        print(f"props keys: {list(props.keys())}")
        
        page_props = props.get('pageProps', {})
        print(f"pageProps keys: {list(page_props.keys())}")
        
        # 深入查看
        for key, value in page_props.items():
            if isinstance(value, dict):
                print(f"\n{key} (dict): {list(value.keys())}")
            elif isinstance(value, list):
                print(f"\n{key} (list): {len(value)} items")
            else:
                print(f"\n{key}: {value}")
        
        # 保存完整數據
        with open('testing/job_next_data.json', 'w', encoding='utf-8') as f:
            json.dump(next_data, f, ensure_ascii=False, indent=2)
        print("\n已保存到 testing/job_next_data.json")
    
    browser.close()
    print("\nDone!")
