"""
測試汽車頁面的多圖片提取
分析頁面結構找出所有汽車照片
"""
import re
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def analyze_car_page(url: str):
    print(f'分析: {url}')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            html = page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # 1. 查找所有 storage.51yun.ca 圖片
            print('\n=== storage.51yun.ca 所有圖片 ===')
            all_storage_imgs = set()
            
            # 從 img 標籤
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and 'storage.51yun.ca' in src:
                    all_storage_imgs.add(src)
            
            # 從 background-image
            bg_pattern = re.compile(r'url\(["\']?(https?://[^"\'()]+)["\']?\)')
            for elem in soup.find_all(style=True):
                style = elem.get('style', '')
                for match in bg_pattern.finditer(style):
                    url_found = match.group(1)
                    if 'storage.51yun.ca' in url_found:
                        all_storage_imgs.add(url_found)
            
            for img in sorted(all_storage_imgs):
                img_type = 'unknown'
                if 'auto-car-photos' in img:
                    img_type = '🚗 汽車照片'
                elif 'dealer-logo' in img:
                    img_type = '🏢 經銷商Logo'
                elif 'salesperson' in img:
                    img_type = '👤 銷售員'
                print(f'  {img_type}: {img}')
            
            print(f'\n總共: {len(all_storage_imgs)} 張')
            car_photos = [img for img in all_storage_imgs if 'auto-car-photos' in img]
            print(f'汽車照片: {len(car_photos)} 張')
            
            # 2. 查找輪播容器
            print('\n=== 輪播/畫廊容器 ===')
            swipers = soup.select('.swiper-slide, .gallery-item, .carousel-item, [class*="slide"]')
            print(f'找到 slide 元素: {len(swipers)}')
            
            # 檢查 swiper 容器內的圖片
            swiper_container = soup.select_one('.swiper, .swiper-container, [class*="swiper"]')
            if swiper_container:
                print('\n=== Swiper 容器內的圖片 ===')
                for elem in swiper_container.find_all(style=True):
                    style = elem.get('style', '')
                    for match in bg_pattern.finditer(style):
                        print(f'  {match.group(1)}')
            
            # 3. 檢查 JavaScript 中的圖片數據
            print('\n=== JavaScript 數據 ===')
            for script in soup.find_all('script'):
                text = script.string or ''
                if 'auto-car-photos' in text:
                    # 提取 URL
                    urls = re.findall(r'https?://storage\.51yun\.ca/auto-car-photos/[^"\']+', text)
                    print(f'  在 JS 中找到 {len(urls)} 張汽車照片')
                    for u in urls[:5]:
                        print(f'    {u}')
                    if len(urls) > 5:
                        print(f'    ... 還有 {len(urls) - 5} 張')
            
        finally:
            browser.close()

if __name__ == '__main__':
    # 測試一個有圖片的汽車頁面
    analyze_car_page('https://www.51.ca/autos/used-cars/9890')
