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
    Generate unauthorized message in the format shown in the screenshot
    
    Args:
        user: Pyrogram User object
    
    Returns:
        tuple: (message_text, reply_markup)
    """
    auth_bot_username = get_auth_bot_username()
    
    # Get user's username or first name
    if user and user.username:
        user_mention = f"@{user.username}"
    elif user and user.first_name:
        user_mention = user.first_name
    else:
        user_mention = "User"
    
    # Message format matching the screenshot
    message_text = f"""Hey, {user_mention},

1: Please verify your account to start using this bot.
2: You need to Start @{auth_bot_username} in DM."""
    
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

async def send_unauthorized_message(message):
    """
    Send unauthorized message and return False
    Use this in filter functions or handlers
    """
    message_text, reply_markup = generate_unauthorized_message(message.from_user)
    await message.reply_text(message_text, reply_markup=reply_markup)
    return False