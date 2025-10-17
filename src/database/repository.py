"""
Repository pattern for database operations.
Provides clean abstraction layer for data access.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, or_, and_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
import os
from loguru import logger

from .models import (
    Base, Profile, Content, Category, ProfileCategory,
    SearchIndex, ScrapeLog, EmbeddingVector,
    KnowledgeSnippet, KnowledgeRelationship, SearchCache
)


class DatabaseSession:
    """Database session manager."""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv('DATABASE_PATH', 'sqlite:///data/profiles.db')
            if not database_url.startswith('sqlite:///'):
                database_url = f'sqlite:///{database_url}'
        
        self.engine = create_engine(
            database_url,
            echo=os.getenv('DATABASE_ECHO', 'false').lower() == 'true',
            connect_args={'check_same_thread': False} if 'sqlite' in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class
    
    def create(self, **kwargs) -> Any:
        """Create a new record."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance
    
    def get_by_id(self, id: int) -> Optional[Any]:
        """Get record by ID."""
        return self.session.query(self.model_class).filter_by(id=id).first()
    
    def get_all(self, limit: int = None, offset: int = 0) -> List[Any]:
        """Get all records with pagination."""
        query = self.session.query(self.model_class)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[Any]:
        """Update a record."""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.session.flush()
        return instance
    
    def delete(self, id: int) -> bool:
        """Delete a record."""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.flush()
            return True
        return False
    
    def count(self) -> int:
        """Count total records."""
        return self.session.query(func.count(self.model_class.id)).scalar()


class ProfileRepository(BaseRepository):
    """Repository for Profile operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Profile)
    
    def create_profile(self, name: str, source_url: str, **kwargs) -> Optional[Profile]:
        """Create a new profile with duplicate checking."""
        try:
            # Check if profile already exists
            existing = self.get_by_url(source_url)
            if existing:
                logger.info(f"Profile already exists: {source_url}")
                return existing
            
            # Extract domain from URL
            from urllib.parse import urlparse
            domain = urlparse(source_url).netloc
            
            profile = Profile(
                name=name,
                source_url=source_url,
                source_domain=domain,
                **kwargs
            )
            self.session.add(profile)
            self.session.flush()
            logger.info(f"Created profile: {name} ({source_url})")
            return profile
            
        except IntegrityError as e:
            self.session.rollback()
            logger.warning(f"Duplicate profile detected: {source_url}")
            return self.get_by_url(source_url)
    
    def get_by_url(self, url: str) -> Optional[Profile]:
        """Get profile by source URL."""
        return self.session.query(Profile).filter_by(source_url=url).first()
    
    def get_by_name(self, name: str, exact: bool = False) -> List[Profile]:
        """Get profiles by name."""
        if exact:
            return self.session.query(Profile).filter_by(name=name).all()
        else:
            return self.session.query(Profile).filter(
                Profile.name.ilike(f'%{name}%')
            ).all()
    
    def get_by_domain(self, domain: str) -> List[Profile]:
        """Get all profiles from a specific domain."""
        return self.session.query(Profile).filter_by(source_domain=domain).all()
    
    def search(self, query: str, limit: int = 20) -> List[Profile]:
        """Search profiles by name, title, or bio."""
        search_term = f'%{query}%'
        return self.session.query(Profile).filter(
            or_(
                Profile.name.ilike(search_term),
                Profile.title.ilike(search_term),
                Profile.bio.ilike(search_term),
                Profile.email.ilike(search_term)
            )
        ).limit(limit).all()
    
    def get_active_profiles(self, limit: int = None) -> List[Profile]:
        """Get all active profiles."""
        query = self.session.query(Profile).filter_by(is_active=True)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_recent_profiles(self, days: int = 7, limit: int = 20) -> List[Profile]:
        """Get recently created profiles."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Profile).filter(
            Profile.created_at >= cutoff_date
        ).order_by(Profile.created_at.desc()).limit(limit).all()
    
    def update_profile(self, profile_id: int, **kwargs) -> Optional[Profile]:
        """Update profile with merge logic for duplicate detection."""
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        
        # Update timestamp
        kwargs['updated_at'] = datetime.utcnow()
        
        for key, value in kwargs.items():
            if value is not None:  # Only update non-None values
                setattr(profile, key, value)
        
        self.session.flush()
        return profile
    
    def merge_profiles(self, primary_id: int, duplicate_id: int) -> Optional[Profile]:
        """Merge duplicate profiles."""
        primary = self.get_by_id(primary_id)
        duplicate = self.get_by_id(duplicate_id)
        
        if not primary or not duplicate:
            return None
        
        # Merge data - keep non-empty values from duplicate
        for field in ['title', 'bio', 'email', 'phone', 'linkedin', 'twitter', 'website']:
            if not getattr(primary, field) and getattr(duplicate, field):
                setattr(primary, field, getattr(duplicate, field))
        
        # Move relationships
        for content in duplicate.contents:
            content.profile_id = primary_id
        
        # Delete duplicate
        self.session.delete(duplicate)
        self.session.flush()
        
        logger.info(f"Merged profile {duplicate_id} into {primary_id}")
        return primary
    
    def find_duplicates(self) -> List[tuple]:
        """Find potential duplicate profiles based on name similarity."""
        profiles = self.get_all()
        duplicates = []
        
        for i, p1 in enumerate(profiles):
            for p2 in profiles[i+1:]:
                # Simple similarity check
                if self._names_similar(p1.name, p2.name):
                    duplicates.append((p1.id, p2.id, p1.name, p2.name))
        
        return duplicates
    
    @staticmethod
    def _names_similar(name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Check if two names are similar."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio() > threshold
    
    def get_profiles_needing_scrape(self, limit: int = 10) -> List[Profile]:
        """Get profiles that need to be scraped or re-scraped."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        return self.session.query(Profile).filter(
            or_(
                Profile.scrape_status == 'pending',
                Profile.scrape_status == 'failed',
                and_(
                    Profile.scrape_status == 'completed',
                    Profile.last_scraped_at < cutoff_date
                )
            )
        ).limit(limit).all()


class ContentRepository(BaseRepository):
    """Repository for Content operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Content)
    
    def create_content(self, title: str, body: str, url: str, **kwargs) -> Optional[Content]:
        """Create new content with duplicate checking."""
        try:
            # Check for existing content
            existing = self.get_by_url(url)
            if existing:
                logger.info(f"Content already exists: {url}")
                return existing
            
            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            content = Content(
                title=title,
                body=body,
                url=url,
                domain=domain,
                **kwargs
            )
            self.session.add(content)
            self.session.flush()
            logger.info(f"Created content: {title}")
            return content
            
        except IntegrityError:
            self.session.rollback()
            return self.get_by_url(url)
    
    def get_by_url(self, url: str) -> Optional[Content]:
        """Get content by URL."""
        return self.session.query(Content).filter_by(url=url).first()
    
    def get_by_profile(self, profile_id: int) -> List[Content]:
        """Get all content for a profile."""
        return self.session.query(Content).filter_by(profile_id=profile_id).all()
    
    def search(self, query: str, limit: int = 20) -> List[Content]:
        """Search content."""
        search_term = f'%{query}%'
        return self.session.query(Content).filter(
            or_(
                Content.title.ilike(search_term),
                Content.body.ilike(search_term),
                Content.summary.ilike(search_term)
            )
        ).limit(limit).all()


