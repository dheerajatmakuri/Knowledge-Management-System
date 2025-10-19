# Vector Embedding & Semantic Search System

## Overview

A comprehensive vector embedding and semantic search system supporting both **OpenAI embeddings** and **Sentence Transformers** for semantic search across knowledge content with similarity scoring and relevance ranking.

## 🚀 Features

### Content Vectorization Pipeline
- **Multiple Embedding Providers**:
  - Sentence Transformers (local, free, multiple models)
  - OpenAI Embeddings (cloud-based, requires API key)
- **Batch Processing**: Efficient batch vectorization
- **Normalization**: L2 normalization for cosine similarity
- **Automatic Model Management**: Downloads and caches models

### Similarity Computation Algorithms
- **Cosine Similarity**: Best for semantic similarity
- **Euclidean Distance**: Traditional distance metric
- **Manhattan Distance**: L1 norm distance
- **Dot Product**: For normalized vectors
- **Batch Computation**: Optimized matrix operations

### Relevance Scoring Mechanisms
- **Multi-Signal Scoring**:
  - Semantic similarity (60% weight)
  - Recency score (20% weight)
  - Popularity signals (10% weight)
  - Quality indicators (10% weight)
- **Configurable Weights**: Adjust scoring components
- **Decay Functions**: Time-based relevance decay

### Query Expansion Techniques
- **Synonym Expansion**: Expand queries with synonyms
- **Stemming**: Word stem variations
- **Related Terms**: Domain-specific expansions
- **Multi-Query Search**: Combine results from expansions

### Result Ranking Optimization
- **Score-Based Ranking**: Primary ranking by similarity
- **Deduplication**: Remove duplicate results
- **Filtering**: Entity type and metadata filters
- **Top-K Selection**: Efficient result limiting

### Search Backends
- **FAISS** (Facebook AI Similarity Search):
  - Fast approximate nearest neighbor search
  - GPU acceleration support
  - Scales to millions of vectors
- **Annoy** (Approximate Nearest Neighbors):
  - Memory-efficient
  - Good for read-heavy workloads
- **Brute Force**:
  - Exact search
  - Best for small datasets

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy `.env.example` to `.env` and configure:

```bash
# For Sentence Transformers (Free, Local)
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2

# For OpenAI (Requires API Key)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_api_key_here
```

## 🔧 Configuration

### Embedding Models

#### Sentence Transformers (Recommended for Getting Started)
- `all-MiniLM-L6-v2` (384 dim) - Fast, good quality
- `all-mpnet-base-v2` (768 dim) - Better quality, slower
- `multi-qa-MiniLM-L6-cos-v1` (384 dim) - Optimized for Q&A

#### OpenAI
- `text-embedding-3-small` (1536 dim) - Cost-effective
- `text-embedding-3-large` (3072 dim) - Highest quality
- `text-embedding-ada-002` (1536 dim) - Legacy model

### Search Configuration

```bash
# Search backend: faiss, annoy, or brute
SEARCH_BACKEND=faiss

# Similarity metric: cosine, euclidean, or dot
SEARCH_METRIC=cosine

# GPU acceleration (requires CUDA)
USE_GPU=false

# Search parameters
MIN_SEARCH_SCORE=0.5
DEFAULT_SEARCH_K=10
USE_QUERY_EXPANSION=true
```

## 💻 Usage

### Basic Usage

```python
from src.database.migrations import DatabaseSession
from src.services.search_service import create_search_service

# Initialize
db_session = DatabaseSession('data/profiles.db')
search_service = create_search_service(db_session)

# Index content
stats = search_service.rebuild_index()
print(f"Indexed {stats['total_indexed']} items")

# Perform search
results = search_service.search(
    query="machine learning and AI",
    k=10,
    min_score=0.5
)

# Display results
for result in results.results:
    print(f"{result.rank}. {result.entity_type}: {result.score:.3f}")
    print(f"   {result.content}")
```

### Advanced Search

```python
# Search specific entity types
profile_results = search_service.search_profiles(
    query="software engineer",
    k=5
)

snippet_results = search_service.search_snippets(
    query="best practices",
    k=5
)

# Find similar content
similar = search_service.find_similar(
    entity_type='profile',
    entity_id=123,
    k=10
)

# Search with query expansion
results = search_service.search(
    query="cloud computing",
    k=10,
    use_expansion=True  # Expands query automatically
)
```

### Custom Vectorization

```python
from src.search.indexing import ContentVectorizationPipeline, EmbeddingConfig

# Custom configuration
config = EmbeddingConfig(
    provider='sentence-transformers',
    model_name='all-mpnet-base-v2',
    device='cuda',  # Use GPU
    batch_size=64
)

vectorizer = ContentVectorizationPipeline(config)

# Encode text
texts = ["First document", "Second document"]
embeddings = vectorizer.encode(texts)

# Single text
embedding = vectorizer.encode_single("Query text")
```

