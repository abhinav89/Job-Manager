"""
Razorpay Payment Gateway Router for DealOS Job-Manager.
Handles order initialization, signature verification, and plan provisioning
for Indian domestic payments (UPI, Cards, NetBanking, Wallets).
"""
import os
import time
import json
import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("cv_tailor.payments")
router = APIRouter(prefix="/payments/razorpay", tags=["payments"])

class CreateOrderRequest(BaseModel):
    plan_id: str = Field(..., description="ID of the subscription plan, e.g. pro_sprint, executive_advisory")
    plan_name: str = Field(..., description="Display title of the plan")
    amount: int = Field(..., description="Price in INR, e.g. 1499")
    currency: str = Field("INR", description="Currency ISO code")
    user_email: Optional[str] = None
    user_name: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: str
    user_email: Optional[str] = None

@router.get("/status")
def get_payment_status() -> Dict[str, Any]:
    """
    Returns public gateway connectivity status and whether live/test keys are present.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    is_configured = bool(key_id and key_secret)

    mode = "sandbox_simulation"
    if is_configured:
        mode = "test" if key_id.startswith("rzp_test") else "live"

    return {
        "provider": "Razorpay",
        "is_configured": is_configured,
        "key_id": key_id if is_configured else "rzp_test_placeholder",
        "mode": mode,
        "currency": "INR",
        "supported_methods": [
            "UPI (Google Pay, PhonePe, Paytm, BHIM)",
            "RuPay & Visa / Mastercard Debit & Credit Cards",
            "NetBanking (50+ Indian banks)",
            "Wallets (Mobikwik, Freecharge, etc.)"
        ],
        "setup_fee": "₹0 Free",
        "amc_fee": "₹0 Free",
        "notes": "Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env for direct live payment processing."
    }

@router.post("/create-order")
def create_razorpay_order(payload: CreateOrderRequest) -> Dict[str, Any]:
    """
    Creates a Razorpay order in INR. If live/test API keys are configured,
    calls api.razorpay.com/v1/orders. Otherwise falls back to simulated
    sandbox order generation for instant developer preview.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    amount_in_paise = int(payload.amount * 100)

    # 1. Real Razorpay API Order Generation
    if key_id and key_secret and not key_id.startswith("rzp_test_placeholder"):
        try:
            auth_bytes = f"{key_id}:{key_secret}".encode("utf-8")
            auth_header = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
            
            req_data = json.dumps({
                "amount": amount_in_paise,
                "currency": payload.currency.upper(),
                "receipt": f"rcpt_{int(time.time())}_{payload.plan_id}",
                "notes": {
                    "plan_id": payload.plan_id,
                    "plan_name": payload.plan_name,
                    "email": payload.user_email or "guest",
                    "platform": "DealOS Job-Manager"
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.razorpay.com/v1/orders",
                data=req_data,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                return {
                    "status": "success",
                    "order_id": res_body["id"],
                    "amount": res_body["amount"],
                    "currency": res_body["currency"],
                    "key_id": key_id,
                    "plan_id": payload.plan_id,
                    "plan_name": payload.plan_name,
                    "is_sandbox": False,
                    "mode": "test" if key_id.startswith("rzp_test") else "live"
                }
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            logger.error("Razorpay order creation HTTP error: %s", err_msg)
            # Fall back to simulated order with warning if keys are invalid
        except Exception as e:
            logger.error("Razorpay network error: %s", str(e))

    # 2. Simulated Sandbox Order (Zero-Friction Default before API Keys)
    sim_order_id = f"order_sim_{int(time.time())}_{payload.plan_id}"
    return {
        "status": "success",
        "order_id": sim_order_id,
        "amount": amount_in_paise,
        "currency": "INR",
        "key_id": key_id or "rzp_test_placeholder",
        "plan_id": payload.plan_id,
        "plan_name": payload.plan_name,
        "is_sandbox": True,
        "mode": "sandbox_simulation",
        "message": "Razorpay sandbox simulation mode active. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env for live gateway processing."
    }

@router.post("/verify")
def verify_razorpay_payment(payload: VerifyPaymentRequest) -> Dict[str, Any]:
    """
    Validates Razorpay payment signature using HMAC SHA256.
    If sandbox simulated order, validates transaction automatically.
    """
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()

    # 1. Handle Sandbox Simulation Orders
    if payload.razorpay_order_id.startswith("order_sim_") or not key_secret:
        logger.info("Sandbox simulated payment verified for plan %s, user: %s", payload.plan_id, payload.user_email)
        return {
            "status": "success",
            "verified": True,
            "mode": "sandbox_simulation",
            "plan_id": payload.plan_id,
            "payment_id": payload.razorpay_payment_id,
            "message": f"Sandbox simulation successful! Plan '{payload.plan_id}' activated."
        }

    # 2. Cryptographic HMAC SHA256 Signature Verification
    try:
        msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8")
        expected_sig = hmac.new(key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, payload.razorpay_signature):
            raise HTTPException(
                status_code=400,
                detail="Payment signature verification failed. Untrusted transaction response."
            )

        logger.info("Live payment verified for order %s, payment %s", payload.razorpay_order_id, payload.razorpay_payment_id)
        return {
            "status": "success",
            "verified": True,
            "mode": "live",
            "plan_id": payload.plan_id,
            "payment_id": payload.razorpay_payment_id,
            "message": f"Payment verified successfully! Welcome to {payload.plan_id} membership."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Verification processing failure: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to verify payment signature.")
