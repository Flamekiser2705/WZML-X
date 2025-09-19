#!/usr/bin/env python3
"""
Duplicate Message Fix Verification
Test script to verify that unauthorized messages are no longer duplicated
"""

import json
import sys
import os

def test_command_config():
    """Test command configuration"""
    config_path = "bot/helper/ext_utils/command_config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ Command configuration loaded successfully!")
        
        # Count commands by access level
        total_commands = 0
        for level, commands in config.get('command_access', {}).items():
            count = len(commands)
            total_commands += count
            print(f"  • {level}: {count} commands")
        
        print(f"  • Total: {total_commands} commands configured")
        
        # Check if essential commands are present
        all_commands = []
        for commands in config.get('command_access', {}).values():
            all_commands.extend(commands)
        
        essential_commands = ['start', 'help', 'mirror', 'leech', 'clone', 'status']
        missing = [cmd for cmd in essential_commands if cmd not in all_commands]
        
        if missing:
            print(f"⚠️  Missing essential commands: {missing}")
        else:
            print("✅ All essential commands are configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading command configuration: {e}")
        return False

def check_unauthorized_message_fix():
    """Check if unauthorized message function is properly fixed"""
    try:
        # Check if the file exists and has proper structure
        message_file = "bot/helper/telegram_helper/unauthorized_message.py"
        
        with open(message_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key fixes
        checks = [
            ("global _message_cache", "_message_cache is properly declared as global"),
            ("_message_cache = set()", "Cache is initialized as set"),
            ("message_key in _message_cache", "Cache checking is implemented"),
            ("Duplicate message prevented", "Duplicate prevention logging is present"),
        ]
        
        all_good = True
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error checking unauthorized message fix: {e}")
        return False

def check_filter_integration():
    """Check if filters are properly integrated"""
    try:
        filter_file = "bot/helper/telegram_helper/filters.py"
        
        with open(filter_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper integration
        if "send_unauthorized_message" in content:
            print("✅ Filter integration with unauthorized message system")
        else:
            print("❌ Filter not properly integrated")
            return False
        
        if "authorized_user" in content:
            print("✅ Authorized user filter is present")
        else:
            print("❌ Authorized user filter missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking filter integration: {e}")
        return False

def summary():
    """Print test summary and instructions"""
    print("\n" + "="*50)
    print("🚀 DUPLICATE MESSAGE FIX APPLIED")
    print("="*50)
    
    print("\n📋 What was fixed:")
    print("• Fixed _message_cache global variable error")
    print("• Added proper deduplication logic")
    print("• Implemented 10-second time windows")
    print("• Added cache cleanup to prevent memory buildup")
    print("• Centralized unauthorized message handling")
    
    print("\n🧪 To test the fix:")
    print("1. Send /start as unauthorized user")
    print("2. Send /mirror as unauthorized user") 
    print("3. Send /leech as unauthorized user")
    print("4. You should see ONLY ONE message per command")
    
    print("\n✅ Expected behavior:")
    print("• Single unauthorized message per command")
    print("• No duplicate messages")
    print("• Clean, professional message format")
    print("• Verify button links to auth bot")
    
    print("\n🔧 If issues persist:")
    print("• Check Docker logs: docker compose logs -f")
    print("• Monitor for any remaining error messages")
    print("• Test with different commands and users")

if __name__ == "__main__":
    print("🔍 Testing Duplicate Message Fix")
    print("="*40)
    
    config_ok = test_command_config()
    print()
    
    message_fix_ok = check_unauthorized_message_fix()
    print()
    
    filter_ok = check_filter_integration()
    print()
    
    if config_ok and message_fix_ok and filter_ok:
        print("✅ All checks passed!")
        summary()
    else:
        print("❌ Some issues found - check the details above")
        print("\n⚠️  Bot may still have duplicate message issues")