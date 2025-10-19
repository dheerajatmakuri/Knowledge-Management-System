# 🔍 Hybrid Search Engine - Quick Reference

## Quick Start

```python
from app_hybrid_search import ProductionHybridSearchService

# Initialize
service = ProductionHybridSearchService()

# Search
result = service.search("machine learning engineer", k=10)

# Display results
for r in result['results']:
    print(f"{r['rank']}. {r['content']['name']} - {r['score']:.2%}")
```

## Common Patterns

### Basic Search
```python
result = service.search(query="data scientist", k=5)
```

### Filtered Search
```python
result = service.search(
    query="python developer",
    filters={'is_verified': True, 'min_confidence': 0.8}
)
```

### Profile Search
```python
result = service.search_profiles(
    query="software engineer",
    verified_only=True,
    min_confidence=0.7
)
```

### Knowledge Search
```python
result = service.search_knowledge(
    query="machine learning",
    category="technical",
    validated_only=True
)
```

### Faceted Search
```python
result = service.search(
    query="web development",
    include_facets=True
)
print(result['facets'])
```

## Weight Presets

### Semantic-First (AI-Powered)
```python
service.update_search_config(
    vector_weight=0.8,
    fulltext_weight=0.1,
    metadata_weight=0.1
)
```

### Keyword-Focused (Traditional)
```python
service.update_search_config(
    vector_weight=0.2,
    fulltext_weight=0.7,
    metadata_weight=0.1
)
```

### Balanced (Default)
```python
service.update_search_config(
    vector_weight=0.5,
    fulltext_weight=0.3,
    metadata_weight=0.2
)
```

## Fusion Methods

```python
# Weighted sum (default) - linear combination
config.fusion_method = 'weighted_sum'

# Reciprocal rank - rank-based fusion
config.fusion_method = 'reciprocal_rank'

# Max score - takes maximum
config.fusion_method = 'max'
```

## Common Filters

### Profile Filters
```python
filters = {
    'is_verified': True,           # Verified profiles only
    'min_confidence': 0.8,         # Minimum confidence score
    'source_domain': 'linkedin.com', # Specific source
    'created_after': datetime(2024, 1, 1)  # Recent only
}
```

### Snippet Filters
```python
filters = {
    'category': 'machine-learning',  # Specific category
    'content_type': 'technical',     # Content type
    'is_validated': True,            # Validated only
    'min_confidence': 0.7            # Minimum confidence
}
```

## Response Format

```python
{
    "success": True,
    "query": "machine learning",
    "total_results": 5,
    "search_time": 0.045,
    "results": [
        {
            "rank": 1,
            "entity_type": "profile",
            "entity_id": 1,
            "score": 0.826,
            "content": {...},
            "metadata": {
                "score_breakdown": {
                    "vector": 0.85,
                    "fulltext": 0.72,
                    "metadata": 1.0
                }
            }
        }
    ],
    "facets": {...}
}
```

## Performance Tips

1. **Use FAISS backend** (default) for fast similarity search
2. **Lower k parameter** if you only need top results
3. **Add filters** to narrow search space
4. **Set min_score** to filter low-quality results
5. **Disable unused methods** if not needed

## Monitoring

```python
# Get statistics
stats = service.get_statistics()
print(f"Indexed: {stats['database']['vectors']}")
print(f"Dimension: {stats['vector_search']['dimension']}")

# Check configuration
config = stats['hybrid_search']['config']
print(f"Weights: V={config['vector_weight']}, T={config['fulltext_weight']}")
```

## Indexing

```python
# Index all content
service.index_all_content()

# Add and index new profile
service.add_and_index_profile({
    'name': 'Jane Smith',
    'title': 'ML Engineer',
    'bio': 'Expert in deep learning...'
})

# Add and index new snippet
service.add_and_index_snippet({
    'title': 'Introduction to NLP',
    'content': 'Natural language processing...',
    'category': 'machine-learning'
})
```

## Files

- **`src/search/hybrid_search.py`** - Core engine (710 lines)
- **`app_hybrid_search.py`** - Production service (630 lines)
- **`demo_hybrid_search.py`** - Full demonstration (440 lines)
- **`docs/HYBRID_SEARCH.md`** - Complete documentation (550 lines)
- **`HYBRID_SEARCH_SUMMARY.md`** - Implementation summary

## Documentation

See `docs/HYBRID_SEARCH.md` for:
- Architecture details
- Advanced features
- Troubleshooting
- Performance optimization
- API reference

---

Copyright 2025 Amzur. All rights reserved.
