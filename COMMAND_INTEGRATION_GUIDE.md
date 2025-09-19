# Integration Examples for Command Management System

## 1. Applying Decorators to Existing Commands

### Before (Traditional Command Handler):
```python
@bot.on_message(filters.command(BotCommands.MirrorCommand) & CustomFilters.authorized)
async def mirror(client, message):
    # Mirror command logic
    pass
```

### After (With Command Management):
```python
from bot.helper.ext_utils.command_decorators import check_access

@bot.on_message(filters.command(BotCommands.MirrorCommand))
@check_access("mirror")
async def mirror(client, message):
    # Mirror command logic
    pass
```

## 2. Existing Command Protection Examples

### Mirror Command (bot/modules/mirror_leech.py):
```python
# Add this import at the top
from bot.helper.ext_utils.command_decorators import check_access

# Replace the filter with decorator
@bot.on_message(filters.command(BotCommands.MirrorCommand))
@check_access("mirror")
async def mirror(client, message):
    # Existing mirror logic remains unchanged
    await mirror_leech(client, message)
```

### Clone Command:
```python
@bot.on_message(filters.command(BotCommands.CloneCommand))
@check_access("clone") 
async def clone(client, message):
    # Existing clone logic
    pass
```

### Status Command:
```python
@bot.on_message(filters.command(BotCommands.StatusCommand))
@check_access("status")
async def status(client, message):
    # Existing status logic
    pass
```

## 3. Special Access Level Examples

### Sudo Commands:
```python
from bot.helper.ext_utils.command_decorators import sudo_access

@bot.on_message(filters.command(BotCommands.UsersCommand))
@sudo_access
async def users_settings(client, message):
    # Admin user management
    pass
```

### Owner Commands:
```python
from bot.helper.ext_utils.command_decorators import owner_access

@bot.on_message(filters.command(BotCommands.ShellCommand))
@owner_access
async def shell(client, message):
    # Shell access for owner only
    pass
```

## 4. Custom Access Logic

### Advanced Access Control:
```python
from bot.helper.ext_utils.command_decorators import check_access

@bot.on_message(filters.command(BotCommands.LeechCommand))
@check_access("leech", allow_media=True, custom_message="Custom denial message")
async def leech(client, message):
    # Leech command logic
    pass
```

## 5. Bot Commands Update (bot/helper/telegram_helper/bot_commands.py)

Add the new config command:
```python
class BotCommands:
    # Existing commands...
    ConfigCommand = "config"
    # Add to __init__ method as well
```

## 6. Complete Module Integration Example

Here's how to update an entire module:

```python
# bot/modules/mirror_leech.py (updated)

from pyrogram import filters
from bot import bot
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.command_decorators import check_access

# Remove CustomFilters.authorized and replace with decorators

@bot.on_message(filters.command(BotCommands.MirrorCommand))
@check_access("mirror")
async def mirror(client, message):
    await mirror_leech(client, message)

@bot.on_message(filters.command(BotCommands.LeechCommand))
@check_access("leech", allow_media=True)
async def leech_command(client, message):
    await mirror_leech(client, message, is_leech=True)

@bot.on_message(filters.command(BotCommands.QbMirrorCommand))
@check_access("qbmirror")
async def qb_mirror(client, message):
    await mirror_leech(client, message, is_qbit=True)

# Existing mirror_leech function remains unchanged
async def mirror_leech(client, message, is_leech=False, is_qbit=False):
    # All existing logic stays the same
    pass
```

## 7. Testing the Integration

1. **Check Command Status:**
   ```
   /checkaccess mirror 123456789
   ```

2. **Update Configuration:**
   ```
   /config add newcommand authorized
   /config move mirror sudo
   /config list authorized
   ```

3. **Reload Configuration:**
   ```
   /config reload
   ```

## 8. Migration Checklist

1. ✅ Remove `CustomFilters.authorized` from command filters
2. ✅ Add appropriate decorator imports
3. ✅ Apply `@check_access("command_name")` decorators
4. ✅ Update command_config.json with all commands
5. ✅ Test unauthorized user access
6. ✅ Test authorized user access
7. ✅ Verify admin commands work
8. ✅ Test configuration changes

## 9. Benefits After Integration

- **Centralized Control:** All command access in one JSON file
- **Runtime Changes:** No bot restart needed for access changes
- **Flexible Access:** Easy to move commands between access levels
- **Audit Trail:** Clear command access documentation
- **Scalable:** Easy to add new commands and access levels
- **User-Friendly:** Clear messages for unauthorized access
- **Admin Tools:** Telegram commands for configuration management

## 10. File Structure After Integration

```
bot/
├── modules/
│   ├── config_manager.py          # New admin commands
│   ├── mirror_leech.py            # Updated with decorators
│   ├── clone.py                   # Updated with decorators
│   └── ...                       # Other modules updated
├── helper/
│   ├── ext_utils/
│   │   ├── command_manager.py     # Core access control
│   │   ├── command_decorators.py  # Decorator functions
│   │   ├── command_config.json    # Configuration file
│   │   └── ...
│   └── telegram_helper/
│       ├── bot_commands.py        # Add ConfigCommand
│       └── ...
```

This integration approach ensures:
- Minimal code changes to existing modules
- Backward compatibility
- Easy rollback if needed
- Clear separation of concerns
- Maintainable access control system