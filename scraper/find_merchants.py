"""查找商家列表"""
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 首頁會顯示一些商家
    url = 'https://merchant.51.ca/'
    print(f'訪問: {url}')
    page.goto(url, timeout=30000)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # 找所有連結到商家頁面的連結
    links = page.query_selector_all('a[href*="/merchants/"]')
    merchant_ids = set()
    for link in links:
        href = link.get_attribute('href')
        if href and '/merchants/' in href:
            match = re.search(r'/merchants/(\d+)', href)
            if match:
                merchant_ids.add(match.group(1))
    
    print(f'從首頁找到 {len(merchant_ids)} 個商家 ID')
    print(f'IDs: {sorted(list(merchant_ids))}')
    
    # 保存 HTML 以便分析
    html = page.content()
    with open('../data/merchant_home.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    browser.close()
