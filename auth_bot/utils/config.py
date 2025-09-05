#!/usr/bin/env python3
"""
Configuration management for Auth Bot
Handles environment variables and bot registration
"""

import os
from typing import List, Dict, Any
from pydantic import BaseSettings


class Config(BaseSettings):
    """Configuration class for Auth Bot"""
    
    # Bot Configuration
    AUTH_BOT_TOKEN: str = ""
    BOT_USERNAME: str = ""
    
    # Database
    MONGODB_URI: str = "mongodb://localhost:27017/auth_bot"
    
    # Payment Gateways
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    JWT_SECRET: str = ""
    
    # Auth API for main bots
    AUTH_API_URL: str = "http://localhost:8001"
    AUTH_API_SECRET_KEY: str = ""
    
    # Pricing (in cents/paise)
    PLAN_7D_PRICE: int = 500
    PLAN_30D_PRICE: int = 2000
    PLAN_90D_PRICE: int = 5000
    
    # Token Configuration
    FREE_TOKEN_HOURS: int = 6
    MAX_FREE_TOKENS_PER_USER: int = 1
    MAX_PREMIUM_TOKENS_PER_USER: int = 4
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Admin User IDs
    ADMIN_IDS: str = ""
    
    # Registered Telegram Bots (bot_id:bot_name:bot_username)
    REGISTERED_BOTS: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def parse_registered_bots(registered_bots_str: str) -> List[Dict[str, Any]]:
    """
    Parse REGISTERED_BOTS string into list of bot dictionaries
    
    Format: "bot_id:bot_name:bot_username,bot_id2:bot_name2:bot_username2"
    Example: "mirror_bot_1:WZML-X Mirror Bot:@wzmlx_mirror_bot,leech_bot_1:WZML-X Leech Bot:@wzmlx_leech_bot"
    
    Returns:
    [
        {
            "bot_id": "mirror_bot_1",
            "name": "WZML-X Mirror Bot", 
            "username": "@wzmlx_mirror_bot"
        },
        {
            "bot_id": "leech_bot_1",
            "name": "WZML-X Leech Bot",
            "username": "@wzmlx_leech_bot"
        }
    ]
    """
    bots = []
    
    if not registered_bots_str:
        return bots
    
    for bot_config in registered_bots_str.split(","):
        bot_config = bot_config.strip()
        if not bot_config:
            continue
            
        parts = bot_config.split(":")
        if len(parts) == 3:
            bot_id, bot_name, bot_username = parts
            bots.append({
                "bot_id": bot_id.strip(),
                "name": bot_name.strip(),
                "username": bot_username.strip()
            })
    
    return bots


def parse_admin_ids(admin_ids_str: str) -> List[int]:
    """Parse ADMIN_IDS string into list of integers"""
    admin_ids = []
    
    if not admin_ids_str:
        return admin_ids
    
    for admin_id in admin_ids_str.split(","):
        admin_id = admin_id.strip()
        if admin_id.isdigit():
            admin_ids.append(int(admin_id))
    
    return admin_ids


# Create global config instance
config = Config()

# Parse configurations
REGISTERED_BOTS = parse_registered_bots(config.REGISTERED_BOTS)
ADMIN_IDS = parse_admin_ids(config.ADMIN_IDS)


def get_bot_by_id(bot_id: str) -> Dict[str, Any]:
    """Get bot configuration by bot_id"""
    for bot in REGISTERED_BOTS:
        if bot["bot_id"] == bot_id:
            return bot
    return {}


def get_bot_names() -> List[str]:
    """Get list of all registered bot names"""
    return [bot["name"] for bot in REGISTERED_BOTS]


def get_bot_ids() -> List[str]:
    """Get list of all registered bot IDs"""
    return [bot["bot_id"] for bot in REGISTERED_BOTS]


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


def validate_config() -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    if not config.AUTH_BOT_TOKEN:
        errors.append("AUTH_BOT_TOKEN is required")
    
    if not config.MONGODB_URI:
        errors.append("MONGODB_URI is required")
    
    if not config.JWT_SECRET:
        errors.append("JWT_SECRET is required")
    
    if not config.AUTH_API_SECRET_KEY:
        errors.append("AUTH_API_SECRET_KEY is required")
    
    if not REGISTERED_BOTS:
        errors.append("At least one bot must be registered in REGISTERED_BOTS")
    
    if not ADMIN_IDS:
        errors.append("At least one admin must be specified in ADMIN_IDS")
    
    return errors


# Example usage and validation
if __name__ == "__main__":
    print("🔧 Auth Bot Configuration")
    print("-" * 30)
    
    # Validate config
    errors = validate_config()
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Configuration is valid")
    
    print(f"\n📱 Registered Telegram Bots ({len(REGISTERED_BOTS)}):")
    for bot in REGISTERED_BOTS:
        print(f"   • {bot['bot_id']}: {bot['name']} ({bot['username']})")
    
    print(f"\n👑 Admin Users ({len(ADMIN_IDS)}):")
    for admin_id in ADMIN_IDS:
        print(f"   • {admin_id}")
    
    print(f"\n🌐 API Configuration:")
    print(f"   • Auth API URL: {config.AUTH_API_URL}")
    print(f"   • API Host: {config.API_HOST}:{config.API_PORT}")
    print(f"   • Database: {config.MONGODB_URI}")
