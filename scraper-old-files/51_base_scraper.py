import requests
from bs4 import BeautifulSoup
import time

def fetch_sitemap(url):
    """
    下載 sitemap，解析所有 URL
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"無法取得 sitemap: {url}")
        return []

    soup = BeautifulSoup(res.content, "xml")  # 解析 XML
    urls = [loc.text for loc in soup.find_all("loc")]
    return urls

def scrape_page(url):
    """
    簡單抓頁面標題和內容
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"無法取得頁面: {url}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.title.text if soup.title else "無標題"
    # 你可以根據需要解析更多內容，例如文章正文、日期、分類等
    return {"url": url, "title": title}

def main():
    sitemap_url = "https://www.51.ca/sitemap_index.xml"  # sitemap index
    urls = fetch_sitemap(sitemap_url)
    print(f"總共 {len(urls)} 個 sitemap 頁面")
    print("Sitemap URLs:")
    for url in urls:
        print(url)

    for sitemap in urls:
        page_urls = fetch_sitemap(sitemap)
        print(f"從 {sitemap} 抓到 {len(page_urls)} 個頁面 URL:")
        for page_url in page_urls:
            print(page_url)
        # 移除抓取頁面的部分

if __name__ == "__main__":
    main()
