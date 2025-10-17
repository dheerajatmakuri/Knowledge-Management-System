"""Debug script to analyze Amzur leadership page structure"""

import requests
from bs4 import BeautifulSoup

url = 'https://amzur.com/leadership-team/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print(f"Fetching: {url}\n")
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

print("="*80)
print("PAGE STRUCTURE ANALYSIS")
print("="*80)

# 1. Check page title
print(f"\n1. PAGE TITLE: {soup.title.string if soup.title else 'No title'}")

# 2. Find all <a> tags with leadership links
print(f"\n2. LEADERSHIP PROFILE LINKS:")
leader_links = []
for link in soup.find_all('a', href=True):
    href = link.get('href', '')
    if '/leadership/' in href and href.count('/') > 2:
        text = link.get_text().strip()
        if text:
            leader_links.append((text, href))
            
print(f"Found {len(leader_links)} individual leader profile links:")
for i, (text, href) in enumerate(leader_links[:10], 1):
    print(f"  {i}. {text[:40]:<40} -> {href}")

# 3. Find sections with leader/team/profile classes
print(f"\n3. SECTIONS WITH LEADERSHIP CLASSES:")
sections = soup.find_all(['div', 'section', 'article'], class_=lambda x: x and any(
    k in str(x).lower() for k in ['leader', 'team', 'profile', 'member', 'executive', 'staff']
))
print(f"Found {len(sections)} sections")
for i, section in enumerate(sections[:5], 1):
    classes = ' '.join(section.get('class', []))
    print(f"  {i}. <{section.name}> class='{classes[:60]}'")

# 4. Find headings that might be names
print(f"\n4. HEADINGS (potential names):")
headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
name_headings = []
for h in headings:
    text = h.get_text().strip()
    words = text.split()
    # Name-like: 2-5 words, starts with capital
    if 2 <= len(words) <= 5 and text[0].isupper():
        name_headings.append((h.name, text))

print(f"Found {len(name_headings)} potential name headings:")
for i, (tag, text) in enumerate(name_headings[:15], 1):
    print(f"  {i}. <{tag}>: {text[:50]}")

# 5. Find images
print(f"\n5. IMAGES:")
images = soup.find_all('img')
print(f"Found {len(images)} total images")
profile_images = []
for img in images:
    src = img.get('src', '')
    alt = img.get('alt', '')
    if any(k in src.lower() or k in alt.lower() for k in ['leader', 'team', 'profile', 'photo', 'headshot']):
        profile_images.append((alt[:40], src[:60]))

print(f"Found {len(profile_images)} potential profile images:")
for i, (alt, src) in enumerate(profile_images[:10], 1):
    print(f"  {i}. alt='{alt}' src='{src}...'")

# 6. Check if it's a grid/list of profiles
print(f"\n6. PROFILE CONTAINERS:")
containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(
    k in str(x).lower() for k in ['card', 'item', 'box', 'entry', 'post']
))
print(f"Found {len(containers)} potential profile containers")
for i, cont in enumerate(containers[:5], 1):
    classes = ' '.join(cont.get('class', []))
    # Check if container has name-like heading
    heading = cont.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if heading:
        print(f"  {i}. <{cont.name}> class='{classes[:50]}' -> heading: '{heading.get_text().strip()[:40]}'")

# 7. Check for WordPress structure
print(f"\n7. WORDPRESS SPECIFIC:")
wp_posts = soup.find_all(class_=lambda x: x and 'post' in str(x).lower())
print(f"Found {len(wp_posts)} WordPress post elements")

# 8. Look for the actual structure
print(f"\n8. DETAILED STRUCTURE (first leader):")
# Try to find first leader container
first_leader = None
for link in soup.find_all('a', href=True):
    if '/leadership/' in link.get('href', ''):
        # Find parent container
        parent = link.find_parent(['div', 'article'])
        if parent:
            first_leader = parent
            break

if first_leader:
    print(f"Found first leader container:")
    print(f"  Tag: <{first_leader.name}>")
    print(f"  Classes: {first_leader.get('class', [])}")
    
    # Find name
    name_elem = first_leader.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if name_elem:
        print(f"  Name: {name_elem.get_text().strip()}")
    
    # Find image
    img = first_leader.find('img')
    if img:
        print(f"  Image: {img.get('src', 'No src')[:60]}")
    
    # Find link
    link = first_leader.find('a', href=True)
    if link:
        print(f"  Link: {link.get('href', 'No href')}")
    
    # Show structure
    print(f"\n  HTML structure:")
    print(str(first_leader)[:500] + "...")
else:
    print("Could not find leader container structure")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
