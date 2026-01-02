"""
爬取缺失的商家資料
"""
import re
import json
import sqlite3
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

DB_PATH = '../data/51ca.db'

def fetch_merchant(merchant_id: str) -> dict:
    """爬取單個商家"""
    url = f'https://merchant.51.ca/merchants/{merchant_id}'
    print(f'爬取商家: {url}')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            html = page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            data = {
                'merchant_id': merchant_id,
                'url': url,
            }
            
            # 名稱
            name_elem = soup.select_one('.business-page__header__title')
            if name_elem:
                full_name = name_elem.get_text(strip=True)
                parts = re.split(r'(?<=[一-龥])(?=[A-Za-z])', full_name, 1)
                data['name'] = parts[0].strip() if parts else full_name
                data['english_name'] = parts[1].strip() if len(parts) > 1 else ''
            
            # Logo
            logo_elem = soup.find('img', src=re.compile(r'merchant-logo/'))
            if logo_elem:
                data['logo_url'] = logo_elem.get('src', '')
            
            # 瀏覽數
            view_elem = soup.find(string=re.compile(r'(\d+)\s*人看过'))
            if view_elem:
                match = re.search(r'(\d+)', view_elem)
                if match:
                    data['review_count'] = int(match.group(1))
            
            # 描述
            for sec in soup.find_all(['section', 'div'], recursive=True):
                heading = sec.find(['h2', 'h3'], string=re.compile('公司介[绍紹]'))
                if heading:
                    content_parts = []
                    for sibling in heading.find_next_siblings():
                        text = sibling.get_text(strip=True)
                        if sibling.name in ['h2', 'h3'] or '联系我们' in text:
                            break
                        if text:
                            content_parts.append(text)
                    if content_parts:
                        data['description'] = ' '.join(content_parts)[:2000]
                    break
            
            # 聯繫資訊
            contact_section = None
            for sec in soup.find_all(['section', 'div'], recursive=True):
                heading = sec.find(['h2', 'h3'], string=re.compile('联系我们|聯繫我們'))
                if heading:
                    contact_section = sec
                    break
            
            if contact_section:
                # 電話
                phones = []
                for tel in contact_section.find_all('a', href=re.compile(r'^tel:')):
                    phone = tel.get('href', '').replace('tel:', '').replace('-', '')
                    if phone and phone not in phones:
                        phones.append(phone)
                if phones:
                    data['phone'] = ', '.join(phones)
                
                # 地址
                maps_link = contact_section.find('a', href=re.compile(r'google\.com/maps'))
                if maps_link:
                    maps_url = maps_link.get('href', '')
                    addr_match = re.search(r'query=([^&]+)', maps_url)
                    if addr_match:
                        from urllib.parse import unquote
                        addr = unquote(addr_match.group(1).replace('+', ' '))
                        if addr and len(addr) > 5:
                            data['address'] = addr
            
            # 圖片
            images = []
            for img in soup.find_all('img', src=re.compile(r'merchant-photos/|merchant-moment-photos/')):
                src = img.get('src', '')
                if src and src not in images:
                    images.append(src)
            if images:
                data['image_urls'] = json.dumps(images[:10], ensure_ascii=False)
            
            return data
            
        finally:
            browser.close()

def save_merchant(data: dict):
    """保存商家到資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO service_merchants 
        (merchant_id, url, name, english_name, description, address, phone, 
         logo_url, image_urls, review_count, scraped_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (
        data.get('merchant_id'),
        data.get('url'),
        data.get('name'),
        data.get('english_name'),
        data.get('description'),
        data.get('address'),
        data.get('phone'),
        data.get('logo_url'),
        data.get('image_urls'),
        data.get('review_count', 0),
    ))
    
    conn.commit()
    conn.close()
    print(f'已保存: {data.get("name")}')

def main():
    # 找出缺失的商家
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT DISTINCT j.merchant_id 
        FROM job_listings j 
        LEFT JOIN service_merchants m ON j.merchant_id = m.merchant_id
        WHERE j.merchant_id IS NOT NULL AND m.merchant_id IS NULL
    ''')
    
    missing = [row[0] for row in c.fetchall()]
    conn.close()
    
    print(f'缺失的商家: {missing}')
    
    for mid in missing:
        data = fetch_merchant(mid)
        if data.get('name'):
            save_merchant(data)
        else:
            print(f'  無法獲取商家資料: {mid}')

if __name__ == '__main__':
    main()
