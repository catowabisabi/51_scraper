"""
添加更多數據的簡化版本
"""
import sqlite3
import os

DB_PATH = os.path.join("scrapers", "data", "51ca.db")

def add_more_urls():
    """添加更多起始URL到隊列"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 房屋 - 添加更多頁面
    house_urls = []
    for page in range(6, 21):  # 第6-20頁
        house_urls.extend([
            f"https://house.51.ca/api/v7/property?limit=50&page={page}&transactionType=1",  # 買賣
            f"https://house.51.ca/api/v7/property?limit=50&page={page}&transactionType=2",  # 出租
        ])
    
    # 汽車 - 添加更多車輛ID
    auto_urls = []
    for car_id in range(9900, 10100):  # 更高ID的車輛
        auto_urls.append(f"https://www.51.ca/autos/used-cars/{car_id}")
    
    # 新聞 - 添加更多分類頁面  
    news_urls = [
        "https://info.51.ca/deals",
        "https://info.51.ca/entertainment", 
        "https://info.51.ca/travel",
        "https://info.51.ca/money",
        "https://info.51.ca/shopping",
    ]
    for page in range(2, 11):
        news_urls.extend([
            f"https://info.51.ca/canada?page={page}",
            f"https://info.51.ca/world?page={page}",
            f"https://info.51.ca/china?page={page}",
        ])
    
    # 集市 - 添加不同分類的更多頁面
    market_urls = []
    categories = ['furniture', 'electronics', 'auto-parts', 'books', 'others']
    for cat in categories:
        for page in range(2, 11):
            market_urls.append(f"https://www.51.ca/market/{cat}?page={page}")
    
    # 活動 - 添加更多頁面
    event_urls = []
    for page in range(2, 21):
        event_urls.append(f"https://info.51.ca/events?page={page}")
    
    # 插入URL到隊列
    urls_to_add = [
        ('house', house_urls),
        ('auto', auto_urls), 
        ('news', news_urls),
        ('market', market_urls),
        ('event', event_urls)
    ]
    
    total_added = 0
    for url_type, urls in urls_to_add:
        for url in urls:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO url_queue (url, url_type, priority, source_url)
                    VALUES (?, ?, 5, 'manual_add')
                """, (url, url_type))
                if c.rowcount > 0:
                    total_added += 1
            except:
                pass
    
    conn.commit()
    conn.close()
    print(f"添加了 {total_added} 個新URL到爬取隊列")

if __name__ == "__main__":
    add_more_urls()