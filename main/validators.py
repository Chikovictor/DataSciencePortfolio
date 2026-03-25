from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_UPLOAD_BYTES = 3 * 1024 * 1024

_extension_validator = FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)


def validate_image_upload(upload):
    if not upload:
        return

    _extension_validator(upload)

    content_type = getattr(upload, "content_type", "") or ""
    if content_type and content_type.lower() not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError("Unsupported image type. Use JPG, PNG, or WEBP.")

    if upload.size > MAX_IMAGE_UPLOAD_BYTES:
        raise ValidationError("Image is too large. Maximum size is 3MB.")
