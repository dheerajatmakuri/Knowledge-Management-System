"""
Quick test script for vector search system.
Tests basic functionality without requiring data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from src.search.indexing import ContentVectorizationPipeline, EmbeddingConfig
from src.search.vector_search import (
    VectorSearch,
    SimilarityComputationAlgorithms,
    RelevanceScoringMechanism,
    QueryExpansionTechniques
)


def test_vectorization():
    """Test vectorization pipeline."""
    print("\n" + "="*60)
    print("Test 1: Vectorization Pipeline")
    print("="*60)
    
    try:
        # Initialize with sentence transformers
        config = EmbeddingConfig(
            provider='sentence-transformers',
            model_name='all-MiniLM-L6-v2'
        )
        
        vectorizer = ContentVectorizationPipeline(config)
        print(f"✅ Vectorizer initialized")
        print(f"   Provider: {config.provider}")
        print(f"   Model: {config.model_name}")
        print(f"   Dimension: {config.dimension}")
        
        # Test encoding
        texts = [
            "Machine learning is a subset of artificial intelligence",
            "Python is a popular programming language",
            "Data science involves statistical analysis"
        ]
        
        embeddings = vectorizer.encode(texts)
        print(f"\n✅ Encoded {len(texts)} texts")
        print(f"   Shape: {embeddings.shape}")
        print(f"   First embedding norm: {np.linalg.norm(embeddings[0]):.3f}")
        
        # Test single encoding
        single = vectorizer.encode_single("Test query")
        print(f"\n✅ Single encoding works")
        print(f"   Shape: {single.shape}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_similarity_algorithms():
    """Test similarity computation."""
    print("\n" + "="*60)
    print("Test 2: Similarity Algorithms")
    print("="*60)
    
    try:
        # Create test vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.9, 0.1, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])
        
        # Test cosine similarity
        sim1 = SimilarityComputationAlgorithms.cosine_similarity(vec1, vec2)
        sim2 = SimilarityComputationAlgorithms.cosine_similarity(vec1, vec3)
        
        print(f"✅ Cosine Similarity:")
        print(f"   Similar vectors: {sim1:.3f}")
        print(f"   Orthogonal vectors: {sim2:.3f}")
        
        # Test batch similarity
        vectors = np.array([vec1, vec2, vec3])
        query = vec1
        batch_sims = SimilarityComputationAlgorithms.cosine_similarity_batch(query, vectors)
        
        print(f"\n✅ Batch Similarity:")
        print(f"   Scores: {batch_sims}")
        
        # Test other metrics
        euclidean = SimilarityComputationAlgorithms.euclidean_distance(vec1, vec2)
        manhattan = SimilarityComputationAlgorithms.manhattan_distance(vec1, vec2)
        
        print(f"\n✅ Other Metrics:")
        print(f"   Euclidean distance: {euclidean:.3f}")
        print(f"   Manhattan distance: {manhattan:.3f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_relevance_scoring():
    """Test relevance scoring mechanism."""
    print("\n" + "="*60)
    print("Test 3: Relevance Scoring")
    print("="*60)
    
    try:
        scorer = RelevanceScoringMechanism()
        
        # Test with different entity data
        from datetime import datetime, timedelta
        
        test_cases = [
            {
                'name': 'Recent + High Quality',
                'data': {
                    'created_at': datetime.utcnow().isoformat(),
                    'is_verified': True,
                    'confidence_score': 0.9,
                    'view_count': 100
                },
                'semantic_score': 0.8
            },
            {
                'name': 'Old + Low Quality',
                'data': {
                    'created_at': (datetime.utcnow() - timedelta(days=400)).isoformat(),
                    'is_verified': False,
                    'confidence_score': 0.3,
                    'view_count': 5
                },
                'semantic_score': 0.8
            }
        ]
        
        print(f"✅ Relevance Scoring:")
        for case in test_cases:
            score = scorer.compute_score(case['semantic_score'], case['data'])
            print(f"   {case['name']}: {score:.3f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_query_expansion():
    """Test query expansion techniques."""
    print("\n" + "="*60)
    print("Test 4: Query Expansion")
    print("="*60)
    
    try:
        expander = QueryExpansionTechniques()
        
        # Test stemming
        query = "running quickly"
        expanded = expander.expand_with_stemming(query)
        print(f"✅ Stemming Expansion:")
        print(f"   Original: {query}")
        print(f"   Expanded: {expanded}")
        
        # Test synonym expansion
        synonyms = {
            'fast': ['quick', 'rapid', 'swift'],
            'machine': ['computer', 'device']
        }
        query2 = "fast machine"
        expanded2 = expander.expand_with_synonyms(query2, synonyms)
        print(f"\n✅ Synonym Expansion:")
        print(f"   Original: {query2}")
        print(f"   Expanded: {expanded2}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_vector_search():
    """Test vector search engine."""
    print("\n" + "="*60)
    print("Test 5: Vector Search Engine")
    print("="*60)
    
    try:
        # Create search engine
        dimension = 384
        search_engine = VectorSearch(
            dimension=dimension,
            backend='brute',  # Use brute force for testing
            metric='cosine'
        )
        
        print(f"✅ Search engine initialized")
        print(f"   Backend: {search_engine.backend}")
        print(f"   Metric: {search_engine.metric}")
        print(f"   Dimension: {search_engine.dimension}")
        
        # Add test vectors
        n_vectors = 100
        vectors = np.random.rand(n_vectors, dimension)
        entity_mapping = [(f'type_{i%3}', i) for i in range(n_vectors)]
        
        search_engine.add_vectors(vectors, entity_mapping)
        search_engine.build_index()
        
        print(f"\n✅ Added {n_vectors} vectors")
        
        # Perform search
        query_vector = np.random.rand(dimension)
        results = search_engine.search(query_vector, k=5)
        
        print(f"\n✅ Search completed:")
        print(f"   Results: {len(results.results)}")
        print(f"   Search time: {results.search_time:.4f}s")
        print(f"   Top score: {results.results[0].score:.3f}")
        
        # Test with filters
        filtered_results = search_engine.search(
            query_vector,
            k=5,
            filters={'entity_type': ['type_0']}
        )
        
        print(f"\n✅ Filtered search:")
        print(f"   Results: {len(filtered_results.results)}")
        print(f"   All type_0: {all(r.entity_type == 'type_0' for r in filtered_results.results)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration."""
    print("\n" + "="*60)
    print("Test 6: Integration Test")
    print("="*60)
    
    try:
        # Initialize vectorizer
        config = EmbeddingConfig(
            provider='sentence-transformers',
            model_name='all-MiniLM-L6-v2'
        )
        vectorizer = ContentVectorizationPipeline(config)
        
        # Initialize search engine
        search_engine = VectorSearch(
            dimension=vectorizer.config.dimension,
            backend='brute',
            metric='cosine'
        )
        
        # Create test documents
        documents = [
            "Python is a high-level programming language",
            "Machine learning enables computers to learn from data",
            "Neural networks are inspired by biological neurons",
            "Data science combines statistics and programming",
            "Artificial intelligence mimics human intelligence"
        ]
        
        # Vectorize documents
        vectors = vectorizer.encode(documents)
        entity_mapping = [('doc', i) for i in range(len(documents))]
        
        # Add to search engine
        search_engine.add_vectors(vectors, entity_mapping)
        search_engine.build_index()
        
        print(f"✅ Indexed {len(documents)} documents")
        
        # Search with text query
        query = "artificial intelligence and machine learning"
        query_vector = vectorizer.encode_single(query)
        results = search_engine.search(query_vector, k=3)
        
        print(f"\n✅ Search query: '{query}'")
        print(f"   Top results:")
        for i, result in enumerate(results.results, 1):
            doc_id = result.entity_id
            print(f"   {i}. Score {result.score:.3f}: {documents[doc_id][:60]}...")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 Vector Search System - Quick Tests")
    print("="*60)
    
    tests = [
        ("Vectorization", test_vectorization),
        ("Similarity Algorithms", test_similarity_algorithms),
        ("Relevance Scoring", test_relevance_scoring),
        ("Query Expansion", test_query_expansion),
        ("Vector Search", test_vector_search),
        ("Integration", test_integration)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check dependencies and configuration.")


if __name__ == "__main__":
    main()
