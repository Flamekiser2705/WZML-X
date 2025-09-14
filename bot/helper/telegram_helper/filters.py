#!/usr/bin/env python3
from pyrogram.filters import create
from pyrogram.enums import ChatType

from bot import user_data, OWNER_ID, config_dict
from bot.helper.telegram_helper.message_utils import chat_info
from bot.helper.telegram_helper.unauthorized_message import send_unauthorized_message
from bot.helper.ext_utils.auth_handler import is_user_authorized


class CustomFilters:

    async def owner_filter(self, _, message):
        user = message.from_user or message.sender_chat
        uid = user.id
        return uid == OWNER_ID

    owner = create(owner_filter)

    async def authorized_user(self, _, message):
        user = message.from_user or message.sender_chat
        uid = user.id
        
        # Check traditional authorization first (owner, sudo, etc)
        if bool(
            uid == OWNER_ID
            or (
                uid in user_data
                and (
                    user_data[uid].get("is_auth", False)
                    or user_data[uid].get("is_sudo", False)
                )
            )
        ):
            return True

        # Check auth bot authorization
        try:
            if await is_user_authorized(uid):
                return True
        except Exception as e:
            # Log error but don't break the filter
            print(f"Auth bot check failed: {e}")

        auth_chat = False
        chat_id = message.chat.id
        if chat_id in user_data and user_data[chat_id].get("is_auth", False):
            if len(topic_ids := user_data[chat_id].get("topic_ids", [])) == 0:
                auth_chat = True
            elif (is_forum := message.reply_to_message) and (
                (
                    is_forum.text is None
                    and is_forum.caption is None
                    and is_forum.id in topic_ids
                )
                or (
                    (is_forum.text or is_forum.caption)
                    and (
                        (
                            not is_forum.reply_to_top_message_id
                            and is_forum.reply_to_message_id in topic_ids
                        )
                        or (is_forum.reply_to_top_message_id in topic_ids)
                    )
                )
            ):
                auth_chat = True
        return auth_chat

    authorized = create(authorized_user)

    async def authorized_usetting(self, _, message):
        uid = (message.from_user or message.sender_chat).id
        chat_id = message.chat.id
        isExists = False
        if (
            uid == OWNER_ID
            or (
                uid in user_data
                and (
                    user_data[uid].get("is_auth", False)
                    or user_data[uid].get("is_sudo", False)
                )
            )
            or (chat_id in user_data and user_data[chat_id].get("is_auth", False))
        ):
            isExists = True
        elif message.chat.type == ChatType.PRIVATE:
            for channel_id in user_data:
                if not (
                    user_data[channel_id].get("is_auth")
                    and str(channel_id).startswith("-100")
                ):
                    continue
                try:
                    if await (await chat_info(str(channel_id))).get_member(uid):
                        isExists = True
                        break
                except Exception:
                    continue
        return isExists

    authorized_uset = create(authorized_usetting)

    async def sudo_user(self, _, message):
        user = message.from_user or message.sender_chat
        uid = user.id
        return bool(
            uid == OWNER_ID or uid in user_data and user_data[uid].get("is_sudo")
        )

    sudo = create(sudo_user)

    async def blacklist_user(self, _, message):
        user = message.from_user or message.sender_chat
        uid = user.id
        return bool(
            uid != OWNER_ID and uid in user_data and user_data[uid].get("is_blacklist")
        )

    blacklisted = create(blacklist_user)

    async def handle_unauthorized_user(self, message):
        """Handle unauthorized user with redirect message"""
        await send_unauthorized_message(message)
        return False
    
    async def check_authorized_and_handle(self, client, message):
        """
        Check if user is authorized and handle unauthorized users with redirect message
        Returns True if authorized, False if unauthorized (and sends message)
        """
        if await self.authorized_user(client, message):
            return True
        else:
            await send_unauthorized_message(message)
            return False
