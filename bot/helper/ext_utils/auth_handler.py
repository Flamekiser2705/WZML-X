#!/usr/bin/env python3
"""
Auth Bot Integration Handler
Handles communication between main bot and auth bot via direct database access
"""

import logging
from typing import Optional, Dict, Any
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class AuthBotHandler:
    """Handles integration with WZML-X Auth Bot via direct database access"""
    
    def __init__(self):
        self.mongodb_uri = os.getenv('DATABASE_URL', '')
        self.client = None
        self.db = None
        self.tokens_collection = None
        self.user_collection = None
        self._initialized = False
    
    async def _init_database(self):
        """Initialize database connection"""
        if self._initialized:
            return
            
        try:
            if not self.mongodb_uri:
                logger.error("[AUTH] DATABASE_URL not configured")
                return
                
            # Connect to MongoDB (same database as auth bot)
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client.auth_bot  # Use auth_bot database
            self.tokens_collection = self.db.tokens
            self.user_collection = self.db.users
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("[AUTH] Connected to auth bot database")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"[AUTH] Database connection failed: {e}")
            self._initialized = False
    
    async def _get_current_bot_key(self) -> str:
        """
        Get the bot_key for the current bot by matching bot token/ID
        """
        try:
            from bot import LOGGER, bot
            
            # Get current bot info
            bot_token = bot.token
            current_bot_id = bot_token.split(':')[0] if ':' in bot_token else None
            
            if not current_bot_id:
                logger.error("[AUTH] Cannot determine current bot ID")
                return "bot1"  # Default fallback
            
            # Read auth bot's bot_configs.json to find matching bot_key
            import json
            from pathlib import Path
            
            auth_bot_config_path = Path(__file__).parent.parent.parent.parent / "auth_bot" / "bot_configs.json"
            
            if auth_bot_config_path.exists():
                with open(auth_bot_config_path, 'r') as f:
                    bot_configs = json.load(f)
                
                # Find bot_key that matches current bot_id
                for bot_key, bot_config in bot_configs.items():
                    if bot_config.get("bot_id") == current_bot_id:
                        logger.info(f"[AUTH] Found bot_key '{bot_key}' for bot_id '{current_bot_id}'")
                        return bot_key
            
            logger.warning(f"[AUTH] Bot_key not found for bot_id '{current_bot_id}', using 'bot1'")
            return "bot1"  # Default fallback
            
        except Exception as e:
            logger.error(f"[AUTH] Error determining bot_key: {e}")
            return "bot1"  # Default fallback
    
    async def validate_token(self, user_id: int) -> Dict[str, Any]:
        """
        Validate user token directly from auth bot database
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Validation result with is_valid, message, and token info
        """
        try:
            await self._init_database()
            if not self._initialized:
                return {"is_valid": False, "message": "Database not initialized"}
            
            # Get the correct bot_key for this bot
            bot_key = await self._get_current_bot_key()
            logger.info(f"[AUTH] Checking token for user {user_id} with bot_key '{bot_key}'")
            
            # Query the tokens collection for valid token
            token_doc = await self.tokens_collection.find_one({
                "user_id": user_id,
                "bot_key": bot_key,
                "verified": True
            })
            
            if not token_doc:
                logger.debug(f"[AUTH] Token not found for user {user_id}")
                return {"is_valid": False, "message": "Invalid token"}
            
            # Check if token is expired
            expires_at = token_doc.get("expires_at")
            if expires_at:
                # Parse ISO datetime string
                if isinstance(expires_at, str):
                    try:
                        expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    except:
                        expires_dt = datetime.fromisoformat(expires_at)
                else:
                    expires_dt = expires_at
                    
                if expires_dt < datetime.now(timezone.utc):
                    logger.debug(f"[AUTH] Token expired for user {user_id}")
                    return {"is_valid": False, "message": "Token expired"}
            
            logger.info(f"[AUTH] Valid token found for user {user_id}")
            return {
                "is_valid": True, 
                "message": "Token valid",
                "bot_key": token_doc.get("bot_key"),
                "type": token_doc.get("type")
            }
                    
        except Exception as e:
            logger.error(f"[AUTH] Error validating token: {e}")
            return {"is_valid": False, "message": "Validation error"}
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information from auth bot database
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: User information or None
        """
        try:
            await self._init_database()
            if not self._initialized:
                return None
            
            # Count active tokens for user
            active_tokens = await self.tokens_collection.count_documents({
                "user_id": user_id,
                "verified": True,
                "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
            })
            
            # Get user data if exists
            user_data = await self.user_collection.find_one({"user_id": user_id})
            
            if active_tokens > 0 or user_data:
                logger.info(f"[AUTH] User {user_id} has {active_tokens} active tokens")
                return {
                    "user_id": user_id,
                    "active_tokens": active_tokens,
                    "user_data": user_data
                }
            
            return None
                    
        except Exception as e:
            logger.error(f"[AUTH] Error getting user info: {e}")
            return None
    
    async def is_user_authorized(self, user_id: int, token: str = None) -> bool:
        """
        Check if user is authorized to use the bot
        
        Args:
            user_id: Telegram user ID
            token: Optional token for validation
            
        Returns:
            bool: True if authorized
        """
        try:
            # If token provided, validate it
            if token:
                validation_result = await self.validate_token(user_id, token)
                return validation_result.get("is_valid", False)
            
            # Otherwise check if user has any active tokens
            user_info = await self.get_user_info(user_id)
            if user_info:
                active_tokens = user_info.get("active_tokens", 0)
                return active_tokens > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user authorization: {e}")
            return False
    
    async def get_auth_message(self, user_id: int, username: str = None) -> str:
        """
        Get appropriate auth message for unauthorized user
        
        Args:
            user_id: Telegram user ID
            username: Optional username
            
        Returns:
            str: Auth message
        """
        # Try to get message from command management system first
        try:
            from bot.helper.ext_utils.command_manager import command_manager
            config = command_manager.get_config()
            if config and 'messages' in config and 'unauthorized' in config['messages']:
                return config['messages']['unauthorized']
        except:
            pass
        
        # Fallback to environment-based message
        auth_bot_username = os.getenv('AUTH_BOT_USERNAME', 'your_auth_bot').replace('@', '')
        
        user_mention = f"@{username}" if username else "User"
        
        return f"""❌ **Unauthorized Access**

Hey {user_mention},

This command requires authorization. Please contact an admin or use our auth bot to gain access.

🔗 **Auth Bot**: @{auth_bot_username}
💡 **How to get access**: Send /start to the auth bot in DM

Need help? Contact an admin."""
    
    async def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            self.client = None
            self._initialized = False
            logger.info("[AUTH] Database connection closed")

# Global instance
auth_handler = AuthBotHandler()

async def validate_user_token(user_id: int, token: str) -> bool:
    """
    Simple function to validate user token
    
    Args:
        user_id: Telegram user ID  
        token: Token to validate
        
    Returns:
        bool: True if valid
    """
    result = await auth_handler.validate_token(user_id, token)
    return result.get("is_valid", False)

async def is_user_authorized(user_id: int, token: str = None) -> bool:
    """
    Simple function to check if user is authorized
    
    Args:
        user_id: Telegram user ID
        token: Optional token
        
    Returns:
        bool: True if authorized
    """
    return await auth_handler.is_user_authorized(user_id, token)

async def get_user_auth_message(user_id: int, username: str = None) -> str:
    """
    Get auth message for unauthorized user
    
    Args:
        user_id: Telegram user ID
        username: Optional username
        
    Returns:
        str: Auth message
    """
    return await auth_handler.get_auth_message(user_id, username)