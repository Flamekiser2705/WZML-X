#!/usr/bin/env python3
"""
WZML-X Auth Bot - Redesigned according to sample images
Handles verification for multiple Mirror Leech Bots
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import uuid

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot_manager import BotManager, get_bot_manager, initialize_bot_manager
from shortener_handler import AuthShortenerManager

# Setup logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('auth_bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class WZMLAuthBot:
    """WZML-X Auth Bot with exact flow from sample images"""
    
    def __init__(self):
        self.app = None
        self.shutdown_event = asyncio.Event()
        self.start_time = datetime.now()
        self.bot_manager = None
        
        # In-memory storage for demo (replace with database later)
        self.user_tokens = {}
        self.user_stats = {"total_users": 0, "total_tokens": 0}
    
    async def initialize(self):
        """Initialize the bot"""
        try:
            logger.info("[INIT] Initializing WZML-X Auth Bot...")
            
            # Load config from main project
            from utils.main_config import config, validate_config, print_config_status
            
            # Print configuration status
            print_config_status()
            
            # Validate configuration
            errors = validate_config()
            if errors:
                logger.error("[ERROR] Configuration errors:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            if not config.AUTH_BOT_TOKEN or config.AUTH_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
                logger.error("[ERROR] Please set AUTH_BOT_TOKEN in main config.env file")
                return False
            
            # Initialize bot manager
            self.bot_manager = await initialize_bot_manager()
            
            # Initialize shortener manager
            self.shortener_manager = AuthShortenerManager()
            
            # Create Pyrogram client with API credentials
            self.app = Client(
                "wzml_auth_bot",
                bot_token=config.AUTH_BOT_TOKEN,
                api_id=config.TELEGRAM_API,
                api_hash=config.TELEGRAM_HASH,
                workdir="sessions"
            )
            
            # Setup handlers
            self.setup_handlers()
            
            logger.info("[SUCCESS] WZML-X Auth Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize bot: {e}")
            return False
    
    def setup_handlers(self):
        """Setup message handlers according to sample images"""
        
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            """Handle /start command - Welcome with available commands"""
            user = message.from_user
            
            # Track user
            if user.id not in self.user_tokens:
                self.user_stats["total_users"] += 1
                self.user_tokens[user.id] = {"tokens": {}, "verified_bots": []}
            
            welcome_text = f"""
🤖 **Welcome to WZML-X Auth Bot**

👋 Hello {user.first_name}!

**Available Commands:**

🚀 `/start` - Start bot
🔐 `/verify` - To Verify yourself  
🕐 `/check` - Check Remaining Time/Token Validity
📊 `/stats` - Bot Stats
🤖 `/listbots` - View configured bots

**Admin Commands:**
⚙️ `/addbot` - Add new mirror bot

ℹ️ **Note:** You need to verify for each Mirror Leech Bot separately to get access tokens.

Use `/verify` to get started!
"""
            
            await message.reply_text(welcome_text)
        
        @self.app.on_message(filters.command("verify") & filters.private)
        async def verify_handler(client: Client, message: Message):
            """Handle /verify command - Show token options first"""
            user = message.from_user
            
            verify_text = f"""
**Hey, {user.first_name}**

