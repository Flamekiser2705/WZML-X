#!/usr/bin/env python3
"""
PayPal Payment Handler
Handles premium subscription payments via PayPal
"""

import paypalrestsdk
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import uuid

logger = logging.getLogger(__name__)

class PayPalHandler:
    """Handles PayPal payment processing"""
    
    def __init__(self):
        self.client_id = os.getenv('PAYPAL_CLIENT_ID', '')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET', '')
        self.mode = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'
        
        if self.client_id and self.client_secret:
            paypalrestsdk.configure({
                "mode": self.mode,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            self.enabled = True
            logger.info(f"✅ PayPal payment handler initialized (mode: {self.mode})")
        else:
            self.enabled = False
            logger.warning("⚠️ PayPal credentials not configured")
    
    def is_enabled(self) -> bool:
        """Check if PayPal is enabled"""
        return self.enabled
    
    async def create_payment(self, amount: float, currency: str = "USD", 
                           user_id: int = None, plan_type: str = None,
                           return_url: str = None, cancel_url: str = None) -> Optional[Dict]:
        """
        Create PayPal payment
        
        Args:
            amount: Amount in currency units
            currency: Currency code (USD, EUR, etc.)
            user_id: Telegram user ID
            plan_type: Plan type (7d, 30d, 90d)
            return_url: Success return URL
            cancel_url: Cancel return URL
            
        Returns:
            dict: Payment details or None if failed
        """
        if not self.enabled:
            logger.error("PayPal not configured")
            return None
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url or "https://t.me/SoulKaizer_bot?start=payment_success",
                    "cancel_url": cancel_url or "https://t.me/SoulKaizer_bot?start=payment_cancelled"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"WZML-X Premium Subscription ({plan_type})",
                            "sku": f"wzmlx_premium_{plan_type}",
                            "price": str(amount),
                            "currency": currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": f"WZML-X Premium subscription for {plan_type}",
                    "custom": f"user_id:{user_id},plan:{plan_type}",
                    "invoice_number": f"WZMLX_{user_id}_{plan_type}_{uuid.uuid4().hex[:8]}"
                }]
            })
            
            if payment.create():
                logger.info(f"Created PayPal payment: {payment.id} for user {user_id}")
                
                # Get approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    "payment_id": payment.id,
                    "approval_url": approval_url,
                    "amount": amount,
                    "currency": currency,
                    "status": payment.state,
                    "created_time": payment.create_time
                }
            else:
                logger.error(f"PayPal payment creation failed: {payment.error}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create PayPal payment: {e}")
            return None
    
    async def execute_payment(self, payment_id: str, payer_id: str) -> Optional[Dict]:
        """
        Execute PayPal payment after user approval
        
        Args:
            payment_id: Payment ID from PayPal
            payer_id: Payer ID from PayPal
            
        Returns:
            dict: Execution result or None
        """
        if not self.enabled:
            return None
        
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"PayPal payment executed: {payment_id}")
                
                return {
                    "payment_id": payment.id,
                    "state": payment.state,
                    "payer_id": payer_id,
                    "transactions": payment.transactions,
                    "executed_time": datetime.now().isoformat()
                }
            else:
                logger.error(f"PayPal payment execution failed: {payment.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing PayPal payment: {e}")
            return None
    
    async def get_payment_details(self, payment_id: str) -> Optional[Dict]:
        """
        Get payment details from PayPal
        
        Args:
            payment_id: Payment ID
            
        Returns:
            dict: Payment details or None
        """
        if not self.enabled:
            return None
        
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            return {
                "id": payment.id,
                "state": payment.state,
                "intent": payment.intent,
                "create_time": payment.create_time,
                "update_time": payment.update_time,
                "transactions": payment.transactions,
                "payer": payment.payer
            }
            
        except Exception as e:
            logger.error(f"Error fetching PayPal payment details: {e}")
            return None
    
    async def refund_payment(self, sale_id: str, amount: float = None, 
                           currency: str = "USD", reason: str = "Refund requested") -> Optional[Dict]:
        """
        Process refund for a PayPal payment
        
        Args:
            sale_id: Sale transaction ID
            amount: Refund amount (None for full refund)
            currency: Currency code
            reason: Reason for refund
            
        Returns:
            dict: Refund details or None
        """
        if not self.enabled:
            return None
        
        try:
            sale = paypalrestsdk.Sale.find(sale_id)
            
            refund_data = {
                "reason": reason
            }
            
            if amount:
                refund_data["amount"] = {
                    "total": str(amount),
                    "currency": currency
                }
            
            refund = sale.refund(refund_data)
            
            if refund.success():
                logger.info(f"PayPal refund processed: {refund.id} for sale {sale_id}")
                
                return {
                    "refund_id": refund.id,
                    "sale_id": sale_id,
                    "state": refund.state,
                    "amount": refund.amount,
                    "reason": reason,
                    "create_time": refund.create_time
                }
            else:
                logger.error(f"PayPal refund failed: {refund.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing PayPal refund: {e}")
            return None

# Global instance
paypal_handler = PayPalHandler()

# Convenience functions
async def create_payment(user_id: int, plan_type: str, amount: float, currency: str = "USD") -> Optional[Dict]:
    """Create PayPal payment for user"""
    return await paypal_handler.create_payment(amount, currency, user_id, plan_type)

async def execute_payment(payment_id: str, payer_id: str) -> Optional[Dict]:
    """Execute PayPal payment"""
    return await paypal_handler.execute_payment(payment_id, payer_id)

async def get_payment_details(payment_id: str) -> Optional[Dict]:
    """Get PayPal payment details"""
    return await paypal_handler.get_payment_details(payment_id)