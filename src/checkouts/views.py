# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from subscriptions.models import SubscriptionsPrice, Subscription, UserSubscription
import helpers.billing
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest

User = get_user_model()
BASE_URL = settings.BASE_URL

def product_price_redirect_view(request, price_id=None, *args, **kwargs):
    request.session['checkout_subscription_price_id'] = price_id
    return redirect("stripe-checkout-start")

@login_required
def checkout_redirect_view(request):
    checkout_subscription_price_id = request.session.get("checkout_subscription_price_id")
    try:
        obj = SubscriptionsPrice.objects.get(id=checkout_subscription_price_id)
    except:
        obj = None 
    
    if checkout_subscription_price_id is None or obj is None:
        return redirect("pricing")
    
    customer_stripe_id = request.user.customer.stripe_id
    pricing_url_path = reverse("pricing")
    success_url_path = reverse("stripe-checkout-end")
    success_url = f"{BASE_URL}{success_url_path}"
    cancel_url = f"{BASE_URL}{pricing_url_path}"
    price_stripe_id = obj.stripe_id
    
    # ✅ Check if user has an existing subscription
    existing_subscription_id = None
    try:
        existing_user_sub = UserSubscription.objects.get(user=request.user)
        if existing_user_sub.stripe_id and existing_user_sub.active:
            existing_subscription_id = existing_user_sub.stripe_id
    except UserSubscription.DoesNotExist:
        pass
    
    # Create checkout session (pass existing subscription if upgrading)
    url = helpers.billing.start_checkout_session(
        customer_stripe_id, 
        success_url=success_url, 
        cancel_url=cancel_url, 
        price_stripe_id=price_stripe_id,
        existing_subscription_id=existing_subscription_id,  # ✅ Pass this
        raw=False
    )
    return redirect(url)

def checkout_finalize_view(request):
    session_id = request.GET.get('session_id')
    customer_id, plan_id, sub_stripe_id = helpers.billing.get_checkout_customer_plan(session_id)
    
    try:
        sub_obj = Subscription.objects.get(subscriptionsprice__stripe_id=plan_id)
    except (Subscription.DoesNotExist, Subscription.MultipleObjectsReturned):
        sub_obj = None
    
    try:
        user_obj = User.objects.get(customer__stripe_id=customer_id)
    except:
        user_obj = None
    
    if None in [user_obj, sub_obj]:
        return HttpResponseBadRequest("Invalid session data.")
    
    # ✅ CRITICAL FIX: Cancel ALL old subscriptions for this customer
    is_upgrade = False
    old_subscription = None
    
    try:
        existing_user_sub = UserSubscription.objects.get(user=user_obj)
        old_subscription = existing_user_sub.subscription
        old_stripe_sub_id = existing_user_sub.stripe_id
        
        is_upgrade = old_subscription is not None and old_subscription != sub_obj
        
        # ✅ Cancel the old subscription if it exists and is different
        if old_stripe_sub_id and old_stripe_sub_id != sub_stripe_id:
            try:
                print(f"Attempting to cancel old subscription: {old_stripe_sub_id}")
                result = helpers.billing.cancel_subscription(
                    subscription_id=old_stripe_sub_id,
                    cancel_at_period_end=False,
                    raw=True  # Get full response to see what happened
                )
                if result:
                    print(f"✅ Successfully cancelled: {old_stripe_sub_id}")
                    print(f"Status: {result.status if hasattr(result, 'status') else 'deleted'}")
                else:
                    print(f"⚠️ Cancellation returned None for: {old_stripe_sub_id}")
            except Exception as e:
                print(f"❌ ERROR cancelling subscription {old_stripe_sub_id}: {e}")
                # Log this to your error tracking system
    
    except UserSubscription.DoesNotExist:
        print("No existing subscription found - this is a new subscription")
    
    # Update Django database
    _user_sub_obj, created = UserSubscription.objects.update_or_create(
        user=user_obj,
        defaults={
            "subscription": sub_obj,
            "stripe_id": sub_stripe_id,
            "active": True
        }
    )
    
    context = {
        "subscription": sub_obj,
        "user_sub": _user_sub_obj,
        "is_new": created,
        "is_upgrade": is_upgrade,
        "old_subscription": old_subscription
    }
    
    return render(request, "checkout/success.html", context)