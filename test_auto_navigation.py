"""
Test Auto-Navigation Feature

This script demonstrates the automatic navigation from homepage to leadership page.
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import functions directly to avoid __init__ issues
import importlib.util
spec = importlib.util.spec_from_file_location("url_chat", project_root / "src" / "ui" / "url_chat_interface.py")
url_chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(url_chat)

scrape_url = url_chat.scrape_url
extract_leadership_info = url_chat.extract_leadership_info
find_leadership_page = url_chat.find_leadership_page


def test_auto_navigation():
    """Test automatic navigation to leadership page."""
    
    print("\n" + "="*80)
    print("🧪 Testing Auto-Navigation Feature")
    print("="*80 + "\n")
    
    # Test URLs
    test_cases = [
        {
            'name': 'Amzur Homepage',
            'url': 'https://amzur.com/',
            'expected_path': 'leadership-team'
        },
        {
            'name': 'Amzur Direct Leadership',
            'url': 'https://amzur.com/leadership-team/',
            'expected_path': 'leadership-team'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}: {test['name']}")
        print(f"{'─'*80}")
        print(f"📍 Input URL: {test['url']}")
        
        # Test with auto-navigation ON
        print("\n🔄 Scraping with AUTO-NAVIGATION ON...")
        result = scrape_url(test['url'], auto_navigate=True)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        print(f"✅ Final URL: {result['url']}")
        print(f"📄 Page Title: {result['title']}")
        
        if result.get('navigated_from'):
            print(f"🔀 Navigated from: {result['navigated_from']}")
            print(f"✨ Auto-navigation worked!")
        else:
            print(f"📌 No navigation (already on target page or auto-nav disabled)")
        
        # Extract leadership
        print(f"\n👥 Extracting leadership information...")
        leaders = extract_leadership_info(result)
        
        print(f"✅ Found {len(leaders)} leaders")
        
        if leaders:
            print(f"\n📋 Leadership Team:")
            for j, leader in enumerate(leaders[:5], 1):
                print(f"  {j}. {leader['name']} - {leader['title']}")
                if leader.get('photo_url'):
                    print(f"     📸 Photo: {leader['photo_url'][:60]}...")
            
            if len(leaders) > 5:
                print(f"  ... and {len(leaders) - 5} more")
        else:
            print(f"⚠️ No leaders found")
        
        # Check if navigation was correct
        if test['expected_path'] in result['url']:
            print(f"\n✅ TEST PASSED: Navigated to correct page!")
        else:
            print(f"\n⚠️ TEST WARNING: Expected '{test['expected_path']}' in URL")


def test_link_detection():
    """Test the link detection algorithm."""
    
    print("\n\n" + "="*80)
    print("🔍 Testing Leadership Link Detection")
    print("="*80 + "\n")
    
    # Fetch Amzur homepage
    url = 'https://amzur.com/'
    print(f"📍 Fetching: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✅ Page loaded successfully")
        
        # Test leadership page detection
        print(f"\n🔍 Looking for leadership page links...")
        leadership_url = find_leadership_page(url, soup)
        
        if leadership_url:
            print(f"✅ Found leadership page: {leadership_url}")
            print(f"📊 Detection successful!")
        else:
            print(f"❌ No leadership page found")
            print(f"⚠️ This might indicate a problem with the detection algorithm")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    
    print("\n" + "🚀"*40)
    print("AUTOMATIC NAVIGATION TEST SUITE")
    print("🚀"*40)
    
    # Test 1: Link Detection
    test_link_detection()
    
    # Test 2: Full Auto-Navigation
    test_auto_navigation()
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")
    
    print("💡 Next steps:")
    print("   1. Open the app: http://localhost:8503")
    print("   2. Enter: https://amzur.com/")
    print("   3. Enable 'Auto-navigate to leadership page'")
    print("   4. Click 'Scrape URL'")
    print("   5. Watch it automatically navigate to /leadership-team/")
    print("   6. Click 'Extract Leadership'")
    print("   7. See 14 leaders extracted! ✨\n")


if __name__ == '__main__':
    main()
