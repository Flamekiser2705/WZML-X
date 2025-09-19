#!/usr/bin/env python3
"""
WZML-X Auth Bot - Complete Implementation
Handles token generation and verification for main mirror bots
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode

# Import auth bot modules
from database.connection import get_database
from database.operations import DatabaseManager
from database.models import User, Token, Bot, TokenType, SubscriptionType
from utils.token_utils import TokenGenerator
from bot_manager import BotManager

# Setup logging
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
    """Main Auth Bot Application"""
    
    def __init__(self):
        self.app = None
        self.db_manager = None
        self.token_generator = None
        self.bot_manager = None
        self.shutdown_event = asyncio.Event()
        
        # Load configuration from main bot config
        self.load_config()
    
    def load_config(self):
        """Load configuration from main bot's config.env"""
        try:
            # Read main bot's config.env
            config_file = Path(__file__).parent.parent / "config.env"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
            
            # Set auth bot specific config
            self.auth_bot_token = os.getenv('AUTH_BOT_TOKEN', '')
            self.telegram_api = int(os.getenv('TELEGRAM_API', '0'))
            self.telegram_hash = os.getenv('TELEGRAM_HASH', '')
            self.database_url = os.getenv('DATABASE_URL', '')
            self.owner_id = int(os.getenv('OWNER_ID', '0'))
            
            logger.info("✅ Configuration loaded from main bot config")
            
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            raise
    
    async def initialize(self):
        """Initialize the auth bot"""
        try:
            logger.info("🚀 Initializing WZML-X Auth Bot...")
            
            # Validate configuration
            if not self.auth_bot_token:
                raise ValueError("AUTH_BOT_TOKEN not found in config.env")
            if not self.database_url:
                raise ValueError("DATABASE_URL not found in config.env")
            if not self.telegram_api or not self.telegram_hash:
                raise ValueError("TELEGRAM_API and TELEGRAM_HASH not found in config.env")
            
            # Initialize database
            database = await get_database()
            self.db_manager = DatabaseManager(database)
            await self.db_manager.create_indexes()
            
            # Initialize token generator
            self.token_generator = TokenGenerator("auth_bot_secret_key")
            
            # Initialize bot manager
            self.bot_manager = BotManager()
            await self.bot_manager.check_all_bots()
            
            # Create Pyrogram client
            self.app = Client(
                "wzml_auth_bot",
                api_id=self.telegram_api,
                api_hash=self.telegram_hash,
                bot_token=self.auth_bot_token,
                workdir="sessions",
                parse_mode=ParseMode.HTML
            )
            
            # Setup handlers
            self.setup_handlers()
            
            logger.info("✅ Auth Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Auth Bot: {e}")
            raise
    
    def setup_handlers(self):
        """Setup message and callback handlers"""
        
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            """Handle /start command"""
            user = message.from_user
            
            # Check for verification callback
            if len(message.command) > 1:
                start_param = message.command[1]
                if start_param.startswith("verify_"):
                    await self.handle_verification_callback(message, start_param)
                    return
            
            # Register user
            await self.register_user(user)
            
            # Get available bots
            available_bots = self.bot_manager.get_available_bots()
            
            if not available_bots:
                welcome_text = """
🤖 **Welcome to WZML-X Auth Bot!**

❌ **No Mirror Leech Bots Available**

All bots are currently offline or not configured.

Please contact the admin to configure mirror bots.
"""
                await message.reply_text(welcome_text)
                return
            
            welcome_text = f"""
🤖 **Welcome to WZML-X Auth Bot!**

👋 Hello {user.first_name}!

This bot manages authentication tokens for WZML-X mirror bots.

**Available Bots:** {len(available_bots)}
**Features:**
• Free tokens (6 hours validity)
• Premium plans (7/30/90 days)
• Secure UUID4 token generation

Use /verify to get started!
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Generate Token", callback_data="verify_start")],
                [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
                [InlineKeyboardButton("🆘 Help", callback_data="show_help")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
        
        @self.app.on_message(filters.command("verify") & filters.private)
        async def verify_handler(client: Client, message: Message):
            """Handle /verify command"""
            await self.show_verification_options(message)
        
        @self.app.on_callback_query()
        async def callback_handler(client: Client, callback_query: CallbackQuery):
            """Handle callback queries"""
            await self.handle_callback_query(callback_query)
    
    async def register_user(self, user):
        """Register or update user in database"""
        try:
            existing_user = await self.db_manager.get_user(user.id)
            
            if not existing_user:
                user_data = User(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    subscription_type=SubscriptionType.FREE
                )
                await self.db_manager.create_user(user_data)
                logger.info(f"✅ New user registered: {user.id}")
            else:
                await self.db_manager.update_user(user.id, {
                    "username": user.username,
                    "first_name": user.first_name
                })
                logger.info(f"ℹ️ User updated: {user.id}")
                
        except Exception as e:
            logger.error(f"❌ Error registering user: {e}")
    
    async def show_verification_options(self, message: Message):
        """Show token generation options"""
        try:
            available_bots = self.bot_manager.get_available_bots()
            
            if not available_bots:
                await message.reply_text("❌ No bots available for token generation.")
                return
            
            keyboard_buttons = []
            
            # Add bot selection buttons
            for bot_key, bot_config in available_bots.items():
                callback_data = f"generate_token:{bot_key}"
                keyboard_buttons.append([
                    InlineKeyboardButton(f"🤖 {bot_config.name}", callback_data=callback_data)
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton("🔙 Back", callback_data="start_menu")
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            verify_text = """
🔑 **Choose Bot for Token Generation:**

