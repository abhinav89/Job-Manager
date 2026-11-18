"""
Razorpay Standard Web Checkout Router for DealOS Jobs.
Implements:
1. POST /create-order (and /payments/razorpay/create-order)
2. POST /verify-payment (and /payments/razorpay/verify)
3. GET /payments/razorpay/status

Supports official 'razorpay' Python SDK with HMAC-SHA256 signature verification.
"""
import os
import time
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    import razorpay
    from razorpay.errors import BadRequestError, SignatureVerificationError
    HAS_RAZORPAY_SDK = True
except ImportError:
    HAS_RAZORPAY_SDK = False

logger = logging.getLogger("cv_tailor.payments")

# Router mounted at both root api (/api) and /api/payments/razorpay
router = APIRouter(tags=["payments"])

DEFAULT_KEY_ID = "rzp_test_U1l0CosFGKivd3"
DEFAULT_KEY_SECRET = "4VK2Hd5o3VxVIHC0nYIS7je8"

def get_razorpay_credentials():
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip() or DEFAULT_KEY_ID
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip() or DEFAULT_KEY_SECRET
    return key_id, key_secret

def get_razorpay_client():
    key_id, key_secret = get_razorpay_credentials()
    if not key_id or not key_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Razorpay API credentials not configured in environment."
        )
    if not HAS_RAZORPAY_SDK:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay Python SDK not installed."
        )
    return razorpay.Client(auth=(key_id, key_secret))

# Request Models
class StandardCreateOrderRequest(BaseModel):
    amount: int = Field(..., description="Amount in paise (minimum 100 paise = ₹1.00) or INR depending on context")
    currency: str = Field("INR", description="Currency code (e.g. INR)")
    receipt: Optional[str] = Field(None, description="Unique receipt identifier")
    notes: Optional[Dict[str, Any]] = None
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    user_email: Optional[str] = None

class StandardVerifyPaymentRequest(BaseModel):
    razorpay_order_id: str = Field(..., description="Order ID returned by Razorpay")
    razorpay_payment_id: str = Field(..., description="Payment ID returned by Razorpay Checkout")
    razorpay_signature: str = Field(..., description="Cryptographic signature returned by Razorpay Checkout")
    plan_id: Optional[str] = None
    user_email: Optional[str] = None

# ─────────────────────────────────────────────────────────────────
# STEP 1: CREATE ORDER ENDPOINTS
# ─────────────────────────────────────────────────────────────────

def execute_create_order(payload: StandardCreateOrderRequest) -> Dict[str, Any]:
    key_id, key_secret = get_razorpay_credentials()
    
    # Standard check: if amount is given in Rupees (e.g. 1499), convert to paise (149900).
    # If already in paise (>= 10000 for ₹100), handle appropriately.
    # The requirement specifies: "Minimum amount: 100 paise".
    amount_in_paise = payload.amount
    # If passed in Rupees (e.g. ₹1 for test or ₹1499):
    if amount_in_paise == 1:
        amount_in_paise = 100  # 100 paise = ₹1.00
    elif amount_in_paise < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum amount is 100 paise (₹1.00)."
        )
    elif payload.plan_id in ["pro_sprint", "pro"] and amount_in_paise == 1499:
        amount_in_paise = 1499 * 100
    elif payload.plan_id in ["executive_advisory", "executive"] and amount_in_paise == 7999:
        amount_in_paise = 7999 * 100

    receipt_id = payload.receipt or f"rcpt_{int(time.time())}_{payload.plan_id or 'std'}"

    notes_dict = payload.notes or {}
    if payload.plan_id:
        notes_dict["plan_id"] = payload.plan_id
    if payload.plan_name:
        notes_dict["plan_name"] = payload.plan_name
    if payload.user_email:
        notes_dict["user_email"] = payload.user_email
    notes_dict["platform"] = "DealOS Jobs"

    client = get_razorpay_client()
    try:
        order_data = {
            "amount": amount_in_paise,
            "currency": payload.currency.upper(),
            "receipt": receipt_id,
            "notes": notes_dict,
        }
        order = client.order.create(data=order_data)

        logger.info("Created Razorpay Order %s for amount %s paise", order["id"], amount_in_paise)
        return {
            "status": "success",
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": key_id,
            "plan_id": payload.plan_id,
            "plan_name": payload.plan_name,
        }
    except BadRequestError as e:
        logger.error("Razorpay BadRequestError: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Razorpay API error creating order: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Razorpay order: {str(e)}"
        )

