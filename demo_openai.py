"""
Rebuild search index with OpenAI embeddings and compare results.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.database.migrations import DatabaseSession
from src.services.search_service import create_search_service
import os

def main():
    print("\n" + "="*60)
    print("🚀 OpenAI Embeddings - Upgrade Demo")
    print("="*60)
    
    # Check configuration
    provider = os.getenv('EMBEDDING_PROVIDER', 'unknown')
    model = os.getenv('EMBEDDING_MODEL', 'unknown')
    
    print(f"\n📋 Current Configuration:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   Dimension: 1536 (OpenAI)" if provider == 'openai' else "   Dimension: 384 (Sentence Transformers)")
    
    # Initialize search service
    print(f"\n🔧 Initializing search service...")
    db_session = DatabaseSession('sqlite:///data/profiles.db')
    search_service = create_search_service(db_session)
    
    # Rebuild index with OpenAI embeddings
    print(f"\n📊 Rebuilding index with {provider}...")
    print("   (This will use your OpenAI API key - costs ~$0.0001)")
    
    stats = search_service.rebuild_index()
    
    print(f"\n✅ Index rebuilt successfully!")
    print(f"   Profiles indexed: {stats['profiles']['indexed']}")
    print(f"   Snippets indexed: {stats['snippets']['indexed']}")
    print(f"   Content indexed: {stats['content']['indexed']}")
    print(f"   Total: {stats['total_indexed']}")
    
    # Demo searches with OpenAI embeddings
    print("\n" + "="*60)
    print("🔍 Testing Search Quality with OpenAI")
    print("="*60)
    
    test_queries = [
        "expert in machine learning and neural networks",
        "full stack web developer with cloud experience",
        "AI researcher specializing in natural language",
        "introduction to deep learning concepts"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 60)
        
        results = search_service.search(
            query=query,
            k=3,
            min_score=0.0
        )
        
        print(f"Found {len(results.results)} results in {results.search_time:.4f}s\n")
        
        for i, result in enumerate(results.results, 1):
            print(f"{i}. [{result.entity_type.upper()}] Score: {result.score:.3f}")
            if result.content:
                if result.entity_type == 'profile':
                    print(f"   👤 {result.content.get('name')}")
                    print(f"   💼 {result.content.get('title')}")
                elif result.entity_type == 'snippet':
                    print(f"   📄 {result.content.get('title')}")
                    print(f"   📂 {result.content.get('category')}")
            print()
    
    # Show statistics
    print("=" * 60)
    print("📊 Search Service Statistics")
    print("=" * 60)
    
    stats = search_service.get_statistics()
    print(f"\n🔧 Configuration:")
    print(f"   Provider: {stats['config']['provider']}")
    print(f"   Model: {stats['config']['model']}")
    print(f"   Dimension: {stats['config']['dimension']}")
    print(f"   Backend: {stats['config']['backend']}")
    
    print(f"\n📈 Index Stats:")
    print(f"   Total vectors: {stats['search_engine']['total_vectors']}")
    print(f"   Profiles: {stats['indexing']['by_entity_type'].get('profile', 0)}")
    print(f"   Snippets: {stats['indexing']['by_entity_type'].get('snippet', 0)}")
    print(f"   Content: {stats['indexing']['by_entity_type'].get('content', 0)}")
    
    print("\n" + "="*60)
    print("✅ OpenAI Embeddings Demo Complete!")
    print("="*60)
    
    print("\n💡 Benefits of OpenAI vs Sentence Transformers:")
    print("   ✅ 4x higher dimension (1536 vs 384)")
    print("   ✅ Better semantic understanding")
    print("   ✅ More accurate similarity scores")
    print("   ✅ Optimized for search and retrieval")
    print("   ✅ No model download required")
    
    print("\n💰 Approximate cost for this demo: $0.0001")
    print("   (5 profiles × 100 tokens × $0.00002/token)")
    
    print("\n🎯 Your search system is now powered by OpenAI!")

if __name__ == "__main__":
    main()
