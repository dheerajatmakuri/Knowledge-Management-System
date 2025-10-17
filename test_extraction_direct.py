"""
Simple test to verify extraction directly with full HTML
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Simulate the extraction
url = 'https://amzur.com/leadership-team/'
headers = {'User-Agent': 'Mozilla/5.0'}

print("Fetching Amzur leadership page...")
response = requests.get(url, headers=headers)
html = response.text
soup = BeautifulSoup(html, 'html.parser')

print(f"HTML length: {len(html)} chars")
print(f"Total <a> tags: {len(soup.find_all('a'))}")

# Strategy 0 logic
print("\n" + "="*80)
print("STRATEGY 0: Link-based extraction")
print("="*80)

leadership_links = []
for link in soup.find_all('a', href=True):
    href = link.get('href', '')
    link_text = link.get_text().strip()
    
    # Convert relative URLs to absolute
    full_href = urljoin(url, href)
    
    # Check if link goes to individual leadership profile
    if '/leadership/' in full_href.lower():
        # Must have individual profile structure
        if full_href.count('/') >= 4:
            # Check if link text looks like a name (simple validation)
            words = link_text.split()
            if 2 <= len(words) <= 5 and link_text[0].isupper():
                leadership_links.append({
                    'name': link_text,
                    'url': full_href
                })

print(f"\n✅ Found {len(leadership_links)} leadership profile links:\n")
for i, lnk in enumerate(leadership_links, 1):
    print(f"{i:2}. {lnk['name']:30} -> {lnk['url']}")

if len(leadership_links) > 0:
    print(f"\n🎉 SUCCESS! Extraction should work!")
    
    # Try to get images
    print(f"\n📸 Checking for images...")
    first_leader = leadership_links[0]
    
    # Find the link element again
    for link in soup.find_all('a', href=True):
        if first_leader['url'] in link.get('href', ''):
            # Find parent
            parent = link.find_parent(['div', 'article'])
            if parent:
                img = parent.find('img')
                if img:
                    img_src = img.get('src')
                    print(f"✅ Found image for {first_leader['name']}: {img_src[:60]}...")
                else:
                    print(f"⚠️ No image found in parent for {first_leader['name']}")
            break
else:
    print("\n❌ No links found - extraction will fail")
    
    # Debug: Show all links with /leadership/
    print("\nDEBUG: All links containing '/leadership/':")
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if '/leadership/' in href.lower():
            print(f"  - {link.get_text().strip()[:40]:40} -> {href}")
