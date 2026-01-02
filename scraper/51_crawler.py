"""
51.ca 網站爬蟲
使用 Playwright 爬取動態內容，將資料存入 SQLite
"""

import sqlite3
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


# ============== 資料庫設定 ==============
DB_PATH = "51ca_data.db"


def init_db():
    """初始化 SQLite 資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 創建頁面資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            content TEXT,
            html TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 創建連結資料表（用於追蹤爬取進度）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            source_url TEXT,
            visited INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成")


def add_link(url, source_url=None):
    """添加連結到資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO links (url, source_url) VALUES (?, ?)",
            (url, source_url)
        )
        conn.commit()
    except Exception as e:
        print(f"添加連結失敗: {e}")
    finally:
        conn.close()


def mark_visited(url):
    """標記連結為已訪問"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE links SET visited = 1 WHERE url = ?", (url,))
    conn.commit()
    conn.close()


def get_unvisited_links(limit=10):
    """獲取未訪問的連結"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT url FROM links WHERE visited = 0 LIMIT ?",
        (limit,)
    )
    urls = [row[0] for row in cursor.fetchall()]
    conn.close()
    return urls


def save_page(url, title, content, html):
    """保存頁面資料到資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR REPLACE INTO pages (url, title, content, html, scraped_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (url, title, content, html, datetime.now())
        )
        conn.commit()
        print(f"✅ 已保存: {title[:50]}...")
    except Exception as e:
        print(f"❌ 保存失敗: {e}")
    finally:
        conn.close()


def is_valid_url(url, base_domain="51.ca"):
    """檢查URL是否有效且屬於目標網域"""
    if not url:
        return False
    
    parsed = urlparse(url)
    
    # 排除非HTTP協議
    if parsed.scheme not in ("http", "https", ""):
        return False
    
    # 排除特定文件類型
    excluded_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.rar', '.exe', '.mp3', '.mp4')
    if parsed.path.lower().endswith(excluded_extensions):
        return False
    
    # 確保是目標網域
    if parsed.netloc and base_domain not in parsed.netloc:
        return False
    
    return True


def extract_links(html, base_url):
    """從HTML中提取所有連結"""
    soup = BeautifulSoup(html, "lxml")
    links = set()
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        
        # 清理URL（移除fragment）
        parsed = urlparse(full_url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        
        if is_valid_url(clean_url):
            links.add(clean_url)
    
    return links


def extract_content(html):
    """從HTML中提取文字內容"""
    soup = BeautifulSoup(html, "lxml")
    
    # 移除script和style標籤
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    
    # 獲取純文字
    text = soup.get_text(separator="\n", strip=True)
    
    # 清理多餘空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text


def crawl_page(page, url):
    """爬取單一頁面"""
    try:
        print(f"🔍 正在爬取: {url}")
        
        # 訪問頁面
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(2)  # 等待動態內容加載
        
        # 獲取頁面內容
        html = page.content()
        title = page.title()
        content = extract_content(html)
        
        # 保存頁面
        save_page(url, title, content, html)
        
        # 提取連結
        links = extract_links(html, url)
        print(f"📎 發現 {len(links)} 個連結")
        
        # 添加新連結到資料庫
        for link in links:
            add_link(link, url)
        
        # 標記當前頁面為已訪問
        mark_visited(url)
        
        return True
        
    except Exception as e:
        print(f"❌ 爬取失敗 {url}: {e}")
        mark_visited(url)  # 避免重複嘗試失敗的頁面
        return False


def crawl_homepage():
    """爬取主頁並顯示內容"""
    print("=" * 60)
    print("🚀 開始爬取 51.ca 主頁")
    print("=" * 60)
    
    # 初始化資料庫
    init_db()
    
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 爬取主頁
        homepage_url = "https://www.51.ca/"
        add_link(homepage_url, None)
        
        success = crawl_page(page, homepage_url)
        
        if success:
            # 顯示統計
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM links")
            total_links = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM links WHERE visited = 1")
            visited_links = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pages")
            total_pages = cursor.fetchone()[0]
            
            print("\n" + "=" * 60)
            print("📊 爬取統計:")
            print(f"   - 發現連結: {total_links}")
            print(f"   - 已訪問: {visited_links}")
            print(f"   - 已保存頁面: {total_pages}")
            print("=" * 60)
            
            # 顯示部分連結
            cursor.execute("SELECT url FROM links LIMIT 20")
            links = cursor.fetchall()
            print("\n🔗 發現的連結 (前20個):")
            for i, (link,) in enumerate(links, 1):
                print(f"   {i}. {link}")
            
            conn.close()
        
        browser.close()
    
    print("\n✅ 主頁爬取完成！資料已存入 51ca_data.db")


def continue_crawling(max_pages=100):
    """繼續爬取未訪問的頁面"""
    print("=" * 60)
    print(f"🔄 繼續爬取 (最多 {max_pages} 頁)")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        pages_crawled = 0
        
        while pages_crawled < max_pages:
            urls = get_unvisited_links(limit=5)
            
            if not urls:
                print("✅ 沒有更多未訪問的連結")
                break
            
            for url in urls:
                if pages_crawled >= max_pages:
                    break
                    
                crawl_page(page, url)
                pages_crawled += 1
                time.sleep(1)  # 避免過於頻繁的請求
        
        browser.close()
    
    print(f"\n✅ 本次爬取完成！共爬取 {pages_crawled} 頁")


if __name__ == "__main__":
    # 先爬取主頁
    crawl_homepage()
    
    # 如果想繼續爬取更多頁面，取消下面的註釋
    # continue_crawling(max_pages=50)
