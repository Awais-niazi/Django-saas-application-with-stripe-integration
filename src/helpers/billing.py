import stripe
from decouple import config


DJANGO_DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="", cast=str)

if STRIPE_SECRET_KEY and "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Using test Stripe secret key in production is not allowed.")

stripe.api_key = STRIPE_SECRET_KEY or None


def stripe_is_configured():
    return bool(STRIPE_SECRET_KEY)


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
