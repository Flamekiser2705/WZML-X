#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    # Connect to the same database as the auth bot
    client = AsyncIOMotorClient('mongodb+srv://akash:hNvDNSWOXCSkzkTG@mirrorleechtesting.kenxovd.mongodb.net/auth_bot?retryWrites=true&w=majority&appName=MirrorLeechTesting')
    db = client.auth_bot
    
    print("=== CHECKING AUTH BOT DATABASE ===")
    
    # Check tokens collection
    tokens_collection = db.tokens
    tokens_count = await tokens_collection.count_documents({})
    print(f"Total tokens in database: {tokens_count}")
    
    if tokens_count > 0:
        print("\n=== TOKENS ===")
        async for token in tokens_collection.find():
            user_id = token.get('user_id')
            bot_key = token.get('bot_key')
            verified = token.get('verified')
            token_type = token.get('type')
            expires_at = token.get('expires_at')
            print(f"User: {user_id}, Bot: {bot_key}, Verified: {verified}, Type: {token_type}, Expires: {expires_at}")
    
    # Check users collection
    users_collection = db.users
    users_count = await users_collection.count_documents({})
    print(f"\nTotal users in database: {users_count}")
    
    if users_count > 0:
        print("\n=== USERS ===")
        async for user in users_collection.find():
            user_id = user.get('user_id')
            username = user.get('username')
            has_multi = 'multi_session' in user
            print(f"User: {user_id}, Username: {username}, Has Multi Session: {has_multi}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())