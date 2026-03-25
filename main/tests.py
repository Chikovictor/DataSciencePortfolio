from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from io import BytesIO
import os

from .forms import ContactForm
from .models import Event, Review
from .views import _send_contact_email


class ReviewModelTests(TestCase):
    @override_settings(MAX_VISIBLE_REVIEWS=2)
    def test_enforce_approved_limit_archives_oldest(self):
        older = Review.objects.create(
            name="Older",
            title="Analyst",
            review_text="Old approved review",
            is_approved=True,
            created_at=timezone.now(),
        )
        middle = Review.objects.create(
            name="Middle",
            title="Manager",
            review_text="Middle approved review",
            is_approved=True,
            created_at=timezone.now(),
        )
        newest = Review.objects.create(
            name="Newest",
            title="Lead",
            review_text="Newest approved review",
            is_approved=True,
            created_at=timezone.now(),
        )

        Review.enforce_approved_limit()
        older.refresh_from_db()
        middle.refresh_from_db()
        newest.refresh_from_db()

        self.assertFalse(older.is_approved)
        self.assertIsNotNone(older.archived_at)
        self.assertTrue(middle.is_approved)
        self.assertTrue(newest.is_approved)

    def test_default_avatar_flag_is_set_when_no_image(self):
        review = Review.objects.create(
            name="No Avatar",
            title="Client",
            review_text="Great work and communication.",
            is_approved=False,
        )
        self.assertTrue(review.uses_default_avatar)


class ContactFormTests(TestCase):
    def test_contact_form_blocks_header_injection(self):
        form = ContactForm(
            data={
                "name": "Attacker\nInjected",
                "email": "valid@example.com",
                "message": "This message has enough content.",
                "honeypot": "",
                "rendered_at": timezone.now().timestamp() - 5,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class ContactEmailFlowTests(TestCase):
    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
        CONTACT_FROM_NAME="Victor.DataScience",
        CONTACT_NOTIFICATION_EMAIL="myportfolio332@gmail.com",
    )
    def test_send_contact_email_sets_from_and_reply_to(self):
        cleaned_data = {
            "name": "Jane Sender",
            "email": "jane.sender@example.com",
            "message": "I need help with a Django API integration for my team.",
        }

        _send_contact_email(cleaned_data)

        self.assertEqual(len(mail.outbox), 1)
        outgoing = mail.outbox[0]
        self.assertEqual(outgoing.subject, "Inquiry via Victor's Portfolio Website")
        self.assertEqual(outgoing.to, ["myportfolio332@gmail.com"])
        self.assertEqual(outgoing.reply_to, ["jane.sender@example.com"])
        self.assertIn("Victor.DataScience", outgoing.from_email)
        self.assertIn("no-reply@example.com", outgoing.from_email)
        self.assertEqual(
            outgoing.body,
            "I need help with a Django API integration for my team.\n\n"
            "Jane Sender\n"
            "jane.sender@example.com",
        )
        self.assertEqual(
            outgoing.body.count("I need help with a Django API integration for my team."),
            1,
        )

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
        CONTACT_FROM_NAME="Victor.DataScience",
        CONTACT_NOTIFICATION_EMAIL="myportfolio332@gmail.com",
        CONTACT_DUPLICATE_WINDOW_SECONDS=300,
    )
    def test_duplicate_contact_submission_is_blocked(self):
        url = reverse("index")
        rendered_at = timezone.now().timestamp() - 5
        payload = {
            "contact_submit": "1",
            "name": "Repeat Sender",
            "email": "repeat.sender@example.com",
            "message": "This is my detailed project brief for duplicate checking.",
            "honeypot": "",
            "rendered_at": rendered_at,
        }

        first_response = self.client.post(url, payload, secure=True)
        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        second_response = self.client.post(url, payload, secure=True)
        self.assertEqual(second_response.status_code, 200)
        self.assertContains(
            second_response,
            "already submitted recently",
            status_code=200,
        )
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
        CONTACT_FROM_NAME="Victor.DataScience",
        CONTACT_NOTIFICATION_EMAIL="myportfolio332@gmail.com",
    )
    def test_ajax_contact_submit_returns_json_success_without_redirect(self):
        url = reverse("index")
        payload = {
            "contact_submit": "1",
            "name": "Ajax Sender",
            "email": "ajax.sender@example.com",
            "message": "This is an ajax flow message that should return json success.",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
        }

        response = self.client.post(
            url,
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("Message sent successfully", payload["message"])
        self.assertIn("rendered_at", payload)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
        CONTACT_FROM_NAME="Victor.DataScience",
        CONTACT_NOTIFICATION_EMAIL="myportfolio332@gmail.com",
        CONTACT_RATE_LIMIT=1,
        CONTACT_RATE_WINDOW_SECONDS=3600,
    )
    def test_rate_limit_does_not_stack_with_invalid_message_error(self):
        url = reverse("index")
        first_payload = {
            "contact_submit": "1",
            "name": "Rate Valid Sender",
            "email": "rate.valid@example.com",
            "message": "This valid message consumes one rate-limit slot.",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
        }
        second_payload = {
            "contact_submit": "1",
            "name": "Rate Valid Sender",
            "email": "rate.valid@example.com",
            "message": "short",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
        }

        first_response = self.client.post(
            url,
            first_payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        second_response = self.client.post(
            url,
            second_payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )
        self.assertEqual(second_response.status_code, 400)
        second_json = second_response.json()
        self.assertIn("message", second_json["field_errors"])
        self.assertIn(
            "Please provide a little more detail in your message.",
            second_json["field_errors"]["message"],
        )
        self.assertNotIn(
            "Too many messages sent. Please wait a few minutes and try again.",
            second_json.get("non_field_errors", []),
        )

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
        CONTACT_FROM_NAME="Victor.DataScience",
        CONTACT_NOTIFICATION_EMAIL="myportfolio332@gmail.com",
        CONTACT_RATE_LIMIT=1,
        CONTACT_RATE_WINDOW_SECONDS=3600,
        CONTACT_DUPLICATE_WINDOW_SECONDS=60,
    )
    def test_rate_limit_key_is_scoped_by_sender_email(self):
        url = reverse("index")
        first_payload = {
            "contact_submit": "1",
            "name": "First Sender",
            "email": "first.sender@example.com",
            "message": "This first message should be accepted for the first sender.",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
        }
        second_payload = {
            "contact_submit": "1",
            "name": "Second Sender",
            "email": "second.sender@example.com",
            "message": "This second message should also pass because sender email differs.",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
        }

        first_response = self.client.post(url, first_payload, secure=True)
        self.assertEqual(first_response.status_code, 302)
        second_response = self.client.post(url, second_payload, secure=True)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)


