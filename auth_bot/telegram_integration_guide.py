#!/usr/bin/env python3
"""
Telegram Bot Integration Architecture
Explains how the auth bot works with main Telegram bots
"""

"""
🤖 TELEGRAM BOT INTEGRATION ARCHITECTURE

The auth bot system is designed for Telegram bots, not HTTP APIs. Here's how it works:

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AUTH BOT      │    │  MAIN BOT 1     │    │  MAIN BOT 2     │
│  @auth_bot      │    │ @mirror_bot     │    │ @leech_bot      │
│                 │    │                 │    │                 │
│ • User registration │    │ • Mirror/Leech  │    │ • Clone tasks   │
│ • Token generation  │    │ • Validates tokens │    │ • Validates tokens │
│ • Payment handling  │    │ • Calls Auth API   │    │ • Calls Auth API   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         └────────────┬───────────┴────────────────────────┘
                      │
              ┌─────────────────┐
              │   AUTH API      │
              │ localhost:8001  │
              │                 │
              │ • Token validation │
              │ • User info API    │
              │ • Webhook handlers │
              └─────────────────┘

🔄 USER WORKFLOW:

1. User starts auth bot: /start @auth_bot
2. User requests token: /verify
3. User chooses plan: Free 6h / Premium 7/30/90d
4. Auth bot generates UUID4 token: 550e8400-e29b-41d4-a716-446655440000
5. User copies token to main bot: /mirror https://example.com 550e8400-e29b-41d4-a716-446655440000
6. Main bot validates token via API call to auth bot
7. Main bot proceeds with mirror/leech operation

🔧 CONFIGURATION EXPLANATION:

REGISTERED_BOTS=mirror_bot_1:WZML-X Mirror Bot:@wzmlx_mirror_bot,leech_bot_1:WZML-X Leech Bot:@wzmlx_leech_bot

This means:
- Bot ID: "mirror_bot_1" (internal identifier)
- Bot Name: "WZML-X Mirror Bot" (display name)
- Bot Username: "@wzmlx_mirror_bot" (Telegram username)

🌐 API ENDPOINTS:

The AUTH_API_URL (http://localhost:8001) is for:
- Token validation between bots
- Not for user access
- Internal bot-to-bot communication

📱 TELEGRAM BOT SETUP:

1. Create separate Telegram bots with @BotFather:
   - @your_auth_bot (for authentication)
   - @your_mirror_bot (for mirror/leech)
   - @your_clone_bot (for clone operations)

2. Configure each bot token in their respective config files

3. Main bots call auth bot API to validate tokens

4. Users interact only with Telegram interface

🔐 TOKEN VALIDATION FLOW:

┌─────────────────┐
│ User sends:     │
│ /mirror url     │ 
│ token           │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ Main Bot        │
│ Extracts token  │
│ from message    │
└─────────┬───────┘
          │
          ▼ HTTP POST
┌─────────────────┐
│ Auth Bot API    │
│ /validate-token │
│ Returns:        │
│ {"valid": true, │
│  "user_id": ...,│
│  "expires": ...}│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ Main Bot        │
│ Proceeds with   │
│ operation if    │
│ token is valid  │
└─────────────────┘

💻 MAIN BOT INTEGRATION CODE:

# In your main mirror bot (not HTTP server - Telegram bot)
from pyrogram import Client, filters
import aiohttp

async def validate_token_with_auth_bot(token: str, bot_id: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8001/validate-token",
            json={"token": token, "bot_id": bot_id},
            headers={"Authorization": f"Bearer {AUTH_API_SECRET}"}
        ) as response:
            result = await response.json()
            return result.get("valid", False)

@Client.on_message(filters.command("mirror"))
async def mirror_handler(client, message):
    # Extract token from message
    if len(message.command) > 2:  # /mirror url token
        url = message.command[1]
        token = message.command[2]
        
        # Validate with auth bot
        is_valid = await validate_token_with_auth_bot(token, "mirror_bot_1")
        
        if is_valid:
            # Proceed with mirror operation
            await message.reply("✅ Token valid, starting mirror...")
        else:
            await message.reply("❌ Invalid token. Get one from @your_auth_bot")

🚀 DEPLOYMENT:

1. Deploy auth bot: python auth_bot/main.py
2. Deploy auth API: python auth_bot/api_server.py  
3. Deploy main bots with integration code
4. Configure REGISTERED_BOTS in auth bot config

✅ CORRECTED CONFIGURATION:

# These are Telegram bots, not HTTP endpoints
REGISTERED_BOTS=mirror_bot_1:WZML-X Mirror Bot:@wzmlx_mirror_bot,leech_bot_1:WZML-X Leech Bot:@wzmlx_leech_bot

# This is the API server for bot-to-bot communication
AUTH_API_URL=http://localhost:8001
AUTH_API_SECRET_KEY=your_secret_api_key_for_bot_communication

No HTTP endpoints needed for main bots - they're Telegram bots!
"""
