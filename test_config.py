#!/usr/bin/env python3
"""
Quick test script to verify command management system is working
"""

import sys
import os
import json

# Add the bot directory to path
sys.path.append('/app')

def test_command_config():
    """Test if the command configuration is properly loaded"""
    config_path = "bot/helper/ext_utils/command_config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ Command configuration loaded successfully!")
        print(f"📊 Total commands configured:")
        
        for level, commands in config.get('command_access', {}).items():
            print(f"  • {level}: {len(commands)} commands")
        
        # Test if common commands are present
        all_commands = []
        for commands in config.get('command_access', {}).values():
            all_commands.extend(commands)
        
        test_commands = ['mirror', 'leech', 'start', 'help']
        missing = [cmd for cmd in test_commands if cmd not in all_commands]
        
        if missing:
            print(f"⚠️  Missing commands: {missing}")
        else:
            print("✅ All essential commands are configured!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def test_auth_bot_config():
    """Test auth bot configuration"""
    config_path = "auth_bot/bot_configs.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        active_bots = [bot for bot in config.values() if bot.get('status') == 'active']
        print(f"🤖 Active auth bots: {len(active_bots)}")
        
        for bot in active_bots:
            print(f"  • {bot.get('name', 'Unknown')} (@{bot.get('username', 'N/A')})")
        
        return len(active_bots) > 0
        
    except Exception as e:
        print(f"❌ Error checking auth bot config: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Command Management System")
    print("=" * 40)
    
    config_ok = test_command_config()
    auth_ok = test_auth_bot_config()
    
    print("=" * 40)
    if config_ok and auth_ok:
        print("✅ All systems ready!")
        print("🚀 You can now restart the bot to apply changes")
    else:
        print("❌ Some issues found - check the logs above")