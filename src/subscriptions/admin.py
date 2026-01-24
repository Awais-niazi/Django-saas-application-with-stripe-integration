from django.contrib import admin
from .models import Subscription, SubscriptionsPrice, UserSubscription 

# 1. Rename this to include "Inline"
class SubscriptionsPriceInline(admin.StackedInline):
    model = SubscriptionsPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0

class SubscriptionAdmin(admin.ModelAdmin):
    # 2. Reference the renamed Inline class here
    inlines = [SubscriptionsPriceInline]
    list_display = ['name', 'active']
    readonly_fields = ['stripe_id']

admin.site.register(Subscription, SubscriptionAdmin) 
admin.site.register(UserSubscription)