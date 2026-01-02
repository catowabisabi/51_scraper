"""Analyze HTML structure of a 51.ca job page"""
import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.51.ca/jobs/job-posts/1173212'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Fetching:", url)
resp = requests.get(url, headers=headers, timeout=30)
print("Status:", resp.status_code)

soup = BeautifulSoup(resp.text, 'lxml')

print("\n" + "="*60)
print("H1 TAGS AND THEIR STRUCTURE")
print("="*60)
for i, h1 in enumerate(soup.find_all('h1')):
    print("\n[H1 #%d]" % (i+1))
    h1_class = h1.get('class', [])
    print("  class:", h1_class)
    
    # Look for direct text children vs element children
    for child in h1.children:
        if hasattr(child, 'name') and child.name:
            child_class = child.get('class', [])
            child_text = child.get_text()[:50].strip()
            print("  Child element:", child.name, "class=", child_class, "text=", child_text)
        elif isinstance(child, str) and child.strip():
            print("  Direct text:", child.strip()[:50])
    
    if h1.parent:
        print("  parent tag:", h1.parent.name)
        print("  parent class:", h1.parent.get('class', []))

print("\n" + "="*60)
print("LOOKING FOR DETAIL/CONTENT/INTRO DIVS")
print("="*60)
keywords = ['detail', 'content', 'intro', 'description', 'job-desc', 'post-content']
for div in soup.find_all(['div', 'section', 'article']):
    classes = div.get('class', [])
    class_str = ' '.join(classes) if classes else ''
    if any(kw in class_str.lower() for kw in keywords):
        text_preview = ' '.join(div.get_text().split())[:100]
        print("\nClass:", classes)
        print("Tag:", div.name)
        print("Text preview:", text_preview[:80], "...")

print("\n" + "="*60)
print("LOOKING FOR ELEMENTS WITH 'title' IN CLASS")
print("="*60)
for elem in soup.find_all(class_=re.compile(r'title', re.I))[:10]:
    elem_class = elem.get('class', [])
    elem_text = elem.get_text()[:60].strip()
    print("Tag:", elem.name, "Class:", elem_class, "Text:", elem_text)

print("\n" + "="*60)
print("RAW HTML SNIPPET AROUND TITLE")
print("="*60)
html = resp.text
# Find title area
match = re.search(r'<h1[^>]*>(.{0,500})</h1>', html, re.DOTALL)
if match:
    print(match.group(0)[:600])

print("\n" + "="*60)
print("LOOKING FOR DESCRIPTION AREA")
print("="*60)
# Find detail-intro-content or similar
for elem in soup.find_all(class_=re.compile(r'intro|desc|content', re.I)):
    elem_class = elem.get('class', [])
    class_str = ' '.join(elem_class)
    # Skip navigation/header elements
    if any(x in class_str.lower() for x in ['nav', 'header', 'footer', 'menu']):
        continue
    text = elem.get_text()[:150].strip()
    if len(text) > 30:
        print("Class:", elem_class)
        print("Tag:", elem.name)
        print("Text:", text[:100], "...")
        print()

print("\n" + "="*60)
print("RAW HTML SNIPPET AROUND DESCRIPTION")
print("="*60)
# Look for description section
match = re.search(r'详细介绍.{0,50}(<div[^>]*class=[^>]*>[\s\S]{0,800}?</div>)', html)
if match:
    print(match.group(1)[:500])
else:
    # Try finding the job description content directly
    match = re.search(r'美式手抓海鲜.{0,500}', html)
    if match:
        print(match.group(0))
