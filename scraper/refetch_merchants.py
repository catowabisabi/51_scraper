"""
重新爬取所有商家的聯繫資訊
修復缺失的電話、地址、描述等欄位
"""
import re
import json
import sqlite3
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

DB_PATH = '../data/51ca.db'

def extract_merchant_data(soup: BeautifulSoup, merchant_id: str, url: str) -> dict:
    """從頁面提取商家資料"""
    data = {
        'merchant_id': merchant_id,
        'url': url,
    }
    
    # 1. 商家名稱
    name_elem = soup.select_one('.business-page__header__title')
    if name_elem:
        full_name = name_elem.get_text(strip=True)
        parts = re.split(r'(?<=[一-龥])(?=[A-Za-z])', full_name, 1)
        data['name'] = parts[0].strip() if parts else full_name
        data['english_name'] = parts[1].strip() if len(parts) > 1 else ''
    
    # 2. Logo
    logo_elem = soup.find('img', src=re.compile(r'merchant-logo/'))
    if logo_elem:
        data['logo_url'] = logo_elem.get('src', '')
    
    # 3. 瀏覽數
    view_elem = soup.find(string=re.compile(r'(\d+)\s*人看过'))
    if view_elem:
        match = re.search(r'(\d+)', view_elem)
        if match:
            data['review_count'] = int(match.group(1))
    
    # 4. 電話 - 從所有 tel: 連結提取
    phones = []
    for tel in soup.find_all('a', href=re.compile(r'^tel:')):
        phone = tel.get('href', '').replace('tel:', '')
        # 清理電話格式
        phone = re.sub(r'[^\d,\-\(\)\s]', '', phone).strip()
        if phone and phone not in phones:
            phones.append(phone)
    if phones:
        data['phone'] = ', '.join(phones)
    
    # 5. 郵箱
    emails = []
    for mail in soup.find_all('a', href=re.compile(r'^mailto:')):
        email = mail.get('href', '').replace('mailto:', '')
        if email and email not in emails:
            emails.append(email)
    if emails:
        data['website'] = ', '.join(emails)
    
    # 6. 地址 - 從 Google Maps 連結提取
    for link in soup.find_all('a', href=re.compile(r'google\.com/maps')):
        href = link.get('href', '')
        addr_match = re.search(r'query=([^&]+)', href)
        if addr_match:
            addr = unquote(addr_match.group(1).replace('+', ' '))
            # 清理地址
            addr = addr.strip().strip(',').strip()
            if addr and len(addr) > 3:
                data['address'] = addr
            break
    
    # 7. 公司介紹 - 精確提取
    for sec in soup.find_all(['section', 'div']):
        heading = sec.find(['h2', 'h3'], string=re.compile('公司介[绍紹]'))
        if heading:
            # 找 heading 之後的所有 p 或 div 文字
            content_parts = []
            for sibling in heading.find_next_siblings():
                # 遇到下一個 h2/h3 就停止
                if sibling.name in ['h2', 'h3']:
                    break
                text = sibling.get_text(strip=True)
                # 排除導航文字
                if text and not any(x in text for x in ['联系我们', '办公环境', '查看路线', '最新动态']):
                    content_parts.append(text)
            
            if content_parts:
                data['description'] = ' '.join(content_parts)[:2000]
            break
    
    # 8. 圖片 - 辦公環境 + 動態圖片
    images = []
    for img in soup.find_all('img', src=re.compile(r'merchant-photos/')):
        src = img.get('src', '')
        if src and src not in images:
            images.append(src)
    for img in soup.find_all('img', src=re.compile(r'merchant-moment-photos/')):
        src = img.get('src', '')
        if src and src not in images:
            images.append(src)
    if images:
        data['image_urls'] = json.dumps(images[:10], ensure_ascii=False)
    
    return data

def update_merchant(data: dict):
    """更新商家資料"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 只更新有值的欄位
    updates = []
    params = []
    
    fields = ['name', 'english_name', 'description', 'address', 'phone', 
              'website', 'logo_url', 'image_urls', 'review_count']
    
    for field in fields:
        if field in data and data[field]:
            updates.append(f'{field} = ?')
            params.append(data[field])
    
    if updates:
        params.append(data['merchant_id'])
        sql = f"UPDATE service_merchants SET {', '.join(updates)}, updated_at = datetime('now') WHERE merchant_id = ?"
        c.execute(sql, params)
    
    conn.commit()
    conn.close()

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 獲取所有商家
    c.execute('SELECT merchant_id, url, name FROM service_merchants')
    merchants = c.fetchall()
    conn.close()
    
    print(f'=== 重新爬取 {len(merchants)} 個商家 ===')
    
    updated = 0
    errors = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, (mid, url, name) in enumerate(merchants):
            print(f'[{i+1}/{len(merchants)}] {name or mid}...', end=' ')
            
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(1500)
                
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')
                
                data = extract_merchant_data(soup, mid, url)
                
                # 檢查是否有新資料
                if data.get('phone') or data.get('description') or data.get('address'):
                    update_merchant(data)
                    updated += 1
                    print('✓ 更新')
                else:
                    print('- 無變化')
                
                time.sleep(0.3)
                
            except Exception as e:
                errors += 1
                print(f'✗ 錯誤: {str(e)[:30]}')
        
        browser.close()
    
    print(f'\n=== 完成 ===')
    print(f'更新: {updated}')
    print(f'錯誤: {errors}')

if __name__ == '__main__':
    main()
