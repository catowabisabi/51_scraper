# pip install firecrawl-py
from firecrawl import Firecrawl

app = Firecrawl(api_key="fc-cdb52acd54584c5386245d78307dc145")

# Scrape a website:
app.scrape('firecrawl.dev')