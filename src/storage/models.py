"""
SQLAlchemy data models for the Knowledge Management System.

Demonstrates professional database design with:
- Proper relationships and foreign keys
- Indexing for query optimization
- Full-text search capabilities
- Metadata tracking
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Document(Base):
    """
    Core document model representing scraped knowledge.
    
    Optimized with:
    - Indexes on frequently queried fields
    - Full-text search capability
    - Metadata for tracking and auditing
    """
    __tablename__ = 'documents'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Content fields
    url = Column(String(2048), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    
    # Structured data (for profiles)
    name = Column(String(200))
    job_title = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))
    
    # Categorization
    category = Column(String(100), index=True)
    source_domain = Column(String(200), index=True)
    doc_type = Column(String(50), default='general', index=True)  # profile, article, general
    
    # Content hash for deduplication
    content_hash = Column(String(32), unique=True, index=True)
    
    # Metadata
    word_count = Column(Integer)
    language = Column(String(10), default='en')
    
    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status tracking
    is_processed = Column(Boolean, default=False, index=True)
    is_indexed = Column(Boolean, default=False, index=True)
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")
    links = relationship("Link", back_populates="source_document", cascade="all, delete-orphan")
    
    # Indexes for optimization
    __table_args__ = (
        Index('idx_doc_category_date', 'category', 'scraped_at'),
        Index('idx_doc_type_processed', 'doc_type', 'is_processed'),
        Index('idx_doc_domain_category', 'source_domain', 'category'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:50]}...', url='{self.url}')>"
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'name': self.name,
            'job_title': self.job_title,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'twitter_handle': self.twitter_handle,
            'category': self.category,
            'source_domain': self.source_domain,
            'doc_type': self.doc_type,
            'word_count': self.word_count,
            'language': self.language,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_processed': self.is_processed,
            'is_indexed': self.is_indexed,
        }


class Embedding(Base):
    """
    Vector embeddings for semantic search.
    
    Stores high-dimensional vector representations for similarity matching.
    """
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    
    # Embedding metadata
    model_name = Column(String(100), nullable=False)
    embedding_type = Column(String(50), default='document')  # document, title, summary
    
    # Vector stored as JSON (for SQLite compatibility)
    # In production, consider PostgreSQL with pgvector extension
    vector_json = Column(Text, nullable=False)  # JSON serialized vector
    vector_dim = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")
    
    # Indexes
    __table_args__ = (
        Index('idx_emb_doc_type', 'document_id', 'embedding_type'),
        Index('idx_emb_model', 'model_name'),
    )
    
    def __repr__(self):
        return f"<Embedding(id={self.id}, doc_id={self.document_id}, model='{self.model_name}')>"


class Link(Base):
    """
    Track discovered links for crawling and relationship mapping.
    
    Enables intelligent auto-discovery and knowledge graph construction.
    """
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source and target
    source_doc_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    target_url = Column(String(2048), nullable=False)
    
    # Link metadata
    anchor_text = Column(String(500))
    link_type = Column(String(50), default='internal')  # internal, external, social
    
    # Discovery tracking
    discovered_at = Column(DateTime, default=datetime.utcnow)
    is_crawled = Column(Boolean, default=False, index=True)
    crawl_depth = Column(Integer, default=0)
    
    # Relationships
    source_document = relationship("Document", back_populates="links")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_link_source_target', 'source_doc_id', 'target_url'),
        Index('idx_link_crawled_depth', 'is_crawled', 'crawl_depth'),
        UniqueConstraint('source_doc_id', 'target_url', name='uq_source_target'),
    )
    
    def __repr__(self):
        return f"<Link(id={self.id}, source={self.source_doc_id}, target='{self.target_url}')>"


class SearchQuery(Base):
    """
    Track search queries for analytics and improvement.
    
    Helps understand user needs and optimize search performance.
    """
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query details
    query_text = Column(String(500), nullable=False, index=True)
    query_type = Column(String(50), default='semantic')  # semantic, keyword, hybrid
    
    # Results
    num_results = Column(Integer)
    top_result_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))
    avg_similarity = Column(Float)
    
    # Performance metrics
    execution_time_ms = Column(Float)
    
    # Scope checking
    is_in_scope = Column(Boolean, default=True)
    scope_confidence = Column(Float)
    
    # Timestamp
    queried_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_query_date_type', 'queried_at', 'query_type'),
        Index('idx_query_scope', 'is_in_scope', 'scope_confidence'),
    )
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query='{self.query_text}', results={self.num_results})>"


class Category(Base):
    """
    Predefined categories for document classification.
    """
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    
    # Hierarchy support
    children = relationship("Category", backref="parent", remote_side=[id])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class SystemMetadata(Base):
    """
    Store system-level metadata and statistics.
    
    Tracks overall system health and usage patterns.
    """
    __tablename__ = 'system_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String(20), default='string')  # string, int, float, json
    description = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemMetadata(key='{self.key}', value='{self.value}')>"


# Create all tables function
def create_all_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all tables from the database."""
    Base.metadata.drop_all(engine)


__all__ = [
    'Base',
    'Document',
    'Embedding',
    'Link',
    'SearchQuery',
    'Category',
    'SystemMetadata',
    'create_all_tables',
    'drop_all_tables',
]
