import stripe
from decouple import config

DJANGO_DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default=None, cast=str) 

if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Using test Stripe secret key in production is not allowed.")

stripe.api_key = STRIPE_SECRET_KEY

def create_customer(
        name="",
        email="",
        metadata={},
        raw=False):
    response = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata,
    )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id    

def create_price(
        currency="usd",
        unit_amount="999",
        interval = "month",
        recurring={"interval": "month"},
        product=None,
        metadata={},
        raw=False):
    if product is None:
        return None
    response = stripe.Price.create(
                currency=currency,
                unit_amount=unit_amount,
                recurring={"interval": interval},
                product=product,
                metadata=metadata,
            )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id
