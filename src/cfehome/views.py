from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from customers.forms import SupportRequestForm
from customers.models import Customer, SupportRequest
from helpers import billing
from subscriptions.models import Subscriptions, SubscriptionsPrice, UserSubscription
from visits.models import PageVisit


BEGINNER_FEATURES = [
    {
        "title": "Authentication",
        "description": "Friendly sign up, login, logout, password, and email flows so new developers can follow the whole account lifecycle.",
    },
    {
        "title": "Subscriptions",
        "description": "Simple plan ideas, upgrade paths, and plan-based permissions that are easy to extend into full billing.",
    },
    {
        "title": "Billing",
        "description": "Starter billing overview pages with room for Stripe checkout, invoices, and webhooks later.",
    },
    {
        "title": "Support",
        "description": "A real contact flow that stores support requests in the database and admin dashboard.",
    },
    {
        "title": "Operations",
        "description": "Health checks, deploy-friendly settings, static files, and environment configuration for Render.",
    },
]


BEGINNER_PLANS = [
    {
        "name": "Starter",
        "price": "$0",
        "description": "For learning the app locally and understanding the basic flow.",
        "features": [
            "Email/password authentication",
            "Profile pages",
            "Protected dashboard",
            "Community-style support form",
        ],
    },
    {
        "name": "Growth",
        "price": "$19/mo",
        "description": "For small paid projects that need billing and a cleaner account experience.",
        "features": [
            "Everything in Starter",
            "Plan-based feature flags",
            "Customer and billing records",
            "Priority support queue",
        ],
    },
    {
        "name": "Pro",
        "price": "$49/mo",
        "description": "For teams that want a strong SaaS starter with room to scale.",
        "features": [
            "Everything in Growth",
            "Advanced permission groups",
            "Operational health checks",
            "Easy path to webhooks and invoices",
        ],
    },
]


def get_plan_cards():
    plans = []
    for subscription in Subscriptions.objects.filter(active=True).order_by("name"):
        prices = list(subscription.subscriptionsprice_set.all().order_by("price"))
        primary_price = prices[0] if prices else None
        plans.append(
            {
                "id": subscription.id,
                "name": subscription.name,
                "price": f"${primary_price.price}/mo" if primary_price else "Custom",
                "description": "Database-backed subscription plan.",
                "features": [
                    f"{subscription.permissions.count()} permission-based features",
                    f"{subscription.groups.count()} linked user groups",
                ],
                "checkout_ready": bool(primary_price and primary_price.stripe_id),
                "price_id": primary_price.id if primary_price else None,
                "interval": primary_price.get_interval_display() if primary_price else "",
            }
        )
    return plans or BEGINNER_PLANS


def ensure_customer_for_user(user):
    customer, _ = Customer.objects.get_or_create(
        user=user,
        defaults={
            "init_email": user.email,
            "init_email_confirmed": bool(user.email),
        },
    )
    updated_fields = []
    if not customer.init_email and user.email:
        customer.init_email = user.email
        updated_fields.append("init_email")
    if user.email and not customer.init_email_confirmed:
        customer.init_email_confirmed = True
        updated_fields.append("init_email_confirmed")
    if updated_fields:
        customer.save(update_fields=updated_fields)
    if not customer.stripe_id:
        customer.save()
    return customer


def ensure_subscription_price_stripe_ids(subscription_price):
    if not subscription_price.subscription:
        return subscription_price

    if not subscription_price.subscription.stripe_id:
        subscription_price.subscription.save()
        subscription_price.subscription.refresh_from_db()

    if not subscription_price.stripe_id:
        subscription_price.save()
        subscription_price.refresh_from_db()

    return subscription_price


