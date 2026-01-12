import sqlite3

conn = sqlite3.connect('scrapers/data/51ca.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM house_listings')
print(f'房屋數量: {c.fetchone()[0]}')

c.execute("SELECT COUNT(*) FROM url_queue WHERE visited=0 AND url LIKE '%house.51.ca/rental%'")
print(f'待爬 URL: {c.fetchone()[0]}')

c.execute("SELECT COUNT(*) FROM url_queue WHERE visited=1 AND url LIKE '%house.51.ca/rental%'")
print(f'已爬 URL: {c.fetchone()[0]}')

conn.close()