Select which bot you want to generate a token for:
"""
            
            await message.reply_text(verify_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"❌ Error showing verification options: {e}")
            await message.reply_text("❌ An error occurred. Please try again.")
    
    async def generate_token_for_bot(self, user_id: int, bot_key: str, message: Message):
        """Generate token for specific bot"""
        try:
            # Generate UUID4 token
            token_id, uuid4_token, expires_at = self.token_generator.generate_access_token(
                user_id=user_id,
                bot_id=bot_key,
                token_type=TokenType.FREE
            )
            
            # Create token record in database
            token_data = Token(
                token_id=token_id,
                user_id=user_id,
                bot_key=bot_key,
                token=uuid4_token,
                type=TokenType.FREE,
                verified=False,  # Will be set to True after shortener verification
                expires_at=expires_at
            )
            
            # Save to database
            if await self.db_manager.create_token(token_data):
                # Create verification URL with shortener
                verification_url = self.create_verification_url(uuid4_token, user_id)
                
                token_text = f"""
🎫 **Token Generated Successfully!**

**Token:** `{uuid4_token}`
**Bot:** {self.bot_manager.bots[bot_key].name}
**Type:** Free (6 hours)
**Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}

⚠️ **Verification Required:**
Click the link below to verify your token:

{verification_url}

