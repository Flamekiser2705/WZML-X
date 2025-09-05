#!/usr/bin/env python3
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from ...database.operations import DatabaseManager
from ...database.models import User, SubscriptionType, TokenType
from ...utils.token_utils import TokenGenerator, format_expiry_time, get_token_type_display
from ..config import MESSAGES, REGISTERED_BOTS, MAX_FREE_TOKENS_PER_USER, MAX_PREMIUM_TOKENS_PER_USER

logger = logging.getLogger(__name__)

# Global instances (will be injected from main)
db_manager: DatabaseManager = None
token_generator: TokenGenerator = None


async def start_command(client: Client, message: Message):
    """Handle /start command with user registration"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        # Check if user exists
        existing_user = await db_manager.get_user(user_id)
        
        if not existing_user:
            # Create new user
            user_data = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                subscription_type=SubscriptionType.FREE
            )
            
            success = await db_manager.create_user(user_data)
            if success:
                logger.info(f"✅ New user registered: {user_id} (@{username})")
            else:
                logger.warning(f"⚠️ Failed to register user: {user_id}")
        else:
            # Update last active time
            await db_manager.update_user(user_id, {"last_active": datetime.utcnow()})
            logger.info(f"ℹ️ Existing user: {user_id} (@{username})")
        
        # Create welcome keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")],
            [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
            [InlineKeyboardButton("🆘 Help", callback_data="show_help")]
        ])
        
        await message.reply_text(
            MESSAGES["WELCOME"],
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"❌ Error in start command: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def help_command(client: Client, message: Message):
    """Handle /help command"""
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")],
            [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
            [InlineKeyboardButton("🔙 Back to Start", callback_data="start_menu")]
        ])
        
        await message.reply_text(
            MESSAGES["HELP"],
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"❌ Error in help command: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def verify_command(client: Client, message: Message):
    """Handle /verify command - show token generation options"""
    await show_verify_options(message.from_user.id, message)


async def status_command(client: Client, message: Message):
    """Handle /status command - show user subscription status"""
    await show_user_status(message.from_user.id, message)


async def show_verify_options(user_id: int, message: Message):
    """Show token generation options"""
    try:
        user = await db_manager.get_user(user_id)
        if not user:
            await message.reply_text("❌ User not found. Please use /start first.")
            return
        
        # Get user's current token stats
        stats = await db_manager.get_user_stats(user_id)
        active_tokens = stats.get("active_tokens", 0)
        
        # Check token limits
        is_premium = user.subscription_type == SubscriptionType.PREMIUM
        max_tokens = MAX_PREMIUM_TOKENS_PER_USER if is_premium else MAX_FREE_TOKENS_PER_USER
        
        keyboard_buttons = []
        
        # Option 1: Generate 1 Token
        if active_tokens < max_tokens:
            keyboard_buttons.append([
                InlineKeyboardButton("🎫 Generate 1 Token", callback_data="gen_one_token")
            ])
        
        # Option 2: Generate 4 Tokens (Premium only)
        if is_premium and active_tokens < max_tokens:
            keyboard_buttons.append([
                InlineKeyboardButton("🎫🎫🎫🎫 Generate 4 Tokens", callback_data="gen_four_tokens")
            ])
        
        # Option 3: Premium Plans (for free users or expired premium)
        if not is_premium or (user.premium_expiry and user.premium_expiry < datetime.utcnow()):
            keyboard_buttons.append([
                InlineKeyboardButton("💎 Premium Plans", callback_data="show_premium_plans")
            ])
        
        # Status and back buttons
        keyboard_buttons.extend([
            [InlineKeyboardButton("📊 My Status", callback_data="check_status")],
            [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
        ])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        status_text = "🆓 Free User" if not is_premium else "💎 Premium User"
        token_info = f"Active Tokens: {active_tokens}/{max_tokens}"
        
        verify_text = f"{MESSAGES['VERIFY_OPTIONS']}\n\n**Current Status:** {status_text}\n**{token_info}**"
        
        if active_tokens >= max_tokens:
            verify_text += f"\n\n⚠️ **Token limit reached!** Wait for tokens to expire or upgrade to premium."
        
        await message.reply_text(
            verify_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Error showing verify options: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def show_user_status(user_id: int, message: Message):
    """Show user's subscription and token status"""
    try:
        user = await db_manager.get_user(user_id)
        if not user:
            await message.reply_text("❌ User not found. Please use /start first.")
            return
        
        stats = await db_manager.get_user_stats(user_id)
        
        # Format premium expiry
        premium_expiry_str = "Not Premium"
        if user.premium_expiry:
            if user.premium_expiry > datetime.utcnow():
                premium_expiry_str = user.premium_expiry.strftime("%Y-%m-%d %H:%M UTC")
            else:
                premium_expiry_str = "Expired"
        
        # Format subscription type
        subscription_type = "💎 Premium" if user.subscription_type == SubscriptionType.PREMIUM else "🆓 Free"
        
        status_text = MESSAGES["SUBSCRIPTION_STATUS"].format(
            user_id=user_id,
            subscription_type=subscription_type,
            premium_expiry=premium_expiry_str,
            total_tokens=stats.get("total_tokens", 0),
            active_tokens=stats.get("active_tokens", 0),
            premium_tokens=stats.get("premium_tokens", 0),
            free_tokens=stats.get("free_tokens", 0)
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")],
            [InlineKeyboardButton("💎 Upgrade Premium", callback_data="show_premium_plans")],
            [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
        ])
        
        await message.reply_text(
            status_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Error showing user status: {e}")
        await message.reply_text(MESSAGES["ERROR"])


async def token_option_callback(client: Client, callback_query: CallbackQuery):
    """Handle token generation option callbacks"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if data == "verify_start":
            await show_verify_options(user_id, callback_query.message)
            
        elif data == "gen_one_token":
            await show_bot_selection(user_id, callback_query.message, token_count=1)
            
        elif data == "gen_four_tokens":
            await show_bot_selection(user_id, callback_query.message, token_count=4)
            
        elif data == "show_premium_plans":
            await show_premium_plans(user_id, callback_query.message)
            
        elif data == "check_status":
            await show_user_status(user_id, callback_query.message)
            
        elif data == "show_help":
            await callback_query.message.edit_text(
                MESSAGES["HELP"],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")],
                    [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
                ])
            )
            
        elif data == "start_menu":
            await callback_query.message.edit_text(
                MESSAGES["WELCOME"],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")],
                    [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
                    [InlineKeyboardButton("🆘 Help", callback_data="show_help")]
                ])
            )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in token option callback: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)


async def show_bot_selection(user_id: int, message: Message, token_count: int):
    """Show bot selection for token generation"""
    try:
        # Get available bots
        bots = await db_manager.get_active_bots()
        
        if not bots:
            await message.edit_text("❌ No bots available for token generation.")
            return
        
        keyboard_buttons = []
        
        # Add bot selection buttons
        for bot in bots:
            callback_data = f"select_bot:{bot.bot_id}:{token_count}"
            keyboard_buttons.append([
                InlineKeyboardButton(f"🤖 {bot.name}", callback_data=callback_data)
            ])
        
        # Add back button
        keyboard_buttons.append([
            InlineKeyboardButton("🔙 Back", callback_data="verify_start")
        ])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        bot_selection_text = f"{MESSAGES['BOT_SELECTION']}\n\n**Tokens to generate:** {token_count}"
        
        await message.edit_text(
            bot_selection_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Error showing bot selection: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def show_premium_plans(user_id: int, message: Message):
    """Show premium plans for upgrade"""
    try:
        plans = await db_manager.get_active_plans()
        
        if not plans:
            await message.edit_text("❌ No premium plans available.")
            return
        
        plans_text = MESSAGES["PREMIUM_PLANS"]
        keyboard_buttons = []
        
        for plan in plans:
            price_display = f"₹{plan.price // 100}"  # Convert paise to rupees
            plan_text = f"\n\n💎 **{plan.name}** - {price_display}\n"
            
            # Add features
            for feature in plan.features:
                plan_text += f"• {feature}\n"
            
            plans_text += plan_text
            
            # Add plan selection button
            callback_data = f"select_plan:{plan.plan_id}"
            keyboard_buttons.append([
                InlineKeyboardButton(f"💳 Buy {plan.name} - {price_display}", callback_data=callback_data)
            ])
        
        # Add back button
        keyboard_buttons.append([
            InlineKeyboardButton("🔙 Back", callback_data="verify_start")
        ])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await message.edit_text(
            plans_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Error showing premium plans: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def bot_selection_callback(client: Client, callback_query: CallbackQuery):
    """Handle bot selection for token generation"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if data.startswith("select_bot:"):
            parts = data.split(":")
            if len(parts) == 3:
                bot_id = parts[1]
                token_count = int(parts[2])
                
                # Generate tokens for selected bot
                await generate_tokens_for_bot(user_id, bot_id, token_count, callback_query.message)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in bot selection callback: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)


