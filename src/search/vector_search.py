"""
Vector-based semantic search with similarity scoring and ranking.
Supports FAISS, Annoy, and brute-force search strategies.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from loguru import logger
import time
from datetime import datetime

# FAISS for efficient similarity search
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Using brute-force search.")

# Annoy for approximate nearest neighbors
try:
    from annoy import AnnoyIndex
    ANNOY_AVAILABLE = True
except ImportError:
    ANNOY_AVAILABLE = False
    logger.warning("Annoy not available")


@dataclass
class SearchResult:
    """Single search result with relevance information."""
    entity_type: str
    entity_id: int
    score: float
    rank: int
    content: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'score': float(self.score),
            'rank': self.rank,
            'content': self.content,
            'metadata': self.metadata
        }


@dataclass
class SearchResults:
    """Collection of search results with metadata."""
    results: List[SearchResult]
    query: str
    total_results: int
    search_time: float
    algorithm: str
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'results': [r.to_dict() for r in self.results],
            'query': self.query,
            'total_results': self.total_results,
            'search_time': self.search_time,
            'algorithm': self.algorithm,
            'filters_applied': self.filters_applied
        }


class SimilarityComputationAlgorithms:
    """Various similarity computation algorithms."""
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Similarity score (0 to 1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    @staticmethod
    def cosine_similarity_batch(query_vec: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and multiple vectors.
        
        Args:
            query_vec: Query vector (1D)
            vectors: Matrix of vectors (2D)
        
        Returns:
            Array of similarity scores
        """
        # Normalize query
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        
        # Normalize vectors
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-10
        vectors_norm = vectors / norms
        
        # Compute similarities
        similarities = np.dot(vectors_norm, query_norm)
        return similarities
    
    @staticmethod
    def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute Euclidean distance between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Distance (lower is more similar)
        """
        return float(np.linalg.norm(vec1 - vec2))
    
    @staticmethod
    def manhattan_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute Manhattan distance between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Distance (lower is more similar)
        """
        return float(np.sum(np.abs(vec1 - vec2)))
    
    @staticmethod
    def dot_product_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute dot product similarity.
        
        Args:
            vec1: First vector (should be normalized)
            vec2: Second vector (should be normalized)
        
        Returns:
            Similarity score
        """
        return float(np.dot(vec1, vec2))


class RelevanceScoringMechanism:
    """Advanced relevance scoring with multiple signals."""
    
    def __init__(self, 
                 semantic_weight: float = 0.6,
                 recency_weight: float = 0.2,
                 popularity_weight: float = 0.1,
                 quality_weight: float = 0.1):
        """
        Initialize scoring mechanism.
        
        Args:
            semantic_weight: Weight for semantic similarity
            recency_weight: Weight for content recency
            popularity_weight: Weight for popularity signals
            quality_weight: Weight for quality signals
        """
        self.semantic_weight = semantic_weight
        self.recency_weight = recency_weight
        self.popularity_weight = popularity_weight
        self.quality_weight = quality_weight
    
    def compute_score(self,
                     semantic_score: float,
                     entity_data: Dict[str, Any]) -> float:
        """
        Compute final relevance score combining multiple signals.
        
        Args:
            semantic_score: Similarity score from vector search
            entity_data: Additional entity data for scoring
        
        Returns:
            Final relevance score
        """
        # Start with semantic similarity
        final_score = semantic_score * self.semantic_weight
        
        # Add recency score
        if 'created_at' in entity_data:
            recency_score = self._compute_recency_score(entity_data['created_at'])
            final_score += recency_score * self.recency_weight
        
        # Add popularity score
        if 'view_count' in entity_data or 'access_count' in entity_data:
            popularity_score = self._compute_popularity_score(entity_data)
            final_score += popularity_score * self.popularity_weight
        
        # Add quality score
        if 'confidence_score' in entity_data or 'is_verified' in entity_data:
            quality_score = self._compute_quality_score(entity_data)
            final_score += quality_score * self.quality_weight
        
        return final_score
    
    def _compute_recency_score(self, created_at) -> float:
        """Compute recency score (newer content scores higher)."""
        try:
            if isinstance(created_at, str):
                from datetime import datetime
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            # Days since creation
            days_old = (datetime.utcnow() - created_at).days
            
            # Decay function: score decreases with age
            # Score ranges from 0 to 1
            if days_old < 7:
                return 1.0
            elif days_old < 30:
                return 0.8
            elif days_old < 90:
                return 0.6
            elif days_old < 180:
                return 0.4
            elif days_old < 365:
                return 0.2
            else:
                return 0.1
        except:
            return 0.5  # Default score
    
    def _compute_popularity_score(self, entity_data: Dict[str, Any]) -> float:
        """Compute popularity score based on engagement metrics."""
        view_count = entity_data.get('view_count', 0) or entity_data.get('access_count', 0)
        
        # Logarithmic scaling to prevent dominant high-view content
        if view_count > 0:
            return min(1.0, np.log10(view_count + 1) / 5.0)
        return 0.0
    
    def _compute_quality_score(self, entity_data: Dict[str, Any]) -> float:
        """Compute quality score based on verification and confidence."""
        score = 0.0
        
        if entity_data.get('is_verified'):
            score += 0.5
        
        if 'confidence_score' in entity_data:
            score += entity_data['confidence_score'] * 0.5
        
        return min(1.0, score)


class QueryExpansionTechniques:
    """Techniques for expanding queries to improve recall."""
    
    @staticmethod
    def expand_with_synonyms(query: str, synonym_dict: Dict[str, List[str]]) -> List[str]:
        """
        Expand query with synonyms.
        
        Args:
            query: Original query
            synonym_dict: Dictionary mapping words to synonyms
        
        Returns:
            List of expanded queries
        """
        expanded = [query]
        words = query.lower().split()
        
        for word in words:
            if word in synonym_dict:
                for synonym in synonym_dict[word]:
                    expanded_query = query.lower().replace(word, synonym)
                    expanded.append(expanded_query)
        
        return list(set(expanded))
    
    @staticmethod
    def expand_with_stemming(query: str) -> List[str]:
        """
        Expand query with word stems.
        
        Args:
            query: Original query
        
        Returns:
            List with original and stemmed versions
        """
        # Simple stemming (would use NLTK in production)
        expanded = [query]
        
        # Remove common suffixes
        suffixes = ['ing', 'ed', 's', 'es', 'er', 'ly']
        words = query.split()
        
        for suffix in suffixes:
            stemmed_words = []
            for word in words:
                if word.endswith(suffix) and len(word) > len(suffix) + 2:
                    stemmed_words.append(word[:-len(suffix)])
                else:
                    stemmed_words.append(word)
            expanded.append(' '.join(stemmed_words))
        
        return list(set(expanded))
    
    @staticmethod
    def expand_with_related_terms(query: str, related_terms: Dict[str, List[str]]) -> List[str]:
        """
        Expand query with related terms.
        
        Args:
            query: Original query
            related_terms: Dictionary mapping terms to related terms
        
        Returns:
            List of expanded queries
        """
        expanded = [query]
        
        for term, relations in related_terms.items():
            if term.lower() in query.lower():
                for related in relations:
                    expanded.append(f"{query} {related}")
        
        return expanded


class VectorSearch:
    """
    Main vector search engine with multiple backends and optimization.
    """
    
    def __init__(self,
                 dimension: int,
                 backend: str = 'faiss',
                 metric: str = 'cosine',
                 use_gpu: bool = False):
        """
        Initialize vector search engine.
        
        Args:
            dimension: Embedding dimension
            backend: Search backend ('faiss', 'annoy', 'brute')
            metric: Distance metric ('cosine', 'euclidean', 'dot')
            use_gpu: Use GPU acceleration (FAISS only)
        """
        self.dimension = dimension
        self.backend = backend
        self.metric = metric
        self.use_gpu = use_gpu
        
        self.index = None
        self.entity_map = []  # Maps index positions to (entity_type, entity_id)
        self.is_trained = False
        
        self.scorer = RelevanceScoringMechanism()
        self.query_expander = QueryExpansionTechniques()
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize the search index based on backend."""
        if self.backend == 'faiss':
            if not FAISS_AVAILABLE:
                logger.warning("FAISS not available, falling back to brute-force")
                self.backend = 'brute'
                return
            
            if self.metric == 'cosine':
                # Cosine similarity using inner product on normalized vectors
                self.index = faiss.IndexFlatIP(self.dimension)
            elif self.metric == 'euclidean':
                self.index = faiss.IndexFlatL2(self.dimension)
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            if self.use_gpu and faiss.get_num_gpus() > 0:
                logger.info("Using GPU acceleration")
                self.index = faiss.index_cpu_to_gpu(
                    faiss.StandardGpuResources(), 0, self.index
                )
            
            logger.success(f"FAISS index initialized: {self.metric}")
        
        elif self.backend == 'annoy':
            if not ANNOY_AVAILABLE:
                logger.warning("Annoy not available, falling back to brute-force")
                self.backend = 'brute'
                return
            
            metric_map = {'cosine': 'angular', 'euclidean': 'euclidean', 'dot': 'dot'}
            self.index = AnnoyIndex(self.dimension, metric_map.get(self.metric, 'angular'))
            logger.success(f"Annoy index initialized: {self.metric}")
        
        elif self.backend == 'brute':
            self.vectors_store = []
            logger.info("Using brute-force search")
        
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def add_vectors(self, vectors: np.ndarray, entity_mapping: List[Tuple[str, int]]):
        """
        Add vectors to the index.
        
        Args:
            vectors: Array of vectors to add
            entity_mapping: List of (entity_type, entity_id) tuples
        """
        if len(vectors) != len(entity_mapping):
            raise ValueError("Vectors and entity_mapping must have same length")
        
        # Normalize for cosine similarity
        if self.metric == 'cosine':
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1
            vectors = vectors / norms
        
        if self.backend == 'faiss':
            self.index.add(vectors.astype('float32'))
            self.entity_map.extend(entity_mapping)
            logger.info(f"Added {len(vectors)} vectors to FAISS index")
        
        elif self.backend == 'annoy':
            start_idx = len(self.entity_map)
            for i, vec in enumerate(vectors):
                self.index.add_item(start_idx + i, vec.tolist())
            self.entity_map.extend(entity_mapping)
            logger.info(f"Added {len(vectors)} vectors to Annoy index")
        
        elif self.backend == 'brute':
            self.vectors_store.extend(vectors)
            self.entity_map.extend(entity_mapping)
    
    def build_index(self, n_trees: int = 10):
        """Build the index (required for Annoy)."""
        if self.backend == 'annoy':
            self.index.build(n_trees)
            self.is_trained = True
            logger.success(f"Annoy index built with {n_trees} trees")
        else:
            self.is_trained = True
    
    def search(self,
               query_vector: np.ndarray,
               k: int = 10,
               filters: Optional[Dict[str, Any]] = None,
               min_score: float = 0.0) -> SearchResults:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding
            k: Number of results to return
            filters: Optional filters (entity_type, etc.)
            min_score: Minimum similarity score
        
        Returns:
            SearchResults object
        """
        start_time = time.time()
        
        # Normalize query vector for cosine similarity
        if self.metric == 'cosine':
            query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-10)
        
        # Perform search based on backend
        if self.backend == 'faiss':
            distances, indices = self.index.search(
                query_vector.reshape(1, -1).astype('float32'), k
            )
            scores = distances[0]
            indices = indices[0]
        
        elif self.backend == 'annoy':
            indices, distances = self.index.get_nns_by_vector(
                query_vector.tolist(), k, include_distances=True
            )
            # Convert distances to similarity scores
            if self.metric == 'cosine':
                scores = [1.0 - d for d in distances]
            else:
                scores = [-d for d in distances]  # Negative distance as score
        
        elif self.backend == 'brute':
            vectors = np.array(self.vectors_store)
            scores = SimilarityComputationAlgorithms.cosine_similarity_batch(
                query_vector, vectors
            )
            indices = np.argsort(scores)[::-1][:k]
            scores = scores[indices]
        
        # Build results
        results = []
        for rank, (idx, score) in enumerate(zip(indices, scores), 1):
            if score < min_score:
                continue
            
            if idx >= len(self.entity_map):
                continue
            
            entity_type, entity_id = self.entity_map[idx]
            
            # Apply filters
            if filters:
                if 'entity_type' in filters and entity_type not in filters['entity_type']:
                    continue
            
            result = SearchResult(
                entity_type=entity_type,
                entity_id=entity_id,
                score=float(score),
                rank=rank,
                metadata={'backend': self.backend, 'metric': self.metric}
            )
            results.append(result)
        
        search_time = time.time() - start_time
        
        return SearchResults(
            results=results,
            query="vector_query",
            total_results=len(results),
            search_time=search_time,
            algorithm=self.backend,
            filters_applied=filters or {}
        )
    
    def search_with_text(self,
                        query_text: str,
                        vectorizer,
                        k: int = 10,
                        expand_query: bool = False,
                        filters: Optional[Dict[str, Any]] = None) -> SearchResults:
        """
        Search using text query.
        
        Args:
            query_text: Text query
            vectorizer: Vectorization pipeline
            k: Number of results
            expand_query: Use query expansion
            filters: Optional filters
        
        Returns:
            SearchResults object
        """
        # Expand query if requested
        queries = [query_text]
        if expand_query:
            queries.extend(self.query_expander.expand_with_stemming(query_text))
        
        # Get embeddings for all query variants
        all_results = []
        for query in queries:
            query_vector = vectorizer.encode_single(query)
            results = self.search(query_vector, k=k, filters=filters)
            all_results.extend(results.results)
        
        # Deduplicate and re-rank
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result.entity_type, result.entity_id)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Sort by score
        unique_results.sort(key=lambda x: x.score, reverse=True)
        unique_results = unique_results[:k]
        
        # Update ranks
        for rank, result in enumerate(unique_results, 1):
            result.rank = rank
        
        return SearchResults(
            results=unique_results,
            query=query_text,
            total_results=len(unique_results),
            search_time=0.0,  # Already calculated
            algorithm=f"{self.backend}_with_expansion" if expand_query else self.backend,
            filters_applied=filters or {}
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'backend': self.backend,
            'metric': self.metric,
            'dimension': self.dimension,
            'total_vectors': len(self.entity_map),
            'is_trained': self.is_trained,
            'use_gpu': self.use_gpu
        }