Choose From Below Buttons!
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Get 1 Token for Single Bot", callback_data="option_single_token")],
                [InlineKeyboardButton("Get 4 Tokens for All our Bots", callback_data="option_multi_token")],
                [InlineKeyboardButton("Buy Subscription | No Ads", callback_data="option_premium")],
                [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
            ])
            
            await message.reply_text(verify_text, reply_markup=keyboard)
        
        @self.app.on_message(filters.command("check") & filters.private)
        async def check_handler(client: Client, message: Message):
            """Handle /check command - Show verification status and remaining time"""
            user = message.from_user
            user_data = self.user_tokens.get(user.id, {"tokens": {}, "verified_bots": []})
            
            if not user_data["tokens"]:
                check_text = f"""
📋 **Token Status for {user.first_name}**

❌ **No Verified Bots Found**

🔐 You haven't verified for any Mirror Leech Bots yet.
Use `/verify` to get verified for Mirror Leech Bots.

📊 **Your Statistics:**
• Verified Bots: 0/6
• Active Verifications: 0
• Account Type: Free
"""
            else:
                active_verifications = []
                expired_verifications = []
                now = datetime.now()
                
                for bot_id, token_info in user_data["tokens"].items():
                    expires_at = datetime.fromisoformat(token_info["expires_at"])
                    bot_config = self.bot_manager.bots.get(bot_id)
                    bot_name = bot_config.name if bot_config else f"Bot {bot_id}"
                    
                    if expires_at > now:
                        remaining = expires_at - now
                        hours = int(remaining.total_seconds() // 3600)
                        minutes = int((remaining.total_seconds() % 3600) // 60)
                        active_verifications.append(f"✅ **{bot_name}**: {hours}h {minutes}m remaining")
                    else:
                        expired_verifications.append(f"❌ **{bot_name}**: Verification expired")
                
                check_text = f"""
📋 **Verification Status for {user.first_name}**

✅ **Active Verifications ({len(active_verifications)}):**
{chr(10).join(active_verifications) if active_verifications else "• No active verifications"}

❌ **Expired Verifications ({len(expired_verifications)}):**
{chr(10).join(expired_verifications) if expired_verifications else "• No expired verifications"}

📊 **Your Statistics:**
• Verified Bots: {len(user_data["verified_bots"])}/6
• Active Verifications: {len(active_verifications)}/6
• Account Type: Free
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Get Verified", callback_data="verify_new")],
                [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_check")]
            ])
            
            await message.reply_text(check_text, reply_markup=keyboard)
        
        @self.app.on_message(filters.command("stats") & filters.private)
        async def stats_handler(client: Client, message: Message):
            """Handle /stats command - Show bot uptime and total users"""
            uptime = datetime.now() - self.start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            all_bots = self.bot_manager.get_all_bots()
            available_bots = self.bot_manager.get_available_bots()
            
            stats_text = f"""
📊 **WZML-X Auth Bot Statistics**

🕐 **Bot Uptime:** {hours}h {minutes}m
👥 **Total Users:** {self.user_stats['total_users']}
🎫 **Total Tokens Generated:** {self.user_stats['total_tokens']}

🤖 **Configured Bots:** {len(all_bots)}
✅ **Available Bots:** {len(available_bots)}
🔧 **Features:** 
• Single Bot Tokens
• Multi Bot Tokens (all configured bots)
• Premium Subscriptions
• Token Expiry Tracking

📈 **System Health:** All systems operational
"""
            
            await message.reply_text(stats_text)
        
        @self.app.on_message(filters.command("addbot") & filters.private)
        async def addbot_handler(client: Client, message: Message):
            """Handle /addbot command - Add new bot (admin only for now)"""
            # Simple admin check (you can implement proper admin system later)
            admin_ids = [123456789]  # Replace with actual admin user IDs
            
            if message.from_user.id not in admin_ids:
                await message.reply_text("❌ You are not authorized to use this command.")
                return
            
            # Parse command: /addbot bot_key "Bot Name" bot_token
            try:
                parts = message.text.split(' ', 3)
                if len(parts) < 4:
                    await message.reply_text("""
🔧 **Add Bot Command Usage:**

`/addbot <bot_key> "<bot_name>" <bot_token>`

**Example:**
`/addbot mlb1 "Mirror Leech Bot 1" 123456:ABC-DEF...`

**Parameters:**
• `bot_key`: Unique identifier (e.g., mlb1, mlb2)
• `bot_name`: Display name in quotes
• `bot_token`: Telegram bot token
""")
                    return
                
                bot_key = parts[1]
                
                # Parse quoted bot name
                remaining = ' '.join(parts[2:])
                if remaining.startswith('"'):
                    quote_end = remaining.find('"', 1)
                    if quote_end == -1:
                        await message.reply_text("❌ Bot name must be enclosed in quotes.")
                        return
                    bot_name = remaining[1:quote_end]
                    bot_token = remaining[quote_end+1:].strip()
                else:
                    await message.reply_text("❌ Bot name must be enclosed in quotes.")
                    return
                
                if not bot_token:
                    await message.reply_text("❌ Bot token is required.")
                    return
                
                # Add bot
                success = await self.bot_manager.add_bot(bot_key, bot_name, bot_token)
                
                if success:
                    await message.reply_text(f"""
✅ **Bot Added Successfully**

🤖 **Bot Key:** `{bot_key}`
📝 **Bot Name:** {bot_name}
🔍 **Status:** Checking availability...

The bot has been added and availability check is in progress.
""")
                else:
                    await message.reply_text(f"❌ Failed to add bot `{bot_key}` (may already exist).")
                    
            except Exception as e:
                await message.reply_text(f"❌ Error adding bot: {str(e)}")
        
        @self.app.on_message(filters.command("listbots") & filters.private)
        async def listbots_handler(client: Client, message: Message):
            """Handle /listbots command - List all configured bots"""
            all_bots = self.bot_manager.get_all_bots()
            
            if not all_bots:
                await message.reply_text("📭 **No bots configured**\n\nUse `/addbot` to add bots.")
                return
            
            bot_list = []
            for bot_key, bot_config in all_bots.items():
                status_emoji = {
                    "active": "✅",
                    "inactive": "⚪", 
                    "error": "❌",
                    "not_configured": "⚙️"
                }.get(bot_config.status, "❓")
                
                bot_list.append(f"{status_emoji} **{bot_config.name}** (`{bot_key}`)")
            
            bots_text = f"""
🤖 **Configured Mirror Leech Bots**

{chr(10).join(bot_list)}

📊 **Summary:**
• Total: {len(all_bots)}
• Available: {len(self.bot_manager.get_available_bots())}

🔄 Use `/stats` for detailed information
⚙️ Use `/addbot` to add new bots
"""
            
            await message.reply_text(bots_text)
        
        @self.app.on_callback_query()
        async def callback_handler(client: Client, callback_query):
            """Handle callback queries"""
            data = callback_query.data
            user = callback_query.from_user
            
            if data == "option_single_token":
                # Show bot selection for single token
                await self.show_bot_selection(callback_query, "single")
            
            elif data == "option_multi_token":
                # Generate multi bot tokens directly (no bot selection needed)
                await self.generate_multi_tokens(callback_query)
            
            elif data == "option_premium":
                # Show premium options
                await self.show_premium_options(callback_query)
            
            elif data.startswith("select_bot_single_"):
                # Bot selected for single token
                bot_key = data.replace("select_bot_single_", "")
                
                # Check if bot is available
                bot_config = self.bot_manager.bots.get(bot_key)
                if not bot_config or not self.bot_manager.is_bot_available(bot_key):
                    # Redirect to unavailable handler
                    await self.callback_handler(client, callback_query.message, 
                                               callback_query._create_new(data=f"bot_unavailable_{bot_key}"))
                    return
                
                # Bot is available, proceed with token generation
                await self.generate_single_token(callback_query, bot_key)
            
            elif data == "verify_new":
                # Go to verify menu (token options)
                verify_text = f"""
**Hey, {user.first_name}**

Choose From Below Buttons!
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Get 1 Token for Single Bot", callback_data="option_single_token")],
                    [InlineKeyboardButton("Get 4 Tokens for All our Bots", callback_data="option_multi_token")],
                    [InlineKeyboardButton("Buy Subscription | No Ads", callback_data="option_premium")],
                    [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
                ])
                
                await callback_query.message.edit_text(verify_text, reply_markup=keyboard)
            
            elif data == "refresh_check":
                # Refresh check status
                await check_handler(client, callback_query.message)
            
            elif data == "back_to_start":
                # Go back to start
                welcome_text = f"""
🤖 **Welcome to WZML-X Auth Bot**

👋 Hello {user.first_name}!

**Available Commands:**

🚀 `/start` - Start bot
🔐 `/verify` - To Verify yourself  
🕐 `/check` - Check Remaining Time/Token Validity
📊 `/stats` - Bot Stats

ℹ️ **Note:** You need to verify for each Mirror Leech Bot separately to get access tokens.

Use `/verify` to get started!
"""
                await callback_query.message.edit_text(welcome_text)
            
            elif data == "back_to_options":
                # Go back to token options
                verify_text = f"""
**Hey, {user.first_name}**

Choose From Below Buttons!
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Get 1 Token for Single Bot", callback_data="option_single_token")],
                    [InlineKeyboardButton("Get 4 Tokens for All our Bots", callback_data="option_multi_token")],
                    [InlineKeyboardButton("Buy Subscription | No Ads", callback_data="option_premium")],
                    [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
                ])
                
                await callback_query.message.edit_text(verify_text, reply_markup=keyboard)
            
            elif data.startswith("bot_unavailable_"):
                # Handle unavailable bot selection
                bot_key = data.replace("bot_unavailable_", "")
                bot_config = self.bot_manager.bots.get(bot_key)
                
                if bot_config:
                    status_message = self.bot_manager.get_bot_status_message(bot_key)
                    unavailable_text = f"""
❌ **{bot_config.name} is not available**

📋 **Status:** {status_message}

🔧 **Possible Issues:**
• Bot is offline or crashed
• Bot token is invalid
• Network connectivity issues
• Bot not properly configured

Please try another bot or contact admin.
"""
                else:
                    unavailable_text = "❌ **Bot not found**"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh & Try Again", callback_data="refresh_bots")],
                    [InlineKeyboardButton("🔙 Back to Bots", callback_data="option_single_token")],
                    [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
                ])
                
                await callback_query.message.edit_text(unavailable_text, reply_markup=keyboard)
            
            elif data == "refresh_bots":
                # Refresh bot availability
                refresh_text = "🔄 **Checking bot availability...**\n\nPlease wait..."
                await callback_query.message.edit_text(refresh_text)
                
                # Check all bots
                await self.bot_manager.check_all_bots()
                
                # Show updated bot selection
                await self.show_bot_selection(callback_query, "single")
            
            elif data == "show_available_bots":
                # Show available bots with status
                user_data = self.user_tokens.get(user.id, {"tokens": {}, "verified_bots": []})
                now = datetime.now()
                
                bot_status = []
                for bot_key, bot_config in self.bot_manager.get_all_bots().items():
                    if bot_key in user_data["tokens"]:
                        expires_at = datetime.fromisoformat(user_data["tokens"][bot_key]["expires_at"])
                        if expires_at > now:
                            remaining = expires_at - now
                            hours = int(remaining.total_seconds() // 3600)
                            minutes = int((remaining.total_seconds() % 3600) // 60)
                            bot_status.append(f"✅ **{bot_config.name}** - Active ({hours}h {minutes}m left)")
                        else:
                            bot_status.append(f"❌ **{bot_config.name}** - Expired")
                    else:
                        bot_status.append(f"⚪ **{bot_config.name}** - Not verified")
                
                status_text = f"""
🤖 **Available Mirror Leech Bots**

{chr(10).join(bot_status)}

📊 **Summary:**
• Verified: {len(user_data['verified_bots'])}/{len(self.bot_manager.get_all_bots())}
• Active: {len([b for b in user_data['tokens'].values() if datetime.fromisoformat(b['expires_at']) > now])}/6
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Get More Tokens", callback_data="verify_new")],
                    [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
                ])
                
                await callback_query.message.edit_text(status_text, reply_markup=keyboard)
            
            elif data.startswith("select_shortener_"):
                # Handle shortener selection
                parts = data.replace("select_shortener_", "").split("_")
                shortener_id = parts[0]
                bot_key = parts[1] if len(parts) > 1 else "multi"
                token_type = parts[2] if len(parts) > 2 else "multi"
                token_num = int(parts[3]) if len(parts) > 3 else None
                await self.handle_shortener_selection(callback_query, shortener_id, bot_key, token_type, token_num)
            
            elif data.startswith("continue_shortener_"):
                # Continue existing shortener verification
                shortener_id = int(data.replace("continue_shortener_", ""))
                await self.continue_shortener_verification(callback_query, shortener_id)
            
            elif data.startswith("verify_token_"):
                # Handle individual token verification (like sample image)
                token_num = data.replace("verify_token_", "")
                await self.verify_individual_token(callback_query, token_num)
            
            elif data.startswith("verify_shortener_"):
                # Handle shortener verification (demo for now)
                token_num = data.replace("verify_shortener_", "")
                await self.complete_token_verification(callback_query, token_num)
            
            elif data.startswith("mark_verified_"):
                # Mark token as verified (demo shortener completion)
                token_num = data.replace("mark_verified_", "")
                await self.mark_token_verified(callback_query, token_num)
            
            elif data.startswith("verified_token_"):
                # User clicked on already verified token
                token_num = data.replace("verified_token_", "")
                await callback_query.answer(f"✅ Token {token_num} is already verified!", show_alert=True)
            
            elif data == "back_to_multi_tokens":
                # Go back to multi-token interface
                await self.show_multi_token_status(callback_query)
            
            elif data == "continue_multi_session":
                # Continue existing multi-token session
                await self.show_multi_token_status(callback_query)
            
            elif data == "restart_multi_session":
                # Clear existing session and start fresh
                user = callback_query.from_user
                if user.id in self.user_tokens and "multi_session" in self.user_tokens[user.id]:
                    del self.user_tokens[user.id]["multi_session"]
                # Start new session
                await self.generate_multi_tokens(callback_query)
            
            elif data.startswith("verify_completed_"):
                # Handle verification completion
                verification_token = data.replace("verify_completed_", "")
                await self.handle_verification_completed(callback_query, verification_token)
            
            elif data.startswith("verify_token_"):
                # Handle individual token verification (show shortener selection)
                token_num = int(data.replace("verify_token_", ""))
                await self.handle_token_verification(callback_query, token_num)
            
            elif data == "continue_multi_verification":
                # Continue multi-token verification from partial state
                await self.generate_multi_tokens(callback_query)
            
            elif data == "reset_multi_verification":
                # Reset multi-token verification completely
                user = callback_query.from_user
                if user.id in self.user_tokens and "multi_session" in self.user_tokens[user.id]:
                    del self.user_tokens[user.id]["multi_session"]
                await self.generate_multi_tokens(callback_query)
            
            elif data == "cooldown_info":
                # Show cooldown information
                await callback_query.answer("⏳ This shortener is on cooldown. Please wait before using it again.", show_alert=True)
            
            elif data == "close_menu":
                await callback_query.message.delete()
            
            await callback_query.answer()
    
    async def show_bot_selection(self, callback_query, token_type):
        """Show bot selection for single token with real availability"""
        user = callback_query.from_user
        
        # Get all bots and their status
        all_bots = self.bot_manager.get_all_bots()
        available_bots = self.bot_manager.get_available_bots()
        
        if not available_bots:
            # No bots available
            no_bots_text = f"""
**{user.first_name},**

❌ **No Mirror Leech Bots Available**

All bots are currently offline or not configured.

🔧 **Bot Status:**
{self.bot_manager.get_bot_config_summary()}

Please contact admin to configure the bots.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_bots")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
                [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
            ])
            
            await callback_query.message.edit_text(no_bots_text, reply_markup=keyboard)
            return
        
        selection_text = f"""
