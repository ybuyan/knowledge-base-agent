import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileTracker:
    """Track file processing state using SQLite database"""
    
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
    
    def _ensure_db_dir(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    last_modified REAL NOT NULL,
                    processed_at REAL,
                    chunk_count INTEGER DEFAULT 0,
                    document_id TEXT,
                    error_message TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_path ON file_states(file_path)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON file_states(status)
            ''')
            conn.commit()
    
    def compute_file_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file record from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM file_states WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file is already tracked"""
        return self.get_file_info(file_path) is not None
    
    def is_file_changed(self, file_path: str) -> bool:
        """Check if file has changed since last processing"""
        info = self.get_file_info(file_path)
        if not info:
            return True
        
        current_hash = self.compute_file_hash(file_path)
        return current_hash != info["file_hash"]
    
    def register_file(self, file_path: str) -> bool:
        """Register a new file for processing"""
        if not os.path.exists(file_path):
            return False
        
        file_hash = self.compute_file_hash(file_path)
        last_modified = os.path.getmtime(file_path)
        now = datetime.now().timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO file_states 
                    (file_path, file_hash, status, last_modified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_path, file_hash, self.STATUS_PENDING, last_modified, now, now))
                conn.commit()
                logger.info(f"Registered new file: {file_path}")
                return True
            except sqlite3.IntegrityError:
                # File already exists, update if changed
                existing = self.get_file_info(file_path)
                if existing and existing["file_hash"] != file_hash:
                    self.mark_for_reprocess(file_path, file_hash, last_modified)
                    return True
                return False
    
    def mark_processing(self, file_path: str) -> bool:
        """Mark file as currently being processed"""
        now = datetime.now().timestamp()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE file_states 
                SET status = ?, updated_at = ?
                WHERE file_path = ?
            ''', (self.STATUS_PROCESSING, now, file_path))
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_done(self, file_path: str, chunk_count: int, document_id: str = None) -> bool:
        """Mark file as successfully processed"""
        now = datetime.now().timestamp()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE file_states 
                SET status = ?, processed_at = ?, chunk_count = ?, document_id = ?, updated_at = ?
                WHERE file_path = ?
            ''', (self.STATUS_DONE, now, chunk_count, document_id, now, file_path))
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_failed(self, file_path: str, error_message: str) -> bool:
        """Mark file as failed processing"""
        now = datetime.now().timestamp()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE file_states 
                SET status = ?, error_message = ?, updated_at = ?
                WHERE file_path = ?
            ''', (self.STATUS_FAILED, error_message, now, file_path))
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_for_reprocess(self, file_path: str, new_hash: str = None, last_modified: float = None) -> bool:
        """Mark file for reprocessing (when modified)"""
        if new_hash is None:
            new_hash = self.compute_file_hash(file_path)
        if last_modified is None:
            last_modified = os.path.getmtime(file_path)
        
        now = datetime.now().timestamp()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE file_states 
                SET status = ?, file_hash = ?, last_modified = ?, error_message = NULL, updated_at = ?
                WHERE file_path = ?
            ''', (self.STATUS_PENDING, new_hash, last_modified, now, file_path))
            conn.commit()
            return cursor.rowcount > 0
    
    def remove_file(self, file_path: str) -> Optional[str]:
        """Remove file record and return document_id if exists"""
        info = self.get_file_info(file_path)
        document_id = info["document_id"] if info else None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_states WHERE file_path = ?", (file_path,))
            conn.commit()
        
        if info:
            logger.info(f"Removed file record: {file_path}")
        
        return document_id
    
    def get_pending_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of pending files to process"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM file_states 
                WHERE status = ? 
                ORDER BY created_at ASC
                LIMIT ?
            ''', (self.STATUS_PENDING, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_failed_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of failed files"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM file_states 
                WHERE status = ? 
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (self.STATUS_FAILED, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM file_states 
                GROUP BY status
            ''')
            stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute("SELECT COUNT(*) FROM file_states")
            stats["total"] = cursor.fetchone()[0]
            
            return stats
