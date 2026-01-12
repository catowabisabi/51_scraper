"""
Clean up house URL queue
"""
import sqlite3

db_path = r'c:\Users\Chris\Desktop\app\CICD\HK-Garden-App\51_scraper\scrapers\data\51ca.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Delete API URLs
cursor.execute("DELETE FROM url_queue WHERE url_type = 'house' AND url LIKE '%api%'")
print(f'Deleted {cursor.rowcount} API URLs')

# Mark non-rental URLs as visited
cursor.execute("UPDATE url_queue SET visited = 1 WHERE url_type = 'house' AND url NOT LIKE '%/rental/ontario/%'")
print(f'Marked {cursor.rowcount} non-rental URLs as visited')

conn.commit()

# Check pending
cursor.execute("SELECT COUNT(*) FROM url_queue WHERE url_type = 'house' AND visited = 0")
print(f'Pending rental URLs: {cursor.fetchone()[0]}')

# Check house listings
cursor.execute("SELECT COUNT(*) FROM house_listings")
print(f'Current house listings: {cursor.fetchone()[0]}')

conn.close()
print('Done!')
