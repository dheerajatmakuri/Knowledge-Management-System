"""
Profile scraping service - orchestrates discovery and extraction.
Implements the expected service pattern with async operations.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from loguru import logger
import yaml

from ..scrapers.profile_scraper import ProfileScraper, ProfileData
from ..scrapers.content_discovery import ContentDiscovery, discover_and_extract
from ..database.repository import DatabaseSession, ProfileRepository, ScrapeLogRepository
from ..database.models import Profile


class ProfileScrapingService:
    """
    Service for coordinating profile scraping operations.
    Handles discovery, extraction, deduplication, and storage.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize scraping service.
        
        Args:
            config_path: Path to scraping configuration file
        """
        self.config = self._load_config(config_path)
        self.db_session = DatabaseSession()
        
        # Initialize with discovery patterns
        self.discovery_patterns = self.config.get('settings', {}).get('auto_discover', {})
        self.scraper_config = {
            'user_agent': self.config.get('settings', {}).get('user_agent', ''),
            'timeout': self.config.get('settings', {}).get('retry', {}).get('timeout', 30),
            'max_retries': self.config.get('settings', {}).get('retry', {}).get('max_attempts', 3),
            'rate_limit_delay': self.config.get('settings', {}).get('rate_limit', {}).get('delay_between_requests', 1.0),
        }
        
        logger.info("ProfileScrapingService initialized")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load scraping configuration from YAML file."""
        if config_path is None:
            config_path = 'config/scraping_targets.yaml'
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {'targets': [], 'settings': {}}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {'targets': [], 'settings': {}}
    
    async def discover_profiles(self, base_url: str, max_depth: int = 3, max_pages: int = 100) -> List[str]:
        """
        Intelligent page discovery.
        
        Args:
            base_url: Starting URL for discovery
            max_depth: Maximum link depth to follow
            max_pages: Maximum pages to discover
        
        Returns:
            List of discovered profile URLs
        """
        logger.info(f"Starting discovery from: {base_url}")
        
        # Update config with parameters
        config = {
            **self.scraper_config,
            'max_depth': max_depth,
            'max_pages': max_pages,
            'same_domain_only': self.discovery_patterns.get('same_domain_only', True)
        }
        
        # Log discovery attempt
        start_time = datetime.utcnow()
        
        try:
            async with ContentDiscovery(config) as discovery:
                profile_urls = await discovery.discover_profiles(base_url)
                
                # Get statistics
                stats = discovery.get_statistics()
                logger.info(f"Discovery stats: {stats}")
                
                # Log to database
                with self.db_session.get_session() as session:
                    scrape_log_repo = ScrapeLogRepository(session)
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    scrape_log_repo.log_scrape(
                        url=base_url,
                        scrape_type='discovery',
                        status='success',
                        profiles_found=len(profile_urls),
                        duration_seconds=duration,
                        started_at=start_time,
                        completed_at=datetime.utcnow()
                    )
                
                return profile_urls
        
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            
            # Log failure
            with self.db_session.get_session() as session:
                scrape_log_repo = ScrapeLogRepository(session)
                duration = (datetime.utcnow() - start_time).total_seconds()
                scrape_log_repo.log_scrape(
                    url=base_url,
                    scrape_type='discovery',
                    status='failed',
                    errors={'error': str(e)},
                    duration_seconds=duration,
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            return []
    
    async def extract_profile(self, url: str) -> Optional[ProfileData]:
        """
        Structured information extraction from a single URL.
        
        Args:
            url: Profile page URL
        
        Returns:
            ProfileData object or None
        """
        logger.info(f"Extracting profile from: {url}")
        
        start_time = datetime.utcnow()
        
        try:
            async with ProfileScraper(self.scraper_config) as scraper:
                profile = await scraper.extract_profile(url)
                
                if profile:
                    # Save to database
                    saved_profile = self._save_profile(profile)
                    
                    # Log success
                    with self.db_session.get_session() as session:
                        scrape_log_repo = ScrapeLogRepository(session)
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        scrape_log_repo.log_scrape(
                            url=url,
                            scrape_type='profile',
                            status='success',
                            profiles_extracted=1,
                            duration_seconds=duration,
                            started_at=start_time,
                            completed_at=datetime.utcnow()
                        )
                    
                    logger.success(f"Extracted and saved profile: {profile.name}")
                    return profile
                else:
                    logger.warning(f"No profile data extracted from: {url}")
                    return None
        
        except Exception as e:
            logger.error(f"Profile extraction failed for {url}: {e}")
            
            # Log failure
            with self.db_session.get_session() as session:
                scrape_log_repo = ScrapeLogRepository(session)
                duration = (datetime.utcnow() - start_time).total_seconds()
                scrape_log_repo.log_scrape(
                    url=url,
                    scrape_type='profile',
                    status='failed',
                    errors={'error': str(e)},
                    duration_seconds=duration,
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            return None
    
    async def extract_profiles_batch(self, urls: List[str]) -> List[ProfileData]:
        """
        Extract multiple profiles concurrently.
        
        Args:
            urls: List of profile URLs
        
        Returns:
            List of ProfileData objects
        """
        logger.info(f"Batch extracting {len(urls)} profiles")
        
        start_time = datetime.utcnow()
        profiles = []
        
        try:
            async with ProfileScraper(self.scraper_config) as scraper:
                extracted = await scraper.extract_profiles_batch(urls)
                
                # Save profiles
                for profile in extracted:
                    if profile:
                        self._save_profile(profile)
                        profiles.append(profile)
                
                # Log batch operation
                with self.db_session.get_session() as session:
                    scrape_log_repo = ScrapeLogRepository(session)
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    scrape_log_repo.log_scrape(
                        url=f"batch_{len(urls)}_urls",
                        scrape_type='batch',
                        status='success',
                        profiles_found=len(urls),
                        profiles_extracted=len(profiles),
                        duration_seconds=duration,
                        started_at=start_time,
                        completed_at=datetime.utcnow()
                    )
                
                logger.success(f"Batch extracted {len(profiles)} profiles")
                return profiles
        
        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            return profiles
    
    async def discover_and_extract(self, base_url: str) -> List[ProfileData]:
        """
        Combined discovery and extraction operation.
        
        Args:
            base_url: Starting URL
        
        Returns:
            List of extracted ProfileData objects
        """
        logger.info(f"Starting full scrape from: {base_url}")
        
        # Discover profile URLs
        urls = await self.discover_profiles(base_url)
        
        if not urls:
            logger.warning("No profile URLs discovered")
            return []
        
        # Extract profiles
        profiles = await self.extract_profiles_batch(urls)
        
        logger.success(f"Completed full scrape: {len(profiles)} profiles extracted")
        return profiles
    
    def _save_profile(self, profile_data: ProfileData) -> Optional[Profile]:
        """
        Save profile to database with duplicate detection.
        
        Args:
            profile_data: ProfileData object
        
        Returns:
            Saved Profile model or None
        """
        try:
            with self.db_session.get_session() as session:
                profile_repo = ProfileRepository(session)
                
                # Check for duplicates
                existing = profile_repo.get_by_url(profile_data.source_url)
                
                if existing:
                    # Update existing profile
                    logger.info(f"Updating existing profile: {profile_data.name}")
                    profile = profile_repo.update_profile(
                        existing.id,
                        name=profile_data.name,
                        title=profile_data.title,
                        bio=profile_data.bio,
                        email=profile_data.email,
                        phone=profile_data.phone,
                        linkedin=profile_data.linkedin,
                        twitter=profile_data.twitter,
                        website=profile_data.website,
                        photo_url=profile_data.photo_url,
                        extraction_method=profile_data.extraction_method,
                        confidence_score=profile_data.confidence_score,
                        metadata=profile_data.metadata,
                        raw_html=profile_data.raw_html,
                        last_scraped_at=datetime.utcnow(),
                        scrape_status='completed'
                    )
                else:
                    # Create new profile
                    logger.info(f"Creating new profile: {profile_data.name}")
                    profile = profile_repo.create_profile(
                        name=profile_data.name,
                        title=profile_data.title,
                        bio=profile_data.bio,
                        email=profile_data.email,
                        phone=profile_data.phone,
                        linkedin=profile_data.linkedin,
                        twitter=profile_data.twitter,
                        website=profile_data.website,
                        photo_url=profile_data.photo_url,
                        source_url=profile_data.source_url,
                        extraction_method=profile_data.extraction_method,
                        confidence_score=profile_data.confidence_score,
                        metadata=profile_data.metadata,
                        raw_html=profile_data.raw_html,
                        scrape_status='completed'
                    )
                
                session.commit()
                return profile
        
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            return None
    
    def merge_duplicate_profiles(self, profile_id1: int, profile_id2: int) -> bool:
        """
        Merge two duplicate profiles.
        
        Args:
            profile_id1: Primary profile ID
            profile_id2: Duplicate profile ID to merge
        
        Returns:
            bool: True if successful
        """
        try:
            with self.db_session.get_session() as session:
                profile_repo = ProfileRepository(session)
                merged = profile_repo.merge_profiles(profile_id1, profile_id2)
                session.commit()
                
                if merged:
                    logger.success(f"Merged profile {profile_id2} into {profile_id1}")
                    return True
                return False
        
        except Exception as e:
            logger.error(f"Failed to merge profiles: {e}")
            return False
    
    def find_duplicates(self) -> List[tuple]:
        """
        Find potential duplicate profiles.
        
        Returns:
            List of tuples (id1, id2, name1, name2)
        """
        try:
            with self.db_session.get_session() as session:
                profile_repo = ProfileRepository(session)
                duplicates = profile_repo.find_duplicates()
                logger.info(f"Found {len(duplicates)} potential duplicate pairs")
                return duplicates
        
        except Exception as e:
            logger.error(f"Failed to find duplicates: {e}")
            return []
    
    async def scrape_from_config(self) -> Dict[str, Any]:
        """
        Scrape all enabled targets from configuration file.
        
        Returns:
            Dictionary with scraping results
        """
        results = {
            'targets_scraped': 0,
            'profiles_extracted': 0,
            'errors': []
        }
        
        targets = self.config.get('targets', [])
        enabled_targets = [t for t in targets if t.get('enabled', False)]
        
        logger.info(f"Scraping {len(enabled_targets)} enabled targets")
        
        for target in enabled_targets:
            try:
                name = target.get('name', 'Unknown')
                url = target.get('url')
                
                logger.info(f"Scraping target: {name}")
                
                profiles = await self.discover_and_extract(url)
                
                results['targets_scraped'] += 1
                results['profiles_extracted'] += len(profiles)
                
            except Exception as e:
                error_msg = f"Failed to scrape {target.get('name')}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.success(f"Configuration scraping complete: {results}")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scraping statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_session.get_session() as session:
                profile_repo = ProfileRepository(session)
                scrape_log_repo = ScrapeLogRepository(session)
                
                stats = {
                    'total_profiles': profile_repo.count(),
                    'active_profiles': len(profile_repo.get_active_profiles()),
                    'scrape_logs': scrape_log_repo.get_statistics(),
                    'recent_profiles': len(profile_repo.get_recent_profiles(days=7))
                }
                
                return stats
        
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# CLI interface for testing
async def main():
    """Command-line interface for testing the scraping service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Profile Scraping Service')
    parser.add_argument('command', choices=['discover', 'extract', 'scrape', 'stats'],
                       help='Command to execute')
    parser.add_argument('--url', type=str, help='URL to scrape')
    parser.add_argument('--config', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    service = ProfileScrapingService(args.config)
    
    if args.command == 'discover':
        if not args.url:
            print("Error: --url required for discover command")
            return
        urls = await service.discover_profiles(args.url)
        print(f"\nDiscovered {len(urls)} profile URLs:")
        for url in urls:
            print(f"  - {url}")
    
    elif args.command == 'extract':
        if not args.url:
            print("Error: --url required for extract command")
            return
        profile = await service.extract_profile(args.url)
        if profile:
            print(f"\nExtracted Profile:")
            print(f"  Name: {profile.name}")
            print(f"  Title: {profile.title}")
            print(f"  Confidence: {profile.confidence_score:.2f}")
    
    elif args.command == 'scrape':
        if not args.url:
            print("Error: --url required for scrape command")
            return
        profiles = await service.discover_and_extract(args.url)
        print(f"\nExtracted {len(profiles)} profiles")
    
    elif args.command == 'stats':
        stats = service.get_statistics()
        print("\nScraping Statistics:")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key}: {value}")


if __name__ == '__main__':
    asyncio.run(main())
