"""
Intelligent profile scraper with automatic discovery and structured extraction.
Handles various website layouts with error recovery.
"""

import asyncio
import re
from typing import List, Optional, Dict, Any, Set
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import validators

# Import will work once packages are installed
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - dynamic content will not be supported")


@dataclass
class ProfileData:
    """Structured profile data."""
    name: str
    title: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    photo_url: Optional[str] = None
    source_url: str = ""
    confidence_score: float = 0.0
    extraction_method: str = ""
    metadata: Dict[str, Any] = None
    raw_html: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def calculate_completeness(self) -> float:
        """Calculate profile completeness score (0-1)."""
        fields = ['name', 'title', 'bio', 'email', 'phone', 'linkedin', 'photo_url']
        filled = sum(1 for f in fields if getattr(self, f, None))
        return filled / len(fields)


class ProfileExtractor:
    """Extract profile information from HTML."""
    
    # Common selectors for profile elements
    NAME_SELECTORS = [
        'h1', 'h2.name', '.profile-name', '.person-name', '.name',
        '[itemprop="name"]', '.team-member-name', '.leadership-name'
    ]
    
    TITLE_SELECTORS = [
        '.title', '.job-title', '.position', '.role', '[itemprop="jobTitle"]',
        '.team-member-title', 'h3', 'h4.title', '.profile-title'
    ]
    
    BIO_SELECTORS = [
        '.bio', '.biography', '.description', '.profile-description',
        '[itemprop="description"]', '.about', '.profile-bio', 'p.bio'
    ]
    
    PHOTO_SELECTORS = [
        '.profile-photo', '.headshot', 'img.photo', '[itemprop="image"]',
        '.team-member-photo', '.profile-image', 'img.profile'
    ]
    
    # Email pattern
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    # Phone pattern (US and international)
    PHONE_PATTERN = re.compile(
        r'(\+?1?\s*\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4})|'
        r'(\+[0-9]{1,3}\s?[0-9\s.-]{7,})'
    )
    
    def extract_profile(self, html: str, url: str, base_url: str) -> Optional[ProfileData]:
        """
        Extract profile data from HTML.
        
        Args:
            html: HTML content
            url: Page URL
            base_url: Base URL for resolving relative links
        
        Returns:
            ProfileData or None
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Try multiple extraction methods
            profile = (
                self._extract_with_schema_org(soup, url) or
                self._extract_with_selectors(soup, url, base_url) or
                self._extract_with_heuristics(soup, url, base_url)
            )
            
            if profile and profile.name:
                profile.raw_html = html[:5000]  # Store first 5000 chars
                profile.confidence_score = self._calculate_confidence(profile, soup)
                logger.info(f"Extracted profile: {profile.name} (confidence: {profile.confidence_score:.2f})")
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Profile extraction failed for {url}: {e}")
            return None
    
    def _extract_with_schema_org(self, soup: BeautifulSoup, url: str) -> Optional[ProfileData]:
        """Extract using Schema.org Person markup."""
        try:
            person = soup.find(attrs={'itemtype': re.compile(r'schema.org/Person')})
            if not person:
                return None
            
            profile = ProfileData(source_url=url, extraction_method='schema.org')
            
            # Extract structured data
            name = person.find(attrs={'itemprop': 'name'})
            if name:
                profile.name = name.get_text(strip=True)
            
            title = person.find(attrs={'itemprop': 'jobTitle'})
            if title:
                profile.title = title.get_text(strip=True)
            
            desc = person.find(attrs={'itemprop': 'description'})
            if desc:
                profile.bio = desc.get_text(strip=True)
            
            email = person.find(attrs={'itemprop': 'email'})
            if email:
                profile.email = email.get('href', '').replace('mailto:', '') or email.get_text(strip=True)
            
            phone = person.find(attrs={'itemprop': 'telephone'})
            if phone:
                profile.phone = phone.get('href', '').replace('tel:', '') or phone.get_text(strip=True)
            
            image = person.find(attrs={'itemprop': 'image'})
            if image:
                profile.photo_url = image.get('src', '')
            
            return profile if profile.name else None
            
        except Exception as e:
            logger.debug(f"Schema.org extraction failed: {e}")
            return None
    
    def _extract_with_selectors(self, soup: BeautifulSoup, url: str, base_url: str) -> Optional[ProfileData]:
        """Extract using common CSS selectors."""
        try:
            profile = ProfileData(source_url=url, extraction_method='selectors')
            
            # Extract name
            for selector in self.NAME_SELECTORS:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    profile.name = element.get_text(strip=True)
                    break
            
            if not profile.name:
                return None
            
            # Extract title
            for selector in self.TITLE_SELECTORS:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    text = element.get_text(strip=True)
                    if text and text != profile.name:
                        profile.title = text
                        break
            
            # Extract bio
            for selector in self.BIO_SELECTORS:
                element = soup.select_one(selector)
                if element:
                    bio = element.get_text(strip=True)
                    if len(bio) > 50:  # Minimum bio length
                        profile.bio = bio
                        break
            
            # Extract photo
            for selector in self.PHOTO_SELECTORS:
                element = soup.select_one(selector)
                if element and element.get('src'):
                    profile.photo_url = urljoin(base_url, element['src'])
                    break
            
            # Extract contact info from links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'mailto:' in href:
                    profile.email = href.replace('mailto:', '').strip()
                elif 'tel:' in href:
                    profile.phone = href.replace('tel:', '').strip()
                elif 'linkedin.com' in href:
                    profile.linkedin = href
                elif 'twitter.com' in href or 'x.com' in href:
                    profile.twitter = href
            
            # Search for email and phone in text
            text_content = soup.get_text()
            if not profile.email:
                email_match = self.EMAIL_PATTERN.search(text_content)
                if email_match:
                    profile.email = email_match.group(0)
            
            if not profile.phone:
                phone_match = self.PHONE_PATTERN.search(text_content)
                if phone_match:
                    profile.phone = phone_match.group(0)
            
            return profile
            
        except Exception as e:
            logger.debug(f"Selector extraction failed: {e}")
            return None
    
    def _extract_with_heuristics(self, soup: BeautifulSoup, url: str, base_url: str) -> Optional[ProfileData]:
        """Extract using heuristic patterns."""
        try:
            profile = ProfileData(source_url=url, extraction_method='heuristics')
            
            # Find the largest heading as name
            for tag in ['h1', 'h2', 'h3']:
                headings = soup.find_all(tag)
                if headings:
                    profile.name = headings[0].get_text(strip=True)
                    break
            
            if not profile.name:
                return None
            
            # Find paragraphs near the name
            paragraphs = soup.find_all('p', limit=10)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 100 and not profile.bio:
                    profile.bio = text
                    break
            
            # Find first image as potential photo
            images = soup.find_all('img', src=True, limit=5)
            for img in images:
                src = img.get('src', '')
                if any(keyword in src.lower() for keyword in ['profile', 'photo', 'headshot', 'avatar', 'team']):
                    profile.photo_url = urljoin(base_url, src)
                    break
            
            return profile
            
        except Exception as e:
            logger.debug(f"Heuristic extraction failed: {e}")
            return None
    
    def _calculate_confidence(self, profile: ProfileData, soup: BeautifulSoup) -> float:
        """Calculate extraction confidence score."""
        score = 0.0
        weights = {
            'name': 0.3,
            'title': 0.15,
            'bio': 0.15,
            'email': 0.15,
            'phone': 0.10,
            'photo_url': 0.10,
            'linkedin': 0.05
        }
        
        for field, weight in weights.items():
            if getattr(profile, field, None):
                score += weight
        
        # Bonus for schema.org markup
        if profile.extraction_method == 'schema.org':
            score += 0.1
        
        # Bonus for professional email domain
        if profile.email and not any(domain in profile.email for domain in ['gmail', 'yahoo', 'hotmail']):
            score += 0.05
        
        return min(score, 1.0)


class ProfileScraper:
    """Intelligent profile scraper with automatic discovery."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.extractor = ProfileExtractor()
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = self.config.get(
            'user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        
        # Visited URLs tracking
        self.visited_urls: Set[str] = set()
        self.discovered_profiles: Set[str] = set()
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.user_agent},
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch page content with retry logic.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
        
        Returns:
            HTML content or None
        """
        try:
            if not self.session:
                raise RuntimeError("Scraper must be used as async context manager")
            
            logger.debug(f"Fetching: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
                    return content
                elif response.status == 429:  # Too many requests
                    wait_time = min(2 ** retry_count, 60)
                    logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    if retry_count < self.max_retries:
                        return await self.fetch_page(url, retry_count + 1)
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            if retry_count < self.max_retries:
                return await self.fetch_page(url, retry_count + 1)
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.fetch_page(url, retry_count + 1)
        
        return None
    
    async def extract_profile(self, url: str) -> Optional[ProfileData]:
        """
        Extract profile from a URL.
        
        Args:
            url: Profile page URL
        
        Returns:
            ProfileData or None
        """
        if url in self.visited_urls:
            logger.debug(f"Already visited: {url}")
            return None
        
        self.visited_urls.add(url)
        
        html = await self.fetch_page(url)
        if not html:
            return None
        
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        profile = self.extractor.extract_profile(html, url, base_url)
        
        if profile:
            self.discovered_profiles.add(url)
        
        return profile
    
    async def extract_profiles_batch(self, urls: List[str]) -> List[ProfileData]:
        """
        Extract profiles from multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
        
        Returns:
            List of ProfileData
        """
        tasks = [self.extract_profile(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        profiles = []
        for result in results:
            if isinstance(result, ProfileData):
                profiles.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Batch extraction error: {result}")
        
        return profiles
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            'urls_visited': len(self.visited_urls),
            'profiles_discovered': len(self.discovered_profiles),
            'success_rate': len(self.discovered_profiles) / len(self.visited_urls) if self.visited_urls else 0
        }
