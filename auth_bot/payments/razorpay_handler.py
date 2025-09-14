#!/usr/bin/env python3
"""
Razorpay Payment Handler
Handles premium subscription payments via Razorpay
"""

import razorpay
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import uuid

logger = logging.getLogger(__name__)

class RazorpayHandler:
    """Handles Razorpay payment processing"""
    
    def __init__(self):
        self.key_id = os.getenv('RAZORPAY_KEY_ID', '')
        self.key_secret = os.getenv('RAZORPAY_KEY_SECRET', '')
        
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            self.enabled = True
            logger.info("✅ Razorpay payment handler initialized")
        else:
            self.client = None
            self.enabled = False
            logger.warning("⚠️ Razorpay credentials not configured")
    
    def is_enabled(self) -> bool:
        """Check if Razorpay is enabled"""
        return self.enabled
    
    async def create_payment_order(self, amount: int, currency: str = "INR", 
                                 user_id: int = None, plan_type: str = None) -> Optional[Dict]:
        """
        Create Razorpay payment order
        
        Args:
            amount: Amount in paise (₹1 = 100 paise)
            currency: Currency code (default INR)
            user_id: Telegram user ID
            plan_type: Plan type (7d, 30d, 90d)
            
        Returns:
            dict: Order details or None if failed
        """
        if not self.enabled:
            logger.error("Razorpay not configured")
            return None
        
        try:
            # Generate unique receipt ID
            receipt_id = f"wzmlx_{user_id}_{plan_type}_{uuid.uuid4().hex[:8]}"
            
            order_data = {
                "amount": amount,  # Amount in paise
                "currency": currency,
                "receipt": receipt_id,
                "notes": {
                    "user_id": str(user_id),
                    "plan_type": plan_type,
                    "service": "WZML-X Premium Subscription",
                    "created_at": datetime.now().isoformat()
                }
            }
            
            order = self.client.order.create(data=order_data)
            logger.info(f"Created Razorpay order: {order['id']} for user {user_id}")
            
            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "receipt": order["receipt"],
                "status": order["status"],
                "created_at": order["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            return None
    
    async def verify_payment(self, payment_id: str, order_id: str, signature: str) -> bool:
        """
        Verify Razorpay payment signature
        
        Args:
            payment_id: Payment ID from Razorpay
            order_id: Order ID from Razorpay
            signature: Payment signature
            
        Returns:
            bool: True if payment is verified
        """
        if not self.enabled:
            return False
        
        try:
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            logger.info(f"Payment verified: {payment_id}")
            return True
            
        except razorpay.errors.SignatureVerificationError:
            logger.error(f"Payment signature verification failed: {payment_id}")
            return False
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    async def get_payment_details(self, payment_id: str) -> Optional[Dict]:
        """
        Get payment details from Razorpay
        
        Args:
            payment_id: Payment ID
            
        Returns:
            dict: Payment details or None
        """
        if not self.enabled:
            return None
        
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                "id": payment["id"],
                "amount": payment["amount"],
                "currency": payment["currency"],
                "status": payment["status"],
                "order_id": payment["order_id"],
                "method": payment["method"],
                "email": payment.get("email", ""),
                "contact": payment.get("contact", ""),
                "created_at": payment["created_at"],
                "captured": payment["captured"]
            }
            
        except Exception as e:
            logger.error(f"Error fetching payment details: {e}")
            return None
    
    async def refund_payment(self, payment_id: str, amount: int = None, 
                           reason: str = "requested_by_customer") -> Optional[Dict]:
        """
        Process refund for a payment
        
        Args:
            payment_id: Payment ID to refund
            amount: Refund amount in paise (None for full refund)
            reason: Reason for refund
            
        Returns:
            dict: Refund details or None
        """
        if not self.enabled:
            return None
        
        try:
            refund_data = {"speed": "normal", "reason": reason}
            if amount:
                refund_data["amount"] = amount
            
            refund = self.client.payment.refund(payment_id, refund_data)
            logger.info(f"Refund processed: {refund['id']} for payment {payment_id}")
            
            return {
                "id": refund["id"],
                "payment_id": refund["payment_id"],
                "amount": refund["amount"],
                "currency": refund["currency"],
                "status": refund["status"],
                "speed": refund["speed"],
                "created_at": refund["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            return None

# Global instance
razorpay_handler = RazorpayHandler()

# Convenience functions
async def create_payment_order(user_id: int, plan_type: str, amount: int) -> Optional[Dict]:
    """Create payment order for user"""
    return await razorpay_handler.create_payment_order(amount, "INR", user_id, plan_type)

async def verify_payment(payment_id: str, order_id: str, signature: str) -> bool:
    """Verify payment signature"""
    return await razorpay_handler.verify_payment(payment_id, order_id, signature)

async def get_payment_details(payment_id: str) -> Optional[Dict]:
    """Get payment details"""
    return await razorpay_handler.get_payment_details(payment_id)