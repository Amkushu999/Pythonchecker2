"""
Database operations for the Darkanon Checker bot.
Uses JSON file for persistent storage.
"""
import os
import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Union, Any
from config import DATABASE_FILE, DEFAULT_CREDITS

logger = logging.getLogger(__name__)

class Database:
    """Database class for the bot."""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        """Initialize the database."""
        self.db_file = db_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from the JSON file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading database: {e}")
                return self._create_default_data()
        else:
            return self._create_default_data()
    
    def _create_default_data(self) -> Dict:
        """Create default data structure."""
        return {
            "users": {},
            "redeem_codes": {},
            "stats": {
                "total_checks": 0,
                "successful_checks": 0
            }
        }
    
    def _save_data(self) -> None:
        """Save data to the JSON file."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving database: {e}")
    
    def user_exists(self, user_id: int) -> bool:
        """Check if a user exists in the database."""
        return str(user_id) in self.data["users"]
    
    def register_user(self, user_id: int, username: str) -> bool:
        """Register a new user."""
        if self.user_exists(user_id):
            return False
        
        self.data["users"][str(user_id)] = {
            "username": username,
            "credits": DEFAULT_CREDITS,
            "is_premium": False,
            "premium_expiry": None,
            "registered_at": int(time.time()),
            "total_checks": 0,
            "successful_checks": 0,
            "redeemed_codes": []
        }
        self._save_data()
        return True
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data."""
        return self.data["users"].get(str(user_id))
    
    def update_user(self, user_id: int, data: Dict) -> bool:
        """Update user data."""
        if not self.user_exists(user_id):
            return False
        
        self.data["users"][str(user_id)].update(data)
        self._save_data()
        return True
    
    def add_credits(self, user_id: int, amount: int) -> bool:
        """Add credits to a user's account."""
        if not self.user_exists(user_id):
            return False
        
        self.data["users"][str(user_id)]["credits"] += amount
        self._save_data()
        return True
    
    def use_credits(self, user_id: int, amount: int) -> bool:
        """Use credits from a user's account."""
        if not self.user_exists(user_id):
            return False
        
        user = self.data["users"][str(user_id)]
        if user["credits"] < amount:
            return False
        
        user["credits"] -= amount
        self._save_data()
        return True
    
    def set_premium(self, user_id: int, expiry: int) -> bool:
        """Set premium status for a user."""
        if not self.user_exists(user_id):
            return False
        
        self.data["users"][str(user_id)]["is_premium"] = True
        self.data["users"][str(user_id)]["premium_expiry"] = expiry
        self._save_data()
        return True
    
    def generate_redeem_code(self, credits: int, premium_days: int) -> str:
        """Generate a new redeem code."""
        code = f"ANON-{uuid.uuid4().hex[:16].upper()}-CHK"
        self.data["redeem_codes"][code] = {
            "credits": credits,
            "premium_days": premium_days,
            "created_at": int(time.time()),
            "used_by": None,
            "used_at": None
        }
        self._save_data()
        return code
    
    def redeem_code(self, user_id: int, code: str) -> Optional[Dict]:
        """Redeem a code."""
        if not self.user_exists(user_id) or code not in self.data["redeem_codes"]:
            return None
        
        redeem_data = self.data["redeem_codes"][code]
        if redeem_data["used_by"] is not None:
            return None
        
        # Mark code as used
        redeem_data["used_by"] = str(user_id)
        redeem_data["used_at"] = int(time.time())
        
        # Add credits to user
        user = self.data["users"][str(user_id)]
        user["credits"] += redeem_data["credits"]
        
        # Add premium if applicable
        if redeem_data["premium_days"] > 0:
            premium_expiry = int(time.time()) + (redeem_data["premium_days"] * 86400)
            user["is_premium"] = True
            user["premium_expiry"] = premium_expiry
        
        # Add code to user's redeemed codes
        user["redeemed_codes"].append(code)
        
        self._save_data()
        return redeem_data
    
    def log_check(self, user_id: int, success: bool) -> None:
        """Log a check attempt."""
        # Update global stats
        self.data["stats"]["total_checks"] += 1
        if success:
            self.data["stats"]["successful_checks"] += 1
        
        # Update user stats if user exists
        if self.user_exists(user_id):
            self.data["users"][str(user_id)]["total_checks"] += 1
            if success:
                self.data["users"][str(user_id)]["successful_checks"] += 1
        
        self._save_data()
    
    def get_all_users(self) -> Dict:
        """Get all users."""
        return self.data["users"]

# Create a global database instance
db = Database()
