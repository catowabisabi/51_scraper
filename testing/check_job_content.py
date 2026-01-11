"""查看工作詳情頁完整內容"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.51.ca/jobs/job-posts/1174975', wait_until='networkidle')
    
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # 找工作描述區域
    print('=== 尋找工作描述 ===\n')
    
    # 方法1: 找 job-detail 相關區域
    detail_sections = soup.find_all(class_=re.compile(r'job-detail|job-content|description'))
    print(f'找到 {len(detail_sections)} 個相關區域')
    
    for section in detail_sections[:5]:
        classes = section.get('class', [])
        text = section.get_text(strip=True)[:300]
        print(f'\nClass: {classes}')
        print(f'Text: {text}...')
    
    # 方法2: 用 Playwright 直接找
    print('\n\n=== Playwright 選擇器 ===\n')
    
    # 找主要內容區
    selectors = [
        '.job-detail-section',
        '.job-content',
        '.detail-content',
        'article',
        '.post-content',
    ]
    
    for sel in selectors:
        elem = page.locator(sel)
        if elem.count() > 0:
            print(f'{sel}: 找到 {elem.count()} 個')
            text = elem.first.inner_text()[:500]
            print(f'內容: {text}...\n')
    
    # 找具體的職位描述
    print('\n=== 尋找職位描述段落 ===\n')
    
    # 找包含具體文字的段落
    paragraphs = soup.find_all(['p', 'div'], string=re.compile(r'.{50,}'))
    for p in paragraphs[:5]:
        text = p.get_text(strip=True)
        if len(text) > 50:
            print(f'{text[:200]}...\n')
    
    browser.close()
