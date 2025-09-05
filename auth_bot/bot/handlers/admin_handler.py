#!/usr/bin/env python3
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from ...database.operations import DatabaseManager
from ...database.models import PaymentStatus, SubscriptionType
from ...utils.token_utils import TokenGenerator
from ..config import ADMIN_IDS, MESSAGES

logger = logging.getLogger(__name__)

# Global instances (will be injected from main)
db_manager: DatabaseManager = None
token_generator: TokenGenerator = None


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


async def admin_stats_command(client: Client, message: Message):
    """Show admin statistics"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text(MESSAGES["UNAUTHORIZED"])
            return
        
        # Get system statistics
        stats = await db_manager.get_system_stats()
        
        stats_text = "📊 **Admin Dashboard - System Statistics**\n\n"
        stats_text += f"**Total Users:** {stats.get('total_users', 0)}\n"
        stats_text += f"**Premium Users:** {stats.get('premium_users', 0)}\n"
        stats_text += f"**Free Users:** {stats.get('free_users', 0)}\n"
        stats_text += f"**Active Tokens:** {stats.get('active_tokens', 0)}\n"
        stats_text += f"**Completed Payments:** {stats.get('completed_payments', 0)}\n"
        
        # Get recent activity
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Add more detailed stats if needed
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("🎫 Token Management", callback_data="admin_tokens")],
            [InlineKeyboardButton("💳 Payment Management", callback_data="admin_payments")],
            [InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_stats")]
        ])
        
        await message.reply_text(stats_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Error in admin stats command: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def admin_users_command(client: Client, message: Message):
    """Show user management options"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text(MESSAGES["UNAUTHORIZED"])
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search User", callback_data="search_user")],
            [InlineKeyboardButton("💎 Upgrade User", callback_data="upgrade_user")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
            [InlineKeyboardButton("📊 User Stats", callback_data="user_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_stats")]
        ])
        
        await message.reply_text(
            "👥 **User Management**\n\nSelect an action:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Error in admin users command: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def admin_tokens_command(client: Client, message: Message):
    """Show token management options"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text(MESSAGES["UNAUTHORIZED"])
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search Tokens", callback_data="search_tokens")],
            [InlineKeyboardButton("❌ Revoke Token", callback_data="revoke_token_admin")],
            [InlineKeyboardButton("📊 Token Stats", callback_data="token_stats")],
            [InlineKeyboardButton("🧹 Cleanup Expired", callback_data="cleanup_tokens")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_stats")]
        ])
        
        await message.reply_text(
            "🎫 **Token Management**\n\nSelect an action:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Error in admin tokens command: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def admin_upgrade_user(admin_id: int, user_id: int, days: int) -> bool:
    """Admin function to upgrade user to premium"""
    try:
        if not is_admin(admin_id):
            return False
        
        success = await db_manager.upgrade_user_to_premium(user_id, days)
        if success:
            logger.info(f"✅ Admin {admin_id} upgraded user {user_id} to premium for {days} days")
        return success
        
    except Exception as e:
        logger.error(f"❌ Error upgrading user by admin: {e}")
        return False


async def admin_ban_user(admin_id: int, user_id: int, reason: str = "") -> bool:
    """Admin function to ban user"""
    try:
        if not is_admin(admin_id):
            return False
        
        success = await db_manager.update_user(user_id, {
            "is_banned": True,
            "ban_reason": reason
        })
        
        if success:
            logger.info(f"✅ Admin {admin_id} banned user {user_id}, reason: {reason}")
        return success
        
    except Exception as e:
        logger.error(f"❌ Error banning user by admin: {e}")
        return False


async def admin_force_payment_success(admin_id: int, payment_id: str) -> bool:
    """Admin function to manually mark payment as successful"""
    try:
        if not is_admin(admin_id):
            return False
        
        payment = await db_manager.get_payment(payment_id)
        if not payment:
            return False
        
        # Update payment status
        await db_manager.update_payment_status(payment_id, PaymentStatus.COMPLETED)
        
        # Upgrade user
        plan_duration_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90
        }.get(payment.plan_type.value, 7)
        
        success = await db_manager.upgrade_user_to_premium(payment.user_id, plan_duration_days)
        
        if success:
            logger.info(f"✅ Admin {admin_id} manually confirmed payment {payment_id}")
        return success
        
    except Exception as e:
        logger.error(f"❌ Error confirming payment by admin: {e}")
        return False


async def admin_callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle admin callback queries"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if not is_admin(user_id):
            await callback_query.answer(MESSAGES["UNAUTHORIZED"], show_alert=True)
            return
        
        if data == "admin_stats":
            stats = await db_manager.get_system_stats()
            
            stats_text = "📊 **System Statistics**\n\n"
            stats_text += f"**Total Users:** {stats.get('total_users', 0)}\n"
            stats_text += f"**Premium Users:** {stats.get('premium_users', 0)}\n"
            stats_text += f"**Free Users:** {stats.get('free_users', 0)}\n"
            stats_text += f"**Active Tokens:** {stats.get('active_tokens', 0)}\n"
            stats_text += f"**Completed Payments:** {stats.get('completed_payments', 0)}\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
                [InlineKeyboardButton("🎫 Tokens", callback_data="admin_tokens")],
                [InlineKeyboardButton("💳 Payments", callback_data="admin_payments")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")]
            ])
            
            await callback_query.message.edit_text(stats_text, reply_markup=keyboard)
            
        elif data == "admin_users":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Search User", callback_data="search_user")],
                [InlineKeyboardButton("💎 Upgrade User", callback_data="upgrade_user")],
                [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_stats")]
            ])
            
            await callback_query.message.edit_text(
                "👥 **User Management**\n\nSelect an action:",
                reply_markup=keyboard
            )
            
        elif data == "admin_tokens":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Search Tokens", callback_data="search_tokens")],
                [InlineKeyboardButton("❌ Revoke Token", callback_data="revoke_token_admin")],
                [InlineKeyboardButton("🧹 Cleanup Expired", callback_data="cleanup_tokens")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_stats")]
            ])
            
            await callback_query.message.edit_text(
                "🎫 **Token Management**\n\nSelect an action:",
                reply_markup=keyboard
            )
            
        elif data == "admin_payments":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Search Payments", callback_data="search_payments")],
                [InlineKeyboardButton("✅ Confirm Payment", callback_data="confirm_payment")],
                [InlineKeyboardButton("❌ Cancel Payment", callback_data="cancel_payment")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_stats")]
            ])
            
            await callback_query.message.edit_text(
                "💳 **Payment Management**\n\nSelect an action:",
                reply_markup=keyboard
            )
        
        # Add more callback handlers as needed
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in admin callback handler: {e}")
        await callback_query.answer("An error occurred.", show_alert=True)


async def broadcast_message(admin_id: int, message_text: str, target_type: str = "all") -> int:
    """Broadcast message to users"""
    try:
        if not is_admin(admin_id):
            return 0
        
        # This is a placeholder - you'd need to implement actual broadcasting
        # You could get all users from database and send message to each
        
        # For now, just return a mock count
        return 100
        
    except Exception as e:
        logger.error(f"❌ Error broadcasting message: {e}")
        return 0


# Create handlers
admin_stats_handler = MessageHandler(
    admin_stats_command,
    filters.command("admin") & filters.private & filters.user(ADMIN_IDS)
)

admin_users_handler = MessageHandler(
    admin_users_command,
    filters.command("users") & filters.private & filters.user(ADMIN_IDS)
)

admin_tokens_handler = MessageHandler(
    admin_tokens_command,
    filters.command("tokens") & filters.private & filters.user(ADMIN_IDS)
)

admin_callback_handler = CallbackQueryHandler(
    admin_callback_handler,
    filters.regex(r"^admin_") & filters.user(ADMIN_IDS)
)