**{user.first_name},**

Choose from below button in which you want to verify

**Note:** Please Check Bot Name Properly before verifying.

🤖 **Available:** {len(available_bots)}/{len(all_bots)} bots online
"""
        
        # Create keyboard with available bots
        keyboard = []
        for bot_key, bot_config in all_bots.items():
            if bot_config.status == "active":
                # Bot is available
                button_text = f"✅ {bot_config.name}"
                callback_data = f"select_bot_{token_type}_{bot_key}"
            else:
                # Bot is not available - show status
                status_msg = {
                    "not_configured": "⚙️ Not Configured",
                    "error": "❌ Offline", 
                    "inactive": "⚪ Inactive"
                }.get(bot_config.status, "❓ Unknown")
                
                button_text = f"{status_msg} {bot_config.name}"
                callback_data = f"bot_unavailable_{bot_key}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons
        keyboard.append([InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_bots")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_options")])
        keyboard.append([InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")])
        
        await callback_query.message.edit_text(selection_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def generate_single_token(self, callback_query, bot_key):
        """Show shortener selection for single bot verification"""
        user = callback_query.from_user
        bot_config = self.bot_manager.bots.get(bot_key)
        
        if not bot_config:
            await callback_query.message.edit_text("❌ Bot not found!")
            return
        
        # Show shortener selection instead of auto-verification
        await self.show_shortener_selection(callback_query, bot_key, "single")
    
    async def show_shortener_selection(self, callback_query, bot_key, token_type, token_num=None):
        """Show shortener selection interface (like screenshot)"""
        user = callback_query.from_user
        bot_config = self.bot_manager.bots.get(bot_key)
        
        if not bot_config:
            await callback_query.message.edit_text("❌ Bot not found!")
            return
        
        # Get verification summary
        verification_summary = self.shortener_manager.get_verification_summary(user.id)
        
        # Check if user is locked to a specific shortener
        if self.shortener_manager.is_user_locked_to_shortener(user.id):
            locked_shortener_id = self.shortener_manager.get_user_locked_shortener(user.id)
            warning_text = f"""
