"""分析聯繫資訊結構"""
from bs4 import BeautifulSoup
import re

with open('../data/merchant_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

# 找 contacts_info
contact = soup.select_one('.contacts_info')
if contact:
    print('=== contacts_info 完整內容 ===')
    print(contact.get_text(separator=' | ')[:500])
    
    # 電話連結
    print('\n=== 電話連結 ===')
    for tel in contact.find_all('a', href=re.compile(r'^tel:')):
        href = tel.get('href', '')
        text = tel.get_text(strip=True)
        print(f'  {href} => {text}')
    
    # 整理提取電話
    phones = []
    for tel in contact.find_all('a', href=re.compile(r'^tel:')):
        phone = tel.get('href', '').replace('tel:', '')
        if phone:
            phones.append(phone)
    print(f'\n提取的電話: {phones}')
