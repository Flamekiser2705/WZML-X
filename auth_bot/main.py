#!/usr/bin/env python3
"""
Main entry point for the Auth Bot
Run this file to start the authentication bot
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

# Fix imports for standalone execution
try:
    # Try importing with relative imports first
    from utils.main_config import config, validate_config, print_config_status
    from utils.token_utils import TokenGenerator
    from database.models import TokenType
    
    # Import pyrogram
    from pyrogram import Client, filters
    from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
    
    print("[SUCCESS] All imports successful")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("[ERROR] Please ensure all auth bot components are properly installed")
    sys.exit(1)
    print(f"❌ Import error: {e}")
    print("❌ Please ensure all auth bot components are properly installed")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('auth_bot.log')
    ]
)

logger = logging.getLogger(__name__)


class AuthBot:
    """Main Auth Bot Application"""
    
    def __init__(self):
        self.app = None
        self.db_manager = None
        self.background_tasks = []
        self.shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize the bot and all components"""
        try:
            logger.info("🚀 Initializing Auth Bot...")
            
            # Initialize database
            database = await get_database()
            self.db_manager = DatabaseManager(database)
            
            # Initialize database indexes
            await self.db_manager.create_indexes()
            logger.info("✅ Database initialized")
            
            # Create Pyrogram client
            self.app = Client(
                "auth_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN,
                workdir="sessions"
            )
            
            # Initialize handlers
            await self.setup_handlers()
            
            # Start background tasks
            self.background_tasks = create_background_tasks()
            
            logger.info("✅ Auth Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Auth Bot: {e}")
            raise
    
    async def setup_handlers(self):
        """Setup all message handlers"""
        try:
            # Initialize handler classes
            auth_handler = AuthHandler(self.db_manager)
            token_handler = TokenHandler(self.db_manager)
            payment_handler = PaymentHandler(self.db_manager)
            admin_handler = AdminHandler(self.db_manager)
            
            # Register handlers with the app
            auth_handler.register_handlers(self.app)
            token_handler.register_handlers(self.app)
            payment_handler.register_handlers(self.app)
            admin_handler.register_handlers(self.app)
            
            logger.info("✅ All handlers registered")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup handlers: {e}")
            raise
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("🤖 Starting Auth Bot...")
            
            await self.app.start()
            
            # Get bot info
            me = await self.app.get_me()
            logger.info(f"✅ Bot started successfully: @{me.username}")
            
            # Send startup message to log
            logger.info(f"📱 Bot ID: {me.id}")
            logger.info(f"📱 Bot Name: {me.first_name}")
            logger.info(f"📱 Bot Username: @{me.username}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except ApiIdInvalid:
            logger.error("❌ Invalid API ID and Hash")
            sys.exit(1)
        except AuthKeyUnregistered:
            logger.error("❌ Bot token is invalid")
            sys.exit(1)
        except UserDeactivated:
            logger.error("❌ Bot account has been deactivated")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot and cleanup"""
        try:
            logger.info("🛑 Stopping Auth Bot...")
            
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # Stop the bot
            if self.app:
                await self.app.stop()
            
            # Close database connection
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
    # Create bot instance
    bot = AuthBot()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        bot.signal_handler(signum, frame)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and start bot
        await bot.initialize()
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("📡 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        # Cleanup
        await bot.stop()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Create sessions directory
    Path("sessions").mkdir(exist_ok=True)
    
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("📡 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
