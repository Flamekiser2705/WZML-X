# Universal Command Access Management System

## 🎯 Overview
A comprehensive, JSON-based command access control system for the Mirror Leech Bot that provides centralized management of command permissions without modifying core bot functionality.

## 🏗️ System Architecture

### Core Components

1. **`command_config.json`** - Centralized configuration file
2. **`command_manager.py`** - Core access control logic
3. **`command_decorators.py`** - Easy-to-use decorators
4. **`config_manager.py`** - Admin Telegram commands

### Key Features

✅ **Runtime Configuration** - No bot restart needed  
✅ **JSON-Based Config** - Easy to edit and maintain  
✅ **Four Access Levels** - Public, Authorized, Sudo, Owner  
✅ **Decorator Pattern** - Minimal code changes  
✅ **Admin Commands** - Telegram-based management  
✅ **Keyword Blocking** - Prevent sensitive content  
✅ **Custom Messages** - Configurable user feedback  
✅ **Audit Trail** - Clear access documentation  

## 📁 File Structure
```
bot/
├── modules/
│   ├── config_manager.py          # Admin management commands
│   └── [other modules]            # Updated with decorators
├── helper/
│   ├── ext_utils/
│   │   ├── command_manager.py     # Core access control
│   │   ├── command_decorators.py  # Decorator functions  
│   │   ├── command_config.json    # Configuration file
│   │   └── auth_handler.py        # Existing auth integration
│   └── telegram_helper/
│       ├── bot_commands.py        # Updated with ConfigCommand
│       └── filters.py             # Legacy filters (optional)
```

## 🔧 Configuration Format

### `command_config.json`
```json
{
  "access_levels": {
    "public": ["start", "help", "ping"],
    "authorized": ["mirror", "clone", "leech", "status"],
    "sudo": ["users", "broadcast", "stats"],
    "owner": ["shell", "eval", "restart"]
  },
  "blocked_keywords": ["eval", "exec", "shell"],
  "settings": {
    "show_auth_button": true,
    "auto_reload": true,
    "strict_mode": false,
    "case_sensitive": false
  },
  "messages": {
    "unauthorized": "❌ **Unauthorized Access**\n\nThis command requires authorization. Please contact an admin or use our auth bot to gain access.\n\n🔗 **Auth Bot**: @YourAuthBot",
    "blocked_keyword": "❌ **Blocked Content**\n\nYour message contains blocked keywords.",
    "config_reloaded": "🔄 **Configuration Reloaded**\n\nCommand access settings have been updated successfully.",
    "command_added": "✅ **Command Added**\n\nCommand '{0}' has been added to '{1}' access level.",
    "command_removed": "❌ **Command Removed**\n\nCommand '{0}' has been removed from all access levels.",
    "command_moved": "🔄 **Command Moved**\n\nCommand '{0}' moved from '{1}' to '{2}' access level."
  }
}
```

## 🎨 Usage Examples

### Basic Command Protection
```python
from bot.helper.ext_utils.command_decorators import check_access

@bot.on_message(filters.command(BotCommands.MirrorCommand))
@check_access("mirror")
async def mirror(client, message):
    # Existing mirror logic unchanged
    await mirror_leech(client, message)
```

### Advanced Access Control
```python
@bot.on_message(filters.command(BotCommands.LeechCommand))
@check_access("leech", allow_media=True, custom_message="Premium feature")
async def leech(client, message):
    # Custom access control with media support
    await mirror_leech(client, message, is_leech=True)
```

### Multiple Access Levels
```python
# Sudo access only
@sudo_access
async def admin_command(client, message):
    pass

# Owner access only  
@owner_access
async def owner_command(client, message):
    pass

# Authorized users only
@authorized_access
async def user_command(client, message):
    pass
```

## 🛠️ Admin Commands

