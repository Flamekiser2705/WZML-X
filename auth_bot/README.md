# WZML-X Auth Bot

A comprehensive authentication system for WZML-X mirror/leech bots with premium subscription management.

## Features

✨ **User Authentication**
- Free users get 6-hour UUID4 tokens
- Premium users get 7/30/90-day UUID4 tokens
- Automatic token expiry with TTL indexes
- Secure UUID4 token generation (RFC 4122 compliant)

💳 **Payment Integration**
- Razorpay integration for Indian users
- PayPal integration for international users
- Automated subscription management
- Webhook support for real-time updates

🤖 **Multi-Bot Support**
- Single auth bot for multiple mirror bots
- API endpoints for UUID4 token validation
- Centralized user management
- Bot-specific access control

🔐 **Security Features**
- UUID4 token standard (128-bit entropy)
- Cryptographically secure random generation
- Rate limiting and abuse prevention
- Admin controls and user banning

📊 **Admin Dashboard**
- User management interface
- Payment tracking
- Token statistics
- System monitoring

## Project Structure

```
auth_bot/
├── main.py                    # Main bot entry point
├── api_server.py             # FastAPI server for token validation
├── setup.py                  # Installation script
├── auth_requirements.txt     # Python dependencies
├── .env.example              # Configuration template
├── README.md                 # This file
│
├── bot/                      # Telegram bot handlers
│   ├── __init__.py
│   └── handlers/
│       ├── __init__.py
│       ├── auth_handler.py   # User registration & verification
│       ├── token_handler.py  # Token generation & management
│       ├── payment_handler.py # Payment processing
│       └── admin_handler.py  # Admin commands
│
├── database/                 # Database models & operations
│   ├── __init__.py
│   ├── connection.py         # MongoDB connection
│   ├── models.py            # Pydantic models
│   └── operations.py        # Database CRUD operations
│
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── token_utils.py       # Token generation utilities
│   └── helpers.py           # Helper functions
│
├── api/                      # FastAPI endpoints
│   ├── __init__.py
│   └── endpoints.py         # API routes
│
├── payments/                 # Payment processing
│   ├── __init__.py
│   ├── razorpay_handler.py  # Razorpay integration
│   ├── paypal_handler.py    # PayPal integration
│   └── payment_utils.py     # Payment utilities
│
└── integration/              # Main bot integration
    ├── __init__.py
    └── main_bot_integration.py # Integration examples
```

## Installation

### Prerequisites
- Python 3.8 or higher
- MongoDB database
- Telegram API credentials
- Payment gateway accounts (optional)

### Quick Setup

1. **Clone and Setup**
   ```bash
   cd auth_bot
   python setup.py
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install Dependencies**
   ```bash
   pip install -r auth_requirements.txt
   ```

### Configuration

Edit the `.env` file with your settings:

```env
# Bot Configuration
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Database
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=wzml_auth_bot

# API Server
API_HOST=0.0.0.0
API_PORT=8001
API_SECRET_KEY=your_secret_api_key

# Payment Gateways
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret

# Security
ENCRYPTION_KEY=your_32_character_encryption_key
JWT_SECRET=your_jwt_secret_key

# Admin
ADMIN_IDS=123456789,987654321
```

## Usage

### Starting the Auth Bot

1. **Start the Telegram Bot**
   ```bash
   python main.py
   ```

2. **Start the API Server** (in another terminal)
   ```bash
   python api_server.py
   ```

### User Flow

1. **User starts the auth bot**
   ```
   /start
   ```

2. **User requests verification**
   ```
   /verify
   ```

3. **User chooses token type**
   - Free Token (6 hours)
   - Premium 7 days
   - Premium 30 days
   - Premium 90 days

4. **For premium tokens, user completes payment**
   - Razorpay for Indian users
   - PayPal for international users

5. **User receives UUID4 token and uses it in main bots**
   ```
   Token: 550e8400-e29b-41d4-a716-446655440000
   Usage: /mirror https://example.com 550e8400-e29b-41d4-a716-446655440000
   ```

### Admin Commands

```bash
/admin_panel          # Access admin dashboard
/ban_user <user_id>   # Ban a user
/unban_user <user_id> # Unban a user
/stats                # View system statistics
/broadcast <message>  # Send message to all users
```

## Integration with Main Bots

### Example Integration

```python
from auth_bot.integration.main_bot_integration import AuthBotClient, AuthMiddleware

