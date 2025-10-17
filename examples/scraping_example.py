"""
Example usage and test script for the scraping system.
Run this to test profile scraping functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.scraping_service import ProfileScrapingService
from src.database.migrations import init_database, get_database_stats
from loguru import logger


async def example_discover_profiles():
    """Example: Discover profile pages from a base URL."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Discover Profile Pages")
    print("=" * 60)
    
    service = ProfileScrapingService()
    
    # Example URLs to try (you can replace with real URLs)
    test_urls = [
        "https://example.com/team",
        "https://example.com/leadership",
    ]
    
    for url in test_urls:
        print(f"\nDiscovering profiles from: {url}")
        try:
            urls = await service.discover_profiles(url, max_depth=2, max_pages=50)
            print(f"✓ Found {len(urls)} potential profile pages")
            
            # Show first few URLs
            for i, discovered_url in enumerate(urls[:5], 1):
                print(f"  {i}. {discovered_url}")
            
            if len(urls) > 5:
                print(f"  ... and {len(urls) - 5} more")
        
        except Exception as e:
            print(f"✗ Discovery failed: {e}")


async def example_extract_single_profile():
    """Example: Extract a single profile."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Extract Single Profile")
    print("=" * 60)
    
    service = ProfileScrapingService()
    
    # Example profile URL (replace with real URL)
    profile_url = "https://example.com/team/john-doe"
    
    print(f"\nExtracting profile from: {profile_url}")
    
    try:
        profile = await service.extract_profile(profile_url)
        
        if profile:
            print("\n✓ Profile extracted successfully!")
            print(f"\nProfile Information:")
            print(f"  Name:          {profile.name}")
            print(f"  Title:         {profile.title or 'N/A'}")
            print(f"  Email:         {profile.email or 'N/A'}")
            print(f"  Phone:         {profile.phone or 'N/A'}")
            print(f"  LinkedIn:      {profile.linkedin or 'N/A'}")
            print(f"  Photo:         {profile.photo_url or 'N/A'}")
            print(f"  Confidence:    {profile.confidence_score:.2%}")
            print(f"  Method:        {profile.extraction_method}")
            print(f"  Completeness:  {profile.calculate_completeness():.2%}")
            
            if profile.bio:
                bio_preview = profile.bio[:150] + "..." if len(profile.bio) > 150 else profile.bio
                print(f"  Bio:           {bio_preview}")
        else:
            print("✗ No profile data could be extracted")
    
    except Exception as e:
        print(f"✗ Extraction failed: {e}")


async def example_full_scrape():
    """Example: Full discovery and extraction."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Full Discovery & Extraction")
    print("=" * 60)
    
    service = ProfileScrapingService()
    
    # Example base URL
    base_url = "https://example.com/team"
    
    print(f"\nStarting full scrape from: {base_url}")
    print("This will discover profile pages and extract data from each...\n")
    
    try:
        profiles = await service.discover_and_extract(base_url)
        
        print(f"\n✓ Scrape completed!")
        print(f"  Total profiles extracted: {len(profiles)}")
        
        if profiles:
            print(f"\nExtracted Profiles:")
            for i, profile in enumerate(profiles[:10], 1):
                confidence_icon = "●" if profile.confidence_score > 0.7 else "○"
                print(f"  {i}. {confidence_icon} {profile.name} - {profile.title or 'No title'}")
                print(f"     Confidence: {profile.confidence_score:.2%} | URL: {profile.source_url[:50]}...")
            
            if len(profiles) > 10:
                print(f"  ... and {len(profiles) - 10} more profiles")
            
            # Calculate average confidence
            avg_confidence = sum(p.confidence_score for p in profiles) / len(profiles)
            print(f"\nAverage Confidence Score: {avg_confidence:.2%}")
    
    except Exception as e:
        print(f"✗ Scrape failed: {e}")


async def example_scrape_from_config():
    """Example: Scrape from configuration file."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Scrape from Configuration")
    print("=" * 60)
    
    service = ProfileScrapingService()
    
    print("\nScraping all enabled targets from config/scraping_targets.yaml...")
    
    try:
        results = await service.scrape_from_config()
        
        print(f"\n✓ Configuration scrape completed!")
        print(f"  Targets scraped:      {results['targets_scraped']}")
        print(f"  Profiles extracted:   {results['profiles_extracted']}")
        
        if results['errors']:
            print(f"  Errors encountered:   {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"    - {error}")
    
    except Exception as e:
        print(f"✗ Configuration scrape failed: {e}")


def example_database_operations():
    """Example: Database operations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Database Operations")
    print("=" * 60)
    
    service = ProfileScrapingService()
    
    print("\n1. Database Statistics:")
    stats = service.get_statistics()
    print(f"  Total profiles:     {stats.get('total_profiles', 0)}")
    print(f"  Active profiles:    {stats.get('active_profiles', 0)}")
    print(f"  Recent profiles:    {stats.get('recent_profiles', 0)} (last 7 days)")
    
    scrape_stats = stats.get('scrape_logs', {})
    if scrape_stats:
        print(f"\n2. Scrape Statistics:")
        print(f"  Total scrapes:      {scrape_stats.get('total_scrapes', 0)}")
        print(f"  Successful:         {scrape_stats.get('successful', 0)}")
        print(f"  Failed:             {scrape_stats.get('failed', 0)}")
        print(f"  Success rate:       {scrape_stats.get('success_rate', 0):.1f}%")
    
    print("\n3. Finding Duplicates:")
    duplicates = service.find_duplicates()
    if duplicates:
        print(f"  Found {len(duplicates)} potential duplicate pairs:")
        for dup in duplicates[:5]:
            print(f"    - ID {dup[0]}: '{dup[2]}' vs ID {dup[1]}: '{dup[3]}'")
    else:
        print("  No duplicates found")


def example_database_setup():
    """Example: Initialize database."""
    print("\n" + "=" * 60)
    print("DATABASE SETUP")
    print("=" * 60)
    
    print("\nInitializing database...")
    
    # Initialize database
    success = init_database()
    
    if success:
        print("✓ Database initialized successfully!")
        
        # Show database stats
        stats = get_database_stats()
        print(f"\nDatabase Information:")
        print(f"  Profiles:         {stats.get('profiles', 0)}")
        print(f"  Contents:         {stats.get('contents', 0)}")
        print(f"  Categories:       {stats.get('categories', 0)}")
        print(f"  Scrape Logs:      {stats.get('scrape_logs', 0)}")
    else:
        print("✗ Database initialization failed")


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "KNOWLEDGE MANAGEMENT SYSTEM" + " " * 20 + "║")
    print("║" + " " * 12 + "Scraping System Examples" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Setup database first
    example_database_setup()
    
    # Show menu
    print("\n" + "=" * 60)
    print("EXAMPLES MENU")
    print("=" * 60)
    print("\n1. Discover profile pages from a URL")
    print("2. Extract a single profile")
    print("3. Full discovery and extraction")
    print("4. Scrape from configuration file")
    print("5. Database operations and statistics")
    print("6. Run all examples")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    if choice == '1':
        await example_discover_profiles()
    elif choice == '2':
        await example_extract_single_profile()
    elif choice == '3':
        await example_full_scrape()
    elif choice == '4':
        await example_scrape_from_config()
    elif choice == '5':
        example_database_operations()
    elif choice == '6':
        await example_discover_profiles()
        await example_extract_single_profile()
        await example_full_scrape()
        await example_scrape_from_config()
        example_database_operations()
    elif choice == '0':
        print("\nExiting...")
        return
    else:
        print("\nInvalid choice!")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    # Configure logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        logger.exception("Example failed")