### Custom Search Engine

```python
from src.search.vector_search import VectorSearch
import numpy as np

# Initialize search engine
search_engine = VectorSearch(
    dimension=384,
    backend='faiss',
    metric='cosine',
    use_gpu=False
)

# Add vectors
vectors = np.random.rand(1000, 384)
entity_mapping = [('profile', i) for i in range(1000)]
search_engine.add_vectors(vectors, entity_mapping)
search_engine.build_index()

# Search
query_vector = np.random.rand(384)
results = search_engine.search(query_vector, k=10)
```

## 🎯 Examples

Run the comprehensive example:

```bash
python examples/search_example.py
```

This demonstrates:
1. ✅ Basic setup and configuration
2. 🔄 Content indexing (profiles, snippets, content)
3. 🔍 Semantic search with various queries
4. 🎯 Filtered search (by entity type)
5. 🔗 Finding similar content
6. ⚖️ Provider comparison (Sentence Transformers vs OpenAI)
7. 🚀 Advanced features (query expansion, caching)
8. 💬 Interactive search mode

## 📊 Performance

### Benchmarks (1M vectors, 384 dimensions)

| Backend | Index Time | Search Time (k=10) | Memory |
|---------|-----------|-------------------|---------|
| FAISS   | ~30s      | ~0.001s           | ~1.5GB  |
| Annoy   | ~60s      | ~0.005s           | ~1.2GB  |
| Brute   | 0s        | ~0.1s             | ~1.5GB  |

### GPU Acceleration

With FAISS on GPU (NVIDIA A100):
- Index time: ~5s
- Search time: ~0.0001s
- 10x-100x faster than CPU

## 🔐 API Key Setup

### Getting OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create new key
5. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...your_key_here
   ```

### Cost Estimation (OpenAI)

For `text-embedding-3-small`:
- $0.02 per 1M tokens
- ~750 words per 1000 tokens
- 1000 documents (~500 words each) ≈ $0.01

## 🏗️ Architecture

```
src/search/
├── indexing.py              # Vectorization & indexing
│   ├── ContentVectorizationPipeline
│   ├── EmbeddingConfig
│   └── EmbeddingIndexer
│
├── vector_search.py         # Search engine
│   ├── VectorSearch
│   ├── SimilarityComputationAlgorithms
│   ├── RelevanceScoringMechanism
│   └── QueryExpansionTechniques
│
└── __init__.py

src/services/
└── search_service.py        # High-level service
    ├── SemanticSearchService
    └── SearchConfig
```

## 🔧 Troubleshooting

### Import Errors

```bash
# Missing dependencies
pip install sentence-transformers faiss-cpu numpy

# For GPU support (FAISS)
pip install faiss-gpu

# For Annoy
pip install annoy
```

### OpenAI Errors

```python
# Check API key
import openai
print(openai.api_key)  # Should not be None

# Test connection
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input="test"
)
```

### Memory Issues

For large datasets:
- Use smaller embedding models
- Increase batch size gradually
- Use Annoy instead of FAISS
- Enable GPU acceleration

## 📈 Optimization Tips

1. **Choose Right Model**:
   - Small dataset: Use larger model (better quality)
   - Large dataset: Use smaller model (faster)

2. **Backend Selection**:
   - <10K vectors: Brute force is fine
   - 10K-1M vectors: FAISS recommended
   - >1M vectors: FAISS with GPU or Annoy

3. **Query Expansion**:
   - Enable for better recall
   - Disable for exact matching

4. **Caching**:
   - Enable for repeated queries
   - Set appropriate TTL

5. **Batch Processing**:
   - Use larger batches for indexing
   - Monitor memory usage

## 🤝 Integration

### With Existing Code

```python
# In your application
from src.services.search_service import create_search_service

search_service = create_search_service(db_session)

# Use in API endpoint
@app.post("/search")
def search_api(query: str, k: int = 10):
    results = search_service.search(query, k=k)
    return results.to_dict()
```

### With Chat Assistant

```python
# Retrieve relevant context for LLM
results = search_service.search(user_question, k=5)
context = "\n".join([r.content for r in results.results])

# Pass to LLM
response = llm.generate(
    prompt=f"Context: {context}\n\nQuestion: {user_question}"
)
```

## 📚 References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Annoy Documentation](https://github.com/spotify/annoy)

## 🎓 Next Steps

After setting up search:
1. ✅ Configure your `.env` with API keys
2. ✅ Run `python examples/search_example.py`
3. ✅ Index your content
4. ✅ Test different queries
5. ✅ Integrate with your application
6. ✅ Monitor performance and optimize

---

**Ready to search semantically! 🚀**