**{user.first_name}**

⚠️ **You must complete verification with Short URL {locked_shortener_id} first!**

Please finish your current verification before trying another shortener.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Continue Short URL {locked_shortener_id}", callback_data=f"continue_shortener_{locked_shortener_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
                [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
            ])
            
            await callback_query.message.edit_text(warning_text, reply_markup=keyboard)
            return
        
        # Get available shorteners
        available_shorteners = verification_summary["available_shorteners"]
        verification_count = verification_summary["verification_count"]
        total_access_hours = verification_summary["total_access_hours"]
        
        if not available_shorteners:
            # All shorteners on cooldown or max verifications reached
            if verification_summary["max_verifications_reached"]:
                max_reached_text = f"""
**{user.first_name}**

🎉 **Maximum verifications reached!**

You have verified all 4 shorteners and have **24-hour access** to all bots.

⏰ **Current access time:** {total_access_hours} hours

🚀 **You can use any Mirror Leech Bot without restrictions!**
"""
            else:
                max_reached_text = f"""
**{user.first_name}**

⏳ **All shorteners are on cooldown**

You have verified {verification_count} shortener(s) and have **{total_access_hours}-hour access** to all bots.

Shortener buttons will reappear after the cooldown period expires.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✖ AVAILABLE BOTS", callback_data="show_available_bots")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
                [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
            ])
            
            await callback_query.message.edit_text(max_reached_text, reply_markup=keyboard)
            return
        
        # Calculate next verification time bonus
        next_verification_hours = min((verification_count + 1) * 6, 24)
        
        # Show shortener selection interface (like screenshot)
        selection_text = f"""
**{user.first_name}**

Choose Shorturl from below buttons to verify yourself in **{bot_config.name}**

📊 **You'll be verified across all bots until {(datetime.now() + timedelta(hours=next_verification_hours)).strftime('%d %b %Y %I:%M %p')} (Asia/Kolkata), If you verify {min(verification_count + 1, 4)} times in any bot..**

You are Verified **{verification_count} Time**.
"""
        
        # Create shortener buttons
        keyboard = []
        for shortener in available_shorteners:
            button_text = f"Short URL {shortener['id']}"
            callback_data = f"select_shortener_{shortener['id']}_{bot_key}_{token_type}"
            if token_num:
                callback_data += f"_{token_num}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons
        keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_options")])
        keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
        
        await callback_query.message.edit_text(selection_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_shortener_selection(self, callback_query, shortener_id, bot_key, token_type, token_num=None):
        """Handle user selecting a specific shortener"""
        user = callback_query.from_user
        
        # For multi-token verification, store the current token number
        verification_data = {
            "shortener_id": shortener_id,
            "bot_key": bot_key,
            "token_type": token_type
        }
        
        if token_type == "multi" and token_num is not None:
            verification_data["current_token"] = token_num
        
        # Start verification session
        verification_token = self.shortener_manager.start_verification_session(
            user.id, shortener_id, bot_key, token_type, verification_data
        )
        
        # Generate verification URL
        verification_url = self.shortener_manager.generate_verification_url(
            user.id, shortener_id, verification_token
        )
        
        # Show verification interface
        if token_type == "multi" and token_num is not None:
            bot_name = "All Bots"
            verification_text = f"""
**Hey, {user.first_name},**

Verify yourself with **Token {token_num} - {shortener_id}**

⚠️ **Using bots, adblockers, or DNS services to bypass the shortener is strictly prohibited and will lead to a ban**

🛡️ **For your safety and the best experience, use Chrome without any tool**

**Token:** {token_num}/4
🔗 **Verification Link:** {verification_url}

Click the link above to complete verification.
"""
        else:
            bot_config = self.bot_manager.bots.get(bot_key)
            bot_name = bot_config.name if bot_config else "Unknown Bot"
            verification_text = f"""
