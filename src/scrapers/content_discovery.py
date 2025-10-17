"""
Intelligent content discovery system.
Automatically discovers profile pages through pattern recognition and link analysis.
"""

import asyncio
import re
from typing import List, Set, Dict, Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from collections import defaultdict
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import validators


@dataclass
class DiscoveredPage:
    """Represents a discovered page."""
    url: str
    page_type: str  # 'profile', 'listing', 'content', 'unknown'
    confidence: float
    depth: int
    parent_url: Optional[str] = None
    metadata: Dict[str, Any] = None


class ContentDiscovery:
    """Intelligent profile page discovery engine."""
    
    # URL patterns that likely contain profiles
    PROFILE_URL_PATTERNS = [
        r'/team/',
        r'/leadership/',
        r'/about/team',
        r'/people/',
        r'/staff/',
        r'/bio/',
        r'/profile/',
        r'/executive/',
        r'/management/',
        r'/person/',
        r'/member/',
        r'/employee/',
        r'/faculty/',
        r'/researcher/',
    ]
    
    # Anchor text patterns
    PROFILE_ANCHOR_PATTERNS = [
        r'meet\s+(the\s+)?team',
        r'our\s+(team|people|leadership)',
        r'leadership\s+team',
        r'about\s+us',
        r'team\s+members',
        r'executive\s+team',
        r'management\s+team',
        r'staff\s+directory',
    ]
    
    # CSS selectors for profile listings
    LISTING_SELECTORS = [
        '.team-grid',
        '.team-list',
        '.team-members',
        '.people-grid',
        '.staff-list',
        '.leadership-team',
        '.profile-grid',
        '[class*="team"]',
        '[class*="people"]',
        '[class*="staff"]',
    ]
    
    # Keywords in page content
    PROFILE_KEYWORDS = [
        'team', 'leadership', 'executive', 'staff', 'people',
        'management', 'director', 'officer', 'member', 'employee'
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize content discovery.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = self.config.get(
            'user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.timeout = self.config.get('timeout', 30)
        self.max_depth = self.config.get('max_depth', 3)
        self.max_pages = self.config.get('max_pages', 100)
        self.same_domain_only = self.config.get('same_domain_only', True)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        
        # Tracking
        self.discovered_pages: Dict[str, DiscoveredPage] = {}
        self.visited_urls: Set[str] = set()
        self.domain_counts: Dict[str, int] = defaultdict(int)
    
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
    
    async def discover_profiles(self, base_url: str) -> List[str]:
        """
        Discover profile pages starting from a base URL.
        
        Args:
            base_url: Starting URL for discovery
        
        Returns:
            List of discovered profile page URLs
        """
        logger.info(f"Starting profile discovery from: {base_url}")
        
        # Initialize with base URL
        await self._discover_recursive(base_url, depth=0)
        
        # Filter and return profile URLs
        profile_urls = [
            page.url for page in self.discovered_pages.values()
            if page.page_type == 'profile' and page.confidence > 0.5
        ]
        
        logger.success(f"Discovered {len(profile_urls)} profile pages")
        return profile_urls
    
    async def _discover_recursive(self, url: str, depth: int, parent_url: str = None):
        """
        Recursively discover pages.
        
        Args:
            url: Current URL to explore
            depth: Current depth in discovery tree
            parent_url: Parent URL
        """
        # Check limits
        if depth > self.max_depth:
            logger.debug(f"Max depth reached: {url}")
            return
        
        if len(self.discovered_pages) >= self.max_pages:
            logger.info(f"Max pages reached: {self.max_pages}")
            return
        
        if url in self.visited_urls:
            return
        
        # Validate URL
        if not validators.url(url):
            logger.debug(f"Invalid URL: {url}")
            return
        
        # Check domain restriction
        if self.same_domain_only and parent_url:
            if urlparse(url).netloc != urlparse(parent_url).netloc:
                logger.debug(f"Different domain, skipping: {url}")
                return
        
        self.visited_urls.add(url)
        
        # Fetch page
        html = await self._fetch_page(url)
        if not html:
            return
        
        # Analyze page
        page_type, confidence = self._classify_page(html, url)
        
        # Store discovered page
        discovered = DiscoveredPage(
            url=url,
            page_type=page_type,
            confidence=confidence,
            depth=depth,
            parent_url=parent_url
        )
        self.discovered_pages[url] = discovered
        
        logger.debug(f"Classified {url} as {page_type} (confidence: {confidence:.2f}, depth: {depth})")
        
        # Extract links and continue discovery
        if page_type in ['listing', 'unknown'] and depth < self.max_depth:
            links = self._extract_links(html, url)
            
            # Prioritize likely profile links
            prioritized_links = self._prioritize_links(links, url)
            
            # Discover links (limit concurrent requests)
            batch_size = 5
            for i in range(0, len(prioritized_links), batch_size):
                batch = prioritized_links[i:i+batch_size]
                tasks = [self._discover_recursive(link, depth + 1, url) for link in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(self.rate_limit_delay)
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content."""
        try:
            if not self.session:
                raise RuntimeError("Discovery must be used as async context manager")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.debug(f"HTTP {response.status} for {url}")
                    return None
        
        except asyncio.TimeoutError:
            logger.debug(f"Timeout: {url}")
            return None
        
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None
    
    def _classify_page(self, html: str, url: str) -> tuple[str, float]:
        """
        Classify page type and confidence.
        
        Args:
            html: Page HTML
            url: Page URL
        
        Returns:
            Tuple of (page_type, confidence)
        """
        soup = BeautifulSoup(html, 'lxml')
        scores = defaultdict(float)
        
        # URL pattern analysis
        url_lower = url.lower()
        for pattern in self.PROFILE_URL_PATTERNS:
            if re.search(pattern, url_lower):
                scores['profile'] += 0.3
        
        # Schema.org Person markup
        if soup.find(attrs={'itemtype': re.compile(r'schema.org/Person')}):
            scores['profile'] += 0.4
        
        # Profile-specific selectors
        profile_selectors = ['.profile', '.bio', '.person', '[itemtype*="Person"]']
        for selector in profile_selectors:
            if soup.select_one(selector):
                scores['profile'] += 0.1
        
        # Listing page indicators
        for selector in self.LISTING_SELECTORS:
            elements = soup.select(selector)
            if elements:
                scores['listing'] += 0.2
                # Check if listing contains multiple profiles
                profile_count = len(soup.select('.profile, .person, .team-member'))
                if profile_count > 3:
                    scores['listing'] += 0.3
        
        # Content analysis
        text = soup.get_text().lower()
        
        # Check for profile keywords
        keyword_count = sum(1 for kw in self.PROFILE_KEYWORDS if kw in text)
        if keyword_count > 0:
            scores['profile'] += min(keyword_count * 0.05, 0.2)
        
        # Check for contact information (strong profile indicator)
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            scores['profile'] += 0.15
        
        # Check for single person indicators
        heading_count = len(soup.find_all(['h1', 'h2']))
        if heading_count == 1:
            scores['profile'] += 0.1
        
        # Check for multiple profiles (listing indicator)
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        if h2_count > 3 or h3_count > 5:
            scores['listing'] += 0.2
        
        # Determine page type
        if not scores:
            return 'unknown', 0.0
        
        page_type = max(scores.items(), key=lambda x: x[1])
        return page_type[0], min(page_type[1], 1.0)
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all relevant links from HTML.
        
        Args:
            html: Page HTML
            base_url: Base URL for resolving relative links
        
        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = set()
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            
            # Skip anchors, mailto, tel, javascript
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            
            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)
            
            # Remove fragments and query params for deduplication
            parsed = urlparse(absolute_url)
            clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            
            # Validate
            if validators.url(clean_url):
                links.add(clean_url)
        
        return list(links)
    
    def _prioritize_links(self, links: List[str], base_url: str) -> List[str]:
        """
        Prioritize links based on likelihood of being profile pages.
        
        Args:
            links: List of URLs
            base_url: Base URL
        
        Returns:
            Sorted list of URLs (highest priority first)
        """
        scored_links = []
        
        for link in links:
            score = 0.0
            link_lower = link.lower()
            
            # URL pattern matching
            for pattern in self.PROFILE_URL_PATTERNS:
                if re.search(pattern, link_lower):
                    score += 0.5
            
            # Anchor text matching (if available)
            # Path depth (prefer moderate depth)
            depth = len(urlparse(link).path.split('/'))
            if 2 <= depth <= 4:
                score += 0.2
            
            # Same domain bonus
            if urlparse(link).netloc == urlparse(base_url).netloc:
                score += 0.1
            
            scored_links.append((link, score))
        
        # Sort by score (descending)
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        return [link for link, score in scored_links]
    
    def get_profile_candidates(self, min_confidence: float = 0.5) -> List[DiscoveredPage]:
        """
        Get discovered pages that are likely profiles.
        
        Args:
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of DiscoveredPage objects
        """
        return [
            page for page in self.discovered_pages.values()
            if page.page_type == 'profile' and page.confidence >= min_confidence
        ]
    
    def get_listing_pages(self) -> List[DiscoveredPage]:
        """Get discovered listing pages."""
        return [
            page for page in self.discovered_pages.values()
            if page.page_type == 'listing'
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        pages_by_type = defaultdict(int)
        for page in self.discovered_pages.values():
            pages_by_type[page.page_type] += 1
        
        return {
            'total_visited': len(self.visited_urls),
            'total_discovered': len(self.discovered_pages),
            'pages_by_type': dict(pages_by_type),
            'profile_candidates': len(self.get_profile_candidates()),
            'listing_pages': len(self.get_listing_pages())
        }


async def discover_and_extract(base_url: str, config: Dict[str, Any] = None) -> List[Any]:
    """
    Convenience function to discover and extract profiles in one go.
    
    Args:
        base_url: Starting URL
        config: Configuration dictionary
    
    Returns:
        List of ProfileData objects
    """
    from .profile_scraper import ProfileScraper
    
    profiles = []
    
    # Discovery phase
    async with ContentDiscovery(config) as discovery:
        profile_urls = await discovery.discover_profiles(base_url)
        logger.info(f"Discovery complete. Found {len(profile_urls)} potential profiles")
    
    # Extraction phase
    if profile_urls:
        async with ProfileScraper(config) as scraper:
            profiles = await scraper.extract_profiles_batch(profile_urls)
            logger.success(f"Extracted {len(profiles)} profiles")
    
    return profiles
