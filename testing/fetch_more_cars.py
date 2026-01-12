"""
直接爬取更多汽車數據
"""
import requests
import sqlite3
import os
from bs4 import BeautifulSoup
import re
import json

DB_PATH = os.path.join("scrapers", "data", "51ca.db")

def fetch_more_cars():
    """直接從汽車列表頁面爬取更多數據"""
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    total_saved = 0
    
    # 從汽車列表頁面爬取
    for page in range(1, 11):  # 前10頁
        try:
            url = f"https://www.51.ca/autos/used-cars?page={page}"
            print(f"爬取頁面 {page}: {url}")
            
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 找到汽車連結
            car_links = soup.find_all('a', href=re.compile(r'/autos/(used-cars|new-cars)/\d+'))
            
            print(f"找到 {len(car_links)} 個汽車連結")
            
            for link in car_links:
                href = link.get('href', '')
                if not href:
                    continue
                    
                # 提取汽車ID
                car_match = re.search(r'/autos/(used-cars|new-cars)/(\d+)', href)
                if not car_match:
                    continue
                    
                car_id = car_match.group(2)
                car_type = car_match.group(1)
                car_url = f"https://www.51.ca{href}" if href.startswith('/') else href
                
                # 獲取基本信息
                title_elem = link.find_parent().find(['h3', 'h4', '.title'])
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # 提取價格
                price_elem = link.find_parent().find(class_=re.compile(r'price'))
                price_text = price_elem.get_text(strip=True) if price_elem else ''
                price = None
                if price_text:
                    price_match = re.search(r'[\$,\d]+', price_text.replace(',', ''))
                    if price_match:
                        try:
                            price = float(price_match.group().replace('$', '').replace(',', ''))
                        except:
                            pass
                
                # 提取品牌和型號
                brand, model, year = '', '', None
                if title:
                    parts = title.split()
                    if len(parts) >= 3:
                        year_match = re.search(r'20\d{2}', title)
                        if year_match:
                            year = int(year_match.group())
                        
                        # 常見品牌
                        brands = ['Toyota', 'Honda', 'BMW', 'Mercedes', 'Audi', 'Ford', 'Chevrolet', 'Nissan']
                        for b in brands:
                            if b.lower() in title.lower():
                                brand = b
                                break
                        
                        # 提取型號
                        title_upper = title.upper()
                        if brand.upper() in title_upper:
                            model_start = title_upper.find(brand.upper()) + len(brand)
                            model = title[model_start:].strip()
                
                try:
                    c.execute("""
                        INSERT OR REPLACE INTO auto_listings (
                            id, listing_id, url, title, brand, model, year, price, 
                            car_type, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (None, car_id, car_url, title, brand, model, year, price, car_type))
                    
                    if c.rowcount > 0:
                        total_saved += 1
                        
                except Exception as e:
                    print(f"保存汽車錯誤: {e}")
            
            conn.commit()
            print(f"頁面 {page} 完成，總計保存 {total_saved} 輛車")
            
        except Exception as e:
            print(f"頁面 {page} 錯誤: {e}")
            continue
    
    conn.close()
    print(f"完成！總共新增 {total_saved} 輛汽車")

if __name__ == "__main__":
    fetch_more_cars()