"""
Example usage of the vector embedding and semantic search system.

This script demonstrates:
1. Setting up the vectorization pipeline
2. Indexing content (profiles, snippets, articles)
3. Performing semantic searches
4. Using different search features
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.database.migrations import DatabaseSession
from src.services.search_service import SemanticSearchService, SearchConfig, create_search_service
from src.search.indexing import ContentVectorizationPipeline, EmbeddingConfig
from loguru import logger

# Load environment variables
load_dotenv()


def setup_logging():
    """Configure logging."""
    logger.add(
        "logs/search_example.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )


def example_1_basic_setup():
    """Example 1: Basic setup and indexing."""
    print("\n" + "="*60)
    print("Example 1: Basic Setup and Indexing")
    print("="*60)
    
    # Initialize database
    db_path = os.getenv('DATABASE_PATH', 'data/profiles.db')
    db_session = DatabaseSession(db_path)
    
    # Create search service (using environment config)
    search_service = create_search_service(db_session)
    
    # Get statistics
    stats = search_service.get_statistics()
    print(f"\n📊 Search Service Statistics:")
    print(f"  Provider: {stats['config']['provider']}")
    print(f"  Model: {stats['config']['model']}")
    print(f"  Backend: {stats['config']['backend']}")
    print(f"  Dimension: {stats['config']['dimension']}")
    print(f"  Total Vectors: {stats['search_engine']['total_vectors']}")
    
    return search_service, db_session


def example_2_index_content(search_service):
    """Example 2: Index content for semantic search."""
    print("\n" + "="*60)
    print("Example 2: Indexing Content")
    print("="*60)
    
    # Index all content
    print("\n🔄 Indexing all content...")
    stats = search_service.rebuild_index()
    
    print(f"\n✅ Indexing Complete!")
    print(f"  Profiles: {stats['profiles']['indexed']} / {stats['profiles']['total_profiles']}")
    print(f"  Snippets: {stats['snippets']['indexed']} / {stats['snippets']['total_snippets']}")
    print(f"  Content: {stats['content']['indexed']} / {stats['content']['total_content']}")
    print(f"  Total: {stats['total_indexed']}")


def example_3_semantic_search(search_service):
    """Example 3: Perform semantic searches."""
    print("\n" + "="*60)
    print("Example 3: Semantic Search")
    print("="*60)
    
    # Example queries
    queries = [
        "machine learning and artificial intelligence",
        "software engineering best practices",
        "leadership and management skills",
        "data science and analytics"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        
        results = search_service.search(
            query=query,
            k=5,
            min_score=0.3,
            use_expansion=True
        )
        
        print(f"   Found {len(results.results)} results in {results.search_time:.3f}s")
        
        for i, result in enumerate(results.results[:3], 1):
            print(f"\n   {i}. [{result.entity_type.upper()}] Score: {result.score:.3f}")
            if result.content:
                if result.entity_type == 'profile':
                    print(f"      Name: {result.content.get('name')}")
                    print(f"      Title: {result.content.get('title')}")
                elif result.entity_type == 'snippet':
                    print(f"      Title: {result.content.get('title')}")
                    print(f"      Type: {result.content.get('content_type')}")
                elif result.entity_type == 'content':
                    print(f"      Title: {result.content.get('title')}")


def example_4_filtered_search(search_service):
    """Example 4: Search with filters."""
    print("\n" + "="*60)
    print("Example 4: Filtered Search")
    print("="*60)
    
    query = "software development"
    
    # Search only profiles
    print(f"\n🔍 Query: '{query}' (Profiles only)")
    profile_results = search_service.search_profiles(query, k=3)
    print(f"   Found {len(profile_results.results)} profiles")
    
    for result in profile_results.results:
        if result.content:
            print(f"   - {result.content.get('name')}: {result.score:.3f}")
    
    # Search only snippets
    print(f"\n🔍 Query: '{query}' (Snippets only)")
    snippet_results = search_service.search_snippets(query, k=3)
    print(f"   Found {len(snippet_results.results)} snippets")
    
    for result in snippet_results.results:
        if result.content:
            print(f"   - {result.content.get('title')}: {result.score:.3f}")


def example_5_find_similar(search_service):
    """Example 5: Find similar content."""
    print("\n" + "="*60)
    print("Example 5: Find Similar Content")
    print("="*60)
    
    # First, search for a profile
    results = search_service.search_profiles("data scientist", k=1)
    
    if results.results:
        target = results.results[0]
        print(f"\n📌 Target: {target.content.get('name')} ({target.entity_type})")
        
        # Find similar profiles
        print("\n🔍 Finding similar profiles...")
        similar = search_service.find_similar(
            entity_type=target.entity_type,
            entity_id=target.entity_id,
            k=5
        )
        
        print(f"   Found {len(similar.results)} similar items:")
        for i, result in enumerate(similar.results, 1):
            if result.content:
                name = result.content.get('name') or result.content.get('title')
                print(f"   {i}. {name}: {result.score:.3f}")


def example_6_provider_comparison():
    """Example 6: Compare different embedding providers."""
    print("\n" + "="*60)
    print("Example 6: Embedding Provider Comparison")
    print("="*60)
    
    db_path = os.getenv('DATABASE_PATH', 'data/profiles.db')
    db_session = DatabaseSession(db_path)
    
    providers = [
        ('sentence-transformers', 'all-MiniLM-L6-v2'),
    ]
    
    # Add OpenAI if API key is available
    if os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_API_KEY') != 'your_openai_api_key_here':
        providers.append(('openai', 'text-embedding-3-small'))
    
    test_query = "artificial intelligence and machine learning"
    
    for provider, model in providers:
        print(f"\n🔧 Provider: {provider} | Model: {model}")
        
        config = SearchConfig(
            embedding_provider=provider,
            embedding_model=model,
            search_backend='brute',  # Use brute force for small test
            use_cache=False
        )
        
        try:
            search_service = SemanticSearchService(db_session, config)
            
            # Quick search test
            import time
            start = time.time()
            results = search_service.search(test_query, k=3, include_content=False)
            elapsed = time.time() - start
            
            print(f"   ⏱️  Search time: {elapsed:.3f}s")
            print(f"   📊 Results: {len(results.results)}")
            
            if results.results:
                print(f"   🏆 Top score: {results.results[0].score:.3f}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")


def example_7_advanced_features(search_service):
    """Example 7: Advanced search features."""
    print("\n" + "="*60)
    print("Example 7: Advanced Features")
    print("="*60)
    
    query = "cloud computing"
    
    # Without query expansion
    print(f"\n🔍 Query: '{query}' (No expansion)")
    results_no_exp = search_service.search(query, k=3, use_expansion=False)
    print(f"   Results: {len(results_no_exp.results)}")
    
    # With query expansion
    print(f"\n🔍 Query: '{query}' (With expansion)")
    results_with_exp = search_service.search(query, k=3, use_expansion=True)
    print(f"   Results: {len(results_with_exp.results)}")
    
    # Show difference
    print(f"\n📈 Improvement: {len(results_with_exp.results) - len(results_no_exp.results)} more results")


def interactive_search(search_service):
    """Interactive search mode."""
    print("\n" + "="*60)
    print("Interactive Search Mode")
    print("="*60)
    print("\nEnter your search queries (or 'quit' to exit)")
    
    while True:
        try:
            query = input("\n🔍 Search: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            results = search_service.search(
                query=query,
                k=5,
                min_score=0.3
            )
            
            print(f"\n✅ Found {len(results.results)} results in {results.search_time:.3f}s\n")
            
            for i, result in enumerate(results.results, 1):
                print(f"{i}. [{result.entity_type.upper()}] Score: {result.score:.3f}")
                if result.content:
                    if result.entity_type == 'profile':
                        print(f"   {result.content.get('name')} - {result.content.get('title')}")
                    elif result.entity_type == 'snippet':
                        print(f"   {result.content.get('title')}")
                        print(f"   {result.content.get('content', '')[:100]}...")
                    elif result.entity_type == 'content':
                        print(f"   {result.content.get('title')}")
                print()
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main example runner."""
    setup_logging()
    
    print("\n" + "="*60)
    print("🚀 Vector Embedding & Semantic Search Examples")
    print("="*60)
    
    try:
        # Example 1: Setup
        search_service, db_session = example_1_basic_setup()
        
        # Check if we have data
        stats = search_service.get_statistics()
        if stats['search_engine']['total_vectors'] == 0:
            print("\n⚠️  No indexed data found. Running indexing...")
            example_2_index_content(search_service)
        
        # Example 3: Semantic search
        example_3_semantic_search(search_service)
        
        # Example 4: Filtered search
        example_4_filtered_search(search_service)
        
        # Example 5: Find similar
        example_5_find_similar(search_service)
        
        # Example 6: Provider comparison
        example_6_provider_comparison()
        
        # Example 7: Advanced features
        example_7_advanced_features(search_service)
        
        # Interactive mode
        response = input("\n💬 Enter interactive search mode? (y/n): ")
        if response.lower() == 'y':
            interactive_search(search_service)
        
        print("\n✅ Examples completed successfully!")
    
    except Exception as e:
        logger.exception(f"Error running examples: {e}")
        print(f"\n❌ Error: {e}")
    
    finally:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
