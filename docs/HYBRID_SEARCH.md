# Hybrid Search Engine - Production Documentation

## Overview

The **Hybrid Search Engine** combines three powerful search methods to provide the most comprehensive and accurate knowledge retrieval:

1. **Full-Text Search** - Traditional keyword matching across content
2. **Vector Similarity** - Semantic search using AI embeddings  
3. **Metadata Filtering** - Faceted search with structured filters

### Architecture

```
┌─────────────────────────────────────────────────────┐
│             Hybrid Search Engine                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Full-Text   │  │    Vector    │  │ Metadata  │ │
│  │    Search    │  │  Similarity  │  │ Filtering │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│         │                 │                 │       │
│         └────────┬────────┴─────────────────┘       │
│                  │                                   │
│         ┌────────▼────────┐                         │
│         │  Result Fusion  │                         │
│         │   & Ranking     │                         │
│         └────────┬────────┘                         │
│                  │                                   │
│         ┌────────▼────────┐                         │
│         │ Enriched Results│                         │
│         └─────────────────┘                         │
└─────────────────────────────────────────────────────┘
```

## Features

### 1. Full-Text Search Engine (`FullTextSearchEngine`)

**Purpose:** Fast keyword-based search using SQL LIKE queries

**Features:**
- Case-insensitive matching
- Multi-field search (name, title, bio, content)
- Weighted scoring (name: 0.5, title: 0.3, bio/content: 0.2)
- Entity type filtering

**Example:**
```python
fulltext_engine = FullTextSearchEngine(db_session)
results = fulltext_engine.search(
    query="machine learning",
    entity_types=['profile', 'snippet'],
    k=10
)
```

### 2. Vector Similarity Search

**Purpose:** Semantic search using AI embeddings

**Features:**
- OpenAI embeddings (text-embedding-3-small, 1536 dims) or Sentence Transformers (384 dims)
- FAISS backend for fast similarity search
- Cosine similarity metric
- Query expansion for better recall

**Example:**
```python
from src.search.vector_search import VectorSearch

vector_search = VectorSearch(dimension=384, backend='faiss', metric='cosine')
query_vector = vectorizer.encode_single("deep learning expert")
results = vector_search.search(query_vector, k=10)
```

### 3. Metadata Filtering Engine (`MetadataFilterEngine`)

**Purpose:** Filter and score results based on structured metadata

**Supported Filters:**
- **Profiles:** `is_verified`, `source_domain`, `min_confidence`, `created_after`
- **Snippets:** `category`, `content_type`, `is_validated`, `min_confidence`
- **Content:** `content_type`, `author`

**Example:**
```python
filters = {
    'is_verified': True,
    'min_confidence': 0.8,
    'source_domain': 'linkedin.com'
}

metadata_engine = MetadataFilterEngine(db_session)
scored_results = metadata_engine.filter_and_score(candidates, filters)
```

### 4. Faceted Search

**Purpose:** Generate aggregated counts for filtering

**Supported Facets:**
- `source_domain` - Group by data source
- `category` - Group by knowledge category
- `content_type` - Group by content type
- `is_verified` - Verified vs unverified
- `author` - Group by author

**Example:**
```python
facets = metadata_engine.get_facets(
    results=search_results,
    facet_fields=['category', 'content_type', 'source_domain']
)

# Returns:
# {
#   'category': {'machine-learning': 15, 'web-development': 8},
#   'content_type': {'technical': 12, 'tutorial': 11},
#   'source_domain': {'github.com': 20, 'stackoverflow.com': 3}
# }
```

### 5. Result Fusion Algorithms (`ResultFusionEngine`)

**Purpose:** Combine results from multiple search methods into unified ranking

#### Weighted Sum Fusion (Default)
- Linearly combines scores with configurable weights
- Formula: `total_score = (vector_score × v_weight) + (fulltext_score × t_weight) + (metadata_score × m_weight)`
- Best for: Balanced search with explicit preference control

```python
config = HybridSearchConfig(
    vector_weight=0.5,     # 50% weight to semantic similarity
    fulltext_weight=0.3,   # 30% weight to keyword matching
    metadata_weight=0.2,   # 20% weight to metadata filters
    fusion_method='weighted_sum'
)
```

#### Reciprocal Rank Fusion (RRF)
- Rank-based fusion using formula: `score = Σ(1 / (k + rank))`
- Less sensitive to score calibration differences
- Best for: When combining methods with different score scales

