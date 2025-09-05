#!/usr/bin/env python3
"""
UUID4 Token Examples and Testing
This file demonstrates how the UUID4 token system works
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.token_utils import TokenGenerator, TokenValidator
from database.models import TokenType
from datetime import datetime


async def demo_uuid4_tokens():
    """Demonstrate UUID4 token generation and validation"""
    
    print("🎯 WZML-X Auth Bot - UUID4 Token System Demo")
    print("=" * 50)
    
    # Initialize token generator
    secret_key = "demo_secret_key_for_testing_12345"
    token_gen = TokenGenerator(secret_key)
    
    print("\n📋 1. Generating UUID4 Tokens")
    print("-" * 30)
    
    # Generate free token (6 hours)
    print("🆓 Free Token (6 hours):")
    token_id, uuid4_token, expires_at = token_gen.generate_access_token(
        user_id=123456789,
        bot_id="mirror_bot_1",
        token_type=TokenType.FREE
    )
    
    print(f"   Token ID: {token_id}")
    print(f"   UUID4 Token: {uuid4_token}")
    print(f"   Expires At: {expires_at}")
    print(f"   Valid UUID4: {token_gen.is_valid_uuid4(uuid4_token)}")
    
    # Generate premium token (30 days)
    print("\n💎 Premium Token (30 days):")
    token_id_premium, uuid4_token_premium, expires_at_premium = token_gen.generate_access_token(
        user_id=987654321,
        bot_id="leech_bot_1",
        token_type=TokenType.PREMIUM,
        custom_days=30
    )
    
    print(f"   Token ID: {token_id_premium}")
    print(f"   UUID4 Token: {uuid4_token_premium}")
    print(f"   Expires At: {expires_at_premium}")
    print(f"   Valid UUID4: {token_gen.is_valid_uuid4(uuid4_token_premium)}")
    
    print("\n🔍 2. Token Validation")
    print("-" * 30)
    
    # Validate tokens
    token_validator = TokenValidator(token_gen)
    
    # Test free token
    print("Testing Free Token:")
    format_valid = token_validator.validate_token_structure(uuid4_token)
    print(f"   Format Valid: {format_valid}")
    
    token_info = token_validator.extract_token_info(uuid4_token)
    print(f"   Token Info: {token_info}")
    
    # Test premium token
    print("\nTesting Premium Token:")
    format_valid_premium = token_validator.validate_token_structure(uuid4_token_premium)
    print(f"   Format Valid: {format_valid_premium}")
    
    token_info_premium = token_validator.extract_token_info(uuid4_token_premium)
    print(f"   Token Info: {token_info_premium}")
    
    print("\n🎲 3. Additional UUID4 Examples")
    print("-" * 30)
    
    # Generate simple UUID4 tokens
    simple_uuid4 = token_gen.generate_simple_uuid4_token()
    print(f"Simple UUID4: {simple_uuid4}")
    print(f"Valid UUID4: {token_gen.is_valid_uuid4(simple_uuid4)}")
    
    # Generate payment ID
    payment_id = token_gen.generate_payment_id()
    print(f"Payment ID: {payment_id}")
    
    # Generate simple token with UUID4 base
    simple_token = token_gen.generate_simple_token(user_id=555555, bot_id="test_bot")
    print(f"Simple Token (base64): {simple_token}")
    
    # Decode simple token
    decoded = token_gen.decode_simple_token(simple_token)
    print(f"Decoded Simple Token: {decoded}")
    
    print("\n✅ 4. Token Security Features")
    print("-" * 30)
    print("🔐 UUID4 Advantages:")
    print("   • Cryptographically secure random generation")
    print("   • 128-bit entropy (2^128 possible values)")
    print("   • No sequential patterns or predictability")
    print("   • Standard format with built-in validation")
    print("   • Clean, readable format without special characters")
    print("   • Database-friendly (indexed efficiently)")
    print("   • URL-safe (no encoding needed)")
    
    print("\n📊 5. Token Storage Example")
    print("-" * 30)
    print("Database Document Structure:")
    
    token_doc = {
        "token_id": token_id,
        "user_id": 123456789,
        "bot_id": "mirror_bot_1",
        "token": uuid4_token,  # This is the UUID4 token users will use
        "type": "FREE",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
        "is_active": True,
        "usage_count": 0
    }
    
    print(f"   {token_doc}")
    
    print("\n🎯 6. User Workflow")
    print("-" * 30)
    print("1. User sends /verify to auth bot")
    print("2. User chooses Free Token (6h)")
    print("3. Bot generates UUID4 token:")
    print(f"   Token: {uuid4_token}")
    print("4. User copies token to main bot")
    print("5. Main bot validates token via API")
    print("6. Token automatically expires via TTL index")
    
    print("\n" + "=" * 50)
    print("✅ UUID4 Token System Demo Complete!")


def test_uuid4_validation():
    """Test UUID4 validation functions"""
    
    print("\n🧪 UUID4 Validation Tests")
    print("-" * 30)
    
    token_gen = TokenGenerator("test_secret")
    
    # Valid UUID4 examples
    valid_uuids = [
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
    ]
    
    # Invalid examples
    invalid_tokens = [
        "not-a-uuid",
        "550e8400-e29b-41d4-a716",  # Too short
        "550e8400-e29b-51d4-a716-446655440000",  # Wrong version (5 instead of 4)
        "",
        "123456789",
        "Base64EncodedString=="
    ]
    
    print("✅ Valid UUID4 tokens:")
    for uuid_token in valid_uuids:
        is_valid = token_gen.is_valid_uuid4(uuid_token)
        print(f"   {uuid_token}: {is_valid}")
    
    print("\n❌ Invalid tokens:")
    for token in invalid_tokens:
        is_valid = token_gen.is_valid_uuid4(token)
        print(f"   {token}: {is_valid}")
    
    print("\n🎲 Generated UUID4 tokens:")
    for i in range(3):
        new_uuid = token_gen.generate_simple_uuid4_token()
        is_valid = token_gen.is_valid_uuid4(new_uuid)
        print(f"   {new_uuid}: {is_valid}")


if __name__ == "__main__":
    print("🚀 Starting UUID4 Token Demo...")
    asyncio.run(demo_uuid4_tokens())
    test_uuid4_validation()
    print("\n🎉 Demo completed successfully!")
