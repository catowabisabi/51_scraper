"""檢查網頁源碼找出缺失欄位的選擇器"""
import requests
from bs4 import BeautifulSoup

def check_news_page():
    url = 'https://info.51.ca/articles/1503361'
    print(f"=== Checking NEWS: {url} ===\n")
    
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # SOURCE
    print('SOURCE candidates:')
    for sel in ['.article-meta .source span', '.source span', '.article-source']:
        elems = soup.select(sel)
        for e in elems[:2]:
            text = e.get_text().strip()
            if text:
                print(f'  {sel}: "{text[:50]}"')
    
    # TIME
    print('\nTIME candidates:')
    for sel in ['.article-meta time', 'time', '.publish-time', '.article-date']:
        elems = soup.select(sel)
        for e in elems[:2]:
            text = e.get_text().strip()
            if text:
                print(f'  {sel}: "{text}"')
    
    # OG:IMAGE
    print('\nOG:IMAGE:')
    og = soup.select_one('meta[property="og:image"]')
    if og:
        print(f'  {og.get("content")}')
    
    # ARCBODY IMAGES
    print('\nARCBODY IMAGES:')
    for img in soup.select('#arcbody img')[:3]:
        src = img.get('data-src') or img.get('src')
        if src:
            print(f'  {src[:70]}...')


def check_house_page():
    url = 'https://house.51.ca/rental/ontario/toronto/scarborough/607004'
    print(f"\n\n=== Checking HOUSE: {url} ===\n")
    
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # TITLE
    print('TITLE candidates:')
    for sel in ['h1', '.listing-title', '.property-title', 'title']:
        elems = soup.select(sel)
        for e in elems[:2]:
            text = e.get_text().strip()
            if text and len(text) < 100:
                print(f'  {sel}: "{text[:60]}"')
    
    # BATHROOMS
    print('\nBATHROOMS candidates:')
    text = soup.get_text()
    import re
    bath_match = re.search(r'(\d+)\s*(?:bath|bathroom|浴室|衛生間|washroom)', text, re.I)
    if bath_match:
        print(f'  Found in text: {bath_match.group(0)}')
    
    # Look for spec tables
    for sel in ['.specs', '.property-info', '.listing-details', 'dl', 'table']:
        elems = soup.select(sel)
        if elems:
            sample = elems[0].get_text()[:200].replace('\n', ' ')
            print(f'  {sel}: "{sample}"')
    
    # AGENT
    print('\nAGENT candidates:')
    for sel in ['.agent', '.realtor', '.contact-name', '.broker', '[class*=agent]']:
        elems = soup.select(sel)
        for e in elems[:2]:
            text = e.get_text().strip()
            if text:
                print(f'  {sel}: "{text[:50]}"')


def check_market_page():
    url = 'https://www.51.ca/market/'
    print(f"\n\n=== Checking MARKET: {url} ===\n")
    
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Check __NEXT_DATA__
    next_data = soup.select_one('#__NEXT_DATA__')
    if next_data:
        import json
        data = json.loads(next_data.string)
        items = data.get('props', {}).get('pageProps', {}).get('initialProducts', [])
        if items:
            item = items[0]
            print(f'Sample item keys: {list(item.keys())}')
            print(f'\nCategory info:')
            print(f'  category: {item.get("category")}')
            print(f'  categoryName: {item.get("categoryName")}')
            print(f'\nLocation info:')
            print(f'  location: {item.get("location")}')
            print(f'  locationId: {item.get("locationId")}')
            print(f'\nContact info:')
            print(f'  phone: {item.get("phone")}')
            print(f'  contactPhone: {item.get("contactPhone")}')
            print(f'  wechatNo: {item.get("wechatNo")}')


if __name__ == '__main__':
    check_news_page()
    check_house_page()
    check_market_page()
