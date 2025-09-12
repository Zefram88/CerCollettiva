# core/middleware/query_monitoring.py

import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

class QueryMonitoringMiddleware:
    """
    Middleware per monitorare le performance delle query database
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Reset query count and time
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        end_time = time.time()
        total_queries = len(connection.queries) - initial_queries
        total_time = end_time - start_time
        
        # Log performance metrics
        if total_queries > 0:
            avg_query_time = sum(float(q['time']) for q in connection.queries[initial_queries:]) / total_queries
            
            # Log warning for slow requests
            if total_queries > 10 or total_time > 1.0 or avg_query_time > 0.1:
                logger.warning(
                    f"Slow request detected - "
                    f"Path: {request.path}, "
                    f"Queries: {total_queries}, "
                    f"Total time: {total_time:.3f}s, "
                    f"Avg query time: {avg_query_time:.3f}s"
                )
            
            # Log detailed query info in debug mode
            if settings.DEBUG and total_queries > 5:
                logger.debug(
                    f"Request: {request.path} - "
                    f"Queries: {total_queries}, "
                    f"Time: {total_time:.3f}s"
                )
                
                # Log individual slow queries
                for query in connection.queries[initial_queries:]:
                    if float(query['time']) > 0.05:  # Queries slower than 50ms
                        logger.debug(f"Slow query ({query['time']}s): {query['sql'][:100]}...")
        
        return response