@router.post("/create-order")
def create_order_standard(payload: StandardCreateOrderRequest):
    """
    Standard Razorpay endpoint: POST /api/create-order
    """
    return execute_create_order(payload)

@router.post("/payments/razorpay/create-order")
def create_order_namespaced(payload: StandardCreateOrderRequest):
    """
    Namespaced compatibility endpoint: POST /api/payments/razorpay/create-order
    """
    return execute_create_order(payload)

# ─────────────────────────────────────────────────────────────────
# STEP 2 & 3: VERIFY PAYMENT SIGNATURE ENDPOINTS
# ─────────────────────────────────────────────────────────────────

def execute_verify_payment(payload: StandardVerifyPaymentRequest) -> Dict[str, Any]:
    key_id, key_secret = get_razorpay_credentials()

    # Validate required fields
    if not payload.razorpay_order_id or not payload.razorpay_payment_id or not payload.razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: razorpay_order_id, razorpay_payment_id, and razorpay_signature are all mandatory."
        )

    # Cryptographic HMAC-SHA256 Verification:
    # Algorithm: HMAC-SHA256(order_id + "|" + payment_id, KEY_SECRET)
    message = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8")
    generated_signature = hmac.new(
        key_secret.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()

    # Safe constant-time comparison
    if not hmac.compare_digest(generated_signature, payload.razorpay_signature):
        logger.warning(
            "Razorpay signature mismatch for order: %s, payment: %s",
            payload.razorpay_order_id,
            payload.razorpay_payment_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature verification failed. Untrusted payment response."
        )

    logger.info("Payment signature verified successfully for order: %s", payload.razorpay_order_id)
    return {
        "status": "success",
        "verified": True,
        "order_id": payload.razorpay_order_id,
        "payment_id": payload.razorpay_payment_id,
        "plan_id": payload.plan_id,
        "message": "Payment verified successfully. Subscription activated."
    }

@router.post("/verify-payment")
def verify_payment_standard(payload: StandardVerifyPaymentRequest):
    """
    Standard Razorpay endpoint: POST /api/verify-payment
    """
    return execute_verify_payment(payload)

@router.post("/payments/razorpay/verify")
def verify_payment_namespaced(payload: StandardVerifyPaymentRequest):
    """
    Namespaced compatibility endpoint: POST /api/payments/razorpay/verify
    """
    return execute_verify_payment(payload)

# ─────────────────────────────────────────────────────────────────
# GATEWAY STATUS & CONFIGURATION
# ─────────────────────────────────────────────────────────────────

@router.get("/payments/razorpay/status")
def get_payment_status() -> Dict[str, Any]:
    key_id, key_secret = get_razorpay_credentials()
    is_configured = bool(key_id and key_secret)
    mode = "test" if key_id.startswith("rzp_test") else ("live" if key_id else "unconfigured")

    return {
        "provider": "Razorpay",
        "is_configured": is_configured,
        "key_id": key_id,
        "mode": mode,
        "currency": "INR",
        "sdk_installed": HAS_RAZORPAY_SDK,
        "supported_methods": [
            "UPI (Google Pay, PhonePe, Paytm, BHIM)",
            "RuPay & Visa / Mastercard Debit & Credit Cards",
            "NetBanking (50+ Indian banks)",
            "Wallets (Mobikwik, Freecharge)"
        ]
    }
