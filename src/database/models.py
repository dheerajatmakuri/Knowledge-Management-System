"""
Database models for knowledge management system.
Professional schema design with indexing and optimization.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class Profile(Base):
    """Profile model for storing individual profile information."""
    
    __tablename__ = 'profiles'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core profile information
    name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), index=True)
    bio = Column(Text)
    
    # Contact information
    email = Column(String(255), index=True)
    phone = Column(String(50))
    linkedin = Column(String(500))
    twitter = Column(String(255))
    website = Column(String(500))
    
    # Source information
    source_url = Column(String(1000), nullable=False, unique=True)
    source_domain = Column(String(255), index=True)
    
    # Media
    photo_url = Column(String(1000))
    photo_local_path = Column(String(500))
    
    # Metadata
    raw_html = Column(Text)
    extraction_method = Column(String(100))
    confidence_score = Column(Float, default=0.0)
    
    # Additional structured data
    additional_data = Column(JSON)  # Flexible JSON field for additional data (renamed from metadata)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # Status tracking
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    scrape_status = Column(String(50), default='pending', index=True)  # pending, completed, failed
    
    # Relationships
    contents = relationship("Content", back_populates="profile", cascade="all, delete-orphan")
    categories = relationship("ProfileCategory", back_populates="profile", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_profile_name_title', 'name', 'title'),
        Index('idx_profile_domain_status', 'source_domain', 'scrape_status'),
        Index('idx_profile_active_created', 'is_active', 'created_at'),
    )
    
    @hybrid_property
    def full_contact(self):
        """Returns formatted contact information."""
        contacts = []
        if self.email:
            contacts.append(f"Email: {self.email}")
        if self.phone:
            contacts.append(f"Phone: {self.phone}")
        if self.linkedin:
            contacts.append(f"LinkedIn: {self.linkedin}")
        return " | ".join(contacts)
    
    def __repr__(self):
        return f"<Profile(id={self.id}, name='{self.name}', title='{self.title}')>"


class Content(Base):
    """Content model for storing additional content related to profiles."""
    
    __tablename__ = 'contents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Content information
    title = Column(String(500), nullable=False, index=True)
    content_type = Column(String(50), index=True)  # article, blog, news, etc.
    body = Column(Text, nullable=False)
    summary = Column(Text)
    
    # Source
    url = Column(String(1000), unique=True, nullable=False)
    domain = Column(String(255), index=True)
    
    # Author/Profile relationship
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    author_name = Column(String(255), index=True)
    
    # Media
    featured_image = Column(String(1000))
    
    # Metadata
    tags = Column(JSON)  # List of tags
    extra_metadata = Column(JSON)  # Additional structured data (renamed from metadata)
    
    # Timestamps
    published_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    profile = relationship("Profile", back_populates="contents")
    
    __table_args__ = (
        Index('idx_content_type_published', 'content_type', 'published_at'),
        Index('idx_content_profile_active', 'profile_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title[:50]}...', type='{self.content_type}')>"


class Category(Base):
    """Category model for organizing profiles and content."""
    
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Hierarchy support
    parent_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    
    # Metadata
    color = Column(String(20))  # For UI visualization
    icon = Column(String(50))
    
    # Keywords for auto-categorization
    keywords = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    profiles = relationship("ProfileCategory", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class ProfileCategory(Base):
    """Association table for many-to-many relationship between profiles and categories."""
    
    __tablename__ = 'profile_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    
    # Confidence score for auto-categorization
    confidence = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="categories")
    category = relationship("Category", back_populates="profiles")
    
    __table_args__ = (
        UniqueConstraint('profile_id', 'category_id', name='uq_profile_category'),
        Index('idx_profile_category', 'profile_id', 'category_id'),
    )
    
    def __repr__(self):
        return f"<ProfileCategory(profile_id={self.profile_id}, category_id={self.category_id})>"


class SearchIndex(Base):
    """Search index for full-text search optimization."""
    
    __tablename__ = 'search_index'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to source
    entity_type = Column(String(50), nullable=False, index=True)  # profile, content
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Search content
    search_text = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_search_entity', 'entity_type', 'entity_id'),
        UniqueConstraint('entity_type', 'entity_id', name='uq_search_entity'),
    )
    
    def __repr__(self):
        return f"<SearchIndex(entity_type='{self.entity_type}', entity_id={self.entity_id})>"


class ScrapeLog(Base):
    """Log table for tracking scraping activities."""
    
    __tablename__ = 'scrape_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Scrape information
    url = Column(String(1000), nullable=False, index=True)
    scrape_type = Column(String(50), index=True)  # discovery, profile, content
    status = Column(String(50), nullable=False, index=True)  # success, failed, skipped
    
    # Results
    profiles_found = Column(Integer, default=0)
    profiles_extracted = Column(Integer, default=0)
    errors = Column(JSON)
    
    # Performance metrics
    duration_seconds = Column(Float)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_scrape_status_started', 'status', 'started_at'),
    )
    
    def __repr__(self):
        return f"<ScrapeLog(id={self.id}, url='{self.url}', status='{self.status}')>"


class KnowledgeSnippet(Base):
    """Knowledge snippets extracted from discovered content."""
    
    __tablename__ = 'knowledge_snippets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core information
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    
    # Source
    url = Column(String(1000), unique=True, nullable=False)
    domain = Column(String(255), index=True)
    
    # Classification
    content_type = Column(String(50), index=True)  # article, blog, documentation, profile, etc.
    category = Column(String(100), index=True)  # Technical, Business, Leadership, etc.
    
    # Keywords and tags
    keywords = Column(JSON)  # List of extracted keywords
    tags = Column(JSON)  # User-defined or auto-generated tags
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0, index=True)
    relevance_score = Column(Float, default=0.0)
    word_count = Column(Integer)
    
    # Relationships
    related_urls = Column(JSON)  # List of related URLs
    parent_snippet_id = Column(Integer, ForeignKey('knowledge_snippets.id', ondelete='SET NULL'))
    
    # Metadata
    snippet_metadata = Column(JSON)  # Additional structured data (renamed from metadata)
    extraction_method = Column(String(100))
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_validated = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False, index=True)
    
    # Relationships
    parent = relationship("KnowledgeSnippet", remote_side=[id], backref="children")
    
    __table_args__ = (
        Index('idx_snippet_type_category', 'content_type', 'category'),
        Index('idx_snippet_confidence', 'confidence_score', 'is_validated'),
        Index('idx_snippet_domain_type', 'domain', 'content_type'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_range'),
    )
    
    def __repr__(self):
        return f"<KnowledgeSnippet(id={self.id}, title='{self.title[:50]}...', type='{self.content_type}')>"


class KnowledgeRelationship(Base):
    """Relationships between knowledge entities for graph building."""
    
    __tablename__ = 'knowledge_relationships'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source entity
    source_type = Column(String(50), nullable=False, index=True)  # snippet, profile, content
    source_id = Column(Integer, nullable=False, index=True)
    
    # Target entity
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    
    # Relationship type
    relationship_type = Column(String(50), nullable=False, index=True)  # links_to, references, authored_by, etc.
    
    # Relationship strength
    strength = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Metadata
    relationship_metadata = Column(JSON)  # Additional structured data (renamed from metadata)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_relationship_source', 'source_type', 'source_id'),
        Index('idx_relationship_target', 'target_type', 'target_id'),
        Index('idx_relationship_type_strength', 'relationship_type', 'strength'),
        UniqueConstraint('source_type', 'source_id', 'target_type', 'target_id', 'relationship_type', 
                        name='uq_relationship'),
    )
    
    def __repr__(self):
        return f"<KnowledgeRelationship({self.source_type}:{self.source_id} -> {self.target_type}:{self.target_id})>"


class EmbeddingVector(Base):
    """Store embedding vectors for semantic search."""
    
    __tablename__ = 'embedding_vectors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to source
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Vector data (stored as JSON for SQLite compatibility)
    vector = Column(JSON, nullable=False)
    vector_dimension = Column(Integer, nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    
    # Vector metadata for optimization
    norm = Column(Float)  # L2 norm for normalization
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_embedding_entity', 'entity_type', 'entity_id'),
        Index('idx_embedding_model', 'model_name', 'created_at'),
        UniqueConstraint('entity_type', 'entity_id', 'model_name', name='uq_embedding_entity_model'),
    )
    
    def __repr__(self):
        return f"<EmbeddingVector(entity_type='{self.entity_type}', entity_id={self.entity_id})>"


class SearchCache(Base):
    """Cache for frequently searched queries to improve performance."""
    
    __tablename__ = 'search_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query information
    query_text = Column(String(500), nullable=False, unique=True, index=True)
    query_hash = Column(String(64), unique=True, index=True)  # MD5/SHA hash of query
    
    # Search type
    search_type = Column(String(50), index=True)  # fulltext, semantic, hybrid
    
    # Cached results (JSON array of result IDs)
    result_ids = Column(JSON, nullable=False)
    result_count = Column(Integer, default=0)
    
    # Cache metadata
    hit_count = Column(Integer, default=0)  # Number of times this cache was used
    last_hit = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, index=True)
    
    __table_args__ = (
        Index('idx_cache_type_expires', 'search_type', 'expires_at'),
        Index('idx_cache_hits', 'hit_count', 'last_hit'),
    )
    
    def __repr__(self):
        return f"<SearchCache(query='{self.query_text[:50]}...', hits={self.hit_count})>"