```python
config.fusion_method = 'reciprocal_rank'
```

#### Max Score Fusion
- Takes maximum score across all methods
- Formula: `total_score = max(vector_score, fulltext_score, metadata_score)`
- Best for: When any single strong signal should dominate

```python
config.fusion_method = 'max'
```

## Production Usage

### Basic Search

```python
from app_hybrid_search import ProductionHybridSearchService

# Initialize service
service = ProductionHybridSearchService(
    db_path="data/profiles.db",
    vector_weight=0.5,
    fulltext_weight=0.3,
    metadata_weight=0.2,
    fusion_method='weighted_sum'
)

# Perform search
result = service.search(
    query="machine learning engineer",
    k=10,
    min_score=0.3,
    include_scores=True
)

print(f"Found {result['total_results']} results in {result['search_time']:.3f}s")
for r in result['results']:
    print(f"  {r['rank']}. [{r['entity_type']}] {r['content']['name']} - {r['score']:.3f}")
```

### Profile Search with Filters

```python
result = service.search_profiles(
    query="data scientist",
    k=5,
    verified_only=True,
    min_confidence=0.8,
    source_domain="linkedin.com"
)
```

### Knowledge Search with Categories

```python
result = service.search_knowledge(
    query="transformer architecture",
    k=5,
    category="machine-learning",
    content_type="technical",
    validated_only=True
)
```

### Advanced Search with Custom Configuration

```python
result = service.advanced_search(
    query="cloud infrastructure",
    k=10,
    entity_types=['profile', 'snippet'],
    filters={
        'is_verified': True,
        'category': 'devops',
        'min_confidence': 0.7
    },
    weights={
        'vector': 0.4,
        'fulltext': 0.4,
        'metadata': 0.2
    },
    fusion_method='reciprocal_rank'
)
```

### Search with Facets

```python
result = service.search(
    query="python programming",
    k=20,
    include_facets=True
)

# Access facets
facets = result['facets']
for field, counts in facets.items():
    print(f"{field}:")
    for value, count in counts.items():
        print(f"  {value}: {count}")
```

## Performance Optimization

### 1. Indexing Strategy

```python
# Index all content at startup
service.index_all_content()

# Auto-index new content
profile_id = service.add_and_index_profile({
    'name': 'John Doe',
    'title': 'ML Engineer',
    'bio': 'Expert in deep learning...'
})

snippet_id = service.add_and_index_snippet({
    'title': 'Neural Networks 101',
    'content': 'Introduction to neural networks...',
    'category': 'machine-learning'
})
```

### 2. Weight Tuning

```python
# Adjust weights dynamically based on use case
service.update_search_config(
    vector_weight=0.7,    # Emphasize semantic search
    fulltext_weight=0.2,  # De-emphasize keyword matching
    metadata_weight=0.1
)
```

### 3. Caching (Future Enhancement)

```python
# Enable result caching
config = HybridSearchConfig(enable_caching=True)
```

## Score Breakdown

When `include_scores=True`, each result includes detailed scoring:

```json
{
  "rank": 1,
  "entity_type": "profile",
  "entity_id": 42,
  "score": 0.735,
  "metadata": {
    "score_breakdown": {
      "total": 0.735,
      "vector": 0.82,      // Semantic similarity score
      "fulltext": 0.65,    // Keyword match score
      "metadata": 1.0,     // Filter match score
      "rank": 0.015        // RRF rank contribution
    },
    "fusion_method": "weighted_sum",
    "search_methods": ["vector", "fulltext", "metadata"]
  }
}
```

## API Response Format

```python
{
    "success": True,
    "query": "machine learning expert",
    "total_results": 5,
    "search_time": 0.045,
    "algorithm": "hybrid",
    "results": [
        {
            "rank": 1,
            "entity_type": "profile",
            "entity_id": 1,
            "score": 0.626,
            "content": {
                "id": 1,
                "name": "Dr. Sarah Johnson",
                "title": "Machine Learning Engineer",
                "bio": "Expert in deep learning...",
                "is_verified": True,
                "confidence_score": 0.95
            },
            "metadata": {
                "score_breakdown": {...},
                "fusion_method": "weighted_sum"
            }
        }
    ],
    "facets": {
        "source_domain": {"linkedin.com": 3, "github.com": 2},
        "is_verified": {"Verified": 4, "Unverified": 1}
    },
    "config": {
        "vector_weight": 0.5,
        "fulltext_weight": 0.3,
        "metadata_weight": 0.2,
        "fusion_method": "weighted_sum"
    }
}
```

