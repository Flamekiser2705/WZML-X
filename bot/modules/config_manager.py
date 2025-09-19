#!/usr/bin/env python3
"""
Command Configuration Management Commands
Admin commands to manage command access configuration via Telegram
"""

import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message

from bot import bot, OWNER_ID
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.command_manager import command_manager

logger = logging.getLogger(__name__)

@bot.on_message(filters.command(BotCommands.ConfigCommand) & CustomFilters.sudo)
async def config_command(client, message: Message):
    """
    Manage command access configuration
    
    Usage:
    /config - Show current configuration
    /config reload - Reload configuration from file
    /config add <command> <level> - Add command to access level
    /config remove <command> - Remove command from all levels
    /config move <command> <new_level> - Move command to different level
    /config list [level] - List commands by access level
    /config validate - Validate configuration
    """
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        # Show current configuration
        summary = command_manager.get_config_summary()
        await sendMessage(message, summary)
        return
    
    action = args[0].lower()
    
    if action == "reload":
        await handle_config_reload(message)
    
    elif action == "add" and len(args) >= 3:
        command_name = args[1]
        access_level = args[2]
        await handle_config_add(message, command_name, access_level)
    
    elif action == "remove" and len(args) >= 2:
        command_name = args[1]
        await handle_config_remove(message, command_name)
    
    elif action == "move" and len(args) >= 3:
        command_name = args[1]
        new_level = args[2]
        await handle_config_move(message, command_name, new_level)
    
    elif action == "list":
        access_level = args[1] if len(args) > 1 else None
        await handle_config_list(message, access_level)
    
    elif action == "validate":
        await handle_config_validate(message)
    
    else:
        help_text = """
🔧 **Command Configuration Help**

**Usage:**
• `/config` - Show current configuration
• `/config reload` - Reload from file
• `/config add <cmd> <level>` - Add command
• `/config remove <cmd>` - Remove command
• `/config move <cmd> <level>` - Move command
• `/config list [level]` - List commands
• `/config validate` - Check configuration

**Access Levels:**
• `public` - Anyone can use
• `authorized` - Requires auth bot verification
• `sudo` - Sudo users only
• `owner` - Owner only

**Examples:**
• `/config add mirror authorized`
• `/config move leech sudo`
• `/config remove outdated_cmd`
• `/config list authorized`
"""
        await sendMessage(message, help_text)

async def handle_config_reload(message: Message):
    """Handle configuration reload"""
    try:
        if command_manager.reload_config():
            msg = command_manager._config.get('messages', {}).get(
                'config_reloaded',
                "🔄 Command configuration reloaded successfully!"
            )
            await sendMessage(message, msg)
        else:
            await sendMessage(message, "❌ Failed to reload configuration. Check logs for details.")
    except Exception as e:
        logger.error(f"Config reload error: {e}")
        await sendMessage(message, f"❌ Error reloading config: {str(e)}")

async def handle_config_add(message: Message, command_name: str, access_level: str):
    """Handle adding command to access level"""
    try:
        if access_level not in command_manager.access_hierarchy:
            await sendMessage(
                message, 
                f"❌ Invalid access level: {access_level}\n"
                f"Valid levels: {', '.join(command_manager.access_hierarchy.keys())}"
            )
            return
        
        if command_manager.add_command(command_name, access_level):
            msg = command_manager._config.get('messages', {}).get(
                'command_added',
                "✅ Command '{}' added to '{}' access level."
            ).format(command_name, access_level)
            await sendMessage(message, msg)
        else:
            await sendMessage(message, f"❌ Failed to add command '{command_name}'")
    
    except Exception as e:
        logger.error(f"Config add error: {e}")
        await sendMessage(message, f"❌ Error adding command: {str(e)}")

async def handle_config_remove(message: Message, command_name: str):
    """Handle removing command from all levels"""
    try:
        if command_manager.remove_command(command_name):
            msg = command_manager._config.get('messages', {}).get(
                'command_removed',
                "❌ Command '{}' removed from all access levels."
            ).format(command_name)
            await sendMessage(message, msg)
        else:
            await sendMessage(message, f"❌ Command '{command_name}' not found in configuration")
    
    except Exception as e:
        logger.error(f"Config remove error: {e}")
        await sendMessage(message, f"❌ Error removing command: {str(e)}")

