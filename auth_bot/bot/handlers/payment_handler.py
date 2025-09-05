#!/usr/bin/env python3
import logging
import secrets
from datetime import datetime
from pyrogram import Client, filters  
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from ...database.operations import DatabaseManager
from ...database.models import Payment, PaymentStatus, PlanType
from ...utils.token_utils import TokenGenerator
from ...utils.payment_utils import RazorpayHandler, PayPalHandler
from ..config import MESSAGES, PLANS_CONFIG

logger = logging.getLogger(__name__)

# Global instances (will be injected from main)
db_manager: DatabaseManager = None
token_generator: TokenGenerator = None
razorpay_handler: RazorpayHandler = None
paypal_handler: PayPalHandler = None


async def initiate_payment(user_id: int, plan_id: str, message):
    """Initiate payment process for premium plan"""
    try:
        # Get plan details
        plans = await db_manager.get_active_plans()
        selected_plan = None
        
        for plan in plans:
            if plan.plan_id == plan_id:
                selected_plan = plan
                break
        
        if not selected_plan:
            await message.edit_text("❌ Plan not found.")
            return
        
        # Show payment gateway selection
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Razorpay (UPI/Card)", callback_data=f"pay_rzp:{plan_id}")],
            [InlineKeyboardButton("🌎 PayPal", callback_data=f"pay_pp:{plan_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="show_premium_plans")]
        ])
        
        price_display = f"₹{selected_plan.price // 100}"
        payment_text = f"💳 **Payment for {selected_plan.name}**\n\n"
        payment_text += f"**Amount:** {price_display}\n"
        payment_text += f"**Duration:** {selected_plan.duration_days} days\n\n"
        payment_text += "**Features:**\n"
        
        for feature in selected_plan.features:
            payment_text += f"• {feature}\n"
        
        payment_text += "\n**Choose Payment Method:**"
        
        await message.edit_text(payment_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Error initiating payment: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def process_razorpay_payment(user_id: int, plan_id: str, message):
    """Process Razorpay payment"""
    try:
        # Get plan details
        plans = await db_manager.get_active_plans()
        selected_plan = None
        
        for plan in plans:
            if plan.plan_id == plan_id:
                selected_plan = plan
                break
        
        if not selected_plan:
            await message.edit_text("❌ Plan not found.")
            return
        
        # Generate payment ID
        payment_id = token_generator.generate_payment_id()
        
        # Create payment record
        payment_data = Payment(
            payment_id=payment_id,
            user_id=user_id,
            plan_type=PlanType(plan_id),
            amount=selected_plan.price,
            currency="INR",
            payment_gateway="razorpay"
        )
        
        await db_manager.create_payment(payment_data)
        
        # Create Razorpay order
        if razorpay_handler:
            order_data = await razorpay_handler.create_order(
                amount=selected_plan.price,
                currency="INR",
                receipt=payment_id
            )
            
            if order_data:
                # Create payment link
                payment_link = await razorpay_handler.create_payment_link(
                    order_data["id"],
                    selected_plan.price,
                    selected_plan.name,
                    user_id
                )
                
                if payment_link:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("💳 Pay Now", url=payment_link)],
                        [InlineKeyboardButton("🔍 Check Status", callback_data=f"check_payment:{payment_id}")],
                        [InlineKeyboardButton("🔙 Back", callback_data="show_premium_plans")]
                    ])
                    
                    payment_text = MESSAGES["PAYMENT_PENDING"].format(
                        payment_id=payment_id,
                        plan_name=selected_plan.name,
                        amount=selected_plan.price // 100
                    )
                    
                    await message.edit_text(payment_text, reply_markup=keyboard)
                    return
        
        # Fallback: Manual payment instructions
        manual_payment_text = f"💳 **Manual Payment - {selected_plan.name}**\n\n"
        manual_payment_text += f"**Amount:** ₹{selected_plan.price // 100}\n"
        manual_payment_text += f"**Payment ID:** `{payment_id}`\n\n"
        manual_payment_text += "**Payment Instructions:**\n"
        manual_payment_text += "1. Make payment using any UPI app\n"
        manual_payment_text += "2. Use UPI ID: `your-upi-id@paytm`\n"
        manual_payment_text += "3. Add payment ID in remarks\n"
        manual_payment_text += "4. Send payment screenshot to admin\n\n"
        manual_payment_text += "⚠️ **Important:** Include payment ID in transaction remarks."
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/your_admin")],
            [InlineKeyboardButton("🔍 Check Status", callback_data=f"check_payment:{payment_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="show_premium_plans")]
        ])
        
        await message.edit_text(manual_payment_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Error processing Razorpay payment: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def process_paypal_payment(user_id: int, plan_id: str, message):
    """Process PayPal payment"""
    try:
        # Get plan details
        plans = await db_manager.get_active_plans()
        selected_plan = None
        
        for plan in plans:
            if plan.plan_id == plan_id:
                selected_plan = plan
                break
        
        if not selected_plan:
            await message.edit_text("❌ Plan not found.")
            return
        
        # Generate payment ID
        payment_id = token_generator.generate_payment_id()
        
        # Convert price to USD (rough conversion)
        usd_price = selected_plan.price // 8000  # 1 USD ≈ 80 INR
        
        # Create payment record
        payment_data = Payment(
            payment_id=payment_id,
            user_id=user_id,
            plan_type=PlanType(plan_id),
            amount=usd_price,
            currency="USD",
            payment_gateway="paypal"
        )
        
        await db_manager.create_payment(payment_data)
        
        # Create PayPal payment link (if handler available)
        if paypal_handler:
            payment_link = await paypal_handler.create_payment_link(
                amount=usd_price,
                currency="USD",
                description=selected_plan.name,
                return_url=f"https://your-domain.com/payment/success/{payment_id}",
                cancel_url=f"https://your-domain.com/payment/cancel/{payment_id}"
            )
            
            if payment_link:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Pay with PayPal", url=payment_link)],
                    [InlineKeyboardButton("🔍 Check Status", callback_data=f"check_payment:{payment_id}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="show_premium_plans")]
                ])
                
                payment_text = MESSAGES["PAYMENT_PENDING"].format(
                    payment_id=payment_id,
                    plan_name=selected_plan.name,
                    amount=f"${usd_price}"
                )
                
                await message.edit_text(payment_text, reply_markup=keyboard)
                return
        
        # Fallback message
        fallback_text = f"💳 **PayPal Payment - {selected_plan.name}**\n\n"
        fallback_text += f"**Amount:** ${usd_price}\n"
        fallback_text += f"**Payment ID:** `{payment_id}`\n\n"
        fallback_text += "**PayPal Email:** your-paypal@email.com\n\n"
        fallback_text += "Please send payment and contact admin with payment ID."
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/your_admin")],
            [InlineKeyboardButton("🔍 Check Status", callback_data=f"check_payment:{payment_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="show_premium_plans")]
        ])
        
        await message.edit_text(fallback_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Error processing PayPal payment: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def check_payment_status(user_id: int, payment_id: str, message):
    """Check payment status"""
    try:
        payment = await db_manager.get_payment(payment_id)
        
        if not payment:
            await message.edit_text("❌ Payment not found.")
            return
        
        if payment.user_id != user_id:
            await message.edit_text("❌ Unauthorized access.")
            return
        
        status_text = f"💳 **Payment Status**\n\n"
        status_text += f"**Payment ID:** `{payment_id}`\n"
        status_text += f"**Plan:** {payment.plan_type.value}\n"
        status_text += f"**Amount:** ₹{payment.amount // 100 if payment.currency == 'INR' else f'${payment.amount}'}\n"
        status_text += f"**Status:** {payment.status.value.title()}\n"
        status_text += f"**Created:** {payment.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if payment.completed_at:
            status_text += f"**Completed:** {payment.completed_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        keyboard_buttons = []
        
        if payment.status == PaymentStatus.COMPLETED:
            status_text += "\n✅ **Payment Successful!** Your premium subscription is active."
            keyboard_buttons.append([InlineKeyboardButton("🔑 Generate Tokens", callback_data="verify_start")])
        elif payment.status == PaymentStatus.PENDING:
            status_text += "\n⏳ **Payment Pending.** Please complete the payment."
            keyboard_buttons.append([InlineKeyboardButton("🔄 Refresh Status", callback_data=f"check_payment:{payment_id}")])
        elif payment.status == PaymentStatus.FAILED:
            status_text += "\n❌ **Payment Failed.** Please try again."
            keyboard_buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="show_premium_plans")])
        
        keyboard_buttons.append([InlineKeyboardButton("🔙 Back", callback_data="start_menu")])
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await message.edit_text(status_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Error checking payment status: {e}")
        await message.edit_text(MESSAGES["ERROR"])


async def handle_payment_success(user_id: int, payment_id: str):
    """Handle successful payment and upgrade user"""
    try:
        payment = await db_manager.get_payment(payment_id)
        if not payment:
            logger.error(f"Payment not found: {payment_id}")
            return False
        
        if payment.status != PaymentStatus.COMPLETED:
            # Update payment status
            await db_manager.update_payment_status(payment_id, PaymentStatus.COMPLETED)
        
        # Get plan details
        plan_duration_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90
        }.get(payment.plan_type.value, 7)
        
        # Upgrade user to premium
        success = await db_manager.upgrade_user_to_premium(user_id, plan_duration_days)
        
        if success:
            logger.info(f"✅ User {user_id} upgraded to premium for {plan_duration_days} days")
            return True
        else:
            logger.error(f"❌ Failed to upgrade user {user_id} to premium")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error handling payment success: {e}")
        return False


async def payment_callback(client: Client, callback_query: CallbackQuery):
    """Handle payment-related callbacks"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if data.startswith("pay_rzp:"):
            plan_id = data.split(":")[1]
            await process_razorpay_payment(user_id, plan_id, callback_query.message)
            
        elif data.startswith("pay_pp:"):
            plan_id = data.split(":")[1]
            await process_paypal_payment(user_id, plan_id, callback_query.message)
            
        elif data.startswith("check_payment:"):
            payment_id = data.split(":")[1]
            await check_payment_status(user_id, payment_id, callback_query.message)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in payment callback: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)


async def payment_success_handler(client: Client, callback_query: CallbackQuery):
    """Handle payment success notifications"""
    try:
        # This would typically be called by webhook
        # For now, it's a placeholder for manual confirmation
        pass
        
    except Exception as e:
        logger.error(f"❌ Error in payment success handler: {e}")


# Create handlers
payment_callback_handler = CallbackQueryHandler(
    payment_callback,
    filters.regex(r"^(pay_rzp:|pay_pp:|check_payment:)")
)

payment_success_handler = CallbackQueryHandler(
    payment_success_handler,
    filters.regex(r"^payment_success:")
)
