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
from datetime import datetime, timedelta
import uuid

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot_manager import BotManager, get_bot_manager, initialize_bot_manager

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
        """Generate token for single bot and auto-verify in background"""
        user = callback_query.from_user
        bot_config = self.bot_manager.bots.get(bot_key)
        
        if not bot_config:
            await callback_query.message.edit_text("❌ Bot not found!")
            return
        
        bot_name = bot_config.name
        
        # Generate UUID4 token in background
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=6)  # 6 hours for free
        
        # Store token (auto-verify in background)
        if user.id not in self.user_tokens:
            self.user_tokens[user.id] = {"tokens": {}, "verified_bots": []}
        
        self.user_tokens[user.id]["tokens"][bot_key] = {
            "token": token,
            "expires_at": expires_at.isoformat(),
            "type": "free_single",
            "verified": True  # Auto-verified
        }
        
        if bot_key not in self.user_tokens[user.id]["verified_bots"]:
            self.user_tokens[user.id]["verified_bots"].append(bot_key)
        
        self.user_stats["total_tokens"] += 1
        
        # Show confirmation message (like in sample image)
        confirmation_text = f"""
**{user.first_name}**

**{bot_name}** token has been verified and is valid for the next **6h**.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✖ AVAILABLE BOTS", callback_data="show_available_bots")],
            [InlineKeyboardButton("🔄 Get Another Token", callback_data="verify_new")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(confirmation_text, reply_markup=keyboard)
    
    async def generate_multi_tokens(self, callback_query):
        """Generate tokens for all bots and auto-verify in background"""
        user = callback_query.from_user
        
        # Get all configured bots (both available and unavailable)
        all_bots = self.bot_manager.get_all_bots()
        available_bots = self.bot_manager.get_available_bots()
        
        if not all_bots:
            await callback_query.message.edit_text("❌ No bots configured! Please contact admin.")
            return
        
        # Generate tokens for all bots in background
        expires_at = datetime.now() + timedelta(hours=6)  # 6 hours for free
        
        if user.id not in self.user_tokens:
            self.user_tokens[user.id] = {"tokens": {}, "verified_bots": []}
        
        verified_bots = []
        for bot_key, bot_config in all_bots.items():
            token = str(uuid.uuid4())
            
            self.user_tokens[user.id]["tokens"][bot_key] = {
                "token": token,
                "expires_at": expires_at.isoformat(),
                "type": "free_multi",
                "verified": True  # Auto-verified
            }
            
            if bot_key not in self.user_tokens[user.id]["verified_bots"]:
                self.user_tokens[user.id]["verified_bots"].append(bot_key)
            
            verified_bots.append(bot_config.name)
        
        self.user_stats["total_tokens"] += len(all_bots)
        
        # Show confirmation message for all bots
        bot_list = "\n".join([f"• {name}" for name in verified_bots])
        multi_text = f"""
**{user.first_name}**

All **{len(all_bots)} Mirror Leech Bots** tokens have been verified and are valid for the next **6h**.

✅ **Verified Bots:**
{bot_list}

📊 **Status:** {len(available_bots)}/{len(all_bots)} bots currently online

You can now use all Mirror Leech Bots without restrictions!
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✖ AVAILABLE BOTS", callback_data="show_available_bots")],
            [InlineKeyboardButton("📊 Check Status", callback_data="refresh_check")],
            [InlineKeyboardButton("✖ CLOSE", callback_data="close_menu")]
        ])
        
        await callback_query.message.edit_text(multi_text, reply_markup=keyboard)
    
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
