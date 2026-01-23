from django.contrib import admin

# Register your models here.
from .models import Subscriptions, SubscriptionsPrice, UserSubscription 

class SubscriptionsPrice(admin.TabularInline):
    model = SubscriptionsPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0
      

class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionsPrice]
    list_display = ['name', 'active']
    readonly_fields = ['stripe_id']



admin.site.register(Subscriptions, SubscriptionAdmin) 
admin.site.register(UserSubscription)