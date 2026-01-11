"""查看工作詳情頁 HTML 結構"""

import json
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("Starting...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto("https://www.51.ca/jobs/job-posts/1174462", wait_until='networkidle')
    
    # 獲取 HTML
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # 保存 HTML
    with open('testing/job_detail_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML saved to testing/job_detail_page.html")
    
    # 查找標題
    title = soup.find('h1')
    print(f"\n標題 (h1): {title.get_text(strip=True) if title else 'N/A'}")
    
    # 查找電話
    tel_links = soup.find_all('a', href=re.compile(r'tel:'))
    print(f"電話連結: {[a.get('href') for a in tel_links]}")
    
    # 查找內容
    content_div = soup.find('div', class_=re.compile(r'content|description|detail'))
    if content_div:
        print(f"\n內容 (前200字): {content_div.get_text(strip=True)[:200]}")
    
    # 找所有 class 包含 job 的元素
    print("\n=== Class 包含 job 的元素 ===")
    for elem in soup.find_all(class_=re.compile(r'job', re.I))[:10]:
        print(f"  {elem.name}.{' '.join(elem.get('class', []))}")
    
    # 找信息列表
    print("\n=== 信息項 ===")
    info_items = soup.find_all(['li', 'span', 'div'], class_=re.compile(r'info|tag|label|item'))
    for item in info_items[:15]:
        text = item.get_text(strip=True)
        if text and len(text) < 50:
            print(f"  {text}")
    
    # 用 Playwright 直接提取特定元素
    print("\n=== Playwright 提取 ===")
    
    # 標題
    title_elem = page.locator('h1').first
    if title_elem.count() > 0:
        print(f"標題: {title_elem.inner_text()}")
    
    # 地區
    location_elem = page.locator('[class*="location"], [class*="area"]').first
    try:
        print(f"地點: {location_elem.inner_text()}")
    except:
        pass
    
    # 分類
    category_elem = page.locator('[class*="category"], [class*="type"]').first
    try:
        print(f"分類: {category_elem.inner_text()}")
    except:
        pass
    
    # 發布者
    publisher_elem = page.locator('[class*="name"], [class*="publisher"], [class*="poster"]').first
    try:
        print(f"發布者: {publisher_elem.inner_text()}")
    except:
        pass
    
    browser.close()
    print("\nDone!")
