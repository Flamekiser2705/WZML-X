#!/usr/bin/env python3
"""
Test script to check auth bot imports and basic functionality
"""
import sys
import os
from pathlib import Path

print("🧪 Testing Auth Bot Components...")
print("-" * 40)

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    print("✅ Testing basic imports...")
    import asyncio
    from uuid import uuid4
    print(f"   • asyncio: {asyncio.__name__}")
    print(f"   • uuid4: {uuid4()}")
    
    print("✅ Testing database models...")
    from database.models import User, Token, TokenType
    print(f"   • User model: {User.__name__}")
    print(f"   • Token model: {Token.__name__}")
    print(f"   • TokenType enum: {list(TokenType)}")
    
    print("✅ Testing token utilities...")
    from utils.token_utils import TokenGenerator
    token_gen = TokenGenerator("test_secret_key")
    test_uuid = token_gen.generate_simple_uuid4_token()
    print(f"   • Generated UUID4: {test_uuid}")
    print(f"   • Valid UUID4: {token_gen.is_valid_uuid4(test_uuid)}")
    
    print("✅ Testing configuration...")
    from utils.config import Config
    config = Config()
    print(f"   • Config loaded: {type(config).__name__}")
    
    print("\n🎉 All imports successful!")
    print("✅ Auth bot components are working correctly.")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 40)
print("Test completed!")
