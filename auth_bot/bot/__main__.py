#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from .config import (
    BOT_TOKEN, BOT_USERNAME, MONGODB_URI, ADMIN_IDS,
    REGISTERED_BOTS, PLANS_CONFIG, JWT_SECRET, MESSAGES
)
from ..database.operations import DatabaseManager
from ..database.models import Bot, Plan
from ..utils.token_utils import TokenGenerator
from .handlers import auth_handler, payment_handler, token_handler, admin_handler

# Setup logging
logger = logging.getLogger(__name__)

# Global instances
db_manager: DatabaseManager = None
token_generator: TokenGenerator = None
app: Client = None


async def initialize_database():
    """Initialize database connection and setup"""
    global db_manager
    
    try:
        db_manager = DatabaseManager(MONGODB_URI)
        await db_manager.connect()
        
        # Register bots from config
        for bot_id, bot_info in REGISTERED_BOTS.items():
            bot_data = Bot(
                bot_id=bot_id,
                name=bot_info["name"],
                username=bot_info["name"].lower().replace(" ", "_"),
                api_endpoint=bot_info["api_endpoint"]
            )
            await db_manager.register_bot(bot_data)
        
        # Create default plans
        for plan_id, plan_config in PLANS_CONFIG.items():
            plan_data = Plan(
                plan_id=plan_id,
                name=plan_config["name"],
                duration_days=plan_config["duration_days"],
                price=plan_config["price"],
                features=plan_config["features"]
            )
            await db_manager.create_plan(plan_data)
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


async def initialize_components():
    """Initialize all bot components"""
    global token_generator
    
    # Initialize token generator
    token_generator = TokenGenerator(JWT_SECRET)
    logger.info("✅ Token generator initialized")
    
    # Initialize database
    await initialize_database()
    
    # Initialize handlers with dependencies
    auth_handler.db_manager = db_manager
    auth_handler.token_generator = token_generator
    
    payment_handler.db_manager = db_manager
    payment_handler.token_generator = token_generator
    
    token_handler.db_manager = db_manager
    token_handler.token_generator = token_generator
    
    admin_handler.db_manager = db_manager
    admin_handler.token_generator = token_generator
    
    logger.info("✅ All components initialized")


async def main():
    """Main bot function"""
    global app
    
    logger.info("🔐 Starting WZML-X Auth Bot...")
    
    # Initialize Pyrogram client
    app = Client(
        "auth_bot",
        api_id=12345,  # You'll need to get this from https://my.telegram.org
        api_hash="your_api_hash",  # You'll need to get this from https://my.telegram.org
        bot_token=BOT_TOKEN,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Initialize components
    await initialize_components()
    
    # Register handlers
    register_handlers()
    
    # Start the bot
    await app.start()
    
    bot_info = await app.get_me()
    logger.info(f"✅ Bot started successfully: @{bot_info.username}")
    
    # Keep the bot running
    await asyncio.Event().wait()


def register_handlers():
    """Register all message and callback handlers"""
    global app
    
    # Basic commands
    app.add_handler(auth_handler.start_handler)
    app.add_handler(auth_handler.help_handler)
    app.add_handler(auth_handler.verify_handler)
    app.add_handler(auth_handler.status_handler)
    
    # Callback handlers
    app.add_handler(auth_handler.token_option_callback_handler)
    app.add_handler(auth_handler.bot_selection_callback_handler)
    app.add_handler(auth_handler.premium_plan_callback_handler)
    
    # Payment handlers
    app.add_handler(payment_handler.payment_callback_handler)
    app.add_handler(payment_handler.payment_success_handler)
    
    # Admin handlers
    app.add_handler(admin_handler.admin_stats_handler)
    app.add_handler(admin_handler.admin_users_handler)
    app.add_handler(admin_handler.admin_tokens_handler)
    
    logger.info("✅ All handlers registered")


async def cleanup():
    """Cleanup function"""
    global db_manager, app
    
    logger.info("🔄 Cleaning up...")
    
    if db_manager:
        await db_manager.disconnect()
    
    if app:
        await app.stop()
    
    logger.info("✅ Cleanup completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
    finally:
        asyncio.run(cleanup())
