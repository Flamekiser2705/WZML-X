#!/usr/bin/env python3
import logging
import httpx
from typing import Optional, Dict, Any
from ..config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

logger = logging.getLogger(__name__)


class RazorpayHandler:
    """Razorpay payment handler"""
    
    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = "https://api.razorpay.com/v1"
        
    async def create_order(self, amount: int, currency: str = "INR", receipt: str = "") -> Optional[Dict]:
        """Create Razorpay order"""
        try:
            if not self.key_id or not self.key_secret:
                logger.warning("Razorpay credentials not configured")
                return None
                
            order_data = {
                "amount": amount,  # amount in paise
                "currency": currency,
                "receipt": receipt,
                "partial_payment": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/orders",
                    json=order_data,
                    auth=(self.key_id, self.key_secret)
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Razorpay order creation failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {e}")
            return None
    
    async def create_payment_link(self, order_id: str, amount: int, description: str, user_id: int) -> Optional[str]:
        """Create Razorpay payment link"""
        try:
            if not self.key_id or not self.key_secret:
                return None
                
            payment_link_data = {
                "amount": amount,
                "currency": "INR",
                "description": description,
                "customer": {
                    "contact": "+919999999999",  # You might want to collect this from user
                    "email": f"user{user_id}@example.com"
                },
                "notify": {
                    "sms": False,
                    "email": False
                },
                "reminder_enable": True,
                "callback_url": f"https://your-domain.com/payment/callback/{order_id}",
                "callback_method": "get"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payment_links",
                    json=payment_link_data,
                    auth=(self.key_id, self.key_secret)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("short_url")
                else:
                    logger.error(f"Razorpay payment link creation failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating Razorpay payment link: {e}")
            return None
    
    async def verify_payment(self, payment_id: str, order_id: str, signature: str) -> bool:
        """Verify Razorpay payment signature"""
        try:
            import hmac
            import hashlib
            
            generated_signature = hmac.new(
                self.key_secret.encode(),
                f"{order_id}|{payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(generated_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Razorpay payment: {e}")
            return False


class PayPalHandler:
    """PayPal payment handler"""
    
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.base_url = "https://api.sandbox.paypal.com" if sandbox else "https://api.paypal.com"
        
    async def get_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        try:
            if not self.client_id or not self.client_secret:
                logger.warning("PayPal credentials not configured")
                return None
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/oauth2/token",
                    data="grant_type=client_credentials",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    auth=(self.client_id, self.client_secret)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
                else:
                    logger.error(f"PayPal token request failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {e}")
            return None
    
    async def create_payment_link(self, amount: int, currency: str, description: str, 
                                return_url: str, cancel_url: str) -> Optional[str]:
        """Create PayPal payment link"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None
                
            payment_data = {
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description
                }],
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/payments/payment",
                    json=payment_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    # Find approval URL
                    for link in data.get("links", []):
                        if link.get("rel") == "approval_url":
                            return link.get("href")
                    return None
                else:
                    logger.error(f"PayPal payment creation failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating PayPal payment: {e}")
            return None
    
    async def execute_payment(self, payment_id: str, payer_id: str) -> bool:
        """Execute PayPal payment"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return False
                
            execute_data = {"payer_id": payer_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/payments/payment/{payment_id}/execute",
                    json=execute_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error executing PayPal payment: {e}")
            return False


class PaymentUtils:
    """General payment utilities"""
    
    @staticmethod
    def format_amount(amount: int, currency: str = "INR") -> str:
        """Format amount for display"""
        if currency == "INR":
            return f"₹{amount // 100}"
        elif currency == "USD":
            return f"${amount}"
        else:
            return f"{amount} {currency}"
    
    @staticmethod
    def convert_currency(amount: int, from_currency: str, to_currency: str) -> int:
        """Simple currency conversion (you might want to use a real API)"""
        # Basic conversion rates (update these with real-time rates)
        rates = {
            ("INR", "USD"): 0.012,
            ("USD", "INR"): 83.0,
            ("INR", "EUR"): 0.011,
            ("EUR", "INR"): 91.0
        }
        
        rate = rates.get((from_currency, to_currency), 1.0)
        return int(amount * rate)
    
    @staticmethod
    def validate_payment_amount(amount: int, min_amount: int = 100) -> bool:
        """Validate payment amount"""
        return amount >= min_amount and amount <= 1000000  # Max 10,000 INR or 100 USD
    
    @staticmethod
    def generate_receipt_id(user_id: int, plan_id: str) -> str:
        """Generate receipt ID for payment"""
        import time
        timestamp = int(time.time())
        return f"rcpt_{user_id}_{plan_id}_{timestamp}"
