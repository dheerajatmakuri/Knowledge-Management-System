"""
Hybrid Search Engine combining full-text, vector similarity, and metadata filtering.
Provides comprehensive and accurate knowledge retrieval.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from loguru import logger
from sqlalchemy import or_, and_

from .vector_search import VectorSearch, SearchResult, SearchResults
from .indexing import ContentVectorizationPipeline


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""
    # Weight distribution for different search methods
    vector_weight: float = 0.5      # Weight for vector similarity
    fulltext_weight: float = 0.3    # Weight for full-text search
    metadata_weight: float = 0.2    # Weight for metadata matching
    
    # Search parameters
    use_fulltext: bool = True
    use_vector: bool = True
    use_metadata: bool = True
    
    # Fusion strategy
    fusion_method: str = 'weighted_sum'  # 'weighted_sum', 'reciprocal_rank', 'max'
    
    # Performance
    enable_caching: bool = True
    parallel_search: bool = True


@dataclass
class SearchScore:
    """Detailed scoring breakdown for a search result."""
    total_score: float
    vector_score: float = 0.0
    fulltext_score: float = 0.0
    metadata_score: float = 0.0
    rank_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'total': self.total_score,
            'vector': self.vector_score,
            'fulltext': self.fulltext_score,
            'metadata': self.metadata_score,
            'rank': self.rank_score
        }


class FullTextSearchEngine:
    """Full-text search using SQLite FTS5."""
    
    def __init__(self, db_session):
        """Initialize full-text search engine."""
        self.db_session = db_session
    
    def search(self,
               query: str,
               entity_types: Optional[List[str]] = None,
               k: int = 100) -> List[Tuple[str, int, float]]:
        """
        Perform full-text search.
        
        Args:
            query: Search query
            entity_types: Filter by entity types
            k: Maximum results
        
        Returns:
            List of (entity_type, entity_id, score) tuples
        """
        from ..database.models import SearchIndex, Profile, KnowledgeSnippet, Content
        
        results = []
        query_lower = query.lower()
        
        with self.db_session.get_session() as session:
            try:
                # Search profiles directly
                if not entity_types or 'profile' in entity_types:
                    profiles = session.query(Profile).filter(
                        or_(
                            Profile.name.ilike(f'%{query}%'),
                            Profile.title.ilike(f'%{query}%'),
                            Profile.bio.ilike(f'%{query}%')
                        )
                    ).limit(k).all()
                    
                    for profile in profiles:
                        # Calculate relevance score
                        score = 0.0
                        name_match = query_lower in (profile.name or '').lower()
                        title_match = query_lower in (profile.title or '').lower()
                        bio_match = query_lower in (profile.bio or '').lower()
                        
                        if name_match:
                            score += 0.5
                        if title_match:
                            score += 0.3
                        if bio_match:
                            score += 0.2
                        
                        score = min(1.0, score)
                        results.append(('profile', profile.id, score))
                
                # Search snippets
                if not entity_types or 'snippet' in entity_types:
                    snippet_results = session.query(
                        KnowledgeSnippet.id,
                        KnowledgeSnippet.title,
                        KnowledgeSnippet.content
                    ).filter(
                        KnowledgeSnippet.title.like(f'%{query}%') |
                        KnowledgeSnippet.content.like(f'%{query}%')
                    ).limit(k).all()
                    
                    for snippet_id, title, content in snippet_results:
                        # Simple relevance scoring
                        title_match = query.lower() in (title or '').lower()
                        content_match = query.lower() in (content or '').lower()
                        score = (0.7 if title_match else 0.0) + (0.3 if content_match else 0.0)
                        results.append(('snippet', snippet_id, score))
                
                # Search content
                if not entity_types or 'content' in entity_types:
                    content_results = session.query(
                        Content.id,
                        Content.title,
                        Content.body
                    ).filter(
                        Content.title.like(f'%{query}%') |
                        Content.body.like(f'%{query}%')
                    ).limit(k).all()
                    
                    for content_id, title, body in content_results:
                        title_match = query.lower() in (title or '').lower()
                        body_match = query.lower() in (body or '').lower()
                        score = (0.7 if title_match else 0.0) + (0.3 if body_match else 0.0)
                        results.append(('content', content_id, score))
            
            except Exception as e:
                logger.error(f"Full-text search error: {e}")
        
        # Sort by score and limit
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:k]


class MetadataFilterEngine:
    """Metadata filtering and faceted search."""
    
    def __init__(self, db_session):
        """Initialize metadata filter engine."""
        self.db_session = db_session
    
    def filter_and_score(self,
                         candidates: List[Tuple[str, int]],
                         filters: Dict[str, Any]) -> List[Tuple[str, int, float]]:
        """
        Filter candidates and score based on metadata matches.
        
        Args:
            candidates: List of (entity_type, entity_id) tuples
            filters: Metadata filters
        
        Returns:
            List of (entity_type, entity_id, score) tuples
        """
        from ..database.models import Profile, KnowledgeSnippet, Content, Category
        
        results = []
        
        with self.db_session.get_session() as session:
            for entity_type, entity_id in candidates:
                score = 0.0
                matched_filters = 0
                total_filters = len(filters)
                
                if total_filters == 0:
                    results.append((entity_type, entity_id, 1.0))
                    continue
                
                try:
                    if entity_type == 'profile':
                        entity = session.query(Profile).get(entity_id)
                        if not entity:
                            continue
                        
                        # Check filters
                        if 'is_verified' in filters and entity.is_verified == filters['is_verified']:
                            matched_filters += 1
                        
                        if 'source_domain' in filters and entity.source_domain == filters['source_domain']:
                            matched_filters += 1
                        
                        if 'min_confidence' in filters and entity.confidence_score >= filters['min_confidence']:
                            matched_filters += 1
                        
                        if 'created_after' in filters:
                            if entity.created_at and entity.created_at >= filters['created_after']:
                                matched_filters += 1
                    
                    elif entity_type == 'snippet':
                        entity = session.query(KnowledgeSnippet).get(entity_id)
                        if not entity:
                            continue
                        
                        # Check filters
                        if 'category' in filters and entity.category == filters['category']:
                            matched_filters += 1
                        
                        if 'content_type' in filters and entity.content_type == filters['content_type']:
                            matched_filters += 1
                        
                        if 'is_validated' in filters and entity.is_validated == filters['is_validated']:
                            matched_filters += 1
                        
                        if 'min_confidence' in filters and entity.confidence_score >= filters['min_confidence']:
                            matched_filters += 1
                    
                    elif entity_type == 'content':
                        entity = session.query(Content).get(entity_id)
                        if not entity:
                            continue
                        
                        # Check filters
                        if 'content_type' in filters and entity.content_type == filters['content_type']:
                            matched_filters += 1
                        
                        if 'author' in filters and entity.author_name == filters['author']:
                            matched_filters += 1
                    
                    # Calculate score based on matched filters
                    if total_filters > 0:
                        score = matched_filters / total_filters
                    
                    results.append((entity_type, entity_id, score))
                
                except Exception as e:
                    logger.error(f"Metadata filtering error for {entity_type}:{entity_id}: {e}")
                    continue
        
        return results
    
    def get_facets(self,
                   results: List[Tuple[str, int]],
                   facet_fields: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Generate facet counts for search results.
        
        Args:
            results: Search results
            facet_fields: Fields to facet on
        
        Returns:
            Dictionary of facet counts
        """
        from ..database.models import Profile, KnowledgeSnippet, Content
        
        facets = {field: {} for field in facet_fields}
        
        with self.db_session.get_session() as session:
            for entity_type, entity_id in results:
                try:
                    if entity_type == 'profile':
                        entity = session.query(Profile).get(entity_id)
                        if entity:
                            if 'source_domain' in facet_fields and entity.source_domain:
                                facets['source_domain'][entity.source_domain] = \
                                    facets['source_domain'].get(entity.source_domain, 0) + 1
                            
                            if 'is_verified' in facet_fields:
                                key = 'Verified' if entity.is_verified else 'Unverified'
                                facets['is_verified'][key] = facets['is_verified'].get(key, 0) + 1
                    
                    elif entity_type == 'snippet':
                        entity = session.query(KnowledgeSnippet).get(entity_id)
                        if entity:
                            if 'category' in facet_fields and entity.category:
                                facets['category'][entity.category] = \
                                    facets['category'].get(entity.category, 0) + 1
                            
                            if 'content_type' in facet_fields and entity.content_type:
                                facets['content_type'][entity.content_type] = \
                                    facets['content_type'].get(entity.content_type, 0) + 1
                    
                    elif entity_type == 'content':
                        entity = session.query(Content).get(entity_id)
                        if entity:
                            if 'content_type' in facet_fields and entity.content_type:
                                facets['content_type'][entity.content_type] = \
                                    facets['content_type'].get(entity.content_type, 0) + 1
                            
                            if 'author' in facet_fields and entity.author_name:
                                facets['author'][entity.author_name] = \
                                    facets['author'].get(entity.author_name, 0) + 1
                
                except Exception as e:
                    logger.error(f"Facet generation error: {e}")
                    continue
        
        return facets


