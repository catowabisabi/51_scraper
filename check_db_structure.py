#!/usr/bin/env python3
"""檢查51ca.db的資料庫結構"""

import sqlite3
import os

# 設定資料庫路徑
db_path = os.path.join(os.path.dirname(__file__), 'data', '51ca.db')

if not os.path.exists(db_path):
    print(f"資料庫檔案不存在: {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 取得所有表格
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("51ca.db 資料庫結構:")
    print("=" * 50)
    
    for table in tables:
        table_name = table[0]
        print(f"\n表格: {table_name}")
        print("-" * 30)
        
        # 取得表格結構
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_nullable = "NOT NULL" if col[3] else "NULL"
            print(f"  {col_name:20} {col_type:15} {is_nullable}")
        
        # 取得資料數量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  總計: {count} 筆資料")
        
        # 如果是auto_listings表格，檢查NULL值
        if table_name == 'auto_listings':
            print(f"\n{table_name} NULL值統計:")
            for col in columns:
                col_name = col[1]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                null_count = cursor.fetchone()[0]
                if null_count > 0:
                    print(f"  {col_name}: {null_count} 個NULL值")
    
    conn.close()
    
except Exception as e:
    print(f"錯誤: {e}")