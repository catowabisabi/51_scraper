"""
寻找 market 分页 API - 详细搜索
"""
import requests
import re
import json
from bs4 import BeautifulSoup

# 获取主页
r = requests.get('https://www.51.ca/market/all')
soup = BeautifulSoup(r.text, 'lxml')

# 找到所有 script src
scripts = soup.find_all('script', src=True)
js_urls = [s['src'] for s in scripts if '/_next/static' in s.get('src', '')]

# 只搜索 categorySlug 相关的 JS 文件
print("=== Searching categorySlug JS file ===")
for url in js_urls:
    if 'categorySlug' in url:
        full_url = 'https://www.51.ca' + url
        print(f"Downloading: {full_url}")
        r = requests.get(full_url, timeout=10)
        content = r.text
        
        # 搜索分页相关代码
        print("\n=== Pagination related patterns ===")
        
        # 找 page 相关的代码
        page_matches = re.findall(r'.{0,50}page.{0,50}', content, re.IGNORECASE)
        for m in page_matches[:20]:
            if 'Page' in m or 'page=' in m or 'page:' in m:
                print(f"  {m[:80]}")
        
        # 找 fetch/axios 调用
        print("\n=== Fetch patterns ===")
        fetch_matches = re.findall(r'fetch\(.{0,100}\)', content)
        for m in fetch_matches[:10]:
            print(f"  {m[:100]}")
        
        # 找 getServerSideProps 或类似
        print("\n=== SSR patterns ===")
        ssr_matches = re.findall(r'getServerSideProps|getStaticProps|getInitialProps', content)
        print(f"  Found: {ssr_matches}")
        
        # 找带 page 参数的 URL 构造
        print("\n=== URL with page param ===")
        url_matches = re.findall(r'["\'][^"\']*\?[^"\']*page[^"\']*["\']', content)
        for m in url_matches[:10]:
            print(f"  {m}")
        
        break
