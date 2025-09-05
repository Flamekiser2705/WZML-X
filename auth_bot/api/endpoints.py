#!/usr/bin/env python3
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from ..database.operations import DatabaseManager
from ..database.models import TokenValidationResponse, TokenRequest
from ..utils.token_utils import TokenValidator
from ..bot.config import MONGODB_URI, JWT_SECRET, API_HOST, API_PORT

logger = logging.getLogger(__name__)

# Global instances
db_manager: DatabaseManager = None
token_validator: TokenValidator = None

# FastAPI app
app = FastAPI(
    title="WZML-X Auth API",
    description="Authentication API for WZML-X Mirror Bots",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


class TokenValidateRequest(BaseModel):
    """Token validation request model"""
    user_id: int
    bot_id: str
    token: str


class TokenValidateResponse(BaseModel):
    """Token validation response model"""
    is_valid: bool
    user_id: Optional[int] = None
    token_type: Optional[str] = None
    expires_at: Optional[str] = None
    message: str = ""


class UserInfoRequest(BaseModel):
    """User info request model"""
    user_id: int


class UserInfoResponse(BaseModel):
    """User info response model"""
    user_id: int
    subscription_type: str
    premium_expiry: Optional[str] = None
    active_tokens: int
    total_tokens: int


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for authentication"""
    # For now, we'll use a simple JWT secret as API key
    # In production, implement proper JWT token validation
    if credentials.credentials != JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global db_manager, token_validator
    
    try:
        db_manager = DatabaseManager(MONGODB_URI)
        await db_manager.connect()
        
        from ..utils.token_utils import TokenGenerator
        token_generator = TokenGenerator(JWT_SECRET)
        token_validator = TokenValidator(token_generator)
        
        logger.info("✅ API server initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize API server: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_manager
    
    if db_manager:
        await db_manager.disconnect()
    
    logger.info("🛑 API server shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WZML-X Auth API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        if db_manager and db_manager.client:
            await db_manager.client.admin.command('ping')
            db_status = "healthy"
        else:
            db_status = "disconnected"
        
        return {
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.post("/validate-token", response_model=TokenValidateResponse)
async def validate_token(
    request: TokenValidateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Validate authentication token"""
    try:
        # Validate token in database
        is_valid = await db_manager.validate_token(
            request.bot_id,
            request.user_id,
            request.token
        )
        
        if is_valid:
            # Get token details
            tokens = await db_manager.get_user_tokens(request.user_id, request.bot_id)
            matching_token = None
            
            for token in tokens:
                if token.token == request.token:
                    matching_token = token
                    break
            
            if matching_token:
                return TokenValidateResponse(
                    is_valid=True,
                    user_id=request.user_id,
                    token_type=matching_token.type.value,
                    expires_at=matching_token.expires_at.isoformat(),
                    message="Token is valid"
                )
        
        return TokenValidateResponse(
            is_valid=False,
            message="Invalid or expired token"
        )
        
    except Exception as e:
        logger.error(f"❌ Error validating token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation error"
        )


@app.post("/user-info", response_model=UserInfoResponse)
async def get_user_info(
    request: UserInfoRequest,
    api_key: str = Depends(verify_api_key)
):
    """Get user information"""
    try:
        user = await db_manager.get_user(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user statistics
        stats = await db_manager.get_user_stats(request.user_id)
        
        return UserInfoResponse(
            user_id=request.user_id,
            subscription_type=user.subscription_type.value,
            premium_expiry=user.premium_expiry.isoformat() if user.premium_expiry else None,
            active_tokens=stats.get("active_tokens", 0),
            total_tokens=stats.get("total_tokens", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@app.get("/stats")
async def get_system_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics"""
    try:
        stats = await db_manager.get_system_stats()
        return {
            "total_users": stats.get("total_users", 0),
            "premium_users": stats.get("premium_users", 0),
            "free_users": stats.get("free_users", 0),
            "active_tokens": stats.get("active_tokens", 0),
            "completed_payments": stats.get("completed_payments", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system statistics"
        )


@app.post("/revoke-token")
async def revoke_token(
    request: TokenValidateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Revoke a token"""
    try:
        # Find the token
        tokens = await db_manager.get_user_tokens(request.user_id, request.bot_id)
        token_to_revoke = None
        
        for token in tokens:
            if token.token == request.token:
                token_to_revoke = token
                break
        
        if not token_to_revoke:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        # Revoke the token
        success = await db_manager.revoke_token(token_to_revoke.token_id)
        
        if success:
            return {"message": "Token revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error revoking token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke token"
        )


# Webhook endpoints for payment gateways
@app.post("/webhook/razorpay")
async def razorpay_webhook(payload: dict):
    """Handle Razorpay webhooks"""
    try:
        # Verify webhook signature (implement this)
        # Process payment update
        event = payload.get("event")
        
        if event == "payment.captured":
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            
            # Update payment status in database
            # This is a simplified version - implement proper webhook handling
            
            logger.info(f"Razorpay payment captured: {order_id}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Error handling Razorpay webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing error"
        )


@app.post("/webhook/paypal")
async def paypal_webhook(payload: dict):
    """Handle PayPal webhooks"""
    try:
        # Process PayPal webhook
        event_type = payload.get("event_type")
        
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Process successful payment
            logger.info("PayPal payment completed")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Error handling PayPal webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing error"
        )


async def start_api_server():
    """Start the API server"""
    config = uvicorn.Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    import asyncio
    asyncio.run(start_api_server())
