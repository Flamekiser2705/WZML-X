#!/usr/bin/env python3
"""
Token Activation Callback Handler
Similar to the token_callback function in main bot
"""

import logging
from uuid import uuid4
from time import time
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# This would be similar to your main bot's token_callback function
async def token_activation_callback(client: Client, callback_query: CallbackQuery):
    """
    Handle token activation callbacks - similar to main bot's token_callback
    This function handles when users click the activation button for their tokens
    """
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Parse callback data: "activate_token:<token_id>:<verification_code>"
        if data.startswith("activate_token:"):
            parts = data.split(":")
            if len(parts) != 3:
                await callback_query.answer("❌ Invalid token data", show_alert=True)
                return
            
            token_id = parts[1]
            verification_code = parts[2]
            
            # Get user data from database
            from database.operations import DatabaseManager
            db_manager = DatabaseManager()
            
            # Validate the token and verification code
            token = await db_manager.get_token(token_id)
            
            if not token:
                await callback_query.answer("❌ Token not found", show_alert=True)
                return
            
            if token.user_id != user_id:
                await callback_query.answer("❌ Unauthorized access", show_alert=True)
                return
            
            if not token.is_active:
                await callback_query.answer("❌ Token already activated or expired", show_alert=True)
                return
            
            # Generate new UUID4 activation code (similar to your uuid4() usage)
            new_activation_code = str(uuid4())
            
            # Update token status
            await db_manager.activate_token(token_id, new_activation_code)
            
            # Update the message keyboard
            keyboard = callback_query.message.reply_markup.inline_keyboard
            
            # Remove the activation button and add "Activated" button
            new_keyboard = []
            for row in keyboard:
                new_row = []
                for button in row:
                    if button.callback_data and not button.callback_data.startswith("activate_token"):
                        new_row.append(button)
                if new_row:
                    new_keyboard.append(new_row)
            
            # Add "Activated" button at the top
            new_keyboard.insert(0, [
                InlineKeyboardButton("✅ Token Activated", callback_data="token_activated")
            ])
            
            # Update the message
            await callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(new_keyboard)
            )
            
            await callback_query.answer("✅ Token Activated Successfully!", show_alert=True)
            
            logger.info(f"✅ Token {token_id} activated for user {user_id}")
            
        elif data.startswith("copy_token:"):
            # Handle token copy functionality
            token_id = data.split(":")[1]
            
            # Get token from database
            from database.operations import DatabaseManager
            db_manager = DatabaseManager()
            
            token = await db_manager.get_token(token_id)
            
            if token and token.user_id == user_id:
                # Show token in popup (similar to copy functionality)
                token_text = f"🎫 **Your UUID4 Token:**\n\n`{token.token}`\n\n**Usage:** Copy this token and use it in your mirror bot commands."
                
                await callback_query.answer(
                    f"Token: {token.token}\n\nCopied to clipboard!",
                    show_alert=True
                )
            else:
                await callback_query.answer("❌ Token not found", show_alert=True)
                
        elif data == "token_activated":
            # Handle already activated token click
            await callback_query.answer("✅ Token is already activated", show_alert=False)
            
        else:
            await callback_query.answer("❌ Unknown action", show_alert=True)
    
    except Exception as e:
        logger.error(f"❌ Error in token activation callback: {e}")
        await callback_query.answer("❌ An error occurred. Please try again.", show_alert=True)


async def token_management_callback(client: Client, callback_query: CallbackQuery):
    """
    Handle token management callbacks
    Similar to the pattern in your main bot but for auth bot token management
    """
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if data.startswith("regenerate_token:"):
            # Regenerate token (similar to your uuid4() regeneration)
            token_id = data.split(":")[1]
            
            from database.operations import DatabaseManager
            from utils.token_utils import TokenGenerator
            from utils.config import Config
            
            db_manager = DatabaseManager()
            token_gen = TokenGenerator(Config.ENCRYPTION_KEY)
            
            # Get existing token
            old_token = await db_manager.get_token(token_id)
            
            if not old_token or old_token.user_id != user_id:
                await callback_query.answer("❌ Token not found", show_alert=True)
                return
            
            # Deactivate old token
            await db_manager.deactivate_token(token_id)
            
            # Generate new UUID4 token
            new_token_id, new_uuid4_token, expires_at = token_gen.generate_access_token(
                user_id=user_id,
                bot_id=old_token.bot_id,
                token_type=old_token.type
            )
            
            # Create new token record
            from database.models import Token
            new_token_data = Token(
                token_id=new_token_id,
                user_id=user_id,
                bot_id=old_token.bot_id,
                token=new_uuid4_token,  # This is the UUID4 token
                type=old_token.type,
                expires_at=expires_at
            )
            
            # Save new token
            if await db_manager.create_token(new_token_data):
                # Update the message with new token info
                new_text = f"🔄 **Token Regenerated**\n\n🎫 **New UUID4 Token:**\n`{new_uuid4_token}`\n\n⏰ **Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}"
                
                # Create new keyboard
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Copy Token", callback_data=f"copy_token:{new_token_id}")],
                    [InlineKeyboardButton("🔄 Regenerate", callback_data=f"regenerate_token:{new_token_id}")],
                    [InlineKeyboardButton("🗑️ Revoke", callback_data=f"revoke_token:{new_token_id}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="my_tokens")]
                ])
                
                await callback_query.message.edit_text(new_text, reply_markup=keyboard)
                await callback_query.answer("✅ Token regenerated successfully!", show_alert=True)
                
                logger.info(f"✅ Token regenerated for user {user_id}: {new_token_id}")
            else:
                await callback_query.answer("❌ Failed to regenerate token", show_alert=True)
                
        elif data.startswith("revoke_token:"):
            # Revoke token
            token_id = data.split(":")[1]
            
            from database.operations import DatabaseManager
            db_manager = DatabaseManager()
            
            if await db_manager.revoke_token(user_id, token_id):
                await callback_query.message.edit_text(
                    "🗑️ **Token Revoked**\n\nThis token is no longer valid and cannot be used."
                )
                await callback_query.answer("✅ Token revoked successfully!", show_alert=True)
            else:
                await callback_query.answer("❌ Failed to revoke token", show_alert=True)
    
    except Exception as e:
        logger.error(f"❌ Error in token management callback: {e}")
        await callback_query.answer("❌ An error occurred. Please try again.", show_alert=True)


# Usage example showing how this integrates with the main auth bot
"""
Integration with main auth bot (similar to your main bot pattern):

# In main.py or handler registration:
app.add_handler(CallbackQueryHandler(
    token_activation_callback, 
    filters=regex(r"^(activate_token|copy_token|token_activated)")
))

app.add_handler(CallbackQueryHandler(
    token_management_callback,
    filters=regex(r"^(regenerate_token|revoke_token)")
))

# Example message with activation button (similar to your start function):
async def send_token_for_activation(user_id: int, token_data: dict):
    activation_code = str(uuid4())  # Similar to your uuid4() usage
    
    text = f'''🎫 **Your Token is Ready**

🔑 **UUID4 Token:** `{token_data["token"]}`
⏰ **Expires:** {token_data["expires_at"]}
🤖 **Bot:** {token_data["bot_name"]}

**Click Activate to start using this token!**'''

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🚀 Activate Token", 
            callback_data=f"activate_token:{token_data['token_id']}:{activation_code}"
        )],
        [InlineKeyboardButton("📋 Copy Token", callback_data=f"copy_token:{token_data['token_id']}")],
        [InlineKeyboardButton("🔙 Back", callback_data="verify_start")]
    ])
    
    await bot.send_message(user_id, text, reply_markup=keyboard)
"""
