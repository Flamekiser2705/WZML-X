#!/usr/bin/env python3
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..database.operations import DatabaseManager
from ..database.models import User, Token, SubscriptionType

logger = logging.getLogger(__name__)


class AuthHelpers:
    """Helper functions for authentication system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def get_user_subscription_info(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user subscription information"""
        try:
            user = await self.db_manager.get_user(user_id)
            if not user:
                return {"error": "User not found"}
            
            stats = await self.db_manager.get_user_stats(user_id)
            
            # Check if premium is expired
            is_premium_active = (
                user.subscription_type == SubscriptionType.PREMIUM and
                user.premium_expiry and
                user.premium_expiry > datetime.utcnow()
            )
            
            return {
                "user_id": user_id,
                "username": user.username,
                "subscription_type": user.subscription_type.value,
                "is_premium_active": is_premium_active,
                "premium_expiry": user.premium_expiry.isoformat() if user.premium_expiry else None,
                "active_tokens": stats.get("active_tokens", 0),
                "total_tokens": stats.get("total_tokens", 0),
                "premium_tokens": stats.get("premium_tokens", 0),
                "free_tokens": stats.get("free_tokens", 0),
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user subscription info: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens and return count of cleaned tokens"""
        try:
            # MongoDB TTL index should handle this automatically,
            # but we can also manually clean up for immediate effect
            count = 0
            
            # Get all expired tokens
            current_time = datetime.utcnow()
            
            # This is a placeholder - actual implementation would depend on
            # your database structure
            logger.info(f"🧹 Cleaned up {count} expired tokens")
            return count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired tokens: {e}")
            return 0
    
    async def get_bot_usage_stats(self, bot_id: str) -> Dict[str, Any]:
        """Get usage statistics for a specific bot"""
        try:
            bot = await self.db_manager.get_bot(bot_id)
            if not bot:
                return {"error": "Bot not found"}
            
            # Get token counts for this bot
            # This would require additional database queries
            
            return {
                "bot_id": bot_id,
                "bot_name": bot.name,
                "is_active": bot.is_active,
                "total_users": 0,  # Would implement actual count
                "active_tokens": 0,  # Would implement actual count
                "created_at": bot.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting bot usage stats: {e}")
            return {"error": str(e)}
    
    async def validate_user_access(self, user_id: int, bot_id: str) -> Dict[str, Any]:
        """Validate if user has access to a specific bot"""
        try:
            user = await self.db_manager.get_user(user_id)
            if not user:
                return {"has_access": False, "reason": "User not found"}
            
            if user.is_banned:
                return {"has_access": False, "reason": "User is banned"}
            
            # Check if user has valid tokens for this bot
            tokens = await self.db_manager.get_user_tokens(user_id, bot_id)
            active_tokens = len(tokens)
            
            if active_tokens > 0:
                return {
                    "has_access": True,
                    "active_tokens": active_tokens,
                    "subscription_type": user.subscription_type.value
                }
            else:
                return {
                    "has_access": False,
                    "reason": "No active tokens for this bot",
                    "subscription_type": user.subscription_type.value
                }
                
        except Exception as e:
            logger.error(f"❌ Error validating user access: {e}")
            return {"has_access": False, "reason": "Validation error"}
    
    @staticmethod
    def format_time_remaining(expiry_time: datetime) -> str:
        """Format remaining time until expiry"""
        now = datetime.utcnow()
        if expiry_time <= now:
            return "Expired"
        
        diff = expiry_time - now
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @staticmethod
    def calculate_pricing_tiers() -> List[Dict[str, Any]]:
        """Calculate dynamic pricing tiers"""
        return [
            {
                "plan_id": "7d",
                "name": "Weekly Premium",
                "duration_days": 7,
                "price_inr": 500,  # ₹5
                "price_usd": 1,    # $1
                "features": [
                    "7 days premium access",
                    "Multiple bot tokens",
                    "Priority support"
                ]
            },
            {
                "plan_id": "30d",
                "name": "Monthly Premium",
                "duration_days": 30,
                "price_inr": 2000,  # ₹20
                "price_usd": 3,     # $3
                "features": [
                    "30 days premium access",
                    "Multiple bot tokens",
                    "Priority support",
                    "Advanced features"
                ]
            },
            {
                "plan_id": "90d",
                "name": "Quarterly Premium",
                "duration_days": 90,
                "price_inr": 5000,  # ₹50
                "price_usd": 7,     # $7
                "features": [
                    "90 days premium access",
                    "Multiple bot tokens",
                    "VIP support",
                    "All premium features",
                    "Best value"
                ]
            }
        ]


class SecurityHelpers:
    """Security helper functions"""
    
    @staticmethod
    def validate_user_input(input_text: str, max_length: int = 100) -> bool:
        """Validate user input for security"""
        if not input_text or len(input_text) > max_length:
            return False
        
        # Add more validation as needed
        forbidden_chars = ['<', '>', '"', "'", '&', '\n', '\r']
        return not any(char in input_text for char in forbidden_chars)
    
    @staticmethod
    def sanitize_user_input(input_text: str) -> str:
        """Sanitize user input"""
        if not input_text:
            return ""
        
        # Remove potentially dangerous characters
        forbidden_chars = ['<', '>', '"', "'", '&']
        for char in forbidden_chars:
            input_text = input_text.replace(char, "")
        
        return input_text.strip()
    
    @staticmethod
    def is_valid_user_id(user_id: int) -> bool:
        """Validate Telegram user ID format"""
        # Telegram user IDs are positive integers
        return isinstance(user_id, int) and user_id > 0
    
    @staticmethod
    def is_valid_bot_id(bot_id: str) -> bool:
        """Validate bot ID format"""
        if not bot_id or not isinstance(bot_id, str):
            return False
        
        # Bot IDs should be alphanumeric with underscores/hyphens
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        return all(c in allowed_chars for c in bot_id) and len(bot_id) <= 50


class MessageHelpers:
    """Message formatting helpers"""
    
    @staticmethod
    def format_user_info_message(user_info: Dict[str, Any]) -> str:
        """Format user information for display"""
        if "error" in user_info:
            return f"❌ Error: {user_info['error']}"
        
        text = f"👤 **User Information**\n\n"
        text += f"**User ID:** {user_info['user_id']}\n"
        
        if user_info.get('username'):
            text += f"**Username:** @{user_info['username']}\n"
        
        text += f"**Subscription:** {user_info['subscription_type'].title()}\n"
        
        if user_info['is_premium_active']:
            text += f"**Premium Until:** {user_info['premium_expiry'][:10]}\n"
        
        text += f"**Active Tokens:** {user_info['active_tokens']}\n"
        text += f"**Total Tokens:** {user_info['total_tokens']}\n"
        text += f"**Premium Tokens:** {user_info['premium_tokens']}\n"
        text += f"**Free Tokens:** {user_info['free_tokens']}\n"
        
        return text
    
    @staticmethod
    def format_token_info_message(token_info: Dict[str, Any]) -> str:
        """Format token information for display"""
        text = f"🎫 **Token Information**\n\n"
        text += f"**Token:** `{token_info.get('token', 'N/A')}`\n"
        text += f"**Type:** {token_info.get('type', 'N/A')}\n"
        text += f"**Bot:** {token_info.get('bot_name', 'N/A')}\n"
        text += f"**Expires:** {token_info.get('expires_at', 'N/A')}\n"
        text += f"**Usage Count:** {token_info.get('usage_count', 0)}\n"
        
        return text
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """Format error message for display"""
        return f"❌ **Error:** {error}\n\nPlease try again later or contact support."
    
    @staticmethod
    def format_success_message(message: str) -> str:
        """Format success message for display"""
        return f"✅ **Success:** {message}"


# Utility functions for background tasks
async def schedule_token_cleanup():
    """Schedule periodic token cleanup"""
    while True:
        try:
            # Wait 1 hour between cleanups
            await asyncio.sleep(3600)
            
            # Perform cleanup (this would be implemented with actual database connection)
            logger.info("🧹 Running scheduled token cleanup...")
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled cleanup: {e}")


async def schedule_stats_update():
    """Schedule periodic statistics update"""
    while True:
        try:
            # Wait 30 minutes between updates
            await asyncio.sleep(1800)
            
            # Update statistics (implement as needed)
            logger.info("📊 Running scheduled stats update...")
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled stats update: {e}")


def create_background_tasks():
    """Create background tasks for the application"""
    tasks = [
        asyncio.create_task(schedule_token_cleanup()),
        asyncio.create_task(schedule_stats_update())
    ]
    return tasks
