from django.conf import settings
from django.db import models
import helpers.billing
from allauth.account.signals import (user_signed_up as allauth_user_signed_up, email_confirmed as allauth_email_confirmed)
User = settings.AUTH_USER_MODEL
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(null=True, blank=True)
    init_email_confirmed = models.BooleanField(default=False)
   
    def __str__(self):
        return f"{self.user.username}"

    @property
    def can_use_stripe(self):
        return bool(self.user.email)
    
    def save(self, *args, **kwargs):         
        created_stripe_id = False
        if not self.stripe_id:
            if self.can_use_stripe:
                email = self.user.email
                stripe_id = helpers.billing.create_customer(
                    email=email,
                    metadata={"user_id": self.user.id, "username": self.user.username},
                    raw=False,
                )
                self.stripe_id = stripe_id
                created_stripe_id = bool(stripe_id)
        update_fields = kwargs.get("update_fields")
        if created_stripe_id and update_fields:
            kwargs["update_fields"] = list(dict.fromkeys([*update_fields, "stripe_id"]))
        super().save(*args, **kwargs)  


class SupportRequest(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.email})"


def allauth_user_signed_up_handler(request, user, *args, **kwargs):
    email = user.email
    Customer.objects.create(user=user, init_email= email, init_email_confirmed=False)

    
allauth_user_signed_up.connect(allauth_user_signed_up_handler)

def allauth_email_confirmed_handler(request, email_address, *args, **kwargs):
    qs = Customer.objects.filter(init_email= email_address, init_email_confirmed=False)
    for obj in qs:
        obj.init_email_confirmed=True
        obj.save()


allauth_email_confirmed.connect(allauth_email_confirmed_handler)
