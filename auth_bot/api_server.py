#!/usr/bin/env python3
"""
API Server for Auth Bot
FastAPI server to handle token validation and webhooks
"""

import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import get_database
from database.operations import DatabaseManager
from utils.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global database manager
db_manager = None
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_manager
    
    # Startup
    logger.info("🚀 Starting Auth Bot API Server...")
    try:
        database = await get_database()
        db_manager = DatabaseManager(database)
        await db_manager.create_indexes()
        logger.info("✅ Database initialized")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Auth Bot API Server...")
        if db_manager:
            await db_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Auth Bot API",
    description="Authentication and Token Validation API for WZML-X Bots",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for protected endpoints"""
    if credentials.credentials != Config.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Auth Bot API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db_manager.get_database_stats()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/validate-token")
async def validate_token(
    request: dict,
    api_key: str = Depends(verify_api_key)
):
    """Validate a user token"""
    try:
        token = request.get("token")
        bot_id = request.get("bot_id")
        
        if not token or not bot_id:
            raise HTTPException(status_code=400, detail="Token and bot_id are required")
        
        # Validate token
        result = await db_manager.validate_token(token, bot_id)
        
        if result:
            # Increment usage count
            await db_manager.increment_token_usage(token)
            
            return {
                "valid": True,
                "user_id": result.user_id,
                "token_type": result.token_type.value,
                "expires_at": result.expires_at.isoformat(),
                "usage_count": result.usage_count + 1
            }
        else:
            return {"valid": False, "reason": "Invalid or expired token"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error validating token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/user-info/{user_id}")
async def get_user_info(
    user_id: int,
    api_key: str = Depends(verify_api_key)
):
    """Get user information"""
    try:
        user = await db_manager.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        stats = await db_manager.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "username": user.username,
            "subscription_type": user.subscription_type.value,
            "premium_expiry": user.premium_expiry.isoformat() if user.premium_expiry else None,
            "is_banned": user.is_banned,
            "created_at": user.created_at.isoformat(),
            "last_active": user.last_active.isoformat(),
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/webhooks/razorpay")
async def razorpay_webhook(request: dict):
    """Handle Razorpay webhook"""
    try:
        # Verify webhook signature (implement as needed)
        event = request.get("event")
        payload = request.get("payload", {})
        
        if event == "payment.captured":
            payment_id = payload.get("payment", {}).get("entity", {}).get("id")
            amount = payload.get("payment", {}).get("entity", {}).get("amount", 0) / 100  # Convert from paise
            
            # Process successful payment
            logger.info(f"💰 Payment captured: {payment_id}, Amount: ₹{amount}")
            
            # Update payment status in database
            # This would be implemented based on your payment tracking
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Error processing Razorpay webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@app.post("/webhooks/paypal")
async def paypal_webhook(request: dict):
    """Handle PayPal webhook"""
    try:
        # Verify webhook signature (implement as needed)
        event_type = request.get("event_type")
        resource = request.get("resource", {})
        
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            payment_id = resource.get("id")
            amount = resource.get("amount", {}).get("value", "0")
            
            # Process successful payment
            logger.info(f"💰 PayPal payment completed: {payment_id}, Amount: ${amount}")
            
            # Update payment status in database
            # This would be implemented based on your payment tracking
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Error processing PayPal webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics"""
    try:
        stats = await db_manager.get_database_stats()
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/admin/ban-user")
async def ban_user(
    request: dict,
    api_key: str = Depends(verify_api_key)
):
    """Ban a user (admin only)"""
    try:
        user_id = request.get("user_id")
        reason = request.get("reason", "No reason provided")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Ban user
        result = await db_manager.ban_user(user_id, reason)
        
        if result:
            return {"success": True, "message": f"User {user_id} banned successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error banning user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/admin/unban-user")
async def unban_user(
    request: dict,
    api_key: str = Depends(verify_api_key)
):
    """Unban a user (admin only)"""
    try:
        user_id = request.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Unban user
        result = await db_manager.unban_user(user_id)
        
        if result:
            return {"success": True, "message": f"User {user_id} unbanned successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error unbanning user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def run_server():
    """Run the API server"""
    try:
        uvicorn.run(
            "api_server:app",
            host=Config.API_HOST,
            port=Config.API_PORT,
            reload=Config.DEBUG,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_server()
