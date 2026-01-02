"""
清理商家數據 - 修復地址和描述中的冗餘文字
"""
import sqlite3
import re
from urllib.parse import unquote

DB_PATH = '../data/51ca.db'

def clean_address(addr: str) -> str:
    """清理地址中的冗餘文字"""
    if not addr:
        return addr
    
    # 移除「查看路線」「聯繫電話」等冗餘文字
    addr = re.sub(r'\s*查看路[线線]\s*', '', addr)
    addr = re.sub(r'\s*[联聯]系[电電][话話].*$', '', addr)
    addr = re.sub(r'\s*移[动動][电電][话話].*$', '', addr)
    addr = re.sub(r'\s*[电電]子[邮郵]箱.*$', '', addr)
    
    # 移除公司/聯繫人名字 (地址前的非地址文字，找到數字地址開始)
    # 格式: "xxx某人名xxx 123 Street, City, ON M1M1M1"
    street_match = re.search(r'(\d+\s+[\w\s\']+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Lane|Ln|Highway|Hwy|Crescent|Cres|Place|Pl|Unit|#)[,.\s].+)', addr, re.I)
    if street_match:
        addr = street_match.group(1).strip()
    else:
        # 嘗試匹配 ", City, ON M1M1M1" 格式
        city_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?[,\s]+(?:ON|BC|AB|QC|MB|SK|NS|NB|PE|NL|YT|NT|NU)\s+[A-Z]\d[A-Z]\s*\d[A-Z]\d)', addr, re.I)
        if city_match:
            addr = city_match.group(1).strip()
    
    # 清理多餘空白和逗號
    addr = re.sub(r'\s+', ' ', addr).strip()
    addr = addr.strip(',').strip()
    return addr

def clean_description(desc: str) -> str:
    """清理描述中的冗餘前綴"""
    if not desc:
        return desc
    
    # 移除「最新動態 更多動態」前綴
    desc = re.sub(r'^最新[动動][态態]\s*更多[动動][态態]\s*', '', desc)
    # 移除「公司介紹」標題
    desc = re.sub(r'^公司介[绍紹]\s*', '', desc)
    # 清理多餘空白
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('=== 清理商家數據 ===')
    
    # 獲取所有商家
    c.execute('SELECT merchant_id, name, address, description FROM service_merchants')
    merchants = c.fetchall()
    
    addr_cleaned = 0
    desc_cleaned = 0
    
    for mid, name, addr, desc in merchants:
        new_addr = clean_address(addr) if addr else None
        new_desc = clean_description(desc) if desc else None
        
        updates = []
        params = []
        
        if addr and new_addr != addr:
            updates.append('address = ?')
            params.append(new_addr)
            addr_cleaned += 1
        
        if desc and new_desc != desc:
            updates.append('description = ?')
            params.append(new_desc)
            desc_cleaned += 1
        
        if updates:
            params.append(mid)
            sql = f"UPDATE service_merchants SET {', '.join(updates)} WHERE merchant_id = ?"
            c.execute(sql, params)
    
    conn.commit()
    
    print(f'已清理 {addr_cleaned} 個地址')
    print(f'已清理 {desc_cleaned} 個描述')
    
    # 顯示清理後的樣本
    print('\n=== 清理後的地址樣本 ===')
    c.execute("SELECT name, address FROM service_merchants WHERE address IS NOT NULL AND address != '' LIMIT 5")
    for row in c.fetchall():
        name = row[0][:20] if row[0] else 'N/A'
        addr = row[1][:80] if row[1] else 'N/A'
        print(f'  {name}: {addr}')
    
    print('\n=== 清理後的描述樣本 ===')
    c.execute("SELECT name, description FROM service_merchants WHERE description IS NOT NULL AND description != '' LIMIT 3")
    for row in c.fetchall():
        name = row[0][:20] if row[0] else 'N/A'
        desc = row[1][:100] if row[1] else 'N/A'
        print(f'  {name}: {desc}...')
    
    conn.close()
    print('\n清理完成!')

if __name__ == '__main__':
    main()
