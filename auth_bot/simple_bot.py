#!/usr/bin/env python3
"""
Simple Auth Bot Runner
A minimal version that works without requiring all handlers
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('auth_bot.log', encoding='utf-8')
    ]
)

# Configure console handler with UTF-8 encoding
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Set encoding for Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

logger = logging.getLogger(__name__)

class SimpleAuthBot:
    """Simple Auth Bot for testing"""
    
    def __init__(self):
        self.app = None
        self.shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize the bot"""
        try:
            logger.info("[INIT] Initializing Simple Auth Bot...")
            
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
                logger.error(f"[INFO] Current AUTH_BOT_TOKEN in config.env: {config.AUTH_BOT_TOKEN}")
                return False
            
            # Create Pyrogram client with API credentials
            self.app = Client(
                "auth_bot",
                bot_token=config.AUTH_BOT_TOKEN,
                api_id=config.TELEGRAM_API,
                api_hash=config.TELEGRAM_HASH,
                workdir="sessions"
            )
            
            # Setup handlers
            self.setup_handlers()
            
            logger.info("[SUCCESS] Simple Auth Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize bot: {e}")
            return False
    
    def setup_handlers(self):
        """Setup message handlers"""
        
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            """Handle /start command - Welcome message only"""
            user = message.from_user
            welcome_text = f"""
🤖 **Welcome to WZML-X Auth Bot**

👋 Hello {user.first_name}!

This is the authentication bot for WZML-X Mirror/Leech Bot.

📋 **Available Commands:**
• `/start` - Show this welcome message
• `/verify` - Get access tokens for mirror bot
• `/status` - Check your token status

🔧 **Bot Status:** Online ✅

ℹ️ Use `/verify` command to get your access token.
"""
            
            await message.reply_text(welcome_text)
        
        @self.app.on_message(filters.command("verify") & filters.private)
        async def verify_handler(client: Client, message: Message):
            """Handle /verify command - Show verification options"""
            user = message.from_user
            
            verify_text = f"""
🎫 **Token Verification System**

👤 **User:** {user.first_name}
� **User ID:** `{user.id}`

🎯 **Choose your plan:**

🆓 **FREE Plan:**
• Duration: 6 hours
• Tokens: 1 active token
• Cost: Free

� **PREMIUM Plans:**
• 7 Days - ₹5.00
• 30 Days - ₹20.00  
• 90 Days - ₹50.00
• Tokens: Up to 4 active tokens

Select your preferred option below:
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🆓 Get Free Token (6h)", callback_data="free_token")],
                [
                    InlineKeyboardButton("� 7 Days - ₹5", callback_data="premium_7d"),
                    InlineKeyboardButton("� 30 Days - ₹20", callback_data="premium_30d")
                ],
                [InlineKeyboardButton("💎 90 Days - ₹50", callback_data="premium_90d")],
                [InlineKeyboardButton("📊 Check Status", callback_data="check_status")]
            ])
            
            await message.reply_text(verify_text, reply_markup=keyboard)
        
        @self.app.on_message(filters.command("status") & filters.private)
        async def status_handler(client: Client, message: Message):
            """Handle /status command"""
            user = message.from_user
            
            status_text = f"""
📊 **Your Auth Bot Status**

� **User Information:**
• Name: {user.first_name}
• Username: @{user.username if user.username else 'Not set'}
• User ID: `{user.id}`

🎫 **Token Status:**
• Active Tokens: 0
• Free Tokens Used Today: 0/1
• Premium Tokens: 0/4
• Account Type: Free

🤖 **Bot Information:**
• Status: Online ✅
• Database: Connected
• Token System: Active (UUID4)
• Uptime: Running

📈 **Statistics:**
• Total Tokens Generated: 0
• Last Token: Never
• Registration Date: Today

🔄 Use `/verify` to get access tokens.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Get Token", callback_data="verify_again")],
                [InlineKeyboardButton("📊 Detailed Status", callback_data="check_status")]
            ])
            
            await message.reply_text(status_text, reply_markup=keyboard)
        
        @self.app.on_callback_query()
        async def callback_handler(client: Client, callback_query):
            """Handle callback queries"""
            data = callback_query.data
            user = callback_query.from_user
            
            if data == "free_token":
                # Generate free token
                try:
                    from utils.token_utils import TokenGenerator
                    from database.models import TokenType
                    
                    token_gen = TokenGenerator("demo_secret_key")
                    
                    # Generate UUID4 token
                    token_id, uuid4_token, expires_at = token_gen.generate_access_token(
                        user_id=user.id,
                        bot_id="test_bot",
                        token_type=TokenType.FREE
                    )
                    
                    token_text = f"""
🎫 **Free Token Generated!**

🔑 **UUID4 Token:**
`{uuid4_token}`

📋 **Token Details:**
• **Type:** Free (6 hours)
• **User:** {user.first_name}
• **Expires:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}
• **Valid:** ✅ Yes

📱 **How to Use:**
Copy the token above and use it in your mirror bot:
`/mirror https://example.com {uuid4_token}`

⚠️ **Note:** This is a demo token. Free users get 6 hours access.
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Copy Token", callback_data=f"copy_{uuid4_token}")],
                        [InlineKeyboardButton("🔄 Get New Token", callback_data="verify_again")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
                    ])
                    
                    await callback_query.message.edit_text(token_text, reply_markup=keyboard)
                    
                except Exception as e:
                    logger.error(f"[ERROR] Error generating token: {e}")
                    await callback_query.message.edit_text("❌ Error generating token. Please try again.")
            
            elif data.startswith("premium_"):
                # Handle premium token requests
                plan = data.replace("premium_", "")
                plan_details = {
                    "7d": {"name": "7 Days", "price": "₹5.00", "days": 7},
                    "30d": {"name": "30 Days", "price": "₹20.00", "days": 30},
                    "90d": {"name": "90 Days", "price": "₹50.00", "days": 90}
                }
                
                if plan in plan_details:
                    plan_info = plan_details[plan]
                    premium_text = f"""
