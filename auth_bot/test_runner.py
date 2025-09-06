#!/usr/bin/env python3
"""
Simple Auth Bot Test Runner
Tests basic bot functionality without requiring full setup
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_auth_bot_components():
    """Test auth bot components without running the full bot"""
    try:
        logger.info("🚀 Testing Auth Bot Components...")
        
        # Test database connection
        logger.info("📦 Testing database connection...")
        from database.connection import get_database
        db = await get_database()
        logger.info("✅ Database connection successful")
        
        # Test configuration
        logger.info("⚙️ Testing configuration...")
        from utils.config import config, validate_config
        errors = validate_config()
        if errors:
            logger.warning("⚠️ Configuration warnings:")
            for error in errors:
                logger.warning(f"   • {error}")
        else:
            logger.info("✅ Configuration is valid")
        
        # Test token generation
        logger.info("🎫 Testing token generation...")
        from utils.token_utils import TokenGenerator
        from database.models import TokenType
        
        token_gen = TokenGenerator("test_secret_key")
        
        # Generate UUID4 token
        token_id, uuid4_token, expires_at = token_gen.generate_access_token(
            user_id=123456789,
            bot_id="test_bot",
            token_type=TokenType.FREE
        )
        
        logger.info(f"✅ Generated UUID4 token: {uuid4_token}")
        logger.info(f"   • Token ID: {token_id}")
        logger.info(f"   • Expires: {expires_at}")
        logger.info(f"   • Valid UUID4: {token_gen.is_valid_uuid4(uuid4_token)}")
        
        # Test token validation
        token_info = token_gen.decrypt_token(uuid4_token)
        logger.info(f"✅ Token validation: {token_info}")
        
        # Test database operations
        logger.info("💾 Testing database operations...")
        from database.operations import DatabaseManager
        
        db_manager = DatabaseManager(db)
        await db_manager.create_indexes()
        logger.info("✅ Database indexes created")
        
        logger.info("🎉 All auth bot components tested successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_creation():
    """Test creating a Pyrogram client without starting it"""
    try:
        logger.info("🤖 Testing bot creation...")
        
        from utils.config import config
        
        # Check if bot token is provided
        if not config.AUTH_BOT_TOKEN or config.AUTH_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.warning("⚠️ No valid bot token provided")
            logger.info("💡 To test with real bot, add your token to .env file:")
            logger.info("   AUTH_BOT_TOKEN=your_bot_token_here")
            return False
        
        from pyrogram import Client
        
        # Create bot client (don't start it)
        app = Client(
            "test_auth_bot",
            bot_token=config.AUTH_BOT_TOKEN,
            workdir="sessions"
        )
        
        logger.info("✅ Bot client created successfully")
        logger.info(f"   • Bot token: {config.AUTH_BOT_TOKEN[:10]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot creation failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🧪 Starting Auth Bot Tests")
    logger.info("=" * 50)
    
    # Test components
    components_ok = await test_auth_bot_components()
    
    # Test bot creation
    bot_ok = await test_bot_creation()
    
    logger.info("=" * 50)
    if components_ok:
        logger.info("✅ Auth bot components are working correctly!")
        
        if bot_ok:
            logger.info("✅ Bot creation successful - ready to run with valid token!")
        else:
            logger.info("⚠️ Need valid bot token to start actual bot")
            
        logger.info("\n📋 Next steps:")
        logger.info("1. Get bot token from @BotFather")
        logger.info("2. Add token to .env file: AUTH_BOT_TOKEN=your_token")
        logger.info("3. Setup MongoDB (or use mock for testing)")
        logger.info("4. Run: python main.py")
        
    else:
        logger.error("❌ Some components failed - check logs above")

if __name__ == "__main__":
    # Create sessions directory
    Path("sessions").mkdir(exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Test stopped by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)
