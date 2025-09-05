#!/usr/bin/env python3
"""
Main Bot Integration Example
This file shows how to integrate the auth bot with your main mirror bot
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthBotClient:
    """Client for integrating with the auth bot API"""
    
    def __init__(self, auth_api_url: str, auth_api_key: str):
        self.auth_api_url = auth_api_url.rstrip('/')
        self.auth_api_key = auth_api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.auth_api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def validate_token(self, token: str, bot_id: str) -> Dict[str, Any]:
        """Validate a UUID4 token with the auth bot"""
        try:
            async with self.session.post(
                f"{self.auth_api_url}/validate-token",
                json={"token": token, "bot_id": bot_id}
            ) as response:
                result = await response.json()
                
                # Additional UUID4 validation on client side
                if result.get("valid") and self._is_valid_uuid4(token):
                    logger.info(f"✅ Valid UUID4 token: {token[:8]}...")
                    return result
                else:
                    logger.warning(f"❌ Invalid UUID4 token format: {token[:8]}...")
                    return {"valid": False, "error": "Invalid token format"}
                    
        except Exception as e:
            logger.error(f"❌ Error validating token: {e}")
            return {"valid": False, "error": str(e)}
    
    @staticmethod
    def _is_valid_uuid4(token: str) -> bool:
        """Validate UUID4 format on client side"""
        try:
            import uuid
            uuid_obj = uuid.UUID(token, version=4)
            return str(uuid_obj) == token
        except (ValueError, TypeError):
            return False
    
    async def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """Get user information from the auth bot"""
        try:
            async with self.session.get(
                f"{self.auth_api_url}/user-info/{user_id}"
            ) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"❌ Error getting user info: {e}")
            return {"error": str(e)}
    
    async def check_user_access(self, user_id: int, bot_id: str) -> bool:
        """Check if user has access to the bot"""
        try:
            user_info = await self.get_user_info(user_id)
            if "error" in user_info:
                return False
            
            # Check if user has active tokens
            token_validation = await self.validate_token("", bot_id)  # We'll use user_id instead
            
            return user_info.get("subscription_type") == "premium" or \
                   len(user_info.get("active_tokens", [])) > 0
        except Exception as e:
            logger.error(f"❌ Error checking user access: {e}")
            return False


# Example integration with your existing bot
class AuthMiddleware:
    """Middleware for checking user authorization in your main bot"""
    
    def __init__(self, auth_client: AuthBotClient, bot_id: str):
        self.auth_client = auth_client
        self.bot_id = bot_id
        self.cache = {}  # Simple cache for token validation
        self.cache_ttl = 300  # Cache for 5 minutes
    
    async def check_authorization(self, user_id: int, token: str = None) -> Dict[str, Any]:
        """Check if user is authorized to use the bot"""
        cache_key = f"{user_id}_{token or 'no_token'}"
        current_time = datetime.now().timestamp()
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if current_time - cached_time < self.cache_ttl:
                return cached_data
        
        # Validate with auth bot
        if token:
            result = await self.auth_client.validate_token(token, self.bot_id)
        else:
            user_info = await self.auth_client.get_user_info(user_id)
            result = {
                "valid": not user_info.get("error") and user_info.get("active_tokens", 0) > 0,
                "user_info": user_info
            }
        
        # Cache the result
        self.cache[cache_key] = (result, current_time)
        
        return result
    
    def clear_cache(self, user_id: int = None):
        """Clear cache for a specific user or all users"""
        if user_id:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()


# Example usage in your main bot handlers
"""
# In your mirror bot's handlers (e.g., mirror_leech.py)

from pyrogram import Client, filters
from pyrogram.types import Message
from .auth_integration import AuthBotClient, AuthMiddleware

# Initialize auth client
auth_client = AuthBotClient(
    auth_api_url="http://localhost:8001",  # Your auth bot API URL
    auth_api_key="your-api-key-here"
)

auth_middleware = AuthMiddleware(auth_client, "mirror_bot_1")

@Client.on_message(filters.command("mirror") & filters.private)
async def mirror_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check authorization
    async with auth_client:
        auth_result = await auth_middleware.check_authorization(user_id)
    
    if not auth_result.get("valid"):
        await message.reply_text(
            "❌ **Access Denied**\n\n"
            "You need a valid UUID4 token to use this bot.\n"
            f"Get your token from: @{AUTH_BOT_USERNAME}\n\n"
            "**Example token format:**\n"
            "`550e8400-e29b-41d4-a716-446655440000`"
        )
        return
    
    # User is authorized, proceed with mirror operation
    await message.reply_text("✅ Starting mirror operation...")
    # Your existing mirror logic here

