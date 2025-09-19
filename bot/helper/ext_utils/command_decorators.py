#!/usr/bin/env python3
"""
Command Access Decorators
Provides decorators for easy command access control
"""

import functools
import logging
from typing import Callable, Optional
from pyrogram import Client
from pyrogram.types import Message

from bot import OWNER_ID, user_data
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.ext_utils.command_manager import command_manager
from bot.helper.ext_utils.auth_handler import is_user_authorized

logger = logging.getLogger(__name__)

def check_access(required_level: Optional[str] = None, 
                check_content: bool = True,
                custom_message: Optional[str] = None):
    """
    Decorator to check command access before execution
    
    Args:
        required_level: Override the configured access level for this command
        check_content: Whether to check message content for blocked keywords
        custom_message: Custom unauthorized message
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(client: Client, message: Message):
            try:
                user = message.from_user
                if not user:
                    return
                
                user_id = user.id
                command = message.command[0] if message.command else ""
                message_text = message.text or message.caption or ""
                
                # Determine user access level
                is_owner = user_id == OWNER_ID
                is_sudo = user_id in user_data and user_data[user_id].get("is_sudo", False)
                
                # Check auth bot authorization for non-sudo/owner users
                is_authorized_user = False
                if not is_owner and not is_sudo:
                    try:
                        is_authorized_user = await is_user_authorized(user_id)
                    except Exception as e:
                        logger.error(f"Auth check failed for user {user_id}: {e}")
                        is_authorized_user = False
                
                # Perform access check
                if required_level:
                    # Use custom required level
                    user_access_level = command_manager.get_user_access_level(
                        user_id, is_sudo, is_owner, is_authorized_user
                    )
                    is_allowed = command_manager.is_command_allowed(command, user_access_level)
                    reason = "insufficient_access_level" if not is_allowed else None
                else:
                    # Use configured access level
                    is_allowed, reason = command_manager.check_command_access(
                        command, message_text if check_content else "",
                        user_id, is_sudo, is_owner, is_authorized_user
                    )
                
                if not is_allowed:
                    # Send unauthorized message
                    if custom_message:
                        await sendMessage(message, custom_message)
                    else:
                        msg, keyboard = command_manager.get_unauthorized_message()
                        await sendMessage(message, msg, keyboard)
                    
                    # Log blocked attempt
                    if command_manager._config.get('settings', {}).get('log_blocked_attempts', True):
                        logger.warning(
                            f"🚫 Blocked command: /{command} from user {user_id} "
                            f"(@{user.username or 'N/A'}) - Reason: {reason}"
                        )
                    return
                
                # Command is allowed, execute original function
                return await func(client, message)
                
            except Exception as e:
                logger.error(f"Error in access check decorator: {e}")
                # On error, still try to execute the command to avoid breaking bot
                return await func(client, message)
        
        return wrapper
    return decorator

# Convenience decorators for specific access levels
def public_access(func: Callable):
    """Decorator for public commands (no authorization required)"""
    return check_access(required_level="public")(func)

def authorized_access(func: Callable):
    """Decorator for commands requiring authorization"""
    return check_access(required_level="authorized")(func)

def sudo_access(func: Callable):
    """Decorator for sudo-only commands"""
    return check_access(required_level="sudo")(func)

def owner_access(func: Callable):
    """Decorator for owner-only commands"""
    return check_access(required_level="owner")(func)

def check_content(func: Callable):
    """Decorator to check message content for unauthorized users"""
    return check_access(check_content=True)(func)

def no_content_check(func: Callable):
    """Decorator to skip content checking"""
    return check_access(check_content=False)(func)

# Alternative function-based approach for complex scenarios
async def verify_command_access(client: Client, message: Message, 
                              required_level: Optional[str] = None) -> bool:
    """
    Function-based access verification
    Returns True if access is granted, False otherwise
    """
    try:
        user = message.from_user
        if not user:
            return False
        
        user_id = user.id
        command = message.command[0] if message.command else ""
        message_text = message.text or message.caption or ""
        
        # Determine user access level
        is_owner = user_id == OWNER_ID
        is_sudo = user_id in user_data and user_data[user_id].get("is_sudo", False)
        
        # Check auth bot authorization
        is_authorized_user = False
        if not is_owner and not is_sudo:
            try:
                is_authorized_user = await is_user_authorized(user_id)
            except Exception as e:
                logger.error(f"Auth check failed for user {user_id}: {e}")
                is_authorized_user = False
        
        # Perform access check
        if required_level:
            user_access_level = command_manager.get_user_access_level(
                user_id, is_sudo, is_owner, is_authorized_user
            )
            is_allowed = command_manager.is_command_allowed(command, user_access_level)
        else:
            is_allowed, _ = command_manager.check_command_access(
                command, message_text, user_id, is_sudo, is_owner, is_authorized_user
            )
        
        if not is_allowed:
            # Send unauthorized message
            msg, keyboard = command_manager.get_unauthorized_message()
            await sendMessage(message, msg, keyboard)
        
        return is_allowed
        
    except Exception as e:
        logger.error(f"Error in verify_command_access: {e}")
        return True  # Allow on error to avoid breaking bot