"""
51.ca 資料查看器
簡單的 Flask 網頁介面來查看爬取的資料
"""

from flask import Flask, render_template_string, request, jsonify, abort
import sqlite3
import os
import json

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "51ca.db")


def get_connection():
    """獲取資料庫連接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 表格設定 (icon + label)
TABLES = {
    'news_articles': {'icon': '📰', 'label': '新聞文章'},
    'house_listings': {'icon': '🏠', 'label': '房屋列表'},
    'job_listings': {'icon': '💼', 'label': '工作職位'},
    'service_merchants': {'icon': '🏪', 'label': '黃頁商家'},
    'service_posts': {'icon': '📋', 'label': '服務帖子'},
    'market_posts': {'icon': '📦', 'label': '集市帖子'},
    'auto_listings': {'icon': '🚗', 'label': '汽車列表'},
}


def get_stats():
    """獲取資料庫統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    table_stats = {}
    
    for table, meta in TABLES.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            table_stats[table] = {
                'label': meta['label'],
                'icon': meta['icon'],
                'count': cursor.fetchone()[0]
            }
        except:
            table_stats[table] = {
                'label': meta['label'],
                'icon': meta['icon'],
                'count': 0
            }
    
    # URL 隊列統計
    cursor.execute("SELECT COUNT(*) FROM url_queue WHERE visited = 0")
    pending_urls = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM url_queue WHERE visited = 1")
    visited_urls = cursor.fetchone()[0]
    
    conn.close()
    return {
        'tables': table_stats,
        'pending_urls': pending_urls,
        'visited_urls': visited_urls
    }