def sync_user_subscription_from_checkout_session(session):
    metadata = session.get("metadata", {}) or {}
    user_id = metadata.get("user_id")
    price_id = metadata.get("subscription_price_id")

    if not user_id or not price_id:
        return

    try:
        customer = Customer.objects.select_related("user").get(user_id=user_id)
        subscription_price = SubscriptionsPrice.objects.select_related("subscription").get(id=price_id)
    except (Customer.DoesNotExist, SubscriptionsPrice.DoesNotExist):
        return

    local_subscription = subscription_price.subscription
    if not local_subscription:
        return

    if session.get("customer") and customer.stripe_id != session["customer"]:
        customer.stripe_id = session["customer"]
        customer.save(update_fields=["stripe_id"])

    user_subscription, _ = UserSubscription.objects.get_or_create(user=customer.user)
    user_subscription.subscription = local_subscription
    user_subscription.active = True
    user_subscription.stripe_subscription_id = session.get("subscription") or ""
    user_subscription.save()


def build_dashboard_context(request):
    total_visits = PageVisit.objects.count()
    current_path_visits = PageVisit.objects.filter(path=request.path).count()
    customer = None
    current_subscription = None
    if request.user.is_authenticated:
        customer = Customer.objects.filter(user=request.user).first()
        current_subscription = UserSubscription.objects.filter(user=request.user).select_related("subscription").first()
    return {
        "page_title": "Dashboard",
        "current_path_visits": current_path_visits,
        "total_visits": total_visits,
        "plan_cards": get_plan_cards(),
        "customer": customer,
        "current_subscription": current_subscription,
    }

def landing_page_view(request):
    context = {
        "page_title": "Laxx",
        "feature_cards": BEGINNER_FEATURES,
        "plan_cards": get_plan_cards(),
    }
    return render(request, "landing_page.html", context)


def home_view(request, *args, **kwargs):
    return dashboard_view(request, *args, **kwargs)


@login_required
def dashboard_view(request, *args, **kwargs):
    PageVisit.objects.create(path=request.path)
    return render(request, "home.html", build_dashboard_context(request))


def about_view(request):
    context = {
        "page_title": "Features",
        "feature_cards": BEGINNER_FEATURES,
        "plan_cards": get_plan_cards(),
    }
    return render(request, "features.html", context)


def pricing_view(request):
    return render(
        request,
        "pricing.html",
        {
            "page_title": "Pricing",
            "plan_cards": get_plan_cards(),
            "stripe_configured": billing.stripe_is_configured(),
        },
    )


@login_required
def onboarding_view(request):
    return render(request, "onboarding.html", {"page_title": "Getting Started"})


@login_required
def account_overview_view(request):
    customer = Customer.objects.filter(user=request.user).first()
    current_subscription = (
        UserSubscription.objects.filter(user=request.user).select_related("subscription").first()
    )
    support_requests = SupportRequest.objects.filter(user=request.user)[:5]
    return render(
        request,
        "account_overview.html",
        {
            "page_title": "Account",
            "customer": customer,
            "current_subscription": current_subscription,
            "support_requests": support_requests,
        },
    )


@login_required
def billing_overview_view(request):
    customer = Customer.objects.filter(user=request.user).first()
    current_subscription = (
        UserSubscription.objects.filter(user=request.user).select_related("subscription").first()
    )
    available_prices = list(
        SubscriptionsPrice.objects.select_related("subscription")
        .filter(subscription__active=True)
        .order_by("subscription__name", "price")
    )
    return render(
        request,
        "billing_overview.html",
        {
            "page_title": "Billing",
            "customer": customer,
            "current_subscription": current_subscription,
            "available_prices": available_prices,
            "stripe_configured": billing.stripe_is_configured(),
            "has_active_subscription": bool(
                current_subscription and current_subscription.active and current_subscription.subscription
            ),
        },
    )


def support_view(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
        }
    form = SupportRequestForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        support_request = form.save(commit=False)
        if request.user.is_authenticated:
            support_request.user = request.user
        support_request.save()
        messages.success(request, "Your support request has been submitted.")
        return redirect("support_view")
    return render(
        request,
        "support.html",
        {
            "page_title": "Support",
            "form": form,
        },
    )


def privacy_view(request):
    return render(request, "privacy.html", {"page_title": "Privacy"})


