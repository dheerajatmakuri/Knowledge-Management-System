"""
Production Hybrid Search Service.
Complete integration for application use.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

from src.database.repository import DatabaseSession
from src.search.indexing import ContentVectorizationPipeline, EmbeddingIndexer
from src.search.vector_search import VectorSearch
from src.search.hybrid_search import HybridSearchEngine, HybridSearchConfig

# Load environment
load_dotenv()


class ProductionHybridSearchService:
    """
    Production-ready hybrid search service combining:
    - Full-text search
    - Vector similarity
    - Metadata filtering
    - Result fusion and ranking
    """
    
    def __init__(self,
                 db_path: str = None,
                 vector_weight: float = 0.5,
                 fulltext_weight: float = 0.3,
                 metadata_weight: float = 0.2,
                 fusion_method: str = 'weighted_sum'):
        """
        Initialize production hybrid search service.
        
        Args:
            db_path: Path to database file
            vector_weight: Weight for vector similarity (0-1)
            fulltext_weight: Weight for full-text search (0-1)
            metadata_weight: Weight for metadata matching (0-1)
            fusion_method: Method for fusing results ('weighted_sum', 'reciprocal_rank', 'max')
        """
        # Validate API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("your-openai-api-key"):
            raise ValueError("Valid OpenAI API key required in .env file")
        
        # Database setup
        if db_path is None:
            db_path = "data/profiles.db"
        
        # Create database URL
        if not str(db_path).startswith('sqlite:///'):
            db_path = f'sqlite:///{db_path}'
        
        self.db_session = DatabaseSession(db_path)
        logger.info(f"Database initialized: {db_path}")
        
        # Initialize search components
        self.vectorizer = ContentVectorizationPipeline()
        self.vector_search = VectorSearch(
            dimension=self.vectorizer.config.dimension,
            backend=os.getenv('SEARCH_BACKEND', 'faiss'),
            metric=os.getenv('SEARCH_METRIC', 'cosine'),
            use_gpu=False
        )
        
        # Configure hybrid search
        self.config = HybridSearchConfig(
            vector_weight=vector_weight,
            fulltext_weight=fulltext_weight,
            metadata_weight=metadata_weight,
            fusion_method=fusion_method,
            use_vector=True,
            use_fulltext=True,
            use_metadata=True
        )
        
        self.hybrid_search = HybridSearchEngine(
            db_session=self.db_session,
            vector_search=self.vector_search,
            vectorizer=self.vectorizer,
            config=self.config
        )
        
        # Load vectors from database into the search index
        self._load_vectors_from_db()
        
        logger.success("Production hybrid search service initialized")
    
    def _load_vectors_from_db(self):
        """Load existing vectors from database into search index."""
        from src.database.repository import EmbeddingVectorRepository
        
        try:
            with self.db_session.get_session() as session:
                embed_repo = EmbeddingVectorRepository(session)
                
                # Get all vectors from database
                all_vectors = embed_repo.get_all()
                
                if not all_vectors:
                    logger.warning("No vectors found in database")
                    return
                
                # Prepare vectors and entity mapping
                vectors = []
                entity_mapping = []
                
                for vec in all_vectors:
                    if vec.vector and vec.vector_dimension == self.vectorizer.config.dimension:
                        vectors.append(vec.vector)
                        entity_mapping.append((vec.entity_type, vec.entity_id))
                
                if vectors:
                    import numpy as np
                    vectors_array = np.array(vectors)
                    self.vector_search.add_vectors(vectors_array, entity_mapping)
                    logger.success(f"Loaded {len(vectors)} vectors from database")
                else:
                    logger.warning("No vector data found")
        
        except Exception as e:
            logger.error(f"Error loading vectors: {e}")
    
    def search(self,
               query: str,
               k: int = 10,
               entity_types: Optional[List[str]] = None,
               filters: Optional[Dict[str, Any]] = None,
               min_score: float = 0.0,
               include_scores: bool = False,
               include_facets: bool = False) -> Dict[str, Any]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            k: Number of results to return
            entity_types: Filter by entity types ('profile', 'snippet', 'content')
            filters: Metadata filters (e.g., {'is_verified': True, 'min_confidence': 0.8})
            min_score: Minimum score threshold
            include_scores: Include detailed score breakdown
            include_facets: Include facet counts
        
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Determine facet fields
            facet_fields = None
            if include_facets:
                facet_fields = ['category', 'content_type', 'source_domain', 'is_verified']
            
            # Perform search
            results = self.hybrid_search.search(
                query=query,
                k=k,
                entity_types=entity_types,
                filters=filters,
                include_scores=include_scores,
                include_facets=include_facets,
                facet_fields=facet_fields
            )
            
            # Filter by min score
            filtered_results = [
                r for r in results.results
                if r.score >= min_score
            ]
            
            # Format response
            return {
                'success': True,
                'query': query,
                'total_results': len(filtered_results),
                'search_time': results.search_time,
                'algorithm': 'hybrid',
                'results': [
                    {
                        'rank': r.rank,
                        'entity_type': r.entity_type,
                        'entity_id': r.entity_id,
                        'score': r.score,
                        'content': r.content,
                        'metadata': r.metadata if include_scores else {}
                    }
                    for r in filtered_results
                ],
                'facets': results.filters_applied.get('facets', {}) if include_facets else {},
                'config': {
                    'vector_weight': self.config.vector_weight,
                    'fulltext_weight': self.config.fulltext_weight,
                    'metadata_weight': self.config.metadata_weight,
                    'fusion_method': self.config.fusion_method
                }
            }
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def search_profiles(self,
                       query: str,
                       k: int = 10,
                       verified_only: bool = False,
                       min_confidence: float = 0.0,
                       source_domain: str = None) -> Dict[str, Any]:
        """
        Search for profiles with specific filters.
        
        Args:
            query: Search query
            k: Number of results
            verified_only: Return only verified profiles
            min_confidence: Minimum confidence score
            source_domain: Filter by source domain
        
        Returns:
            Search results
        """
        filters = {}
        
        if verified_only:
            filters['is_verified'] = True
        
        if min_confidence > 0:
            filters['min_confidence'] = min_confidence
        
        if source_domain:
            filters['source_domain'] = source_domain
        
        return self.search(
            query=query,
            k=k,
            entity_types=['profile'],
            filters=filters,
            include_scores=True
        )
    
    def search_knowledge(self,
                        query: str,
                        k: int = 10,
                        category: str = None,
                        content_type: str = None,
                        validated_only: bool = False) -> Dict[str, Any]:
        """
        Search for knowledge snippets with filters.
        
        Args:
            query: Search query
            k: Number of results
            category: Filter by category
            content_type: Filter by content type
            validated_only: Return only validated content
        
        Returns:
            Search results
        """
        filters = {}
        
        if category:
            filters['category'] = category
        
        if content_type:
            filters['content_type'] = content_type
        
        if validated_only:
            filters['is_validated'] = True
        
        return self.search(
            query=query,
            k=k,
            entity_types=['snippet'],
            filters=filters,
            include_scores=True
        )
    
    def advanced_search(self,
                       query: str,
                       k: int = 10,
                       entity_types: List[str] = None,
                       filters: Dict[str, Any] = None,
                       weights: Dict[str, float] = None,
                       fusion_method: str = None) -> Dict[str, Any]:
        """
        Advanced search with custom configuration.
        
        Args:
            query: Search query
            k: Number of results
            entity_types: Entity types to search
            filters: Metadata filters
            weights: Custom weights {'vector': 0.5, 'fulltext': 0.3, 'metadata': 0.2}
            fusion_method: Custom fusion method
        
        Returns:
            Search results
        """
        # Update weights if provided
        if weights:
            self.hybrid_search.update_weights(
                vector=weights.get('vector'),
                fulltext=weights.get('fulltext'),
                metadata=weights.get('metadata')
            )
        
        # Update fusion method if provided
        if fusion_method:
            original_method = self.hybrid_search.config.fusion_method
            self.hybrid_search.config.fusion_method = fusion_method
        
        # Perform search
        result = self.search(
            query=query,
            k=k,
            entity_types=entity_types,
            filters=filters,
            include_scores=True,
            include_facets=True
        )
        
        # Restore original method
        if fusion_method:
            self.hybrid_search.config.fusion_method = original_method
        
        return result
    
    def index_all_content(self) -> Dict[str, Any]:
        """
        Index all content in the database.
        
        Returns:
            Indexing statistics
        """
        try:
            logger.info("Starting full content indexing...")
            
            indexer = EmbeddingIndexer(
                vectorizer=self.vectorizer,
                db_session=self.db_session
            )
            
            stats = indexer.index_all()
            
            # Add computed fields
            stats['time_taken'] = stats.get('profiles', {}).get('time_taken', 0) + \
                                 stats.get('snippets', {}).get('time_taken', 0) + \
                                 stats.get('content', {}).get('time_taken', 0)
            stats['profiles_indexed'] = stats.get('profiles', {}).get('indexed', 0)
            stats['snippets_indexed'] = stats.get('snippets', {}).get('indexed', 0)
            
            # Reload vectors into search index
            self._load_vectors_from_db()
            
            logger.success(f"Indexed {stats['total_indexed']} items in {stats['time_taken']:.2f}s")
            
            return {
                'success': True,
                'statistics': stats
            }
        
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_and_index_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new profile and index it immediately.
        
        Args:
            profile_data: Profile information
        
        Returns:
            Result with profile ID
        """
        from src.database.repository import ProfileRepository
        from src.database.models import Profile
        
        try:
            with self.db_session.get_session() as session:
                repo = ProfileRepository(session)
                
                # Create profile
                profile = Profile(**profile_data)
                profile = repo.create(profile)
                
                profile_id = profile.id
            
            # Index the new profile
            indexer = EmbeddingIndexer(
                vectorizer=self.vectorizer,
                db_session=self.db_session
            )
            
            indexer.index_profiles([profile_id])
            
            logger.success(f"Added and indexed profile: {profile_id}")
            
            return {
                'success': True,
                'profile_id': profile_id,
                'message': 'Profile added and indexed successfully'
            }
        
        except Exception as e:
            logger.error(f"Error adding profile: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_and_index_snippet(self, snippet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new knowledge snippet and index it.
        
        Args:
            snippet_data: Snippet information
        
        Returns:
            Result with snippet ID
        """
        from src.database.repository import KnowledgeSnippetRepository
        from src.database.models import KnowledgeSnippet
        
        try:
            with self.db_session.get_session() as session:
                repo = KnowledgeSnippetRepository(session)
                
                # Create snippet
                snippet = KnowledgeSnippet(**snippet_data)
                snippet = repo.create(snippet)
                
                snippet_id = snippet.id
            
            # Index the new snippet
            indexer = EmbeddingIndexer(
                vectorizer=self.vectorizer,
                db_session=self.db_session
            )
            
            indexer.index_snippets([snippet_id])
            
            logger.success(f"Added and indexed snippet: {snippet_id}")
            
            return {
                'success': True,
                'snippet_id': snippet_id,
                'message': 'Snippet added and indexed successfully'
            }
        
        except Exception as e:
            logger.error(f"Error adding snippet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive search statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get vector search stats
            vector_stats = self.vector_search.get_statistics()
            
            # Get hybrid search config
            hybrid_stats = self.hybrid_search.get_statistics()
            
            # Get database counts
            from src.database.models import Profile, KnowledgeSnippet, Content, EmbeddingVector
            
            with self.db_session.get_session() as session:
                profile_count = session.query(Profile).count()
                snippet_count = session.query(KnowledgeSnippet).count()
                content_count = session.query(Content).count()
                vector_count = session.query(EmbeddingVector).count()
            
            return {
                'database': {
                    'profiles': profile_count,
                    'snippets': snippet_count,
                    'content': content_count,
                    'vectors': vector_count
                },
                'vector_search': vector_stats,
                'hybrid_search': hybrid_stats,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'error': str(e)
            }
    
    def update_search_config(self,
                           vector_weight: float = None,
                           fulltext_weight: float = None,
                           metadata_weight: float = None,
                           fusion_method: str = None):
        """
        Update search configuration dynamically.
        
        Args:
            vector_weight: New vector weight
            fulltext_weight: New full-text weight
            metadata_weight: New metadata weight
            fusion_method: New fusion method
        """
        if any(w is not None for w in [vector_weight, fulltext_weight, metadata_weight]):
            self.hybrid_search.update_weights(
                vector=vector_weight,
                fulltext=fulltext_weight,
                metadata=metadata_weight
            )
        
        if fusion_method:
            self.hybrid_search.config.fusion_method = fusion_method
        
        logger.info("Search configuration updated")


# Example usage
if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold cyan]Production Hybrid Search Service[/bold cyan]\n"
        "Full-text + Vector + Metadata = Comprehensive Search",
        border_style="cyan"
    ))
    
    # Initialize service
    console.print("\n[yellow]Initializing hybrid search service...[/yellow]")
    service = ProductionHybridSearchService(
        vector_weight=0.5,
        fulltext_weight=0.3,
        metadata_weight=0.2,
        fusion_method='weighted_sum'
    )
    console.print("[green]✓[/green] Service initialized")
    
    # Index all content
    console.print("\n[yellow]Indexing all content...[/yellow]")
    index_result = service.index_all_content()
    
    if index_result['success']:
        stats = index_result['statistics']
        console.print(f"[green]✓[/green] Indexed {stats['total_indexed']} items in {stats['time_taken']:.2f}s")
        console.print(f"  Profiles: {stats['profiles_indexed']}")
        console.print(f"  Snippets: {stats['snippets_indexed']}")
    
    # Search examples
    test_queries = [
        ("machine learning expert", "General search"),
        ("React developer", "Full-text emphasis"),
        ("cloud security", "Metadata filtering")
    ]
    
    for query, description in test_queries:
        console.print(f"\n[bold blue]Search: '{query}'[/bold blue] [dim]({description})[/dim]")
        
        result = service.search(
            query=query,
            k=3,
            include_scores=True
        )
        
        if result['success']:
            table = Table(show_header=True)
            table.add_column("Rank", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Title", style="green")
            table.add_column("Score", style="yellow")
            
            for r in result['results']:
                content = r.get('content', {})
                title = content.get('title') or content.get('name', 'N/A')
                
                table.add_row(
                    str(r['rank']),
                    r['entity_type'],
                    title[:40],
                    f"{r['score']:.3f}"
                )
            
            console.print(table)
            console.print(f"[dim]Time: {result['search_time']:.3f}s | "
                         f"Config: V={result['config']['vector_weight']:.1f} "
                         f"T={result['config']['fulltext_weight']:.1f} "
                         f"M={result['config']['metadata_weight']:.1f}[/dim]")
    
    # Statistics
    console.print("\n[bold green]Service Statistics:[/bold green]")
    stats = service.get_statistics()
    
    stats_table = Table(show_header=True)
    stats_table.add_column("Category", style="cyan")
    stats_table.add_column("Metric", style="yellow")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Database", "Profiles", str(stats['database']['profiles']))
    stats_table.add_row("Database", "Snippets", str(stats['database']['snippets']))
    stats_table.add_row("Database", "Vectors", str(stats['database']['vectors']))
    
    if 'vector_search' in stats and stats['vector_search']:
        if 'total_indexed' in stats['vector_search']:
            stats_table.add_row("Search", "Total Indexed", str(stats['vector_search']['total_indexed']))
        if 'dimension' in stats['vector_search']:
            stats_table.add_row("Search", "Dimensions", str(stats['vector_search']['dimension']))
    
    console.print(stats_table)
    
    console.print("\n[bold green]✓ Hybrid search service demo completed![/bold green]")