class CategoryRepository(BaseRepository):
    """Repository for Category operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Category)
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        return self.session.query(Category).filter_by(name=name).first()
    
    def get_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return self.session.query(Category).filter_by(slug=slug).first()
    
    def get_or_create(self, name: str, **kwargs) -> Category:
        """Get existing category or create new one."""
        category = self.get_by_name(name)
        if not category:
            slug = name.lower().replace(' ', '-')
            category = Category(name=name, slug=slug, **kwargs)
            self.session.add(category)
            self.session.flush()
        return category


class ScrapeLogRepository(BaseRepository):
    """Repository for ScrapeLog operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, ScrapeLog)
    
    def log_scrape(self, url: str, scrape_type: str, status: str, **kwargs) -> ScrapeLog:
        """Create a scrape log entry."""
        log = ScrapeLog(
            url=url,
            scrape_type=scrape_type,
            status=status,
            **kwargs
        )
        self.session.add(log)
        self.session.flush()
        return log
    
    def get_recent_logs(self, limit: int = 100) -> List[ScrapeLog]:
        """Get recent scrape logs."""
        return self.session.query(ScrapeLog).order_by(
            ScrapeLog.started_at.desc()
        ).limit(limit).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        total = self.count()
        successful = self.session.query(func.count(ScrapeLog.id)).filter_by(status='success').scalar()
        failed = self.session.query(func.count(ScrapeLog.id)).filter_by(status='failed').scalar()
        
        return {
            'total_scrapes': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }


class KnowledgeSnippetRepository(BaseRepository):
    """Repository for KnowledgeSnippet operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, KnowledgeSnippet)
    
    def create_snippet(self, title: str, content: str, url: str, **kwargs) -> Optional[KnowledgeSnippet]:
        """Create new knowledge snippet with duplicate checking."""
        try:
            existing = self.get_by_url(url)
            if existing:
                logger.info(f"Snippet already exists: {url}")
                return existing
            
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            snippet = KnowledgeSnippet(
                title=title,
                content=content,
                url=url,
                domain=domain,
                **kwargs
            )
            self.session.add(snippet)
            self.session.flush()
            logger.info(f"Created knowledge snippet: {title}")
            return snippet
            
        except IntegrityError:
            self.session.rollback()
            return self.get_by_url(url)
    
    def get_by_url(self, url: str) -> Optional[KnowledgeSnippet]:
        """Get snippet by URL."""
        return self.session.query(KnowledgeSnippet).filter_by(url=url).first()
    
    def get_by_category(self, category: str, limit: int = 50) -> List[KnowledgeSnippet]:
        """Get snippets by category."""
        return self.session.query(KnowledgeSnippet).filter_by(category=category).limit(limit).all()
    
    def get_by_content_type(self, content_type: str, limit: int = 50) -> List[KnowledgeSnippet]:
        """Get snippets by content type."""
        return self.session.query(KnowledgeSnippet).filter_by(content_type=content_type).limit(limit).all()
    
    def search(self, query: str, limit: int = 20) -> List[KnowledgeSnippet]:
        """Search snippets by title or content."""
        search_term = f'%{query}%'
        return self.session.query(KnowledgeSnippet).filter(
            or_(
                KnowledgeSnippet.title.ilike(search_term),
                KnowledgeSnippet.content.ilike(search_term),
                KnowledgeSnippet.summary.ilike(search_term)
            )
        ).limit(limit).all()
    
    def get_high_confidence(self, min_confidence: float = 0.7, limit: int = 50) -> List[KnowledgeSnippet]:
        """Get high-confidence snippets."""
        return self.session.query(KnowledgeSnippet).filter(
            KnowledgeSnippet.confidence_score >= min_confidence
        ).order_by(KnowledgeSnippet.confidence_score.desc()).limit(limit).all()
    
    def get_validated_snippets(self, limit: int = 50) -> List[KnowledgeSnippet]:
        """Get validated snippets."""
        return self.session.query(KnowledgeSnippet).filter_by(
            is_validated=True
        ).limit(limit).all()
    
    def get_by_domain(self, domain: str) -> List[KnowledgeSnippet]:
        """Get all snippets from a domain."""
        return self.session.query(KnowledgeSnippet).filter_by(domain=domain).all()


class KnowledgeRelationshipRepository(BaseRepository):
    """Repository for KnowledgeRelationship operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, KnowledgeRelationship)
    
    def create_relationship(
        self, 
        source_type: str, 
        source_id: int,
        target_type: str,
        target_id: int,
        relationship_type: str,
        strength: float = 1.0,
        **kwargs
    ) -> Optional[KnowledgeRelationship]:
        """Create a relationship between entities."""
        try:
            relationship = KnowledgeRelationship(
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                relationship_type=relationship_type,
                strength=strength,
                **kwargs
            )
            self.session.add(relationship)
            self.session.flush()
            return relationship
        except IntegrityError:
            self.session.rollback()
            logger.warning(f"Relationship already exists: {source_type}:{source_id} -> {target_type}:{target_id}")
            return None
    
    def get_relationships_from(
        self, 
        source_type: str, 
        source_id: int,
        relationship_type: str = None
    ) -> List[KnowledgeRelationship]:
        """Get all relationships from a source entity."""
        query = self.session.query(KnowledgeRelationship).filter_by(
            source_type=source_type,
            source_id=source_id
        )
        if relationship_type:
            query = query.filter_by(relationship_type=relationship_type)
        return query.all()
    
    def get_relationships_to(
        self, 
        target_type: str, 
        target_id: int,
        relationship_type: str = None
    ) -> List[KnowledgeRelationship]:
        """Get all relationships to a target entity."""
        query = self.session.query(KnowledgeRelationship).filter_by(
            target_type=target_type,
            target_id=target_id
        )
        if relationship_type:
            query = query.filter_by(relationship_type=relationship_type)
        return query.all()
    
    def get_related_entities(
        self,
        entity_type: str,
        entity_id: int,
        max_depth: int = 2
    ) -> List[tuple]:
        """Get related entities up to max_depth levels."""
        # BFS traversal of relationships
        visited = set()
        queue = [(entity_type, entity_id, 0)]
        related = []
        
        while queue:
            curr_type, curr_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            if (curr_type, curr_id) in visited:
                continue
            
            visited.add((curr_type, curr_id))
            
            # Get outgoing relationships
            relationships = self.get_relationships_from(curr_type, curr_id)
            for rel in relationships:
                target = (rel.target_type, rel.target_id)
                if target not in visited:
                    related.append((target[0], target[1], rel.relationship_type, depth + 1))
                    queue.append((target[0], target[1], depth + 1))
        
        return related


