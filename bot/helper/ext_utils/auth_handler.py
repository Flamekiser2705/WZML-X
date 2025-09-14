#!/usr/bin/env python3
"""
Auth Bot Integration Handler
Handles communication between main bot and auth bot API
"""

import aiohttp
import logging
from typing import Optional, Dict, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AuthBotHandler:
    """Handles integration with WZML-X Auth Bot API"""
    
    def __init__(self):
        self.auth_api_url = os.getenv('AUTH_API_URL', 'http://localhost:8001')
        self.auth_api_key = os.getenv('AUTH_API_KEY', 'wzmlx_auth_api_key_2024')
        self.bot_id = os.getenv('BOT_ID', 'main_bot')
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.auth_api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def validate_token(self, user_id: int, token: str) -> Dict[str, Any]:
        """
        Validate user token with auth bot API
        
        Args:
            user_id: Telegram user ID
            token: Token to validate
            
        Returns:
            dict: Validation result
        """
        try:
            session = await self._get_session()
            
            payload = {
                "user_id": user_id,
                "bot_id": self.bot_id,
                "token": token
            }
            
            async with session.post(
                f"{self.auth_api_url}/validate-token",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Token validation result for user {user_id}: {result.get('is_valid', False)}")
                    return result
                else:
                    logger.error(f"Token validation failed: HTTP {response.status}")
                    return {"is_valid": False, "message": "API call failed"}
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during token validation: {e}")
            return {"is_valid": False, "message": "Network error"}
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return {"is_valid": False, "message": "Validation error"}
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information from auth bot
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: User information or None
        """
        try:
            session = await self._get_session()
            
            payload = {"user_id": user_id}
            
            async with session.post(
                f"{self.auth_api_url}/user-info",
                json=payload
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    logger.info(f"Retrieved user info for {user_id}")
                    return user_info
                elif response.status == 404:
                    logger.info(f"User {user_id} not found in auth system")
                    return None
                else:
                    logger.error(f"Failed to get user info: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
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
        auth_bot_username = os.getenv('AUTH_BOT_USERNAME', 'SoulKaizer_bot').replace('@', '')
        
        user_mention = f"@{username}" if username else "User"
        
        return f"""Hey, {user_mention},

1: Please verify your account to start using this bot.
2: You need to Start @{auth_bot_username} in DM to get access tokens.

🔗 Get your tokens: https://t.me/{auth_bot_username}"""
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

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