from django.conf import settings
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Review


def _validate_header_safe(value, field_name):
    if "\n" in value or "\r" in value:
        raise ValidationError(f"Invalid characters detected in {field_name}.")


class AntiSpamMixin:
    min_submit_seconds = 2
    max_form_age_seconds = 60 * 60 * 12

    def clean_honeypot(self):
        value = self.cleaned_data.get("honeypot", "")
        if value:
            raise ValidationError("Spam submission detected.")
        return value

    def clean(self):
        cleaned = super().clean()
        rendered_at = cleaned.get("rendered_at")
        if rendered_at:
            elapsed = timezone.now().timestamp() - rendered_at
            if elapsed < self.min_submit_seconds:
                raise ValidationError("Please wait a moment before submitting.")
            if elapsed > self.max_form_age_seconds:
                raise ValidationError("This form expired. Refresh and submit again.")
        return cleaned


class ReviewForm(AntiSpamMixin, forms.ModelForm):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput, strip=False)
    rendered_at = forms.FloatField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Review
        fields = ["name", "title", "review_text", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Role / Company"}
            ),
            "review_text": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Your review..."}
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        _validate_header_safe(value, "name")
        return value

    def clean_title(self):
        value = (self.cleaned_data.get("title") or "").strip()
        _validate_header_safe(value, "title")
        return value


class ContactForm(AntiSpamMixin, forms.Form):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput, strip=False)
    rendered_at = forms.FloatField(required=False, widget=forms.HiddenInput)

    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@email.com"}),
    )
    message = forms.CharField(
        max_length=3000,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Tell me about your project.",
            }
        ),
    )

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        _validate_header_safe(value, "name")
        return value

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip()
        _validate_header_safe(value, "email")
        return value

    def clean_message(self):
        value = (self.cleaned_data.get("message") or "").strip()
        if len(value) < 10:
            raise ValidationError("Please provide a little more detail in your message.")
        return value


class CommentForm(AntiSpamMixin, forms.Form):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput, strip=False)
    rendered_at = forms.FloatField(required=False, widget=forms.HiddenInput)
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    user_name = forms.CharField(
        min_length=2,
        max_length=120,
        widget=forms.HiddenInput(),
    )
    user_email = forms.EmailField(
        required=False,
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@email.com (optional)",
            }
        ),
    )
    content = forms.CharField(
        max_length=getattr(settings, "COMMENT_MAX_LENGTH", 1000),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Share your perspective...",
            }
        ),
    )

    def clean_user_name(self):
        value = (self.cleaned_data.get("user_name") or "").strip()
        _validate_header_safe(value, "name")
        if len(value) < 2:
            raise ValidationError("Name must be at least 2 characters.")
        return value

    def clean_user_email(self):
        value = (self.cleaned_data.get("user_email") or "").strip()
        if value:
            _validate_header_safe(value, "email")
        return value

    def clean_parent_id(self):
        value = self.cleaned_data.get("parent_id")
        if value in (None, ""):
            return None
        if value <= 0:
            raise ValidationError("Invalid parent comment.")
        return value

    def clean_content(self):
        value = (self.cleaned_data.get("content") or "").strip()
        if len(value) < 2:
            raise ValidationError("Please add a more detailed comment.")
        return value
