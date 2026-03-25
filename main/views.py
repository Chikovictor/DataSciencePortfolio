import logging
import json
from hashlib import sha256
from email.utils import formataddr, parseaddr
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import BadHeaderError, EmailMessage, EmailMultiAlternatives
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import CommentForm, ContactForm, ReviewForm
from .models import CaseStudy, Certification, Event, ProfileImage, Review
from .security import client_identifier, is_rate_limited

logger = logging.getLogger(__name__)
DISPLAY_NAME_COOKIE = "portfolio_display_name"


def _form_initial():
    return {"rendered_at": timezone.now().timestamp()}


def _fallback_case_studies():
    return [
        {
            "title": "Retail Demand Forecasting Platform",
            "summary": "Improved replenishment accuracy for a regional retail operation.",
            "problem": "Stock-outs and overstocking were affecting revenue and warehouse cost.",
            "data": "2 years of sales transactions, seasonality patterns, and store-level inventory logs.",
            "approach": "Forecasting pipeline with engineered features, weekly retraining, and quality monitoring.",
            "results": "Lower stock-out incidents and more consistent store-level inventory planning.",
            "tech_stack_list": ["Python", "Pandas", "Scikit-learn", "Django API", "PostgreSQL"],
            "github_url": "",
            "preview_image_url": static("images/project1.jpg"),
        },
        {
            "title": "Loan Risk Classification Service",
            "summary": "Data product to support faster and safer lending decisions.",
            "problem": "Manual risk assessment delayed decisions and introduced inconsistency.",
            "data": "Applicant profiles, repayment behavior, transactional records, and default labels.",
            "approach": "Classification workflow with feature selection, threshold optimization, and API inference.",
            "results": "Faster pre-screening and stronger alignment between approvals and risk policy.",
            "tech_stack_list": ["Python", "NumPy", "Scikit-learn", "Django REST", "MySQL"],
            "github_url": "",
            "preview_image_url": static("images/project2.jpg"),
        },
        {
            "title": "Customer Churn Early-Warning Model",
            "summary": "Retention analytics to detect churn risk before revenue impact.",
            "problem": "The business had no early warning system for at-risk customer segments.",
            "data": "CRM activity logs, billing history, support interactions, and product usage events.",
            "approach": "Built churn features, evaluated threshold scenarios, and exposed scoring through Django.",
            "results": "Higher retention campaign precision and faster intervention for high-risk cohorts.",
            "tech_stack_list": ["Python", "Pandas", "XGBoost", "Django", "PostgreSQL"],
            "github_url": "",
            "preview_image_url": static("images/project1.jpg"),
        },
        {
            "title": "Operations KPI Intelligence Dashboard",
            "summary": "Executive-grade KPI monitoring with actionable drill-downs.",
            "problem": "Teams lacked a single trusted source for operational and financial KPIs.",
            "data": "Warehouse movements, sales KPIs, and service-level metrics from multiple systems.",
            "approach": "Unified datasets, modeled KPIs, and built a reliable reporting API layer.",
            "results": "Shorter reporting cycles and faster decisions for operations leadership.",
            "tech_stack_list": ["Power BI", "SQL", "Python", "Django API", "MySQL"],
            "github_url": "",
            "preview_image_url": static("images/project2.jpg"),
        },
    ]


def _case_studies_for_homepage(min_cards=4):
    published = list(
        CaseStudy.objects.filter(is_published=True).order_by("display_order", "-created_at")[:8]
    )
    if len(published) >= min_cards:
        return published
    fallback = _fallback_case_studies()
    published.extend(fallback[: max(0, min_cards - len(published))])
    return published


def _profile_images_for_homepage():
    return list(ProfileImage.objects.filter(is_active=True).order_by("order", "-created_at"))


def _reaction_emoji_values():
    return [emoji for emoji, _ in Reaction.EMOJI_CHOICES]


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key or "anonymous-session"


def _clean_identity_name(raw_name):
    name = (raw_name or "").strip()
    if not name:
        return ""
    if "\n" in name or "\r" in name:
        return ""
    return name


def _identity_name_from_request(request):
    posted_name = request.POST.get("user_name", "")
    if not posted_name:
        content_type = (request.content_type or "").lower()
        if "application/json" in content_type:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
            except (ValueError, UnicodeDecodeError):
                payload = {}
            posted_name = str(payload.get("user_name", "")).strip()

    if posted_name:
        return _clean_identity_name(posted_name)

    return _clean_identity_name(request.COOKIES.get(DISPLAY_NAME_COOKIE, ""))


