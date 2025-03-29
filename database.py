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
            },
            "authorized_groups": [],  # List of authorized group IDs
            "banned_users": {},  # Dict of banned user IDs with reason and timestamp
            "system_settings": {
                "global_lock": False,  # Global lock status
                "maintenance_mode": False,  # Maintenance mode status
                "min_credits_for_private": 1,  # Minimum credits required for private use
                "group_enabled": True  # Whether group usage is enabled
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
    
    # Group management methods
    def add_authorized_group(self, group_id: int) -> bool:
        """Add a group to the authorized groups list."""
        if group_id in self.data["authorized_groups"]:
            return False
        
        self.data["authorized_groups"].append(group_id)
        self._save_data()
        return True
    
    def remove_authorized_group(self, group_id: int) -> bool:
        """Remove a group from the authorized groups list."""
        if group_id not in self.data["authorized_groups"]:
            return False
        
        self.data["authorized_groups"].remove(group_id)
        self._save_data()
        return True
    
    def is_group_authorized(self, group_id: int) -> bool:
        """Check if a group is authorized."""
        return group_id in self.data["authorized_groups"]
    
    def get_authorized_groups(self) -> List[int]:
        """Get all authorized groups."""
        return self.data["authorized_groups"]
    
    # User ban management methods
    def ban_user(self, user_id: int, reason: str) -> bool:
        """Ban a user."""
        if str(user_id) in self.data["banned_users"]:
            return False
        
        self.data["banned_users"][str(user_id)] = {
            "reason": reason,
            "timestamp": int(time.time())
        }
        self._save_data()
        return True
    
    def unban_user(self, user_id: int) -> bool:
        """Unban a user."""
        if str(user_id) not in self.data["banned_users"]:
            return False
        
        del self.data["banned_users"][str(user_id)]
        self._save_data()
        return True
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if a user is banned."""
        return str(user_id) in self.data["banned_users"]
    
    def get_ban_reason(self, user_id: int) -> Optional[str]:
        """Get the reason a user was banned."""
        if not self.is_user_banned(user_id):
            return None
        
        return self.data["banned_users"][str(user_id)]["reason"]
    
    def get_banned_users(self) -> Dict:
        """Get all banned users."""
        return self.data["banned_users"]
    
    # System settings methods
    def set_global_lock(self, locked: bool) -> None:
        """Set the global lock status."""
        self.data["system_settings"]["global_lock"] = locked
        self._save_data()
    
    def is_globally_locked(self) -> bool:
        """Check if the system is globally locked."""
        return self.data["system_settings"]["global_lock"]
    
    def set_maintenance_mode(self, enabled: bool) -> None:
        """Set the maintenance mode status."""
        self.data["system_settings"]["maintenance_mode"] = enabled
        self._save_data()
    
    def is_in_maintenance_mode(self) -> bool:
        """Check if the system is in maintenance mode."""
        return self.data["system_settings"]["maintenance_mode"]
    
    def set_min_credits_for_private(self, amount: int) -> None:
        """Set the minimum credits required for private use."""
        self.data["system_settings"]["min_credits_for_private"] = amount
        self._save_data()
    
    def get_min_credits_for_private(self) -> int:
        """Get the minimum credits required for private use."""
        return self.data["system_settings"]["min_credits_for_private"]
    
    def set_group_enabled(self, enabled: bool) -> None:
        """Set whether group usage is enabled."""
        self.data["system_settings"]["group_enabled"] = enabled
        self._save_data()
    
    def is_group_enabled(self) -> bool:
        """Check if group usage is enabled."""
        return self.data["system_settings"]["group_enabled"]
    
    def can_use_in_private(self, user_id: int) -> bool:
        """Check if a user can use the bot in private chat."""
        if not self.user_exists(user_id):
            return False
        
        user = self.get_user(user_id)
        
        # Premium users can always use in private
        if user["is_premium"]:
            # Check if premium has expired
            if user["premium_expiry"] and user["premium_expiry"] < time.time():
                # Premium expired, update user status
                self.update_user(user_id, {"is_premium": False, "premium_expiry": None})
                # Continue to credit check
            else:
                # Premium active
                return True
        
        # Check if user has enough credits
        min_credits = self.get_min_credits_for_private()
        return user["credits"] >= min_credits

# Create a global database instance
db = Database()
