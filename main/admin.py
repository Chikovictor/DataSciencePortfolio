from django.contrib import admin

from .models import CaseStudy, Certification, Event, ProfileImage, Review


class SuperuserOnlyAdminMixin:
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser


@admin.register(Review)
class ReviewAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "title",
        "is_approved",
        "uses_default_avatar",
        "created_at",
        "archived_at",
    ]
    list_filter = ["is_approved", "uses_default_avatar", "created_at"]
    search_fields = ["name", "title", "review_text"]
    readonly_fields = ["created_at", "uses_default_avatar", "archived_at"]
    actions = ["approve_reviews", "unapprove_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True, archived_at=None)
        Review.enforce_approved_limit()
        self.message_user(request, f"{updated} review(s) approved.")

    @admin.action(description="Set selected reviews as unapproved")
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False, archived_at=None)
        self.message_user(request, f"{updated} review(s) set as unapproved.")


@admin.register(CaseStudy)
class CaseStudyAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["title", "is_published", "display_order", "updated_at"]
    list_filter = ["is_published", "created_at"]
    search_fields = ["title", "summary", "tech_stack"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["is_published", "display_order"]


@admin.register(Event)
class EventAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["title", "date", "order", "is_active", "created_at"]
    list_filter = ["is_active", "date"]
    search_fields = ["title", "description"]
    list_editable = ["order", "is_active"]


@admin.register(ProfileImage)
class ProfileImageAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["caption", "order", "is_active", "updated_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["caption"]
    list_editable = ["order", "is_active"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        image_field = form.base_fields.get("image")
        if image_field:
            image_field.help_text = (
                "Recommended portrait orientation (around 4:5) so the full head remains visible in carousel."
            )
        return form
