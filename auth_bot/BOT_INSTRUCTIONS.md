# WZML-X Auth Bot Setup & Configuration Guide

## 📋 Table of Contents

1. [Overview](#overview)[Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Bot Configuration](#bot-configuration)
4. [Adding Mirror Bots](#adding-mirror-bots)
5. [User Commands](#user-commands)
6. [Admin Commands](#admin-commands)
7. [Troubleshooting](#troubleshooting)
8. [API Integration](#api-integration)

---

## 🎯 Overview

The WZML-X Auth Bot is a separate authentication system that provides:

- **Free 6-hour tokens** for single or multiple bots
- **Premium subscriptions** (7/30/90 days)
- **Real-time bot availability** checking
- **UUID4 token system** with auto-verification
- **Admin bot management** interface

---

## ⚡ Prerequisites

### Required Software

- **Python 3.8+** (tested with Python 3.13.2)
- **MongoDB** database access
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

### Required API Credentials

- `TELEGRAM_API` - Your Telegram API ID
- `TELEGRAM_HASH` - Your Telegram API Hash
- `BOT_TOKEN` - Auth bot token from BotFather
- `MONGODB_URI` - MongoDB connection string

---

## 🚀 Initial Setup

### 1. Install Dependencies

```bash
cd auth_bot/
pip install pyrogram motor aiohttp pymongo
```

### 2. Configure Environment

Create or update your main `config.env` file with:

```env
# Telegram API (from my.telegram.org)
TELEGRAM_API = 25888025
TELEGRAM_HASH = ae38655a4fb7d0ab3ff89e1b22052312

# Auth Bot Token (from @BotFather)
BOT_TOKEN = YOUR_AUTH_BOT_TOKEN_HERE

# MongoDB Connection
MONGODB_URI = mongodb+srv://username:password@cluster.mongodb.net/auth_bot

# Optional: Admin User IDs (comma separated)
ADMIN_IDS = 123456789,987654321
```

### 3. Start the Auth Bot

```bash
python wzml_auth_bot.py
```

---

## 🤖 Bot Configuration

### Initial State

When first started, the bot will show:

```
❌ No Mirror Leech Bots Available
All bots are currently offline or not configured.
```

This is **normal behavior** - you need to add mirror bots first.

### Adding Your First Bot

Use the admin command to add mirror bots:

```
/addbot <bot_username> <bot_token> <display_name>
```

**Example:**

```
/addbot MirrorBot1 1234567890:AAEFGHijklmnopQRSTuvwxyz123456789 Mirror Leech Bot 1
```

---

## 🔧 Adding Mirror Bots

### Method 1: Admin Commands (Recommended)

```bash
# Add a new bot
/addbot <username> <token> <name>

# Example
/addbot wzmlxbot 1234567890:AAEFGHijklmnop... WZML-X Mirror Bot

# Remove a bot
/removebot <username>

# List all configured bots
/listbots

# Check bot status
/checkbots
```

### Method 2: Manual JSON Configuration

Edit `bot_configs.json` directly:

```json
{
  "wzmlx_bot": {
    "username": "wzmlxbot",
    "token": "1234567890:AAEFGHijklmnopQRSTuvwxyz123456789",
    "name": "WZML-X Mirror Bot",
    "status": "not_configured",
    "last_checked": null,
    "added_date": "2025-09-06T10:30:00"
  }
}
```

### Method 3: Programmatic Addition

```python
from bot_manager import BotManager

bot_manager = BotManager()
await bot_manager.add_bot(
    username="wzmlxbot",
    token="1234567890:AAE...",
    name="WZML-X Mirror Bot"
)
```

---

## 👥 User Commands

### Basic Commands

```bash
/start          # Welcome message and bot info
/verify         # Start verification process
/check          # Check token status and remaining time
/stats          # Show bot statistics
```

### Verification Process

1. User sends `/verify`
2. Choose token type:
   - **Single Bot Token** (6 hours)
   - **Multi Bot Tokens** (all bots, 6 hours)
   - **Premium Subscription** (7/30/90 days)
3. Select specific bot (for single token)
4. Token generated automatically (UUID4 format)

### Token Format

```
Example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## 🔐 Admin Commands

### Bot Management

```bash
# Add new mirror bot
/addbot <username> <token> <display_name>

# Remove existing bot
/removebot <username>

# List all configured bots
/listbots

# Check all bot availability
/checkbots

# Force refresh bot status
/refreshbots
```

### System Management

```bash
# View detailed statistics
/stats

# Export user data
/export

# System health check
/health
```

### Example Admin Session

```bash
# Add multiple bots
/addbot wzmlx1 1234567890:AAE... WZML-X Bot 1
/addbot wzmlx2 0987654321:BBF... WZML-X Bot 2
/addbot wzmlx3 1122334455:CCG... WZML-X Bot 3

# Check if they're online
/checkbots

# List all configured bots
/listbots
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "No Mirror Leech Bots Available"

**Cause:** No bots configured or all bots offline
**Solution:**

```bash
# Check current bots
/listbots

# Add a bot if none exist
/addbot mybotusername token "My Bot Name"

# Check bot connectivity
/checkbots
```

#### 2. Bot Shows as "Offline" or "Error"

**Possible Causes:**

- Invalid bot token
- Bot is stopped/deleted
- Network connectivity issues
- Bot not started by owner

**Solution:**

```bash
# Remove problematic bot
/removebot problematic_bot

# Add with correct token
/addbot corrected_bot new_token "Corrected Bot Name"
```

#### 3. MongoDB Connection Error

**Check:**

- MongoDB URI is correct
- Database cluster is running
- Network access allowed
- Credentials are valid

#### 4. Telegram API Errors

**Check:**

- `TELEGRAM_API` and `TELEGRAM_HASH` are correct
- Bot token is valid
- Bot is not rate-limited

### Debug Mode

Enable detailed logging by setting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🔗 API Integration

### For Mirror Bot Integration

Mirror bots should check user verification via HTTP endpoints:

#### Check User Verification

```python
import aiohttp

async def check_user_verification(user_id, bot_key):
    """Check if user is verified for this bot"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://auth-bot-server:8000/verify/{user_id}/{bot_key}"
        ) as response:
            return await response.json()

# Response format:
{
    "verified": true,
    "expires_at": "2025-09-06T16:30:00",
    "token_type": "free_single",
    "remaining_time": "5h 23m"
}
```

#### FastAPI Endpoints (to be implemented)

```python
@app.get("/verify/{user_id}/{bot_key}")
async def verify_user(user_id: int, bot_key: str):
    # Check verification status
    pass

@app.get("/user/{user_id}/tokens")
async def get_user_tokens(user_id: int):
    # Get all user tokens
    pass
```

---

## 📊 Bot Status Indicators

### Status Types

- ✅ **Active** - Bot is online and responding
- ❌ **Error** - Bot token invalid or bot crashed
- ⚪ **Inactive** - Bot configured but not responding
- ⚙️ **Not Configured** - Bot exists but needs setup

### Auto-Refresh

- Bot status is checked every 5 minutes automatically
- Manual refresh available via "🔄 Refresh Status" button
- Failed bots are rechecked more frequently

---

## 🚀 Advanced Configuration

### Custom Token Duration

Modify in `wzml_auth_bot.py`:

```python
# Free token duration (default: 6 hours)
FREE_TOKEN_HOURS = 6

# Premium durations
PREMIUM_DURATIONS = {
    "7_days": timedelta(days=7),
    "30_days": timedelta(days=30),
    "90_days": timedelta(days=90)
}
```

### Database Persistence

Switch from in-memory to MongoDB:

```python
# Replace user_tokens dictionary with MongoDB collection
self.user_collection = self.db["user_tokens"]
```

### Custom Bot Themes

Create custom message templates in `wzml_auth_bot.py`:

```python
WELCOME_TEXT = """
🤖 **Welcome to {bot_name}**
Custom welcome message here...
"""
```

---

## 📝 Best Practices

### Security

1. **Never share bot tokens** in public
2. **Use environment variables** for sensitive data
3. **Regularly rotate tokens** if compromised
4. **Monitor bot access logs**

### Performance

1. **Limit concurrent token requests**
2. **Cache bot status** for 5-10 minutes
3. **Use background tasks** for availability checks
4. **Monitor database connection pool**

### Maintenance

1. **Regular database backups**
2. **Monitor bot uptime**
3. **Clean expired tokens** periodically
4. **Update dependencies** regularly

---

## 🆘 Support

### Getting Help

1. Check this documentation first
2. Review error logs in terminal
3. Test with a single bot first
4. Verify all credentials are correct

### Common Commands for Testing

```bash
# Quick test sequence
/start
/verify
# Select "Get 1 Token for Single Bot"
# Should show configured bots

# Admin test sequence
/listbots
/checkbots
/stats
```

---

## 📋 Checklist for Setup

### ✅ Pre-Setup

- [ ] Python 3.8+ installed
- [ ] MongoDB access configured
- [ ] Telegram API credentials obtained
- [ ] Bot token from @BotFather

### ✅ Configuration

- [ ] `config.env` updated with credentials
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Admin user IDs configured

### ✅ Bot Management

- [ ] At least one mirror bot added via `/addbot`
- [ ] Bot status checked via `/checkbots`
- [ ] Test verification flow with `/verify`

### ✅ Testing

- [ ] User can see bot selection buttons
- [ ] Tokens are generated successfully
- [ ] Token expiration tracking works
- [ ] Admin commands respond correctly

---

## 🔄 Updates & Migration

### Version Updates

When updating the auth bot:

1. **Backup** `bot_configs.json`
2. **Backup** MongoDB user data
3. **Test** in development environment first
4. **Update** dependencies if needed

### Data Migration

If changing database structure:

```python
# Migration script example
async def migrate_user_data():
    # Convert old format to new format
    pass
```

---

**🎉 Your WZML-X Auth Bot is now ready to use!**

For additional support or custom modifications, refer to the source code in `wzml_auth_bot.py` and `bot_manager.py`.