**Note:** Token will be active only after verification.
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Verify Token", url=verification_url)],
                    [InlineKeyboardButton("🔙 Back", callback_data="verify_start")]
                ])
                
                await message.edit_text(token_text, reply_markup=keyboard)
                
                logger.info(f"✅ Token generated for user {user_id}, bot {bot_key}")
            else:
                await message.edit_text("❌ Failed to generate token. Please try again.")
                
        except Exception as e:
            logger.error(f"❌ Error generating token: {e}")
            await message.edit_text("❌ An error occurred while generating token.")
    
    def create_verification_url(self, token: str, user_id: int) -> str:
        """Create verification URL with shortener"""
        try:
            # Import shortener from main bot
            from shortener_handler import short_url
            
            # Create verification URL that redirects back to auth bot
            base_url = f"https://t.me/{self.app.me.username}?start=verify_{token}_{user_id}"
            
            # Use shortener to create verification link
            shortened_url = short_url(base_url)
            
            return shortened_url if shortened_url != base_url else base_url
            
        except Exception as e:
            logger.error(f"❌ Error creating verification URL: {e}")
            # Fallback to direct URL
            return f"https://t.me/{self.app.me.username}?start=verify_{token}_{user_id}"
    
    async def handle_verification_callback(self, message: Message, start_param: str):
        """Handle verification callback from shortener"""
        try:
            # Parse verification data
            parts = start_param.split("_")
            if len(parts) != 3 or parts[0] != "verify":
                await message.reply_text("❌ Invalid verification link.")
                return
            
            token = parts[1]
            user_id = int(parts[2])
            
            # Verify the user matches
            if message.from_user.id != user_id:
                await message.reply_text("❌ This verification link is not for you.")
                return
            
            # Mark token as verified
            if await self.db_manager.verify_token(token):
                success_text = f"""
✅ **Token Verified Successfully!**

Your token has been activated and is now ready to use.

**Token:** `{token}`
**Status:** Active
**Valid Until:** 6 hours from now

You can now use this token in the mirror bot commands.

**Example Usage:**
`/mirror https://example.com {token}`
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Copy Token", callback_data=f"copy_token:{token}")],
                    [InlineKeyboardButton("🔑 Generate New Token", callback_data="verify_start")]
                ])
                
                await message.reply_text(success_text, reply_markup=keyboard)
                
                logger.info(f"✅ Token verified successfully: {token[:8]}... for user {user_id}")
            else:
                await message.reply_text("❌ Token verification failed. Please generate a new token.")
                
        except Exception as e:
            logger.error(f"❌ Error handling verification callback: {e}")
            await message.reply_text("❌ Verification failed. Please try again.")
    
    async def handle_callback_query(self, callback_query: CallbackQuery):
        """Handle callback queries"""
        try:
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            if data == "verify_start":
                await self.show_verification_options(callback_query.message)
            
            elif data.startswith("generate_token:"):
                bot_key = data.split(":")[1]
                await self.generate_token_for_bot(user_id, bot_key, callback_query.message)
            
            elif data == "check_status":
                await self.show_user_status(user_id, callback_query.message)
            
            elif data == "show_help":
                await self.show_help(callback_query.message)
            
            elif data == "start_menu":
                # Go back to start menu
                await callback_query.message.delete()
                await self.app.send_message(user_id, "/start")
            
            elif data.startswith("copy_token:"):
                token = data.split(":")[1]
                await callback_query.answer(f"Token: {token}\n\nCopied to clipboard!", show_alert=True)
            
            await callback_query.answer()
            
        except Exception as e:
            logger.error(f"❌ Error handling callback query: {e}")
            await callback_query.answer("❌ An error occurred.", show_alert=True)
    
    async def show_user_status(self, user_id: int, message: Message):
        """Show user's token status"""
        try:
            user = await self.db_manager.get_user(user_id)
            if not user:
                await message.edit_text("❌ User not found.")
                return
            
            stats = await self.db_manager.get_user_stats(user_id)
            
            status_text = f"""
📊 **Your Token Status**

**User ID:** {user_id}
**Subscription:** {'💎 Premium' if user.subscription_type == SubscriptionType.PREMIUM else '🆓 Free'}

**Token Statistics:**
• Active Tokens: {stats.get('active_tokens', 0)}
• Total Generated: {stats.get('total_tokens', 0)}
• Premium Tokens: {stats.get('premium_tokens', 0)}
• Free Tokens: {stats.get('free_tokens', 0)}

**Available Actions:**
Use /verify to generate new tokens
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Generate Token", callback_data="verify_start")],
                [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
            ])
            
            await message.edit_text(status_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"❌ Error showing user status: {e}")
            await message.edit_text("❌ Error retrieving status.")
    
    async def show_help(self, message: Message):
        """Show help information"""
        help_text = """
🆘 **Help & Commands**

**Available Commands:**
• `/start` - Start the bot
• `/verify` - Generate authentication tokens

**How to Use:**
1. Send `/verify` to generate a token
2. Select the bot you want to use
3. Complete verification via shortener link
4. Copy your UUID4 token
5. Use token in mirror bot commands

**Token Format:**
`550e8400-e29b-41d4-a716-446655440000`

**Example Usage in Mirror Bot:**
`/mirror https://example.com 550e8400-e29b-41d4-a716-446655440000`

**Need Support?**
Contact the bot administrator for assistance.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Generate Token", callback_data="verify_start")],
            [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
        ])
        
        await message.edit_text(help_text, reply_markup=keyboard)
    
    async def start(self):
        """Start the auth bot"""
        try:
            logger.info("🤖 Starting WZML-X Auth Bot...")
            
            await self.app.start()
            
            # Get bot info
            me = await self.app.get_me()
            logger.info(f"✅ Auth Bot started successfully: @{me.username}")
            logger.info(f"📱 Bot ID: {me.id}")
            logger.info(f"📱 Bot Name: {me.first_name}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Failed to start auth bot: {e}")
            raise
    
    async def stop(self):
        """Stop the auth bot"""
        try:
            logger.info("🛑 Stopping WZML-X Auth Bot...")
            
            if self.app:
                await self.app.stop()
            
            if self.db_manager:
                await self.db_manager.close()
            
            logger.info("✅ Auth Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}")
        self.shutdown_event.set()

async def main():
    """Main function"""
    # Create auth bot instance
    auth_bot = WZMLAuthBot()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        auth_bot.signal_handler(signum, frame)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and start auth bot
        await auth_bot.initialize()
        await auth_bot.start()
        
    except KeyboardInterrupt:
        logger.info("📡 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        # Cleanup
        await auth_bot.stop()

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Create sessions directory
    Path("sessions").mkdir(exist_ok=True)
    
    try:
        # Run the auth bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("📡 Auth Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)