# 🚀 Quick Start - Vector Search

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `sentence-transformers` - For local embeddings
- `faiss-cpu` - For fast similarity search
- `numpy` - For numerical operations
- `openai` - For OpenAI embeddings (optional)

## Step 2: Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Option A: Free Local Embeddings (Recommended to Start)

```bash
# In .env
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
SEARCH_BACKEND=faiss
SEARCH_METRIC=cosine
```

### Option B: OpenAI Embeddings (Better Quality, Requires API Key)

```bash
# In .env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-your-actual-api-key-here
SEARCH_BACKEND=faiss
SEARCH_METRIC=cosine
```

**Get OpenAI API Key:** https://platform.openai.com/api-keys

## Step 3: Test Installation

```bash
python tests/test_vector_search.py
```

Expected output:
```
✅ PASS: Vectorization
✅ PASS: Similarity Algorithms
✅ PASS: Relevance Scoring
✅ PASS: Query Expansion
✅ PASS: Vector Search
✅ PASS: Integration

🎯 Results: 6/6 tests passed
🎉 All tests passed! System is ready to use.
```

## Step 4: Run Examples

```bash
python examples/search_example.py
```

This will:
1. Initialize the search service
2. Index content (if available)
3. Run semantic searches
4. Show filtered searches
5. Demonstrate similarity search
6. Compare providers (if both configured)
7. Offer interactive search mode

## Step 5: Use in Your Code

```python
from src.database.migrations import DatabaseSession
from src.services.search_service import create_search_service

# Initialize
db_session = DatabaseSession('data/profiles.db')
search_service = create_search_service(db_session)

# Index content (first time only)
stats = search_service.rebuild_index()
print(f"Indexed {stats['total_indexed']} items")

# Search
results = search_service.search(
    query="machine learning engineer",
    k=10,
    min_score=0.5
)

# Display results
for result in results.results:
    print(f"{result.rank}. Score: {result.score:.3f}")
    print(f"   Type: {result.entity_type}")
    print(f"   Content: {result.content}")
```

## Common Commands

### Index Content
```python
# Index everything
stats = search_service.rebuild_index()

# Index specific types
search_service.indexer.index_profiles()
search_service.indexer.index_snippets()
search_service.indexer.index_content()
```

### Search
```python
# General search
results = search_service.search("query", k=10)

# Search profiles only
results = search_service.search_profiles("query", k=5)

# Search snippets only
results = search_service.search_snippets("query", k=5)

# Find similar items
similar = search_service.find_similar('profile', 123, k=10)
```

### Get Statistics
```python
stats = search_service.get_statistics()
print(stats)
```

## Troubleshooting

### "Import could not be resolved"
```bash
pip install sentence-transformers faiss-cpu numpy openai
```

### "OPENAI_API_KEY not found"
Either:
1. Add to `.env`: `OPENAI_API_KEY=sk-your-key`
2. Use Sentence Transformers instead: `EMBEDDING_PROVIDER=sentence-transformers`

### "No module named 'faiss'"
```bash
pip install faiss-cpu
# For GPU: pip install faiss-gpu
```

### Memory Issues
- Use smaller model: `all-MiniLM-L6-v2` (384 dim)
- Reduce batch size: `EMBEDDINGS_BATCH_SIZE=16`
- Use Annoy: `SEARCH_BACKEND=annoy`

## Performance Tips

| Dataset Size | Recommended Config |
|-------------|-------------------|
| < 1K items | Backend: brute, Model: any |
| 1K - 100K | Backend: faiss, Model: MiniLM-L6 |
| 100K - 1M | Backend: faiss, Model: MiniLM-L6, GPU: true |
| > 1M | Backend: faiss, Model: MiniLM-L6, GPU: required |

## What's Next?

- ✅ Integrate with chat assistant
- ✅ Build UI for search
- ✅ Add advanced filters
- ✅ Implement relevance feedback
- ✅ Add more query expansion rules

## Resources

- **Full Documentation:** `docs/VECTOR_SEARCH.md`
- **Implementation Summary:** `VECTOR_SEARCH_SUMMARY.md`
- **Examples:** `examples/search_example.py`
- **Tests:** `tests/test_vector_search.py`

---

**Ready to search! 🚀**

Questions? Check the full documentation in `docs/VECTOR_SEARCH.md`
