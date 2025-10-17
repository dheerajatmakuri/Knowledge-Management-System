"""
Vector embedding generation and management.
Supports both OpenAI embeddings and sentence transformers.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
import numpy as np
from dataclasses import dataclass
import os
from loguru import logger

# Sentence Transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available")

# OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not available")


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""
    provider: str = 'sentence-transformers'  # 'sentence-transformers' or 'openai'
    model_name: str = 'all-MiniLM-L6-v2'
    dimension: int = 384
    normalize: bool = True
    batch_size: int = 32
    device: str = 'cpu'  # 'cpu' or 'cuda'


class ContentVectorizationPipeline:
    """Pipeline for vectorizing content using embeddings."""
    
    def __init__(self, config: EmbeddingConfig = None):
        """
        Initialize vectorization pipeline.
        
        Args:
            config: Embedding configuration
        """
        self.config = config or EmbeddingConfig()
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model based on provider."""
        if self.config.provider == 'sentence-transformers':
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
            
            logger.info(f"Loading sentence-transformers model: {self.config.model_name}")
            self.model = SentenceTransformer(self.config.model_name, device=self.config.device)
            self.config.dimension = self.model.get_sentence_embedding_dimension()
            logger.success(f"Model loaded. Embedding dimension: {self.config.dimension}")
        
        elif self.config.provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("openai not installed. Run: pip install openai")
            
            # Set API key from environment
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            # Set dimensions based on model
            if self.config.model_name == 'text-embedding-3-small':
                self.config.dimension = 1536
            elif self.config.model_name == 'text-embedding-3-large':
                self.config.dimension = 3072
            elif self.config.model_name == 'text-embedding-ada-002':
                self.config.dimension = 1536
            
            logger.success(f"OpenAI embeddings initialized: {self.config.model_name}")
        
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")
    
    def encode(self, texts: Union[str, List[str]], show_progress: bool = False) -> np.ndarray:
        """
        Encode text(s) to embeddings.
        
        Args:
            texts: Single text or list of texts
            show_progress: Show progress bar
        
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self.config.provider == 'sentence-transformers':
            embeddings = self.model.encode(
                texts,
                batch_size=self.config.batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=self.config.normalize
            )
        
        elif self.config.provider == 'openai':
            embeddings = self._encode_openai(texts)
        
        return embeddings
    
    def _encode_openai(self, texts: List[str]) -> np.ndarray:
        """Encode using OpenAI API."""
        if not texts:
            return np.array([]).reshape(0, self.config.dimension)
        
        embeddings = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            
            try:
                response = openai.embeddings.create(
                    model=self.config.model_name,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                # Return zero vectors on error
                embeddings.extend([np.zeros(self.config.dimension) for _ in batch])
        
        embeddings_array = np.array(embeddings)
        
        if self.config.normalize and len(embeddings_array) > 0:
            embeddings_array = self._normalize_embeddings(embeddings_array)
        
        return embeddings_array
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode(text)[0]
    
    def encode_batch(self, texts: List[str], batch_size: int = None) -> np.ndarray:
        """
        Encode texts in batches.
        
        Args:
            texts: List of texts
            batch_size: Batch size (overrides config)
        
        Returns:
            Array of embeddings
        """
        original_batch_size = self.config.batch_size
        if batch_size:
            self.config.batch_size = batch_size
        
        embeddings = self.encode(texts, show_progress=True)
        
        self.config.batch_size = original_batch_size
        return embeddings
    
    @staticmethod
    def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length."""
        if embeddings.ndim == 1:
            # Single embedding
            norm = np.linalg.norm(embeddings)
            return embeddings / (norm if norm != 0 else 1)
        else:
            # Multiple embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            return embeddings / norms
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            'provider': self.config.provider,
            'model_name': self.config.model_name,
            'dimension': self.config.dimension,
            'device': self.config.device,
            'normalize': self.config.normalize,
            'batch_size': self.config.batch_size
        }


