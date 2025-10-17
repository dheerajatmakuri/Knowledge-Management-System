"""
Database migrations and initialization.
"""

import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from loguru import logger

from .models import Base, Category
from .repository import DatabaseSession


def init_database(database_url: str = None, force: bool = False) -> bool:
    """
    Initialize the database with tables and default data.
    
    Args:
        database_url: Database connection string
        force: If True, drop existing tables
    
    Returns:
        bool: True if successful
    """
    try:
        if database_url is None:
            database_url = os.getenv('DATABASE_PATH', 'data/profiles.db')
            if not database_url.startswith('sqlite:///'):
                database_url = f'sqlite:///{database_url}'
        
        # Create directory if it doesn't exist
        if 'sqlite:///' in database_url:
            db_path = database_url.replace('sqlite:///', '')
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        if force:
            logger.warning("Dropping existing tables...")
            Base.metadata.drop_all(engine)
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        
        # Enable WAL mode for SQLite (better concurrency)
        if 'sqlite' in database_url:
            with engine.connect() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA synchronous=NORMAL"))
                conn.execute(text("PRAGMA cache_size=10000"))
                conn.execute(text("PRAGMA temp_store=MEMORY"))
                conn.commit()
                logger.info("SQLite optimizations applied")
        
        # Insert default data
        _insert_default_categories(engine)
        
        logger.success(f"Database initialized successfully at {database_url}")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def _insert_default_categories(engine):
    """Insert default categories."""
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        default_categories = [
            {
                'name': 'Leadership',
                'slug': 'leadership',
                'description': 'Executive leadership and management',
                'color': '#FF6B6B',
                'icon': '👔',
                'keywords': ['ceo', 'cto', 'cfo', 'president', 'director', 'executive', 'chief', 'vp', 'vice president']
            },
            {
                'name': 'Technology',
                'slug': 'technology',
                'description': 'Technology and engineering professionals',
                'color': '#4ECDC4',
                'icon': '💻',
                'keywords': ['engineer', 'developer', 'architect', 'technical', 'software', 'programming', 'coding']
            },
            {
                'name': 'Business',
                'slug': 'business',
                'description': 'Business development and operations',
                'color': '#45B7D1',
                'icon': '📊',
                'keywords': ['business', 'sales', 'marketing', 'strategy', 'operations', 'product', 'manager']
            },
            {
                'name': 'Research',
                'slug': 'research',
                'description': 'Research and data science',
                'color': '#96CEB4',
                'icon': '🔬',
                'keywords': ['research', 'scientist', 'phd', 'analysis', 'data', 'analytics', 'ml', 'ai']
            },
            {
                'name': 'Design',
                'slug': 'design',
                'description': 'Design and creative professionals',
                'color': '#FFEAA7',
                'icon': '🎨',
                'keywords': ['design', 'ux', 'ui', 'creative', 'visual', 'graphic', 'product design']
            },
            {
                'name': 'Finance',
                'slug': 'finance',
                'description': 'Finance and accounting',
                'color': '#DFE6E9',
                'icon': '💰',
                'keywords': ['finance', 'accounting', 'controller', 'analyst', 'financial', 'treasurer']
            },
            {
                'name': 'Human Resources',
                'slug': 'human-resources',
                'description': 'HR and people operations',
                'color': '#FD79A8',
                'icon': '👥',
                'keywords': ['hr', 'human resources', 'people', 'recruiting', 'talent', 'recruitment']
            },
            {
                'name': 'Legal',
                'slug': 'legal',
                'description': 'Legal and compliance',
                'color': '#A29BFE',
                'icon': '⚖️',
                'keywords': ['legal', 'counsel', 'attorney', 'lawyer', 'compliance', 'general counsel']
            }
        ]
        
        for cat_data in default_categories:
            # Check if category already exists
            existing = session.query(Category).filter_by(slug=cat_data['slug']).first()
            if not existing:
                category = Category(**cat_data)
                session.add(category)
                logger.info(f"Added category: {cat_data['name']}")
        
        session.commit()
        logger.info(f"Inserted {len(default_categories)} default categories")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert default categories: {e}")
    finally:
        session.close()


def migrate_database(database_url: str = None) -> bool:
    """
    Run database migrations.
    
    Args:
        database_url: Database connection string
    
    Returns:
        bool: True if successful
    """
    try:
        logger.info("Running database migrations...")
        
        # For now, just ensure all tables exist
        # In the future, implement proper migration versioning
        return init_database(database_url, force=False)
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False


def backup_database(database_url: str = None, backup_dir: str = None) -> str:
    """
    Create a backup of the database.
    
    Args:
        database_url: Database connection string
        backup_dir: Directory to store backups
    
    Returns:
        str: Path to backup file
    """
    try:
        if database_url is None:
            database_url = os.getenv('DATABASE_PATH', 'data/profiles.db')
            if database_url.startswith('sqlite:///'):
                database_url = database_url.replace('sqlite:///', '')
        
        if backup_dir is None:
            backup_dir = 'data/backups'
        
        # Create backup directory
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'backup_{timestamp}.db')
        
        # Copy database file
        import shutil
        shutil.copy2(database_url, backup_path)
        
        logger.success(f"Database backed up to: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return None


def restore_database(backup_path: str, database_url: str = None) -> bool:
    """
    Restore database from backup.
    
    Args:
        backup_path: Path to backup file
        database_url: Database connection string
    
    Returns:
        bool: True if successful
    """
    try:
        if database_url is None:
            database_url = os.getenv('DATABASE_PATH', 'data/profiles.db')
            if database_url.startswith('sqlite:///'):
                database_url = database_url.replace('sqlite:///', '')
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Create backup of current database before restoring
        current_backup = backup_database(database_url)
        logger.info(f"Current database backed up to: {current_backup}")
        
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, database_url)
        
        logger.success(f"Database restored from: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        return False


def get_database_stats(database_url: str = None) -> dict:
    """
    Get database statistics.
    
    Args:
        database_url: Database connection string
    
    Returns:
        dict: Database statistics
    """
    try:
        db_session = DatabaseSession(database_url)
        
        with db_session.get_session() as session:
            from .models import Profile, Content, Category, ScrapeLog
            
            stats = {
                'profiles': session.query(Profile).count(),
                'active_profiles': session.query(Profile).filter_by(is_active=True).count(),
                'contents': session.query(Content).count(),
                'categories': session.query(Category).count(),
                'scrape_logs': session.query(ScrapeLog).count(),
                'recent_scrapes': session.query(ScrapeLog).filter(
                    ScrapeLog.status == 'success'
                ).count()
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


if __name__ == '__main__':
    """CLI for database operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management')
    parser.add_argument('command', choices=['init', 'migrate', 'backup', 'stats'],
                       help='Command to execute')
    parser.add_argument('--force', action='store_true',
                       help='Force operation (drops tables for init)')
    parser.add_argument('--db', type=str, default=None,
                       help='Database URL')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_database(args.db, force=args.force)
    elif args.command == 'migrate':
        migrate_database(args.db)
    elif args.command == 'backup':
        backup_database(args.db)
    elif args.command == 'stats':
        stats = get_database_stats(args.db)
        print("\nDatabase Statistics:")
        print("=" * 40)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
