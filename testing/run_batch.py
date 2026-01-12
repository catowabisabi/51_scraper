"""
批量運行爬蟲 - 增強版
每個爬蟲單獨運行，更穩健的錯誤處理
"""

import subprocess
import sys
import os
from datetime import datetime

def run_scraper(name: str, command: list, timeout: int = 3600):
    """運行單個爬蟲"""
    print(f"\n{'=' * 60}")
    print(f"開始運行: {name}")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            command,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=timeout,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {name} 完成!")
            return True
        else:
            print(f"❌ {name} 失敗 (返回碼: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {name} 超時!")
        return False
    except Exception as e:
        print(f"❌ {name} 錯誤: {e}")
        return False


def main():
    """運行所有爬蟲"""
    print("=" * 60)
    print(f"開始批量爬取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # 爬蟲配置: (名稱, 命令, 超時秒數)
    scrapers = [
        # 新聞爬蟲 - 200頁約需15分鐘
        ("新聞", [sys.executable, "-m", "scrapers.news_scraper"], 1800),
        
        # 工作爬蟲 - 1000個約需30分鐘 
        ("工作", [sys.executable, "-m", "scrapers.jobs_scraper", "--max-jobs", "1000"], 3600),
        
        # 房屋爬蟲
        ("房屋", [sys.executable, "-m", "scrapers.house_scraper"], 1800),
        
        # 集市爬蟲  
        ("集市", [sys.executable, "-m", "scrapers.market_scraper"], 1800),
        
        # 汽車爬蟲
        ("汽車", [sys.executable, "-m", "scrapers.auto_scraper"], 1800),
        
        # 活動爬蟲
        ("活動", [sys.executable, "-m", "scrapers.event_scraper"], 1800),
    ]
    
    for name, command, timeout in scrapers:
        success = run_scraper(name, command, timeout)
        results[name] = "成功" if success else "失敗"
    
    # 打印總結
    print("\n" + "=" * 60)
    print("批量爬取完成!")
    print("=" * 60)
    
    for name, status in results.items():
        emoji = "✅" if status == "成功" else "❌"
        print(f"  {emoji} {name}: {status}")
    
    # 運行統計腳本
    print("\n" + "=" * 60)
    print("最終數據統計:")
    print("=" * 60)
    subprocess.run([sys.executable, "check_all_data.py"], 
                   cwd=os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    main()