### Configuration Management
```bash
/config                     # Show current configuration
/config reload              # Reload from file
/config add mirror sudo     # Add command to access level
/config remove oldcmd       # Remove command
/config move mirror owner   # Move command to different level
/config list authorized     # List commands by access level
/config validate           # Check configuration
```

### Access Testing
```bash
/checkaccess mirror 123456789  # Test specific user access
```

## 🔄 Migration Process

### Step 1: Remove Old Filters
```python
# OLD
from bot.helper.telegram_helper.filters import CustomFilters

@bot.on_message(filters.command(BotCommands.MirrorCommand) & CustomFilters.authorized)
async def mirror(client, message):
    pass
```

### Step 2: Add New Decorators
```python
# NEW
from bot.helper.ext_utils.command_decorators import check_access

@bot.on_message(filters.command(BotCommands.MirrorCommand))
@check_access("mirror")
async def mirror(client, message):
    pass
```

### Step 3: Update Configuration
```json
{
  "access_levels": {
    "authorized": ["mirror", "clone", "leech"]
  }
}
```

## 📊 Access Level Hierarchy

1. **Public** - Anyone can use (no restrictions)
2. **Authorized** - Requires auth bot verification  
3. **Sudo** - Admin users only
4. **Owner** - Bot owner only

Higher levels inherit lower level permissions.

## 🔐 Security Features

- **Keyword Blocking** - Prevent sensitive commands in messages
- **Strict Mode** - Enhanced security checks
- **URL Detection** - Block unauthorized media/links
- **Audit Logging** - Track access attempts
- **Real-time Updates** - No restart required

## 🎛️ Advanced Configuration

### Custom Access Logic
```python
@check_access("mirror", allow_media=True, require_sudo=False)
async def mirror_with_media(client, message):
    # Allow media files for this command
    pass
```

### Conditional Access
```python
@check_access("premium_feature", custom_check=lambda user_id: is_premium_user(user_id))
async def premium_command(client, message):
    # Custom access validation
    pass
```

## 📈 Benefits

### For Administrators
- **Centralized Control** - One place to manage all access
- **Runtime Changes** - Modify access without downtime
- **Easy Auditing** - Clear documentation of permissions
- **Telegram Management** - Control via bot commands

### For Developers  
- **Clean Code** - Remove complex filter chains
- **Consistent API** - Standardized access patterns
- **Easy Integration** - Minimal code changes
- **Maintainable** - Separated concerns

### For Users
- **Clear Messages** - Understand access requirements
- **Auth Integration** - Direct links to auth bot
- **Consistent Experience** - Standardized responses

## 🚀 Future Enhancements

- **Time-based Access** - Temporary permissions
- **Group-specific Rules** - Different access per chat
- **Usage Limits** - Rate limiting per user
- **Access Analytics** - Usage statistics
- **API Integration** - External access management

## 🔧 Troubleshooting

### Common Issues

1. **Commands Not Working**
   - Check command_config.json syntax
   - Verify command names match exactly
   - Reload configuration

2. **Access Denied Errors**
   - Check user authorization status
   - Verify access level configuration
   - Test with /checkaccess command

3. **Configuration Changes Not Applied**
   - Use `/config reload` command
   - Check file permissions
   - Verify JSON syntax

### Debug Commands
```bash
/config validate           # Check configuration
/checkaccess cmd user_id   # Test user access
/config list              # View all commands
```

## 📝 Changelog

### v1.0.0 - Initial Release
- JSON-based configuration system
- Four-tier access control
- Decorator pattern implementation
- Admin management commands
- Runtime configuration updates
- Auth bot integration
- Comprehensive documentation

## 🤝 Contributing

1. Test with existing commands
2. Report integration issues
3. Suggest feature improvements
4. Document usage patterns
5. Create integration guides

## 📄 License

This command management system is part of the Mirror Leech Bot project and follows the same licensing terms.

---

**Ready for Production** ✅  
**Tested Integration** ✅  
**Admin Tools** ✅  
**Documentation** ✅