from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .validators import validate_image_upload

CASE_STUDY_SECTION_MAX_CHARS = 500


class Review(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=120)
    review_text = models.TextField()
    image = models.ImageField(
        upload_to="reviews/",
        blank=True,
        null=True,
        validators=[validate_image_upload],
    )
    uses_default_avatar = models.BooleanField(default=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.title}"

    def save(self, *args, **kwargs):
        self.uses_default_avatar = not bool(self.image)
        if not self.is_approved:
            self.archived_at = None
        super().save(*args, **kwargs)
        if self.is_approved:
            self.enforce_approved_limit()

    @classmethod
    def enforce_approved_limit(cls):
        max_visible = max(int(getattr(settings, "MAX_VISIBLE_REVIEWS", 10)), 1)
        approved_ids = list(
            cls.objects.filter(is_approved=True)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
        )
        overflow_ids = approved_ids[max_visible:]
        if overflow_ids:
            cls.objects.filter(id__in=overflow_ids).update(
                is_approved=False,
                archived_at=timezone.now(),
            )


class CaseStudy(models.Model):
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    summary = models.CharField(max_length=180)
    preview_image = models.ImageField(upload_to="case-studies/", validators=[validate_image_upload])
    problem = models.TextField(
        max_length=CASE_STUDY_SECTION_MAX_CHARS,
        validators=[MaxLengthValidator(CASE_STUDY_SECTION_MAX_CHARS)],
        help_text=f"Maximum {CASE_STUDY_SECTION_MAX_CHARS} characters.",
    )
    data = models.TextField(
        max_length=CASE_STUDY_SECTION_MAX_CHARS,
        validators=[MaxLengthValidator(CASE_STUDY_SECTION_MAX_CHARS)],
        help_text=f"Maximum {CASE_STUDY_SECTION_MAX_CHARS} characters.",
    )
    approach = models.TextField(
        max_length=CASE_STUDY_SECTION_MAX_CHARS,
        validators=[MaxLengthValidator(CASE_STUDY_SECTION_MAX_CHARS)],
        help_text=f"Maximum {CASE_STUDY_SECTION_MAX_CHARS} characters.",
    )
    results = models.TextField(
        max_length=CASE_STUDY_SECTION_MAX_CHARS,
        validators=[MaxLengthValidator(CASE_STUDY_SECTION_MAX_CHARS)],
        help_text=f"Maximum {CASE_STUDY_SECTION_MAX_CHARS} characters.",
    )
    tech_stack = models.CharField(
        max_length=220,
        help_text="Comma-separated values, e.g. Python, Pandas, Django REST.",
    )
    github_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def repository_url(self):
        return self.github_url

    @property
    def tech_stack_list(self):
        return [item.strip() for item in self.tech_stack.split(",") if item.strip()]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:140] or "case-study"
            candidate = base_slug
            counter = 2
            while CaseStudy.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                suffix = f"-{counter}"
                candidate = f"{base_slug[: max(1, 160 - len(suffix))]}{suffix}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Concise description of the event.")
    image = models.ImageField(upload_to="events/", validators=[validate_image_upload])
    date = models.DateField(blank=True, null=True, help_text="Date for chronological sorting.")
    order = models.PositiveIntegerField(default=0, help_text="Manual display ordering.")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-date", "-created_at"]

    def __str__(self):
        return self.title


class Certification(models.Model):
    title = models.CharField(max_length=180)
    issuing_organization = models.CharField(max_length=180)
    issue_date = models.DateField()
    verification_link = models.URLField()
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "-issue_date", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.issuing_organization}"


class ProfileImage(models.Model):
    image = models.ImageField(upload_to="profile-images/", validators=[validate_image_upload])
    caption = models.CharField(max_length=140, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        if self.caption:
            return self.caption
        return f"Profile Image #{self.pk}"
