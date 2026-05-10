from django import forms

from .models import SupportRequest


class SupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "subject": forms.TextInput(attrs={"placeholder": "What do you need help with?"}),
            "message": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Describe your issue, question, or idea.",
                }
            ),
        }
