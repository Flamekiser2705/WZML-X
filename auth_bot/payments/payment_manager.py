#!/usr/bin/env python3
"""
Payment Manager
Coordinates payment processing between different payment providers
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentProvider(Enum):
    RAZORPAY = "razorpay"
    PAYPAL = "paypal"

class PlanType(Enum):
    PREMIUM_7D = "7d"
    PREMIUM_30D = "30d"
    PREMIUM_90D = "90d"

class PaymentManager:
    """Manages payment processing across multiple providers"""
    
    def __init__(self):
        self.providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available payment providers"""
        try:
            from .razorpay_handler import razorpay_handler
            if razorpay_handler.is_enabled():
                self.providers[PaymentProvider.RAZORPAY] = razorpay_handler
                logger.info("✅ Razorpay provider enabled")
        except ImportError:
            logger.warning("⚠️ Razorpay not available (missing razorpay package)")
        
        try:
            from .paypal_handler import paypal_handler
            if paypal_handler.is_enabled():
                self.providers[PaymentProvider.PAYPAL] = paypal_handler
                logger.info("✅ PayPal provider enabled")
        except ImportError:
            logger.warning("⚠️ PayPal not available (missing paypalrestsdk package)")
    
    def get_enabled_providers(self) -> List[PaymentProvider]:
        """Get list of enabled payment providers"""
        return list(self.providers.keys())
    
    def is_provider_enabled(self, provider: PaymentProvider) -> bool:
        """Check if specific provider is enabled"""
        return provider in self.providers
    
    async def create_payment(self, provider: PaymentProvider, user_id: int, 
                           plan_type: str, amount: float, currency: str = "INR") -> Optional[Dict]:
        """
        Create payment order/request
        
        Args:
            provider: Payment provider to use
            user_id: Telegram user ID
            plan_type: Plan type (7d, 30d, 90d)
            amount: Amount in currency units
            currency: Currency code
            
        Returns:
            dict: Payment creation result or None
        """
        if provider not in self.providers:
            logger.error(f"Provider {provider.value} not enabled")
            return None
        
        handler = self.providers[provider]
        
        if provider == PaymentProvider.RAZORPAY:
            # Razorpay expects amount in paise for INR
            amount_paise = int(amount * 100) if currency == "INR" else int(amount)
            return await handler.create_payment_order(amount_paise, currency, user_id, plan_type)
        
        elif provider == PaymentProvider.PAYPAL:
            return await handler.create_payment(amount, currency, user_id, plan_type)
        
        return None
    
    async def verify_payment(self, provider: PaymentProvider, **kwargs) -> bool:
        """
        Verify payment completion
        
        Args:
            provider: Payment provider
            **kwargs: Provider-specific verification parameters
            
        Returns:
            bool: True if payment verified
        """
        if provider not in self.providers:
            return False
        
        handler = self.providers[provider]
        
        if provider == PaymentProvider.RAZORPAY:
            return await handler.verify_payment(
                kwargs.get('payment_id'),
                kwargs.get('order_id'),
                kwargs.get('signature')
            )
        
        elif provider == PaymentProvider.PAYPAL:
            result = await handler.execute_payment(
                kwargs.get('payment_id'),
                kwargs.get('payer_id')
            )
            return result is not None and result.get('state') == 'approved'
        
        return False
    
    def get_plan_details(self, plan_type: str) -> Dict[str, Any]:
        """
        Get plan pricing and details
        
        Args:
            plan_type: Plan type (7d, 30d, 90d)
            
        Returns:
            dict: Plan details
        """
        plans = {
            "7d": {
                "name": "Premium 7 Days",
                "duration_days": 7,
                "price_inr": 5.0,
                "price_usd": 0.06,
                "features": [
                    "No shortener verification",
                    "Instant token generation",
                    "Up to 4 active tokens",
                    "Priority support",
                    "No ads"
                ]
            },
            "30d": {
                "name": "Premium 30 Days",
                "duration_days": 30,
                "price_inr": 20.0,
                "price_usd": 0.24,
                "features": [
                    "No shortener verification",
                    "Instant token generation",
                    "Up to 4 active tokens",
                    "Priority support",
                    "No ads",
                    "Extended validity"
                ]
            },
            "90d": {
                "name": "Premium 90 Days",
                "duration_days": 90,
                "price_inr": 50.0,
                "price_usd": 0.60,
                "features": [
                    "No shortener verification",
                    "Instant token generation",
                    "Up to 4 active tokens",
                    "Priority support",
                    "No ads",
                    "Best value plan"
                ]
            }
        }
        
        return plans.get(plan_type, {})
    
    def get_payment_buttons(self, plan_type: str) -> List[Dict[str, str]]:
        """
        Get payment buttons for a plan
        
        Args:
            plan_type: Plan type
            
        Returns:
            list: Button configurations
        """
        buttons = []
        
        if PaymentProvider.RAZORPAY in self.providers:
            buttons.append({
                "text": "💳 Pay with UPI/Card (₹)",
                "callback_data": f"pay_razorpay_{plan_type}"
            })
        
        if PaymentProvider.PAYPAL in self.providers:
            buttons.append({
                "text": "💰 Pay with PayPal ($)",
                "callback_data": f"pay_paypal_{plan_type}"
            })
        
        return buttons

# Global instance
payment_manager = PaymentManager()

# Convenience functions
async def create_payment(provider_name: str, user_id: int, plan_type: str) -> Optional[Dict]:
    """Create payment for user"""
    try:
        provider = PaymentProvider(provider_name)
        plan_details = payment_manager.get_plan_details(plan_type)
        
        if not plan_details:
            return None
        
        # Use appropriate currency based on provider
        if provider == PaymentProvider.RAZORPAY:
            amount = plan_details["price_inr"]
            currency = "INR"
        else:
            amount = plan_details["price_usd"]
            currency = "USD"
        
        return await payment_manager.create_payment(provider, user_id, plan_type, amount, currency)
        
    except ValueError:
        logger.error(f"Invalid payment provider: {provider_name}")
        return None

async def verify_payment(provider_name: str, **kwargs) -> bool:
    """Verify payment completion"""
    try:
        provider = PaymentProvider(provider_name)
        return await payment_manager.verify_payment(provider, **kwargs)
    except ValueError:
        return False

def get_plan_details(plan_type: str) -> Dict[str, Any]:
    """Get plan details"""
    return payment_manager.get_plan_details(plan_type)

def get_payment_buttons(plan_type: str) -> List[Dict[str, str]]:
    """Get payment buttons for plan"""
    return payment_manager.get_payment_buttons(plan_type)