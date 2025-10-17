"""
Production search service using OpenAI embeddings.
This is the real implementation for your application.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from src.database.migrations import DatabaseSession
from src.services.search_service import create_search_service
from src.database.repository import ProfileRepository, KnowledgeSnippetRepository, ContentRepository

class ProductionSearchService:
    """Production-ready search service with OpenAI embeddings."""
    
    def __init__(self):
        """Initialize the production search service."""
        # Verify OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            raise ValueError("Please set your OPENAI_API_KEY in .env file")
        
        # Initialize database and search
        self.db_session = DatabaseSession('sqlite:///data/profiles.db')
        self.search_service = create_search_service(self.db_session)
        
        print("✅ Production search service initialized with OpenAI")
        print(f"   Model: {os.getenv('EMBEDDING_MODEL')}")
        print(f"   Dimension: 1536")
    
    def index_all_content(self):
        """Index all content in the database."""
        print("\n📊 Indexing all content with OpenAI embeddings...")
        stats = self.search_service.rebuild_index()
        
        print(f"\n✅ Indexing complete!")
        print(f"   Profiles: {stats['profiles']['indexed']}/{stats['profiles']['total_profiles']}")
        print(f"   Snippets: {stats['snippets']['indexed']}/{stats['snippets']['total_snippets']}")
        print(f"   Content: {stats['content']['indexed']}/{stats['content']['total_content']}")
        print(f"   Total: {stats['total_indexed']} items indexed")
        
        return stats
    
    def search(self, query, k=10, entity_types=None, min_score=0.3):
        """
        Search across all content.
        
        Args:
            query: Search query
            k: Number of results
            entity_types: Filter by types (e.g., ['profile', 'snippet'])
            min_score: Minimum similarity score
        
        Returns:
            SearchResults object
        """
        results = self.search_service.search(
            query=query,
            k=k,
            entity_types=entity_types,
            min_score=min_score,
            use_expansion=True
        )
        return results
    
    def search_profiles(self, query, k=10):
        """Search for profiles."""
        return self.search_service.search_profiles(query, k=k)
    
    def search_knowledge(self, query, k=10):
        """Search for knowledge snippets."""
        return self.search_service.search_snippets(query, k=k)
    
    def find_similar(self, entity_type, entity_id, k=5):
        """Find similar items."""
        return self.search_service.find_similar(entity_type, entity_id, k=k)
    
    def get_statistics(self):
        """Get search statistics."""
        return self.search_service.get_statistics()
    
    def add_profile(self, name, title, bio, email=None, source_url=None, **kwargs):
        """Add a new profile and index it."""
        with self.db_session.get_session() as session:
            profile_repo = ProfileRepository(session)
            
            if not source_url:
                source_url = f"https://internal.system/profiles/{name.lower().replace(' ', '-')}"
            
            profile = profile_repo.create(
                name=name,
                title=title,
                bio=bio,
                email=email,
                source_url=source_url,
                source_domain='internal.system',
                **kwargs
            )
            session.commit()
            
            # Index the new profile
            from src.search.indexing import EmbeddingIndexer
            indexer = EmbeddingIndexer(self.search_service.vectorizer, self.db_session)
            indexer.index_profiles([profile.id])
            
            # Reload index
            self.search_service._load_index()
            
            print(f"✅ Added and indexed: {name}")
            return profile
    
    def add_knowledge_snippet(self, title, content, category, content_type='article', url=None, **kwargs):
        """Add a new knowledge snippet and index it."""
        with self.db_session.get_session() as session:
            snippet_repo = KnowledgeSnippetRepository(session)
            
            if not url:
                url = f"https://internal.system/knowledge/{title.lower().replace(' ', '-')}"
            
            snippet = snippet_repo.create_snippet(
                url=url,
                title=title,
                content=content,
                category=category,
                content_type=content_type,
                source_url=url,
                source_domain='internal.system',
                **kwargs
            )
            session.commit()
            
            # Index the new snippet
            from src.search.indexing import EmbeddingIndexer
            indexer = EmbeddingIndexer(self.search_service.vectorizer, self.db_session)
            indexer.index_snippets([snippet.id])
            
            # Reload index
            self.search_service._load_index()
            
            print(f"✅ Added and indexed: {title}")
            return snippet


def main():
    """Example usage of the production search service."""
    print("\n" + "="*60)
    print("🚀 Production Search Service - OpenAI Powered")
    print("="*60)
    
    try:
        # Initialize
        search = ProductionSearchService()
        
        # Index existing content
        print("\n📊 Indexing existing content...")
        stats = search.index_all_content()
        
        # Example: Search for profiles
        print("\n" + "="*60)
        print("🔍 Example Searches")
        print("="*60)
        
        queries = [
            "machine learning engineer with Python experience",
            "full stack developer specializing in React",
            "data scientist with statistical modeling skills"
        ]
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            results = search.search(query, k=3)
            
            if results.results:
                for i, result in enumerate(results.results, 1):
                    score_pct = result.score * 100
                    print(f"   {i}. [{result.entity_type}] {score_pct:.1f}% match")
                    if result.content:
                        if result.entity_type == 'profile':
                            print(f"      👤 {result.content.get('name')} - {result.content.get('title')}")
                        elif result.entity_type == 'snippet':
                            print(f"      📄 {result.content.get('title')}")
            else:
                print("   No results found")
        
        # Show statistics
        print("\n" + "="*60)
        print("📊 System Statistics")
        print("="*60)
        stats = search.get_statistics()
        print(f"\n✅ Search system ready!")
        print(f"   Total indexed: {stats['search_engine']['total_vectors']}")
        print(f"   Provider: {stats['config']['provider']}")
        print(f"   Model: {stats['config']['model']}")
        print(f"   Dimension: {stats['config']['dimension']}")
        
        print("\n" + "="*60)
        print("✅ Production Search Service Ready!")
        print("="*60)
        print("\n💡 Your application can now:")
        print("   ✅ Search across all content with OpenAI")
        print("   ✅ Find similar profiles/snippets")
        print("   ✅ Add new content and auto-index")
        print("   ✅ Get high-quality semantic matches")
        
        return search
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    search_service = main()
    
    if search_service:
        print("\n" + "="*60)
        print("🎯 Ready to use in your application!")
        print("="*60)
        print("\nImport in your code:")
        print("   from app_search import ProductionSearchService")
        print("   search = ProductionSearchService()")
        print("   results = search.search('your query')")