**Hey, {user.first_name},**

Verify yourself with **Short URL {shortener_id}**

⚠️ **Using bots, adblockers, or DNS services to bypass the shortener is strictly prohibited and will lead to a ban**

🛡️ **For your safety and the best experience, use Chrome without any tool**

**Bot:** {bot_name}
🔗 **Verification Link:** {verification_url}

Click the link above to complete verification.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ I've Completed Verification", callback_data=f"verify_completed_{verification_token}")],
            [InlineKeyboardButton("🔙 Back to Shorteners", callback_data=f"back_to_shortener_selection_{bot_key}_{token_type}")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(verification_text, reply_markup=keyboard)
    
    async def continue_shortener_verification(self, callback_query, shortener_id):
        """Continue existing shortener verification"""
        user = callback_query.from_user
        
        if user.id not in self.shortener_manager.active_verifications:
            await callback_query.message.edit_text("❌ No active verification found.")
            return
        
        verification_data = self.shortener_manager.active_verifications[user.id]
        verification_token = verification_data["verification_token"]
        bot_key = verification_data["bot_key"]
        
        # Generate verification URL again
        verification_url = self.shortener_manager.generate_verification_url(
            user.id, shortener_id, verification_token
        )
        
        bot_config = self.bot_manager.bots.get(bot_key)
        bot_name = bot_config.name if bot_config else "Unknown Bot"
        
        verification_text = f"""
**Hey, {user.first_name},**

Continue verification with **Short URL {shortener_id}**

**Bot:** {bot_name}
🔗 **Verification Link:** {verification_url}

Click the link above to complete verification.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ I've Completed Verification", callback_data=f"verify_completed_{verification_token}")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(verification_text, reply_markup=keyboard)
    
    async def generate_multi_tokens(self, callback_query):
        """Show individual token buttons for manual verification (like sample image)"""
        user = callback_query.from_user
        
        # Get all configured bots (both available and unavailable)
        all_bots = self.bot_manager.get_all_bots()
        
        if not all_bots:
            await callback_query.message.edit_text("❌ No bots configured! Please contact admin.")
            return
        
        # Check if user has already completed the 4-token task
        if user.id in self.user_tokens:
            # Check if user has any active multi-token access (24-hour access to all bots)
            user_tokens = self.user_tokens[user.id].get("tokens", {})
            now = datetime.now()
            
            # Look for active multi-token access
            has_active_multi_access = False
            for bot_key, token_info in user_tokens.items():
                if (token_info.get("type") == "multi_token_24h" and 
                    token_info.get("all_tokens_completed") and
                    datetime.fromisoformat(token_info["expires_at"]) > now):
                    has_active_multi_access = True
                    break
            
            if has_active_multi_access:
                # User already has active 24-hour access
                expires_at = datetime.fromisoformat(list(user_tokens.values())[0]["expires_at"])
                remaining_time = expires_at - now
                hours = int(remaining_time.total_seconds() // 3600)
                minutes = int((remaining_time.total_seconds() % 3600) // 60)
                
                already_verified_text = f"""
**{user.first_name}**

✅ **You are already verified with all 4 tokens!**

🎉 **You have 24-hour access to ALL {len(all_bots)} Mirror Leech Bots**

⏰ **Time remaining:** {hours}h {minutes}m

🚀 **You can use any of our Mirror Leech Bots without restrictions!**

**Valid until:** {expires_at.strftime('%d %b %Y %I:%M %p')} Asia/Kolkata
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✖ AVAILABLE BOTS", callback_data="show_available_bots")],
                    [InlineKeyboardButton("📊 Check Status", callback_data="refresh_check")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
                    [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
                ])
                
                await callback_query.message.edit_text(already_verified_text, reply_markup=keyboard)
                return
            
            # Check if user has an incomplete multi-session in progress
            if "multi_session" in self.user_tokens[user.id]:
                session_data = self.user_tokens[user.id]["multi_session"]
                verified_count = sum(1 for t in session_data.values() if t["verified"])
                
                if verified_count > 0 and verified_count < 4:
                    # User has partial progress, ask if they want to continue or restart
                    partial_progress_text = f"""
**{user.first_name}**

🔄 **You have a 4-token verification in progress**

📊 **Current Progress:** {verified_count}/4 tokens verified

Do you want to:
• **Continue** your existing verification
• **Restart** with new 4 tokens
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Continue Existing", callback_data="continue_multi_session")],
                        [InlineKeyboardButton("🆕 Start Fresh", callback_data="restart_multi_session")],
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
                        [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
                    ])
                    
                    await callback_query.message.edit_text(partial_progress_text, reply_markup=keyboard)
                    return
        
        # Create list of bots for reference (but always generate exactly 4 tokens)
        all_bots = list(all_bots.items())
        
        # Store token generation session
        if user.id not in self.user_tokens:
            self.user_tokens[user.id] = {"tokens": {}, "verified_bots": [], "multi_session": {}}
        
        # Generate exactly 4 tokens (regardless of bot count)
        expires_at = datetime.now() + timedelta(days=1)  # 24 hours (1 day) for 4-token system
        token_data = {}
        
        # Always create exactly 4 tokens
        for i in range(4):
            token = str(uuid.uuid4())
            # Assign a representative bot name for display (cycle through available bots)
            bot_for_display = all_bots[i % len(all_bots)] if all_bots else ("demo_bot", {"name": "Demo Bot"})
            
            token_data[f"token_{i+1}"] = {
                "token": token,
                "bot_key": bot_for_display[0],  # Just for display
                "bot_name": bot_for_display[1].name,  # Just for display
                "expires_at": expires_at.isoformat(),
                "verified": False,
                "task_number": i+1  # This is a task, not bot-specific
            }
        
        # Store in multi_session for tracking
        self.user_tokens[user.id]["multi_session"] = token_data
        
        # Show token verification interface (like sample image)
        verification_text = f"""
**{user.first_name},**

Verify yourself with below tokens & get access in **all our bots** until {expires_at.strftime('%d %b %Y %I:%M %p')} Asia/Kolkata

You are Verified with **0 token**.
"""
        
        # Create token buttons (always exactly 4 tokens)
        keyboard = []
        for i in range(4):
            token_num = i + 1
            keyboard.append([InlineKeyboardButton(f"Token {token_num}", callback_data=f"verify_token_{token_num}")])
        
        # Add navigation buttons
        keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_options")])
        keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
        
        await callback_query.message.edit_text(verification_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def verify_individual_token(self, callback_query, token_num):
        """Handle individual token verification with shortener links"""
        user = callback_query.from_user
        
        # Show loading state first (like screenshot 3)
        loading_text = f"Generating Link for Token {token_num}..."
        await callback_query.message.edit_text(loading_text)
        
        # Simulate link generation delay
        await asyncio.sleep(2)
        
        # Check if user has multi_session
        if user.id not in self.user_tokens or "multi_session" not in self.user_tokens[user.id]:
            await callback_query.message.edit_text("❌ No active token session found. Please start again.")
            return
        
        token_key = f"token_{token_num}"
        token_data = self.user_tokens[user.id]["multi_session"].get(token_key)
        
        if not token_data:
            await callback_query.message.edit_text("❌ Invalid token number.")
            return
        
        if token_data["verified"]:
            await callback_query.message.edit_text(f"✅ Token {token_num} is already verified!")
            return
        
        # Show verification interface (like screenshot 4)
        verification_text = f"""
**Hey, {user.first_name},**

Verify yourself with **Token No. {token_num}**

⚠️ **Using bots, adblockers, or DNS services to bypass the shortener is strictly prohibited and will lead to a ban**

🛡️ **For your safety and the best experience, use Chrome without any tool**

**Bot:** {token_data['bot_name']}
⏰ **Expires:** {datetime.fromisoformat(token_data['expires_at']).strftime('%d %b %Y %I:%M %p')}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Verify (Token {token_num})", callback_data=f"verify_shortener_{token_num}")],
            [InlineKeyboardButton("Buy Subscription | No Ads", callback_data="option_premium")],
            [InlineKeyboardButton("Back", callback_data="back_to_multi_tokens")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(verification_text, reply_markup=keyboard)
    
    async def complete_token_verification(self, callback_query, token_num):
        """Complete token verification and show success message (like screenshot 5)"""
        user = callback_query.from_user
        
        if user.id not in self.user_tokens or "multi_session" not in self.user_tokens[user.id]:
            await callback_query.message.edit_text("❌ No active token session found.")
            return
        
        token_key = f"token_{token_num}"
        token_data = self.user_tokens[user.id]["multi_session"].get(token_key)
        
        if not token_data:
            await callback_query.message.edit_text("❌ Invalid token number.")
            return
        
        # Mark as verified
        token_data["verified"] = True
        
        # Count how many tokens are verified now
        verified_count = sum(1 for t in self.user_tokens[user.id]["multi_session"].values() if t["verified"])
        total_tokens = len(self.user_tokens[user.id]["multi_session"])
        
        # IMPORTANT: Only give bot access when ALL 4 tokens are verified
        if verified_count == total_tokens:  # All 4 tokens verified
            # NOW unlock access to ALL bots
            all_bots = self.bot_manager.get_all_bots()
            for bot_key, bot_config in all_bots.items():
                self.user_tokens[user.id]["tokens"][bot_key] = {
                    "token": f"multi_token_{user.id}_{datetime.now().timestamp()}",
                    "expires_at": token_data["expires_at"],
                    "type": "multi_token_24h",
                    "verified": True,
                    "all_tokens_completed": True
                }
                
                if bot_key not in self.user_tokens[user.id]["verified_bots"]:
                    self.user_tokens[user.id]["verified_bots"].append(bot_key)
        
        self.user_stats["total_tokens"] += 1
        
        # Show success message (like screenshot 5)
        if verified_count == total_tokens:
            # All 4 tokens verified - SUCCESS!
            success_text = f"""
**{user.first_name}**

**Token {token_num} Verified** ✅

🎉 **ALL 4 TOKENS COMPLETED!**

✅ You now have **24-hour access** to **ALL {len(self.bot_manager.get_all_bots())} Mirror Leech Bots**!
"""
        else:
            # Just one token verified, more to go
            success_text = f"""
**{user.first_name}**

**Token {token_num} Verified** ✅

📊 **Progress:** {verified_count}/{total_tokens} tokens completed

🔄 **Continue verifying remaining tokens to unlock ALL bots**
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✖ AVAILABLE BOTS", callback_data="show_available_bots")],
        ])
        
        await callback_query.message.edit_text(success_text, reply_markup=keyboard)
        
        # Auto-redirect back to multi-token interface after 2 seconds
        await asyncio.sleep(2)
        await self.show_multi_token_status(callback_query)
    
    async def mark_token_verified(self, callback_query, token_num):
        """Mark individual token as verified and update status"""
        user = callback_query.from_user
        
        if user.id not in self.user_tokens or "multi_session" not in self.user_tokens[user.id]:
            await callback_query.message.edit_text("❌ No active token session found.")
            return
        
        token_key = f"token_{token_num}"
        token_data = self.user_tokens[user.id]["multi_session"].get(token_key)
        
        if not token_data:
            await callback_query.message.edit_text("❌ Invalid token number.")
            return
        
        # Mark as verified
        token_data["verified"] = True
        
        # Add to main tokens collection
        bot_key = token_data["bot_key"]
        self.user_tokens[user.id]["tokens"][bot_key] = {
            "token": token_data["token"],
            "expires_at": token_data["expires_at"],
            "type": "free_multi",
            "verified": True
        }
        
        if bot_key not in self.user_tokens[user.id]["verified_bots"]:
            self.user_tokens[user.id]["verified_bots"].append(bot_key)
        
        self.user_stats["total_tokens"] += 1
        
        # Count verified tokens
        verified_count = sum(1 for t in self.user_tokens[user.id]["multi_session"].values() if t["verified"])
        total_tokens = len(self.user_tokens[user.id]["multi_session"])
        
        success_text = f"""
✅ **Token {token_num} Verified Successfully!**

**Bot:** {token_data['bot_name']}
**Progress:** {verified_count}/{total_tokens} tokens verified

{f"🎉 **All tokens verified!** You now have access to all {total_tokens} bots!" if verified_count == total_tokens else f"Continue verifying remaining {total_tokens - verified_count} tokens."}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Tokens", callback_data="back_to_multi_tokens")],
            [InlineKeyboardButton("📊 Check Status", callback_data="show_available_bots")],
            [InlineKeyboardButton("✖ Close", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(success_text, reply_markup=keyboard)
    
    async def show_multi_token_status(self, callback_query):
        """Show multi-token verification status (like sample image)"""
        user = callback_query.from_user
        
        if user.id not in self.user_tokens or "multi_session" not in self.user_tokens[user.id]:
            await callback_query.message.edit_text("❌ No active token session found.")
            return
        
        session_data = self.user_tokens[user.id]["multi_session"]
        verified_count = sum(1 for t in session_data.values() if t["verified"])
        total_tokens = len(session_data)
        
        # Get expiration time from first token
        first_token = list(session_data.values())[0]
        expires_at = datetime.fromisoformat(first_token["expires_at"])
        
        # Show updated verification interface (like sample image)
        verification_text = f"""
**{user.first_name},**

Verify yourself with below tokens & get access in **all our bots** until {expires_at.strftime('%d %b %Y %I:%M %p')} Asia/Kolkata

You are Verified with **{verified_count} token**.
"""
        
        # Create token buttons ONLY for unverified tokens (verified ones disappear)
        keyboard = []
        for i in range(4):  # Always exactly 4 tokens
            token_num = i + 1
            token_key = f"token_{token_num}"
            token_data = session_data.get(token_key)
            
            # Only show button if token exists and is NOT verified (verified tokens disappear)
            if token_data and not token_data["verified"]:
                button_text = f"Token {token_num}"
                callback_data = f"verify_token_{token_num}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons
        keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_options")])
        keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
        
        # Special case: If all tokens are verified, show completion message
        if verified_count == total_tokens:
            completion_text = f"""
🎉 **Congratulations {user.first_name}!**

**All {total_tokens} tokens verified successfully!**

✅ You now have **24-hour access** to **ALL {len(self.bot_manager.get_all_bots())} Mirror Leech Bots**

⏰ **Valid until:** {expires_at.strftime('%d %b %Y %I:%M %p')} Asia/Kolkata

🚀 **You can now use any of our Mirror Leech Bots without restrictions!**
"""
            
            keyboard = [
                [InlineKeyboardButton("✖ AVAILABLE BOTS", callback_data="show_available_bots")],
                [InlineKeyboardButton("📊 Check Status", callback_data="refresh_check")],
                [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
            ]
            
            await callback_query.message.edit_text(completion_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await callback_query.message.edit_text(verification_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_premium_options(self, callback_query):
        """Show premium subscription options"""
        premium_text = f"""
💎 **Premium Subscription Plans**

🚀 **Skip all shorteners and get instant access!**

📦 **Available Plans:**
• **7 Days** - ₹5.00
• **30 Days** - ₹20.00  
• **90 Days** - ₹50.00

✨ **Premium Benefits:**
• No shortener verification required
• Instant token generation
• Up to 4 active tokens per bot
• Priority support
• No ads

💳 **Payment Methods:**
• UPI/Card (Razorpay)
• PayPal (International)

⚠️ **Note:** Payment integration coming soon!
"""
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💎 7 Days - ₹5", callback_data="buy_7d"),
                InlineKeyboardButton("💎 30 Days - ₹20", callback_data="buy_30d")
            ],
            [InlineKeyboardButton("💎 90 Days - ₹50", callback_data="buy_90d")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(premium_text, reply_markup=keyboard)
    
    async def handle_verification_completed(self, callback_query, verification_token):
        """Handle when user clicks 'I've Completed Verification'"""
        user = callback_query.from_user
        
        # Check if verification is valid
        if not self.shortener_manager.verify_completion(user.id, verification_token):
            await callback_query.answer("❌ Verification failed or expired. Please try again.", show_alert=True)
            return
        
        # Get verification data
        verification_data = self.shortener_manager.active_verifications.get(user.id)
        if not verification_data:
            await callback_query.answer("❌ No active verification found.", show_alert=True)
            return
        
        bot_key = verification_data["bot_key"]
        token_type = verification_data["token_type"]
        shortener_id = verification_data["shortener_id"]
        
        # For multi-token verification, handle differently
        if token_type == "multi":
            await self.complete_multi_token_verification(callback_query, verification_token)
            return
        
        # For single bot verification
        if user.id not in self.user_tokens:
            self.user_tokens[user.id] = {"tokens": {}, "verified_bots": []}
        
        # Generate access token
        access_token = str(uuid.uuid4())
        
        # Determine duration based on type
        if token_type == "premium_7d":
            duration = timedelta(days=7)
        elif token_type == "premium_30d":
            duration = timedelta(days=30)
        elif token_type == "premium_90d":
            duration = timedelta(days=90)
        else:  # free_6h
            duration = timedelta(hours=6)
        
        expires_at = datetime.now(timezone.utc) + duration
        
        # Store token
        self.user_tokens[user.id]["tokens"][bot_key] = {
            "token": access_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Add to verified bots
        if bot_key not in self.user_tokens[user.id]["verified_bots"]:
            self.user_tokens[user.id]["verified_bots"].append(bot_key)
        
        # Clean up verification session
        self.shortener_manager.cleanup_verification_session(user.id)
        
        # Show success message
        bot_config = self.bot_manager.bots.get(bot_key)
        bot_name = bot_config.name if bot_config else "Unknown Bot"
        
        success_text = f"""
**✅ Verification Successful!**

**User:** {user.first_name}
**Bot:** {bot_name}
**Duration:** {duration.days} days {duration.seconds//3600} hours
**Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}

**Your Access Token:**
`{access_token}`

You now have access to {bot_name}!
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Options", callback_data="back_to_options")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(success_text, reply_markup=keyboard)
    
    async def complete_multi_token_verification(self, callback_query, verification_token):
        """Complete multi-token verification process"""
        user = callback_query.from_user
        
        # Get verification data
        verification_data = self.shortener_manager.active_verifications.get(user.id)
        if not verification_data:
            await callback_query.answer("❌ No active verification found.", show_alert=True)
            return
        
        # Get current token number from verification data
        current_token = verification_data.get("current_token", 1)
        
        # Update multi-session progress
        if user.id not in self.user_tokens:
            self.user_tokens[user.id] = {"tokens": {}, "verified_bots": [], "multi_session": {}}
        
        session_data = self.user_tokens[user.id].get("multi_session", {})
        verified_tokens = session_data.get("verified_tokens", [])
        
        # Add current token to verified list
        if current_token not in verified_tokens:
            verified_tokens.append(current_token)
            session_data["verified_tokens"] = verified_tokens
            self.user_tokens[user.id]["multi_session"] = session_data
        
        # Clean up current verification session
        self.shortener_manager.cleanup_verification_session(user.id)
        
        # Check if all 4 tokens are completed
        if len(verified_tokens) >= 4:
            # All tokens completed - grant 24-hour access to ALL bots
            await self.grant_full_access(callback_query, user)
        else:
            # Show progress and continue
            await self.show_multi_token_progress(callback_query, user, verified_tokens)
    
    async def grant_full_access(self, callback_query, user):
        """Grant 24-hour access to all bots"""
        all_bots = self.bot_manager.get_all_bots()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        if user.id not in self.user_tokens:
            self.user_tokens[user.id] = {"tokens": {}, "verified_bots": []}
        
        # Generate tokens for all bots
        for bot_key in all_bots:
            access_token = str(uuid.uuid4())
            self.user_tokens[user.id]["tokens"][bot_key] = {
                "token": access_token,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            }
            
            if bot_key not in self.user_tokens[user.id]["verified_bots"]:
                self.user_tokens[user.id]["verified_bots"].append(bot_key)
        
        # Clear multi-session data
        if "multi_session" in self.user_tokens[user.id]:
            del self.user_tokens[user.id]["multi_session"]
        
        success_text = f"""
**🎉 CONGRATULATIONS! 🎉**

**All 4 Tokens Verified Successfully!**

**User:** {user.first_name}
**Access Duration:** ⏰ **24 Hours**
**Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}

**🔓 ACCESS GRANTED TO ALL BOTS:**
"""
        
        # List all bots with their tokens
        for bot_key, bot_config in all_bots.items():
            token_data = self.user_tokens[user.id]["tokens"][bot_key]
            success_text += f"\n**{bot_config.name}:**\n`{token_data['token']}`\n"
        
        success_text += "\n✅ **You now have full access to all available bots!**"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(success_text, reply_markup=keyboard)
    
    async def show_multi_token_progress(self, callback_query, user, verified_tokens):
        """Show current progress in multi-token verification"""
        progress_text = f"""
**🔄 Token Verification Progress**

**User:** {user.first_name}
**Progress:** {len(verified_tokens)}/4 tokens completed

**Verification Status:**
"""
        for i in range(1, 5):
            if i in verified_tokens:
                progress_text += f"🟢 **Token {i}:** ✅ Verified\n"
            else:
                progress_text += f"🔴 **Token {i}:** ⏳ Pending\n"
        
        progress_text += f"\n📋 **Complete all 4 tokens to unlock 24-hour access to ALL bots!**"
        progress_text += f"\n⏱️ **Remaining:** {4 - len(verified_tokens)} tokens"
        
        # Create buttons for remaining tokens
        keyboard = []
        token_row = []
        
        for i in range(1, 5):
            if i not in verified_tokens:
                token_row.append(InlineKeyboardButton(f"🪙 Token {i}", callback_data=f"verify_token_{i}"))
                if len(token_row) == 2:
                    keyboard.append(token_row)
                    token_row = []
        
        if token_row:  # Add remaining buttons
            keyboard.append(token_row)
        
        keyboard.extend([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_options")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(progress_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_token_verification(self, callback_query, token_num):
        """Handle individual token verification (show shortener selection)"""
        user = callback_query.from_user
        
        # Show shortener selection for this token
        configured_shorteners = self.shortener_manager.get_configured_shorteners()
        
        if not configured_shorteners:
            await callback_query.message.edit_text("❌ No shorteners configured! Please contact admin.")
            return
        
        selection_text = f"""
**🪙 Token {token_num} Verification**

**User:** {user.first_name}
**Step:** {token_num}/4

Select a shortener service to complete Token {token_num} verification:

⚠️ **Important:** Choose any available shortener. Each adds 6 hours to your access duration.
"""
        
        keyboard = []
        for shortener_id in configured_shorteners:
            # Check cooldown
            if self.shortener_manager.is_on_cooldown(user.id, shortener_id):
                remaining = self.shortener_manager.get_cooldown_remaining(user.id, shortener_id)
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                button_text = f"🚫 {shortener_id} (⏳ {hours}h {minutes}m)"
                keyboard.append([InlineKeyboardButton(button_text, callback_data="cooldown_info")])
            else:
                keyboard.append([InlineKeyboardButton(f"🔗 {shortener_id}", callback_data=f"select_shortener_{shortener_id}_multi_{token_num}")])
        
        # Add navigation buttons
        keyboard.append([InlineKeyboardButton("🔙 Back to Tokens", callback_data="get_free_multi_token")])
        keyboard.append([InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")])
        
        await callback_query.message.edit_text(selection_text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def start(self):
        """Start the bot"""
        try:
            logger.info("[START] Starting WZML-X Auth Bot...")
            
            await self.app.start()
            
            # Get bot info
            me = await self.app.get_me()
            logger.info(f"[SUCCESS] Bot started successfully: @{me.username}")
            logger.info(f"[INFO] Bot ID: {me.id}")
            logger.info(f"[INFO] Bot Name: {me.first_name}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot"""
        try:
            logger.info("[STOP] Stopping WZML-X Auth Bot...")
            
            if self.app:
                await self.app.stop()
            
            logger.info("[SUCCESS] Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"[ERROR] Error during shutdown: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"[SIGNAL] Received signal {signum}")
        self.shutdown_event.set()

async def main():
    """Main function"""
    # Create bot instance
    bot = WZMLAuthBot()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        bot.signal_handler(signum, frame)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and start bot
        if await bot.initialize():
            await bot.start()
        else:
            logger.error("[ERROR] Failed to initialize bot")
            return
        
    except KeyboardInterrupt:
        logger.info("[SIGNAL] Received keyboard interrupt")
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}")
    finally:
        # Cleanup
        await bot.stop()

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("[ERROR] Python 3.8 or higher is required")
        sys.exit(1)
    
    # Create sessions directory
    Path("sessions").mkdir(exist_ok=True)
    
    logger.info("[START] Starting WZML-X Auth Bot...")
    logger.info("[INFO] Exact flow as per sample images")
    
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[SIGNAL] Bot stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] Fatal error: {e}")
        sys.exit(1)
