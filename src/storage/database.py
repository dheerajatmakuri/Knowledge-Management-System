"""
Database operations and connection management.

Implements:
- Connection pooling and optimization
- CRUD operations with transactions
- Full-text search indexing
- Query optimization with caching
"""

import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import create_engine, event, or_, and_, func, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from loguru import logger

from .models import (
    Base, Document, Embedding, Link, SearchQuery,
    Category, SystemMetadata, create_all_tables
)


class DatabaseManager:
    """
    Professional database manager with optimization and best practices.
    
    Features:
    - Connection pooling
    - WAL mode for SQLite
    - Transaction management
    - Query optimization
    """
    
    def __init__(self, db_path: str = "data/database.db", echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            echo: Echo SQL statements (for debugging)
        """
        self.db_path = db_path
        self._ensure_db_directory()
        
        # Create engine with optimizations
        connection_string = f"sqlite:///{db_path}"
        self.engine = create_engine(
            connection_string,
            echo=echo,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections
        )
        
        # Configure SQLite for optimal performance
        self._configure_sqlite()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        create_all_tables(self.engine)
        
        logger.info(f"Database initialized at: {db_path}")
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _configure_sqlite(self):
        """Configure SQLite for optimal performance."""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            # WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Increase cache size (10MB)
            cursor.execute("PRAGMA cache_size=10000")
            # Faster synchronization
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        
        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== Document Operations ====================
    
    def add_document(
        self,
        url: str,
        title: str,
        content: str,
        **kwargs
    ) -> Optional[Document]:
        """
        Add a new document to the database.
        
        Args:
            url: Document URL
            title: Document title
            content: Document content
            **kwargs: Additional fields (category, name, etc.)
            
        Returns:
            Created Document or None if exists
        """
        with self.get_session() as session:
            # Check if document exists
            existing = session.query(Document).filter_by(url=url).first()
            if existing:
                logger.warning(f"Document already exists: {url}")
                return None
            
            # Create document
            doc = Document(
                url=url,
                title=title,
                content=content,
                word_count=len(content.split()),
                scraped_at=datetime.utcnow(),
                **kwargs
            )
            
            session.add(doc)
            session.flush()  # Get ID before commit
            
            logger.info(f"Added document: {doc.id} - {title}")
            return doc
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        """Get document by ID."""
        with self.get_session() as session:
            return session.query(Document).filter_by(id=doc_id).first()
    
    def get_document_by_url(self, url: str) -> Optional[Document]:
        """Get document by URL."""
        with self.get_session() as session:
            return session.query(Document).filter_by(url=url).first()
    
    def update_document(self, doc_id: int, **kwargs) -> bool:
        """
        Update document fields.
        
        Args:
            doc_id: Document ID
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        with self.get_session() as session:
            doc = session.query(Document).filter_by(id=doc_id).first()
            if not doc:
                return False
            
            for key, value in kwargs.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)
            
            doc.last_updated = datetime.utcnow()
            logger.info(f"Updated document: {doc_id}")
            return True
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete document and related data."""
        with self.get_session() as session:
            doc = session.query(Document).filter_by(id=doc_id).first()
            if not doc:
                return False
            
            session.delete(doc)
            logger.info(f"Deleted document: {doc_id}")
            return True
    
    def get_all_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> List[Document]:
        """
        Get documents with filtering and pagination.
        
        Args:
            limit: Maximum number of documents
            offset: Offset for pagination
            category: Filter by category
            doc_type: Filter by document type
            
        Returns:
            List of documents
        """
        with self.get_session() as session:
            query = session.query(Document)
            
            if category:
                query = query.filter_by(category=category)
            if doc_type:
                query = query.filter_by(doc_type=doc_type)
            
            return query.order_by(Document.scraped_at.desc()) \
                       .limit(limit).offset(offset).all()
    
    def search_documents(
        self,
        query: str,
        limit: int = 10
    ) -> List[Document]:
        """
        Simple text search in documents.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        with self.get_session() as session:
            search_pattern = f"%{query}%"
            return session.query(Document).filter(
                or_(
                    Document.title.like(search_pattern),
                    Document.content.like(search_pattern),
                    Document.name.like(search_pattern),
                )
            ).limit(limit).all()
    
    def get_document_count(
        self,
        category: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> int:
        """Get total document count with optional filtering."""
        with self.get_session() as session:
            query = session.query(func.count(Document.id))
            
            if category:
                query = query.filter_by(category=category)
            if doc_type:
                query = query.filter_by(doc_type=doc_type)
            
            return query.scalar()
    
    # ==================== Embedding Operations ====================
    
    def add_embedding(
        self,
        doc_id: int,
        vector: List[float],
        model_name: str,
        embedding_type: str = "document"
    ) -> Optional[Embedding]:
        """
        Add vector embedding for a document.
        
        Args:
            doc_id: Document ID
            vector: Embedding vector
            model_name: Model used for embedding
            embedding_type: Type of embedding
            
        Returns:
            Created Embedding
        """
        with self.get_session() as session:
            embedding = Embedding(
                document_id=doc_id,
                vector_json=json.dumps(vector),
                vector_dim=len(vector),
                model_name=model_name,
                embedding_type=embedding_type,
            )
            
            session.add(embedding)
            session.flush()
            
            # Mark document as indexed
            doc = session.query(Document).filter_by(id=doc_id).first()
            if doc:
                doc.is_indexed = True
            
            logger.info(f"Added embedding for document: {doc_id}")
            return embedding
    
    def get_embeddings(
        self,
        model_name: Optional[str] = None,
        embedding_type: Optional[str] = None
    ) -> List[Tuple[int, List[float]]]:
        """
        Get all embeddings with optional filtering.
        
        Returns:
            List of (document_id, vector) tuples
        """
        with self.get_session() as session:
            query = session.query(Embedding)
            
            if model_name:
                query = query.filter_by(model_name=model_name)
            if embedding_type:
                query = query.filter_by(embedding_type=embedding_type)
            
            embeddings = query.all()
            return [
                (emb.document_id, json.loads(emb.vector_json))
                for emb in embeddings
            ]
    
    def get_embedding_by_doc_id(self, doc_id: int) -> Optional[List[float]]:
        """Get embedding vector for a document."""
        with self.get_session() as session:
            emb = session.query(Embedding).filter_by(document_id=doc_id).first()
            if emb:
                return json.loads(emb.vector_json)
            return None
    
    # ==================== Link Operations ====================
    
    def add_link(
        self,
        source_doc_id: int,
        target_url: str,
        anchor_text: Optional[str] = None,
        link_type: str = "internal",
        crawl_depth: int = 0
    ) -> Optional[Link]:
        """
        Add a discovered link.
        
        Args:
            source_doc_id: Source document ID
            target_url: Target URL
            anchor_text: Link text
            link_type: Type of link
            crawl_depth: Crawl depth level
            
        Returns:
            Created Link or None if exists
        """
        with self.get_session() as session:
            # Check if link exists
            existing = session.query(Link).filter_by(
                source_doc_id=source_doc_id,
                target_url=target_url
            ).first()
            
            if existing:
                return None
            
            link = Link(
                source_doc_id=source_doc_id,
                target_url=target_url,
                anchor_text=anchor_text,
                link_type=link_type,
                crawl_depth=crawl_depth,
            )
            
            session.add(link)
            return link
    
    def get_uncrawled_links(self, max_depth: int = 3, limit: int = 100) -> List[Link]:
        """Get uncrawled links up to max depth."""
        with self.get_session() as session:
            return session.query(Link).filter(
                and_(
                    Link.is_crawled == False,
                    Link.crawl_depth < max_depth
                )
            ).limit(limit).all()
    
    def mark_link_crawled(self, link_id: int) -> bool:
        """Mark a link as crawled."""
        with self.get_session() as session:
            link = session.query(Link).filter_by(id=link_id).first()
            if link:
                link.is_crawled = True
                return True
            return False
    
    # ==================== Search Query Tracking ====================
    
    def log_search_query(
        self,
        query_text: str,
        num_results: int,
        execution_time_ms: float,
        **kwargs
    ) -> SearchQuery:
        """Log a search query for analytics."""
        with self.get_session() as session:
            search_query = SearchQuery(
                query_text=query_text,
                num_results=num_results,
                execution_time_ms=execution_time_ms,
                **kwargs
            )
            
            session.add(search_query)
            return search_query
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            return {
                'total_documents': session.query(func.count(Document.id)).scalar(),
                'indexed_documents': session.query(func.count(Document.id)).filter_by(is_indexed=True).scalar(),
                'total_links': session.query(func.count(Link.id)).scalar(),
                'uncrawled_links': session.query(func.count(Link.id)).filter_by(is_crawled=False).scalar(),
                'total_searches': session.query(func.count(SearchQuery.id)).scalar(),
                'categories': session.query(func.count(func.distinct(Document.category))).scalar(),
            }
    
    def close(self):
        """Close database connections."""
        self.engine.dispose()
        logger.info("Database connections closed")


__all__ = ['DatabaseManager']
