# Web Scraping System - Technical Documentation

## Overview

The intelligent web scraping system implements automatic profile discovery, multi-template content extraction, contact parsing, and duplicate detection with error recovery.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  ProfileScrapingService                       │
│  (Orchestration Layer - Business Logic)                      │
└────────────┬────────────────────────────┬────────────────────┘
             │                            │
    ┌────────▼────────┐        ┌─────────▼──────────┐
    │ ContentDiscovery│        │  ProfileScraper    │
    │                 │        │                    │
    │ • Page Analysis │        │ • HTML Parsing     │
    │ • Link Discovery│        │ • Data Extraction  │
    │ • Classification│        │ • Confidence Score │
    └─────────────────┘        └────────────────────┘
             │                            │
             └────────────┬───────────────┘
                          │
                ┌─────────▼──────────┐
                │  Database Layer    │
                │                    │
                │ • Profile Repo     │
                │ • Deduplication    │
                │ • Merge Logic      │
                └────────────────────┘
```

## Core Components

### 1. ProfileScraper (`src/scrapers/profile_scraper.py`)

**Purpose:** Extract structured profile information from HTML pages.

**Key Features:**
- **Multi-Template Extraction:** Supports Schema.org, CSS selectors, and heuristics
- **Contact Parsing:** Regex patterns for emails and phone numbers
- **Photo Detection:** Multiple selector strategies for profile images
- **Confidence Scoring:** Calculates extraction reliability

**Extraction Methods:**

1. **Schema.org Markup** (Highest Confidence)
   ```html
   <div itemtype="http://schema.org/Person">
     <span itemprop="name">John Doe</span>
     <span itemprop="jobTitle">CEO</span>
   </div>
   ```

2. **CSS Selectors** (Medium Confidence)
   - Common patterns: `.profile-name`, `.title`, `.bio`
   - Customizable selector lists

3. **Heuristic Analysis** (Lower Confidence)
   - Heading analysis
   - Paragraph proximity
   - Pattern matching

**Usage Example:**
```python
async with ProfileScraper(config) as scraper:
    profile = await scraper.extract_profile(url)
    print(f"Name: {profile.name}")
    print(f"Confidence: {profile.confidence_score}")
```

### 2. ContentDiscovery (`src/scrapers/content_discovery.py`)

**Purpose:** Automatically discover profile pages through intelligent crawling.

**Discovery Strategies:**

1. **URL Pattern Analysis**
   - `/team/`, `/leadership/`, `/about/team`
   - `/people/`, `/staff/`, `/bio/`

2. **Page Classification**
   - Profile pages (single person)
   - Listing pages (multiple profiles)
   - Content pages (articles, blogs)

3. **Link Prioritization**
   - Scores links based on likelihood of being profiles
   - Prioritizes same-domain links
   - Respects depth limits

**Configuration:**
```python
config = {
    'max_depth': 3,          # Max link following depth
    'max_pages': 100,        # Max pages to discover
    'same_domain_only': True,# Stay on same domain
    'rate_limit_delay': 1.0  # Delay between requests
}
```

**Usage Example:**
```python
async with ContentDiscovery(config) as discovery:
    urls = await discovery.discover_profiles(base_url)
    stats = discovery.get_statistics()
```

### 3. ProfileScrapingService (`src/services/scraping_service.py`)

**Purpose:** Orchestrate discovery, extraction, and storage operations.

**Service Pattern Implementation:**

```python
class ProfileScrapingService:
    def __init__(self):
        # Initialize with discovery patterns
        pass
    
    async def discover_profiles(self, base_url: str) -> List[str]:
        # Intelligent page discovery
        pass
    
    async def extract_profile(self, url: str) -> ProfileData:
        # Structured information extraction
        pass
    
    async def extract_profiles_batch(self, urls: List[str]) -> List[ProfileData]:
        # Concurrent extraction
        pass
    
    async def discover_and_extract(self, base_url: str) -> List[ProfileData]:
        # Combined operation
        pass
```

**Features:**
- Automatic duplicate detection
- Database persistence
- Scrape logging and statistics
- Configuration-based scraping
- Error recovery and retry logic

## Database Models

### Profile Model
```python
class Profile:
    # Core Information
    name: str
    title: str
    bio: text
    
    # Contact Information
    email: str
    phone: str
    linkedin: str
    twitter: str
    website: str
    
    # Source & Metadata
    source_url: str (unique)
    source_domain: str (indexed)
    confidence_score: float
    extraction_method: str
    
    # Media
    photo_url: str
    photo_local_path: str
    
    # Status
    scrape_status: str (pending/completed/failed)
    is_active: bool
    is_verified: bool
```

### Key Features:
- **Indexes:** Optimized for name, title, domain, and status queries
- **Unique Constraints:** Prevent duplicate URLs
- **Relationships:** Links to content, categories, and embeddings
- **JSON Fields:** Flexible metadata storage

## Duplicate Detection & Merging

### Detection Strategies:

1. **URL-Based** (Primary)
   ```python
   existing = profile_repo.get_by_url(source_url)
   ```

2. **Name Similarity** (Secondary)
   ```python
   duplicates = profile_repo.find_duplicates()
   # Uses SequenceMatcher with 80% threshold
   ```

### Merge Logic:
```python
def merge_profiles(primary_id, duplicate_id):
    # Keep non-empty values from duplicate
    # Move relationships to primary
    # Delete duplicate
    # Return merged profile