@Client.on_message(filters.command("leech") & filters.private)
async def leech_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check for UUID4 token in message
    uuid4_token = None
    if len(message.command) > 1:
        potential_token = message.command[1]
        # Validate UUID4 format
        if _is_valid_uuid4_format(potential_token):
            uuid4_token = potential_token
    
    async with auth_client:
        auth_result = await auth_middleware.check_authorization(user_id, uuid4_token)
    
    if not auth_result.get("valid"):
        await message.reply_text(
            "❌ **Access Denied**\n\n"
            "You need a valid UUID4 token to use this bot.\n"
            f"Get your token from: @{AUTH_BOT_USERNAME}\n\n"
            "**Usage:** `/leech <url> <uuid4_token>`\n"
            "**Example:** `/leech https://example.com 550e8400-e29b-41d4-a716-446655440000`"
        )
        return
    
    # User is authorized, proceed with leech operation
    await message.reply_text("✅ Starting leech operation...")
    # Your existing leech logic here

def _is_valid_uuid4_format(token: str) -> bool:
    '''Check if token is valid UUID4 format'''
    try:
        import uuid
        uuid_obj = uuid.UUID(token, version=4)
        return str(uuid_obj) == token
    except:
        return False
"""


# Configuration example for your config.py
AUTH_BOT_CONFIG = {
    "AUTH_API_URL": "http://localhost:8001",  # URL where auth bot API is running
    "AUTH_API_KEY": "your-secret-api-key",    # API key for authentication
    "AUTH_BOT_USERNAME": "your_auth_bot",     # Username of your auth bot
    "BOT_ID": "mirror_bot_1",                 # Unique ID for this bot
    "CACHE_TTL": 300,                         # Cache time-to-live in seconds
    "UNAUTHORIZED_MESSAGE": (
        "❌ **Access Denied**\n\n"
        "You need a valid UUID4 token to use this bot.\n"
        "Get your token from: @{auth_bot_username}\n\n"
        "**How to get a UUID4 token:**\n"
        "1. Start the auth bot: @{auth_bot_username}\n"
        "2. Use /verify command\n"
        "3. Choose your plan (Free 6h or Premium 7/30/90 days)\n"
        "4. Copy the UUID4 token (format: xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx)\n"
        "5. Use it here: `/mirror <url> <uuid4_token>`\n\n"
        "**Example:** `/mirror https://example.com 550e8400-e29b-41d4-a716-446655440000`"
    )
}


# Helper function to add to your existing filters.py
def create_auth_filter(auth_middleware: AuthMiddleware):
    """Create a custom filter for authorization"""
    from pyrogram import filters
    
    async def auth_filter(_, __, message):
        if not message.from_user:
            return False
        
        user_id = message.from_user.id
        
        # Extract UUID4 token from message if present
        uuid4_token = None
        if hasattr(message, 'command') and len(message.command) > 1:
            # Check if last argument looks like a UUID4 token
            potential_token = message.command[-1]
            if _is_valid_uuid4_format(potential_token):
                uuid4_token = potential_token
        
        # Check authorization
        auth_result = await auth_middleware.check_authorization(user_id, uuid4_token)
        
        # Store result in message for use in handler
        message.auth_result = auth_result
        
        return auth_result.get("valid", False)
    
    return filters.create(auth_filter)

def _is_valid_uuid4_format(token: str) -> bool:
    """Check if token is valid UUID4 format"""
    try:
        import uuid
        uuid_obj = uuid.UUID(token, version=4)
        return str(uuid_obj) == token
    except (ValueError, TypeError):
        return False


# Example decorator for your handlers
def require_auth(func):
    """Decorator to require authentication for a handler"""
    async def wrapper(client, message):
        if not hasattr(message, 'auth_result') or not message.auth_result.get("valid"):
            await message.reply_text(
                AUTH_BOT_CONFIG["UNAUTHORIZED_MESSAGE"].format(
                    auth_bot_username=AUTH_BOT_CONFIG["AUTH_BOT_USERNAME"]
                )
            )
            return
        
        return await func(client, message)
    
    return wrapper
