#!/usr/bin/env python3
import os
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config.env")

# Basic Configuration
BOT_TOKEN = os.getenv("AUTH_BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("AUTH_BOT_TOKEN is required in config.env")

BOT_USERNAME = os.getenv("BOT_USERNAME", "")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/auth_bot")

# Payment Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")

# Pricing Configuration (in paise for Razorpay)
PLAN_7D_PRICE = int(os.getenv("PLAN_7D_PRICE", "500"))  # ₹5
PLAN_30D_PRICE = int(os.getenv("PLAN_30D_PRICE", "2000"))  # ₹20
PLAN_90D_PRICE = int(os.getenv("PLAN_90D_PRICE", "5000"))  # ₹50

# Token Configuration
FREE_TOKEN_HOURS = int(os.getenv("FREE_TOKEN_HOURS", "6"))
MAX_FREE_TOKENS_PER_USER = int(os.getenv("MAX_FREE_TOKENS_PER_USER", "1"))
MAX_PREMIUM_TOKENS_PER_USER = int(os.getenv("MAX_PREMIUM_TOKENS_PER_USER", "4"))

# Redis Configuration (optional)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Admin Configuration
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = []
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip()]
    except ValueError:
        logging.warning("Invalid ADMIN_IDS format in config.env")

# Registered Bots Configuration
REGISTERED_BOTS_STR = os.getenv("REGISTERED_BOTS", "")
REGISTERED_BOTS: Dict[str, Dict[str, str]] = {}
if REGISTERED_BOTS_STR:
    try:
        for bot_info in REGISTERED_BOTS_STR.split(","):
            parts = bot_info.strip().split(":")
            if len(parts) >= 3:
                bot_id, bot_name, api_endpoint = parts[0], parts[1], ":".join(parts[2:])
                REGISTERED_BOTS[bot_id] = {
                    "name": bot_name,
                    "api_endpoint": api_endpoint
                }
    except Exception as e:
        logging.warning(f"Invalid REGISTERED_BOTS format in config.env: {e}")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auth_bot.log"),
        logging.StreamHandler()
    ]
)

# Plan Configuration
PLANS_CONFIG = {
    "7d": {
        "name": "7 Days Premium",
        "duration_days": 7,
        "price": PLAN_7D_PRICE,
        "features": [
            "7 days premium access",
            "Generate tokens for all bots",
            "Priority support",
            "No daily limits"
        ]
    },
    "30d": {
        "name": "30 Days Premium",
        "duration_days": 30,
        "price": PLAN_30D_PRICE,
        "features": [
            "30 days premium access",
            "Generate tokens for all bots",
            "Priority support",
            "No daily limits",
            "Advanced features"
        ]
    },
    "90d": {
        "name": "90 Days Premium",
        "duration_days": 90,
        "price": PLAN_90D_PRICE,
        "features": [
            "90 days premium access",
            "Generate tokens for all bots",
            "VIP support",
            "No daily limits",
            "All premium features",
            "Best value plan"
        ]
    }
}

# Messages Configuration
MESSAGES = {
    "WELCOME": """
🔐 **Welcome to WZML-X Auth Bot!**

This bot manages authentication tokens for WZML-X mirror bots.

**Features:**
• Free tokens (6 hours validity)
• Premium plans (7/30/90 days)
• Multi-bot support
• Secure token generation

Use /verify to get started!
""",
    
    "HELP": """
🆘 **Help & Commands**

**Available Commands:**
/start - Start the bot
/verify - Generate authentication tokens
/status - Check your subscription status
/help - Show this help message

**Token Types:**
🆓 **Free**: 6 hours validity, 1 token at a time
💎 **Premium**: 7/30/90 days validity, multiple tokens

**Need Support?**
Contact our support team for assistance.
""",
    
    "VERIFY_OPTIONS": """
🔑 **Choose Token Generation Option:**

Select how you want to generate your authentication tokens:
""",
    
    "BOT_SELECTION": """
🤖 **Select Target Bot:**

Choose which bot you want to generate token for:
""",
    
    "PREMIUM_PLANS": """
💎 **Premium Plans Available:**

Upgrade to premium for extended access and multiple bot tokens:
""",
    
    "PAYMENT_PENDING": """
💳 **Payment Required**

Your payment is being processed. You will receive your premium tokens once payment is confirmed.

**Payment ID:** `{payment_id}`
**Plan:** {plan_name}
**Amount:** ₹{amount}

Please complete the payment to activate your premium subscription.
""",
    
    "TOKEN_GENERATED": """
✅ **Token Generated Successfully!**

**Token:** `{token}`
**Bot:** {bot_name}
**Type:** {token_type}
**Expires:** {expires_at}

⚠️ **Important:** Keep this token secure and don't share it with others.
""",
    
    "TOKEN_LIMIT_REACHED": """
⚠️ **Token Limit Reached**

You have reached the maximum number of active tokens for your subscription tier.

**Free Users:** 1 active token
**Premium Users:** 4 active tokens

Please wait for existing tokens to expire or upgrade to premium.
""",
    
    "PREMIUM_REQUIRED": """
💎 **Premium Required**

This feature requires a premium subscription.

**Benefits of Premium:**
• Extended token validity (7/30/90 days)
• Multiple bot tokens
• Priority support
• No daily limits

Use /verify to upgrade to premium!
""",
    
    "INVALID_TOKEN": """
❌ **Invalid Token**

The provided token is either:
• Expired
• Invalid
• Already used
• Not found

Please generate a new token using /verify command.
""",
    
    "PAYMENT_SUCCESS": """
🎉 **Payment Successful!**

Your premium subscription has been activated!

**Plan:** {plan_name}
**Valid Until:** {expiry_date}
**Features Unlocked:**
{features}

You can now generate premium tokens using /verify command.
""",
    
    "SUBSCRIPTION_STATUS": """
📊 **Your Subscription Status**

**User ID:** {user_id}
**Subscription:** {subscription_type}
**Premium Expiry:** {premium_expiry}

**Token Statistics:**
• Total Generated: {total_tokens}
• Currently Active: {active_tokens}
• Premium Tokens: {premium_tokens}
• Free Tokens: {free_tokens}

**Available Actions:**
Use /verify to generate new tokens
""",
    
    "ERROR": "❌ An error occurred. Please try again later.",
    "UNAUTHORIZED": "🚫 You are not authorized to use this command.",
    "MAINTENANCE": "🔧 Bot is under maintenance. Please try again later."
}
