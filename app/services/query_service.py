"""
Query history service for managing query records in the database
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database_models import Query
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryService:
    """Service for managing query history"""
    
    @staticmethod
    async def create_query_record(
        db: Session,
        user_id: Optional[int],
        query_text: str,
        response_text: str,
        processing_time: float,
        success: bool,
        sources: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        original_language: str = "en",
        target_language: str = "en",
    ) -> Query:
        """
        Create a new query record in the database
        
        Args:
            db: Database session
            user_id: ID of the user who made the query (None for anonymous)
            query_text: The original query text
            response_text: The response generated
            processing_time: Time taken to process the query in seconds
            success: Whether the query was successful
            sources: List of source URLs/references used
            metadata: Additional metadata (RAG info, MCP tools used, etc.)
            error: Error message if query failed
            original_language: Source language code
            target_language: Target language code
            
        Returns:
            Created Query object
        """
        try:
            # Convert sources to comma-separated string, handling dict objects
            if sources:
                sources_list = []
                for source in sources:
                    if isinstance(source, dict):
                        # Extract URL or title from dict
                        sources_list.append(source.get('url') or source.get('title') or str(source))
                    else:
                        sources_list.append(str(source))
                sources_str = ",".join(sources_list)
            else:
                sources_str = None
            
            # Create query record
            query_record = Query(
                user_id=user_id,
                query_text=query_text,
                response_text=response_text,
                processing_time=processing_time,
                success=success,
                sources=sources_str,
                metadata=metadata or {},
                error=error,
                original_language=original_language,
                target_language=target_language,
                timestamp=datetime.now(timezone.utc),
            )
            
            db.add(query_record)
            db.commit()
            db.refresh(query_record)
            
            logger.info(f"Created query record ID: {query_record.id} for user: {user_id or 'anonymous'}")
            return query_record
            
        except Exception as e:
            logger.error(f"Error creating query record: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def get_user_query_history(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Query]:
        """
        Get query history for a specific user
        
        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of Query objects
        """
        try:
            queries = (
                db.query(Query)
                .filter(Query.user_id == user_id)
                .order_by(desc(Query.timestamp))
                .limit(limit)
                .offset(offset)
                .all()
            )
            return queries
        except Exception as e:
            logger.error(f"Error fetching query history for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def get_query_by_id(
        db: Session,
        query_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[Query]:
        """
        Get a specific query by ID
        
        Args:
            db: Database session
            query_id: ID of the query
            user_id: Optional user ID to verify ownership
            
        Returns:
            Query object or None if not found
        """
        try:
            query = db.query(Query).filter(Query.id == query_id)
            
            # If user_id provided, verify ownership
            if user_id is not None:
                query = query.filter(Query.user_id == user_id)
            
            return query.first()
        except Exception as e:
            logger.error(f"Error fetching query {query_id}: {e}")
            raise
    
    @staticmethod
    async def delete_query(
        db: Session,
        query_id: int,
        user_id: int,
    ) -> bool:
        """
        Delete a query record (user can only delete their own queries)
        
        Args:
            db: Database session
            query_id: ID of the query to delete
            user_id: ID of the user requesting deletion
            
        Returns:
            True if deleted, False if not found or unauthorized
        """
        try:
            query = (
                db.query(Query)
                .filter(Query.id == query_id, Query.user_id == user_id)
                .first()
            )
            
            if not query:
                return False
            
            db.delete(query)
            db.commit()
            logger.info(f"Deleted query record ID: {query_id} by user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting query {query_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def get_query_count(
        db: Session,
        user_id: Optional[int] = None,
    ) -> int:
        """
        Get total query count, optionally filtered by user
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by
            
        Returns:
            Total count of queries
        """
        try:
            query = db.query(Query)
            
            if user_id is not None:
                query = query.filter(Query.user_id == user_id)
            
            return query.count()
        except Exception as e:
            logger.error(f"Error counting queries: {e}")
            raise
