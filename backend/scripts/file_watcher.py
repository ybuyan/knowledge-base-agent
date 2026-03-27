#!/usr/bin/env python
"""
File Watcher Service
Monitors configured directories for file changes and triggers processing.
"""

import os
import sys
import json
import time
import signal
import logging
import argparse
import threading
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.file_tracker import FileTracker
from app.core.chroma import delete_document_vectors
from app.core.constants import DocumentConstants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @property
    def watch_dirs(self) -> List[Dict[str, Any]]:
        """Get watch directories with auto extension resolution"""
        dirs = self.config.get("watch_dirs", [])
        # 处理 extensions: "auto" 的情况
        for dir_config in dirs:
            if dir_config.get("extensions") == "auto":
                dir_config["extensions"] = DocumentConstants.SUPPORTED_EXTENSIONS
        return dirs
    
    @property
    def processing(self) -> Dict[str, Any]:
        return self.config.get("processing", {})
    
    @property
    def storage(self) -> Dict[str, Any]:
        return self.config.get("storage", {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        return self.config.get("logging", {})


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""
    
    def __init__(self, tracker: FileTracker, task_queue: Queue, config: Config):
        self.tracker = tracker
        self.task_queue = task_queue
        self.config = config
        self.extensions: Set[str] = set()
        self.debounce_timers: Dict[str, threading.Timer] = {}
        self.debounce_seconds = config.processing.get("debounce_seconds", 2)
    
    def set_extensions(self, extensions: List[str]):
        """Set allowed file extensions"""
        self.extensions = set(ext.lower() for ext in extensions)
    
    def _is_valid_file(self, file_path: str) -> bool:
        """Check if file has valid extension"""
        if not self.extensions:
            return True
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.extensions
    
    def _debounce(self, file_path: str, action: str):
        """Debounce file events to avoid duplicate processing"""
        # Cancel existing timer if any
        if file_path in self.debounce_timers:
            self.debounce_timers[file_path].cancel()
        
        # Create new timer
        timer = threading.Timer(
            self.debounce_seconds,
            self._process_event,
            args=[file_path, action]
        )
        self.debounce_timers[file_path] = timer
        timer.start()
    
    def _process_event(self, file_path: str, action: str):
        """Process the file event after debounce"""
        if file_path in self.debounce_timers:
            del self.debounce_timers[file_path]
        
        if action == "delete":
            self._handle_delete(file_path)
        elif action in ("create", "modify"):
            self._handle_create_or_modify(file_path, action)
    
    def _handle_create_or_modify(self, file_path: str, action: str):
        """Handle file create or modify event"""
        if not os.path.exists(file_path):
            return
        
        if not self._is_valid_file(file_path):
            return
        
        logger.info(f"File {action} detected: {file_path}")
        
        # Check if file exists in tracker
        existing = self.tracker.get_file_info(file_path)
        
        if existing:
            # Check if file has changed
            if self.tracker.is_file_changed(file_path):
                logger.info(f"File modified, marking for reprocessing: {file_path}")
                self.tracker.mark_for_reprocess(file_path)
                self.task_queue.put(("reprocess", file_path))
            else:
                logger.debug(f"File unchanged, skipping: {file_path}")
        else:
            # New file
            self.tracker.register_file(file_path)
            self.task_queue.put(("process", file_path))
    
    def _handle_delete(self, file_path: str):
        """Handle file delete event"""
        logger.info(f"File deleted: {file_path}")
        
        # Get document_id before removing
        document_id = self.tracker.remove_file(file_path)
        
        if document_id:
            # Add delete task to queue
            self.task_queue.put(("delete", file_path, document_id))
    
    def on_created(self, event):
        """Handle file created event"""
        if event.is_directory:
            return
        self._debounce(event.src_path, "create")
    
    def on_modified(self, event):
        """Handle file modified event"""
        if event.is_directory:
            return
        self._debounce(event.src_path, "modify")
    
    def on_deleted(self, event):
        """Handle file deleted event"""
        if event.is_directory:
            return
        self._debounce(event.src_path, "delete")


class FileWatcherService:
    """Main file watcher service"""
    
    def __init__(self, config_path: str):
        self.config = Config(config_path)
        self.tracker = self._init_tracker()
        self.task_queue = Queue()
        self.observer = Observer()
        self.running = False
        self.workers: List[threading.Thread] = []
    
    def _init_tracker(self) -> FileTracker:
        """Initialize file tracker"""
        db_path = self.config.storage.get("state_db", "data/watch_state.db")
        # Make path relative to backend directory
        if not os.path.isabs(db_path):
            backend_dir = Path(__file__).parent.parent
            db_path = str(backend_dir / db_path)
        return FileTracker(db_path)
    
    def _setup_logging(self):
        """Setup logging based on config"""
        log_config = self.config.logging_config
        
        if log_config.get("file"):
            log_dir = self.config.storage.get("log_dir", "data/watch_logs")
            if not os.path.isabs(log_dir):
                backend_dir = Path(__file__).parent.parent
                log_dir = str(backend_dir / log_dir)
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(
                log_dir, 
                f"watcher_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(file_handler)
        
        if log_config.get("level"):
            logging.getLogger().setLevel(getattr(logging, log_config["level"]))
    
    def _initial_scan(self):
        """Perform initial scan of all watch directories"""
        logger.info("Performing initial scan of watch directories...")
        
        for watch_dir in self.config.watch_dirs:
            if not watch_dir.get("enabled", True):
                continue
            
            dir_path = watch_dir["path"]
            if not os.path.exists(dir_path):
                logger.warning(f"Watch directory does not exist: {dir_path}")
                continue
            
            extensions = watch_dir.get("extensions", [])
            recursive = watch_dir.get("recursive", True)
            
            logger.info(f"Scanning directory: {dir_path}")
            
            # Walk directory
            if recursive:
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self._check_and_register_file(file_path, extensions)
            else:
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path):
                        self._check_and_register_file(file_path, extensions)
        
        # Log stats
        stats = self.tracker.get_stats()
        logger.info(f"Initial scan complete. Stats: {stats}")
    
    def _check_and_register_file(self, file_path: str, extensions: List[str]):
        """Check file extension and register if valid"""
        ext = os.path.splitext(file_path)[1].lower()
        if extensions and ext not in [e.lower() for e in extensions]:
            return
        
        if not self.tracker.file_exists(file_path):
            self.tracker.register_file(file_path)
            self.task_queue.put(("process", file_path))
        elif self.tracker.is_file_changed(file_path):
            self.tracker.mark_for_reprocess(file_path)
            self.task_queue.put(("reprocess", file_path))
    
    def _process_task(self, task):
        """Process a single task from the queue"""
        from scripts.batch_processor import BatchProcessor
        
        processor = BatchProcessor(self.tracker)
        
        if task[0] == "process":
            _, file_path = task
            logger.info(f"Processing new file: {file_path}")
            processor.process_file(file_path)
        
        elif task[0] == "reprocess":
            _, file_path = task
            logger.info(f"Reprocessing modified file: {file_path}")
            # Get old document_id and delete vectors
            info = self.tracker.get_file_info(file_path)
            if info and info.get("document_id"):
                delete_document_vectors(info["document_id"])
            processor.process_file(file_path)
        
        elif task[0] == "delete":
            _, file_path, document_id = task
            logger.info(f"Deleting vectors for removed file: {file_path}")
            delete_document_vectors(document_id)
    
    def _worker_loop(self):
        """Worker thread loop"""
        from queue import Empty
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    continue
                self._process_task(task)
                self.task_queue.task_done()
            except Empty:
                # Timeout, just continue
                pass
            except Exception as e:
                if self.running:
                    logger.error(f"Worker error: {e}")
    
    def start(self, initial_scan: bool = True):
        """Start the file watcher service"""
        logger.info("Starting file watcher service...")
        
        self._setup_logging()
        
        # Perform initial scan if requested
        if initial_scan:
            self._initial_scan()
        
        # Start worker threads
        self.running = True
        num_workers = self.config.processing.get("workers", 4)
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
        
        # Setup file watchers
        for watch_dir in self.config.watch_dirs:
            if not watch_dir.get("enabled", True):
                continue
            
            dir_path = watch_dir["path"]
            if not os.path.exists(dir_path):
                logger.warning(f"Watch directory does not exist: {dir_path}")
                continue
            
            recursive = watch_dir.get("recursive", True)
            extensions = watch_dir.get("extensions", [])
            
            event_handler = FileEventHandler(self.tracker, self.task_queue, self.config)
            event_handler.set_extensions(extensions)
            
            self.observer.schedule(event_handler, dir_path, recursive=recursive)
            logger.info(f"Watching directory: {dir_path} (recursive={recursive})")
        
        # Start observer
        self.observer.start()
        logger.info("File watcher service started")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the file watcher service"""
        logger.info("Stopping file watcher service...")
        self.running = False
        self.observer.stop()
        self.observer.join()
        
        for worker in self.workers:
            worker.join(timeout=5)
        
        logger.info("File watcher service stopped")


def main():
    parser = argparse.ArgumentParser(description="File Watcher Service")
    parser.add_argument(
        "--config", "-c",
        default="scripts/config/watch.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--initial-scan", "-i",
        action="store_true",
        default=True,
        help="Perform initial scan on startup"
    )
    parser.add_argument(
        "--no-initial-scan",
        action="store_true",
        help="Skip initial scan"
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon"
    )
    
    args = parser.parse_args()
    
    # Resolve config path
    config_path = args.config
    if not os.path.isabs(config_path):
        backend_dir = Path(__file__).parent.parent
        config_path = str(backend_dir / config_path)
    
    # Create and start service
    service = FileWatcherService(config_path)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start service
    initial_scan = args.initial_scan and not args.no_initial_scan
    service.start(initial_scan=initial_scan)


if __name__ == "__main__":
    main()
