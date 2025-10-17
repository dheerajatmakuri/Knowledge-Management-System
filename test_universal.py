"""
Test the universal extractor with real URLs
"""

import sys
sys.path.insert(0, 'src')

from ui.url_chat_interface import scrape_url, extract_leadership_info

print("="*70)
print("TESTING UNIVERSAL EXTRACTOR")
print("="*70)

# Test URLs
test_urls = [
    "https://amzur.com/leadership-team/",
    # "https://stripe.com/about",
]

for url in test_urls:
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print('='*70)
    
    # Scrape
    print("📥 Scraping...")
    content = scrape_url(url)
    
    if 'error' in content:
        print(f"❌ Error: {content['error']}")
        continue
    
    print(f"✅ Scraped: {content['title']}")
    print(f"   📄 Text: {len(content.get('full_text', ''))} chars")
    print(f"   🖼️  Images: {len(content.get('images', []))}")
    print(f"   🔗 Links: {len(content.get('links', []))}")
    
    # Extract
    print("\n🔍 Extracting leadership...")
    leaders = extract_leadership_info(content)
    
    if not leaders:
        print("❌ No leaders found!")
        suggested = content.get('suggested_leadership_urls', [])
        if suggested:
            print(f"💡 Suggestions: {suggested[:3]}")
    else:
        print(f"✅ Found {len(leaders)} leaders:\n")
        for i, leader in enumerate(leaders, 1):
            print(f"  {i}. {leader['name']}")
            print(f"     Title: {leader['title']}")
            if leader.get('image_url'):
                print(f"     Image: {leader['image_url'][:60]}...")
            if leader.get('profile_url'):
                print(f"     Profile: {leader['profile_url']}")
            print()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
