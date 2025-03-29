"""
Helper functions and decorators for the Darkanon Checker bot.
"""
import time
import logging
import functools
from typing import Any, Callable, Dict, Optional
from database import db
from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

def is_user_registered(user_id: int) -> bool:
    """
    Check if a user is registered.
    
    Args:
        user_id: The user ID to check.
        
    Returns:
        True if the user is registered, False otherwise.
    """
    return db.user_exists(user_id)

def check_premium_expiry(user_id: int) -> None:
    """
    Check if a user's premium has expired and update accordingly.
    
    Args:
        user_id: The user ID to check.
    """
    user = db.get_user(user_id)
    if not user:
        return
    
    if user["is_premium"] and user["premium_expiry"] and user["premium_expiry"] < time.time():
        db.update_user(user_id, {"is_premium": False, "premium_expiry": None})

def require_registration(func: Callable) -> Callable:
    """
    Decorator to require registration for a function.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        
        if not is_user_registered(user_id):
            await update.message.reply_text(
                "You need to register first to use this command.\n"
                "Use /register to register."
            )
            return
        
        check_premium_expiry(user_id)
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def require_credits(amount: int) -> Callable:
    """
    Decorator to require a certain amount of credits for a function.
    
    Args:
        amount: The amount of credits required.
        
    Returns:
        The decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Check if user is registered
            if not is_user_registered(user_id):
                await update.message.reply_text(
                    "You need to register first to use this command.\n"
                    "Use /register to register."
                )
                return
            
            # Check if user has enough credits
            user = db.get_user(user_id)
            if user["credits"] < amount:
                await update.message.reply_text(
                    f"You don't have enough credits for this operation.\n"
                    f"Required: {amount} credits\n"
                    f"Available: {user['credits']} credits\n\n"
                    f"Use /buy to purchase more credits."
                )
                return
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    return decorator

def check_rate_limit(func: Callable) -> Callable:
    """
    Decorator to check rate limits for a function.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is registered
        if not is_user_registered(user_id):
            await update.message.reply_text(
                "You need to register first to use this command.\n"
                "Use /register to register."
            )
            return
        
        # Get user info
        user = db.get_user(user_id)
        is_premium = user["is_premium"]
        
        # Check if user is rate limited
        if rate_limiter.is_rate_limited(user_id, is_premium):
            limit = 30 if is_premium else 10
            count = rate_limiter.get_requests_count(user_id)
            
            await update.message.reply_text(
                f"You're making too many requests. Please slow down.\n"
                f"Limit: {limit} requests per minute\n"
                f"Current: {count} requests\n\n"
                f"{'Premium users have higher rate limits.' if not is_premium else ''}"
            )
            return
        
        # Add request to rate limiter
        rate_limiter.add_request(user_id)
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper
