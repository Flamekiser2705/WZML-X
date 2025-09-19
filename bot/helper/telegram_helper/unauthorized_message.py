#!/usr/bin/env python3
"""
Unauthorized User Message Generator
Handles message formatting for unauthorized users
"""

import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_auth_bot_username():
    """Get AUTH_BOT_USERNAME from environment or use default"""
    return os.getenv('AUTH_BOT_USERNAME', 'SoulKaizer_bot').replace('@', '')

def generate_unauthorized_message(user):
    """
    Generate unauthorized message using new command management system
    
    Args:
        user: Pyrogram User object
    
    Returns:
        tuple: (message_text, reply_markup)
    """
    # Try to get message from command management system first
    try:
        from bot.helper.ext_utils.command_manager import command_manager
        config = command_manager.get_config()
        if config and 'messages' in config and 'unauthorized' in config['messages']:
            message_text = config['messages']['unauthorized']
            
            # Create verify button if show_auth_button is enabled
            if config.get('settings', {}).get('show_auth_button', True):
                auth_bot_username = get_auth_bot_username()
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("👉 Verify", url=f"https://t.me/{auth_bot_username}")]
                ])
                return message_text, keyboard
            else:
                return message_text, None
    except Exception as e:
        print(f"Error loading command management config: {e}")
    
    # Fallback to legacy message format
    auth_bot_username = get_auth_bot_username()
    
    # Get user's username or first name
    if user and user.username:
        user_mention = f"@{user.username}"
    elif user and user.first_name:
        user_mention = user.first_name
    else:
        user_mention = "User"
    
    # Updated message format
    message_text = f"""❌ **Unauthorized Access**

Hey {user_mention},

This command requires authorization. Please contact an admin or use our auth bot to gain access.

🔗 **Auth Bot**: @{auth_bot_username}
💡 **How to get access**: Send /start to the auth bot in DM"""
    
    # Create verify button that redirects to auth bot
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👉 Verify", url=f"https://t.me/{auth_bot_username}")]
    ])
    
    return message_text, keyboard

def get_unauthorized_reply_markup():
    """Get just the reply markup for unauthorized users"""
    auth_bot_username = get_auth_bot_username()
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👉 Verify", url=f"https://t.me/{auth_bot_username}")]
    ])

# Global cache to prevent duplicate messages - Simple implementation
_message_cache = {}

async def send_unauthorized_message(message):
    """
    Send unauthorized message and return False
    Use this in filter functions or handlers
    Prevents duplicate messages within 5 seconds
    """
    import time
    
    global _message_cache
    
    current_time = time.time()
    
    # Create unique key for this message/user combination
    user_id = message.from_user.id if message.from_user else 0
    chat_id = message.chat.id
    command = ""
    
    if message.text and message.text.startswith('/'):
        command = message.text.split()[0]
    
    # Simple cache key
    cache_key = f"{user_id}_{command}"
    
    # Check if we've sent a message recently (within 5 seconds)
    if cache_key in _message_cache:
        time_diff = current_time - _message_cache[cache_key]
        if time_diff < 5:  # 5 seconds cooldown
            print(f"Duplicate message prevented for user {user_id}, command {command}")
            return False
    
    # Update cache with current time
    _message_cache[cache_key] = current_time
    
    # Simple cleanup: remove entries older than 60 seconds
    if len(_message_cache) > 100:
        cutoff_time = current_time - 60
        _message_cache = {k: v for k, v in _message_cache.items() if v > cutoff_time}
        print(f"Cache cleaned, {len(_message_cache)} entries remaining")
    
    # Send the unauthorized message
    try:
        message_text, reply_markup = generate_unauthorized_message(message.from_user)
        await message.reply_text(message_text, reply_markup=reply_markup)
        print(f"Unauthorized message sent to user {user_id} for command {command}")
    except Exception as e:
        print(f"Error sending unauthorized message: {e}")
    
    return False
    
    try:
        message_text, reply_markup = generate_unauthorized_message(message.from_user)
        await message.reply_text(message_text, reply_markup=reply_markup)
        print(f"Unauthorized message sent to user {user_id} for command {command}")
    except Exception as e:
        print(f"Error sending unauthorized message: {e}")
    
    return False