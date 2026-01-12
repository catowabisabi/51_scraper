"""检查新闻数据"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 查看所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("=== 所有表 ===")
print([r[0] for r in c.fetchall()])

# 检查新闻表是否存在
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_articles'")
if c.fetchone():
    print("\n=== 新闻资料 ===")
    c.execute("SELECT COUNT(*) FROM news_articles")
    print(f"总数: {c.fetchone()[0]}")
    
    # 查看样本数据
    c.execute("""
        SELECT article_id, title, category, publish_date, source, author,
               LENGTH(content) as content_len
        FROM news_articles 
        LIMIT 10
    """)
    print("\n样本数据:")
    for r in c.fetchall():
        print(f"  ID: {r[0]}, 标题: {r[1][:30] if r[1] else None}...")
        print(f"    分类: {r[2]}, 日期: {r[3]}, 来源: {r[4]}, 作者: {r[5]}, 内容长度: {r[6]}")
    
    # 检查空白数据
    c.execute("SELECT COUNT(*) FROM news_articles WHERE content IS NULL OR content = ''")
    empty_content = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM news_articles WHERE title IS NULL OR title = ''")
    empty_title = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM news_articles WHERE publish_date IS NULL")
    empty_date = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM news_articles WHERE source IS NULL")
    empty_source = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM news_articles WHERE author IS NULL")
    empty_author = c.fetchone()[0]
    
    print(f"\n=== 空白数据统计 ===")
    print(f"  空内容: {empty_content}")
    print(f"  空标题: {empty_title}")
    print(f"  空日期: {empty_date}")
    print(f"  空来源: {empty_source}")
    print(f"  空作者: {empty_author}")
    
    # 查看一篇完整内容
    print("\n=== 完整内容样本 ===")
    c.execute("SELECT title, content, author, source, tags FROM news_articles ORDER BY LENGTH(content) DESC LIMIT 1")
    row = c.fetchone()
    if row:
        print(f"标题: {row[0]}")
        print(f"作者: {row[2]}")
        print(f"来源: {row[3]}")
        print(f"标签: {row[4]}")
        print(f"内容 (前500字):\n{row[1][:500]}...")
else:
    print("\n新闻表不存在!")

conn.close()