def get_table_data(table_name, page=1, per_page=20, search=None):
    """獲取表格資料"""
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    # 構建查詢
    if search:
        # 簡單搜索 (搜索 title 或 name 欄位)
        search_cols = {
            'news_articles': 'title',
            'house_listings': 'title',
            'job_listings': 'title',
            'service_merchants': 'name',
            'service_posts': 'title',
            'market_posts': 'title',
            'auto_listings': 'title',
        }
        col = search_cols.get(table_name, 'title')
        cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?",
                       (f"%{search}%", per_page, offset))
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} LIKE ?", (f"%{search}%",))
    else:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset))
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    
    total = cursor.fetchone()[0]
    
    # 重新查詢資料
    if search:
        col = {'news_articles': 'title', 'house_listings': 'title', 'job_listings': 'title',
               'service_merchants': 'name', 'service_posts': 'title', 'market_posts': 'title',
               'auto_listings': 'title'}.get(table_name, 'title')
        cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?",
                       (f"%{search}%", per_page, offset))
    else:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset))
    
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description] if rows else []
    
    data = []
    for row in rows:
        data.append(dict(zip(columns, row)))
    
    conn.close()
    
    return {
        'data': data,
        'columns': columns,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def parse_json_list(value):
    """將資料轉換為列表"""
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [f"{k}: {v}" for k, v in parsed.items()]
        return [str(parsed)]
    except Exception:
        # 逗號分隔的純文字
        if isinstance(value, str) and ',' in value:
            return [item.strip() for item in value.split(',') if item.strip()]
    return [value] if value else []


def format_multiline(text):
    """格式化多行文字"""
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "<br>".join(lines)


def format_currency(value, unit=None):
    """格式化金額"""
    if value in (None, ""):
        return None
    try:
        amount = float(value)
        text = f"${amount:,.0f}"
    except (ValueError, TypeError):
        text = str(value)
    if unit:
        text = f"{text} {unit}"
    return text


def format_number(value, suffix=""):
    """格式化數字"""
    if value in (None, ""):
        return None
    try:
        number = int(value)
        return f"{number:,}{suffix}"
    except (ValueError, TypeError):
        return f"{value}{suffix}"


DETAIL_CONFIG = {
    'news_articles': [
        {
            'title': '文章資訊',
            'columns': 3,
            'fields': [
                {'key': 'category', 'label': '分類'},
                {'key': 'publish_date', 'label': '發布時間'},
                {'key': 'author', 'label': '作者'},
                {'key': 'source', 'label': '來源'},
                {'key': 'comment_count', 'label': '評論數'},
                {'key': 'view_count', 'label': '閱讀數'},
                {'key': 'scraped_at', 'label': '收錄時間'},
            ]
        },
        {
            'title': '摘要',
            'columns': 1,
            'fields': [
                {'key': 'summary', 'label': '摘要', 'type': 'richtext'},
            ]
        },
        {
            'title': '全文內容',
            'columns': 1,
            'fields': [
                {'key': 'content', 'label': '內容', 'type': 'richtext'},
            ]
        },
        {
            'title': '媒體',
            'columns': 1,
            'fields': [
                {'key': 'image_urls', 'label': '圖片', 'type': 'images'},
            ]
        },
    ],
    'house_listings': [
        {
            'title': '房源資訊',
            'columns': 3,
            'fields': [
                {'key': 'title', 'label': '標題'},
                {'key': 'listing_type', 'label': '交易類型'},
                {'key': 'property_type', 'label': '房屋類型'},
                {'key': 'price', 'label': '價格', 'type': 'currency', 'unit_field': 'price_unit'},
                {'key': 'address', 'label': '地址'},
                {'key': 'city', 'label': '城市'},
                {'key': 'community', 'label': '社區'},
                {'key': 'bedrooms', 'label': '臥室'},
                {'key': 'bathrooms', 'label': '浴室'},
                {'key': 'parking', 'label': '車位'},
                {'key': 'sqft', 'label': '面積 (sqft)'},
                {'key': 'scraped_at', 'label': '收錄時間'},
            ]
        },
        {
            'title': '房源描述',
            'columns': 1,
            'fields': [
                {'key': 'description', 'label': '描述', 'type': 'richtext'},
                {'key': 'amenities', 'label': '生活機能', 'type': 'list'},
            ]
        },
        {
            'title': '經紀人資訊',
            'columns': 2,
            'fields': [
                {'key': 'agent_name', 'label': '經紀人'},
                {'key': 'agent_phone', 'label': '電話'},
                {'key': 'agent_company', 'label': '公司'},
            ]
        },
        {
            'title': '媒體',
            'columns': 1,
            'fields': [
                {'key': 'image_urls', 'label': '圖片', 'type': 'images'},
            ]
        },
    ],
    'job_listings': [
        {
            'title': '職位資訊',
            'columns': 3,
            'fields': [
                {'key': 'title', 'label': '職位'},
                {'key': 'company_name', 'label': '公司'},
                {'key': 'location', 'label': '地點'},
                {'key': 'category', 'label': '類別'},
                {'key': 'job_type', 'label': '工作型態'},
                {'key': 'work_period', 'label': '工期'},
                {'key': 'shift', 'label': '班次'},
                {'key': 'salary', 'label': '薪資'},
                {'key': 'salary_unit', 'label': '薪資單位'},
                {'key': 'post_date', 'label': '發布日期'},
            ]
        },
        {
            'title': '職務描述',
            'columns': 1,
            'fields': [
                {'key': 'description', 'label': '描述', 'type': 'richtext'},
            ]
        },
        {
            'title': '要求與福利',
            'columns': 2,
            'fields': [
                {'key': 'requirements', 'label': '應徵條件', 'type': 'list'},
                {'key': 'benefits', 'label': '福利', 'type': 'list'},
            ]
        },
        {
            'title': '聯繫方式',
            'columns': 2,
            'fields': [
                {'key': 'contact_info', 'label': '聯絡資訊'},
                {'key': 'merchant_id', 'label': '商家頁面', 'type': 'merchant_link', 'text': '查看商家'},
            ]
        },
    ],
    'service_merchants': [
        {
            'title': '商家資訊',
            'columns': 3,
            'fields': [
                {'key': 'name', 'label': '商家名稱'},
                {'key': 'english_name', 'label': '英文名稱'},
                {'key': 'category', 'label': '分類'},
                {'key': 'subcategory', 'label': '子分類'},
                {'key': 'phone', 'label': '電話'},
                {'key': 'website', 'label': '網站', 'type': 'link', 'text': '前往網站'},
                {'key': 'address', 'label': '地址'},
            ]
        },
        {
            'title': '服務內容',
            'columns': 2,
            'fields': [
                {'key': 'description', 'label': '描述', 'type': 'richtext'},
                {'key': 'services', 'label': '服務項目', 'type': 'list'},
                {'key': 'business_hours', 'label': '營業時間', 'type': 'richtext'},
            ]
        },
        {
            'title': '媒體',
            'columns': 1,
            'fields': [
                {'key': 'logo_url', 'label': 'Logo', 'type': 'image'},
                {'key': 'image_urls', 'label': '圖片', 'type': 'images'},
            ]
        },
    ],
    'service_posts': [
        {
            'title': '帖子資訊',
            'columns': 3,
            'fields': [
                {'key': 'title', 'label': '標題'},
                {'key': 'category', 'label': '分類'},
                {'key': 'subcategory', 'label': '子分類'},
                {'key': 'price', 'label': '價格'},
                {'key': 'location', 'label': '位置'},
                {'key': 'contact_phone', 'label': '電話'},
                {'key': 'merchant_id', 'label': '商家 ID'},
            ]
        },
        {
            'title': '服務內容',
            'columns': 1,
            'fields': [
                {'key': 'content', 'label': '內容', 'type': 'richtext'},
            ]
        },
        {
            'title': '媒體',
            'columns': 1,
            'fields': [
                {'key': 'image_urls', 'label': '圖片', 'type': 'images'},
            ]
        },
    ],
    'market_posts': [
        {
            'title': '商品資訊',
            'columns': 3,
            'fields': [
                {'key': 'title', 'label': '標題'},
                {'key': 'category', 'label': '分類'},
                {'key': 'price', 'label': '價格', 'type': 'currency'},
                {'key': 'original_price', 'label': '原價', 'type': 'currency'},
                {'key': 'condition', 'label': '物品狀態'},
                {'key': 'location', 'label': '位置'},
                {'key': 'contact_info', 'label': '聯繫方式'},
                {'key': 'post_date', 'label': '發布日期'},
                {'key': 'view_count', 'label': '瀏覽次數'},
            ]
        },
        {
            'title': '商品描述',
            'columns': 1,
            'fields': [
                {'key': 'description', 'label': '描述', 'type': 'richtext'},
            ]
        },
        {
            'title': '媒體',
            'columns': 1,
            'fields': [
                {'key': 'image_urls', 'label': '圖片', 'type': 'images'},
            ]
        },
    ],
    'auto_listings': [
        {
            'title': '車輛概覽',
            'columns': 3,
            'fields': [
                {'key': 'title', 'label': '標題'},
                {'key': 'listing_type', 'label': '類型'},
                {'key': 'year', 'label': '年份'},
                {'key': 'make', 'label': '品牌'},
                {'key': 'model', 'label': '型號'},
                {'key': 'body_type', 'label': '車身'},
                {'key': 'price', 'label': '價格', 'type': 'currency'},
                {'key': 'mileage', 'label': '里程', 'type': 'number', 'suffix': ' km'},
                {'key': 'transmission', 'label': '變速箱'},
                {'key': 'fuel_type', 'label': '燃料'},
                {'key': 'color', 'label': '顏色'},
                {'key': 'location', 'label': '位置'},
            ]
        },
        {
            'title': '車輛細節',
            'columns': 2,
            'fields': [
                {'key': 'vin', 'label': 'VIN'},
                {'key': 'features', 'label': '配備', 'type': 'list'},
                {'key': 'description', 'label': '描述', 'type': 'richtext'},
            ]
        },
        {
            'title': '賣家資訊',
            'columns': 2,
            'fields': [
                {'key': 'seller_type', 'label': '賣家類型'},
                {'key': 'seller_name', 'label': '賣家'},
                {'key': 'contact_phone', 'label': '電話'},
            ]
        },
        {
            'title': '媒體',
            'columns': 1,
            'fields': [
                {'key': 'image_urls', 'label': '圖片', 'type': 'images'},
            ]
        },
    ],
}


def prepare_field(record: dict, field: dict) -> dict:
    """根據設定準備欄位資料"""
    field_type = field.get('type', 'text')
    key = field.get('key')
    raw_value = record.get(key)

    if field_type == 'currency':
        unit = record.get(field.get('unit_field')) if field.get('unit_field') else field.get('unit')
        value = format_currency(raw_value, unit)
        field_type = 'text'
    elif field_type == 'number':
        value = format_number(raw_value, field.get('suffix', ''))
        field_type = 'text'
    elif field_type == 'list':
        value = parse_json_list(raw_value)
    elif field_type == 'richtext':
        value = format_multiline(raw_value)
    elif field_type == 'images':
        value = parse_json_list(raw_value)
    elif field_type == 'image':
        value = [raw_value] if raw_value else []
        field_type = 'images'
    elif field_type == 'link':
        link_url = raw_value or record.get(field.get('fallback_key', 'url'))
        value = {'url': link_url, 'text': field.get('text') or link_url}
    elif field_type == 'merchant_link':
        # 連結到本地商家詳情頁
        merchant_id = raw_value
        if merchant_id:
            # 從 service_merchants 找到對應的 id
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM service_merchants WHERE merchant_id = ?", (str(merchant_id),))
            merchant = cursor.fetchone()
            conn.close()
            if merchant:
                value = {'url': f'/detail/service_merchants/{merchant[0]}', 'text': merchant[1] or field.get('text', '查看商家')}
            else:
                value = None
        else:
            value = None
        field_type = 'link'
    else:
        value = raw_value

    if field_type == 'text' and (value is None or value == ''):
        value = '-'
    if field_type in ('list', 'images') and not value:
        value = []
    if field_type == 'richtext' and not value:
        value = '<span class="empty">尚無內容</span>'
    if field_type == 'link' and (not value or not value.get('url')):
        value = None

    return {
        'label': field.get('label'),
        'type': field_type,
        'value': value,
    }


def build_detail_sections(table_name: str, record: dict) -> list:
    """組裝詳情頁區塊"""
    sections = []
    for section in DETAIL_CONFIG.get(table_name, []):
        prepared_fields = [prepare_field(record, field) for field in section['fields']]
        sections.append({
            'title': section['title'],
            'columns': section.get('columns', 2),
            'fields': prepared_fields
        })
    return sections


def get_record(table_name: str, record_id: int) -> dict | None:
    """取得單筆資料"""
    if table_name not in TABLES:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def build_meta(record: dict) -> list:
    """建立頂部統計資訊"""
    meta = []
    meta.append({'label': '資料 ID', 'value': record.get('id')})
    if record.get('scraped_at'):
        meta.append({'label': '收錄時間', 'value': record.get('scraped_at')})
    if record.get('updated_at'):
        meta.append({'label': '最後更新', 'value': record.get('updated_at')})
    if record.get('url'):
        meta.append({'label': '原始頁面', 'type': 'link', 'value': {'url': record['url'], 'text': '開啟 51.ca'}})
    return meta


# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>51.ca 資料查看器</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; margin-bottom: 30px; border-radius: 10px; }
        header h1 { font-size: 2em; margin-bottom: 10px; }
        header p { opacity: 0.9; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .stat-card:hover { transform: translateY(-5px); box-shadow: 0 5px 20px rgba(0,0,0,0.15); }
        .stat-card.active { border: 2px solid #667eea; }
        .stat-icon { font-size: 2em; margin-bottom: 10px; }
        .stat-count { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-name { color: #666; margin-top: 5px; }
        
        .data-section { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; }
        .data-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
        .data-title { font-size: 1.5em; color: #333; }
        
        .search-box { display: flex; gap: 10px; }
        .search-box input { padding: 10px 15px; border: 1px solid #ddd; border-radius: 5px; width: 250px; }
        .search-box button { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .search-box button:hover { background: #5a6fd6; }

        .detail-btn { padding: 6px 12px; border-radius: 999px; border: none; background: #f97316; color: #fff; font-size: 12px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .detail-btn:hover { transform: translateY(-1px); box-shadow: 0 3px 8px rgba(249,115,22,0.4); }
        
        .table-container { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; color: #555; position: sticky; top: 0; }
        tr:hover { background: #f8f9fa; }
        td { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        td a { color: #667eea; text-decoration: none; }
        td a:hover { text-decoration: underline; }
        
        .pagination { display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 20px; }
        .pagination button { padding: 8px 15px; border: 1px solid #ddd; background: white; border-radius: 5px; cursor: pointer; }
        .pagination button:hover { background: #f0f0f0; }
        .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
        .pagination span { color: #666; }
        
        .empty-state { text-align: center; padding: 50px; color: #999; }
        .empty-state .icon { font-size: 4em; margin-bottom: 20px; }
        
        .url-stats { display: flex; gap: 20px; margin-top: 20px; justify-content: center; }
        .url-stat { background: #f8f9fa; padding: 10px 20px; border-radius: 5px; }
        
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .search-box input { width: 150px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 51.ca 資料查看器</h1>
            <p>查看爬取的新聞、房屋、工作、汽車等資料</p>
        </header>
        
        <div class="stats-grid">
            {% for table, info in table_stats.items() %}
            <div class="stat-card {% if current_table == table %}active{% endif %}" onclick="loadTable('{{ table }}')">
                <div class="stat-icon">{{ info.icon }}</div>
                <div class="stat-count">{{ info.count }}</div>
                <div class="stat-name">{{ info.label }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="url-stats">
            <div class="url-stat">⏳ 待爬取: <strong>{{ pending_urls }}</strong></div>
            <div class="url-stat">✅ 已爬取: <strong>{{ visited_urls }}</strong></div>
        </div>
        
        <div class="data-section" style="margin-top: 30px;">
            <div class="data-header">
                <h2 class="data-title" id="table-title">{{ table_info.label if table_info else '選擇一個資料表' }}</h2>
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="搜索..." value="{{ search or '' }}">
                    <button onclick="doSearch()">搜索</button>
                </div>
            </div>
            
            <div class="table-container">
                {% if table_data and table_data.data %}
                <table>
                    <thead>
                        <tr>
                            <th>詳情</th>
                            {% for col in table_data.columns[:10] %}
                            <th>{{ col }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in table_data.data %}
                        <tr>
                            <td>
                                {% if row['id'] %}
                                <button class="detail-btn" onclick="viewDetail({{ row['id'] }})">查看詳情</button>
                                {% else %}
                                -
                                {% endif %}
                            </td>
                            {% for col in table_data.columns[:10] %}
                            <td>
                                {% if col == 'url' and row[col] %}
                                <a href="{{ row[col] }}" target="_blank">🔗 查看</a>
                                {% elif row[col] is not none %}
                                {{ row[col]|string|truncate(100, True, '...') }}
                                {% else %}
                                -
                                {% endif %}
                            </td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <div class="pagination">
                    <button onclick="changePage({{ table_data.page - 1 }})" {% if table_data.page <= 1 %}disabled{% endif %}>上一頁</button>
                    <span>第 {{ table_data.page }} / {{ table_data.total_pages }} 頁 (共 {{ table_data.total }} 條)</span>
                    <button onclick="changePage({{ table_data.page + 1 }})" {% if table_data.page >= table_data.total_pages %}disabled{% endif %}>下一頁</button>
                </div>
                {% else %}
                <div class="empty-state">
                    <div class="icon">📭</div>
                    <p>暫無資料，請選擇一個資料表或使用搜索</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
        const currentTable = '{{ current_table or "" }}';
        
        function loadTable(table) {
            window.location.href = '/?table=' + table;
        }
        
        function viewDetail(id) {
            if (!id || !currentTable) return;
            window.open('/detail/' + currentTable + '/' + id, '_blank');
        }

        function changePage(page) {
            const search = document.getElementById('search-input').value;
            let url = '/?table=' + currentTable + '&page=' + page;
            if (search) url += '&search=' + encodeURIComponent(search);
            window.location.href = url;
        }
        
        function doSearch() {
            const search = document.getElementById('search-input').value;
            let url = '/?table=' + (currentTable || 'news_articles') + '&page=1';
            if (search) url += '&search=' + encodeURIComponent(search);
            window.location.href = url;
        }
        
        document.getElementById('search-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') doSearch();
        });
    </script>
</body>
</html>
'''


DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ table_label }} - 詳情</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: 'Segoe UI', 'Noto Sans TC', sans-serif; background: radial-gradient(circle at top, #0ea5e9 0%, #0f172a 55%, #020617 100%); color: #e2e8f0; min-height: 100vh; }
        a { color: inherit; }
        .detail-wrapper { max-width: 1100px; margin: 0 auto; padding: 40px 24px 80px; }
        .detail-hero { background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 24px; padding: 32px; display: flex; flex-wrap: wrap; gap: 24px; align-items: center; box-shadow: 0 30px 120px rgba(14, 165, 233, 0.15); }
        .hero-icon { font-size: 48px; background: rgba(14,165,233,0.2); padding: 18px; border-radius: 20px; }
        .hero-text h1 { margin: 0 0 8px; font-size: 32px; line-height: 1.2; color: #f8fafc; }
        .hero-text p { margin: 0; color: #94a3b8; letter-spacing: 0.3em; text-transform: uppercase; font-size: 12px; }
        .hero-meta { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 12px; }
        .hero-meta span { background: rgba(148,163,184,0.15); padding: 6px 14px; border-radius: 999px; font-size: 12px; }
        .hero-actions { margin-left: auto; display: flex; flex-wrap: wrap; gap: 12px; }
        .hero-actions a, .hero-actions button { border: none; border-radius: 999px; padding: 10px 20px; cursor: pointer; font-weight: 600; letter-spacing: 0.04em; }
        .hero-actions button { background: linear-gradient(120deg, #f97316, #fb923c); color: #0f172a; }
        .hero-actions a { text-decoration: none; border: 1px solid rgba(248, 250, 252, 0.3); color: #f8fafc; background: transparent; }
        .meta-grid { margin-top: 24px; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
        .meta-card { background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 18px; }
        .meta-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.2em; color: #94a3b8; }
        .meta-card p { margin: 6px 0 0; font-size: 16px; color: #f8fafc; }
        .detail-section { margin-top: 32px; background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(148,163,184,0.25); border-radius: 20px; padding: 24px; box-shadow: inset 0 0 0 1px rgba(148,163,184,0.05); }
        .section-header h2 { margin: 0; font-size: 20px; letter-spacing: 0.08em; text-transform: uppercase; color: #38bdf8; }
        .field-grid { margin-top: 20px; display: grid; gap: 16px; }
        .field-grid.columns-1 { grid-template-columns: 1fr; }
        .field-grid.columns-2 { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
        .field-grid.columns-3 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        .info-card { background: rgba(15,23,42,0.8); border: 1px solid rgba(30,41,59,0.9); border-radius: 16px; padding: 16px 18px; min-height: 110px; display: flex; flex-direction: column; gap: 10px; }
        .field-label { font-size: 12px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.2em; }
        .info-card p { margin: 0; font-size: 16px; color: #f8fafc; line-height: 1.4; }
        .chip-row { display: flex; flex-wrap: wrap; gap: 8px; }
        .chip { padding: 6px 12px; border-radius: 999px; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.4); font-size: 12px; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
        .image-grid img { width: 100%; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); object-fit: cover; max-height: 160px; }
        .rich-text { color: #e2e8f0; line-height: 1.6; font-size: 15px; }
        .rich-text br { content: ""; display: block; margin-bottom: 6px; }
        .empty { color: #475569; font-style: italic; }
        @media (max-width: 768px) {
            .detail-hero { flex-direction: column; align-items: flex-start; }
            .hero-actions { width: 100%; }
            .hero-actions button, .hero-actions a { flex: 1; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="detail-wrapper">
        <header class="detail-hero">
            <div class="hero-icon">{{ table_icon }}</div>
            <div class="hero-text">
                <p>{{ table_label }}</p>
                <h1>{{ hero_title }}</h1>
                <div class="hero-meta">
                    <span>ID #{{ record.id }}</span>
                    {% if record.scraped_at %}<span>收錄於 {{ record.scraped_at }}</span>{% endif %}
                    {% if record.updated_at %}<span>更新於 {{ record.updated_at }}</span>{% endif %}
                </div>
            </div>
            <div class="hero-actions">
                <button onclick="window.location.href='/?table={{ table_key }}'">返回列表</button>
                {% if record.url %}
                <a href="{{ record.url }}" target="_blank">開啟原文</a>
                {% endif %}
            </div>
        </header>
        <section class="meta-grid">
            {% for item in meta %}
            <div class="meta-card">
                <span class="meta-label">{{ item.label }}</span>
                {% if item.type == 'link' and item.value %}
                <p><a href="{{ item.value.url }}" target="_blank">{{ item.value.text }}</a></p>
                {% else %}
                <p>{{ item.value or '-' }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </section>
        {% for section in sections %}
        <section class="detail-section">
            <div class="section-header">
                <h2>{{ section.title }}</h2>
            </div>
            <div class="field-grid columns-{{ section.columns }}">
                {% for field in section.fields %}
                <div class="info-card">
                    <span class="field-label">{{ field.label }}</span>
                    {% if field.type == 'list' %}
                        {% if field.value %}
                        <div class="chip-row">
                            {% for item in field.value %}
                            <span class="chip">{{ item }}</span>
                            {% endfor %}
                        </div>
                        {% else %}
                        <p class="empty">尚無資料</p>
                        {% endif %}
                    {% elif field.type == 'images' %}
                        {% if field.value %}
                        <div class="image-grid">
                            {% for img in field.value %}
                            <a href="{{ img }}" target="_blank"><img src="{{ img }}" alt="image" loading="lazy"></a>
                            {% endfor %}
                        </div>
                        {% else %}
                        <p class="empty">尚無圖片</p>
                        {% endif %}
                    {% elif field.type == 'richtext' %}
                        <div class="rich-text">{{ field.value|safe }}</div>
                    {% elif field.type == 'link' and field.value %}
                        <a href="{{ field.value.url }}" target="_blank">{{ field.value.text }}</a>
                    {% else %}
                        <p>{{ field.value }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </section>
        {% endfor %}
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    """首頁"""
    stats = get_stats()
    current_table = request.args.get('table', 'news_articles')
    if current_table not in TABLES:
        current_table = 'news_articles'
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    
    table_data = None
    table_info = None
    
    if current_table:
        table_data = get_table_data(current_table, page, 20, search if search else None)
        table_info = stats['tables'].get(current_table, {})
    
    return render_template_string(
        HTML_TEMPLATE,
        table_stats=stats['tables'],
        pending_urls=stats['pending_urls'],
        visited_urls=stats['visited_urls'],
        current_table=current_table,
        table_data=table_data,
        table_info=table_info,
        search=search
    )


@app.route('/detail/<table_name>/<int:record_id>')
def detail_view(table_name: str, record_id: int):
    """詳情頁面"""
    if table_name not in TABLES:
        abort(404)
    record = get_record(table_name, record_id)
    if not record:
        abort(404)
    sections = build_detail_sections(table_name, record)
    meta = build_meta(record)
    hero_title = record.get('title') or record.get('name') or record.get('company_name') or record.get('merchant_id') or f"{TABLES[table_name]['label']} #{record_id}"
    return render_template_string(
        DETAIL_TEMPLATE,
        table_key=table_name,
        table_label=TABLES[table_name]['label'],
        table_icon=TABLES[table_name]['icon'],
        hero_title=hero_title,
        record=record,
        sections=sections,
        meta=meta
    )


@app.route('/api/stats')
def api_stats():
    """API: 獲取統計"""
    return jsonify(get_stats())


@app.route('/api/table/<table_name>')
def api_table(table_name):
    """API: 獲取表格資料"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', None)
    
    return jsonify(get_table_data(table_name, page, per_page, search))


if __name__ == '__main__':
    print("=" * 60)
    print("📊 51.ca 資料查看器")
    print("=" * 60)
    
    # 顯示統計
    stats = get_stats()
    total = 0
    for table, info in stats['tables'].items():
        print(f"  {info['icon']} {info['label']}: {info['count']}")
        total += info['count']
    
    print("-" * 60)
    print(f"  📈 總計資料: {total}")
    print(f"  ⏳ 待爬取URL: {stats['pending_urls']}")
    print(f"  ✅ 已爬取URL: {stats['visited_urls']}")
    print("=" * 60)
    print()
    print("🌐 啟動網頁伺服器...")
    print("   打開瀏覽器訪問: http://127.0.0.1:5000")
    print()
    
    app.run(debug=True, port=5000)
