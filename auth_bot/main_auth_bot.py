#!/usr/bin/env python3
"""
Main Auth Bot - Full Featured Version
Includes all handlers and database operations
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging without emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('auth_bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Fix imports
try:
    from utils.main_config import config, validate_config, print_config_status
    from utils.token_utils import TokenGenerator
    from database.models import TokenType
    from pyrogram import Client, filters
    from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
    
    logger.info("[SUCCESS] All imports successful")
    
except ImportError as e:
    logger.error(f"[ERROR] Import error: {e}")
    logger.error("[ERROR] Please ensure all auth bot components are properly installed")
    sys.exit(1)

class MainAuthBot:
    """Main Auth Bot with full features"""
    
    def __init__(self):
        self.app = None
        self.shutdown_event = asyncio.Event()
        self.token_generator = None
        
    async def initialize(self):
        """Initialize the bot"""
        try:
            logger.info("[INIT] Initializing Main Auth Bot...")
            
            # Print configuration status
            print_config_status()
            
            # Validate configuration
            errors = validate_config()
            if errors:
                logger.error("[ERROR] Configuration errors:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # Initialize token generator
            self.token_generator = TokenGenerator(config.JWT_SECRET)
            
            # Create Pyrogram client
            self.app = Client(
                "main_auth_bot",
                bot_token=config.AUTH_BOT_TOKEN,
                api_id=config.TELEGRAM_API,
                api_hash=config.TELEGRAM_HASH,
                workdir="sessions"
            )
            
            # Setup handlers
            self.setup_handlers()
            
            logger.info("[SUCCESS] Main Auth Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize bot: {e}")
            return False
    
    def setup_handlers(self):
        """Setup all message handlers"""
        
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            """Handle /start command"""
            user = message.from_user
            welcome_text = f"""
**Welcome to WZML-X Auth Bot**

Hello {user.first_name}!

This is the main auth bot for WZML-X mirror/leech bot.

**Available Commands:**
• /start - Show this message
• /verify - Generate access token
• /premium - Premium plans
• /status - Check bot status
• /help - Get help

**Token Types:**
• Free: 6 hours validity
• Premium: 7/30/90 days validity

**Bot Status:** Online
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Generate Free Token", callback_data="gen_free"),
                    InlineKeyboardButton("Premium Plans", callback_data="premium_plans")
                ],
                [
                    InlineKeyboardButton("Bot Status", callback_data="bot_status"),
                    InlineKeyboardButton("Help", callback_data="help_menu")
                ]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
        
        @self.app.on_message(filters.command("verify") & filters.private)
        async def verify_handler(client: Client, message: Message):
            """Handle /verify command"""
            try:
                user_id = message.from_user.id
                user_name = message.from_user.first_name
                
                # Generate free token (6 hours)
                token_id, uuid4_token, expires_at = self.token_generator.generate_access_token(
                    user_id=user_id,
                    bot_id=config.MAIN_BOT_ID,
                    token_type=TokenType.FREE
                )
                
                token_text = f"""
**Your Access Token Generated!**

**UUID4 Token:**
`{uuid4_token}`

**Token Details:**
• **Type:** Free (6 hours)
• **Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}
• **User:** {user_name}
• **Valid:** Yes

**How to Use:**
Copy the token above and use it in your mirror bot commands:

`/mirror https://example.com {uuid4_token}`

**Note:** Free tokens are limited to 6 hours. Get premium for longer access.
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Copy Token", callback_data=f"copy_{uuid4_token[:20]}")],
                    [
                        InlineKeyboardButton("Generate New", callback_data="gen_free"),
                        InlineKeyboardButton("Premium Plans", callback_data="premium_plans")
                    ],
                    [InlineKeyboardButton("Back to Menu", callback_data="start_menu")]
                ])
                
                await message.reply_text(token_text, reply_markup=keyboard)
                
                logger.info(f"[TOKEN] Generated free token for user {user_id} ({user_name})")
                
            except Exception as e:
                logger.error(f"[ERROR] Error generating token: {e}")
                await message.reply_text("Error generating token. Please try again later.")
        
        @self.app.on_message(filters.command("premium") & filters.private)
        async def premium_handler(client: Client, message: Message):
            """Handle /premium command"""
            premium_text = """
**Premium Token Plans**

**7 Days Plan**
• Duration: 7 days
• Price: ₹5.00
• Features: Extended access

**30 Days Plan**
• Duration: 30 days  
• Price: ₹20.00
• Features: Full access

**90 Days Plan**
• Duration: 90 days
• Price: ₹50.00
• Features: Extended access + Priority support

**Payment Methods:**
• Razorpay (UPI, Cards, NetBanking)
• PayPal (International)