# Initialize auth client
auth_client = AuthBotClient(
    auth_api_url="http://localhost:8001",
    auth_api_key="your-api-key"
)

auth_middleware = AuthMiddleware(auth_client, "your_bot_id")

# In your mirror/leech handlers
@Client.on_message(filters.command("mirror"))
async def mirror_handler(client, message):
    user_id = message.from_user.id
    
    # Check authorization
    async with auth_client:
        auth_result = await auth_middleware.check_authorization(user_id)
    
    if not auth_result.get("valid"):
        await message.reply_text("❌ Access Denied. Get token from @YourAuthBot")
        return
    
    # User is authorized, proceed with mirror operation
    await message.reply_text("✅ Starting mirror...")
```

### API Endpoints

- `POST /validate-token` - Validate user tokens
- `GET /user-info/{user_id}` - Get user information
- `POST /webhooks/razorpay` - Razorpay webhook
- `POST /webhooks/paypal` - PayPal webhook
- `GET /stats` - System statistics

## Token Types

### Free Tokens
- **Duration**: 6 hours
- **Bots**: All registered bots
- **Limit**: 1 active token per user per bot

### Premium Tokens
- **7 Days**: ₹5 / $1
- **30 Days**: ₹20 / $3
- **90 Days**: ₹50 / $7
- **Features**: Multiple bot access, priority support

## Database Schema

### Collections

1. **users** - User accounts and subscriptions
2. **tokens** - Active tokens with TTL expiry
3. **bots** - Registered bot information
4. **payments** - Payment transaction records
5. **plans** - Subscription plan details

### TTL Indexes

- Tokens automatically expire based on subscription type
- Free tokens: 6 hours
- Premium tokens: 7/30/90 days

## Security Features

### Token Security
- **UUID4 Standard**: RFC 4122 compliant universally unique identifiers
- **128-bit Entropy**: 2^128 possible token combinations (340,282,366,920,938,463,463,374,607,431,768,211,456)
- **Cryptographic Randomness**: Generated using secure random number generators
- **No Predictable Patterns**: Version 4 UUIDs use random/pseudo-random numbers
- **Database Optimized**: Efficient indexing and validation
- **URL Safe**: No special characters requiring encoding
- **Human Readable**: Standard format with hyphens for clarity

### Token Format
```
Format: xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx
Example: 550e8400-e29b-41d4-a716-446655440000
Length: 36 characters (32 hex digits + 4 hyphens)
Version: 4 (indicated by the '4' in the 3rd group)
```

### Access Control
- User authentication required for all operations
- Admin-only commands and endpoints
- Rate limiting on API endpoints
- Input validation and sanitization

### Payment Security
- Webhook signature verification
- Secure payment gateway integration
- Transaction logging and audit trails
- Fraud detection mechanisms

## Monitoring and Logging

### Logging
- Structured logging with timestamps
- Separate log files for different components
- Error tracking and alerts
- User activity monitoring

### Statistics
- User registration trends
- Token usage patterns
- Payment success rates
- Bot usage statistics

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
- Modular design with clear separation of concerns
- Async/await throughout for performance
- Type hints for better code quality
- Comprehensive error handling

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

2. **Database Connection Issues**
   - Verify MongoDB is running
   - Check connection string in .env

3. **Bot Token Issues**
   - Verify bot token with @BotFather
   - Check API ID and hash

4. **Payment Issues**
   - Verify payment gateway credentials
   - Check webhook URLs

### Support

For support and questions:
- Check the documentation
- Review error logs
- Contact the development team

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Changelog

### v1.0.0
- Initial release
- User authentication system
- Payment integration
- Multi-bot support
- Admin dashboard
- API endpoints for token validation

---

**Created for WZML-X Project**  
*Secure, Scalable, and Feature-Rich Authentication System*
