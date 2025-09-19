#!/usr/bin/env python3
"""
Example: Clone Module Updated with Command Management System
This demonstrates how to integrate the new command access control system
"""

from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from secrets import token_hex
from asyncio import sleep, gather
from aiofiles.os import path as aiopath
from cloudscraper import create_scraper as cget
from json import loads, dumps as jdumps

from bot import (
    LOGGER,
    download_dict,
    download_dict_lock,
    categories_dict,
    config_dict,
    bot,
)
from bot.helper.ext_utils.task_manager import limit_checker, task_utils
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage,
    deleteMessage,
    sendStatusMessage,
    delete_links,
    auto_delete_message,
    open_category_btns,
)
# OLD: from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.ext_utils.bot_utils import (
    is_gdrive_link,
    new_task,
    get_readable_file_size,
    sync_to_async,
    fetch_user_tds,
    is_share_link,
    new_task,
    is_rclone_path,
    cmd_exec,
    get_telegraph_list,
    arg_parser,
)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.mirror_utils.download_utils.direct_link_generator import (
    direct_link_generator,
)
from bot.helper.mirror_utils.rclone_utils.list import RcloneList
from bot.helper.mirror_utils.rclone_utils.transfer import RcloneTransferHelper
from bot.helper.ext_utils.help_messages import CLONE_HELP_MESSAGE
from bot.helper.mirror_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.listeners.tasks_listener import MirrorLeechListener
from bot.helper.themes import BotTheme

# NEW: Import command management system
from bot.helper.ext_utils.command_decorators import check_access


async def rcloneNode(client, message, link, dst_path, rcf, tag):
    if link == "rcl":
        link = await RcloneList(client, message).get_rclone_path("rcd")
        if link is None:
            return
    if dst_path == "rcl" or config_dict["RCLONE_PATH"] == "rcl":
        dst_path = await RcloneList(client, message).get_rclone_path("rcu", link)
        if dst_path is None:
            return
    
    # Rest of rcloneNode function remains the same...
    # [Content unchanged for brevity]


# NEW: Apply command access decorator to the clone function
@new_task
async def clone(client, message):
    # All existing clone logic remains exactly the same
    # No changes needed to the function implementation
    _link = ""
    multi = 0
    dst_path = ""
    bulk_start = 0
    bulk_end = 0
    rcf = ""
    tag = ""
    
    # [All existing clone logic continues unchanged...]
    # This is just to show the pattern - in real implementation,
    # you would keep all the existing clone function code
    
    input_list = message.text.split(" ")
    
    if len(input_list) > 1:
        args = input_list[1:]
        for x in args:
            x = x.strip()
            if x == "rcl":
                dst_path = x
                continue
            elif x.startswith("Tag:"):
                tag = x.replace("Tag:", "")
                continue
            # ... rest of argument parsing
    
    # Continue with existing clone implementation...
    pass


# OLD METHOD - Using CustomFilters and manual handler registration:
# bot.add_handler(
#     MessageHandler(
#         clone,
#         filters=command(BotCommands.CloneCommand)
#         & CustomFilters.authorized
#         & ~CustomFilters.blacklisted,
#     )
# )

# NEW METHOD - Using decorators (Option 1: Decorator approach):
@bot.on_message(command(BotCommands.CloneCommand))
@check_access("clone")
async def clone_handler(client, message):
    """Clone command handler with access control"""
    await clone(client, message)

# Alternative NEW METHOD (Option 2: Direct decoration):
# @bot.on_message(command(BotCommands.CloneCommand))
# @check_access("clone", allow_media=True)  # Allow media files if needed
# async def clone(client, message):
#     # Direct function decoration - rename your main function
#     pass

"""
Migration Benefits:

1. **Centralized Control**: All access control in command_config.json
2. **Runtime Configuration**: Change access without bot restart
3. **Flexible Access Levels**: Easy to move between public/authorized/sudo/owner
4. **Clean Code**: Remove CustomFilters imports and complex filter chains
5. **Consistent Messages**: Standardized unauthorized access messages
6. **Admin Tools**: Telegram commands to manage access in real-time

Migration Steps for Any Module:

1. Remove: from bot.helper.telegram_helper.filters import CustomFilters
2. Add: from bot.helper.ext_utils.command_decorators import check_access
3. Replace filter with decorator: 
   OLD: filters=command(BotCommands.Command) & CustomFilters.authorized
   NEW: @check_access("command_name")
4. Update command_config.json with the command name
5. Test unauthorized and authorized access

Example Configuration in command_config.json:
{
  "access_levels": {
    "authorized": ["clone", "mirror", "leech"],
    "sudo": ["users", "broadcast"],
    "owner": ["shell", "eval"]
  }
}

This approach maintains all existing functionality while adding:
- Centralized access control
- Runtime configuration changes
- Better admin tools
- Cleaner code structure
"""