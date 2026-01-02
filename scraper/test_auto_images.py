"""
測試汽車圖片爬取 - 使用 Playwright 獲取動態加載的圖片
"""
import re
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def test_scrape():
    url = 'https://www.51.ca/autos/used-cars/9890'
    
    print(f'Testing: {url}')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)  # 等待圖片加載
            
            html = page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            print('\n=== 所有 storage.51yun.ca 圖片 ===')
            all_imgs = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and 'storage.51yun.ca' in src:
                    all_imgs.append(src)
                    print(f'  {src}')
            
            print(f'\n總共 {len(all_imgs)} 張')
            
            # 分類
            print('\n=== 圖片分類 ===')
            car_photos = [img for img in all_imgs if 'auto-photos' in img or 'auto-image' in img or 'car-' in img]
            dealer_logos = [img for img in all_imgs if 'dealer-logo' in img]
            salesperson = [img for img in all_imgs if 'salesperson' in img]
            
            print(f'  汽車照片: {len(car_photos)}')
            print(f'  經銷商Logo: {len(dealer_logos)}')
            print(f'  銷售員頭像: {len(salesperson)}')
            
            # 檢查是否有圖片輪播區域
            print('\n=== 檢查圖片輪播 ===')
            swipers = soup.select('.swiper, .gallery, .carousel, .slider, [class*="swiper"], [class*="gallery"]')
            print(f'  找到輪播/畫廊容器: {len(swipers)}')
            
            # 檢查 data-src 屬性（懶加載圖片）
            print('\n=== 懶加載圖片 (data-src) ===')
            lazy_imgs = soup.find_all('img', attrs={'data-src': True})
            for img in lazy_imgs[:5]:
                print(f'  {img.get("data-src")}')
            print(f'  總共 {len(lazy_imgs)} 張')
            
            # 檢查 background-image
            print('\n=== 背景圖片樣式 ===')
            bg_pattern = re.compile(r'background(?:-image)?\s*:\s*url\(["\']?(https?://[^"\'()]+)["\']?\)')
            for elem in soup.find_all(style=True)[:10]:
                style = elem.get('style', '')
                match = bg_pattern.search(style)
                if match:
                    print(f'  {match.group(1)}')
            
        finally:
            browser.close()

if __name__ == '__main__':
    test_scrape()
