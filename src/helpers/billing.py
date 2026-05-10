import stripe
from decouple import config


DJANGO_DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="", cast=str)
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="", cast=str)
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="", cast=str)

if STRIPE_SECRET_KEY and "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Using test Stripe secret key in production is not allowed.")

stripe.api_key = STRIPE_SECRET_KEY or None


def stripe_is_configured():
    return bool(STRIPE_SECRET_KEY)


def billing_portal_is_configured():
    return stripe_is_configured()


def webhook_is_configured():
    return bool(STRIPE_WEBHOOK_SECRET)


def create_customer(name="", email="", metadata=None, raw=False):
    if not stripe_is_configured():
        return None

    response = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata or {},
    )
    if raw:
        return response
    return response.id


def retrieve_customer(customer_id, raw=False):
    if not stripe_is_configured() or not customer_id:
        return None

    response = stripe.Customer.retrieve(customer_id)
    if raw:
        return response
    return response.id


def create_product(name="", metadata=None, raw=False):
    if not stripe_is_configured():
        return None

    response = stripe.Product.create(
        name=name,
        metadata=metadata or {},
    )
    if raw:
        return response
    return response.id


def create_price(
    currency="usd",
    unit_amount=999,
    interval="month",
    recurring=None,
    product=None,
    metadata=None,
    raw=False,
):
    if not stripe_is_configured() or product is None:
        return None

    response = stripe.Price.create(
        currency=currency,
        unit_amount=unit_amount,
        recurring=recurring or {"interval": interval},
        product=product,
        metadata=metadata or {},
    )
    if raw:
        return response
    return response.id


def create_checkout_session(
    *,
    customer_id,
    price_id,
    success_url,
    cancel_url,
    metadata=None,
    client_reference_id="",
    raw=False,
):
    if not stripe_is_configured() or not customer_id or not price_id:
        return None

    response = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata or {},
        client_reference_id=client_reference_id or None,
        allow_promotion_codes=True,
        billing_address_collection="auto",
        customer_update={"name": "auto", "address": "auto"},
    )
    if raw:
        return response
    return response.url


def create_billing_portal_session(*, customer_id, return_url, raw=False):
    if not billing_portal_is_configured() or not customer_id:
        return None

    response = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    if raw:
        return response
    return response.url


def construct_webhook_event(payload, signature):
    if not stripe_is_configured() or not STRIPE_WEBHOOK_SECRET:
        raise ValueError("Stripe webhook secret is not configured.")

    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=STRIPE_WEBHOOK_SECRET,
    )