class EmbeddingIndexer:
    """
    Indexes content for semantic search.
    Manages embedding generation and storage.
    """
    
    def __init__(self, vectorizer: ContentVectorizationPipeline, db_session):
        """
        Initialize indexer.
        
        Args:
            vectorizer: Content vectorization pipeline
            db_session: Database session manager
        """
        self.vectorizer = vectorizer
        self.db_session = db_session
    
    def index_profiles(self, profile_ids: List[int] = None, batch_size: int = 32) -> Dict[str, Any]:
        """
        Index profiles for semantic search.
        
        Args:
            profile_ids: Specific profile IDs to index (None for all)
            batch_size: Batch size for processing
        
        Returns:
            Statistics about indexing
        """
        from ..database.repository import ProfileRepository, EmbeddingVectorRepository
        
        with self.db_session.get_session() as session:
            profile_repo = ProfileRepository(session)
            embedding_repo = EmbeddingVectorRepository(session)
            
            # Get profiles to index
            if profile_ids:
                profiles = [profile_repo.get_by_id(pid) for pid in profile_ids]
                profiles = [p for p in profiles if p]
            else:
                profiles = profile_repo.get_all()
            
            logger.info(f"Indexing {len(profiles)} profiles...")
            
            # Prepare texts for embedding
            texts = []
            profile_map = []
            
            for profile in profiles:
                # Combine profile information for embedding
                text_parts = [profile.name]
                if profile.title:
                    text_parts.append(profile.title)
                if profile.bio:
                    text_parts.append(profile.bio[:500])  # Limit bio length
                
                text = " | ".join(text_parts)
                texts.append(text)
                profile_map.append(profile.id)
            
            # Generate embeddings
            embeddings = self.vectorizer.encode_batch(texts, batch_size=batch_size)
            
            # Store embeddings
            indexed_count = 0
            for profile_id, embedding in zip(profile_map, embeddings):
                embedding_vector = embedding.tolist()
                
                result = embedding_repo.create_embedding(
                    entity_type='profile',
                    entity_id=profile_id,
                    vector=embedding_vector,
                    model_name=self.vectorizer.config.model_name,
                    model_version='1.0',
                    norm=float(np.linalg.norm(embedding))
                )
                
                if result:
                    indexed_count += 1
            
            session.commit()
            
            logger.success(f"Indexed {indexed_count} profiles")
            
            return {
                'total_profiles': len(profiles),
                'indexed': indexed_count,
                'model': self.vectorizer.config.model_name,
                'dimension': self.vectorizer.config.dimension
            }
    
    def index_snippets(self, snippet_ids: List[int] = None, batch_size: int = 32) -> Dict[str, Any]:
        """
        Index knowledge snippets for semantic search.
        
        Args:
            snippet_ids: Specific snippet IDs to index (None for all)
            batch_size: Batch size for processing
        
        Returns:
            Statistics about indexing
        """
        from ..database.repository import KnowledgeSnippetRepository, EmbeddingVectorRepository
        
        with self.db_session.get_session() as session:
            snippet_repo = KnowledgeSnippetRepository(session)
            embedding_repo = EmbeddingVectorRepository(session)
            
            # Get snippets to index
            if snippet_ids:
                snippets = [snippet_repo.get_by_id(sid) for sid in snippet_ids]
                snippets = [s for s in snippets if s]
            else:
                snippets = snippet_repo.get_all()
            
            logger.info(f"Indexing {len(snippets)} knowledge snippets...")
            
            # Prepare texts
            texts = []
            snippet_map = []
            
            for snippet in snippets:
                # Combine title and content
                text = f"{snippet.title} | {snippet.content[:1000]}"
                texts.append(text)
                snippet_map.append(snippet.id)
            
            # Generate embeddings
            embeddings = self.vectorizer.encode_batch(texts, batch_size=batch_size)
            
            # Store embeddings
            indexed_count = 0
            for snippet_id, embedding in zip(snippet_map, embeddings):
                embedding_vector = embedding.tolist()
                
                result = embedding_repo.create_embedding(
                    entity_type='snippet',
                    entity_id=snippet_id,
                    vector=embedding_vector,
                    model_name=self.vectorizer.config.model_name,
                    model_version='1.0',
                    norm=float(np.linalg.norm(embedding))
                )
                
                if result:
                    indexed_count += 1
                    
                    # Update snippet indexed status
                    snippet_repo.update(snippet_id, is_indexed=True)
            
            session.commit()
            
            logger.success(f"Indexed {indexed_count} snippets")
            
            return {
                'total_snippets': len(snippets),
                'indexed': indexed_count,
                'model': self.vectorizer.config.model_name,
                'dimension': self.vectorizer.config.dimension
            }
    
    def index_content(self, content_ids: List[int] = None, batch_size: int = 32) -> Dict[str, Any]:
        """
        Index content for semantic search.
        
        Args:
            content_ids: Specific content IDs to index (None for all)
            batch_size: Batch size for processing
        
        Returns:
            Statistics about indexing
        """
        from ..database.repository import ContentRepository, EmbeddingVectorRepository
        
        with self.db_session.get_session() as session:
            content_repo = ContentRepository(session)
            embedding_repo = EmbeddingVectorRepository(session)
            
            # Get content to index
            if content_ids:
                contents = [content_repo.get_by_id(cid) for cid in content_ids]
                contents = [c for c in contents if c]
            else:
                contents = content_repo.get_all()
            
            logger.info(f"Indexing {len(contents)} content items...")
            
            # Prepare texts
            texts = []
            content_map = []
            
            for content in contents:
                # Combine title and body
                text = f"{content.title} | {content.body[:1000]}"
                if content.summary:
                    text = f"{text} | {content.summary}"
                texts.append(text)
                content_map.append(content.id)
            
            # Generate embeddings
            embeddings = self.vectorizer.encode_batch(texts, batch_size=batch_size)
            
            # Store embeddings
            indexed_count = 0
            for content_id, embedding in zip(content_map, embeddings):
                embedding_vector = embedding.tolist()
                
                result = embedding_repo.create_embedding(
                    entity_type='content',
                    entity_id=content_id,
                    vector=embedding_vector,
                    model_name=self.vectorizer.config.model_name,
                    model_version='1.0',
                    norm=float(np.linalg.norm(embedding))
                )
                
                if result:
                    indexed_count += 1
            
            session.commit()
            
            logger.success(f"Indexed {indexed_count} content items")
            
            return {
                'total_content': len(contents),
                'indexed': indexed_count,
                'model': self.vectorizer.config.model_name,
                'dimension': self.vectorizer.config.dimension
            }
    
    def index_all(self, batch_size: int = 32) -> Dict[str, Any]:
        """
        Index all content types.
        
        Args:
            batch_size: Batch size for processing
        
        Returns:
            Combined statistics
        """
        logger.info("Starting full index...")
        
        profile_stats = self.index_profiles(batch_size=batch_size)
        snippet_stats = self.index_snippets(batch_size=batch_size)
        content_stats = self.index_content(batch_size=batch_size)
        
        return {
            'profiles': profile_stats,
            'snippets': snippet_stats,
            'content': content_stats,
            'total_indexed': (
                profile_stats['indexed'] + 
                snippet_stats['indexed'] + 
                content_stats['indexed']
            )
        }
    
    def reindex_entity(self, entity_type: str, entity_id: int) -> bool:
        """
        Reindex a single entity.
        
        Args:
            entity_type: Type of entity ('profile', 'snippet', 'content')
            entity_id: Entity ID
        
        Returns:
            True if successful
        """
        if entity_type == 'profile':
            return self.index_profiles([entity_id])['indexed'] > 0
        elif entity_type == 'snippet':
            return self.index_snippets([entity_id])['indexed'] > 0
        elif entity_type == 'content':
            return self.index_content([entity_id])['indexed'] > 0
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        from ..database.repository import EmbeddingVectorRepository
        
        with self.db_session.get_session() as session:
            embedding_repo = EmbeddingVectorRepository(session)
            
            # Count embeddings by type
            all_embeddings = embedding_repo.get_all()
            
            stats = {
                'total_embeddings': len(all_embeddings),
                'by_entity_type': {},
                'by_model': {},
                'model_info': self.vectorizer.get_model_info()
            }
            
            for emb in all_embeddings:
                # Count by entity type
                stats['by_entity_type'][emb.entity_type] = \
                    stats['by_entity_type'].get(emb.entity_type, 0) + 1
                
                # Count by model
                stats['by_model'][emb.model_name] = \
                    stats['by_model'].get(emb.model_name, 0) + 1
            
            return stats
