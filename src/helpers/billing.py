import stripe
from decouple import config
import logging


logger = logging.getLogger(__name__)

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

def create_product(
    name="",
    metadata={},
    raw=False):
    response = stripe.Product.create(
        name=name,
        metadata=metadata,
    )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id

def create_price(
    currency="usd",
    unit_amount="999",
    interval="month",
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

def start_checkout_session(
    customer_id, 
    success_url="", 
    cancel_url="", 
    price_stripe_id="", 
    existing_subscription_id=None,  # ✅ NEW PARAMETER
    raw=True):
    """
    Create a Stripe checkout session.
    """
    # Fix the URL to include session_id
    if "{CHECKOUT_SESSION_ID}" not in success_url:
        separator = "&" if "?" in success_url else "?"
        success_url = f"{success_url}{separator}session_id={{CHECKOUT_SESSION_ID}}"
    
    # Build parameters
    session_params = {
        'customer': customer_id,
        'cancel_url': cancel_url,
        'success_url': success_url,
        'line_items': [{"price": price_stripe_id, "quantity": 1}],
        'mode': 'subscription',
    }
    
    # Add metadata if upgrading
    if existing_subscription_id:
        session_params['subscription_data'] = {
            'metadata': {
                'previous_subscription': existing_subscription_id
            }
        }
    
    response = stripe.checkout.Session.create(**session_params)
    
    if raw:
        return response
    return response.url

def get_checkout_session(session_id, raw=True):
    response = stripe.checkout.Session.retrieve(session_id)
    if raw:
        return response
    return response.url

def get_subscription(stripe_id, raw=True):
    response = stripe.Subscription.retrieve(stripe_id)
    if raw:
        return response
    return response.id

def get_checkout_customer_plan(session_id):
    checkout_r = get_checkout_session(session_id, raw=True)
    customer_id = checkout_r.customer
    sub_stripe_id = checkout_r.subscription
    sub_r = get_subscription(sub_stripe_id, raw=True)
    sub_plan = sub_r.plan
    return customer_id, sub_plan.id, sub_stripe_id

def cancel_subscription(subscription_id, cancel_at_period_end=False, raw=False):
    """
    Cancel a Stripe subscription
    """
    try:
        if cancel_at_period_end:
            response = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            response = stripe.Subscription.delete(subscription_id)
        
        if raw:
            return response
        return response.status
    except stripe.error.InvalidRequestError as e:
        print(f"Error cancelling subscription {subscription_id}: {e}")
        if raw:
            return None
        return "already_cancelled"
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        raise

def get_subscription_status(subscription_id):
    """Get subscription status"""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription.status
    except stripe.error.StripeError as e:
        print(f"Error retrieving subscription: {e}")
        return None
    

def cancel_subscription(subscription_id, cancel_at_period_end=False, raw=False):
    """Cancel a Stripe subscription"""
    try:
        logger.info(f"Attempting to cancel subscription: {subscription_id}")
        
        if cancel_at_period_end:
            response = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Subscription {subscription_id} will cancel at period end")
        else:
            response = stripe.Subscription.delete(subscription_id)
            logger.info(f"Subscription {subscription_id} cancelled immediately")
        
        if raw:
            return response
        return response.status
        
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"Subscription {subscription_id} already cancelled or doesn't exist: {e}")
        if raw:
            return None
        return "already_cancelled"
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error cancelling {subscription_id}: {e}", exc_info=True)
        raise

def get_checkout_customer_plan(session_id):
    """Extract customer and plan info from checkout session"""
    try:
        logger.debug(f"Retrieving checkout session: {session_id}")
        checkout_r = get_checkout_session(session_id, raw=True)
        customer_id = checkout_r.customer
        sub_stripe_id = checkout_r.subscription
        sub_r = get_subscription(sub_stripe_id, raw=True)
        sub_plan = sub_r.plan
        
        logger.debug(
            f"Session {session_id}: customer={customer_id}, "
            f"subscription={sub_stripe_id}, plan={sub_plan.id}"
        )
        
        return customer_id, sub_plan.id, sub_stripe_id
        
    except Exception as e:
        logger.error(f"Error retrieving checkout session {session_id}: {e}", exc_info=True)
        raise    