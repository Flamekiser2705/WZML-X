#!/usr/bin/env python3
"""
Quick Setup and Run Script for Auth Bot
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import pyrogram
        import motor
        import fastapi
        print("✅ All required packages found")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def setup_env():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# Auth Bot Configuration
AUTH_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DATABASE_URL=mongodb://localhost:27017
DATABASE_NAME=auth_bot_test
JWT_SECRET_KEY=your-secret-key-here
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_secret
WEBHOOK_URL=https://yoursite.com/webhook
API_HOST=0.0.0.0
API_PORT=8000
REGISTERED_BOTS=123456789:TestBot:@testbot
"""
        env_file.write_text(env_content)
        print("✅ .env file created")
        print("📝 Please edit .env file and add your bot token from @BotFather")
        return False
    else:
        # Check if token is set
        with open(env_file, 'r') as f:
            content = f.read()
            if "YOUR_BOT_TOKEN_HERE" in content:
                print("⚠️  Please set AUTH_BOT_TOKEN in .env file")
                return False
        print("✅ .env file exists and configured")
        return True

def main():
    """Main setup function"""
    print("🤖 WZML-X Auth Bot Setup")
    print("=" * 40)
    
    # Change to auth_bot directory
    auth_bot_dir = Path(__file__).parent
    os.chdir(auth_bot_dir)
    print(f"📁 Working directory: {auth_bot_dir}")
    
    # Check requirements
    if not check_requirements():
        return
    
    # Setup environment
    if not setup_env():
        print("\n📋 Next steps:")
        print("1. Get bot token from @BotFather")
        print("2. Edit .env file and add your token")
        print("3. Run this script again")
        return
    
    # Run the bot
    print("\n🚀 Starting Auth Bot...")
    print("💡 Use Ctrl+C to stop the bot")
    print("-" * 40)
    
    try:
        # Import and run simple bot
        import subprocess
        result = subprocess.run([sys.executable, "simple_bot.py"], cwd=auth_bot_dir)
        
    except KeyboardInterrupt:
        print("\n📡 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error running bot: {e}")

if __name__ == "__main__":
    main()
