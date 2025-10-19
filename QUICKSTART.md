# Quick Start Guide - Web Scraping System

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python -m src.database.migrations init
```

### 3. Configure (Optional)
Edit `config/scraping_targets.yaml` to add your target websites.

## 💡 Common Tasks

### Scrape a Website

**Single Command:**
```python
from src.services.scraping_service import ProfileScrapingService
import asyncio

async def scrape():
    service = ProfileScrapingService()
    profiles = await service.discover_and_extract("https://example.com/team")
    print(f"Extracted {len(profiles)} profiles")

asyncio.run(scrape())
```

**Or use CLI:**
```bash
python -m src.services.scraping_service scrape --url https://example.com/team
```

### Discover Profile Pages Only
```python
urls = await service.discover_profiles("https://example.com/team")
```

### Extract Single Profile
```python
profile = await service.extract_profile("https://example.com/team/john-doe")
print(f"{profile.name} - {profile.title}")
```

### Find Duplicates
```python
duplicates = service.find_duplicates()
for dup in duplicates:
    print(f"Potential duplicate: {dup[2]} vs {dup[3]}")
```

### Merge Duplicates
```python
service.merge_duplicate_profiles(primary_id=1, duplicate_id=2)
```

### Get Statistics
```python
stats = service.get_statistics()
print(f"Total profiles: {stats['total_profiles']}")
print(f"Success rate: {stats['scrape_logs']['success_rate']:.1f}%")
```

## 🔧 Configuration

### Rate Limiting
```yaml
# config/scraping_targets.yaml
settings:
  rate_limit:
    requests_per_second: 1
    delay_between_requests: 1.0
```

### Custom Selectors
```yaml
targets:
  - name: "My Company"
    url: "https://mycompany.com/team"
    config:
      selectors:
        name: "h2.employee-name"
        title: "p.job-title"
        bio: "div.biography"
        photo: "img.headshot"
```

### Discovery Settings
```python
config = {
    'max_depth': 3,          # How deep to follow links
    'max_pages': 100,        # Maximum pages to discover
    'same_domain_only': True,# Stay on same domain
    'rate_limit_delay': 1.0  # Delay between requests (seconds)
}
```

## 📊 Database Operations

### View Profiles
```python
from src.database.repository import DatabaseSession, ProfileRepository

db_session = DatabaseSession()
with db_session.get_session() as session:
    repo = ProfileRepository(session)
    
    # Get all profiles
    profiles = repo.get_all(limit=10)
    
    # Search by name
    results = repo.search("john")
    
    # Get by domain
    company_profiles = repo.get_by_domain("example.com")
```

### Update Profile
```python
with db_session.get_session() as session:
    repo = ProfileRepository(session)
    repo.update_profile(
        profile_id=1,
        title="Senior Engineer",
        email="newemail@example.com"
    )
```

### Backup Database
```bash
python -m src.database.migrations backup
```

### View Statistics
```bash
python -m src.database.migrations stats
```

## 🎯 Extraction Methods

The scraper tries three methods in order:

### 1. Schema.org (Highest Confidence)
```html
<div itemtype="http://schema.org/Person">
  <span itemprop="name">John Doe</span>
  <span itemprop="jobTitle">CEO</span>
</div>
```

### 2. CSS Selectors (Medium Confidence)
- Common patterns automatically detected
- Customizable via configuration

### 3. Heuristics (Lowest Confidence)
- Heading analysis
- Paragraph proximity
- Pattern matching

## 🔍 Discovery Patterns

### Automatically Detected URL Patterns:
- `/team/`
- `/leadership/`
- `/about/team`
- `/people/`
- `/staff/`
- `/bio/`
- `/profile/`
- `/executive/`

### Page Classification:
- **Profile:** Single person page (high confidence)
- **Listing:** Multiple profiles (triggers deeper crawl)
- **Content:** Articles, blogs (lower priority)

## ⚠️ Error Handling

### Automatic Retry
- 3 retries by default
- Exponential backoff
- Handles timeouts and rate limits

### Error Logging
All errors are logged to:
- Database (`scrape_logs` table)
- Log files (`logs/app.log`)
- Console (configurable level)

## 📈 Performance Tips

### 1. Batch Operations
```python
# Good: Batch extraction
profiles = await scraper.extract_profiles_batch(urls)

# Avoid: Sequential extraction
for url in urls:
    profile = await scraper.extract_profile(url)
```

### 2. Rate Limiting
```python
config = {'rate_limit_delay': 1.0}  # Respectful scraping
```

### 3. Limit Discovery Depth
```python
urls = await service.discover_profiles(url, max_depth=2)
```

## 🐛 Troubleshooting

### No Profiles Discovered
1. Check URL patterns match site structure
2. Verify site is accessible
3. Increase `max_depth`
4. Check logs for errors

### Low Confidence Scores
1. Review page HTML structure
2. Add custom selectors in config
3. Check for dynamic content (JavaScript)

### Rate Limit Errors (429)
1. Increase `rate_limit_delay`
2. Reduce concurrent requests
3. Check site's robots.txt

### Duplicate Profiles
1. Run `service.find_duplicates()`
2. Review potential matches
3. Merge with `service.merge_duplicate_profiles()`

## 📚 Examples

### Complete Example Script
```python
import asyncio
from src.services.scraping_service import ProfileScrapingService
from src.database.migrations import init_database

async def main():
    # Setup
    init_database()
    service = ProfileScrapingService()
    
    # Scrape
    profiles = await service.discover_and_extract(
        "https://example.com/team"
    )
    
    # Results
    print(f"\nExtracted {len(profiles)} profiles:")
    for p in profiles:
        print(f"  - {p.name}: {p.title}")
        print(f"    Confidence: {p.confidence_score:.2%}")
        print(f"    Contact: {p.email or 'N/A'}")
    
    # Stats
    stats = service.get_statistics()
    print(f"\nTotal in database: {stats['total_profiles']}")

if __name__ == '__main__':
    asyncio.run(main())
```

Run with:
```bash
python examples/scraping_example.py
```

## 🔗 Useful Commands

```bash
# Database
python -m src.database.migrations init          # Initialize
python -m src.database.migrations backup        # Backup
python -m src.database.migrations stats         # Statistics

# Scraping
python -m src.services.scraping_service discover --url URL
python -m src.services.scraping_service extract --url URL
python -m src.services.scraping_service scrape --url URL
python -m src.services.scraping_service stats

# Examples
python examples/scraping_example.py
```

## 📖 Documentation

- [Full Scraping Documentation](docs/SCRAPING.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Main README](README.md)

## 🆘 Need Help?

1. Check logs in `logs/app.log`
2. Review scrape_logs table for errors
3. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
4. See examples in `examples/scraping_example.py`

---

**Remember:** Always scrape responsibly!
- Respect robots.txt
- Use appropriate rate limiting
- Set a clear User-Agent
- Follow website terms of service
