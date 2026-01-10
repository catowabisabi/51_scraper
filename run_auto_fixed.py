#!/usr/bin/env python3
"""運行修正後的汽車爬蟲"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

# 導入修正版本
import importlib.util
spec = importlib.util.spec_from_file_location("auto_scraper", "scraper/51_scraper_auto_fixed.py")
auto_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_module)
AutoScraper = auto_module.AutoScraper

def main():
    """運行汽車爬蟲"""
    print("開始運行修正版本的汽車爬蟲...")
    
    try:
        scraper = AutoScraper(headless=True)
        scraper.run_auto_scraper(max_pages=5)
        print("汽車爬蟲運行完成!")
        
        # 檢查更新後的資料
        print("\n檢查更新後的資料...")
        import sqlite3
        conn = sqlite3.connect('data/51ca.db')
        cursor = conn.cursor()
        
        # 檢查NULL值統計
        cursor.execute('SELECT COUNT(*) FROM auto_listings')
        total = cursor.fetchone()[0]
        print(f"總計汽車記錄: {total}")
        
        null_fields = ['listing_type', 'price', 'location', 'post_date', 'vin', 'seller_name']
        for field in null_fields:
            cursor.execute(f'SELECT COUNT(*) FROM auto_listings WHERE {field} IS NOT NULL')
            non_null = cursor.fetchone()[0]
            cursor.execute(f'SELECT COUNT(*) FROM auto_listings WHERE {field} IS NULL')
            null_count = cursor.fetchone()[0]
            print(f"{field}: {non_null} 有值, {null_count} NULL")
        
        # 顯示最新的幾筆資料
        print("\n最新爬取的資料:")
        cursor.execute("""
            SELECT listing_id, title, listing_type, price, location, post_date 
            FROM auto_listings 
            ORDER BY updated_at DESC LIMIT 3
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Title: {row[1]}, Type: {row[2]}, Price: {row[3]}, Location: {row[4]}, Date: {row[5]}")
            
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()