class ReviewAjaxFlowTests(TestCase):
    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
        REVIEW_NOTIFICATION_EMAIL="myportfolio332@gmail.com",
    )
    def test_review_ajax_submit_returns_json_success(self):
        url = reverse("index")
        payload = {
            "review_submit": "1",
            "name": "Review Ajax Sender",
            "title": "Data Lead",
            "review_text": "Great collaboration and delivery quality.",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
        }

        response = self.client.post(
            url,
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertTrue(json_body["success"])
        self.assertIn("awaiting approval", json_body["message"])
        self.assertIn("rendered_at", json_body)
        self.assertTrue(Review.objects.filter(name="Review Ajax Sender").exists())

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@example.com",
    )
    def test_review_ajax_large_image_returns_inline_field_error(self):
        url = reverse("index")
        image_bytes = BytesIO()
        noisy_bytes = os.urandom(2200 * 2200 * 3)
        image = Image.frombytes("RGB", (2200, 2200), noisy_bytes)
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        oversized = SimpleUploadedFile(
            "oversized.png",
            image_bytes.read(),
            content_type="image/png",
        )
        payload = {
            "review_submit": "1",
            "name": "Oversized Image Sender",
            "title": "Program Manager",
            "review_text": "The review text is valid and sufficiently detailed.",
            "honeypot": "",
            "rendered_at": timezone.now().timestamp() - 5,
            "image": oversized,
        }

        response = self.client.post(
            url,
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        json_body = response.json()
        self.assertFalse(json_body["success"])
        self.assertIn("image", json_body["field_errors"])
        self.assertIn("Image is too large. Maximum size is 3MB.", json_body["field_errors"]["image"])
        self.assertFalse(Review.objects.filter(name="Oversized Image Sender").exists())



