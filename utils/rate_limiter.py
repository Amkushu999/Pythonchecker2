"""
Rate limiting functionality to prevent abuse.
"""
import time
import logging
from typing import Dict, List, Optional
from config import MAX_CHECKS_PER_MINUTE, PREMIUM_MAX_CHECKS_PER_MINUTE

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter to prevent abuse of the bot.
    Uses a sliding window algorithm.
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        self.request_history: Dict[int, List[float]] = {}
    
    def add_request(self, user_id: int) -> None:
        """
        Add a request to the history.
        
        Args:
            user_id: The user ID making the request.
        """
        current_time = time.time()
        
        # Initialize history for user if needed
        if user_id not in self.request_history:
            self.request_history[user_id] = []
        
        # Add current request time
        self.request_history[user_id].append(current_time)
        
        # Clean up old requests (older than 60 seconds)
        self.request_history[user_id] = [
            t for t in self.request_history[user_id] 
            if current_time - t < 60
        ]
    
    def is_rate_limited(self, user_id: int, is_premium: bool = False) -> bool:
        """
        Check if a user is rate limited.
        
        Args:
            user_id: The user ID to check.
            is_premium: Whether the user is premium.
            
        Returns:
            True if the user is rate limited, False otherwise.
        """
        if user_id not in self.request_history:
            return False
        
        # Count requests in the last 60 seconds
        current_time = time.time()
        recent_requests = len([
            t for t in self.request_history[user_id] 
            if current_time - t < 60
        ])
        
        # Determine the limit based on premium status
        limit = PREMIUM_MAX_CHECKS_PER_MINUTE if is_premium else MAX_CHECKS_PER_MINUTE
        
        return recent_requests >= limit
    
    def get_requests_count(self, user_id: int) -> int:
        """
        Get the number of requests made by a user in the last minute.
        
        Args:
            user_id: The user ID to check.
            
        Returns:
            The number of requests made in the last minute.
        """
        if user_id not in self.request_history:
            return 0
        
        current_time = time.time()
        return len([
            t for t in self.request_history[user_id] 
            if current_time - t < 60
        ])

# Create a global rate limiter instance
rate_limiter = RateLimiter()
