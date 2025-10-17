"""
Advanced knowledge discovery system.
Identifies relevant pages, extracts snippets, categorizes information,
and builds a comprehensive knowledge graph.
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field
from collections import defaultdict
import re

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import validators


@dataclass
class KnowledgeSnippet:
    """Represents an extracted knowledge snippet."""
    title: str
    content: str
    url: str
    content_type: str  # article, blog, documentation, profile, etc.
    category: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_urls: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class KnowledgeNode:
    """Node in the knowledge graph."""
    id: str
    url: str
    title: str
    content_type: str
    category: str
    relationships: Dict[str, List[str]] = field(default_factory=dict)  # relationship_type -> [node_ids]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SitemapAnalyzer:
    """Analyzes and parses website sitemaps."""
    
    def __init__(self):
        self.discovered_sitemaps: List[str] = []
        self.urls_from_sitemap: Set[str] = set()
    
    async def discover_sitemaps(self, base_url: str, session: aiohttp.ClientSession) -> List[str]:
        """
        Discover sitemap files from common locations.
        
        Args:
            base_url: Website base URL
            session: HTTP session
        
        Returns:
            List of sitemap URLs
        """
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Common sitemap locations
        sitemap_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap-index.xml',
            '/sitemap1.xml',
            '/sitemaps.xml',
            '/sitemap/sitemap.xml',
        ]
        
        sitemaps = []
        
        # Check robots.txt first
        try:
            robots_url = f"{domain}/robots.txt"
            async with session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    # Extract sitemap URLs from robots.txt
                    for line in robots_content.split('\n'):
                        if line.lower().startswith('sitemap:'):
                            sitemap_url = line.split(':', 1)[1].strip()
                            sitemaps.append(sitemap_url)
                            logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
        except Exception as e:
            logger.debug(f"Could not read robots.txt: {e}")
        
        # Try common sitemap paths
        for path in sitemap_paths:
            sitemap_url = urljoin(domain, path)
            try:
                async with session.get(sitemap_url) as response:
                    if response.status == 200:
                        sitemaps.append(sitemap_url)
                        logger.info(f"Found sitemap: {sitemap_url}")
            except Exception:
                pass
        
        self.discovered_sitemaps = list(set(sitemaps))
        return self.discovered_sitemaps
    
    async def parse_sitemap(self, sitemap_url: str, session: aiohttp.ClientSession) -> List[str]:
        """
        Parse sitemap XML and extract URLs.
        
        Args:
            sitemap_url: URL of the sitemap
            session: HTTP session
        
        Returns:
            List of URLs from sitemap
        """
        try:
            async with session.get(sitemap_url) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                
                # Parse XML
                root = ET.fromstring(content)
                
                # Handle sitemap index (contains references to other sitemaps)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                urls = []
                
                # Check if it's a sitemap index
                sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
                if sitemaps:
                    logger.info(f"Found sitemap index with {len(sitemaps)} sitemaps")
                    # Recursively parse child sitemaps
                    for sitemap in sitemaps:
                        child_urls = await self.parse_sitemap(sitemap.text, session)
                        urls.extend(child_urls)
                else:
                    # Regular sitemap with URLs
                    url_elements = root.findall('.//ns:url/ns:loc', namespace)
                    urls = [url.text for url in url_elements if url.text]
                    logger.info(f"Extracted {len(urls)} URLs from sitemap")
                
                self.urls_from_sitemap.update(urls)
                return urls
        
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []


class LinkPatternRecognizer:
    """Recognizes and categorizes link patterns."""
    
    # Pattern definitions for different content types
    PATTERNS = {
        'blog': [
            r'/blog/',
            r'/article/',
            r'/post/',
            r'/news/',
            r'/\d{4}/\d{2}/',  # Date-based URLs
        ],
        'documentation': [
            r'/docs/',
            r'/documentation/',
            r'/guide/',
            r'/tutorial/',
            r'/help/',
            r'/wiki/',
        ],
        'profile': [
            r'/team/',
            r'/people/',
            r'/staff/',
            r'/leadership/',
            r'/bio/',
            r'/profile/',
            r'/author/',
        ],
        'product': [
            r'/product/',
            r'/service/',
            r'/solution/',
            r'/offering/',
        ],
        'case_study': [
            r'/case-study/',
            r'/success-story/',
            r'/customer/',
            r'/testimonial/',
        ],
        'resource': [
            r'/resource/',
            r'/whitepaper/',
            r'/ebook/',
            r'/download/',
            r'/pdf/',
        ],
    }
    
    def recognize_pattern(self, url: str) -> Tuple[str, float]:
        """
        Recognize content type from URL pattern.
        
        Args:
            url: URL to analyze
        
        Returns:
            Tuple of (content_type, confidence)
        """
        url_lower = url.lower()
        
        for content_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return content_type, 0.8
        
        return 'unknown', 0.0
    
    def extract_url_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata from URL structure."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        metadata = {
            'domain': parsed.netloc,
            'path_depth': len(path_parts),
            'has_query': bool(parsed.query),
            'extension': path_parts[-1].split('.')[-1] if path_parts and '.' in path_parts[-1] else None,
        }
        
        # Try to extract date from URL
        date_match = re.search(r'/(\d{4})/(\d{2})/', url)
        if date_match:
            metadata['year'] = date_match.group(1)
            metadata['month'] = date_match.group(2)
        
        return metadata


class ContentTypeIdentifier:
    """Identifies content type from page content."""
    
    # Keywords for different content types
    CONTENT_KEYWORDS = {
        'article': ['article', 'read more', 'published', 'author', 'share this'],
        'blog': ['blog', 'posted by', 'comments', 'categories', 'tags'],
        'documentation': ['documentation', 'api', 'reference', 'guide', 'tutorial', 'example'],
        'profile': ['biography', 'contact', 'email', 'phone', 'linkedin', 'experience'],
        'product': ['features', 'pricing', 'buy now', 'demo', 'specifications'],
        'case_study': ['challenge', 'solution', 'results', 'customer', 'success'],
        'news': ['press release', 'announcement', 'breaking', 'latest news'],
    }
    
    def identify_from_html(self, html: str, url: str) -> Tuple[str, float]:
        """
        Identify content type from HTML.
        
        Args:
            html: Page HTML
            url: Page URL
        
        Returns:
            Tuple of (content_type, confidence)
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Check meta tags
        meta_type = self._check_meta_tags(soup)
        if meta_type:
            return meta_type, 0.9
        
        # Check Schema.org markup
        schema_type = self._check_schema_org(soup)
        if schema_type:
            return schema_type, 0.85
        
        # Check Open Graph tags
        og_type = self._check_open_graph(soup)
        if og_type:
            return og_type, 0.8
        
        # Analyze content and structure
        content_type = self._analyze_content(soup)
        if content_type:
            return content_type, 0.7
        
        # Fallback to URL pattern
        pattern_recognizer = LinkPatternRecognizer()
        return pattern_recognizer.recognize_pattern(url)
    
    def _check_meta_tags(self, soup: BeautifulSoup) -> Optional[str]:
        """Check meta tags for content type."""
        meta_type = soup.find('meta', attrs={'name': 'type'})
        if meta_type and meta_type.get('content'):
            return meta_type['content'].lower()
        return None
    
    def _check_schema_org(self, soup: BeautifulSoup) -> Optional[str]:
        """Check Schema.org markup."""
        schema_mapping = {
            'Article': 'article',
            'BlogPosting': 'blog',
            'NewsArticle': 'news',
            'Person': 'profile',
            'Product': 'product',
            'TechArticle': 'documentation',
        }
        
        for schema_type, content_type in schema_mapping.items():
            if soup.find(attrs={'itemtype': re.compile(f'schema.org/{schema_type}')}):
                return content_type
        return None
    
    def _check_open_graph(self, soup: BeautifulSoup) -> Optional[str]:
        """Check Open Graph tags."""
        og_type = soup.find('meta', attrs={'property': 'og:type'})
        if og_type and og_type.get('content'):
            og_content = og_type['content'].lower()
            if 'article' in og_content:
                return 'article'
            elif 'profile' in og_content:
                return 'profile'
        return None
    
    def _analyze_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Analyze page content and structure."""
        text = soup.get_text().lower()
        
        scores = defaultdict(int)
        
        for content_type, keywords in self.CONTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[content_type] += 1
        
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] >= 2:  # At least 2 keyword matches
                return best_type[0]
        
        return None


class KnowledgeCategorizer:
    """Categorizes content into knowledge categories."""
    
    # Category definitions with keywords
    CATEGORIES = {
        'Technical': [
            'api', 'code', 'programming', 'development', 'software',
            'technical', 'engineering', 'architecture', 'database', 'algorithm'
        ],
        'Business': [
            'business', 'strategy', 'market', 'sales', 'revenue',
            'growth', 'customer', 'roi', 'enterprise', 'commercial'
        ],
        'Leadership': [
            'leadership', 'management', 'executive', 'ceo', 'director',
            'vision', 'strategy', 'team', 'culture', 'organization'
        ],
        'Product': [
            'product', 'feature', 'functionality', 'solution', 'offering',
            'capability', 'specification', 'release', 'version'
        ],
        'Research': [
            'research', 'study', 'analysis', 'data', 'findings',
            'methodology', 'experiment', 'results', 'paper', 'publication'
        ],
        'Marketing': [
            'marketing', 'campaign', 'brand', 'content', 'social',
            'advertising', 'promotion', 'audience', 'engagement'
        ],
        'Support': [
            'support', 'help', 'faq', 'troubleshooting', 'guide',
            'tutorial', 'how-to', 'documentation', 'manual'
        ],
    }
    
    def categorize(self, content: str, title: str = "") -> Tuple[str, float]:
        """
        Categorize content.
        
        Args:
            content: Text content
            title: Content title
        
        Returns:
            Tuple of (category, confidence)
        """
        text = (title + " " + content).lower()
        
        scores = defaultdict(int)
        
        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                count = text.count(keyword)
                scores[category] += count
        
        if not scores:
            return 'General', 0.0
        
        best_category = max(scores.items(), key=lambda x: x[1])
        total_matches = sum(scores.values())
        confidence = best_category[1] / total_matches if total_matches > 0 else 0.0
        
        return best_category[0], min(confidence, 1.0)
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract key terms from content."""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b[a-z]{4,}\b', content.lower())
        
        # Filter common words
        stop_words = {
            'that', 'this', 'with', 'from', 'have', 'been', 'will',
            'their', 'there', 'which', 'what', 'when', 'where', 'about'
        }
        
        keywords = [w for w in words if w not in stop_words]
        
        # Count frequency
        keyword_freq = defaultdict(int)
        for keyword in keywords:
            keyword_freq[keyword] += 1
        
        # Return top keywords
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [k for k, v in sorted_keywords[:max_keywords]]


