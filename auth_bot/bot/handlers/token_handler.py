#!/usr/bin/env python3
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from ...database.operations import DatabaseManager
from ...database.models import Token, TokenType, SubscriptionType
from ...utils.token_utils import TokenGenerator, format_expiry_time, get_token_type_display
from ..config import MESSAGES, MAX_FREE_TOKENS_PER_USER, MAX_PREMIUM_TOKENS_PER_USER

logger = logging.getLogger(__name__)

# Global instances (will be injected from main)
db_manager: DatabaseManager = None
token_generator: TokenGenerator = None


async def generate_user_tokens(user_id: int, bot_id: str, token_count: int, message):
    """Generate tokens for user and specific bot"""
    try:
        # Get user info
        user = await db_manager.get_user(user_id)
        if not user:
            await message.edit_text("❌ User not found. Please use /start first.")
            return
        
        # Get bot info
        bot = await db_manager.get_bot(bot_id)
        if not bot:
            await message.edit_text("❌ Bot not found.")
            return
        
        # Check user's current token count
        current_tokens = await db_manager.get_user_tokens(user_id, bot_id)
        active_token_count = len(current_tokens)
        
        # Check token limits
        is_premium = user.subscription_type == SubscriptionType.PREMIUM
        if is_premium and user.premium_expiry and user.premium_expiry < datetime.utcnow():
            is_premium = False  # Premium expired
        
        max_tokens = MAX_PREMIUM_TOKENS_PER_USER if is_premium else MAX_FREE_TOKENS_PER_USER
        
        if active_token_count + token_count > max_tokens:
            limit_text = MESSAGES["TOKEN_LIMIT_REACHED"]
            
            # Add current status
            limit_text += f"\n\n**Current Status:**"
            limit_text += f"\nActive Tokens: {active_token_count}/{max_tokens}"
            limit_text += f"\nRequested: {token_count}"
            limit_text += f"\nSubscription: {'💎 Premium' if is_premium else '🆓 Free'}"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Upgrade to Premium", callback_data="show_premium_plans")],
                [InlineKeyboardButton("🔙 Back", callback_data="verify_start")]
            ])
            
            await message.edit_text(limit_text, reply_markup=keyboard)
            return
        
        # Determine token type
        token_type = TokenType.PREMIUM if is_premium else TokenType.FREE
        
        # Calculate custom days for premium tokens
        custom_days = None
        if is_premium and user.premium_expiry:
            remaining_days = (user.premium_expiry - datetime.utcnow()).days
            custom_days = min(remaining_days, 90)  # Cap at 90 days
        
        # Generate tokens
        generated_tokens = []
        success_count = 0
        
        for i in range(token_count):
            try:
                # Generate token
                token_id, encrypted_token, expires_at = token_generator.generate_access_token(
                    user_id, bot_id, token_type, custom_days
                )
                
                # Create token record
                token_data = Token(
                    token_id=token_id,
                    user_id=user_id,
                    bot_id=bot_id,
                    token=encrypted_token,
                    type=token_type,
                    expires_at=expires_at
                )
                
                # Save to database
                if await db_manager.create_token(token_data):
                    generated_tokens.append({
                        "token": encrypted_token,
                        "expires_at": expires_at,
                        "token_id": token_id
                    })
                    success_count += 1
                else:
                    logger.error(f"Failed to save token for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error generating token {i+1} for user {user_id}: {e}")
        
        if success_count == 0:
            await message.edit_text("❌ Failed to generate tokens. Please try again.")
            return
        
        # Format response message
        if success_count == 1:
            # Single token response
            token_info = generated_tokens[0]
            response_text = MESSAGES["TOKEN_GENERATED"].format(
                token=token_info["token"],
                bot_name=bot.name,
                token_type=get_token_type_display(token_type),
                expires_at=token_info["expires_at"].strftime("%Y-%m-%d %H:%M UTC")
            )
        else:
            # Multiple tokens response
            response_text = f"✅ **{success_count} Tokens Generated Successfully!**\n\n"
            response_text += f"**Bot:** {bot.name}\n"
            response_text += f"**Type:** {get_token_type_display(token_type)}\n\n"
            
            for i, token_info in enumerate(generated_tokens, 1):
                response_text += f"**Token {i}:**\n"
                response_text += f"`{token_info['token']}`\n"
                response_text += f"**Expires:** {token_info['expires_at'].strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            
            response_text += "⚠️ **Important:** Keep these tokens secure and don't share them with others."
        
        # Create keyboard for further actions
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
            [InlineKeyboardButton("🔑 Generate More", callback_data="verify_start")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="start_menu")]
        ])
        
        await message.edit_text(response_text, reply_markup=keyboard)
        
        logger.info(f"✅ Generated {success_count} tokens for user {user_id}, bot {bot_id}")
        
    except Exception as e:
        logger.error(f"❌ Error generating tokens: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def revoke_user_token(user_id: int, token_id: str, message):
    """Revoke a specific user token"""
    try:
        success = await db_manager.revoke_token(token_id)
        
        if success:
            await message.edit_text("✅ Token revoked successfully.")
            logger.info(f"✅ Token {token_id} revoked by user {user_id}")
        else:
            await message.edit_text("❌ Failed to revoke token.")
            
    except Exception as e:
        logger.error(f"❌ Error revoking token: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def list_user_tokens(user_id: int, message):
    """List all active tokens for user"""
    try:
        user = await db_manager.get_user(user_id)
        if not user:
            await message.edit_text("❌ User not found.")
            return
        
        # Get all active tokens
        all_tokens = await db_manager.get_user_tokens(user_id)
        
        if not all_tokens:
            await message.edit_text(
                "📋 **Your Tokens**\n\nNo active tokens found.\n\nUse /verify to generate new tokens.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")],
                    [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
                ])
            )
            return
        
        # Group tokens by bot
        tokens_by_bot = {}
        for token in all_tokens:
            bot_id = token.bot_id
            if bot_id not in tokens_by_bot:
                tokens_by_bot[bot_id] = []
            tokens_by_bot[bot_id].append(token)
        
        # Format token list
        tokens_text = "📋 **Your Active Tokens**\n\n"
        
        for bot_id, tokens in tokens_by_bot.items():
            bot = await db_manager.get_bot(bot_id)
            bot_name = bot.name if bot else f"Bot {bot_id}"
            
            tokens_text += f"🤖 **{bot_name}**\n"
            
            for i, token in enumerate(tokens, 1):
                expires_in = format_expiry_time(token.expires_at)
                token_type_display = get_token_type_display(token.type)
                
                tokens_text += f"  {i}. {token_type_display}\n"
                tokens_text += f"     Expires in: {expires_in}\n"
                tokens_text += f"     Used: {token.usage_count} times\n"
                
                # Show partial token for identification
                partial_token = f"{token.token[:8]}...{token.token[-8:]}"
                tokens_text += f"     Token: `{partial_token}`\n\n"
        
        # Add action buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Generate More", callback_data="verify_start")],
            [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
            [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
        ])
        
        await message.edit_text(tokens_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Error listing user tokens: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def validate_token_request(bot_id: str, user_id: int, token: str) -> dict:
    """Validate token request from main bots"""
    try:
        # Validate token in database
        is_valid = await db_manager.validate_token(bot_id, user_id, token)
        
        if is_valid:
            # Get token details
            tokens = await db_manager.get_user_tokens(user_id, bot_id)
            matching_token = None
            
            for t in tokens:
                if t.token == token:
                    matching_token = t
                    break
            
            if matching_token:
                return {
                    "is_valid": True,
                    "user_id": user_id,
                    "token_type": matching_token.type.value,
                    "expires_at": matching_token.expires_at.isoformat(),
                    "message": "Token is valid"
                }
        
        return {
            "is_valid": False,
            "message": "Invalid or expired token"
        }
        
    except Exception as e:
        logger.error(f"❌ Error validating token request: {e}")
        return {
            "is_valid": False,
            "message": "Token validation error"
        }


# Callback handlers for token operations
async def token_operations_callback(client: Client, callback_query: CallbackQuery):
    """Handle token operation callbacks"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if data == "list_tokens":
            await list_user_tokens(user_id, callback_query.message)
        elif data.startswith("revoke_token:"):
            token_id = data.split(":")[1]
            await revoke_user_token(user_id, token_id, callback_query.message)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in token operations callback: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)


# Create handlers
token_operations_callback_handler = CallbackQueryHandler(
    token_operations_callback,
    filters.regex(r"^(list_tokens|revoke_token:)")
)
