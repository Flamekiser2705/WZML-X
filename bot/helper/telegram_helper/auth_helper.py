#!/usr/bin/env python3
"""
Authorization Helper Module
Provides decorators and functions for handling unauthorized users
"""

from functools import wraps
from bot.helper.telegram_helper.unauthorized_message import send_unauthorized_message
from bot.helper.telegram_helper.filters import CustomFilters

def require_authorization(func):
    """
    Decorator for command handlers that require authorization
    Automatically sends unauthorized message if user is not authorized
    
    Usage:
    @require_authorization
    async def my_command(client, message):
        # Command code here
        pass
    """
    @wraps(func)
    async def wrapper(client, message):
        # Check if user is authorized
        custom_filter = CustomFilters()
        if await custom_filter.authorized_user(client, message):
            return await func(client, message)
        else:
            await send_unauthorized_message(message)
            return
    
    return wrapper

async def check_auth_or_send_message(client, message):
    """
    Helper function to check authorization and send message if unauthorized
    
    Returns:
        bool: True if authorized, False if unauthorized (message already sent)
    """
    custom_filter = CustomFilters()
    if await custom_filter.authorized_user(client, message):
        return True
    else:
        await send_unauthorized_message(message)
        return False