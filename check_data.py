# -*- coding: utf-8 -*-
import sqlite3
import re
import sys

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/51ca.db')
cursor = conn.cursor()

print("=" * 60)
print("DATA QUALITY CHECK REPORT")
print("=" * 60)

# 1. News - check for nav menu text
cursor.execute("SELECT title, content FROM news_articles LIMIT 3")
news = cursor.fetchall()
print(f"\n[News Articles]")
nav_issues = 0
for title, content in news:
    has_nav = any(x in (content or '') for x in ['本地要闻', '生活资讯', '热门栏目'])
    if has_nav:
        nav_issues += 1
    status = "BAD" if has_nav else "OK"
    preview = (content or 'N/A')[:80].replace('\n', ' ')
    print(f"  [{status}] {title[:40]}")
    print(f"       Content: {preview}...")
if nav_issues == 0:
    print("  => All clean! No navigation text found.")

# 2. Auto - check for duplicate patterns and static-maps
cursor.execute("SELECT title, make, model, image_urls FROM auto_listings LIMIT 5")
autos = cursor.fetchall()
print(f"\n[Auto Listings]")
auto_issues = 0
for title, make, model, images in autos:
    make_model = f"{make} {model}" if make and model else (make or model or '')
    has_dup = '_车行直卖_' in (title or '') or '_车行直卖_' in make_model
    has_static = 'static-maps' in (images or '')
    if has_dup or has_static:
        auto_issues += 1
    status = "BAD" if (has_dup or has_static) else "OK"
    img_count = len([x for x in (images or '').split(',') if x.strip()]) if images else 0
    print(f"  [{status}] Title: {title}")
    print(f"       Make/Model: {make_model} | Images: {img_count}")
if auto_issues == 0:
    print("  => All clean! No duplicate patterns or static-maps.")

# 3. Service - check for date noise
cursor.execute("SELECT title, content FROM service_posts LIMIT 3")
services = cursor.fetchall()
print(f"\n[Service Posts]")
svc_issues = 0
for title, content in services:
    date_pattern = r'\d{2}\.\d{2}\s+\d{4}'
    dates = re.findall(date_pattern, content or '')
    if len(dates) > 2:
        svc_issues += 1
    status = "BAD" if len(dates) > 2 else "OK"
    preview = (content or 'N/A')[:80].replace('\n', ' ')
    print(f"  [{status}] {title[:40]}")
    print(f"       Content: {preview}...")
if svc_issues == 0:
    print("  => All clean! No excessive date patterns.")

# Summary
print("\n" + "=" * 60)
print("DATA SUMMARY")
print("=" * 60)

tables = [
    ('news_articles', 'News'),
    ('house_listings', 'House'),
    ('job_listings', 'Jobs'),
    ('service_posts', 'Service'),
    ('auto_listings', 'Auto'),
    ('market_posts', 'Market')
]

total = 0
for table, label in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    total += count
    print(f"  {label}: {count}")

print(f"  ----")
print(f"  TOTAL: {total}")

conn.close()
