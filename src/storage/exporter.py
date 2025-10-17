"""
Data export and import functionality for knowledge management.

Supports multiple formats and backup/restore operations.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from zipfile import ZipFile, ZIP_DEFLATED

from loguru import logger

from .database import DatabaseManager
from .models import Document


class DataExporter:
    """
    Export and import knowledge base data.
    
    Features:
    - Multiple format support (JSON, CSV)
    - Backup and restore
    - Data validation
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize exporter.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
    
    def export_to_json(
        self,
        filepath: str,
        include_embeddings: bool = False,
        category: Optional[str] = None
    ) -> bool:
        """
        Export documents to JSON file.
        
        Args:
            filepath: Output file path
            include_embeddings: Include embedding vectors
            category: Filter by category
            
        Returns:
            True if successful
        """
        try:
            documents = self.db.get_all_documents(limit=10000, category=category)
            
            export_data = {
                'metadata': {
                    'exported_at': datetime.utcnow().isoformat(),
                    'total_documents': len(documents),
                    'include_embeddings': include_embeddings,
                    'category': category,
                },
                'documents': []
            }
            
            for doc in documents:
                doc_data = doc.to_dict()
                
                # Add embeddings if requested
                if include_embeddings:
                    embedding = self.db.get_embedding_by_doc_id(doc.id)
                    doc_data['embedding'] = embedding
                
                export_data['documents'].append(doc_data)
            
            # Write to file
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(documents)} documents to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def import_from_json(
        self,
        filepath: str,
        skip_duplicates: bool = True
    ) -> int:
        """
        Import documents from JSON file.
        
        Args:
            filepath: Input file path
            skip_duplicates: Skip documents with existing URLs
            
        Returns:
            Number of imported documents
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = data.get('documents', [])
            imported_count = 0
            
            for doc_data in documents:
                # Check for duplicates
                if skip_duplicates:
                    existing = self.db.get_document_by_url(doc_data['url'])
                    if existing:
                        continue
                
                # Extract embedding if present
                embedding = doc_data.pop('embedding', None)
                
                # Remove fields that shouldn't be set directly
                doc_data.pop('id', None)
                doc_data.pop('scraped_at', None)
                doc_data.pop('last_updated', None)
                
                # Create document
                doc = self.db.add_document(**doc_data)
                
                if doc and embedding:
                    # Add embedding
                    self.db.add_embedding(
                        doc_id=doc.id,
                        vector=embedding,
                        model_name=data['metadata'].get('embedding_model', 'unknown'),
                    )
                
                if doc:
                    imported_count += 1
            
            logger.info(f"Imported {imported_count} documents from {filepath}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return 0
    
    def export_to_csv(
        self,
        filepath: str,
        fields: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> bool:
        """
        Export documents to CSV file.
        
        Args:
            filepath: Output file path
            fields: Fields to include (default: basic fields)
            category: Filter by category
            
        Returns:
            True if successful
        """
        try:
            documents = self.db.get_all_documents(limit=10000, category=category)
            
            if not fields:
                fields = [
                    'id', 'url', 'title', 'name', 'job_title',
                    'email', 'phone', 'category', 'scraped_at'
                ]
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for doc in documents:
                    doc_dict = doc.to_dict()
                    row = {field: doc_dict.get(field, '') for field in fields}
                    writer.writerow(row)
            
            logger.info(f"Exported {len(documents)} documents to CSV: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def create_backup(self, backup_dir: str = "data/backups") -> Optional[str]:
        """
        Create a compressed backup of the entire database.
        
        Args:
            backup_dir: Directory for backups
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"backup_{timestamp}.zip"
            
            # Export to JSON
            temp_json = backup_path / f"temp_export_{timestamp}.json"
            self.export_to_json(str(temp_json), include_embeddings=True)
            
            # Create ZIP archive
            with ZipFile(backup_file, 'w', ZIP_DEFLATED) as zipf:
                zipf.write(temp_json, arcname="data.json")
                
                # Include database file if exists
                db_path = Path(self.db.db_path)
                if db_path.exists():
                    zipf.write(db_path, arcname="database.db")
            
            # Clean up temp file
            temp_json.unlink()
            
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """
        Restore database from backup file.
        
        Args:
            backup_file: Path to backup ZIP file
            
        Returns:
            True if successful
        """
        try:
            temp_dir = Path("data/temp_restore")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            with ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Import JSON data
            json_file = temp_dir / "data.json"
            if json_file.exists():
                count = self.import_from_json(str(json_file), skip_duplicates=False)
                logger.info(f"Restored {count} documents from backup")
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def export_statistics(self, filepath: str) -> bool:
        """
        Export database statistics to JSON.
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful
        """
        try:
            stats = self.db.get_statistics()
            stats['generated_at'] = datetime.utcnow().isoformat()
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Statistics exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Statistics export failed: {e}")
            return False


__all__ = ['DataExporter']