class RelationshipMapper:
    """Maps relationships between knowledge nodes."""
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.url_to_id: Dict[str, str] = {}
    
    def add_node(self, node: KnowledgeNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.url_to_id[node.url] = node.id
    
    def add_relationship(self, from_url: str, to_url: str, relationship_type: str = 'links_to'):
        """
        Add a relationship between nodes.
        
        Args:
            from_url: Source URL
            to_url: Target URL
            relationship_type: Type of relationship
        """
        from_id = self.url_to_id.get(from_url)
        to_id = self.url_to_id.get(to_url)
        
        if from_id and to_id and from_id in self.nodes:
            node = self.nodes[from_id]
            if relationship_type not in node.relationships:
                node.relationships[relationship_type] = []
            if to_id not in node.relationships[relationship_type]:
                node.relationships[relationship_type].append(to_id)
    
    def find_related_nodes(self, node_id: str, relationship_type: str = None) -> List[KnowledgeNode]:
        """Find nodes related to a given node."""
        if node_id not in self.nodes:
            return []
        
        node = self.nodes[node_id]
        related = []
        
        if relationship_type:
            related_ids = node.relationships.get(relationship_type, [])
        else:
            # All relationships
            related_ids = []
            for ids in node.relationships.values():
                related_ids.extend(ids)
        
        for rid in related_ids:
            if rid in self.nodes:
                related.append(self.nodes[rid])
        
        return related
    
    def get_node_by_url(self, url: str) -> Optional[KnowledgeNode]:
        """Get node by URL."""
        node_id = self.url_to_id.get(url)
        return self.nodes.get(node_id) if node_id else None
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        total_relationships = sum(
            len(relationships)
            for node in self.nodes.values()
            for relationships in node.relationships.values()
        )
        
        nodes_by_type = defaultdict(int)
        nodes_by_category = defaultdict(int)
        
        for node in self.nodes.values():
            nodes_by_type[node.content_type] += 1
            nodes_by_category[node.category] += 1
        
        return {
            'total_nodes': len(self.nodes),
            'total_relationships': total_relationships,
            'nodes_by_type': dict(nodes_by_type),
            'nodes_by_category': dict(nodes_by_category),
            'average_connections': total_relationships / len(self.nodes) if self.nodes else 0
        }


class KnowledgeDiscoverySystem:
    """
    Comprehensive knowledge discovery system.
    Integrates all discovery capabilities.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize discovery system."""
        self.config = config or {}
        self.sitemap_analyzer = SitemapAnalyzer()
        self.pattern_recognizer = LinkPatternRecognizer()
        self.content_identifier = ContentTypeIdentifier()
        self.categorizer = KnowledgeCategorizer()
        self.relationship_mapper = RelationshipMapper()
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.discovered_snippets: List[KnowledgeSnippet] = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        user_agent = self.config.get('user_agent', 'KnowledgeDiscoveryBot/1.0')
        timeout = self.config.get('timeout', 30)
        
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': user_agent},
            timeout=aiohttp.ClientTimeout(total=timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def discover_knowledge(self, base_url: str) -> List[KnowledgeSnippet]:
        """
        Comprehensive knowledge discovery.
        
        Args:
            base_url: Starting URL
        
        Returns:
            List of discovered knowledge snippets
        """
        logger.info(f"Starting knowledge discovery from: {base_url}")
        
        # Step 1: Discover and parse sitemaps
        sitemaps = await self.sitemap_analyzer.discover_sitemaps(base_url, self.session)
        logger.info(f"Found {len(sitemaps)} sitemaps")
        
        urls_to_process = set()
        for sitemap in sitemaps:
            sitemap_urls = await self.sitemap_analyzer.parse_sitemap(sitemap, self.session)
            urls_to_process.update(sitemap_urls)
        
        logger.info(f"Extracted {len(urls_to_process)} URLs from sitemaps")
        
        # Step 2: Process URLs in batches
        batch_size = 10
        url_list = list(urls_to_process)[:100]  # Limit for demo
        
        for i in range(0, len(url_list), batch_size):
            batch = url_list[i:i+batch_size]
            tasks = [self._process_url(url) for url in batch]
            snippets = await asyncio.gather(*tasks, return_exceptions=True)
            
            for snippet in snippets:
                if isinstance(snippet, KnowledgeSnippet):
                    self.discovered_snippets.append(snippet)
        
        logger.success(f"Discovered {len(self.discovered_snippets)} knowledge snippets")
        return self.discovered_snippets
    
    async def _process_url(self, url: str) -> Optional[KnowledgeSnippet]:
        """Process a single URL and extract knowledge."""
        try:
            # Fetch content
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract basic information
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            
            if not title or len(content) < 100:
                return None
            
            # Identify content type
            content_type, type_confidence = self.content_identifier.identify_from_html(html, url)
            
            # Categorize
            category, cat_confidence = self.categorizer.categorize(content, title)
            
            # Extract keywords
            keywords = self.categorizer.extract_keywords(content)
            
            # Extract links for relationship mapping
            related_urls = self._extract_links(soup, url)
            
            # Create knowledge node
            node_id = str(hash(url))
            node = KnowledgeNode(
                id=node_id,
                url=url,
                title=title,
                content_type=content_type,
                category=category,
                metadata={
                    'type_confidence': type_confidence,
                    'category_confidence': cat_confidence,
                }
            )
            self.relationship_mapper.add_node(node)
            
            # Map relationships
            for related_url in related_urls:
                self.relationship_mapper.add_relationship(url, related_url)
            
            # Create snippet
            snippet = KnowledgeSnippet(
                title=title,
                content=content[:1000],  # First 1000 chars
                url=url,
                content_type=content_type,
                category=category,
                keywords=keywords,
                related_urls=related_urls[:10],
                confidence=(type_confidence + cat_confidence) / 2,
                metadata={
                    'word_count': len(content.split()),
                    'has_images': bool(soup.find_all('img')),
                }
            )
            
            logger.debug(f"Processed: {title} ({content_type} - {category})")
            return snippet
        
        except Exception as e:
            logger.debug(f"Error processing {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try different title sources
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and og_title.get('content'):
            return og_title['content']
        
        return "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content."""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article'))
        )
        
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract internal links."""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            absolute_url = urljoin(base_url, href)
            
            # Only include same domain links
            if urlparse(absolute_url).netloc == base_domain:
                links.append(absolute_url)
        
        return links
    
    def get_knowledge_graph(self) -> RelationshipMapper:
        """Get the built knowledge graph."""
        return self.relationship_mapper
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        stats = {
            'total_snippets': len(self.discovered_snippets),
            'snippets_by_type': defaultdict(int),
            'snippets_by_category': defaultdict(int),
            'average_confidence': 0.0,
        }
        
        total_confidence = 0
        for snippet in self.discovered_snippets:
            stats['snippets_by_type'][snippet.content_type] += 1
            stats['snippets_by_category'][snippet.category] += 1
            total_confidence += snippet.confidence
        
        if self.discovered_snippets:
            stats['average_confidence'] = total_confidence / len(self.discovered_snippets)
        
        # Add graph statistics
        stats['knowledge_graph'] = self.relationship_mapper.get_graph_statistics()
        
        return dict(stats)
