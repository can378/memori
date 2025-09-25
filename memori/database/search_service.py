"""
SQLAlchemy-based search service for Memori v2.0
Provides cross-database full-text search capabilities
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, desc, or_, text
from sqlalchemy.orm import Session

from .models import LongTermMemory, ShortTermMemory


class SearchService:
    """Cross-database search service using SQLAlchemy"""

    def __init__(self, session: Session, database_type: str):
        self.session = session
        self.database_type = database_type

    def search_memories(
        self,
        query: str,
        namespace: str = "default",
        category_filter: Optional[List[str]] = None,
        limit: int = 10,
        memory_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories across different database backends

        Args:
            query: Search query string
            namespace: Memory namespace
            category_filter: List of categories to filter by
            limit: Maximum number of results
            memory_types: Types of memory to search ('short_term', 'long_term', or both)

        Returns:
            List of memory dictionaries with search metadata
        """
        logger.debug(
            f"SearchService.search_memories called - query: '{query}', namespace: '{namespace}', database: {self.database_type}, limit: {limit}"
        )

        if not query or not query.strip():
            logger.debug("Empty query provided, returning recent memories")
            return self._get_recent_memories(
                namespace, category_filter, limit, memory_types
            )

        results = []

        # Determine which memory types to search
        search_short_term = not memory_types or "short_term" in memory_types
        search_long_term = not memory_types or "long_term" in memory_types

        logger.debug(
            f"Memory types to search - short_term: {search_short_term}, long_term: {search_long_term}, categories: {category_filter}"
        )

        try:
            # Try database-specific full-text search first
            if self.database_type == "postgresql":
                logger.debug("Using PostgreSQL FTS search strategy")
                results = self._search_postgresql_fts(
                    query,
                    namespace,
                    category_filter,
                    limit,
                    search_short_term,
                    search_long_term,
                )

            logger.debug(f"Primary search strategy returned {len(results)} results")

            # If no results or full-text search failed, fall back to LIKE search
            if not results:
                logger.debug(
                    "Primary search returned no results, falling back to LIKE search"
                )
                results = self._search_like_fallback(
                    query,
                    namespace,
                    category_filter,
                    limit,
                    search_short_term,
                    search_long_term,
                )

        except Exception as e:
            logger.error(
                f"Full-text search failed for query '{query}' in namespace '{namespace}': {e}"
            )
            logger.debug(
                f"Full-text search error details: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            logger.warning(f"Falling back to LIKE search for query '{query}'")
            try:
                results = self._search_like_fallback(
                    query,
                    namespace,
                    category_filter,
                    limit,
                    search_short_term,
                    search_long_term,
                )
                logger.debug(f"LIKE fallback search returned {len(results)} results")
            except Exception as fallback_e:
                logger.error(
                    f"LIKE fallback search also failed for query '{query}': {fallback_e}"
                )
                results = []

        final_results = self._rank_and_limit_results(results, limit)
        logger.debug(
            f"SearchService completed - returning {len(final_results)} final results after ranking and limiting"
        )

        if final_results:
            logger.debug(
                f"Top result: memory_id={final_results[0].get('memory_id')}, score={final_results[0].get('composite_score', 0):.3f}, strategy={final_results[0].get('search_strategy')}"
            )

        return final_results


    def _search_postgresql_fts(
        self,
        query: str,
        namespace: str,
        category_filter: Optional[List[str]],
        limit: int,
        search_short_term: bool,
        search_long_term: bool,
    ) -> List[Dict[str, Any]]:
        """Search using PostgreSQL tsvector"""
        results = []

        try:
            # Apply limit proportionally between memory types
            short_limit = (
                limit // 2 if search_short_term and search_long_term else limit
            )
            long_limit = (
                limit - short_limit if search_short_term and search_long_term else limit
            )

            # Prepare query for tsquery - handle spaces and special characters
            # Convert simple query to tsquery format (join words with &)
            

            # Search short-term memory if requested
            if search_short_term:
                short_query = self.session.query(ShortTermMemory).filter(
                    ShortTermMemory.namespace == namespace
                )

                # Add tsvector search
                ts_query = text(
                    "search_vector @@ websearch_to_tsquery('english', :query)"
                ).params(query=query)

                short_query = short_query.filter(ts_query)

                # Add category filter
                if category_filter:
                    short_query = short_query.filter(
                        ShortTermMemory.category_primary.in_(category_filter)
                    )

                # Add relevance score and limit
                short_results = self.session.execute(
                    short_query.statement.add_columns(
                        text(
                            "ts_rank(search_vector, websearch_to_tsquery('english', :query)) as search_score"
                        ).params(query=query),
                        text("'short_term' as memory_type"),
                        text("'postgresql_fts' as search_strategy"),
                    )
                    .order_by(text("search_score DESC"))
                    .limit(short_limit)
                ).fetchall()
                
                
                results.extend([dict(row._mapping) for row in short_results])

            # Search long-term memory if requested
            if search_long_term:
                long_query = self.session.query(LongTermMemory).filter(
                    LongTermMemory.namespace == namespace
                )

                # Add tsvector search
                ts_query = text(
                    "search_vector @@ websearch_to_tsquery('english', :query)"
                ).params(query=query)
                long_query = long_query.filter(ts_query)

                # Add category filter
                if category_filter:
                    long_query = long_query.filter(
                        LongTermMemory.category_primary.in_(category_filter)
                    )

                # Add relevance score and limit
                long_results = self.session.execute(
                    long_query.statement.add_columns(
                        text(
                            "ts_rank(search_vector, websearch_to_tsquery('english', :query)) as search_score"
                        ).params(query=query),
                        text("'long_term' as memory_type"),
                        text("'postgresql_fts' as search_strategy"),
                    )
                    .order_by(text("search_score DESC"))
                    .limit(long_limit)
                ).fetchall()

                results.extend([dict(row._mapping) for row in long_results])

            return results

        except Exception as e:
            logger.error(
                f"PostgreSQL FTS search failed for query '{query}' in namespace '{namespace}': {e}"
            )
            logger.debug(
                f"PostgreSQL FTS error details: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            # Roll back the transaction to recover from error state
            self.session.rollback()
            return []

    def _search_like_fallback(
        self,
        query: str,
        namespace: str,
        category_filter: Optional[List[str]],
        limit: int,
        search_short_term: bool,
        search_long_term: bool,
    ) -> List[Dict[str, Any]]:
        """Fallback LIKE-based search with improved flexibility"""
        logger.debug(
            f"Starting LIKE fallback search for query: '{query}' in namespace: '{namespace}'"
        )
        results = []

        # Create multiple search patterns for better matching
        search_patterns = [
            f"%{query}%",  # Original full query
        ]

        # Add individual word patterns for better matching
        words = query.strip().split()
        if len(words) > 1:
            for word in words:
                if len(word) > 2:  # Skip very short words
                    search_patterns.append(f"%{word}%")

        logger.debug(f"LIKE search patterns: {search_patterns}")

        # Search short-term memory
        if search_short_term:
            # Build OR conditions for all search patterns
            search_conditions = []
            for pattern in search_patterns:
                search_conditions.extend(
                    [
                        ShortTermMemory.searchable_content.like(pattern),
                        ShortTermMemory.summary.like(pattern),
                    ]
                )

            short_query = self.session.query(ShortTermMemory).filter(
                and_(
                    ShortTermMemory.namespace == namespace,
                    or_(*search_conditions),
                )
            )

            if category_filter:
                short_query = short_query.filter(
                    ShortTermMemory.category_primary.in_(category_filter)
                )

            short_results = (
                short_query.order_by(
                    desc(ShortTermMemory.importance_score),
                    desc(ShortTermMemory.created_at),
                )
                .limit(limit)
                .all()
            )

            logger.debug(f"LIKE fallback found {len(short_results)} short-term results")

            for result in short_results:
                memory_dict = {
                    "memory_id": result.memory_id,
                    "memory_type": "short_term",
                    "processed_data": result.processed_data,
                    "importance_score": result.importance_score,
                    "created_at": result.created_at,
                    "summary": result.summary,
                    "category_primary": result.category_primary,
                    "search_score": 0.4,  # Fixed score for LIKE search
                    "search_strategy": f"{self.database_type}_like_fallback",
                }
                results.append(memory_dict)

        # Search long-term memory
        if search_long_term:
            # Build OR conditions for all search patterns
            search_conditions = []
            for pattern in search_patterns:
                search_conditions.extend(
                    [
                        LongTermMemory.searchable_content.like(pattern),
                        LongTermMemory.summary.like(pattern),
                    ]
                )

            long_query = self.session.query(LongTermMemory).filter(
                and_(
                    LongTermMemory.namespace == namespace,
                    or_(*search_conditions),
                )
            )

            if category_filter:
                long_query = long_query.filter(
                    LongTermMemory.category_primary.in_(category_filter)
                )

            long_results = (
                long_query.order_by(
                    desc(LongTermMemory.importance_score),
                    desc(LongTermMemory.created_at),
                )
                .limit(limit)
                .all()
            )

            logger.debug(f"LIKE fallback found {len(long_results)} long-term results")

            for result in long_results:
                memory_dict = {
                    "memory_id": result.memory_id,
                    "memory_type": "long_term",
                    "processed_data": result.processed_data,
                    "importance_score": result.importance_score,
                    "created_at": result.created_at,
                    "summary": result.summary,
                    "category_primary": result.category_primary,
                    "search_score": 0.4,  # Fixed score for LIKE search
                    "search_strategy": f"{self.database_type}_like_fallback",
                }
                results.append(memory_dict)

        logger.debug(
            f"LIKE fallback search completed, returning {len(results)} total results"
        )
        return results

    def _get_recent_memories(
        self,
        namespace: str,
        category_filter: Optional[List[str]],
        limit: int,
        memory_types: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Get recent memories when no search query is provided"""
        results = []

        search_short_term = not memory_types or "short_term" in memory_types
        search_long_term = not memory_types or "long_term" in memory_types

        # Get recent short-term memories
        if search_short_term:
            short_query = self.session.query(ShortTermMemory).filter(
                ShortTermMemory.namespace == namespace
            )

            if category_filter:
                short_query = short_query.filter(
                    ShortTermMemory.category_primary.in_(category_filter)
                )

            short_results = (
                short_query.order_by(desc(ShortTermMemory.created_at))
                .limit(limit // 2)
                .all()
            )

            for result in short_results:
                memory_dict = {
                    "memory_id": result.memory_id,
                    "memory_type": "short_term",
                    "processed_data": result.processed_data,
                    "importance_score": result.importance_score,
                    "created_at": result.created_at,
                    "summary": result.summary,
                    "category_primary": result.category_primary,
                    "search_score": 1.0,
                    "search_strategy": "recent_memories",
                }
                results.append(memory_dict)

        # Get recent long-term memories
        if search_long_term:
            long_query = self.session.query(LongTermMemory).filter(
                LongTermMemory.namespace == namespace
            )

            if category_filter:
                long_query = long_query.filter(
                    LongTermMemory.category_primary.in_(category_filter)
                )

            long_results = (
                long_query.order_by(desc(LongTermMemory.created_at))
                .limit(limit // 2)
                .all()
            )

            for result in long_results:
                memory_dict = {
                    "memory_id": result.memory_id,
                    "memory_type": "long_term",
                    "processed_data": result.processed_data,
                    "importance_score": result.importance_score,
                    "created_at": result.created_at,
                    "summary": result.summary,
                    "category_primary": result.category_primary,
                    "search_score": 1.0,
                    "search_strategy": "recent_memories",
                }
                results.append(memory_dict)

        return results

    def _rank_and_limit_results(
        self, results: List[Dict[str, Any]], limit: int
    ) -> List[Dict[str, Any]]:
        """Rank and limit search results"""
        # Calculate composite score
        for result in results:
            search_score = result.get("search_score", 0.4)
            importance_score = result.get("importance_score", 0.5)
            recency_score = self._calculate_recency_score(result.get("created_at"))

            # Weighted composite score
            result["composite_score"] = (
                search_score * 0.5 + importance_score * 0.3 + recency_score * 0.2
            )

        # Sort by composite score and limit
        results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
        return results[:limit]

    def _calculate_recency_score(self, created_at) -> float:
        """Calculate recency score (0-1, newer = higher)"""
        try:
            if not created_at:
                return 0.0

            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            days_old = (datetime.now() - created_at).days
            return max(0, 1 - (days_old / 30))  # Full score for recent, 0 after 30 days
        except:
            return 0.0