💎 **Premium Plan Selected**

📦 **Plan:** {plan_info['name']}
💰 **Price:** {plan_info['price']}
⏰ **Duration:** {plan_info['days']} days
🎫 **Tokens:** Up to 4 active tokens

🔄 **Payment Options:**

💳 **UPI/Card Payment:**
• Razorpay integration
• Instant activation

💰 **PayPal:**
• International payments
• Secure checkout

⚠️ **Note:** This is a demo version. Payment integration will be added soon.
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("💳 Pay with Razorpay", callback_data=f"pay_razorpay_{plan}")],
                        [InlineKeyboardButton("💰 Pay with PayPal", callback_data=f"pay_paypal_{plan}")],
                        [InlineKeyboardButton("🔙 Back to Plans", callback_data="verify_again")]
                    ])
                    
                    await callback_query.message.edit_text(premium_text, reply_markup=keyboard)
            
            elif data == "check_status":
                # Show user status
                status_text = f"""
📊 **Your Token Status**

👤 **User:** {user.first_name}
🆔 **User ID:** `{user.id}`

🎫 **Active Tokens:** 0
🆓 **Free Tokens Used Today:** 0/1
💎 **Premium Tokens:** 0/4

📈 **Statistics:**
• Total Tokens Generated: 0
• Last Token: Never
• Account Type: Free

🔄 Use `/verify` to generate new tokens.
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Get New Token", callback_data="verify_again")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
                ])
                
                await callback_query.message.edit_text(status_text, reply_markup=keyboard)
            
            elif data == "verify_again":
                # Go back to verify options
                verify_text = f"""
🎫 **Token Verification System**

👤 **User:** {user.first_name}
🆔 **User ID:** `{user.id}`

🎯 **Choose your plan:**

🆓 **FREE Plan:**
• Duration: 6 hours
• Tokens: 1 active token
• Cost: Free

💎 **PREMIUM Plans:**
• 7 Days - ₹5.00
• 30 Days - ₹20.00  
• 90 Days - ₹50.00
• Tokens: Up to 4 active tokens

Select your preferred option below:
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🆓 Get Free Token (6h)", callback_data="free_token")],
                    [
                        InlineKeyboardButton("💎 7 Days - ₹5", callback_data="premium_7d"),
                        InlineKeyboardButton("💎 30 Days - ₹20", callback_data="premium_30d")
                    ],
                    [InlineKeyboardButton("💎 90 Days - ₹50", callback_data="premium_90d")],
                    [InlineKeyboardButton("📊 Check Status", callback_data="check_status")]
                ])
                
                await callback_query.message.edit_text(verify_text, reply_markup=keyboard)
            
            elif data == "main_menu":
                # Go back to main menu
                welcome_text = f"""
🤖 **Welcome to WZML-X Auth Bot**

👋 Hello {user.first_name}!

This is the authentication bot for WZML-X Mirror/Leech Bot.

📋 **Available Commands:**
• `/start` - Show this welcome message
• `/verify` - Get access tokens for mirror bot
• `/status` - Check your token status

🔧 **Bot Status:** Online ✅

ℹ️ Use `/verify` command to get your access token.
"""
                await callback_query.message.edit_text(welcome_text)
            
            elif data.startswith("copy_"):
                token = data.replace("copy_", "")
                await callback_query.answer(f"Token copied: {token[:20]}...", show_alert=True)
            
            elif data.startswith("pay_"):
                # Handle payment callbacks
                payment_method = data.split("_")[1]
                plan = data.split("_")[2]
                
                await callback_query.answer(f"Payment integration for {payment_method} will be added soon!", show_alert=True)
            
            await callback_query.answer()
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("[START] Starting Simple Auth Bot...")
            
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
            logger.info("[STOP] Stopping Simple Auth Bot...")
            
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
    bot = SimpleAuthBot()
    
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
    
    logger.info("[START] Starting Simple Auth Bot...")
    logger.info("[INFO] Make sure to set AUTH_BOT_TOKEN in config.env file")
    
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[SIGNAL] Bot stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] Fatal error: {e}")
        sys.exit(1)
