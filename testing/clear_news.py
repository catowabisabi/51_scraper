"""清除新闻数据并重新爬取"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "scrapers", "data", "51ca.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 清除旧新闻数据
c.execute("DELETE FROM news_articles")
c.execute("DELETE FROM url_queue WHERE url_type='news'")
conn.commit()
print("已清除新聞數據")

conn.close()