## Statistics and Monitoring

```python
stats = service.get_statistics()

# Returns:
{
    "database": {
        "profiles": 150,
        "snippets": 320,
        "content": 500,
        "vectors": 970
    },
    "vector_search": {
        "dimension": 384,
        "total_indexed": 970,
        "backend": "faiss",
        "metric": "cosine"
    },
    "hybrid_search": {
        "config": {
            "vector_weight": 0.5,
            "fulltext_weight": 0.3,
            "metadata_weight": 0.2,
            "fusion_method": "weighted_sum"
        },
        "enabled_methods": {
            "vector": True,
            "fulltext": True,
            "metadata": True
        }
    },
    "timestamp": "2025-10-16T20:37:05Z"
}
```

## Configuration Options

### HybridSearchConfig

```python
from src.search.hybrid_search import HybridSearchConfig

config = HybridSearchConfig(
    # Weights (must sum to 1.0 after normalization)
    vector_weight=0.5,        # Weight for vector similarity
    fulltext_weight=0.3,      # Weight for full-text search
    metadata_weight=0.2,      # Weight for metadata matching
    
    # Method toggles
    use_vector=True,          # Enable vector search
    use_fulltext=True,        # Enable full-text search
    use_metadata=True,        # Enable metadata filtering
    
    # Fusion strategy
    fusion_method='weighted_sum',  # 'weighted_sum', 'reciprocal_rank', 'max'
    
    # Performance
    enable_caching=True,      # Enable result caching (future)
    parallel_search=True      # Parallel search execution (future)
)
```

## Use Case Examples

### 1. Semantic-First Search (AI-Powered)

```python
service.update_search_config(
    vector_weight=0.8,
    fulltext_weight=0.1,
    metadata_weight=0.1
)
result = service.search("AI ethics and responsible ML")
```

### 2. Keyword-Focused Search (Traditional)

```python
service.update_search_config(
    vector_weight=0.2,
    fulltext_weight=0.7,
    metadata_weight=0.1
)
result = service.search("Python Flask REST API")
```

### 3. Metadata-Driven Search (Filtered)

```python
service.update_search_config(
    vector_weight=0.3,
    fulltext_weight=0.3,
    metadata_weight=0.4
)
result = service.search(
    query="software engineer",
    filters={
        'is_verified': True,
        'min_confidence': 0.9,
        'source_domain': 'linkedin.com',
        'created_after': datetime(2024, 1, 1)
    }
)
```

## Performance Benchmarks

Based on production testing with 5 profiles:

| Metric | Value |
|--------|-------|
| Search time | 25-45ms |
| Indexing time | 100-150ms per item |
| Vector dimension | 384 (sentence-transformers) or 1536 (OpenAI) |
| FAISS memory | ~4KB per vector |
| Accuracy | 60-65% on semantic queries |

## Troubleshooting

### No Results Returned

**Issue:** Search returns 0 results

**Solutions:**
1. Check if content is indexed: `service.get_statistics()`
2. Lower `min_score` threshold
3. Verify vectors loaded: Check logs for "Loaded X vectors from database"
4. Ensure query matches entity types being searched

### Slow Search Performance

**Issue:** Search takes >500ms

**Solutions:**
1. Use FAISS backend (not brute-force)
2. Reduce `k` parameter
3. Disable unused search methods
4. Check database indexes exist

### Inconsistent Scoring

**Issue:** Results have unexpected scores

**Solutions:**
1. Review weight configuration
2. Check score breakdown with `include_scores=True`
3. Try different fusion methods
4. Verify vector normalization

## Future Enhancements

1. **Query Understanding**
   - Intent classification
   - Entity recognition
   - Query spelling correction

2. **Advanced Ranking**
   - Learning-to-rank models
   - Personalized ranking
   - Click-through rate optimization

3. **Performance**
   - Async search execution
   - Distributed index sharding
   - GPU acceleration

4. **Features**
   - Multi-language support
   - Image and video search
   - Temporal relevance decay

## License

Copyright 2025 Amzur. All rights reserved.

## Support

For issues or questions, please contact the development team.
