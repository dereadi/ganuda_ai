#!/usr/bin/env python3
"""
Download Conde Furniture Website
=================================
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

print("📥 DOWNLOADING CONDE FURNITURE WEBSITE")
print("="*60)

base_url = "https://www.condedfurn.com"
start_url = "https://www.condedfurn.com/Custom/default.htm"

# Create directory
save_dir = "/home/dereadi/scripts/claude/condedfurn_site"
os.makedirs(save_dir, exist_ok=True)

# Headers to bypass protection
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

# Use session to maintain cookies
session = requests.Session()
session.headers.update(headers)

visited = set()
to_visit = [start_url]

def save_page(url, content):
    """Save page content to file"""
    parsed = urlparse(url)
    path = parsed.path if parsed.path else "/index.html"
    if path.endswith('/'):
        path += "index.html"
    
    # Create full file path
    file_path = os.path.join(save_dir, path.lstrip('/'))
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Saved: {path}")
    return file_path

def extract_links(html, base):
    """Extract all links from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for tag in soup.find_all(['a', 'link']):
        href = tag.get('href')
        if href:
            full_url = urljoin(base, href)
            # Only follow internal links
            if full_url.startswith(base_url):
                links.append(full_url)
    
    return links

print(f"Starting download from: {start_url}")
print(f"Saving to: {save_dir}")
print("-"*60)

# Download pages
page_count = 0
while to_visit and page_count < 50:  # Limit to 50 pages
    url = to_visit.pop(0)
    
    if url in visited:
        continue
    
    try:
        print(f"\n📄 Downloading: {url}")
        
        # Get page
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            # Save page
            save_page(url, response.text)
            visited.add(url)
            page_count += 1
            
            # Extract links
            new_links = extract_links(response.text, url)
            for link in new_links:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)
            
            print(f"  Found {len(new_links)} links")
            
        else:
            print(f"  ❌ Status: {response.status_code}")
        
        # Be polite
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*60)
print(f"✅ DOWNLOAD COMPLETE!")
print(f"  Pages downloaded: {page_count}")
print(f"  Saved to: {save_dir}")

# Create index
print("\n📚 Creating index...")

index_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Conde Furniture - Downloaded Site</title>
</head>
<body>
    <h1>Conde Furniture - Downloaded Pages</h1>
    <p>Downloaded {page_count} pages from condedfurn.com</p>
    <h2>Pages:</h2>
    <ul>
"""

for url in sorted(visited):
    path = urlparse(url).path
    index_html += f'        <li><a href=".{path}">{path}</a></li>\n'

index_html += """
    </ul>
</body>
</html>
"""

with open(os.path.join(save_dir, "index.html"), 'w') as f:
    f.write(index_html)

print(f"✅ Index created: {save_dir}/index.html")