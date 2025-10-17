"""
Database module for data persistence and management.
"""

from .models import (
    Profile, Content, Category, SearchIndex,
    KnowledgeSnippet, KnowledgeRelationship,
    EmbeddingVector, SearchCache, ScrapeLog, ProfileCategory
)
from .repository import (
    ProfileRepository, ContentRepository, CategoryRepository,
    ScrapeLogRepository, DatabaseSession
)
from .migrations import init_database, migrate_database, backup_database

__all__ = [
    # Models
    'Profile', 
    'Content', 
    'Category', 
    'SearchIndex',
    'KnowledgeSnippet',
    'KnowledgeRelationship',
    'EmbeddingVector',
    'SearchCache',
    'ScrapeLog',
    'ProfileCategory',
    # Repositories
    'ProfileRepository', 
    'ContentRepository',
    'CategoryRepository',
    'ScrapeLogRepository',
    'DatabaseSession',
    # Operations
    'init_database',
    'migrate_database',
    'backup_database'
]
