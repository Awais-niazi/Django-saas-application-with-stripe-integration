from django.shortcuts import render
from subscriptions.models import SubscriptionsPrice

# Create your views here.
def subscription_price_view(request):
    qs = SubscriptionsPrice.objects.filter(featured=True)
    monthly_qs = qs.filter(interval=SubscriptionsPrice.IntervalChoices.MONTHLY)
    yearly_qs = qs.filter(interval=SubscriptionsPrice.IntervalChoices.YEARLY)
    return render(request, "subscriptions/pricing.html", {
        "monthly_qs":monthly_qs,
        "yearly_qs":yearly_qs,
    }) 