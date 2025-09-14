#!/usr/bin/env python3
"""
Bot Configuration Manager for WZML-X Auth Bot
Handles real bot availability checking and configuration
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from dataclasses import dataclass, asdict

@dataclass
class BotConfig:
    """Bot configuration dataclass"""
    bot_id: str
    name: str
    username: str
    token: str
    status: str  # 'active', 'inactive', 'error', 'not_configured'
    api_url: Optional[str] = None
    webhook_url: Optional[str] = None
    last_check: Optional[str] = None
    error_message: Optional[str] = None

class BotManager:
    """Manages Mirror Leech Bot configurations and availability"""
    
    def __init__(self):
        self.config_file = Path("bot_configs.json")
        self.bots: Dict[str, BotConfig] = {}
        self.load_configurations()
    
    def load_configurations(self):
        """Load bot configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for bot_key, bot_data in data.items():
                        self.bots[bot_key] = BotConfig(**bot_data)
                print(f"[CONFIG] Loaded {len(self.bots)} bot configurations")
            except Exception as e:
                print(f"[ERROR] Failed to load bot configs: {e}")
                self.create_default_configs()
        else:
            self.create_default_configs()
    
    def save_configurations(self):
        """Save bot configurations to file"""
        try:
            data = {bot_key: asdict(bot_config) for bot_key, bot_config in self.bots.items()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[CONFIG] Saved {len(self.bots)} bot configurations")
        except Exception as e:
            print(f"[ERROR] Failed to save bot configs: {e}")
    
    def create_default_configs(self):
        """Create default bot configurations"""
        print("[CONFIG] Creating default bot configurations")
        
        # Default configuration for 6 bots
        default_bots = {
            "bot1": BotConfig(
                bot_id="bot1",
                name="Mirror Leech Bot 1",
                username="",
                token="",
                status="not_configured"
            ),
            "bot2": BotConfig(
                bot_id="bot2",
                name="Mirror Leech Bot 2", 
                username="",
                token="",
                status="not_configured"
            ),
            "bot3": BotConfig(
                bot_id="bot3",
                name="Mirror Leech Bot 3",
                username="",
                token="",
                status="not_configured"
            ),
            "bot4": BotConfig(
                bot_id="bot4",
                name="Mirror Leech Bot 4",
                username="",
                token="",
                status="not_configured"
            ),
            "bot5": BotConfig(
                bot_id="bot5",
                name="Mirror Leech Bot 5",
                username="",
                token="",
                status="not_configured"
            ),
            "bot6": BotConfig(
                bot_id="bot6",
                name="Mirror Leech Bot 6",
                username="",
                token="",
                status="not_configured"
            )
        }
        
        self.bots = default_bots
        self.save_configurations()
    
    async def check_bot_availability(self, bot_key: str) -> bool:
        """Check if a bot is actually available and responsive"""
        if bot_key not in self.bots:
            return False
        
        bot = self.bots[bot_key]
        
        # If not configured, mark as unavailable
        if not bot.token or bot.status == "not_configured":
            bot.status = "not_configured"
            bot.error_message = "Bot not configured - missing token or username"
            bot.last_check = datetime.now().isoformat()
            return False
        
        try:
            # Try to get bot info using Telegram Bot API
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{bot.token}/getMe"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            bot_info = data.get("result", {})
                            bot.username = bot_info.get("username", "")
                            bot.status = "active"
                            bot.error_message = None
                            bot.last_check = datetime.now().isoformat()
                            print(f"[CHECK] {bot.name} is ACTIVE (@{bot.username})")
                            return True
                        else:
                            bot.status = "error"
                            bot.error_message = data.get("description", "API error")
                            bot.last_check = datetime.now().isoformat()
                            return False
                    else:
                        bot.status = "error"
                        bot.error_message = f"HTTP {response.status}"
                        bot.last_check = datetime.now().isoformat()
                        return False
        except asyncio.TimeoutError:
            bot.status = "error"
            bot.error_message = "Connection timeout"
            bot.last_check = datetime.now().isoformat()
            return False
        except Exception as e:
            bot.status = "error"
            bot.error_message = str(e)
            bot.last_check = datetime.now().isoformat()
            return False
    
    async def check_all_bots(self) -> Dict[str, bool]:
        """Check availability of all configured bots"""
        print("[CHECK] Checking all bot availability...")
        results = {}
        
        # Check all bots concurrently
        tasks = []
        for bot_key in self.bots.keys():
            task = self.check_bot_availability(bot_key)
            tasks.append((bot_key, task))
        
        # Wait for all checks to complete
        for bot_key, task in tasks:
            try:
                results[bot_key] = await task
            except Exception as e:
                print(f"[ERROR] Failed to check {bot_key}: {e}")
                results[bot_key] = False
        
        # Save updated configurations
        self.save_configurations()
        
        active_count = sum(1 for available in results.values() if available)
        print(f"[CHECK] Bot availability check complete: {active_count}/{len(self.bots)} bots active")
        
        return results
    
    def get_bot_status_message(self, bot_key: str) -> str:
        """Get status message for a bot"""
        if bot_key not in self.bots:
            return "❌ Bot not found"
        
        bot = self.bots[bot_key]
        
        if bot.status == "not_configured":
            return "⚙️ Bot not configured yet"
        elif bot.status == "active":
            return f"✅ Bot is active (@{bot.username})"
        elif bot.status == "error":
            return f"❌ Bot error: {bot.error_message}"
        elif bot.status == "inactive":
            return "⚪ Bot is inactive"
        else:
            return "❓ Unknown status"
    
    def get_available_bots(self) -> Dict[str, BotConfig]:
        """Get only available (active) bots"""
        return {k: v for k, v in self.bots.items() if v.status == "active"}
    
    def is_bot_available(self, bot_key: str) -> bool:
        """Check if a specific bot is available (active)"""
        if bot_key not in self.bots:
            return False
        return self.bots[bot_key].status == "active"
    
    def get_all_bots(self) -> Dict[str, BotConfig]:
        """Get all bots regardless of status"""
        return self.bots.copy()
    
    def add_bot(self, bot_key: str, name: str, token: str, username: str = "") -> bool:
        """Add or update a bot configuration"""
        try:
            self.bots[bot_key] = BotConfig(
                bot_id=bot_key,
                name=name,
                username=username,
                token=token,
                status="inactive"  # Will be checked later
            )
            self.save_configurations()
            print(f"[CONFIG] Added/Updated bot: {name}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add bot {bot_key}: {e}")
            return False
    
    def remove_bot(self, bot_key: str) -> bool:
        """Remove a bot configuration"""
        try:
            if bot_key in self.bots:
                bot_name = self.bots[bot_key].name
                del self.bots[bot_key]
                self.save_configurations()
                print(f"[CONFIG] Removed bot: {bot_name}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Failed to remove bot {bot_key}: {e}")
            return False
    
    def get_bot_config_summary(self) -> str:
        """Get a summary of all bot configurations"""
        if not self.bots:
            return "No bots configured"
        
        summary_lines = []
        for bot_key, bot in self.bots.items():
            status_icon = {
                "active": "✅",
                "inactive": "⚪", 
                "error": "❌",
                "not_configured": "⚙️"
            }.get(bot.status, "❓")
            
            summary_lines.append(f"{status_icon} **{bot.name}** - {bot.status}")
            if bot.error_message:
                summary_lines.append(f"   ↳ {bot.error_message}")
        
        return "\n".join(summary_lines)

# Global bot manager instance
bot_manager = BotManager()

# Utility functions
async def initialize_bot_manager():
    """Initialize bot manager and check all bots"""
    print("[INIT] Initializing Bot Manager...")
    await bot_manager.check_all_bots()
    return bot_manager

def get_bot_manager():
    """Get the global bot manager instance"""
    return bot_manager

# Configuration management functions
def configure_bot_interactive():
    """Interactive bot configuration (for manual setup)"""
    print("\n" + "="*50)
    print("WZML-X Auth Bot - Bot Configuration Manager")
    print("="*50)
    
    while True:
        print("\n📋 Current Bot Status:")
        print(bot_manager.get_bot_config_summary())
        
        print("\n🔧 Configuration Options:")
        print("1. Add/Update Bot")
        print("2. Remove Bot")
        print("3. Check Bot Availability")
        print("4. View Bot Details")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            # Add/Update bot
            bot_key = input("Enter bot key (bot1, bot2, etc.): ").strip()
            name = input("Enter bot name: ").strip()
            token = input("Enter bot token: ").strip()
            username = input("Enter bot username (optional): ").strip()
            
            if bot_manager.add_bot(bot_key, name, token, username):
                print(f"✅ Bot {bot_key} configured successfully!")
            else:
                print("❌ Failed to configure bot")
        
        elif choice == "2":
            # Remove bot
            bot_key = input("Enter bot key to remove: ").strip()
            if bot_manager.remove_bot(bot_key):
                print(f"✅ Bot {bot_key} removed successfully!")
            else:
                print("❌ Bot not found or failed to remove")
        
        elif choice == "3":
            # Check availability
            print("🔍 Checking bot availability...")
            # This would need async context, so skip for now
            print("Use the main bot to check availability")
        
        elif choice == "4":
            # View details
            bot_key = input("Enter bot key to view: ").strip()
            if bot_key in bot_manager.bots:
                bot = bot_manager.bots[bot_key]
                print(f"\n📋 Bot Details for {bot_key}:")
                print(f"Name: {bot.name}")
                print(f"Username: @{bot.username}")
                print(f"Status: {bot.status}")
                print(f"Last Check: {bot.last_check}")
                if bot.error_message:
                    print(f"Error: {bot.error_message}")
            else:
                print("❌ Bot not found")
        
        elif choice == "5":
            break
        
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    # Run interactive configuration
    configure_bot_interactive()
