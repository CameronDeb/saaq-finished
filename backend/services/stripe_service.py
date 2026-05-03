"""
Stripe Service — handles checkout sessions, webhooks, and price management.
"""
import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def get_prices_from_db(supabase):
    """Get current prices from admin_settings table."""
    result = supabase.table("admin_settings").select("*").like("key", "price_%").execute()
    prices = {}
    for row in result.data:
        prices[row["key"]] = row["value"]
    return prices


def update_price(supabase, key: str, amount: int, label: str):
    """Update a price in admin_settings."""
    supabase.table("admin_settings").upsert({
        "key": key,
        "value": {"amount": amount, "label": label}
    }).execute()


def create_checkout_session(
    supabase,
    product_type: str,
    user_id: str,
    user_email: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """Create a Stripe checkout session for a report purchase."""
    prices = get_prices_from_db(supabase)
    price_key = f"price_{product_type}"
    
    if price_key not in prices:
        raise ValueError(f"Unknown product type: {product_type}")
    
    price_info = prices[price_key]
    amount_cents = price_info["amount"] * 100  # Convert dollars to cents
    label = price_info["label"]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=user_email,
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"SAAQ {label}"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        metadata={
            "user_id": user_id,
            "product_type": product_type,
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # Record payment in DB
    supabase.table("payments").insert({
        "user_id": user_id,
        "stripe_session_id": session.id,
        "product_type": product_type,
        "amount": price_info["amount"],
        "status": "pending",
    }).execute()

    return {"checkout_url": session.url, "session_id": session.id}


def handle_webhook(supabase, payload: bytes, sig_header: str) -> dict:
    """Handle Stripe webhook events."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")
    else:
        import json
        event = json.loads(payload)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]
        payment_intent = session.get("payment_intent")
        
        # Update payment status
        supabase.table("payments").update({
            "status": "completed",
            "stripe_payment_intent": payment_intent,
        }).eq("stripe_session_id", session_id).execute()

        return {"status": "completed", "session_id": session_id}
    
    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        supabase.table("payments").update({
            "status": "failed",
        }).eq("stripe_session_id", session["id"]).execute()

    return {"status": "received"}


def get_payment_by_session(supabase, session_id: str) -> dict | None:
    """Get payment record by Stripe session ID."""
    result = supabase.table("payments").select("*").eq("stripe_session_id", session_id).execute()
    return result.data[0] if result.data else None


def get_user_payments(supabase, user_id: str) -> list:
    """Get all payments for a user."""
    result = supabase.table("payments").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


def get_all_payments(supabase) -> list:
    """Get all payments (admin)."""
    result = supabase.table("payments").select("*").order("created_at", desc=True).execute()
    return result.data