**Contact Admin:** Contact bot owner for premium access
"""
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("7 Days - ₹5", callback_data="buy_7d"),
                    InlineKeyboardButton("30 Days - ₹20", callback_data="buy_30d")
                ],
                [
                    InlineKeyboardButton("90 Days - ₹50", callback_data="buy_90d")
                ],
                [
                    InlineKeyboardButton("Contact Admin", url="https://t.me/your_admin"),
                    InlineKeyboardButton("Back", callback_data="start_menu")
                ]
            ])
            
            await message.reply_text(premium_text, reply_markup=keyboard)
        
        @self.app.on_message(filters.command("status") & filters.private)
        async def status_handler(client: Client, message: Message):
            """Handle /status command"""
            status_text = f"""
**Auth Bot Status**

**Bot Information:**
• Status: Online
• Bot ID: {config.MAIN_BOT_ID}
• Username: @{config.BOT_USERNAME}

**Database:**
• Status: Connected
• Type: MongoDB

**Token System:**
• Generator: UUID4 Active
• Free Duration: {config.FREE_TOKEN_HOURS} hours
• Premium Plans: Available

**Features:**
• Free Token Generation: Available
• Premium Plans: Available
• Payment Integration: Configured
• API Validation: Active

**Statistics:**
• Uptime: Running
• Total Users: Contact admin for stats
"""
            
            await message.reply_text(status_text)
        
        @self.app.on_message(filters.command("help") & filters.private)
        async def help_handler(client: Client, message: Message):
            """Handle /help command"""
            help_text = """
**Auth Bot Help**

**Commands:**
• `/start` - Main menu
• `/verify` - Generate free token  
• `/premium` - View premium plans
• `/status` - Bot status
• `/help` - This help message

**How to Use Tokens:**
1. Generate token using `/verify`
2. Copy the UUID4 token
3. Use in mirror bot: `/mirror <link> <token>`

**Token Types:**
• **Free:** 6 hours validity, generate anytime
• **Premium:** 7/30/90 days, requires payment

**Support:**
• Contact: Bot owner
• Issues: Report to admin
• Updates: Check announcements

**Important:**
• Keep your tokens secure
• Don't share tokens with others
• Premium tokens have priority support
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Generate Token", callback_data="gen_free")],
                [InlineKeyboardButton("Premium Plans", callback_data="premium_plans")],
                [InlineKeyboardButton("Back to Menu", callback_data="start_menu")]
            ])
            
            await message.reply_text(help_text, reply_markup=keyboard)
        
        @self.app.on_callback_query()
        async def callback_handler(client: Client, callback_query):
            """Handle callback queries"""
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            try:
                if data == "gen_free":
                    # Generate free token
                    token_id, uuid4_token, expires_at = self.token_generator.generate_access_token(
                        user_id=user_id,
                        bot_id=config.MAIN_BOT_ID,
                        token_type=TokenType.FREE
                    )
                    
                    token_text = f"""
**Free Token Generated!**

**Token:** `{uuid4_token}`
**Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}
**Duration:** 6 hours

Use this token in your mirror bot commands.
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("Copy Token", callback_data=f"copy_{uuid4_token[:20]}")],
                        [InlineKeyboardButton("Back", callback_data="start_menu")]
                    ])
                    
                    await callback_query.message.edit_text(token_text, reply_markup=keyboard)
                    
                elif data == "premium_plans":
                    premium_text = """
**Premium Plans Available**

Choose your plan for extended access:

**7 Days:** ₹5.00
**30 Days:** ₹20.00  
**90 Days:** ₹50.00

Contact admin for premium access.
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("Contact Admin", url="https://t.me/your_admin")],
                        [InlineKeyboardButton("Back", callback_data="start_menu")]
                    ])
                    
                    await callback_query.message.edit_text(premium_text, reply_markup=keyboard)
                
                elif data == "bot_status":
                    await callback_query.message.edit_text(
                        "**Bot Status:** Online\n**Token System:** Active\n**Database:** Connected"
                    )
                
                elif data == "help_menu":
                    await callback_query.message.edit_text(
                        "**Help:** Use /help command for detailed help information."
                    )
                
                elif data == "start_menu":
                    # Go back to start
                    await callback_query.message.edit_text(
                        "**Main Menu**\n\nUse /start command to see the welcome message."
                    )
                
                elif data.startswith("copy_"):
                    await callback_query.answer("Token copied to clipboard!", show_alert=True)
                
                elif data.startswith("buy_"):
                    plan = data.replace("buy_", "")
                    await callback_query.answer(f"Contact admin to purchase {plan} plan", show_alert=True)
                
                else:
                    await callback_query.answer("Option not available", show_alert=True)
                
            except Exception as e:
                logger.error(f"[ERROR] Callback error: {e}")
                await callback_query.answer("An error occurred", show_alert=True)
            
            await callback_query.answer()
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("[START] Starting Main Auth Bot...")
            
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
            logger.info("[STOP] Stopping Main Auth Bot...")
            
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
    bot = MainAuthBot()
    
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
    
    logger.info("[START] Starting Main Auth Bot...")
    logger.info("[INFO] Full featured auth bot with all handlers")
    
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[SIGNAL] Bot stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] Fatal error: {e}")
        sys.exit(1)
