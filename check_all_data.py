"""
查看數據庫中所有爬蟲的數據統計
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

def check_all_data():
    """檢查所有數據"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=" * 60)
    print(f"51.ca 數據庫統計 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 獲取所有表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    
    # 統計每個表的數據
    stats = {}
    
    # 新聞
    if 'news_articles' in tables:
        c.execute("SELECT COUNT(*) FROM news_articles")
        count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM news_articles WHERE content IS NOT NULL AND LENGTH(content) > 100")
        with_content = c.fetchone()[0]
        stats['新聞 (news_articles)'] = f"{count} 篇 (有內容: {with_content})"
    
    # 房屋
    if 'house_listings' in tables:
        c.execute("SELECT COUNT(*) FROM house_listings")
        count = c.fetchone()[0]
        stats['房屋 (house_listings)'] = f"{count} 筆"
    
    # 工作
    if 'jobs' in tables:
        c.execute("SELECT COUNT(*) FROM jobs")
        count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM jobs WHERE phone IS NOT NULL AND phone != ''")
        with_phone = c.fetchone()[0]
        stats['工作 (jobs)'] = f"{count} 筆 (有電話: {with_phone})"
    
    # 舊工作表
    if 'job_listings' in tables:
        c.execute("SELECT COUNT(*) FROM job_listings")
        count = c.fetchone()[0]
        stats['工作舊表 (job_listings)'] = f"{count} 筆"
    
    # 集市
    if 'market_posts' in tables:
        c.execute("SELECT COUNT(*) FROM market_posts")
        count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM market_posts WHERE contact_phone IS NOT NULL AND contact_phone != ''")
        with_phone = c.fetchone()[0]
        stats['集市 (market_posts)'] = f"{count} 筆 (有電話: {with_phone})"
    
    # 汽車
    if 'auto_listings' in tables:
        c.execute("SELECT COUNT(*) FROM auto_listings")
        count = c.fetchone()[0]
        stats['汽車 (auto_listings)'] = f"{count} 筆"
    
    # 活動
    if 'events' in tables:
        c.execute("SELECT COUNT(*) FROM events")
        count = c.fetchone()[0]
        stats['活動 (events)'] = f"{count} 筆"
    
    # 商戶
    if 'merchants' in tables:
        c.execute("SELECT COUNT(*) FROM merchants")
        count = c.fetchone()[0]
        stats['商戶 (merchants)'] = f"{count} 筆"
    
    # 服務
    if 'service_posts' in tables:
        c.execute("SELECT COUNT(*) FROM service_posts")
        count = c.fetchone()[0]
        stats['服務 (service_posts)'] = f"{count} 筆"
    
    # 打印統計
    print("\n數據統計:")
    print("-" * 40)
    for name, value in stats.items():
        print(f"  {name}: {value}")
    
    # URL 隊列統計
    if 'url_queue' in tables:
        print("\n" + "-" * 40)
        print("URL 隊列統計:")
        c.execute("""
            SELECT url_type, 
                   SUM(CASE WHEN visited = 1 THEN 1 ELSE 0 END) as visited,
                   SUM(CASE WHEN visited = 0 THEN 1 ELSE 0 END) as pending
            FROM url_queue 
            GROUP BY url_type
        """)
        for row in c.fetchall():
            print(f"  {row[0]}: 已訪問={row[1]}, 待處理={row[2]}")
    
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    check_all_data()