def _identity_name_is_valid(identity_name):
    return len(identity_name) >= 2


def _identity_user_identifier(request, identity_name):
    normalized_name = identity_name.strip().lower()
    raw = f"{_ensure_session_key(request)}|{client_identifier(request)}|{normalized_name}"
    return sha256(raw.encode("utf-8")).hexdigest()


def _apply_identity_cookie(response, identity_name):
    if not _identity_name_is_valid(identity_name):
        return response
    response.set_cookie(
        DISPLAY_NAME_COOKIE,
        identity_name,
        max_age=60 * 60 * 24 * 30,
        samesite="Lax",
        secure=getattr(settings, "SESSION_COOKIE_SECURE", False),
        httponly=False,
    )
    return response


def _send_review_notification(review):
    notification_recipient = getattr(
        settings, "REVIEW_NOTIFICATION_EMAIL", settings.CONTACT_NOTIFICATION_EMAIL
    )
    admin_path = getattr(settings, "ADMIN_URL", "admin/")
    body = (
        "New review awaiting approval.\n\n"
        f"Name: {review.name}\n"
        f"Title: {review.title}\n"
        f"Submitted: {review.created_at:%Y-%m-%d %H:%M UTC}\n"
        f"Uses default avatar: {'Yes' if review.uses_default_avatar else 'No'}\n"
        f"Moderate in admin: /{admin_path}main/review/{review.pk}/change/\n"
    )
    message = EmailMultiAlternatives(
        subject="New portfolio review pending approval",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notification_recipient],
    )
    message.send(fail_silently=False)


def _notification_recipients():
    raw = getattr(settings, "CONTACT_NOTIFICATION_EMAIL", "myportfolio332@gmail.com")
    recipients = [value.strip() for value in str(raw).split(",") if value.strip()]
    return recipients or ["myportfolio332@gmail.com"]


def _contact_email_subject():
    subject = getattr(
        settings, "CONTACT_EMAIL_SUBJECT", "Inquiry via Victor's Portfolio Website"
    ).strip()
    return subject or "Inquiry via Victor's Portfolio Website"


def _format_contact_email_body(sender_name, sender_email, message_text):
    return f"{message_text}\n\n{sender_name}\n{sender_email}"


def _contact_from_email():
    default_from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "").strip()
    _, from_address = parseaddr(default_from_email)
    if not from_address:
        from_address = getattr(settings, "EMAIL_HOST_USER", "").strip()

    from_name = getattr(settings, "CONTACT_FROM_NAME", "Victor.DataScience").strip()
    from_name = from_name or "Victor.DataScience"
    return formataddr((from_name, from_address))


def _contact_submission_cache_key(request, cleaned_data):
    normalized_payload = "|".join(
        [
            cleaned_data["name"].strip().lower(),
            cleaned_data["email"].strip().lower(),
            " ".join(cleaned_data["message"].split()).lower(),
        ]
    )
    fingerprint = sha256(normalized_payload.encode("utf-8")).hexdigest()
    return f"contact-duplicate:{client_identifier(request)}:{fingerprint}"


def _is_duplicate_contact_submission(request, cleaned_data):
    cache_key = _contact_submission_cache_key(request, cleaned_data)
    return cache.get(cache_key) is not None


def _mark_contact_submission_sent(request, cleaned_data, window_seconds):
    cache_key = _contact_submission_cache_key(request, cleaned_data)
    cache.set(cache_key, timezone.now().isoformat(), timeout=window_seconds)


def _send_contact_email(cleaned_data):
    sender_name = cleaned_data["name"].strip()
    sender_email = cleaned_data["email"].strip()
    message_text = cleaned_data["message"].strip()
    subject = _contact_email_subject()

    outgoing = EmailMessage(
        subject=subject,
        body=_format_contact_email_body(sender_name, sender_email, message_text),
        from_email=_contact_from_email(),
        to=_notification_recipients(),
        reply_to=[sender_email],
        headers={"X-Portfolio-Source": "contact-form"},
    )
    outgoing.content_subtype = "plain"
    sent_count = outgoing.send(fail_silently=False)
    logger.info("Contact email sent. sender=%s sent_count=%s", sender_email, sent_count)


