"""深入分析商家頁面結構 - 找出如何提取數據"""
from bs4 import BeautifulSoup
import re

with open('../data/merchant_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

# 1. 找商家名稱 - 通常在 avatar 附近
print("=== 商家名稱 ===")
# 找 merchant-logo 附近的文字
for img in soup.find_all('img'):
    src = img.get('src', '')
    if 'merchant-logo' in src and 's0E4F' in src:  # 特定 logo
        parent = img.find_parent('div')
        for _ in range(5):  # 向上找幾層
            if parent:
                siblings = parent.find_next_siblings()
                for sib in siblings[:3]:
                    text = sib.get_text(strip=True)
                    if text and len(text) < 50 and '登录' not in text:
                        print(f"  可能的商家名: {text}")
                parent = parent.find_parent()

# 2. 用 CSS class 找
print("\n=== 通過 class 尋找 ===")
# 找所有有意義的 class
classes_found = set()
for tag in soup.find_all(True):
    for cls in tag.get('class', []):
        if any(k in cls.lower() for k in ['merchant', 'name', 'title', 'company', 'info', 'detail', 'profile']):
            classes_found.add(cls)
print(f"  相關 classes: {classes_found}")

for cls in classes_found:
    elements = soup.find_all(class_=cls)
    for el in elements[:2]:
        text = el.get_text(strip=True)[:100]
        if text:
            print(f"  .{cls}: {text}")

# 3. 直接搜索頁面內的商家名稱（我們知道是大统华）
print("\n=== 搜索 '大统华' ===")
elements = soup.find_all(string=lambda t: t and '大统华' in t)
for el in elements[:5]:
    parent = el.find_parent()
    if parent:
        print(f"  <{parent.name} class='{parent.get('class', [])}'>: {el.strip()[:60]}")

# 4. 找頁面的主要容器
print("\n=== 主要容器結構 ===")
main_container = soup.find(class_=re.compile('container|wrapper|main|content', re.I))
if main_container:
    print(f"  找到容器: class={main_container.get('class')}")

# 5. 查找公司資料區塊結構
print("\n=== 公司介紹區塊 ===")
h2_intro = soup.find('h2', string=lambda t: t and '公司介绍' in t)
if h2_intro:
    parent = h2_intro.find_parent('section') or h2_intro.find_parent('div')
    if parent:
        # 找該區塊下的所有文字段落
        paragraphs = parent.find_all(['p', 'div'], recursive=True)
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20 and '公司介绍' not in text:
                print(f"  內容: {text[:150]}...")
                break

# 6. 聯繫資訊區塊
print("\n=== 聯繫我們區塊 ===")
h2_contact = soup.find('h2', string=lambda t: t and '联系我们' in t)
if h2_contact:
    parent = h2_contact.find_parent('section') or h2_contact.find_parent('div')
    if parent:
        # 電話
        tel_links = parent.find_all('a', href=re.compile(r'^tel:'))
        for t in tel_links:
            print(f"  電話: {t.get('href')} => {t.get_text(strip=True)}")
        
        # 郵箱
        mail_links = parent.find_all('a', href=re.compile(r'^mailto:'))
        for m in mail_links:
            print(f"  郵箱: {m.get('href')}")
        
        # 地址 - 找包含 ON, BC 等省份的文字
        all_text = parent.get_text()
        addr_match = re.findall(r'[A-Za-z0-9\s,]+(?:ON|BC|AB|QC)[A-Za-z0-9\s]*', all_text)
        for addr in addr_match[:3]:
            print(f"  地址: {addr.strip()}")

# 7. 瀏覽數
print("\n=== 瀏覽數 ===")
view_text = soup.find(string=re.compile(r'\d+\s*人看过'))
if view_text:
    print(f"  {view_text.strip()}")
