"""
Add more house URLs to the queue by crawling rental listing pages
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import time

db_path = r'c:\Users\Chris\Desktop\app\CICD\HK-Garden-App\51_scraper\scrapers\data\51ca.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
all_urls = set()

print('Crawling rental listing pages...')
for page in range(1, 101):  # 100 pages
    try:
        url = f'https://house.51.ca/rental?page={page}'
        response = requests.get(url, timeout=30, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            links = soup.find_all('a', href=True)
            for a in links:
                href = a.get('href', '')
                if '/rental/ontario/' in href:
                    parts = href.split('/')
                    if parts and parts[-1].split('?')[0].isdigit():
                        clean = href.split('?')[0]
                        if not clean.startswith('http'):
                            clean = f'https://house.51.ca{clean}'
                        all_urls.add(clean)
        
        if page % 10 == 0:
            print(f'  Page {page}: {len(all_urls)} unique URLs')
        time.sleep(0.2)
    except Exception as e:
        print(f'  Page {page} error: {e}')

print(f'\nTotal unique URLs found: {len(all_urls)}')

added = 0
for url in all_urls:
    cursor.execute(
        "INSERT OR IGNORE INTO url_queue (url, url_type, priority, visited) VALUES (?, 'house', 5, 0)", 
        (url,)
    )
    if cursor.rowcount > 0:
        added += 1

conn.commit()
print(f'Added {added} new URLs to queue')

cursor.execute("SELECT COUNT(*) FROM url_queue WHERE url_type = 'house'")
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM url_queue WHERE url_type = 'house' AND visited = 0")
pending = cursor.fetchone()[0]
print(f'House URL queue: {total} total, {pending} pending')

conn.close()
print('Done!')
