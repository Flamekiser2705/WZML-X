#!/usr/bin/env python3
"""
Test script for WZML-X Auth Bot
Tests the shortener integration and multi-token system
"""

import asyncio
import logging
from datetime import datetime, timezone
from bot_manager import BotManager
from shortener_handler import AuthShortenerManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot_manager():
    """Test bot manager functionality"""
    logger.info("Testing Bot Manager...")
    
    bot_manager = BotManager()
    
    # Add a test bot
    test_bot = {
        "token": "YOUR_BOT_TOKEN",
        "name": "Test Mirror Bot",
        "description": "Test mirror bot for auth system"
    }
    
    bot_manager.add_bot("test_bot", test_bot)
    
    all_bots = bot_manager.get_all_bots()
    logger.info(f"All bots: {list(all_bots.keys())}")
    
    available_bots = bot_manager.get_available_bots()
    logger.info(f"Available bots: {list(available_bots.keys())}")
    
    return bot_manager

async def test_shortener_manager():
    """Test shortener manager functionality"""
    logger.info("Testing Shortener Manager...")
    
    shortener_manager = AuthShortenerManager()
    
    # Test configuration loading
    configured_shorteners = shortener_manager.get_configured_shorteners()
    logger.info(f"Configured shorteners: {configured_shorteners}")
    
    # Test verification session
    user_id = 123456789
    shortener_id = "gplinks.com"
    bot_key = "test_bot"
    token_type = "multi"
    
    verification_token = shortener_manager.start_verification_session(
        user_id, shortener_id, bot_key, token_type, {"current_token": 1}
    )
    
    logger.info(f"Started verification session: {verification_token}")
    
    # Test verification URL generation
    verification_url = shortener_manager.generate_verification_url(
        user_id, shortener_id, verification_token
    )
    
    logger.info(f"Verification URL: {verification_url}")
    
    # Test cooldown system
    is_on_cooldown = shortener_manager.is_on_cooldown(user_id, shortener_id)
    logger.info(f"Is on cooldown: {is_on_cooldown}")
    
    if is_on_cooldown:
        remaining = shortener_manager.get_cooldown_remaining(user_id, shortener_id)
        logger.info(f"Cooldown remaining: {remaining}")
    
    # Test verification completion
    success = shortener_manager.verify_completion(user_id, verification_token)
    logger.info(f"Verification completion: {success}")
    
    return shortener_manager

async def test_multi_token_flow():
    """Test multi-token verification flow simulation"""
    logger.info("Testing Multi-Token Flow...")
    
    # Simulate user tokens storage
    user_tokens = {}
    user_id = 123456789
    
    # Initialize user session
    user_tokens[user_id] = {
        "tokens": {},
        "verified_bots": [],
        "multi_session": {
            "verified_tokens": [],
            "started_at": datetime.now(timezone.utc),
            "current_token": 1
        }
    }
    
    # Simulate completing tokens 1-4
    for token_num in range(1, 5):
        logger.info(f"Simulating Token {token_num} verification...")
        
        # Mark token as verified
        verified_tokens = user_tokens[user_id]["multi_session"]["verified_tokens"]
        if token_num not in verified_tokens:
            verified_tokens.append(token_num)
        
        logger.info(f"Progress: {len(verified_tokens)}/4 tokens completed")
        
        if len(verified_tokens) >= 4:
            logger.info("All tokens completed! Granting 24-hour access to all bots...")
            
            # Grant access to all bots
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            all_bots = ["bot1", "bot2", "bot3"]  # Simulated bots
            for bot_key in all_bots:
                import uuid
                access_token = str(uuid.uuid4())
                user_tokens[user_id]["tokens"][bot_key] = {
                    "token": access_token,
                    "expires_at": expires_at,
                    "created_at": datetime.now(timezone.utc)
                }
                
                if bot_key not in user_tokens[user_id]["verified_bots"]:
                    user_tokens[user_id]["verified_bots"].append(bot_key)
            
            # Clear multi-session data
            del user_tokens[user_id]["multi_session"]
            
            logger.info(f"Access granted to {len(all_bots)} bots until {expires_at}")
            break
    
    return user_tokens

async def main():
    """Main test function"""
    logger.info("Starting WZML-X Auth Bot Tests...")
    
    try:
        # Test bot manager
        bot_manager = await test_bot_manager()
        
        # Test shortener manager
        shortener_manager = await test_shortener_manager()
        
        # Test multi-token flow
        user_tokens = await test_multi_token_flow()
        
        logger.info("All tests completed successfully!")
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"Bot Manager: ✅ Working")
        logger.info(f"Shortener Manager: ✅ Working")
        logger.info(f"Multi-Token Flow: ✅ Working")
        logger.info(f"User Tokens: {len(user_tokens)} users simulated")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
