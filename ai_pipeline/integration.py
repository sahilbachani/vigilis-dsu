"""
AI Pipeline Integration Module
Orchestrates the entire analysis pipeline with async processing.
Handles real-time post processing and database operations.
"""

import asyncio
import logging
from typing import Optional, List, Callable
from datetime import datetime
from queue import Queue
from threading import Thread

from sqlalchemy.orm import Session

from .analyzer import TextAnalyzer, AnalysisResult
from .models_loader import ModelsLoader
from .text_processor import TextProcessor
from .db_operations import AnalyzedPostDB
from .config import LOG_PREDICTIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAnalysisPipeline:
    """
    Complete AI analysis pipeline.
    Handles real-time processing of posts as they're scraped.
    Manages async processing, queuing, and database operations.
    """
    
    def __init__(self, models_loader: Optional[ModelsLoader] = None):
        """
        Initialize the AI pipeline.
        
        Args:
            models_loader: Optional pre-initialized ModelsLoader
        """
        self.models_loader = models_loader or ModelsLoader.create_singleton()
        self.analyzer = TextAnalyzer(self.models_loader)
        self.text_processor = TextProcessor()
        self.db_ops = AnalyzedPostDB()
        
        # Event loop for async operations
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def analyze_and_save_async(
        self,
        db: Session,
        source_id: int,
        author: str,
        text_content: str,
        timestamp: datetime,
        url: Optional[str] = None,
        category: str = "twitter"
    ) -> Optional[int]:
        """
        Analyze a post and save it if flagged (async version).
        Best for real-time scraper integration.
        
        Args:
            db: Database session
            source_id: Source ID
            author: Post author
            text_content: Original text
            timestamp: Post timestamp
            url: Optional URL
            category: Post category
            
        Returns:
            post_id if saved, None otherwise
        """
        # Analyze asynchronously
        analysis_result = await self.analyzer.analyze_text_async(text_content)
        
        # Save synchronously on the provided session
        return self.db_ops.save_analyzed_post(
            db=db,
            source_id=source_id,
            author=author,
            text_content=text_content,
            timestamp=timestamp,
            analysis_result=analysis_result,
            url=url,
            category=category
        )
    
    def analyze_and_save(
        self,
        db: Session,
        source_id: int,
        author: str,
        text_content: str,
        timestamp: datetime,
        url: Optional[str] = None,
        category: str = "twitter"
    ) -> Optional[int]:
        """
        Analyze a post and save it if flagged (synchronous version).
        Simpler for integration but blocks on analysis.
        
        Args:
            db: Database session
            source_id: Source ID
            author: Post author
            text_content: Original text
            timestamp: Post timestamp
            url: Optional URL
            category: Post category
            
        Returns:
            post_id if saved, None otherwise
        """
        # Analyze
        analysis_result = self.analyzer.analyze_text(text_content)
        
        # Log if enabled
        if LOG_PREDICTIONS:
            logger.info(
                f"Analysis: {author} | "
                f"hate={analysis_result.hate_score:.2f}, "
                f"extremism={analysis_result.extremism_score:.2f}, "
                f"misinformation={analysis_result.misinformation_score:.2f}, "
                f"confidence={analysis_result.confidence_score:.2f} | "
                f"flagged={analysis_result.flagged}"
            )
        
        # Save
        return self.db_ops.save_analyzed_post(
            db=db,
            source_id=source_id,
            author=author,
            text_content=text_content,
            timestamp=timestamp,
            analysis_result=analysis_result,
            url=url,
            category=category
        )
    
    def analyze_batch(self, texts: List[str]) -> List[AnalysisResult]:
        """
        Analyze multiple texts in batch.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of AnalysisResult objects
        """
        return self.analyzer.analyze_batch(texts)
    
    async def analyze_batch_async(self, texts: List[str]) -> List[AnalysisResult]:
        """
        Analyze multiple texts concurrently.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of AnalysisResult objects
        """
        return await self.analyzer.analyze_batch_async(texts)
    
    def get_analysis_stats(self, db: Session) -> dict:
        """Get analysis statistics from database"""
        return self.db_ops.get_analysis_stats(db)
    
    def get_flagged_posts(
        self,
        db: Session,
        limit: int = 50,
        category: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[dict]:
        """Get flagged posts for dashboard"""
        return self.db_ops.get_flagged_posts(
            db=db,
            limit=limit,
            category=category,
            min_confidence=min_confidence
        )
    
    def get_unanalyzed_posts(self, db: Session, limit: int = 100) -> List[dict]:
        """Get unanalyzed posts for batch processing"""
        return self.db_ops.get_unanalyzed_posts(db=db, limit=limit)
    
    def process_unanalyzed_backlog(self, db: Session, batch_size: int = 10) -> int:
        """
        Process backlog of unanalyzed posts.
        Useful for processing posts saved before analysis was implemented.
        
        Args:
            db: Database session
            batch_size: Number of posts to process at once
            
        Returns:
            Number of posts processed
        """
        logger.info("Starting backlog processing...")
        processed_count = 0
        
        while True:
            posts = self.get_unanalyzed_posts(db, limit=batch_size)
            if not posts:
                break
            
            for post in posts:
                try:
                    analysis_result = self.analyzer.analyze_text(post['text_content'])
                    
                    # Update the post with analysis
                    self.db_ops.update_post_analysis(db, post['post_id'], analysis_result)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing post {post['post_id']}: {str(e)}")
                    continue
        
        logger.info(f"✓ Backlog processing complete: {processed_count} posts processed")
        return processed_count


class PostAnalysisQueue:
    """
    Thread-safe queue for asynchronous post analysis.
    Useful for high-volume scraping scenarios.
    """
    
    def __init__(self, db_session_factory, pipeline: AIAnalysisPipeline, max_workers: int = 4):
        """
        Initialize the queue processor.
        
        Args:
            db_session_factory: Factory function to create DB sessions
            pipeline: AIAnalysisPipeline instance
            max_workers: Number of worker threads
        """
        self.queue: Queue = Queue(maxsize=1000)
        self.db_session_factory = db_session_factory
        self.pipeline = pipeline
        self.max_workers = max_workers
        self._running = False
        self._workers: List[Thread] = []
    
    def start(self):
        """Start the queue processor workers"""
        logger.info(f"Starting {self.max_workers} analysis workers...")
        self._running = True
        
        for i in range(self.max_workers):
            worker = Thread(
                target=self._worker_loop,
                name=f"AnalysisWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        
        logger.info("✓ Analysis workers started")
    
    def stop(self):
        """Stop the queue processor"""
        logger.info("Stopping analysis workers...")
        self._running = False
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=5)
        
        logger.info("✓ Analysis workers stopped")
    
    def add_post(self, post_data: dict):
        """
        Add a post to the analysis queue.
        
        Args:
            post_data: Dict with keys: source_id, author, text_content, timestamp, url, category
        """
        try:
            self.queue.put(post_data, timeout=5)
        except Exception as e:
            logger.error(f"Failed to add post to queue: {str(e)}")
    
    def _worker_loop(self):
        """Main worker loop - process posts from queue"""
        while self._running:
            try:
                # Get post from queue with timeout
                post_data = self.queue.get(timeout=1)
                
                # Create DB session
                db = self.db_session_factory()
                
                try:
                    # Analyze and save
                    self.pipeline.analyze_and_save(
                        db=db,
                        source_id=post_data['source_id'],
                        author=post_data['author'],
                        text_content=post_data['text_content'],
                        timestamp=post_data['timestamp'],
                        url=post_data.get('url'),
                        category=post_data.get('category', 'twitter')
                    )
                finally:
                    db.close()
                    self.queue.task_done()
                    
            except Exception as e:
                if "Empty" not in str(e):  # Ignore timeout exceptions
                    logger.debug(f"Worker error: {str(e)}")
                continue
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