def _contact_email_transport_ready():
    backend = getattr(settings, "EMAIL_BACKEND", "").strip()
    non_delivery_backends = (
        "django.core.mail.backends.console.EmailBackend",
        "django.core.mail.backends.locmem.EmailBackend",
        "django.core.mail.backends.dummy.EmailBackend",
        "django.core.mail.backends.filebased.EmailBackend",
    )

    if not backend:
        logger.error("EMAIL_BACKEND is empty.")
        return False

    if backend in non_delivery_backends:
        if settings.DEBUG:
            logger.warning("Non-delivery email backend enabled in DEBUG: %s", backend)
            return True
        logger.error("Non-delivery EMAIL_BACKEND configured in non-DEBUG mode: %s", backend)
        return False

    if not backend.endswith("smtp.EmailBackend"):
        logger.warning("Custom EMAIL_BACKEND in use: %s", backend)
        return True

    required = {
        "EMAIL_HOST": getattr(settings, "EMAIL_HOST", "").strip(),
        "EMAIL_PORT": str(getattr(settings, "EMAIL_PORT", "")).strip(),
        "EMAIL_HOST_USER": getattr(settings, "EMAIL_HOST_USER", "").strip(),
        "EMAIL_HOST_PASSWORD": getattr(settings, "EMAIL_HOST_PASSWORD", "").strip(),
        "DEFAULT_FROM_EMAIL": getattr(settings, "DEFAULT_FROM_EMAIL", "").strip(),
        "CONTACT_NOTIFICATION_EMAIL": str(
            getattr(settings, "CONTACT_NOTIFICATION_EMAIL", "")
        ).strip(),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        logger.error("Contact email config missing: %s", ", ".join(missing))
        return False

    if getattr(settings, "EMAIL_USE_TLS", False) and getattr(settings, "EMAIL_USE_SSL", False):
        logger.error("Invalid email config: both EMAIL_USE_TLS and EMAIL_USE_SSL are enabled.")
        return False

    return True


def _is_ajax_request(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _dedupe_messages(messages):
    deduped = []
    seen = set()
    for message in messages:
        text = str(message)
        if text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _add_non_field_error_once(form, message):
    if message in _dedupe_messages(form.non_field_errors()):
        return
    form.add_error(None, message)


def _form_error_response(form, status=400, field_names=None):
    field_errors = {}
    if field_names is None:
        field_names = [name for name in form.errors.keys() if name != "__all__"]

    for field_name in field_names:
        errors = form.errors.get(field_name)
        if errors:
            field_errors[field_name] = _dedupe_messages(errors)

    non_field_errors = _dedupe_messages(form.non_field_errors())
    message = non_field_errors[0] if non_field_errors else ""
    return JsonResponse(
        {
            "success": False,
            "message": message,
            "field_errors": field_errors,
            "errors": field_errors,
            "non_field_errors": non_field_errors,
            "rendered_at": timezone.now().timestamp(),
        },
        status=status,
    )


def index(request):
    review_form = ReviewForm(initial=_form_initial())
    contact_form = ContactForm(initial=_form_initial())

    if request.method == "POST":
        if "review_submit" in request.POST:
            review_form = ReviewForm(request.POST, request.FILES)
            contact_form = ContactForm(initial=_form_initial())
            ajax_request = _is_ajax_request(request)

            if review_form.is_valid():
                reviewer_name = review_form.cleaned_data["name"].strip().lower()
                if is_rate_limited(
                    request,
                    scope="review-submit",
                    limit=getattr(settings, "REVIEW_RATE_LIMIT", 5),
                    window_seconds=getattr(settings, "REVIEW_RATE_WINDOW_SECONDS", 600),
                    identifier_suffix=reviewer_name,
                ):
                    _add_non_field_error_once(
                        review_form,
                        "Too many submissions. Please wait a few minutes and try again.",
                    )
                    if ajax_request:
                        return _form_error_response(review_form, status=429)
                else:
                    review = review_form.save(commit=False)
                    review.is_approved = False
                    review.save()
                    try:
                        _send_review_notification(review)
                    except Exception:
                        logger.exception("Review notification email failed.")
                    success_message = (
                        "Thank you. Your testimonial was submitted and is awaiting approval."
                    )
                    if ajax_request:
                        return JsonResponse(
                            {
                                "success": True,
                                "message": success_message,
                                "rendered_at": timezone.now().timestamp(),
                            }
                        )
                    messages.success(
                        request,
                        success_message,
                        extra_tags="review",
                    )
                    return redirect(f"{request.path}#submit-review")
            if ajax_request:
                return _form_error_response(review_form, status=400)

        elif "contact_submit" in request.POST:
            contact_form = ContactForm(request.POST)
            review_form = ReviewForm(initial=_form_initial())
            ajax_request = _is_ajax_request(request)

            if contact_form.is_valid():
                duplicate_window_seconds = getattr(
                    settings, "CONTACT_DUPLICATE_WINDOW_SECONDS", 300
                )
                sender_email = contact_form.cleaned_data["email"].strip().lower()
                if is_rate_limited(
                    request,
                    scope="contact-submit",
                    limit=getattr(settings, "CONTACT_RATE_LIMIT", 10),
                    window_seconds=getattr(settings, "CONTACT_RATE_WINDOW_SECONDS", 3600),
                    identifier_suffix=sender_email,
                ):
                    _add_non_field_error_once(
                        contact_form,
                        "Too many messages sent. Please wait a few minutes and try again.",
                    )
                    if ajax_request:
                        return _form_error_response(
                            contact_form, status=429, field_names=("name", "email", "message")
                        )
                elif _is_duplicate_contact_submission(request, contact_form.cleaned_data):
                    _add_non_field_error_once(
                        contact_form,
                        "This message was already submitted recently. Please avoid duplicate submissions.",
                    )
                    if ajax_request:
                        return _form_error_response(
                            contact_form, status=409, field_names=("name", "email", "message")
                        )
                elif not _contact_email_transport_ready():
                    _add_non_field_error_once(
                        contact_form,
                        "Contact email is not configured correctly. Site owner: check SMTP and sender settings.",
                    )
                    logger.error(
                        "Contact form email transport is not configured correctly. backend=%s",
                        getattr(settings, "EMAIL_BACKEND", ""),
                    )
                    if ajax_request:
                        return _form_error_response(
                            contact_form, status=500, field_names=("name", "email", "message")
                        )
                else:
                    try:
                        _send_contact_email(contact_form.cleaned_data)
                    except BadHeaderError:
                        logger.warning(
                            "Rejected contact submission due to header validation. sender=%s",
                            contact_form.cleaned_data.get("email"),
                        )
                        _add_non_field_error_once(
                            contact_form,
                            "Invalid email headers detected. Please edit your message and try again.",
                        )
                        if ajax_request:
                            return _form_error_response(
                                contact_form, status=400, field_names=("name", "email", "message")
                            )
                    except (SMTPException, TimeoutError, OSError):
                        logger.exception("Contact email transport failed.")
                        _add_non_field_error_once(
                            contact_form,
                            "Email server is temporarily unavailable. Please try again in a few minutes.",
                        )
                        if ajax_request:
                            return _form_error_response(
                                contact_form, status=503, field_names=("name", "email", "message")
                            )
                    except Exception:
                        logger.exception("Contact email failed.")
                        _add_non_field_error_once(
                            contact_form,
                            "Message could not be delivered right now. Please try again shortly.",
                        )
                        if ajax_request:
                            return _form_error_response(
                                contact_form, status=500, field_names=("name", "email", "message")
                            )
                    else:
                        _mark_contact_submission_sent(
                            request, contact_form.cleaned_data, duplicate_window_seconds
                        )
                        success_message = "Message sent successfully. I will respond soon."
                        if ajax_request:
                            return JsonResponse(
                                {
                                    "success": True,
                                    "message": success_message,
                                    "rendered_at": timezone.now().timestamp(),
                                    }
                                )
                        messages.success(
                            request,
                            success_message,
                            extra_tags="contact",
                        )
                        return redirect(f"{request.path}#contact")
            if ajax_request:
                return _form_error_response(
                    contact_form, status=400, field_names=("name", "email", "message")
                )

    approved_reviews = Review.objects.filter(is_approved=True).order_by("-created_at")[
        : getattr(settings, "MAX_VISIBLE_REVIEWS", 10)
    ]
    case_studies = _case_studies_for_homepage(min_cards=4)
    profile_images = _profile_images_for_homepage()
    certifications = list(
        Certification.objects.all().order_by("display_order", "-issue_date", "-created_at")
    )
    events_gallery = list(
        Event.objects.filter(is_active=True).order_by("order", "-date")
    )
    queued_messages = list(messages.get_messages(request))
    review_messages = [message for message in queued_messages if "review" in message.tags]
    contact_messages = [message for message in queued_messages if "contact" in message.tags]

    context = {
        "approved_reviews": approved_reviews,
        "review_form": review_form,
        "contact_form": contact_form,
        "case_studies": case_studies,
        "profile_images": profile_images,
        "certifications": certifications,
        "events_gallery": events_gallery,
        "review_messages": review_messages,
        "contact_messages": contact_messages,
        "resume_url": getattr(
            settings,
            "RESUME_URL",
            static("documents/Victor_Mwadzombo_Resume.pdf"),
        ),
        "tiktok_url": getattr(settings, "TIKTOK_URL", "https://www.tiktok.com/@victords"),
    }
    return render(request, "index.html", context)





