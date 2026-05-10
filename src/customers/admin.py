from django.contrib import admin

# Register your models here.
from .models import Customer, SupportRequest

admin.site.register(Customer)


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ["subject", "email", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["subject", "email", "name", "message"]