class ResultFusionEngine:
    """Result fusion and ranking algorithms."""
    
    @staticmethod
    def weighted_sum(results: Dict[str, List[Tuple[str, int, float]]],
                    weights: Dict[str, float]) -> List[Tuple[str, int, SearchScore]]:
        """
        Fuse results using weighted sum of scores.
        
        Args:
            results: Dictionary of result lists by method
            weights: Weights for each method
        
        Returns:
            Fused results with detailed scores
        """
        # Combine all results
        combined = {}
        
        for method, result_list in results.items():
            weight = weights.get(method, 0.0)
            
            for entity_type, entity_id, score in result_list:
                key = (entity_type, entity_id)
                
                if key not in combined:
                    combined[key] = SearchScore(total_score=0.0)
                
                weighted_score = score * weight
                combined[key].total_score += weighted_score
                
                # Track individual scores
                if method == 'vector':
                    combined[key].vector_score = score
                elif method == 'fulltext':
                    combined[key].fulltext_score = score
                elif method == 'metadata':
                    combined[key].metadata_score = score
        
        # Convert to list and sort
        fused_results = [
            (entity_type, entity_id, score)
            for (entity_type, entity_id), score in combined.items()
        ]
        
        fused_results.sort(key=lambda x: x[2].total_score, reverse=True)
        
        return fused_results
    
    @staticmethod
    def reciprocal_rank_fusion(results: Dict[str, List[Tuple[str, int, float]]],
                               k: int = 60) -> List[Tuple[str, int, SearchScore]]:
        """
        Fuse results using Reciprocal Rank Fusion (RRF).
        
        Args:
            results: Dictionary of result lists by method
            k: Constant for RRF formula
        
        Returns:
            Fused results with RRF scores
        """
        combined = {}
        
        for method, result_list in results.items():
            for rank, (entity_type, entity_id, original_score) in enumerate(result_list, 1):
                key = (entity_type, entity_id)
                
                if key not in combined:
                    combined[key] = SearchScore(total_score=0.0)
                
                # RRF score: 1 / (k + rank)
                rrf_score = 1.0 / (k + rank)
                combined[key].total_score += rrf_score
                combined[key].rank_score += rrf_score
                
                # Track original scores
                if method == 'vector':
                    combined[key].vector_score = original_score
                elif method == 'fulltext':
                    combined[key].fulltext_score = original_score
                elif method == 'metadata':
                    combined[key].metadata_score = original_score
        
        # Convert and sort
        fused_results = [
            (entity_type, entity_id, score)
            for (entity_type, entity_id), score in combined.items()
        ]
        
        fused_results.sort(key=lambda x: x[2].total_score, reverse=True)
        
        return fused_results
    
    @staticmethod
    def max_score_fusion(results: Dict[str, List[Tuple[str, int, float]]]) -> List[Tuple[str, int, SearchScore]]:
        """
        Fuse results by taking maximum score across methods.
        
        Args:
            results: Dictionary of result lists by method
        
        Returns:
            Fused results with max scores
        """
        combined = {}
        
        for method, result_list in results.items():
            for entity_type, entity_id, score in result_list:
                key = (entity_type, entity_id)
                
                if key not in combined:
                    combined[key] = SearchScore(total_score=0.0)
                
                # Track individual scores
                if method == 'vector':
                    combined[key].vector_score = score
                elif method == 'fulltext':
                    combined[key].fulltext_score = score
                elif method == 'metadata':
                    combined[key].metadata_score = score
                
                # Take maximum
                combined[key].total_score = max(
                    combined[key].total_score,
                    score
                )
        
        # Convert and sort
        fused_results = [
            (entity_type, entity_id, score)
            for (entity_type, entity_id), score in combined.items()
        ]
        
        fused_results.sort(key=lambda x: x[2].total_score, reverse=True)
        
        return fused_results


