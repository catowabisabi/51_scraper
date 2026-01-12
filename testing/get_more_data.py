"""
持續爬取更多數據直到達到目標數量
"""

import subprocess
import sqlite3
import time
import os

DB_PATH = os.path.join("scrapers", "data", "51ca.db")

def get_current_counts():
    """獲取當前數據統計"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    counts = {}
    
    # 房屋
    c.execute("SELECT COUNT(*) FROM house_listings")
    counts['house'] = c.fetchone()[0]
    
    # 汽車
    c.execute("SELECT COUNT(*) FROM auto_listings")
    counts['auto'] = c.fetchone()[0]
    
    # 新聞
    c.execute("SELECT COUNT(*) FROM news_articles")
    counts['news'] = c.fetchone()[0]
    
    # 集市
    c.execute("SELECT COUNT(*) FROM market_posts")
    counts['market'] = c.fetchone()[0]
    
    # 工作
    c.execute("SELECT COUNT(*) FROM jobs")
    counts['jobs'] = c.fetchone()[0]
    
    # 活動
    c.execute("SELECT COUNT(*) FROM events")
    counts['events'] = c.fetchone()[0]
    
    conn.close()
    return counts

def run_scraper_until_target(scraper_name, module, target_count, current_count):
    """運行爬蟲直到達到目標數量"""
    print(f"\n=== {scraper_name} 爬蟲 ===")
    print(f"目標: {target_count}, 當前: {current_count}")
    
    rounds = 0
    while current_count < target_count and rounds < 10:  # 最多10輪防止無限循環
        rounds += 1
        print(f"\n第 {rounds} 輪爬取...")
        
        try:
            result = subprocess.run(['python', '-m', module], 
                                  capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                # 獲取新的數量
                counts = get_current_counts()
                new_count = counts.get(scraper_name.lower().split()[0], current_count)
                added = new_count - current_count
                current_count = new_count
                
                print(f"✅ 完成！新增 {added} 筆，總計 {current_count} 筆")
                
                if added == 0:
                    print("沒有新增數據，停止")
                    break
            else:
                print(f"❌ 錯誤: {result.stderr}")
                break
        except subprocess.TimeoutExpired:
            print("⏰ 超時")
            break
        except Exception as e:
            print(f"❌ 異常: {e}")
            break
    
    return current_count

def main():
    # 目標數量
    targets = {
        'house': 1000,   # 房屋 1000套
        'auto': 1000,    # 汽車 1000輛  
        'news': 500,     # 新聞 500篇
        'market': 1000,  # 集市 1000筆
        'jobs': 1000,    # 工作 1000筆 (已達到)
        'events': 200,   # 活動 200筆
    }
    
    # 爬蟲模組
    modules = {
        'house': 'scrapers.house_scraper',
        'auto': 'scrapers.auto_scraper', 
        'news': 'scrapers.news_scraper',
        'market': 'scrapers.market_scraper',
        'events': 'scrapers.event_scraper'
    }
    
    print("=" * 60)
    print("持續爬取數據直到達到目標")
    print("=" * 60)
    
    current = get_current_counts()
    print(f"\n當前數據量:")
    for name, count in current.items():
        target = targets.get(name, 0)
        print(f"  {name}: {count} / {target}")
    
    # 按需要數量排序，優先爬取差距最大的
    for name in ['house', 'auto', 'market', 'events', 'news']:
        if name not in targets:
            continue
            
        target = targets[name]
        current_count = current.get(name, 0)
        
        if current_count < target:
            current[name] = run_scraper_until_target(
                name.title(), modules[name], target, current_count
            )
    
    # 最終統計
    print("\n" + "=" * 60)
    print("最終數據統計:")
    print("=" * 60)
    subprocess.run(['python', 'check_all_data.py'])

if __name__ == "__main__":
    main()