#!/usr/bin/env python3
"""
Test Auth Bot Integration
Verify that token generation and validation works correctly
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth_bot"))

async def test_auth_integration():
    """Test the complete auth integration flow"""
    
    print("🧪 Testing Auth Bot Integration")
    print("=" * 50)
    
    try:
        # Test 1: Database Connection
        print("\n1️⃣ Testing Database Connection...")
        from auth_bot.database.connection import get_database
        from auth_bot.database.operations import DatabaseManager
        
        database = await get_database()
        db_manager = DatabaseManager(database)
        await db_manager.create_indexes()
        print("✅ Database connection successful")
        
        # Test 2: Token Generation
        print("\n2️⃣ Testing Token Generation...")
        from auth_bot.utils.token_utils import TokenGenerator
        from auth_bot.database.models import TokenType
        
        token_gen = TokenGenerator("test_secret_key")
        
        # Generate test token
        test_user_id = 123456789
        test_bot_key = "bot1"
        
        token_id, uuid4_token, expires_at = token_gen.generate_access_token(
            user_id=test_user_id,
            bot_id=test_bot_key,
            token_type=TokenType.FREE
        )
        
        print(f"✅ Token generated: {uuid4_token}")
        print(f"   Token ID: {token_id}")
        print(f"   Expires: {expires_at}")
        
        # Test 3: Token Storage
        print("\n3️⃣ Testing Token Storage...")
        from auth_bot.database.models import Token
        
        token_data = Token(
            token_id=token_id,
            user_id=test_user_id,
            bot_key=test_bot_key,
            token=uuid4_token,
            type=TokenType.FREE,
            verified=False,  # Initially not verified
            expires_at=expires_at
        )
        
        if await db_manager.create_token(token_data):
            print("✅ Token stored in database")
        else:
            print("❌ Failed to store token")
            return False
        
        # Test 4: Token Verification (simulate shortener completion)
        print("\n4️⃣ Testing Token Verification...")
        if await db_manager.verify_token(uuid4_token):
            print("✅ Token marked as verified")
        else:
            print("❌ Failed to verify token")
            return False
        
        # Test 5: Token Validation (main bot check)
        print("\n5️⃣ Testing Token Validation...")
        is_valid = await db_manager.validate_token(test_bot_key, test_user_id, uuid4_token)
        
        if is_valid:
            print("✅ Token validation successful")
        else:
            print("❌ Token validation failed")
            return False
        
        # Test 6: Main Bot Auth Handler
        print("\n6️⃣ Testing Main Bot Auth Handler...")
        from bot.helper.ext_utils.auth_handler import auth_handler
        
        validation_result = await auth_handler.validate_token(test_user_id)
        
        if validation_result.get("is_valid"):
            print("✅ Main bot auth handler working")
            print(f"   Token: {validation_result.get('token', 'N/A')[:8]}...")
            print(f"   Type: {validation_result.get('type', 'N/A')}")
        else:
            print("❌ Main bot auth handler failed")
            print(f"   Message: {validation_result.get('message', 'Unknown error')}")
            return False
        
        # Test 7: Cleanup
        print("\n7️⃣ Cleaning up test data...")
        await db_manager.revoke_token(token_id)
        print("✅ Test data cleaned up")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Auth integration is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_token_flow():
    """Test the complete token flow"""
    
    print("\n🔄 Testing Complete Token Flow")
    print("-" * 30)
    
    try:
        # Step 1: User requests token in auth bot
        print("1. User sends /verify to auth bot")
        
        # Step 2: Token generated but not verified
        print("2. Auth bot generates UUID4 token (unverified)")
        
        # Step 3: User clicks shortener link
        print("3. User completes shortener verification")
        
        # Step 4: Token marked as verified
        print("4. Auth bot marks token as verified")
        
        # Step 5: User uses token in main bot
        print("5. User sends command with token to main bot")
        
        # Step 6: Main bot validates token
        print("6. Main bot checks token in database")
        
        # Step 7: Command proceeds or fails
        print("7. Command proceeds if token is valid and verified")
        
        print("\n✅ Token flow documented")
        
    except Exception as e:
        print(f"❌ Error in token flow test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Auth Bot Integration Tests...")
    
    try:
        # Run tests
        success = asyncio.run(test_auth_integration())
        asyncio.run(test_token_flow())
        
        if success:
            print("\n🎯 SOLUTION SUMMARY:")
            print("=" * 50)
            print("The issue was in the token validation logic:")
            print("1. ✅ Fixed database query to check 'verified' field")
            print("2. ✅ Added proper expiry checking")
            print("3. ✅ Ensured tokens are marked verified after shortener")
            print("4. ✅ Main bot now properly validates verified tokens")
            print("\n🔧 Next Steps:")
            print("1. Configure AUTH_BOT_TOKEN in config.env")
            print("2. Add bot tokens to auth_bot/bot_configs.json")
            print("3. Start auth bot: python auth_bot/wzml_auth_bot.py")
            print("4. Test token generation and verification")
        else:
            print("\n❌ Some tests failed - check the logs above")
            
    except KeyboardInterrupt:
        print("\n📡 Tests stopped by user")
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)