def terms_view(request):
    return render(request, "terms.html", {"page_title": "Terms"})


def health_check_view(request):
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def create_checkout_session_view(request, price_id):
    if not billing.stripe_is_configured():
        messages.error(request, "Stripe is not configured yet. Add your Stripe keys first.")
        return redirect("billing_overview_view")

    try:
        subscription_price = SubscriptionsPrice.objects.select_related("subscription").get(
            id=price_id,
            subscription__active=True,
        )
    except SubscriptionsPrice.DoesNotExist:
        messages.error(request, "That subscription price could not be found.")
        return redirect("billing_overview_view")

    subscription_price = ensure_subscription_price_stripe_ids(subscription_price)
    if not subscription_price.stripe_id:
        messages.error(request, "This plan is not ready in Stripe yet. Save the subscription and price records after configuring Stripe.")
        return redirect("billing_overview_view")

    customer = ensure_customer_for_user(request.user)
    if not customer.stripe_id:
        messages.error(request, "A Stripe customer could not be created for this account yet.")
        return redirect("billing_overview_view")

    success_url = request.build_absolute_uri("/billing/success/?session_id={CHECKOUT_SESSION_ID}")
    cancel_url = request.build_absolute_uri("/billing/cancel/")
    checkout_url = billing.create_checkout_session(
        customer_id=customer.stripe_id,
        price_id=subscription_price.stripe_id,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(request.user.id),
        metadata={
            "user_id": str(request.user.id),
            "subscription_id": str(subscription_price.subscription_id or ""),
            "subscription_price_id": str(subscription_price.id),
        },
    )

    if not checkout_url:
        messages.error(request, "Stripe Checkout could not be created.")
        return redirect("billing_overview_view")

    return redirect(checkout_url)


@login_required
def billing_success_view(request):
    session_id = request.GET.get("session_id", "")
    return render(
        request,
        "billing_success.html",
        {
            "page_title": "Billing Success",
            "session_id": session_id,
        },
    )


@login_required
def billing_cancel_view(request):
    return render(request, "billing_cancel.html", {"page_title": "Billing Cancelled"})


@login_required
def billing_portal_view(request):
    if not billing.billing_portal_is_configured():
        messages.error(request, "Stripe Billing Portal is not configured yet.")
        return redirect("billing_overview_view")

    customer = ensure_customer_for_user(request.user)
    if not customer.stripe_id:
        messages.error(request, "This account does not have a Stripe customer yet.")
        return redirect("billing_overview_view")

    portal_url = billing.create_billing_portal_session(
        customer_id=customer.stripe_id,
        return_url=request.build_absolute_uri("/billing/"),
    )
    if not portal_url:
        messages.error(request, "The billing portal could not be created.")
        return redirect("billing_overview_view")

    return redirect(portal_url)


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = billing.construct_webhook_event(request.body, signature)
    except ValueError:
        return HttpResponseBadRequest("Stripe webhook secret is not configured.")
    except Exception:
        return HttpResponseBadRequest("Invalid webhook signature.")

    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed" and event_data.get("mode") == "subscription":
        sync_user_subscription_from_checkout_session(event_data)
    elif event_type in {"customer.subscription.deleted", "customer.subscription.updated"}:
        stripe_subscription_id = event_data.get("id", "")
        if stripe_subscription_id:
            try:
                user_subscription = UserSubscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            except UserSubscription.DoesNotExist:
                user_subscription = None
            if user_subscription:
                status = event_data.get("status", "")
                user_subscription.active = status in {"active", "trialing"}
                if status in {"canceled", "unpaid", "incomplete_expired"}:
                    user_subscription.subscription = None
                user_subscription.save()

    return HttpResponse(status=200)


VALID_CODE = "abc123"

def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed
    if is_allowed:
        return render(request, "protected/view.html", {})
    return render(request, "protected/entry.html", {})

@login_required
def user_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {}) 


@staff_member_required
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {}) 
