#!/usr/bin/env python3
"""
Universal Command Access Manager
Manages command access levels and authorization across the bot
Designed to be portable and reusable across different bots
"""

import json
import logging
import os
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

class CommandAccessManager:
    """
    Universal Command Access Manager
    
    Features:
    - Multiple access levels (public, authorized, sudo, owner)
    - JSON-based configuration
    - Runtime reloading without restart
    - URL/media content detection for unauthorized users
    - Admin commands for configuration management
    - Portable design for multiple bots
    """
    
    def __init__(self, config_path: str = None, auth_bot_username: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), 'command_config.json'
        )
        self.auth_bot_username = auth_bot_username or os.getenv('AUTH_BOT_USERNAME', 'SoulKaizer_bot').replace('@', '')
        
        # Access level hierarchy (higher number = more permissions)
        self.access_hierarchy = {
            'public': 0,
            'authorized': 1, 
            'sudo': 2,
            'owner': 3
        }
        
        # Cached configuration
        self._config = {}
        self._command_map = {}  # command -> access_level
        self._blocked_keywords = set()
        
        # Load initial configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"Command config file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            # Build command mapping for fast lookup
            self._build_command_map()
            
            # Cache blocked keywords
            self._blocked_keywords = set(
                self._config.get('settings', {}).get('blocked_keywords', [])
            )
            
            logger.info(f"✅ Command configuration loaded: {len(self._command_map)} commands")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load command config: {e}")
            return False
    
    def _build_command_map(self):
        """Build command to access level mapping"""
        self._command_map = {}
        
        for access_level, commands in self._config.get('command_access', {}).items():
            for command in commands:
                # Remove leading slash if present
                clean_command = command.lstrip('/')
                self._command_map[clean_command] = access_level
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Update metadata
            self._config.setdefault('metadata', {})
            self._config['metadata'].update({
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'total_commands': len(self._command_map)
            })
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Command configuration saved")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save command config: {e}")
            return False
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        if self.load_config():
            logger.info("🔄 Command configuration reloaded")
            return True
        return False
    
    def get_command_access_level(self, command: str) -> str:
        """Get access level required for a command"""
        clean_command = command.lstrip('/')
        return self._command_map.get(
            clean_command,
            self._config.get('settings', {}).get('default_access_level', 'authorized')
        )
    
    def get_user_access_level(self, user_id: int, is_sudo: bool = False, 
                            is_owner: bool = False, is_authorized: bool = False) -> str:
        """Determine user's access level"""
        if is_owner:
            return 'owner'
        elif is_sudo:
            return 'sudo'
        elif is_authorized:
            return 'authorized'
        else:
            return 'public'
    
    def is_command_allowed(self, command: str, user_access_level: str) -> bool:
        """Check if user can execute command based on access level"""
        required_level = self.get_command_access_level(command)
        
        user_level_value = self.access_hierarchy.get(user_access_level, 0)
        required_level_value = self.access_hierarchy.get(required_level, 1)
        
        return user_level_value >= required_level_value
    
    def contains_blocked_content(self, text: str) -> bool:
        """Check if text contains blocked keywords (URLs, etc.)"""
        if not text or not self._config.get('settings', {}).get('check_args_for_auth', True):
            return False
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self._blocked_keywords)
    
    def check_command_access(self, command: str, message_text: str, user_id: int,
                           is_sudo: bool = False, is_owner: bool = False, 
                           is_authorized: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive command access check
        
        Returns:
            (is_allowed, reason_if_blocked)
        """
        user_access_level = self.get_user_access_level(user_id, is_sudo, is_owner, is_authorized)
        
        # Check command access level
        if not self.is_command_allowed(command, user_access_level):
            return False, "insufficient_access_level"
        
        # For non-authorized users, check for blocked content
        if user_access_level == 'public' and self.contains_blocked_content(message_text):
            return False, "blocked_content_detected"
        
        return True, None
    
    def get_unauthorized_message(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Get unauthorized access message and markup"""
        message = self._config.get('messages', {}).get(
            'unauthorized',
            "🚫 **Access Denied**\n\nYou are not authorized to use this command.\nPlease verify your account to get access."
        )
        
        button_text = self._config.get('messages', {}).get(
            'verify_button_text',
            "🔐 Verify Account"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text, url=f"https://t.me/{self.auth_bot_username}")]
        ])
        
        return message, keyboard
    
    def add_command(self, command: str, access_level: str) -> bool:
        """Add command to specific access level"""
        if access_level not in self.access_hierarchy:
            return False
        
        clean_command = command.lstrip('/')
        
        # Remove from other levels first
        self.remove_command(clean_command)
        
        # Add to specified level
        self._config.setdefault('command_access', {}).setdefault(access_level, [])
        if clean_command not in self._config['command_access'][access_level]:
            self._config['command_access'][access_level].append(clean_command)
            self._build_command_map()
            return self.save_config()
        
        return True
    
    def remove_command(self, command: str) -> bool:
        """Remove command from all access levels"""
        clean_command = command.lstrip('/')
        removed = False
        
        for access_level, commands in self._config.get('command_access', {}).items():
            if clean_command in commands:
                commands.remove(clean_command)
                removed = True
        
        if removed:
            self._build_command_map()
            self.save_config()
        
        return removed
    
    def move_command(self, command: str, new_access_level: str) -> bool:
        """Move command to different access level"""
        if new_access_level not in self.access_hierarchy:
            return False
        
        # Remove and add
        self.remove_command(command)
        return self.add_command(command, new_access_level)
    
    def get_command_list(self, access_level: str = None) -> Dict[str, List[str]]:
        """Get list of commands by access level"""
        if access_level:
            return {access_level: self._config.get('command_access', {}).get(access_level, [])}
        return self._config.get('command_access', {})
    
    def get_config_summary(self) -> str:
        """Get formatted configuration summary"""
        summary = "📋 **Command Access Configuration**\n\n"
        
        for level in ['public', 'authorized', 'sudo', 'owner']:
            commands = self._config.get('command_access', {}).get(level, [])
            summary += f"🔸 **{level.title()}** ({len(commands)}): {', '.join(commands) if commands else 'None'}\n"
        
        summary += f"\n⚙️ **Settings:**\n"
        summary += f"• Default Access: {self._config.get('settings', {}).get('default_access_level', 'authorized')}\n"
        summary += f"• Check Args: {self._config.get('settings', {}).get('check_args_for_auth', True)}\n"
        summary += f"• Blocked Keywords: {len(self._blocked_keywords)}\n"
        
        return summary
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required sections
        if 'command_access' not in self._config:
            issues.append("Missing 'command_access' section")
        
        if 'settings' not in self._config:
            issues.append("Missing 'settings' section")
        
        # Check access levels
        for level in self._config.get('command_access', {}):
            if level not in self.access_hierarchy:
                issues.append(f"Invalid access level: {level}")
        
        # Check for duplicate commands
        all_commands = []
        for commands in self._config.get('command_access', {}).values():
            all_commands.extend(commands)
        
        duplicates = [cmd for cmd in set(all_commands) if all_commands.count(cmd) > 1]
        if duplicates:
            issues.append(f"Duplicate commands found: {', '.join(duplicates)}")
        
        return issues

# Global instance
command_manager = CommandAccessManager()

# Convenience functions for easy integration
def check_command_access(command: str, message_text: str, user_id: int,
                        is_sudo: bool = False, is_owner: bool = False, 
                        is_authorized: bool = False) -> Tuple[bool, Optional[str]]:
    """Check if user can execute command"""
    return command_manager.check_command_access(
        command, message_text, user_id, is_sudo, is_owner, is_authorized
    )

def get_unauthorized_message() -> Tuple[str, InlineKeyboardMarkup]:
    """Get unauthorized message and keyboard"""
    return command_manager.get_unauthorized_message()

def reload_command_config() -> bool:
    """Reload command configuration"""
    return command_manager.reload_config()

def is_command_allowed(command: str, user_access_level: str) -> bool:
    """Simple command access check"""
    return command_manager.is_command_allowed(command, user_access_level)