```

## Error Handling & Recovery

### Retry Logic:
- Configurable max retries (default: 3)
- Exponential backoff for rate limiting
- Timeout handling

### Error Logging:
```python
ScrapeLog:
    url: str
    status: str (success/failed/skipped)
    errors: JSON
    duration_seconds: float
    profiles_extracted: int
```

## Configuration

### Scraping Targets (`config/scraping_targets.yaml`)

```yaml
targets:
  - name: "Company Leadership"
    url: "https://example.com/leadership"
    type: "profile"
    enabled: true
    config:
      follow_links: true
      max_depth: 2
      selectors:
        name: "h2.name"
        title: "p.title"
        bio: "div.bio"

settings:
  rate_limit:
    requests_per_second: 1
    delay_between_requests: 1.0
  
  retry:
    max_attempts: 3
    backoff_factor: 2
    timeout: 30
```

## Usage Examples

### 1. Discover Profiles from URL
```python
from src.services.scraping_service import ProfileScrapingService

service = ProfileScrapingService()
urls = await service.discover_profiles("https://example.com/team")
print(f"Found {len(urls)} profile URLs")
```

### 2. Extract Single Profile
```python
profile = await service.extract_profile("https://example.com/team/john-doe")
print(f"Name: {profile.name}")
print(f"Title: {profile.title}")
print(f"Email: {profile.email}")
```

### 3. Full Discovery & Extraction
```python
profiles = await service.discover_and_extract("https://example.com/team")
print(f"Extracted {len(profiles)} profiles")

for profile in profiles:
    print(f"- {profile.name}: {profile.title}")
```

### 4. Scrape from Configuration
```python
results = await service.scrape_from_config()
print(f"Scraped {results['targets_scraped']} targets")
print(f"Extracted {results['profiles_extracted']} profiles")
```

### 5. Find and Merge Duplicates
```python
# Find duplicates
duplicates = service.find_duplicates()
for dup in duplicates:
    print(f"Potential duplicate: {dup[2]} vs {dup[3]}")

# Merge specific profiles
service.merge_duplicate_profiles(primary_id=1, duplicate_id=2)
```

## Command-Line Interface

```bash
# Discover profile URLs
python -m src.services.scraping_service discover --url https://example.com/team

# Extract single profile
python -m src.services.scraping_service extract --url https://example.com/team/john-doe

# Full scrape (discover + extract)
python -m src.services.scraping_service scrape --url https://example.com/team

# Show statistics
python -m src.services.scraping_service stats
```

## Performance Optimization

### 1. Concurrent Extraction
```python
# Batch processing with asyncio
profiles = await scraper.extract_profiles_batch(urls)
```

### 2. Rate Limiting
- Configurable delay between requests
- Respects 429 (Too Many Requests) responses
- Exponential backoff on errors

### 3. Database Optimization
- Indexed fields for fast lookups
- WAL mode for SQLite
- Batch inserts for performance

### 4. Caching
- Visited URLs tracking
- Profile deduplication
- HTML content caching (optional)

## Best Practices

### 1. Respectful Scraping
- Set appropriate `User-Agent`
- Respect `robots.txt` (configurable)
- Implement rate limiting
- Use timeouts

### 2. Data Quality
- Validate extracted data
- Calculate confidence scores
- Store raw HTML for reprocessing
- Track extraction methods

### 3. Error Handling
- Log all scraping activities
- Implement retry logic
- Handle timeouts gracefully
- Store error details

### 4. Maintenance
- Regular duplicate checks
- Update stale profiles
- Monitor scrape logs
- Review failed scrapes

## Testing

### Unit Tests
```python
# Test extraction methods
def test_schema_org_extraction():
    html = '<div itemtype="http://schema.org/Person">...</div>'
    profile = extractor.extract_profile(html, url, base_url)
    assert profile.name == "John Doe"
```

### Integration Tests
```python
# Test full workflow
async def test_discover_and_extract():
    profiles = await service.discover_and_extract(test_url)
    assert len(profiles) > 0
    assert profiles[0].confidence_score > 0.5
```

## Troubleshooting

### Common Issues:

1. **No profiles discovered**
   - Check URL patterns in configuration
   - Verify site structure
   - Increase max_depth

2. **Low confidence scores**
   - Review extraction selectors
   - Check for dynamic content
   - Examine raw HTML

3. **Rate limiting errors**
   - Increase delay between requests
   - Reduce concurrent requests
   - Implement exponential backoff

4. **Duplicate profiles**
   - Run duplicate detection
   - Merge duplicates manually
   - Improve URL normalization

## Future Enhancements

- [ ] JavaScript rendering support (Selenium/Playwright)
- [ ] Image download and storage
- [ ] Natural language processing for bio analysis
- [ ] Machine learning for selector generation
- [ ] Distributed scraping with Celery
- [ ] Real-time monitoring dashboard
- [ ] API rate limit auto-detection
- [ ] Proxy rotation support

## Related Documentation

- [Database Models](../database/README.md)
- [Configuration Guide](../../config/README.md)
- [API Reference](../API.md)
