"""
深入分析商家頁面結構
使用 Playwright 獲取完整 HTML 並分析
"""
import re
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def analyze_merchant_page(merchant_id: str):
    url = f'https://merchant.51.ca/merchants/{merchant_id}'
    print(f'分析商家頁面: {url}')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            html = page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # 1. 商家名稱
            print('\n=== 1. 商家名稱 ===')
            title_elem = soup.select_one('.business-page__header__title')
            if title_elem:
                print(f'  找到: {title_elem.get_text(strip=True)}')
            else:
                print('  未找到 .business-page__header__title')
                # 嘗試其他選擇器
                for h1 in soup.find_all('h1'):
                    print(f'  H1: {h1.get_text(strip=True)[:50]}')
            
            # 2. 聯繫資訊區域
            print('\n=== 2. 聯繫我們區域 ===')
            contact_section = None
            for sec in soup.find_all(['section', 'div']):
                heading = sec.find(['h2', 'h3'], string=re.compile('联系我们|聯繫我們'))
                if heading:
                    contact_section = sec
                    print(f'  找到聯繫區域')
                    break
            
            if not contact_section:
                print('  未找到「聯繫我們」section')
            
            # 3. 電話連結
            print('\n=== 3. 電話連結 ===')
            for tel in soup.find_all('a', href=re.compile(r'^tel:')):
                href = tel.get('href', '')
                text = tel.get_text(strip=True)
                print(f'  tel: {href} => {text}')
            
            # 4. 郵箱連結
            print('\n=== 4. 郵箱連結 ===')
            for mail in soup.find_all('a', href=re.compile(r'^mailto:')):
                href = mail.get('href', '')
                print(f'  mailto: {href}')
            
            # 5. Google Maps 連結
            print('\n=== 5. 地址 (Google Maps) ===')
            for link in soup.find_all('a', href=re.compile(r'google\.com/maps')):
                href = link.get('href', '')
                addr_match = re.search(r'query=([^&]+)', href)
                if addr_match:
                    from urllib.parse import unquote
                    addr = unquote(addr_match.group(1).replace('+', ' '))
                    print(f'  地址: {addr}')
            
            # 6. 公司介紹
            print('\n=== 6. 公司介紹 ===')
            for sec in soup.find_all(['section', 'div']):
                heading = sec.find(['h2', 'h3'], string=re.compile('公司介[绍紹]'))
                if heading:
                    # 找下一個 sibling 或 p 標籤
                    next_elem = heading.find_next_sibling()
                    if next_elem:
                        text = next_elem.get_text(strip=True)[:200]
                        print(f'  描述: {text}...')
                    break
            
            # 7. 圖片
            print('\n=== 7. 圖片 ===')
            photos = []
            for img in soup.find_all('img', src=re.compile(r'merchant-photos/')):
                photos.append(img.get('src'))
            print(f'  辦公環境圖片: {len(photos)} 張')
            
            moment_photos = []
            for img in soup.find_all('img', src=re.compile(r'merchant-moment-photos/')):
                moment_photos.append(img.get('src'))
            print(f'  動態圖片: {len(moment_photos)} 張')
            
            # 8. Logo
            print('\n=== 8. Logo ===')
            logo = soup.find('img', src=re.compile(r'merchant-logo/'))
            if logo:
                print(f'  Logo: {logo.get("src")}')
            
            # 9. 瀏覽數
            print('\n=== 9. 瀏覽數 ===')
            view_elem = soup.find(string=re.compile(r'(\d+)\s*人看过'))
            if view_elem:
                match = re.search(r'(\d+)', view_elem)
                if match:
                    print(f'  瀏覽數: {match.group(1)}')
            
        finally:
            browser.close()

if __name__ == '__main__':
    # 測試幾個不同的商家
    analyze_merchant_page('3116')  # 大統華
    print('\n' + '='*60 + '\n')
    analyze_merchant_page('7936')  # 恒泰会计师事务所 (沒電話的)
