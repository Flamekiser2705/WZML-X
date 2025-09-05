#!/usr/bin/env python3
"""
Setup and Installation Script for WZML-X Auth Bot
Run this script to setup the auth bot environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def setup_auth_bot():
    """Setup the auth bot environment"""
    print("🚀 Setting up WZML-X Auth Bot...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Create necessary directories
    directories = [
        "sessions",
        "logs",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Install requirements
    if Path("auth_requirements.txt").exists():
        run_command(
            f"{sys.executable} -m pip install -r auth_requirements.txt",
            "Installing Python packages"
        )
    else:
        # Install packages individually if requirements file not found
        packages = [
            "pyrogram==2.0.106",
            "motor==3.3.2",
            "pymongo==4.6.0",
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "cryptography==41.0.8",
            "pyjwt==2.8.0",
            "razorpay==1.4.1",
            "paypalrestsdk==1.13.3",
            "python-dotenv==1.0.0",
            "aiohttp==3.9.1",
            "requests==2.31.0"
        ]
        
        for package in packages:
            run_command(
                f"{sys.executable} -m pip install {package}",
                f"Installing {package}"
            )
    
    # Create example .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# WZML-X Auth Bot Configuration
# Copy this file and rename to .env, then fill in your values

# Bot Configuration
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Database Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=wzml_auth_bot

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_SECRET_KEY=your_secret_api_key

# Payment Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret

# Admin Configuration
ADMIN_IDS=123456789,987654321
LOG_CHANNEL_ID=-1001234567890

# Security
ENCRYPTION_KEY=your_32_character_encryption_key
JWT_SECRET=your_jwt_secret_key

# Bot Settings
FREE_TOKEN_HOURS=6
PREMIUM_TOKEN_DAYS_7=7
PREMIUM_TOKEN_DAYS_30=30
PREMIUM_TOKEN_DAYS_90=90

# Pricing (in smallest currency unit)
PRICE_7_DAYS_INR=500
PRICE_30_DAYS_INR=2000
PRICE_90_DAYS_INR=5000
PRICE_7_DAYS_USD=100
PRICE_30_DAYS_USD=300
PRICE_90_DAYS_USD=700

# Optional
DEBUG=false
TIMEZONE=UTC
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("📝 Created example .env file")
        print("⚠️  Please edit .env file with your actual configuration values")
    
    print("\n🎉 Auth Bot setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your configuration")
    print("2. Set up MongoDB database")
    print("3. Get your Telegram API credentials")
    print("4. Create your bot with @BotFather")
    print("5. Configure payment gateways (optional)")
    print("6. Run the bot: python main.py")
    print("7. Run the API server: python api_server.py")

if __name__ == "__main__":
    setup_auth_bot()
