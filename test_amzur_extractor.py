"""
Dedicated Amzur Leadership Extractor

This script provides a specialized extractor for the Amzur leadership page
that uses the specific HTML structure of their site.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def extract_amzur_leadership(url="https://amzur.com/leadership-team/"):
    """Extract leadership from Amzur's specific page structure."""
    
    print(f"🔍 Scraping: {url}")
    
    # Fetch page
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    leaders = []
    
    # Strategy 1: Find all h4 tags with links (names are in h4 tags)
    h4_tags = soup.find_all('h4')
    
    for h4 in h4_tags:
        # Get name from h4
        name_link = h4.find('a')
        if name_link:
            name = name_link.get_text().strip()
            profile_url = name_link.get('href', '')
            
            # Validate name (2-4 words)
            name_parts = name.split()
            if not (2 <= len(name_parts) <= 4):
                continue
            
            # Skip if not proper names
            if not all(part[0].isupper() for part in name_parts if part):
                continue
            
            # Get title from text immediately after h4
            title = None
            
            # Check all following siblings until next h4 or significant break
            current = h4.next_sibling
            checked_siblings = 0
            while current and checked_siblings < 5:
                checked_siblings += 1
                
                if isinstance(current, str):
                    text = current.strip()
                    if text and len(text) > 5 and len(text) < 200:
                        # This looks like a title
                        title = text
                        break
                elif hasattr(current, 'name'):
                    if current.name == 'h4':
                        # Hit next person
                        break
                    elif current.name in ['p', 'span', 'div']:
                        text = current.get_text().strip()
                        if text and len(text) > 5 and len(text) < 200:
                            # Check if it's a title (not a long paragraph)
                            lines = text.split('\n')
                            first_line = lines[0].strip()
                            if first_line and len(first_line) < 150:
                                title = first_line
                                break
                
                current = current.next_sibling
            
            # Try to find image
            image_url = None
            
            # Look backwards from h4 for an image
            prev = h4.previous_sibling
            checked_prev = 0
            while prev and checked_prev < 10:
                checked_prev += 1
                if hasattr(prev, 'find') and callable(prev.find):
                    img = prev.find('img')
                    if img and hasattr(img, 'get') and img.get('src'):
                        image_url = urljoin(url, img['src'])
                        # Check if image filename relates to person
                        if any(word.lower() in image_url.lower() for word in name_parts):
                            break
                        elif not image_url.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            image_url = None
                            continue
                        break
                prev = prev.previous_sibling
            
            if title:
                leaders.append({
                    'name': name,
                    'title': title,
                    'image_url': image_url,
                    'profile_url': urljoin(url, profile_url) if profile_url else None,
                    'source': 'amzur_leadership_page'
                })
                print(f"✅ Found: {name} - {title}")
            else:
                print(f"⚠️  Found name but no title: {name}")
    
    # Strategy 2: Look for specific div/section patterns
    leadership_section = soup.find('section', class_=re.compile(r'leadership', re.I))
    if leadership_section and len(leaders) < 5:
        print("📦 Trying section-based extraction...")
        
        # Look for card-like structures
        cards = leadership_section.find_all(['div', 'article'])
        for card in cards:
            h4 = card.find('h4')
            if h4:
                name_link = h4.find('a')
                if name_link:
                    name = name_link.get_text().strip()
                    
                    # Get title from next element
                    title_elem = h4.find_next(['p', 'span', 'div'])
                    if title_elem:
                        title = title_elem.get_text().strip()
                        
                        # Get image
                        img = card.find('img')
                        image_url = urljoin(url, img['src']) if img and img.get('src') else None
                        
                        # Avoid duplicates
                        if not any(l['name'] == name for l in leaders):
                            leaders.append({
                                'name': name,
                                'title': title,
                                'image_url': image_url,
                                'profile_url': urljoin(url, name_link.get('href', '')) if name_link.get('href') else None,
                                'source': 'amzur_section_extraction'
                            })
                            print(f"✅ Found (section): {name} - {title}")
    
    print(f"\n🎉 Total extracted: {len(leaders)} leaders")
    return leaders


if __name__ == "__main__":
    import re
    
    # Test the extractor
    leaders = extract_amzur_leadership()
    
    # Print results
    print("\n" + "="*60)
    print("AMZUR LEADERSHIP TEAM")
    print("="*60)
    
    for i, leader in enumerate(leaders, 1):
        print(f"\n{i}. {leader['name']}")
        print(f"   Title: {leader['title']}")
        if leader.get('image_url'):
            print(f"   Image: {leader['image_url']}")
        if leader.get('profile_url'):
            print(f"   Profile: {leader['profile_url']}")
    
    # Save to JSON
    with open('amzur_leadership.json', 'w', encoding='utf-8') as f:
        json.dump(leaders, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(leaders)} profiles to amzur_leadership.json")
