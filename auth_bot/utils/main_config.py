#!/usr/bin/env python3
"""
Configuration management for Auth Bot
Reads from main project's config.env file
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to read main config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_env_file():
    """Load environment variables from config.env"""
    config_file = project_root / "config.env"
    
    if not config_file.exists():
        print(f"[ERROR] Config file not found: {config_file}")
        return {}
    
    env_vars = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes
                    if value.startswith('"') and '"' in value[1:]:
                        value = value[1:value.index('"', 1)]
                    elif value.startswith("'") and "'" in value[1:]:
                        value = value[1:value.index("'", 1)]
                    
                    # Remove comments (anything after # outside quotes)
                    if '#' in value and not (value.startswith('"') or value.startswith("'")):
                        value = value.split('#')[0].strip()
                    
                    env_vars[key] = value
                    # Also set as environment variable
                    os.environ[key] = value
    except Exception as e:
        print(f"[ERROR] Error reading config file: {e}")
    
    return env_vars

# Load config on import
env_vars = load_env_file()

class Config:
    """Configuration class for Auth Bot"""
    
    def __init__(self):
        # Load from main config.env
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment"""
        
        # Telegram API Credentials (from main bot config)
        telegram_api = os.getenv('TELEGRAM_API', '0')
        self.TELEGRAM_API = int(telegram_api) if telegram_api.isdigit() else 0
        self.TELEGRAM_HASH = os.getenv('TELEGRAM_HASH', '')
        
        # Bot Configuration - Use AUTH_BOT_TOKEN from main config
        self.AUTH_BOT_TOKEN = os.getenv('AUTH_BOT_TOKEN', '')
        bot_username = os.getenv('AUTH_BOT_USERNAME', 'auth_bot')
        # Clean up the bot username (remove quotes and extra text)
        self.BOT_USERNAME = bot_username.split('"')[0].strip() if '"' in bot_username else bot_username.strip()
        
        # Database - Use AUTH_BOT_DATABASE_URL from main config
        self.MONGODB_URI = os.getenv('AUTH_BOT_DATABASE_URL', 
                                   os.getenv('DATABASE_URL', 
                                           'mongodb://localhost:27017/auth_bot'))
        
        # Security
        self.JWT_SECRET = os.getenv('AUTH_BOT_TOKEN_SECRET', 
                                  os.getenv('JWT_SECRET', 'default-secret-key'))
        self.AUTH_API_SECRET_KEY = os.getenv('AUTH_BOT_TOKEN_SECRET', 
                                           'default-api-secret')
        
        # Admin Configuration
        self.ADMIN_IDS = self._parse_ids(os.getenv('OWNER_ID', ''))
        self.SUDO_USERS = self._parse_ids(os.getenv('SUDO_USERS', ''))
        
        # Main Bot Configuration
        self.MAIN_BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        self.MAIN_BOT_ID = self._extract_bot_id(self.MAIN_BOT_TOKEN)
        
        # API Configuration
        self.API_HOST = "0.0.0.0"
        self.API_PORT = 8001
        self.AUTH_API_URL = f"http://localhost:{self.API_PORT}"
        
        # Payment Gateways (if configured)
        self.RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
        self.RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
        self.PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
        self.PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', '')
        
        # Pricing (in cents/paise)
        self.PLAN_7D_PRICE = 500    # ₹5.00
        self.PLAN_30D_PRICE = 2000  # ₹20.00
        self.PLAN_90D_PRICE = 5000  # ₹50.00
        
        # Token Configuration
        self.FREE_TOKEN_HOURS = 6
        self.MAX_FREE_TOKENS_PER_USER = 1
        self.MAX_PREMIUM_TOKENS_PER_USER = 4
        
        # Registration
        main_bot_username = self._extract_username_from_token(self.MAIN_BOT_TOKEN)
        self.REGISTERED_BOTS = f"{self.MAIN_BOT_ID}:WZML-X Bot:@{main_bot_username}"
        
        # Token Timeout
        token_timeout = os.getenv('TOKEN_TIMEOUT', '21600')
        self.TOKEN_TIMEOUT = int(token_timeout) if token_timeout and token_timeout.isdigit() else 21600
        
        # Feature Flags
        self.AUTH_BOT_ENABLED = os.getenv('AUTH_BOT_ENABLED', 'True').lower() == 'true'
    
    def _parse_ids(self, ids_string: str) -> List[int]:
        """Parse comma-separated IDs"""
        if not ids_string:
            return []
        return [int(id.strip()) for id in ids_string.split(',') if id.strip().isdigit()]
    
    def _extract_bot_id(self, bot_token: str) -> str:
        """Extract bot ID from token"""
        if not bot_token or ':' not in bot_token:
            return "123456789"  # Default fallback
        return bot_token.split(':')[0]
    
    def _extract_username_from_token(self, bot_token: str) -> str:
        """Extract username from bot token (placeholder)"""
        # This would need actual API call to get username
        # For now, use a default
        return os.getenv('AUTH_BOT_USERNAME', 'wzml_auth_bot').replace('@', '')
    
    @property
    def admin_ids(self) -> List[int]:
        """Get all admin IDs"""
        return list(set(self.ADMIN_IDS + self.SUDO_USERS))
    
    @property
    def registered_bots_list(self) -> List[Dict[str, Any]]:
        """Parse registered bots string into list"""
        bots = []
        for bot_entry in self.REGISTERED_BOTS.split(','):
            bot_entry = bot_entry.strip()
            if ':' in bot_entry:
                parts = bot_entry.split(':')
                if len(parts) >= 3:
                    bots.append({
                        'id': parts[0].strip(),
                        'name': parts[1].strip(),
                        'username': parts[2].strip().replace('@', '')
                    })
        return bots
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_ids
    
    def is_bot_registered(self, bot_id: str) -> bool:
        """Check if bot is registered"""
        return any(bot['id'] == str(bot_id) for bot in self.registered_bots_list)

# Create global config instance
config = Config()

# Validation
def validate_config():
    """Validate configuration"""
    errors = []
    
    if not config.AUTH_BOT_TOKEN or config.AUTH_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("AUTH_BOT_TOKEN is not set")
    
    if not config.MONGODB_URI:
        errors.append("Database URL is not configured")
    
    if not config.JWT_SECRET or config.JWT_SECRET == "your-secret-key-here":
        errors.append("JWT_SECRET is not set")
    
    return errors

# Print config status
def print_config_status():
    """Print configuration status"""
    print("[CONFIG] Auth Bot Configuration:")
    print(f"[CONFIG] Auth Bot Token: {'Set' if config.AUTH_BOT_TOKEN and config.AUTH_BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'Not Set'}")
    print(f"[CONFIG] Bot Username: {config.BOT_USERNAME}")
    print(f"[CONFIG] Database: {'Connected' if config.MONGODB_URI else 'Not Set'}")
    print(f"[CONFIG] JWT Secret: {'Set' if config.JWT_SECRET else 'Not Set'}")
    print(f"[CONFIG] Admin IDs: {len(config.admin_ids)} configured")
    print(f"[CONFIG] Auth Bot Enabled: {config.AUTH_BOT_ENABLED}")
    print(f"[CONFIG] Main Bot ID: {config.MAIN_BOT_ID}")
    print(f"[CONFIG] Telegram API: {'Set' if config.TELEGRAM_API else 'Not Set'}")
    print(f"[CONFIG] Telegram Hash: {'Set' if config.TELEGRAM_HASH else 'Not Set'}")

if __name__ == "__main__":
    print_config_status()
    errors = validate_config()
    if errors:
        print("\n[ERROR] Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n[SUCCESS] Configuration is valid!")
