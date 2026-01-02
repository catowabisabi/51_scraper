"""分析商家頁面結構"""
from bs4 import BeautifulSoup

with open('../data/merchant_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

# 1. 找商家名稱 - 通常在 h1 或特定 class
print("=== 尋找商家名稱 ===")
for tag in ['h1', 'h2', 'h3']:
    elements = soup.find_all(tag)
    for el in elements[:5]:
        text = el.get_text(strip=True)
        if text and len(text) < 100:
            print(f"  {tag}: {text}")

# 2. 找 avatar/logo
print("\n=== 尋找 Logo/Avatar ===")
for img in soup.find_all('img'):
    src = img.get('src', '')
    alt = img.get('alt', '')
    if 'logo' in src.lower() or 'avatar' in src.lower() or 'merchant' in src.lower():
        print(f"  src: {src[:100]}")

# 3. 找公司介紹
print("\n=== 尋找公司介紹 ===")
# 找包含"公司介紹"的 section
sections = soup.find_all(['section', 'div'])
for sec in sections:
    heading = sec.find(['h2', 'h3', 'div'], string=lambda t: t and '公司介紹' in t)
    if heading:
        # 找下一個包含實際內容的元素
        content = sec.find('p') or sec.find('div', class_=lambda x: x and 'content' in str(x).lower())
        if content:
            print(f"  公司介紹: {content.get_text()[:200]}")
        else:
            text = sec.get_text()
            # 移除 "公司介紹" 標題本身
            text = text.replace('公司介紹', '').strip()
            if text:
                print(f"  整段: {text[:200]}")

# 4. 找聯繫資訊區塊
print("\n=== 尋找聯繫資訊 ===")
for sec in sections:
    heading = sec.find(['h2', 'h3', 'div'], string=lambda t: t and '聯繫' in t)
    if heading:
        # 電話
        phones = sec.find_all('a', href=lambda h: h and 'tel:' in h)
        for p in phones:
            print(f"  電話: {p.get('href')} - {p.get_text(strip=True)}")
        
        # 郵箱
        emails = sec.find_all('a', href=lambda h: h and 'mailto:' in h)
        for e in emails:
            print(f"  郵箱: {e.get('href')}")
        
        # 地址
        address_text = sec.get_text()
        if 'ON' in address_text or 'BC' in address_text:
            import re
            # 找地址模式
            addr_match = re.search(r'[\w\s]+,\s*[\w\s]+,\s*ON[\w\s]*', address_text)
            if addr_match:
                print(f"  地址: {addr_match.group()}")

# 5. 頁面中的所有 script 標籤
print("\n=== Script 標籤 ===")
scripts = soup.find_all('script')
for script in scripts:
    if script.get('id'):
        print(f"  id: {script.get('id')}")
    if script.get('src'):
        print(f"  src: {script.get('src')[:80]}")

# 6. 尋找可能的 JSON 數據
print("\n=== 內嵌 JSON ===")
for script in scripts:
    if script.string and script.string.strip().startswith('{'):
        print(f"  發現 JSON 數據: {script.string[:200]}...")
        break
