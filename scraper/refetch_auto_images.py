"""
重新爬取汽車圖片 - 使用更新後的圖片提取邏輯
"""
import sqlite3
import json
import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DB_PATH = '../data/51ca.db'

def extract_car_images(soup: BeautifulSoup) -> list:
    """從頁面提取汽車圖片 - 從 JavaScript 提取"""
    images = []
    seen = set()
    
    exclude_keywords = [
        'logo', 'icon', 'avatar', 'button', 'ad', 'static-maps', 
        'placeholder', 'loading', 'assets/images', 'common/', 
        'detail/', 'radio_', 'checkbox', 'carfax', 'bell.png',
        'test-driv', 'empty', 'search', 'svg', 'default',
        'dealer-logo', 'salesperson'
    ]
    
    # 1. 從 JavaScript 提取 (最完整的來源)
    for script in soup.find_all('script'):
        text = script.string or ''
        if 'auto-car-photos' in text:
            urls = re.findall(r'https?://storage\.51yun\.ca/auto-car-photos/[^"\']+\.(?:jpg|jpeg|png|webp)', text, re.I)
            for url in urls:
                if url not in seen:
                    images.append(url)
                    seen.add(url)
    
    # 2. 從 CSS background-image 提取 (備用)
    if not images:
        bg_pattern = re.compile(r'url\(["\']?(https?://[^"\'()]+)["\']?\)')
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            for match in bg_pattern.finditer(style):
                url = match.group(1)
                if url in seen:
                    continue
                if any(x in url.lower() for x in exclude_keywords):
                    continue
                if 'storage.51yun.ca' in url and 'auto-car-photos' in url:
                    images.append(url)
                    seen.add(url)
    
    return images[:20]

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('=== 重新爬取汽車圖片 ===')
    
    c.execute('SELECT listing_id, url, title FROM auto_listings')
    rows = c.fetchall()
    
    print(f'總汽車列表: {len(rows)}')
    
    updated_count = 0
    total_images = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, (listing_id, url, title) in enumerate(rows):
            print(f'[{i+1}/{len(rows)}] {title[:30]}...', end=' ')
            
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(1500)
                
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')
                
                images = extract_car_images(soup)
                
                if images:
                    image_json = json.dumps(images, ensure_ascii=False)
                    c.execute('UPDATE auto_listings SET image_urls = ? WHERE listing_id = ?',
                             (image_json, listing_id))
                    updated_count += 1
                    total_images += len(images)
                    print(f'✓ {len(images)} 張圖片')
                else:
                    print('✗ 無圖片')
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f'✗ 錯誤: {str(e)[:30]}')
        
        browser.close()
    
    conn.commit()
    
    print('\n=== 結果 ===')
    print(f'更新記錄: {updated_count}/{len(rows)}')
    print(f'總圖片數: {total_images}')
    
    conn.close()
    print('完成!')

if __name__ == '__main__':
    main()