class HybridSearchEngine:
    """
    Comprehensive hybrid search engine combining multiple search methods.
    """
    
    def __init__(self,
                 db_session,
                 vector_search: VectorSearch,
                 vectorizer: ContentVectorizationPipeline,
                 config: HybridSearchConfig = None):
        """
        Initialize hybrid search engine.
        
        Args:
            db_session: Database session manager
            vector_search: Vector search engine
            vectorizer: Content vectorization pipeline
            config: Hybrid search configuration
        """
        self.db_session = db_session
        self.vector_search = vector_search
        self.vectorizer = vectorizer
        self.config = config or HybridSearchConfig()
        
        # Initialize sub-engines
        self.fulltext_engine = FullTextSearchEngine(db_session)
        self.metadata_engine = MetadataFilterEngine(db_session)
        self.fusion_engine = ResultFusionEngine()
        
        logger.success("Hybrid search engine initialized")
    
    def search(self,
               query: str,
               k: int = 10,
               entity_types: Optional[List[str]] = None,
               filters: Optional[Dict[str, Any]] = None,
               include_scores: bool = False,
               include_facets: bool = False,
               facet_fields: Optional[List[str]] = None) -> SearchResults:
        """
        Perform hybrid search combining all methods.
        
        Args:
            query: Search query
            k: Number of results
            entity_types: Filter by entity types
            filters: Metadata filters
            include_scores: Include detailed score breakdown
            include_facets: Include facet counts
            facet_fields: Fields to facet on
        
        Returns:
            SearchResults with fused and ranked results
        """
        import time
        start_time = time.time()
        
        logger.info(f"Hybrid search: '{query}'")
        
        # Collect results from different methods
        all_results = {}
        
        # 1. Vector similarity search
        if self.config.use_vector:
            logger.debug("Performing vector search...")
            query_vector = self.vectorizer.encode_single(query)
            vector_results = self.vector_search.search(
                query_vector=query_vector,
                k=k * 3,  # Get more candidates for fusion
                filters={'entity_type': entity_types} if entity_types else None
            )
            
            all_results['vector'] = [
                (r.entity_type, r.entity_id, r.score)
                for r in vector_results.results
            ]
            logger.debug(f"Vector search: {len(all_results['vector'])} results")
        
        # 2. Full-text search
        if self.config.use_fulltext:
            logger.debug("Performing full-text search...")
            fulltext_results = self.fulltext_engine.search(
                query=query,
                entity_types=entity_types,
                k=k * 3
            )
            all_results['fulltext'] = fulltext_results
            logger.debug(f"Full-text search: {len(fulltext_results)} results")
        
        # 3. Metadata filtering (if filters provided)
        if self.config.use_metadata and filters:
            logger.debug("Applying metadata filters...")
            # Get all candidates
            candidates = set()
            for results in all_results.values():
                candidates.update((et, eid) for et, eid, _ in results)
            
            metadata_results = self.metadata_engine.filter_and_score(
                list(candidates),
                filters
            )
            all_results['metadata'] = metadata_results
            logger.debug(f"Metadata filtered: {len(metadata_results)} results")
        
        # 4. Fuse results
        logger.debug(f"Fusing results using {self.config.fusion_method}...")
        
        weights = {
            'vector': self.config.vector_weight,
            'fulltext': self.config.fulltext_weight,
            'metadata': self.config.metadata_weight
        }
        
        if self.config.fusion_method == 'weighted_sum':
            fused_results = self.fusion_engine.weighted_sum(all_results, weights)
        elif self.config.fusion_method == 'reciprocal_rank':
            fused_results = self.fusion_engine.reciprocal_rank_fusion(all_results)
        elif self.config.fusion_method == 'max':
            fused_results = self.fusion_engine.max_score_fusion(all_results)
        else:
            fused_results = self.fusion_engine.weighted_sum(all_results, weights)
        
        # 5. Convert to SearchResults
        results = []
        for rank, (entity_type, entity_id, search_score) in enumerate(fused_results[:k], 1):
            result = SearchResult(
                entity_type=entity_type,
                entity_id=entity_id,
                score=search_score.total_score,
                rank=rank,
                metadata={
                    'fusion_method': self.config.fusion_method,
                    'search_methods': list(all_results.keys())
                }
            )
            
            # Add detailed scores if requested
            if include_scores:
                result.metadata['score_breakdown'] = search_score.to_dict()
            
            results.append(result)
        
        # 6. Enrich results with content
        self._enrich_results(results)
        
        # 7. Generate facets if requested
        facets = {}
        if include_facets and facet_fields:
            logger.debug("Generating facets...")
            candidates = [(r.entity_type, r.entity_id) for r in results]
            facets = self.metadata_engine.get_facets(candidates, facet_fields)
        
        search_time = time.time() - start_time
        
        search_results = SearchResults(
            results=results,
            query=query,
            total_results=len(results),
            search_time=search_time,
            algorithm='hybrid',
            filters_applied=filters or {}
        )
        
        # Add facets to metadata
        if facets:
            search_results.filters_applied['facets'] = facets
        
        logger.info(f"Hybrid search completed: {len(results)} results in {search_time:.3f}s")
        
        return search_results
    
    def _enrich_results(self, results: List[SearchResult]):
        """Enrich results with full content."""
        from ..database.repository import ProfileRepository, ContentRepository, KnowledgeSnippetRepository
        
        with self.db_session.get_session() as session:
            profile_repo = ProfileRepository(session)
            content_repo = ContentRepository(session)
            snippet_repo = KnowledgeSnippetRepository(session)
            
            for result in results:
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
                                'is_verified': profile.is_verified,
                                'confidence_score': profile.confidence_score
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
                                'is_validated': snippet.is_validated
                            }
                    
                    elif result.entity_type == 'content':
                        content = content_repo.get_by_id(result.entity_id)
                        if content:
                            result.content = {
                                'id': content.id,
                                'title': content.title,
                                'summary': content.summary,
                                'body': content.body[:300] if content.body else None,
                                'content_type': content.content_type,
                                'author_name': content.author_name
                            }
                
                except Exception as e:
                    logger.error(f"Error enriching result: {e}")
                    result.content = {'error': 'Failed to load content'}
    
    def update_weights(self, vector: float = None, fulltext: float = None, metadata: float = None):
        """Update search method weights dynamically."""
        if vector is not None:
            self.config.vector_weight = vector
        if fulltext is not None:
            self.config.fulltext_weight = fulltext
        if metadata is not None:
            self.config.metadata_weight = metadata
        
        # Normalize weights
        total = self.config.vector_weight + self.config.fulltext_weight + self.config.metadata_weight
        if total > 0:
            self.config.vector_weight /= total
            self.config.fulltext_weight /= total
            self.config.metadata_weight /= total
        
        logger.info(f"Updated weights: vector={self.config.vector_weight:.2f}, "
                   f"fulltext={self.config.fulltext_weight:.2f}, "
                   f"metadata={self.config.metadata_weight:.2f}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get hybrid search statistics."""
        return {
            'config': {
                'vector_weight': self.config.vector_weight,
                'fulltext_weight': self.config.fulltext_weight,
                'metadata_weight': self.config.metadata_weight,
                'fusion_method': self.config.fusion_method
            },
            'enabled_methods': {
                'vector': self.config.use_vector,
                'fulltext': self.config.use_fulltext,
                'metadata': self.config.use_metadata
            }
        }
