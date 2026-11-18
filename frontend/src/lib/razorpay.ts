/**
 * Razorpay Payment Gateway Client Integration for DealOS Job-Manager.
 * Supports domestic Indian UPI (Google Pay, PhonePe, Paytm, BHIM),
 * NetBanking, RuPay & International Debit/Credit cards.
 */
import { API_URL } from "./api";
import { toast } from "sonner";

export interface CreateOrderResponse {
  status: string;
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  plan_id: string;
  plan_name: string;
  is_sandbox?: boolean;
  mode: string;
  message?: string;
}

export interface CheckoutOptions {
  planId: string;
  planName: string;
  amount: number; // in INR, e.g. 1499
  user?: {
    name?: string;
    email?: string;
  } | null;
  onSuccess?: (planId: string, paymentId: string) => void;
  onError?: (errMessage: string) => void;
}

/**
 * Loads the official Razorpay Checkout SDK dynamically.
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
      console.error("Failed to load Razorpay SDK");
      resolve(false);
    };
    document.body.appendChild(script);
  });
}

/**
 * Initiates Razorpay payment order and launches the standard checkout modal.
 */
export async function initiateRazorpayPayment(options: CheckoutOptions): Promise<void> {
  const { planId, planName, amount, user, onSuccess, onError } = options;

  try {
    toast.loading("Initializing secure Razorpay payment...", { id: "razorpay-init" });

    // 1. Create order on backend
    const orderRes = await fetch(`${API_URL}/payments/razorpay/create-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan_id: planId,
        plan_name: planName,
        amount: amount,
        currency: "INR",
        user_email: user?.email || "guest@dealos.in",
        user_name: user?.name || "Candidate",
      }),
    });

    if (!orderRes.ok) {
      throw new Error("Unable to create payment order. Please try again.");
    }

    const orderData: CreateOrderResponse = await orderRes.json();
    toast.dismiss("razorpay-init");

    // 2. Handle Sandbox Simulation Mode (when real API keys are not yet input in .env)
    if (orderData.is_sandbox || !orderData.key_id || orderData.key_id === "rzp_test_placeholder") {
      toast.info("Sandbox Simulation: Processing test payment verification...", {
        duration: 3000,
      });

      // Verify simulated transaction
      const verifyRes = await fetch(`${API_URL}/payments/razorpay/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          razorpay_order_id: orderData.order_id,
          razorpay_payment_id: `pay_sim_${Date.now()}`,
          razorpay_signature: "sandbox_simulated_signature",
          plan_id: planId,
          user_email: user?.email || "guest@dealos.in",
        }),
      });

      if (!verifyRes.ok) {
        throw new Error("Sandbox payment verification failed.");
      }

      toast.success(`🎉 Subscription to ${planName} activated (Sandbox Mode)!`);
      if (onSuccess) onSuccess(planId, `pay_sim_${Date.now()}`);
      return;
    }

    // 3. Live / Test Mode with Razorpay SDK
    const isScriptLoaded = await loadRazorpayScript();
    if (!isScriptLoaded || !(window as any).Razorpay) {
      throw new Error("Razorpay Checkout SDK could not be loaded. Check your internet connection.");
    }

    const razorpayOptions = {
      key: orderData.key_id,
      amount: orderData.amount,
      currency: orderData.currency,
      name: "DealOS Job-Manager",
      description: planName,
      order_id: orderData.order_id,
      image: "https://jobs.dealos.in/favicon.ico",
      prefill: {
        name: user?.name || "",
        email: user?.email || "",
      },
      theme: {
        color: "#2563eb", // DealOS Blue
      },
      handler: async function (response: any) {
        try {
          toast.loading("Verifying transaction authenticity...", { id: "verify-tx" });

          const verifyRes = await fetch(`${API_URL}/payments/razorpay/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              plan_id: planId,
              user_email: user?.email,
            }),
          });

          toast.dismiss("verify-tx");

          if (!verifyRes.ok) {
            throw new Error("Payment signature verification failed. Please contact support.");
          }

          toast.success(`🎉 Payment verified! Welcome to ${planName}.`);
          if (onSuccess) onSuccess(planId, response.razorpay_payment_id);
        } catch (err: any) {
          toast.error(err.message || "Failed to verify transaction signature.");
          if (onError) onError(err.message);
        }
      },
      modal: {
        ondismiss: function () {
          toast.info("Payment window dismissed.");
        },
      },
    };

    const rzpInstance = new (window as any).Razorpay(razorpayOptions);
    rzpInstance.on("payment.failed", function (failResponse: any) {
      toast.error(`Payment failed: ${failResponse?.error?.description || "Transaction declined."}`);
      if (onError) onError(failResponse?.error?.description);
    });
    rzpInstance.open();
  } catch (err: any) {
    toast.dismiss("razorpay-init");
    toast.error(err.message || "Payment initiation failed.");
    if (onError) onError(err.message);
  }
}