async def handle_config_move(message: Message, command_name: str, new_level: str):
    """Handle moving command to different access level"""
    try:
        if new_level not in command_manager.access_hierarchy:
            await sendMessage(
                message,
                f"❌ Invalid access level: {new_level}\n"
                f"Valid levels: {', '.join(command_manager.access_hierarchy.keys())}"
            )
            return
        
        # Get current level
        old_level = command_manager.get_command_access_level(command_name)
        
        if command_manager.move_command(command_name, new_level):
            msg = command_manager._config.get('messages', {}).get(
                'command_moved',
                "🔄 Command '{}' moved from '{}' to '{}' access level."
            ).format(command_name, old_level, new_level)
            await sendMessage(message, msg)
        else:
            await sendMessage(message, f"❌ Failed to move command '{command_name}'")
    
    except Exception as e:
        logger.error(f"Config move error: {e}")
        await sendMessage(message, f"❌ Error moving command: {str(e)}")

async def handle_config_list(message: Message, access_level: str = None):
    """Handle listing commands by access level"""
    try:
        command_list = command_manager.get_command_list(access_level)
        
        if not command_list:
            await sendMessage(message, "❌ No commands found")
            return
        
        response = "📋 **Command List**\n\n"
        
        for level, commands in command_list.items():
            if commands:
                response += f"🔸 **{level.title()}** ({len(commands)}):\n"
                # Group commands in rows of 4
                cmd_rows = [commands[i:i+4] for i in range(0, len(commands), 4)]
                for row in cmd_rows:
                    response += f"  `{' | '.join(row)}`\n"
                response += "\n"
            else:
                response += f"🔸 **{level.title()}**: No commands\n\n"
        
        await sendMessage(message, response)
    
    except Exception as e:
        logger.error(f"Config list error: {e}")
        await sendMessage(message, f"❌ Error listing commands: {str(e)}")

async def handle_config_validate(message: Message):
    """Handle configuration validation"""
    try:
        issues = command_manager.validate_config()
        
        if not issues:
            response = "✅ **Configuration Validation Passed**\n\n"
            response += f"📊 **Stats:**\n"
            response += f"• Total Commands: {len(command_manager._command_map)}\n"
            response += f"• Access Levels: {len(command_manager.access_hierarchy)}\n"
            response += f"• Blocked Keywords: {len(command_manager._blocked_keywords)}\n"
        else:
            response = "❌ **Configuration Validation Failed**\n\n"
            response += "**Issues Found:**\n"
            for i, issue in enumerate(issues, 1):
                response += f"{i}. {issue}\n"
        
        await sendMessage(message, response)
    
    except Exception as e:
        logger.error(f"Config validate error: {e}")
        await sendMessage(message, f"❌ Error validating config: {str(e)}")

# Command to check specific command access (for testing)
@bot.on_message(filters.command("checkaccess") & CustomFilters.sudo)
async def check_access_command(client, message: Message):
    """
    Check access level for a specific command
    Usage: /checkaccess <command> [user_id]
    """
    args = message.text.split()[1:]
    
    if not args:
        await sendMessage(message, "❌ Usage: `/checkaccess <command> [user_id]`")
        return
    
    command_name = args[0]
    target_user_id = int(args[1]) if len(args) > 1 else message.from_user.id
    
    try:
        # Get command access level
        required_level = command_manager.get_command_access_level(command_name)
        
        # Determine user access level (simplified for testing)
        is_owner = target_user_id == OWNER_ID
        # Check if user is sudo (import from appropriate module or use your existing method)
        try:
            from bot.helper.ext_utils.db_handler import DbManger
            is_sudo = await DbManger().user_data.find_one({"_id": target_user_id, "is_sudo": True}) is not None
        except:
            is_sudo = False  # Fallback if database check fails
        
        user_access_level = command_manager.get_user_access_level(
            target_user_id, is_sudo, is_owner, False
        )
        
        # Check if allowed
        is_allowed = command_manager.is_command_allowed(command_name, user_access_level)
        
        response = f"🔍 **Access Check for /{command_name}**\n\n"
        response += f"**User ID:** `{target_user_id}`\n"
        response += f"**User Access Level:** `{user_access_level}`\n"
        response += f"**Required Level:** `{required_level}`\n"
        response += f"**Access Granted:** {'✅ Yes' if is_allowed else '❌ No'}\n"
        
        await sendMessage(message, response)
    
    except Exception as e:
        logger.error(f"Check access error: {e}")
        await sendMessage(message, f"❌ Error checking access: {str(e)}")