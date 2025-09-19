#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_tokens():
    client = AsyncIOMotorClient('mongodb+srv://akash:hNvDNSWOXCSkzkTG@mirrorleechtesting.kenxovd.mongodb.net/auth_bot?retryWrites=true&w=majority&appName=MirrorLeechTesting')
    db = client.auth_bot
    tokens = db.tokens
    
    print('=== TOKENS COLLECTION ===')
    async for token in tokens.find():
        print(f'User ID: {token.get("user_id")}, Bot Key: {token.get("bot_key")}, Verified: {token.get("verified")}, Type: {token.get("type")}')
    
    print('\n=== USER COLLECTION ===')
    users = db.users
    async for user in users.find():
        print(f'User ID: {user.get("user_id")}, Username: {user.get("username")}, Multi Session: {bool(user.get("multi_session"))}')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_tokens())