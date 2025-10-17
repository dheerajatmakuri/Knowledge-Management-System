"""
High-level semantic search service integrating all search components.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import os
from loguru import logger

from ..search.indexing import ContentVectorizationPipeline, EmbeddingConfig, EmbeddingIndexer
from ..search.vector_search import VectorSearch, SearchResults
from ..database.repository import (
    ProfileRepository,
    ContentRepository,
    KnowledgeSnippetRepository,
    SearchCacheRepository,
    EmbeddingVectorRepository
)


@dataclass
class SearchConfig:
    """Configuration for semantic search."""
    embedding_provider: str = 'sentence-transformers'
    embedding_model: str = 'all-MiniLM-L6-v2'
    search_backend: str = 'faiss'
    search_metric: str = 'cosine'
    use_gpu: bool = False
    use_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    default_k: int = 10
    min_score: float = 0.5
    use_query_expansion: bool = True


class SemanticSearchService:
    """
    Unified semantic search service.
    Provides high-level search across all content types.
    """
    
    def __init__(self, db_session, config: SearchConfig = None):
        """
        Initialize semantic search service.
        
        Args:
            db_session: Database session manager
            config: Search configuration
        """
        self.db_session = db_session
        self.config = config or SearchConfig()
        
        # Initialize vectorization pipeline
        embedding_config = EmbeddingConfig(
            provider=self.config.embedding_provider,
            model_name=self.config.embedding_model,
            normalize=True
        )
        self.vectorizer = ContentVectorizationPipeline(embedding_config)
        
        # Initialize indexer
        self.indexer = EmbeddingIndexer(self.vectorizer, db_session)
        
        # Initialize vector search engine
        self.search_engine = VectorSearch(
            dimension=self.vectorizer.config.dimension,
            backend=self.config.search_backend,
            metric=self.config.search_metric,
            use_gpu=self.config.use_gpu
        )
        
        self._load_index()
        
        logger.success("Semantic search service initialized")
    
    def _load_index(self):
        """Load vectors from database into search engine."""
        logger.info("Loading vector index from database...")
        
        with self.db_session.get_session() as session:
            embedding_repo = EmbeddingVectorRepository(session)
            
            # Get all embeddings
            embeddings = embedding_repo.get_all()
            
            if not embeddings:
                logger.warning("No embeddings found in database. Run indexing first.")
                return
            
            # Prepare vectors and entity mapping
            import numpy as np
            vectors = []
            entity_mapping = []
            
            for emb in embeddings:
                if len(emb.vector) == self.vectorizer.config.dimension:
                    vectors.append(emb.vector)
                    entity_mapping.append((emb.entity_type, emb.entity_id))
            
            if vectors:
                vectors_array = np.array(vectors)
                self.search_engine.add_vectors(vectors_array, entity_mapping)
                self.search_engine.build_index()
                
                logger.success(f"Loaded {len(vectors)} vectors into search engine")
            else:
                logger.warning("No valid vectors found")
    
    def search(self,
               query: str,
               k: int = None,
               entity_types: List[str] = None,
               min_score: float = None,
               use_expansion: bool = None,
               include_content: bool = True) -> SearchResults:
        """
        Perform semantic search across all content.
        
        Args:
            query: Search query
            k: Number of results to return
            entity_types: Filter by entity types (e.g., ['profile', 'snippet'])
            min_score: Minimum similarity score
            use_expansion: Use query expansion
            include_content: Include full content in results
        
        Returns:
            SearchResults object
        """
        k = k or self.config.default_k
        min_score = min_score or self.config.min_score
        use_expansion = use_expansion if use_expansion is not None else self.config.use_query_expansion
        
        # Check cache first
        if self.config.use_cache:
            cached = self._get_cached_results(query, k, entity_types)
            if cached:
                logger.info("Returning cached results")
                return cached
        
        # Prepare filters
        filters = {}
        if entity_types:
            filters['entity_type'] = entity_types
        
        # Perform search
        results = self.search_engine.search_with_text(
            query_text=query,
            vectorizer=self.vectorizer,
            k=k,
            expand_query=use_expansion,
            filters=filters
        )
        
        # Enrich results with content
        if include_content:
            self._enrich_results(results)
        
        # Cache results
        if self.config.use_cache:
            self._cache_results(query, k, entity_types, results)
        
        logger.info(f"Found {len(results.results)} results for query: {query}")
        return results
    
    def search_profiles(self, query: str, k: int = None, **kwargs) -> SearchResults:
        """Search for profiles."""
        return self.search(query, k=k, entity_types=['profile'], **kwargs)
    
    def search_snippets(self, query: str, k: int = None, **kwargs) -> SearchResults:
        """Search for knowledge snippets."""
        return self.search(query, k=k, entity_types=['snippet'], **kwargs)
    
    def search_content(self, query: str, k: int = None, **kwargs) -> SearchResults:
        """Search for content."""
        return self.search(query, k=k, entity_types=['content'], **kwargs)
    
    def find_similar(self,
                    entity_type: str,
                    entity_id: int,
                    k: int = 10) -> SearchResults:
        """
        Find similar entities to a given entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            k: Number of similar items to return
        
        Returns:
            SearchResults object
        """
        with self.db_session.get_session() as session:
            embedding_repo = EmbeddingVectorRepository(session)
            
            # Get entity embedding
            embeddings = embedding_repo.get_by_entity(entity_type, entity_id)
            
            if not embeddings:
                logger.warning(f"No embedding found for {entity_type}:{entity_id}")
                return SearchResults(
                    results=[],
                    query=f"similar_to_{entity_type}_{entity_id}",
                    total_results=0,
                    search_time=0.0,
                    algorithm=self.config.search_backend
                )
            
            # Use the embedding to search
            import numpy as np
            query_vector = np.array(embeddings[0].vector)
            
            results = self.search_engine.search(
                query_vector=query_vector,
                k=k + 1,  # +1 to exclude self
                min_score=self.config.min_score
            )
            
            # Remove self from results
            results.results = [
                r for r in results.results 
                if not (r.entity_type == entity_type and r.entity_id == entity_id)
            ][:k]
            
            # Update ranks
            for rank, result in enumerate(results.results, 1):
                result.rank = rank
            
            self._enrich_results(results)
            
            return results
    
    def _enrich_results(self, results: SearchResults):
        """Enrich search results with full content."""
        with self.db_session.get_session() as session:
            profile_repo = ProfileRepository(session)
            content_repo = ContentRepository(session)
            snippet_repo = KnowledgeSnippetRepository(session)
            
            for result in results.results:
                try:
                    if result.entity_type == 'profile':
                        profile = profile_repo.get_by_id(result.entity_id)
                        if profile:
                            result.content = {
                                'id': profile.id,
                                'name': profile.name,
                                'title': profile.title,
                                'bio': profile.bio[:200] if profile.bio else None,
                                'email': profile.email,
                                'source_url': profile.source_url,
                                'created_at': profile.created_at.isoformat() if profile.created_at else None
                            }
                    
                    elif result.entity_type == 'snippet':
                        snippet = snippet_repo.get_by_id(result.entity_id)
                        if snippet:
                            result.content = {
                                'id': snippet.id,
                                'title': snippet.title,
                                'content': snippet.content[:300] if snippet.content else None,
                                'content_type': snippet.content_type,
                                'category': snippet.category,
                                'confidence_score': snippet.confidence_score,
                                'source_url': snippet.source_url,
                                'created_at': snippet.created_at.isoformat() if snippet.created_at else None
                            }
                    
                    elif result.entity_type == 'content':
                        content = content_repo.get_by_id(result.entity_id)
                        if content:
                            result.content = {
                                'id': content.id,
                                'title': content.title,
                                'summary': content.summary,
                                'body': content.body[:300] if content.body else None,
                                'url': content.url,
                                'content_type': content.content_type,
                                'created_at': content.created_at.isoformat() if content.created_at else None
                            }
                
                except Exception as e:
                    logger.error(f"Error enriching result: {e}")
                    result.content = {'error': 'Failed to load content'}
    
    def _get_cached_results(self,
                           query: str,
                           k: int,
                           entity_types: List[str]) -> Optional[SearchResults]:
        """Get cached search results."""
        try:
            with self.db_session.get_session() as session:
                cache_repo = SearchCacheRepository(session)
                
                # Create cache key
                cache_key = f"{query}|{k}|{','.join(sorted(entity_types or []))}"
                
                cached = cache_repo.get_cached_results(cache_key)
                if cached:
                    # Convert cached JSON to SearchResults
                    # (Would need to implement from_dict methods)
                    return None  # Placeholder
                
                return None
        
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    def _cache_results(self,
                      query: str,
                      k: int,
                      entity_types: List[str],
                      results: SearchResults):
        """Cache search results."""
        try:
            with self.db_session.get_session() as session:
                cache_repo = SearchCacheRepository(session)
                
                # Extract result IDs
                result_ids = [r.entity_id for r in results.results]
                
                # Store results
                cache_repo.cache_results(
                    query_text=query,
                    result_ids=result_ids,
                    search_type='semantic',
                    ttl_hours=self.config.cache_ttl // 3600  # Convert seconds to hours
                )
                
                session.commit()
        
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def rebuild_index(self) -> Dict[str, Any]:
        """
        Rebuild the entire search index.
        
        Returns:
            Statistics about the rebuild
        """
        logger.info("Rebuilding search index...")
        
        # Clear current index
        self.search_engine = VectorSearch(
            dimension=self.vectorizer.config.dimension,
            backend=self.config.search_backend,
            metric=self.config.search_metric,
            use_gpu=self.config.use_gpu
        )
        
        # Reindex all content
        stats = self.indexer.index_all()
        
        # Reload index
        self._load_index()
        
        logger.success("Index rebuild complete")
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search service statistics."""
        index_stats = self.indexer.get_index_statistics()
        search_stats = self.search_engine.get_statistics()
        
        return {
            'indexing': index_stats,
            'search_engine': search_stats,
            'config': {
                'provider': self.config.embedding_provider,
                'model': self.config.embedding_model,
                'backend': self.config.search_backend,
                'dimension': self.vectorizer.config.dimension
            }
        }


# Utility function to create service with environment config
def create_search_service(db_session) -> SemanticSearchService:
    """
    Create search service from environment configuration.
    
    Args:
        db_session: Database session manager
    
    Returns:
        Configured SemanticSearchService
    """
    config = SearchConfig(
        embedding_provider=os.getenv('EMBEDDING_PROVIDER', 'sentence-transformers'),
        embedding_model=os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
        search_backend=os.getenv('SEARCH_BACKEND', 'faiss'),
        search_metric=os.getenv('SEARCH_METRIC', 'cosine'),
        use_gpu=os.getenv('USE_GPU', 'false').lower() == 'true',
        use_cache=os.getenv('USE_SEARCH_CACHE', 'true').lower() == 'true',
        cache_ttl=int(os.getenv('SEARCH_CACHE_TTL', '3600')),
        default_k=int(os.getenv('DEFAULT_SEARCH_K', '10')),
        min_score=float(os.getenv('MIN_SEARCH_SCORE', '0.5')),
        use_query_expansion=os.getenv('USE_QUERY_EXPANSION', 'true').lower() == 'true'
    )
    
    return SemanticSearchService(db_session, config)
