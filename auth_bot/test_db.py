#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def test_database():
    print("Testing database connection and write capability...")
    
    # Connect to the same database as the auth bot
    client = AsyncIOMotorClient('mongodb+srv://akash:hNvDNSWOXCSkzkTG@mirrorleechtesting.kenxovd.mongodb.net/auth_bot?retryWrites=true&w=majority&appName=MirrorLeechTesting')
    db = client.auth_bot
    
    # Test writing to tokens collection
    tokens_collection = db.tokens
    
    test_token = {
        "user_id": 12345,
        "bot_key": "bot1",
        "token": "test_token_123",
        "verified": True,
        "type": "test",
        "created_at": datetime.now().isoformat(),
        "expires_at": datetime.now().isoformat()
    }
    
    try:
        result = await tokens_collection.insert_one(test_token)
        print(f"✅ Successfully inserted test token with ID: {result.inserted_id}")
        
        # Try to read it back
        found_token = await tokens_collection.find_one({"user_id": 12345})
        if found_token:
            print(f"✅ Successfully read back token: {found_token}")
        else:
            print("❌ Could not read back the token")
        
        # Clean up test data
        await tokens_collection.delete_one({"user_id": 12345})
        print("✅ Test token cleaned up")
        
    except Exception as e:
        print(f"❌ Database write error: {e}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_database())