async def generate_tokens_for_bot(user_id: int, bot_id: str, token_count: int, message: Message):
    """Generate tokens for specific bot"""
    # This will be implemented in token_handler.py
    from . import token_handler
    await token_handler.generate_user_tokens(user_id, bot_id, token_count, message)


async def premium_plan_callback(client: Client, callback_query: CallbackQuery):
    """Handle premium plan selection"""
    try:
        data = callback_query.data
        
        if data.startswith("select_plan:"):
            plan_id = data.split(":")[1]
            
            # Redirect to payment handler
            from . import payment_handler
            await payment_handler.initiate_payment(callback_query.from_user.id, plan_id, callback_query.message)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in premium plan callback: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)


# Create handlers
start_handler = MessageHandler(start_command, filters.command("start") & filters.private)
help_handler = MessageHandler(help_command, filters.command("help") & filters.private)
verify_handler = MessageHandler(verify_command, filters.command("verify") & filters.private)
status_handler = MessageHandler(status_command, filters.command("status") & filters.private)

token_option_callback_handler = CallbackQueryHandler(
    token_option_callback,
    filters.regex(r"^(verify_start|gen_one_token|gen_four_tokens|show_premium_plans|check_status|show_help|start_menu)$")
)

bot_selection_callback_handler = CallbackQueryHandler(
    bot_selection_callback,
    filters.regex(r"^select_bot:")
)

premium_plan_callback_handler = CallbackQueryHandler(
    premium_plan_callback,
    filters.regex(r"^select_plan:")
)
