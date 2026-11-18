/**
 * Razorpay Standard Web Checkout Integration for DealOS Jobs.
 * Implements:
 * 1. POST /api/create-order (creates order via backend with minimum amount validation)
 * 2. Standard Checkout modal via https://checkout.razorpay.com/v1/checkout.js
 * 3. POST /api/verify-payment (cryptographic HMAC-SHA256 signature verification)
 */
import { API_URL } from "./api";
import { toast } from "sonner";

export interface CreateOrderResponse {
  status: string;
  order_id: string;
  amount: number;
  currency: string;
  key_id?: string;
  plan_id?: string;
  plan_name?: string;
  detail?: string;
}

export interface CheckoutOptions {
  planId: string;
  planName: string;
  amount: number; // in INR (e.g. 1 for ₹1 or 1499 for ₹1,499)
  user?: {
    name?: string;
    email?: string;
  } | null;
  onSuccess?: (planId: string, paymentId: string) => void;
  onError?: (errMessage: string) => void;
}

/**
 * Loads the official Razorpay Checkout SDK script dynamically.
 */
export function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") return resolve(false);
    if ((window as any).Razorpay) return resolve(true);

    const existingScript = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
    if (existingScript) return resolve(true);

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => {
      console.error("Failed to load Razorpay Checkout script");
      resolve(false);
    };
    document.body.appendChild(script);
  });
}

/**
 * Initiates Razorpay Standard Web Checkout flow.
 */
export async function initiateRazorpayPayment(options: CheckoutOptions): Promise<void> {
  const { planId, planName, amount, user, onSuccess, onError } = options;

  try {
    toast.loading("Creating secure Razorpay order...", { id: "razorpay-init" });

    // Calculate amount in paise: 1 INR = 100 paise (Razorpay minimum is 100 paise)
    const amountInPaise = Math.max(100, Math.round(amount * 100));

    // STEP 1: BACKEND - Call Create Order Endpoint with fallback routing
    let orderRes: Response;
    const orderPayload = JSON.stringify({
      amount: amountInPaise,
      currency: "INR",
      receipt: `rcpt_${Date.now()}_${planId}`,
      plan_id: planId,
      plan_name: planName,
      user_email: user?.email || "candidate@dealos.in",
    });

    try {
      orderRes = await fetch(`${API_URL}/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: orderPayload,
      });
    } catch {
      // Fallback to namespaced endpoint if direct route had network hiccup
      orderRes = await fetch(`${API_URL}/payments/razorpay/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: orderPayload,
      });
    }

    if (!orderRes.ok) {
      const errData = await orderRes.json().catch(() => null);
      throw new Error(errData?.detail || `Order creation failed (${orderRes.status})`);
    }

    const orderData: CreateOrderResponse = await orderRes.json();
    toast.dismiss("razorpay-init");

    // STEP 2: FRONTEND - Load Script & Launch Checkout Modal
    const isScriptLoaded = await loadRazorpayScript();
    if (!isScriptLoaded || !(window as any).Razorpay) {
      throw new Error("Unable to load Razorpay Checkout SDK. Please verify network connectivity.");
    }

    // Resolve key: Prefer frontend env variable, fallback to order key_id, fallback to active test key
    const keyId =
      process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID ||
      orderData.key_id ||
      "rzp_test_U1l0CosFGKivd3";

    const razorpayOptions = {
      key: keyId,
      amount: orderData.amount,
      currency: orderData.currency,
      name: "DealOS Jobs",
      description: planName,
      order_id: orderData.order_id,
      image: "https://jobs.dealos.in/favicon.ico",
      prefill: {
        name: user?.name || "Executive Candidate",
        email: user?.email || "candidate@dealos.in",
        contact: "9876543210",
      },
      theme: {
        color: "#2563eb", // DealOS Blue
      },
      // Display blocks for Standard Checkout v1 & v2 to force UPI collect (manual VPA entry)
      display: {
        blocks: {
          upi_block: {
            name: "Pay using UPI / QR / UPI ID",
            instruments: [
              {
                method: "upi",
                flows: ["collect", "qr"], // Explicitly enables the manual "Enter UPI ID" text field
              },
            ],
          },
        },
        sequence: ["block.upi_block"],
        preferences: {
          show_default_blocks: true,
        },
      },
      config: {
        display: {
          blocks: {
            upi_block: {
              name: "Pay using UPI / QR / UPI ID",
              instruments: [
                {
                  method: "upi",
                  flows: ["collect", "qr"], // Explicitly enables the manual "Enter UPI ID" text field
                },
              ],
            },
          },
          sequence: ["block.upi_block"],
          preferences: {
            show_default_blocks: true,
          },
        },
      },
      // On Success: Receive razorpay_payment_id, razorpay_order_id, razorpay_signature
      handler: async function (response: {
        razorpay_payment_id: string;
        razorpay_order_id: string;
        razorpay_signature: string;
      }) {
        try {
          toast.loading("Verifying transaction authenticity with Razorpay...", { id: "verify-tx" });

          // STEP 3: BACKEND - Call Verify Signature Endpoint with fallback
          const verifyPayload = JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
            plan_id: planId,
            user_email: user?.email,
          });

          let verifyRes: Response;
          try {
            verifyRes = await fetch(`${API_URL}/verify-payment`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: verifyPayload,
            });
          } catch {
            verifyRes = await fetch(`${API_URL}/payments/razorpay/verify`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: verifyPayload,
            });
          }

          toast.dismiss("verify-tx");

          if (!verifyRes.ok) {
            const verifyErr = await verifyRes.json().catch(() => null);
            throw new Error(verifyErr?.detail || "Payment signature verification failed.");
          }

          toast.success(`🎉 Payment verified successfully! Welcome to ${planName}.`);
          if (onSuccess) onSuccess(planId, response.razorpay_payment_id);
        } catch (err: any) {
          toast.dismiss("verify-tx");
          toast.error(err.message || "Failed to verify transaction signature.");
          if (onError) onError(err.message);
        }
      },
      modal: {
        ondismiss: function () {
          toast.info("Payment window closed. Transaction was not completed.");
        },
      },
    };

    const rzpInstance = new (window as any).Razorpay(razorpayOptions);

    // Handle payment.failed event
    rzpInstance.on("payment.failed", function (failResponse: any) {
      const errorReason = failResponse?.error?.description || "Transaction declined by issuing bank.";
      toast.error(`Payment failed: ${errorReason}`);
      if (onError) onError(errorReason);
    });

    rzpInstance.open();
  } catch (err: any) {
    toast.dismiss("razorpay-init");
    toast.error(err.message || "Payment initiation failed.");
    if (onError) onError(err.message);
  }
}