class EmbeddingVectorRepository(BaseRepository):
    """Repository for EmbeddingVector operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, EmbeddingVector)
    
    def create_embedding(
        self,
        entity_type: str,
        entity_id: int,
        vector: List[float],
        model_name: str,
        **kwargs
    ) -> Optional[EmbeddingVector]:
        """Create or update embedding vector."""
        try:
            # Check for existing embedding
            existing = self.session.query(EmbeddingVector).filter_by(
                entity_type=entity_type,
                entity_id=entity_id,
                model_name=model_name
            ).first()
            
            if existing:
                # Update existing
                existing.vector = vector
                existing.vector_dimension = len(vector)
                existing.updated_at = datetime.utcnow()
                if 'norm' in kwargs:
                    existing.norm = kwargs['norm']
                self.session.flush()
                return existing
            
            # Create new
            import numpy as np
            norm = kwargs.get('norm') or float(np.linalg.norm(vector))
            
            embedding = EmbeddingVector(
                entity_type=entity_type,
                entity_id=entity_id,
                vector=vector,
                vector_dimension=len(vector),
                model_name=model_name,
                norm=norm,
                **{k: v for k, v in kwargs.items() if k != 'norm'}
            )
            self.session.add(embedding)
            self.session.flush()
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            self.session.rollback()
            return None
    
    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        model_name: str = None
    ) -> Optional[EmbeddingVector]:
        """Get embedding for an entity."""
        query = self.session.query(EmbeddingVector).filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        )
        if model_name:
            query = query.filter_by(model_name=model_name)
        return query.first()
    
    def get_by_model(self, model_name: str, limit: int = None) -> List[EmbeddingVector]:
        """Get all embeddings for a model."""
        query = self.session.query(EmbeddingVector).filter_by(model_name=model_name)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def batch_get_embeddings(
        self,
        entity_ids: List[int],
        entity_type: str,
        model_name: str
    ) -> List[EmbeddingVector]:
        """Get multiple embeddings at once."""
        return self.session.query(EmbeddingVector).filter(
            EmbeddingVector.entity_type == entity_type,
            EmbeddingVector.entity_id.in_(entity_ids),
            EmbeddingVector.model_name == model_name
        ).all()


class SearchCacheRepository(BaseRepository):
    """Repository for SearchCache operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, SearchCache)
    
    def get_cached_results(self, query_text: str, search_type: str = 'fulltext') -> Optional[SearchCache]:
        """Get cached search results."""
        import hashlib
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        
        cache = self.session.query(SearchCache).filter_by(
            query_hash=query_hash,
            search_type=search_type
        ).filter(
            SearchCache.expires_at > datetime.utcnow()
        ).first()
        
        if cache:
            # Update hit count
            cache.hit_count += 1
            cache.last_hit = datetime.utcnow()
            self.session.flush()
        
        return cache
    
    def cache_results(
        self,
        query_text: str,
        result_ids: List[int],
        search_type: str = 'fulltext',
        ttl_hours: int = 24
    ) -> SearchCache:
        """Cache search results."""
        import hashlib
        from datetime import timedelta
        
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        cache = SearchCache(
            query_text=query_text,
            query_hash=query_hash,
            search_type=search_type,
            result_ids=result_ids,
            result_count=len(result_ids),
            expires_at=expires_at
        )
        self.session.add(cache)
        self.session.flush()
        return cache
    
    def clear_expired(self) -> int:
        """Clear expired cache entries."""
        count = self.session.query(SearchCache).filter(
            SearchCache.expires_at <= datetime.utcnow()
        ).delete()
        self.session.flush()
        return count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self.count()
        total_hits = self.session.query(func.sum(SearchCache.hit_count)).scalar() or 0
        avg_hits = self.session.query(func.avg(SearchCache.hit_count)).scalar() or 0
        
        return {
            'total_cached_queries': total,
            'total_hits': int(total_hits),
            'average_hits_per_query': float(avg_hits),
            'cache_hit_rate': (total_hits / total) if total > 0 else 0
        }
