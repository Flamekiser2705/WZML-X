#!/usr/bin/env python3
import secrets
import string
import hashlib
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from typing import Tuple, Optional
import uuid
import logging

from ..database.models import TokenType

logger = logging.getLogger(__name__)


class TokenGenerator:
    """Token generation and validation utilities"""
    
    def __init__(self, secret_key: str):
        """Initialize with secret key for encryption"""
        # Create a consistent key from secret
        key = hashlib.sha256(secret_key.encode()).digest()
        self.fernet = Fernet(b64encode(key))
    
    @staticmethod
    def generate_token_id() -> str:
        """Generate unique token ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token using UUID4"""
        # Use UUID4 as base and add additional randomness if needed
        base_token = str(uuid.uuid4()).replace('-', '')
        
        if length <= 32:
            return base_token[:length]
        else:
            # If longer token needed, add more UUID4s
            additional_length = length - 32
            additional_uuid = str(uuid.uuid4()).replace('-', '')
            return base_token + additional_uuid[:additional_length]

    def create_uuid4_token(self, user_id: int, bot_id: str, token_type: TokenType) -> str:
        """Create UUID4-based token - primary token generation method"""
        try:
            # Generate UUID4 token
            uuid4_token = str(uuid.uuid4())
            
            # Store metadata separately in database, return clean UUID4
            logger.info(f"Generated UUID4 token for user {user_id}, bot {bot_id}, type {token_type}")
            return uuid4_token
            
        except Exception as e:
            logger.error(f"Error creating UUID4 token: {e}")
            return ""

    def create_encrypted_token(self, user_id: int, bot_id: str, token_type: TokenType, 
                             expires_at: datetime) -> str:
        """Create encrypted token with metadata (legacy method)"""
        try:
            # Use UUID4 as base token
            uuid4_token = str(uuid.uuid4())
            
            # Create token payload with UUID4
            token_data = {
                "user_id": user_id,
                "bot_id": bot_id,
                "type": token_type.value,
                "expires_at": expires_at.isoformat(),
                "uuid_token": uuid4_token
            }
            
            # Convert to string and encrypt
            token_string = f"{user_id}:{bot_id}:{token_type.value}:{expires_at.isoformat()}:{uuid4_token}"
            encrypted_data = self.fernet.encrypt(token_string.encode())
            
            # Return the UUID4 token directly for simplicity
            return uuid4_token
            
        except Exception as e:
            logger.error(f"Error creating encrypted token: {e}")
            return ""
    
    def decrypt_token(self, token: str) -> Optional[dict]:
        """Validate UUID4 token format"""
        try:
            # Check if it's a valid UUID4 format
            uuid_obj = uuid.UUID(token, version=4)
            if str(uuid_obj) == token:
                return {
                    "uuid_token": token,
                    "valid_format": True
                }
            else:
                return None
                
        except (ValueError, TypeError) as e:
            # If UUID4 check fails, try legacy encrypted token format
            try:
                # Decode from base64
                encrypted_data = b64decode(token.encode())
                
                # Decrypt
                decrypted_data = self.fernet.decrypt(encrypted_data).decode()
                
                # Parse token data
                parts = decrypted_data.split(":")
                if len(parts) != 5:
                    return None
                
                user_id, bot_id, token_type, expires_at_str, uuid_token = parts
                
                return {
                    "user_id": int(user_id),
                    "bot_id": bot_id,
                    "type": token_type,
                    "expires_at": datetime.fromisoformat(expires_at_str),
                    "uuid_token": uuid_token
                }
                
            except Exception as decrypt_error:
                logger.error(f"Error validating token: {e}, {decrypt_error}")
                return None
    
    @staticmethod
    def calculate_expiry_time(token_type: TokenType, custom_days: Optional[int] = None) -> datetime:
        """Calculate token expiry time based on type"""
        now = datetime.utcnow()
        
        if token_type == TokenType.FREE:
            # Free tokens expire in 6 hours
            return now + timedelta(hours=6)
        else:
            # Premium tokens - default to 7 days if no custom days specified
            days = custom_days or 7
            return now + timedelta(days=days)
    
    def generate_access_token(self, user_id: int, bot_id: str, token_type: TokenType,
                            custom_days: Optional[int] = None) -> Tuple[str, str, datetime]:
        """Generate complete access token using UUID4"""
        try:
            # Generate unique token ID (also UUID4)
            token_id = str(uuid.uuid4())
            
            # Calculate expiry time
            expires_at = self.calculate_expiry_time(token_type, custom_days)
            
            # Create UUID4 token (primary method)
            uuid4_token = self.create_uuid4_token(user_id, bot_id, token_type)
            
            if not uuid4_token:
                raise Exception("Failed to create UUID4 token")
            
            logger.info(f"Generated UUID4 token {uuid4_token} for user {user_id}, bot {bot_id}, type {token_type}")
            return token_id, uuid4_token, expires_at
            
        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            raise
    
    def validate_token_format(self, token: str) -> bool:
        """Validate UUID4 token format"""
        try:
            # Check if it's a valid UUID4
            uuid_obj = uuid.UUID(token, version=4)
            return str(uuid_obj) == token
        except (ValueError, TypeError):
            # If UUID4 check fails, try legacy base64 format
            try:
                b64decode(token.encode())
                return True
            except Exception:
                return False
    
    @staticmethod
    def generate_payment_id() -> str:
        """Generate unique payment ID using UUID4"""
        return f"pay_{uuid.uuid4()}"
    
    @staticmethod
    def generate_simple_uuid4_token() -> str:
        """Generate simple UUID4 token"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_simple_token(user_id: int, bot_id: str) -> str:
        """Generate simple token using UUID4 as base"""
        # Use UUID4 as primary identifier
        uuid4_token = str(uuid.uuid4())
        timestamp = int(datetime.utcnow().timestamp())
        
        # Format: uuid4_timestamp for easy parsing
        token_data = f"{uuid4_token}_{timestamp}_{user_id}_{bot_id}"
        return b64encode(token_data.encode()).decode()
    
    @staticmethod
    def decode_simple_token(token: str) -> Optional[dict]:
        """Decode simple UUID4-based token"""
        try:
            decoded_data = b64decode(token.encode()).decode()
            parts = decoded_data.split("_")
            
            if len(parts) >= 4:
                # New format: uuid4_timestamp_user_id_bot_id
                uuid4_token, timestamp, user_id, bot_id = parts[0], parts[1], parts[2], "_".join(parts[3:])
                return {
                    "uuid_token": uuid4_token,
                    "user_id": int(user_id),
                    "bot_id": bot_id,
                    "timestamp": int(timestamp)
                }
            else:
                # Try legacy format: user_id&&bot_id&&timestamp&&random
                legacy_parts = decoded_data.split("&&")
                if len(legacy_parts) == 4:
                    user_id, bot_id, timestamp, random_data = legacy_parts
                    return {
                        "user_id": int(user_id),
                        "bot_id": bot_id,
                        "timestamp": int(timestamp),
                        "random": random_data
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error decoding simple token: {e}")
            return None
    
    @staticmethod
    def is_valid_uuid4(token: str) -> bool:
        """Check if string is a valid UUID4"""
        try:
            uuid_obj = uuid.UUID(token, version=4)
            return str(uuid_obj) == token
        except (ValueError, TypeError):
            return False


class TokenValidator:
    """Token validation utilities"""
    
    def __init__(self, token_generator: TokenGenerator):
        self.token_generator = token_generator
    
    def validate_token_expiry(self, expires_at: datetime) -> bool:
        """Check if token has expired"""
        return datetime.utcnow() < expires_at
    
    def validate_token_structure(self, token: str) -> bool:
        """Validate token structure"""
        return self.token_generator.validate_token_format(token)
    
    def extract_token_info(self, token: str) -> Optional[dict]:
        """Extract information from token"""
        return self.token_generator.decrypt_token(token)
    
    async def validate_token_in_database(self, db_manager, token: str, user_id: int, bot_id: str) -> bool:
        """Validate token against database"""
        try:
            return await db_manager.validate_token(bot_id, user_id, token)
        except Exception as e:
            logger.error(f"Error validating token in database: {e}")
            return False


# Utility functions for token management
def format_expiry_time(expires_at: datetime) -> str:
    """Format expiry time for display"""
    now = datetime.utcnow()
    diff = expires_at - now
    
    if diff.total_seconds() <= 0:
        return "Expired"
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_token_type_display(token_type: TokenType) -> str:
    """Get display string for token type"""
    return "🆓 Free" if token_type == TokenType.FREE else "💎 Premium"


def calculate_plan_duration_days(plan_type: str) -> int:
    """Calculate duration in days for plan type"""
    plan_mapping = {
        "7d": 7,
        "30d": 30,
        "90d": 90
    }
    return plan_mapping.get(plan_type, 7)
